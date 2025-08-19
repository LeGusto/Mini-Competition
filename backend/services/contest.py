import os
import psycopg2
from psycopg2 import extras
import requests
import json
from services.connection import get_connection


class ContestService:
    """
    Contest service
    """

    def __init__(self):
        judge_host = os.getenv("JUDGE_HOST", "mini-judge")
        judge_port = os.getenv("JUDGE_PORT", "3000")
        self.judge_base_url = f"http://{judge_host}:{judge_port}"

    def get_contests(self):
        """Get all contests"""
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

            return [
                {
                    "id": contest["id"],
                    "name": contest["name"],
                    "description": contest["description"],
                    "start_time": contest["start_time"].isoformat(),
                    "end_time": contest["end_time"].isoformat(),
                    "problems": contest["problems"],
                    "created_at": contest["created_at"].isoformat(),
                }
                for contest in contests
            ]
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
                "start_time": contest["start_time"].isoformat(),
                "end_time": contest["end_time"].isoformat(),
                "problems": contest["problems"],
                "created_at": contest["created_at"].isoformat(),
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
