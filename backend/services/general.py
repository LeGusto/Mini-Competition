import requests
from flask import Response


class GeneralService:
    """
    General service for handling problem-related operations
    """

    def __init__(self):
        self.judge_base_url = "http://localhost:3000"

    def get_problems(self):
        """
        Get all available problems from the judge server
        """
        judge_url = f"{self.judge_base_url}/problems"

        try:
            judge_response = requests.get(judge_url)
            judge_response.raise_for_status()
            return {"problems": judge_response.json()["problems"]}
        except requests.RequestException as e:
            raise Exception(f"Failed to contact judge server: {e}")

    def get_problem_statement(self, problem_id):
        """
        Get problem statement PDF from the judge server
        """
        judge_url = f"{self.judge_base_url}/problem/{problem_id}/statement"

        try:
            judge_response = requests.get(judge_url, stream=True)
            judge_response.raise_for_status()

            # Return the response object for streaming
            return {
                "content": judge_response.iter_content(chunk_size=8192),
                "content_type": judge_response.headers.get(
                    "content-type", "application/pdf"
                ),
                "content_disposition": judge_response.headers.get(
                    "content-disposition",
                    f'inline; filename="problem_{problem_id}_statement.pdf"',
                ),
            }
        except requests.RequestException as e:
            raise Exception(f"Failed to get problem statement: {e}")

    def health_check(self):
        """
        Health check
        """
        return {"message": "OK"}
