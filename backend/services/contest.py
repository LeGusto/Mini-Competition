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
        self.judge_base_url = f"http://{judge_host}:{judge_port}"

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
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT id, name, description, start_time, end_time, problems, created_at
                FROM contests
                ORDER BY created_at DESC
            """
            )

            contests = cursor.fetchall()
            result = []

            # Get all solved problems for the user once
            solved_problems = self.get_user_solved_problems_count(user_id)

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

                # Count how many solved problems are in this contest
                if user_id and contest["problems"]:
                    contest_problems = contest["problems"]
                    if isinstance(contest_problems, str):
                        contest_problems = json.loads(contest_problems)

                    # Count intersection of solved problems and contest problems
                    solved_in_contest = sum(
                        1
                        for problem in solved_problems
                        if problem["problem_id"] in contest_problems
                    )
                    contest_data["solved_problems"] = solved_in_contest

                result.append(contest_data)

            return result
        finally:
            cursor.close()
            conn.close()

    def get_user_solved_problems_count(self, user_id):
        """Get count of problems solved by user in a specific contest"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Count distinct problems where user has accepted submissions
            # A problem is considered solved if all test cases passed (failed = 0)
            # Also handle cases where judge_response might be null or incomplete
            query = """
                SELECT DISTINCT problem_id
                FROM submissions 
                WHERE user_id = %s 
                AND status = 'accepted'
            """

            cursor.execute(query, (user_id,))
            result = cursor.fetchall()

            return result
        finally:
            cursor.close()
            conn.close()

    def create_contest(self, name, description, start_time, end_time, problems):
        """Create a new contest"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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

            cursor.execute(
                """
                INSERT INTO contests (name, description, start_time, end_time, problems)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, name, description, start_time, end_time, problems, created_at
            """,
                (name, description, start_time, end_time, problems_json),
            )

            contest = cursor.fetchone()
            conn.commit()

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
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_problem_ids(self, contest_id):
        """Get the contest problems"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT problems FROM contests WHERE id = %s", (contest_id,))
        problems = cursor.fetchone()
        cursor.close()
        conn.close()
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
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get contest info
            cursor.execute(
                """
                SELECT id, name, start_time, end_time, problems
                FROM contests WHERE id = %s
            """,
                (contest_id,),
            )

            contest = cursor.fetchone()
            if not contest:
                return None

            # Check if there are any contest submissions
            cursor.execute(
                "SELECT COUNT(*) as count FROM contest_submissions WHERE contest_id = %s",
                (contest_id,),
            )
            submission_count = cursor.fetchone()["count"]

            if submission_count == 0:
                # No submissions yet, return empty leaderboard
                return {
                    "contest": {
                        "id": contest["id"],
                        "name": contest["name"],
                        "start_time": self.convert_to_local_time(contest["start_time"]),
                        "end_time": self.convert_to_local_time(contest["end_time"]),
                        "problems": contest["problems"],
                    },
                    "leaderboard": [],
                    "message": "No submissions yet for this contest",
                }

            # Get leaderboard data
            cursor.execute(
                """
                SELECT 
                    u.id as user_id,
                    u.username,
                    COUNT(DISTINCT cs.problem_id) as problems_solved,
                    SUM(cs.score) as total_score,
                    SUM(cs.penalty_time) as total_penalty,
                    MIN(cs.submission_time) as first_solve_time
                FROM users u
                LEFT JOIN contest_submissions cs ON u.id = cs.user_id AND cs.contest_id = %s AND cs.is_accepted = TRUE
                WHERE u.id IN (
                    SELECT DISTINCT user_id FROM contest_submissions WHERE contest_id = %s
                )
                GROUP BY u.id, u.username
                ORDER BY problems_solved DESC, total_score DESC, total_penalty ASC, first_solve_time ASC
            """,
                (contest_id, contest_id),
            )

            leaderboard = cursor.fetchall()

            # Convert to list of dictionaries
            result = []
            for i, entry in enumerate(leaderboard):
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

        finally:
            cursor.close()
            conn.close()

    def get_user_contest_submissions(self, contest_id, user_id):
        """Get all submissions for a user in a specific contest"""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Check if there are any contest submissions for this contest
            cursor.execute(
                "SELECT COUNT(*) as count FROM contest_submissions WHERE contest_id = %s",
                (contest_id,),
            )
            submission_count = cursor.fetchone()["count"]

            if submission_count == 0:
                # No submissions yet for this contest
                return []

            cursor.execute(
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

            submissions = cursor.fetchall()

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

        finally:
            cursor.close()
            conn.close()
