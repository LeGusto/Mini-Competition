from flask import Blueprint, request, jsonify
from models.solution import Solution
from werkzeug.utils import secure_filename
from services.decorators import require_auth
from services.submission import SubmissionService
import os
import uuid
import requests

submission_bp = Blueprint("submission", __name__)
submission_service = SubmissionService()


@submission_bp.route("/submission/submit", methods=["POST"])
@require_auth
def submit_solution():
    """Submit a solution to a problem"""
    file = request.files.get("file")
    problem_id = request.form.get("problem_id")
    language = request.form.get("language")
    user_id = request.user_id

    print(file, problem_id, language, user_id)

    try:
        result = submission_service.submit_solution(file, problem_id, language, user_id)
        return jsonify(result["data"]), result["status_code"]
    except Exception as e:
        print(e)
        return jsonify({"message": str(e)}), 400


@submission_bp.route("/submission/status/<submission_id>", methods=["GET"])
@require_auth
def get_submission_status(submission_id):
    """Proxy to the judge server to get submission status"""
    try:
        result = submission_service.get_submission_status(submission_id)
        return jsonify(result["data"]), result["status_code"]
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@submission_bp.route("/submission/all", methods=["GET"])
@require_auth
def get_user_submissions():
    """Get all submissions for the current user"""
    try:
        user_id = request.user_id
        result = submission_service.get_user_submissions(user_id)
        return jsonify(result["data"]), result["status_code"]
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@submission_bp.route("/submission/result", methods=["POST"])
def receive_judge_result():
    """Receive results from the judge server"""
    try:
        data = request.get_json()
        print(f"Received callback data: {data}")

        if not data:
            return jsonify({"message": "No data received"}), 400

        # Extract required fields
        submission_id = data.get("submission_id")
        problem_id = data.get("problem_id")
        status = data.get("status")
        judge_response = data.get("judge_response", {})
        execution_time = data.get("execution_time")
        memory_used = data.get("memory_used")

        print(f"Received callback data: {data}")
        print(
            f"Extracted execution_time: {execution_time} (type: {type(execution_time)})"
        )
        print(f"Extracted memory_used: {memory_used} (type: {type(memory_used)})")
        print(
            f"Extracted fields: submission_id={submission_id}, problem_id={problem_id}, status={status}"
        )

        if not submission_id or not problem_id or not status:
            return jsonify({"message": "Missing required fields"}), 400

        # Update the submission in the database
        result = submission_service.update_submission_result(
            submission_id,
            problem_id,
            status,
            judge_response,
            execution_time,
            memory_used,
        )

        return jsonify(result["data"]), result["status_code"]

    except Exception as e:
        print(f"Error receiving judge result: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"message": str(e)}), 500
