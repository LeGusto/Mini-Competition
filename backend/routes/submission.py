from flask import Blueprint, request, jsonify
from models.solution import Solution
from werkzeug.utils import secure_filename
from services.decorators import require_auth
from services.submission import SubmissionService
import os
import uuid
import requests
from datetime import datetime

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

        if not submission_id or not problem_id or not status:
            return jsonify({"message": "Missing required fields"}), 400

        # Update the submission with judge results
        result = submission_service.update_submission_result(
            submission_id,
            problem_id,
            status,
            judge_response,
            execution_time,
            memory_used,
        )

        if result["status_code"] == 200:
            print(f"✅ Submission {submission_id} updated successfully")

            # Check for all active contests where the user is registered and the problem exists
            print(f"🔍 Checking for active contests for problem {problem_id}...")

            try:
                # Get submission details first to get user_id
                submission_details = submission_service.get_submission_details(
                    submission_id
                )

                if not submission_details:
                    print(
                        f"❌ Could not get submission details for submission {submission_id}"
                    )
                    return (
                        jsonify(
                            {
                                "message": "Submission processed but contest tracking failed"
                            }
                        ),
                        200,
                    )

                user_id = submission_details["user_id"]
                print(f"👤 User ID: {user_id}")

                # Get all active contests for this user and problem
                contests = (
                    submission_service.get_all_active_contests_for_user_and_problem(
                        user_id, problem_id
                    )
                )

                if contests:
                    print(
                        f"🎯 Found {len(contests)} active contests for this submission"
                    )

                    # Determine if submission was accepted
                    is_accepted = False
                    score = 0
                    penalty_time = 0

                    if status in ["completed", "accepted"] and judge_response:
                        # Check if all test cases passed
                        summary = judge_response.get("summary", {})
                        failed = summary.get("failed", 0)
                        is_accepted = failed == 0

                        if is_accepted:
                            score = 100  # Standard score for accepted submissions
                            print(f"✅ Submission accepted with score {score}")
                        else:
                            # Calculate penalty time (you can adjust this logic)
                            penalty_time = 20  # 20 minutes penalty for wrong submission
                            print(
                                f"❌ Submission failed, penalty time: {penalty_time} minutes"
                            )

                    # Create contest submission entries for ALL matching contests
                    print(
                        f"📝 Creating contest submission entries for {len(contests)} contests..."
                    )
                    submission_time = submission_details["submission_time"]

                    for contest in contests:
                        print(
                            f"   📋 Processing contest: {contest['name']} (ID: {contest['id']})"
                        )

                        contest_submission_id = (
                            submission_service.create_contest_submission(
                                contest["id"],
                                user_id,
                                problem_id,
                                submission_id,
                                submission_time,
                                is_accepted,
                                score,
                                penalty_time,
                            )
                        )

                        if contest_submission_id:
                            print(
                                f"   ✅ Created contest submission {contest_submission_id} for contest {contest['id']}"
                            )
                        else:
                            print(
                                f"   ❌ Failed to create contest submission for contest {contest['id']}"
                            )
                else:
                    print(
                        f"ℹ️ Submission {submission_id} was not made for any active contests where user is registered"
                    )
            except Exception as e:
                print(f"❌ Error processing contest submission logic: {e}")
                # Don't fail the entire callback if contest logic fails
                pass

        return jsonify(result["data"]), result["status_code"]

    except Exception as e:
        print(f"Error processing judge callback: {e}")
        return jsonify({"message": str(e)}), 500
