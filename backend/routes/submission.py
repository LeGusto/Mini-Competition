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

    try:
        result = submission_service.submit_solution(file, problem_id, language, user_id)
        return jsonify(result["data"]), result["status_code"]
    except Exception as e:
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
