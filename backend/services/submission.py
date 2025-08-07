import os
import uuid
import requests
from werkzeug.utils import secure_filename
from models.solution import Solution
import psycopg2
import psycopg2.extras
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, JUDGE_BASE_URL


class SubmissionService:
    """
    Submission service for handling solution submissions
    """

    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        # Use RealDictCursor for dictionary-like access
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.judge_base_url = JUDGE_BASE_URL
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

            # Validate using Pydantic
            # data = {
            #     "problem_id": problem_id,
            #     "language": language,
            # }
            # try:
            #     solution = Solution(**data)
            # except Exception as e:
            #     raise Exception(f"Invalid solution data: {e}")

            # Forward to judge server
            judge_url = f"{self.judge_base_url}/judge"

            with open(file_path, "rb") as f:
                files = {"code": (saved_filename, f)}
                payload = {"problemID": problem_id, "language": language}

                judge_response = requests.post(judge_url, files=files, data=payload)
                judge_response.raise_for_status()

            db_id = self.save_submission(problem_id, language, user_id)

            return {
                "data": judge_response.json(),
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
        judge_url = f"{self.judge_base_url}/submission/{submission_id}"

        try:
            response = requests.get(judge_url, params={"submission_id": submission_id})
            response.raise_for_status()
            return {"data": response.json(), "status_code": response.status_code}
        except requests.RequestException as e:
            raise Exception(f"Failed to get submission status: {e}")
