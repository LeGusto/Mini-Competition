from flask import Blueprint, request, jsonify, Response
from models.solution import Solution
from werkzeug.utils import secure_filename
import os
import uuid
import requests
import pathlib

general_bp = Blueprint("general", __name__)


@general_bp.route("/general/problems", methods=["GET"])
def get_problems():
    """Proxy to the judge server to get problem ids"""
    judge_url = "http://localhost:3000/problems"

    try:
        judge_response = requests.get(judge_url)
        judge_response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"message": f"Failed to contact judge server: {e}"}), 500

    return jsonify({"problems": judge_response.json()["problems"]})


@general_bp.route("/general/problem/<problem_id>/statement", methods=["GET"])
def get_problem_statement(problem_id):
    """Proxy to the judge server to get problem statement PDF"""
    judge_url = f"http://localhost:3000/problem/{problem_id}/statement"

    try:
        judge_response = requests.get(judge_url, stream=True)
        judge_response.raise_for_status()

        # Stream the PDF response
        return Response(
            judge_response.iter_content(chunk_size=8192),
            content_type=judge_response.headers.get("content-type", "application/pdf"),
            headers={
                "Content-Disposition": judge_response.headers.get(
                    "content-disposition",
                    f'inline; filename="problem_{problem_id}_statement.pdf"',
                )
            },
        )
    except requests.RequestException as e:
        return jsonify({"message": f"Failed to get problem statement: {e}"}), 500
