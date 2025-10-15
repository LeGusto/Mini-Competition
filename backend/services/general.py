import os
import requests
from flask import Response


class GeneralService:
    """
    General service for handling problem-related operations
    """

    def __init__(self):
        judge_host = os.getenv("JUDGE_HOST", "mini-judge")
        judge_port = os.getenv("JUDGE_PORT", "3000")
        # Use HTTPS for Railway domains, HTTP for local development
        if judge_host.endswith(".railway.app"):
            self.judge_base_url = f"https://{judge_host}"
        else:
            self.judge_base_url = f"http://{judge_host}:{judge_port}"

    def get_problems(self):
        """
        Get all available problems from the judge server
        """
        print("get_problems===\n\n", flush=True)
        judge_url = f"{self.judge_base_url}/problems"
        print("judge_url===\n\n", judge_url, flush=True)

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

    def get_problem_metadata(self, problem_id):
        """
        Get metadata for a specific problem from the judge server
        """
        judge_url = f"{self.judge_base_url}/problem/{problem_id}/metadata"

        try:
            judge_response = requests.get(judge_url)
            judge_response.raise_for_status()
            return judge_response.json()
        except requests.RequestException as e:
            # If individual metadata endpoint doesn't exist, try to get it from the problems list
            try:
                problems_response = requests.get(f"{self.judge_base_url}/problems")
                problems_response.raise_for_status()
                problems_data = problems_response.json()

                # Find the specific problem
                for problem in problems_data.get("problems", []):
                    if problem.get("id") == problem_id:
                        return problem

                raise Exception(f"Problem {problem_id} not found")
            except requests.RequestException as fallback_error:
                raise Exception(f"Failed to get problem metadata: {e}")

    def health_check(self):
        """
        Health check
        """
        return {"message": "OK"}
