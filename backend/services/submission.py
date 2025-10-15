import os
import uuid
import requests
from werkzeug.utils import secure_filename
from models.solution import Solution
import psycopg2
import psycopg2.extras
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from services.connection import get_connection
from datetime import datetime


class SubmissionService:
    """
    Submission service for handling solution submissions
    """

    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        judge_host = os.getenv("JUDGE_HOST", "mini-judge")
        judge_port = os.getenv("JUDGE_PORT", "3000")
        # Use HTTPS for Railway domains, HTTP for local development
        if judge_host.endswith(".railway.app"):
            self.judge_base_url = f"https://{judge_host}"
        else:
            self.judge_base_url = f"http://{judge_host}:{judge_port}"
        self.upload_folder = "tmp"
        os.makedirs(self.upload_folder, exist_ok=True)

    def save_submission(self, problem_id, language, user_id):
        """
        Save a submission to the database
        """
        query = """
            INSERT INTO submissions (problem_id, language, user_id)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        self.cursor.execute(query, (problem_id, language, user_id))
        self.conn.commit()
        return self.cursor.fetchone()["id"]

    def update_judge_submission_id(self, db_id, judge_submission_id):
        """
        Update the submission with the judge submission ID
        """
        query = """
            UPDATE submissions 
            SET judge_submission_id = %s
            WHERE id = %s
        """
        self.cursor.execute(query, (judge_submission_id, db_id))
        self.conn.commit()

    def submit_solution(self, file, problem_id, language, user_id):
        """
        Submit a solution to a problem
        """
        # Validate required fields
        if not file or not problem_id or not language:
            raise Exception("Missing required fields: file, problem_id, language")

        # Sanitize and save the file
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        saved_filename = f"{unique_id}_{original_filename}"
        file_path = os.path.join(self.upload_folder, saved_filename)

        try:
            file.save(file_path)

            # Save submission to database first to get the ID
            db_id = self.save_submission(problem_id, language, user_id)

            # Forward to judge server with callback URL
            judge_url = f"{self.judge_base_url}/judge"
            print(f"Submitting to judge at: {judge_url}")

            # Create callback URL for the judge to send results back
            # Use Railway public domain for callback
            callback_url = os.getenv("RAILWAY_STATIC_URL", "http://localhost:5000")
            if callback_url.startswith("http://") and "railway.app" in callback_url:
                callback_url = callback_url.replace("http://", "https://")
            elif not callback_url.startswith(("http://", "https://")):
                # If no protocol is specified, assume https for Railway domains
                if "railway.app" in callback_url:
                    callback_url = f"https://{callback_url}"
                else:
                    callback_url = f"http://{callback_url}"
            callback_url = f"{callback_url}/submission/result"
            print(f"Callback URL: {callback_url}")

            with open(file_path, "rb") as f:
                files = {"code": (saved_filename, f)}
                payload = {
                    "problemID": problem_id,
                    "language": language,
                    "submission_id": str(db_id),
                    "callback_url": callback_url,
                }
                print(f"Payload: {payload}")

                judge_response = requests.post(judge_url, files=files, data=payload)
                print(f"Judge response status: {judge_response.status_code}")
                print(f"Judge response text: {judge_response.text}")
                if judge_response.status_code != 200:
                    print(f"Judge URL was: {judge_url}")
                    print(f"Payload was: {payload}")
                judge_response.raise_for_status()

                # Parse the judge response to get the judge submission ID
                judge_data = judge_response.json()
                judge_submission_id = judge_data.get("submissionId")

                # Update our database with the judge submission ID
                if judge_submission_id:
                    self.update_judge_submission_id(db_id, judge_submission_id)

            return {
                "data": {
                    "submission_id": db_id,
                    "judge_submission_id": judge_submission_id,
                    "message": "Solution submitted successfully",
                    "judge_response": judge_response.json(),
                },
                "status_code": judge_response.status_code,
                "db_id": db_id,
            }

        except Exception as e:
            # Clean up file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
        finally:
            # Clean up file after processing
            if os.path.exists(file_path):
                os.remove(file_path)

    def get_submission_status(self, submission_id):
        """
        Get submission status from database (includes judge results after callback)
        """
        # Get submission data from database
        query = """
            SELECT id, user_id, problem_id, language, submission_time, 
                   status, judge_response, execution_time, memory_used, judge_submission_id
            FROM submissions WHERE id = %s
        """
        self.cursor.execute(query, (submission_id,))
        submission = self.cursor.fetchone()

        if not submission:
            raise Exception("Submission not found")

        submission_data = dict(submission) if submission else {}

        return {
            "data": {
                "submission_id": submission_data.get("id"),
                "problem_id": submission_data.get("problem_id"),
                "language": submission_data.get("language"),
                "status": submission_data.get("status", "queued"),
                "judge_response": submission_data.get("judge_response"),
                "execution_time": (
                    float(submission_data.get("execution_time"))
                    if submission_data.get("execution_time")
                    else None
                ),
                "memory_used": submission_data.get("memory_used"),
                "judge_submission_id": submission_data.get("judge_submission_id"),
                "submission_time": (
                    submission_data.get("submission_time").isoformat()
                    if submission_data.get("submission_time")
                    else None
                ),
            },
            "status_code": 200,
        }

    def get_user_submissions(self, user_id):
        """
        Get all submissions for a specific user
        """
        query = """
            SELECT s.id, s.problem_id, s.language, s.submission_time, s.status, s.judge_response, s.execution_time, s.memory_used, s.judge_submission_id
            FROM submissions s
            WHERE s.user_id = %s
            ORDER BY s.submission_time DESC
        """

        try:
            print(f"Attempting to get submissions for user {user_id}")
            self.cursor.execute(query, (user_id,))
            submissions = self.cursor.fetchall()
            print(f"Found {len(submissions)} submissions")

            # Convert to list of dictionaries
            result = []
            for submission in submissions:
                result.append(
                    {
                        "id": submission["id"],
                        "problem_id": submission["problem_id"],
                        "language": submission["language"],
                        "submission_time": (
                            submission["submission_time"].isoformat() + "Z"
                            if submission["submission_time"]
                            else None
                        ),
                        "status": submission["status"],
                        "judge_response": submission["judge_response"],
                        "execution_time": submission["execution_time"],
                        "memory_used": submission["memory_used"],
                        "judge_submission_id": submission["judge_submission_id"],
                    }
                )

            return {"data": result, "status_code": 200}
        except Exception as e:
            print(f"Database error in get_user_submissions: {e}")
            print(f"Error type: {type(e)}")
            import traceback

            traceback.print_exc()
            raise Exception(f"Failed to get user submissions: {e}")

    def update_submission_result(
        self,
        submission_id,
        problem_id,
        status,
        judge_response,
        execution_time=None,
        memory_used=None,
    ):
        """
        Update submission result when received from judge
        """
        print(f"Updating submission result: {submission_id}, {problem_id}, {status}")
        print(f"Judge response: {judge_response}")
        print(f"Execution time: {execution_time}, Memory: {memory_used}")

        query = """
            UPDATE submissions 
            SET status = %s, 
                judge_response = %s,
                execution_time = %s,
                memory_used = %s
            WHERE id = %s AND problem_id = %s
            RETURNING id
        """

        try:
            print(
                f"Executing query with params: {status}, {judge_response}, {execution_time}, {memory_used}, {submission_id}, {problem_id}"
            )

            # Convert judge_response dict to JSON string for PostgreSQL
            import json

            judge_response_json = json.dumps(judge_response) if judge_response else None

            self.cursor.execute(
                query,
                (
                    status,
                    judge_response_json,  # Use JSON string instead of dict
                    execution_time,
                    memory_used,
                    submission_id,
                    problem_id,
                ),
            )
            self.conn.commit()

            if self.cursor.rowcount == 0:
                print(f"No rows updated for submission {submission_id}")
                raise Exception("Submission not found or problem_id mismatch")

            print(f"Successfully updated submission {submission_id}")
            return {
                "data": {"message": "Submission result updated successfully"},
                "status_code": 200,
            }
        except Exception as e:
            print(f"Error updating submission result: {e}")
            self.conn.rollback()
            raise Exception(f"Failed to update submission result: {e}")

    def get_database_timezone_info(self):
        """Get database timezone information for debugging"""
        try:
            # Get current database time and timezone
            self.cursor.execute("SELECT CURRENT_TIMESTAMP, CURRENT_TIME, NOW()")
            result = self.cursor.fetchone()

            # Get timezone setting
            self.cursor.execute("SHOW timezone")
            timezone_result = self.cursor.fetchone()

            print(f"🌍 Database timezone info:")
            print(f"   Current timestamp: {result[0]}")
            print(f"   Current time: {result[1]}")
            print(f"   NOW(): {result[2]}")
            print(
                f"   Timezone setting: {timezone_result[0] if timezone_result else 'Unknown'}"
            )

            return result
        except Exception as e:
            print(f"Error getting timezone info: {e}")
            return None

    def get_active_contest_for_problem(self, problem_id):
        """Get the active contest that contains this problem"""
        try:
            # Handle JSONB array properly
            query = """
                SELECT id, name, start_time, end_time, problems
                FROM contests 
                WHERE problems @> %s::jsonb
                AND start_time <= CURRENT_TIMESTAMP 
                AND end_time >= CURRENT_TIMESTAMP
                ORDER BY start_time DESC
                LIMIT 1
            """

            self.cursor.execute(query, (f'["{problem_id}"]',))
            contest = self.cursor.fetchone()

            if contest:
                print(
                    f"🎯 Found active contest for problem {problem_id}: {contest['name']} (ID: {contest['id']})"
                )
                print(
                    f"   Contest time range: {contest['start_time']} to {contest['end_time']}"
                )

                # Contest is already found by the query which checks time constraints
                print(f"   Contest is active (verified by query constraints)")
            else:
                print(f"ℹ️ No active contest found for problem {problem_id}")

            return contest
        except Exception as e:
            print(f"❌ Error getting active contest for problem {problem_id}: {e}")
            import traceback

            traceback.print_exc()
            return None

    def get_all_active_contests_for_user_and_problem(
        self, user_id, problem_id, submission_time=None
    ):
        """Get all active contests where the user is registered and the problem exists"""
        try:
            if submission_time:
                # Use submission time for validation - submission must be within contest bounds
                query = """
                    SELECT DISTINCT c.id, c.name, c.start_time, c.end_time, c.problems
                    FROM contests c
                    JOIN contest_participants cp ON c.id = cp.contest_id
                    WHERE cp.user_id = %s
                    AND c.problems @> %s::jsonb
                    AND %s >= c.start_time
                    AND %s <= c.end_time
                    ORDER BY c.start_time DESC
                """
                print(f"   Querying contests for submission at {submission_time}")
                self.cursor.execute(
                    query,
                    (user_id, f'["{problem_id}"]', submission_time, submission_time),
                )
            else:
                # Use current timestamp
                query = """
                    SELECT DISTINCT c.id, c.name, c.start_time, c.end_time, c.problems
                    FROM contests c
                    JOIN contest_participants cp ON c.id = cp.contest_id
                    WHERE cp.user_id = %s
                    AND c.problems @> %s::jsonb
                    AND c.start_time <= CURRENT_TIMESTAMP
                    AND c.end_time >= CURRENT_TIMESTAMP
                    ORDER BY c.start_time DESC
                """
                self.cursor.execute(query, (user_id, f'["{problem_id}"]'))
            contests = self.cursor.fetchall()

            print(
                f"🎯 Found {len(contests)} active contests for user {user_id} and problem {problem_id}"
            )
            for contest in contests:
                print(f"   - {contest['name']} (ID: {contest['id']})")

            return contests
        except Exception as e:
            print(
                f"❌ Error getting active contests for user {user_id} and problem {problem_id}: {e}"
            )
            return []

    def create_contest_submission(
        self,
        contest_id,
        user_id,
        problem_id,
        submission_id,
        submission_time,
        is_accepted,
        score=0,
        penalty_time=0,
    ):
        """Create a contest submission entry"""
        try:
            # Get contest start and end times
            query = """
                SELECT start_time, end_time FROM contests WHERE id = %s
            """
            self.cursor.execute(query, (contest_id,))
            contest = self.cursor.fetchone()

            if not contest:
                print(f"Contest {contest_id} not found")
                return None

            # Insert contest submission
            insert_query = """
                INSERT INTO contest_submissions 
                (contest_id, user_id, problem_id, submission_id, submission_time, 
                 is_accepted, score, penalty_time, contest_start_time, contest_end_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """

            self.cursor.execute(
                insert_query,
                (
                    contest_id,
                    user_id,
                    problem_id,
                    submission_id,
                    submission_time,
                    is_accepted,
                    score,
                    penalty_time,
                    contest["start_time"],
                    contest["end_time"],
                ),
            )

            result = self.cursor.fetchone()
            self.conn.commit()
            print(f"Created contest submission: {result['id']}")
            return result["id"]

        except Exception as e:
            self.conn.rollback()
            print(f"Error creating contest submission: {e}")
            return None

    def get_submission_details(self, submission_id):
        """Get submission details including user_id"""
        try:
            query = """
                SELECT id, user_id, problem_id, language, submission_time, status
                FROM submissions 
                WHERE id = %s
            """

            self.cursor.execute(query, (submission_id,))
            submission = self.cursor.fetchone()
            return submission
        except Exception as e:
            print(f"Error getting submission details: {e}")
            return None
