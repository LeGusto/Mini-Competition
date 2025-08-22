import os
import uuid
import requests
from werkzeug.utils import secure_filename
from models.solution import Solution
import psycopg2
import psycopg2.extras
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from services.connection import get_connection


class SubmissionService:
    """
    Submission service for handling solution submissions
    """

    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        judge_host = os.getenv("JUDGE_HOST", "mini-judge")
        judge_port = os.getenv("JUDGE_PORT", "3000")
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
            callback_url = f"http://backend:5000/submission/result"
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
                print(f"Judge response: {judge_response.text}")
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
        Get submission status from the judge server
        """
        # First get the judge submission ID from our database
        query = """
            SELECT judge_submission_id FROM submissions WHERE id = %s
        """
        self.cursor.execute(query, (submission_id,))
        result = self.cursor.fetchone()

        if not result or not result["judge_submission_id"]:
            raise Exception("Judge submission ID not found")

        judge_submission_id = result["judge_submission_id"]
        judge_url = f"{self.judge_base_url}/submission/{judge_submission_id}"
        print(f"Getting submission status from: {judge_url}")

        try:
            response = requests.get(judge_url)
            print(f"Judge status response: {response.status_code} - {response.text}")
            response.raise_for_status()
            return {"data": response.json(), "status_code": response.status_code}
        except requests.RequestException as e:
            print(f"Request exception: {e}")
            raise Exception(f"Failed to get submission status: {e}")
        except Exception as e:
            print(f"Other exception: {e}")
            raise Exception(f"Failed to get submission status: {e}")

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
                            submission["submission_time"].isoformat()
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

            print(f"Database update completed. Rows affected: {self.cursor.rowcount}")
            print(
                f"Stored execution_time: {execution_time}, memory_used: {memory_used}"
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
