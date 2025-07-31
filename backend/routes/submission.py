from flask import Blueprint, request, jsonify
from models.solution import Solution
from werkzeug.utils import secure_filename
from services.decorators import require_auth
import os
import uuid
import requests

submission_bp = Blueprint("submission", __name__)

UPLOAD_FOLDER = "tmp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@submission_bp.route("/submission/submit", methods=["POST"])
@require_auth
def submit_solution():
    """Submit a solution to a problem"""

    # Check for required fields and file
    if (
        "file" not in request.files
        or "problem_id" not in request.form
        or "language" not in request.form
    ):
        return (
            jsonify({"message": "Missing required fields: file, problem_id, language"}),
            400,
        )

    file = request.files["file"]
    problem_id = request.form["problem_id"]
    language = request.form["language"]

    # Sanitize and save the file
    original_filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    saved_filename = f"{unique_id}_{original_filename}"
    file_path = os.path.join(UPLOAD_FOLDER, saved_filename)
    file.save(file_path)

    # Validate using Pydantic
    data = {
        "file_name": saved_filename,
        "problem_id": problem_id,
        "language": language,
    }
    try:
        solution = Solution(**data)
    except Exception as e:
        os.remove(file_path)
        return jsonify({"message": str(e)}), 400

    # Forward to judge server
    judge_url = "http://localhost:3000/judge"
    with open(file_path, "rb") as f:
        files = {"code": (saved_filename, f)}
        payload = {"problemID": problem_id, "language": language}
        try:
            judge_response = requests.post(judge_url, files=files, data=payload)
            judge_response.raise_for_status()
        except requests.RequestException as e:
            print(e)
            os.remove(file_path)
            return jsonify({"message": f"Failed to contact judge server: {e}"}), 500

    os.remove(file_path)
    return jsonify(judge_response.json()), judge_response.status_code


@submission_bp.route("/submission/status/<submission_id>", methods=["GET"])
@require_auth
def get_submission_status(submission_id):
    """Proxy to the judge server to get submission status"""
    try:
        judge_url = "http://localhost:3000/submission/" + submission_id
        response = requests.get(judge_url, params={"submission_id": submission_id})
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({"message": f"Failed to get submission status: {e}"}), 500
