import os
import psycopg2
from psycopg2 import extras
import requests
from services.connection import get_connection


class ContestService:
    """
    Contest service
    """

    def __init__(self):
        judge_host = os.getenv("JUDGE_HOST", "mini-judge")
        judge_port = os.getenv("JUDGE_PORT", "3000")
        self.judge_base_url = f"http://{judge_host}:{judge_port}"

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
