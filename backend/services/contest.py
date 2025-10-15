import os
import psycopg2
from psycopg2 import extras
import requests
import json
from datetime import datetime, timezone
import pytz
from services.connection import get_connection


class ContestService:
    """
    Contest service
    """

    def __init__(self):
        judge_host = os.getenv("JUDGE_HOST", "mini-judge")
        judge_port = os.getenv("JUDGE_PORT", "3000")
        # Use HTTPS for Railway domains, HTTP for local development
        if judge_host.endswith(".railway.app"):
            self.judge_base_url = f"https://{judge_host}"
        else:
            self.judge_base_url = f"http://{judge_host}:{judge_port}"
        # Initialize with UTC timezone by default
        self.local_timezone = pytz.timezone("UTC")
        self.conn = get_connection()
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def set_timezone(self, timezone_name):
        """Set the timezone for time conversions"""
        try:
            self.local_timezone = pytz.timezone(timezone_name)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fallback to UTC if invalid timezone
            self.local_timezone = pytz.timezone("UTC")

    def convert_to_local_time(self, utc_time):
        """Convert UTC time to local timezone with timezone info"""
        if utc_time is None:
            return None

        # Ensure the time is timezone-aware (UTC)
        if utc_time.tzinfo is None:
            utc_time = utc_time.replace(tzinfo=timezone.utc)

        # Convert to local timezone
        local_time = utc_time.astimezone(self.local_timezone)

        # Format with timezone abbreviation
        timezone_abbr = local_time.strftime("%Z")
        return {
            "iso": local_time.isoformat(),
            "formatted": local_time.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": timezone_abbr,
            "timezone_name": str(self.local_timezone),
            "utc_iso": utc_time.isoformat(),  # Keep UTC for status calculations
        }

    def get_contests(self, user_id=None):
        """Get all contests with optional solved problems count for a user"""
        self.cursor.execute(
            """
            SELECT id, name, description, start_time, end_time, problems, created_at
            FROM contests
            ORDER BY created_at DESC
        """
        )

        contests = self.cursor.fetchall()
        result = []

        for contest in contests:
            contest_data = {
                "id": contest["id"],
                "name": contest["name"],
                "description": contest["description"],
                "start_time": self.convert_to_local_time(contest["start_time"]),
                "end_time": self.convert_to_local_time(contest["end_time"]),
                "problems": contest["problems"],
                "created_at": self.convert_to_local_time(contest["created_at"]),
            }

            # Count how many problems user solved DURING this contest
            if user_id:
                self.cursor.execute(
                    """
                    SELECT COUNT(DISTINCT problem_id) as solved_count
                    FROM contest_submissions
                    WHERE contest_id = %s 
                    AND user_id = %s 
                    AND is_accepted = TRUE
                    """,
                    (contest["id"], user_id),
                )
                solved_result = self.cursor.fetchone()
                contest_data["solved_problems"] = solved_result["solved_count"] or 0

            result.append(contest_data)

        return result

    def get_user_solved_problems_count(self, user_id):
        """Get count of all problems solved by user (across all submissions, not contest-specific)"""
        # Count distinct problems where user has accepted submissions
        # A problem is considered solved if all test cases passed (failed = 0)
        # Also handle cases where judge_response might be null or incomplete
        query = """
            SELECT DISTINCT problem_id
            FROM submissions 
            WHERE user_id = %s 
            AND status = 'accepted'
        """

        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchall()

        return result

    def create_contest(self, name, description, start_time, end_time, problems):
        """Create a new contest"""
        try:
            # Convert problems list to JSONB
            problems_json = json.dumps(problems)

            # Ensure times are stored as UTC
            # If start_time and end_time are strings, parse them and ensure they're UTC
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

            # If times don't have timezone info, assume they're in UTC
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)

            self.cursor.execute(
                """
                INSERT INTO contests (name, description, start_time, end_time, problems)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, name, description, start_time, end_time, problems, created_at
            """,
                (name, description, start_time, end_time, problems_json),
            )

            contest = self.cursor.fetchone()
            self.conn.commit()

            return {
                "id": contest["id"],
                "name": contest["name"],
                "description": contest["description"],
                "start_time": self.convert_to_local_time(contest["start_time"]),
                "end_time": self.convert_to_local_time(contest["end_time"]),
                "problems": contest["problems"],
                "created_at": self.convert_to_local_time(contest["created_at"]),
            }
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_problem_ids(self, contest_id):
        """Get the contest problems"""
        self.cursor.execute(
            "SELECT problems FROM contests WHERE id = %s", (contest_id,)
        )
        problems = self.cursor.fetchone()
        return list(problems["problems"])

    def get_problem_data(self, contest_id):
        """Get the problem data"""
        problems = self.get_problem_ids(contest_id)
        print("problems===", problems, flush=True)
        judge_url = f"{self.judge_base_url}/problems?problems={problems}"
        response = requests.get(judge_url)
        print("response===", response.json())
        return response.json()

    def get_contest_leaderboard(self, contest_id):
        """Get the leaderboard for a specific contest"""
        # Get contest info
        self.cursor.execute(
            """
            SELECT id, name, start_time, end_time, problems
            FROM contests WHERE id = %s
        """,
            (contest_id,),
        )

        contest = self.cursor.fetchone()
        if not contest:
            return None

        # Get leaderboard data for ALL registered users (including those with no submissions)
        self.cursor.execute(
            """
            SELECT 
                u.id as user_id,
                u.username,
                COUNT(DISTINCT CASE WHEN cs.is_accepted = TRUE THEN cs.problem_id END) as problems_solved,
                COALESCE(SUM(CASE WHEN cs.is_accepted = TRUE AND cs.submission_time = (
                    SELECT MIN(cs2.submission_time) 
                    FROM contest_submissions cs2 
                    WHERE cs2.contest_id = cs.contest_id 
                    AND cs2.user_id = cs.user_id 
                    AND cs2.problem_id = cs.problem_id 
                    AND cs2.is_accepted = TRUE
                ) THEN cs.score END), 0) as total_score,
                0 as total_penalty,  -- Will calculate penalty properly below
                MIN(CASE WHEN cs.is_accepted = TRUE THEN cs.submission_time END) as first_solve_time
            FROM users u
            INNER JOIN contest_participants cp ON u.id = cp.user_id AND cp.contest_id = %s
            LEFT JOIN contest_submissions cs ON u.id = cs.user_id AND cs.contest_id = %s
            GROUP BY u.id, u.username
            ORDER BY problems_solved DESC, total_score DESC, first_solve_time ASC
        """,
            (contest_id, contest_id),
        )

        leaderboard = self.cursor.fetchall()

        # Calculate penalty times properly for each user
        for entry in leaderboard:
            user_id = entry["user_id"]
            total_penalty = 0

            # Get problems that this user eventually solved
            self.cursor.execute(
                """
                SELECT DISTINCT problem_id 
                FROM contest_submissions 
                WHERE contest_id = %s AND user_id = %s AND is_accepted = TRUE
                """,
                (contest_id, user_id),
            )
            solved_problems = [row["problem_id"] for row in self.cursor.fetchall()]

            # For each solved problem, count wrong submissions before the accepted one
            for problem_id in solved_problems:
                self.cursor.execute(
                    """
                    SELECT COUNT(*) as wrong_attempts
                    FROM contest_submissions cs1
                    WHERE cs1.contest_id = %s 
                    AND cs1.user_id = %s 
                    AND cs1.problem_id = %s
                    AND cs1.is_accepted = FALSE
                    AND cs1.submission_time < (
                        SELECT MIN(cs2.submission_time)
                        FROM contest_submissions cs2
                        WHERE cs2.contest_id = %s 
                        AND cs2.user_id = %s 
                        AND cs2.problem_id = %s
                        AND cs2.is_accepted = TRUE
                    )
                    """,
                    (
                        contest_id,
                        user_id,
                        problem_id,
                        contest_id,
                        user_id,
                        problem_id,
                    ),
                )
                wrong_attempts = self.cursor.fetchone()["wrong_attempts"]
                total_penalty += (
                    wrong_attempts * 20
                )  # 20 minutes penalty per wrong attempt

            # Update the entry with calculated penalty
            entry["total_penalty"] = total_penalty

        # Sort leaderboard properly: by problems solved (desc), then by penalty (asc), then by first solve time (asc)
        leaderboard = sorted(
            leaderboard,
            key=lambda x: (
                -x["problems_solved"],
                x["total_penalty"],
                x["first_solve_time"] or datetime.max.replace(tzinfo=timezone.utc),
            ),
        )

        # Get first blood information for each problem
        first_blood = {}
        for problem_id in contest["problems"]:
            self.cursor.execute(
                """
                SELECT user_id, MIN(submission_time) as first_solve_time
                FROM contest_submissions 
                WHERE contest_id = %s AND problem_id = %s AND is_accepted = TRUE
                GROUP BY user_id
                ORDER BY first_solve_time ASC
                LIMIT 1
                """,
                (contest_id, problem_id),
            )
            first_solver = self.cursor.fetchone()
            if first_solver:
                first_blood[problem_id] = first_solver["user_id"]

        # Convert to list of dictionaries and add problem status for each user
        result = []
        for i, entry in enumerate(leaderboard):
            user_id = entry["user_id"]

            # Get problem status for each problem in the contest
            problem_statuses = {}
            for problem_id in contest["problems"]:
                # Get all submissions for this user-problem combination
                self.cursor.execute(
                    """
                    SELECT is_accepted, submission_time 
                    FROM contest_submissions 
                    WHERE contest_id = %s AND user_id = %s AND problem_id = %s 
                    ORDER BY submission_time ASC
                    """,
                    (contest_id, user_id, problem_id),
                )
                submissions = self.cursor.fetchall()

                if not submissions:
                    # Check if there are any pending submissions from main submissions table
                    self.cursor.execute(
                        """
                        SELECT status FROM submissions 
                        WHERE user_id = %s AND problem_id = %s AND status = 'pending'
                        ORDER BY submission_time DESC LIMIT 1
                        """,
                        (user_id, problem_id),
                    )
                    pending_submission = self.cursor.fetchone()

                    if pending_submission:
                        problem_statuses[problem_id] = {
                            "status": "pending",
                            "attempts": 0,
                            "solve_time": None,
                            "is_first_blood": False,
                        }
                    else:
                        problem_statuses[problem_id] = {
                            "status": "untried",
                            "attempts": 0,
                            "solve_time": None,
                            "is_first_blood": False,
                        }
                else:
                    # Check if any submission was accepted
                    accepted_submission = next(
                        (s for s in submissions if s["is_accepted"]), None
                    )

                    if accepted_submission:
                        # Calculate solve time from contest start
                        contest_start = contest["start_time"]
                        if contest_start.tzinfo is None:
                            contest_start = contest_start.replace(tzinfo=timezone.utc)

                        solve_time = accepted_submission["submission_time"]
                        if solve_time.tzinfo is None:
                            solve_time = solve_time.replace(tzinfo=timezone.utc)

                        solve_minutes = int(
                            (solve_time - contest_start).total_seconds() / 60
                        )

                        # Count penalty attempts (wrong attempts before first accepted)
                        penalty_attempts = 0
                        for sub in submissions:
                            if (
                                not sub["is_accepted"]
                                and sub["submission_time"]
                                < accepted_submission["submission_time"]
                            ):
                                penalty_attempts += 1

                        problem_statuses[problem_id] = {
                            "status": "solved",
                            "attempts": len(submissions),
                            "penalty_attempts": penalty_attempts,
                            "solve_time": solve_minutes,
                            "is_first_blood": first_blood.get(problem_id) == user_id,
                        }
                    else:
                        # Check if there are any pending submissions from main submissions table
                        self.cursor.execute(
                            """
                            SELECT status FROM submissions 
                            WHERE user_id = %s AND problem_id = %s AND status = 'pending'
                            ORDER BY submission_time DESC LIMIT 1
                            """,
                            (user_id, problem_id),
                        )
                        pending_submission = self.cursor.fetchone()

                        if pending_submission:
                            problem_statuses[problem_id] = {
                                "status": "pending",
                                "attempts": len(submissions),
                                "solve_time": None,
                                "is_first_blood": False,
                            }
                        else:
                            problem_statuses[problem_id] = {
                                "status": "attempted",
                                "attempts": len(submissions),
                                "solve_time": None,
                                "is_first_blood": False,
                            }

            result.append(
                {
                    "rank": i + 1,
                    "user_id": entry["user_id"],
                    "username": entry["username"],
                    "problems_solved": entry["problems_solved"] or 0,
                    "total_score": entry["total_score"] or 0,
                    "total_penalty": entry["total_penalty"] or 0,
                    "first_solve_time": (
                        self.convert_to_local_time(entry["first_solve_time"])
                        if entry["first_solve_time"]
                        else None
                    ),
                    "problem_statuses": problem_statuses,
                }
            )

        return {
            "contest": {
                "id": contest["id"],
                "name": contest["name"],
                "start_time": self.convert_to_local_time(contest["start_time"]),
                "end_time": self.convert_to_local_time(contest["end_time"]),
                "problems": contest["problems"],
            },
            "leaderboard": result,
        }

    def get_user_contest_submissions(self, contest_id, user_id):
        """Get all submissions for a user in a specific contest"""
        # Check if there are any contest submissions for this contest
        self.cursor.execute(
            "SELECT COUNT(*) as count FROM contest_submissions WHERE contest_id = %s",
            (contest_id,),
        )
        submission_count = self.cursor.fetchone()["count"]

        if submission_count == 0:
            # No submissions yet for this contest
            return []

        self.cursor.execute(
            """
            SELECT
                cs.id,
                cs.problem_id,
                cs.submission_time,
                cs.is_accepted,
                cs.score,
                cs.penalty_time,
                s.language,
                s.judge_response
            FROM contest_submissions cs
            JOIN submissions s ON cs.submission_id = s.id
            WHERE cs.contest_id = %s AND cs.user_id = %s
            ORDER BY cs.submission_time DESC
        """,
            (contest_id, user_id),
        )

        submissions = self.cursor.fetchall()

        result = []
        for sub in submissions:
            result.append(
                {
                    "id": sub["id"],
                    "problem_id": sub["problem_id"],
                    "submission_time": self.convert_to_local_time(
                        sub["submission_time"]
                    ),
                    "is_accepted": sub["is_accepted"],
                    "score": sub["score"],
                    "penalty_time": sub["penalty_time"],
                    "language": sub["language"],
                    "judge_response": sub["judge_response"],
                }
            )

        return result

    def check_user_registration(self, contest_id, user_id):
        """Check if a user is registered for a contest"""
        self.cursor.execute(
            """
            SELECT id FROM contest_participants
            WHERE contest_id = %s AND user_id = %s
        """,
            (contest_id, user_id),
        )

        result = self.cursor.fetchone()
        return result is not None

    def get_user_registration_data(self, contest_id, user_id):
        """Get detailed registration data for a user in a contest"""
        self.cursor.execute(
            """
            SELECT
                cp.id,
                cp.created_at as registered_at,
                cp.updated_at,
                u.username,
                c.name as contest_name
            FROM contest_participants cp
            JOIN users u ON cp.user_id = u.id
            JOIN contests c ON cp.contest_id = c.id
            WHERE cp.contest_id = %s AND cp.user_id = %s
        """,
            (contest_id, user_id),
        )

        result = self.cursor.fetchone()
        if result:
            return {
                "registration_id": result["id"],
                "registered_at": self.convert_to_local_time(result["registered_at"]),
                "username": result["username"],
                "contest_name": result["contest_name"],
            }
        return None

    def register_for_contest(self, contest_id, user_id):
        """Register a user for a contest"""
        try:
            # Check if user is already registered
            if self.check_user_registration(contest_id, user_id):
                return {
                    "success": False,
                    "message": "User is already registered for this contest",
                }

            # Check if contest exists
            self.cursor.execute("SELECT id FROM contests WHERE id = %s", (contest_id,))
            contest = self.cursor.fetchone()
            if not contest:
                return {"success": False, "message": "Contest not found"}

            # Register the user
            self.cursor.execute(
                """
                INSERT INTO contest_participants (contest_id, user_id)
                VALUES (%s, %s)
                RETURNING id
            """,
                (contest_id, user_id),
            )

            self.conn.commit()
            return {"success": True, "message": "Successfully registered for contest"}

        except Exception as e:
            self.conn.rollback()
            return {"success": False, "message": f"Registration failed: {str(e)}"}

    def get_contest_access_status(self, contest_id, user_id):
        """Get access status for a user to view contest problems"""
        # Get contest info
        self.cursor.execute(
            """
            SELECT id, start_time, end_time
            FROM contests WHERE id = %s
        """,
            (contest_id,),
        )

        contest = self.cursor.fetchone()
        if not contest:
            return {"can_access": False, "reason": "Contest not found"}

        # Check if user is registered
        is_registered = self.check_user_registration(contest_id, user_id)

        # Determine contest status
        now = datetime.now(timezone.utc)
        start_time = contest["start_time"]
        end_time = contest["end_time"]

        # Ensure start_time and end_time are timezone-aware
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        if now < start_time:
            contest_status = "upcoming"
        elif now > end_time:
            contest_status = "ended"
        else:
            contest_status = "active"

        # Determine access rights
        if contest_status == "ended":
            # Ended contests are viewable by everyone
            return {
                "can_access": True,
                "reason": "Contest has ended - you can view all problems",
                "contest_status": contest_status,
                "is_registered": is_registered,
            }
        elif not is_registered:
            return {
                "can_access": False,
                "reason": "You must register for this contest to view problems",
                "can_register": contest_status != "ended",
                "contest_status": contest_status,
                "is_registered": False,
            }

        # User is registered
        if contest_status == "active":
            return {
                "can_access": True,
                "reason": "Contest is active - you can view and solve problems",
                "contest_status": contest_status,
                "is_registered": True,
            }
        else:  # upcoming
            return {
                "can_access": False,
                "reason": "Contest hasn't started yet. You can view problems once it begins.",
                "contest_status": contest_status,
                "is_registered": True,
            }
