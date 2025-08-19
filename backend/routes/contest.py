from flask import Blueprint, jsonify, request
from services.contest import ContestService
from services.decorators import require_auth

contest_bp = Blueprint("contest", __name__)
contest_service = ContestService()


@contest_bp.route("/contests", methods=["GET"])
@require_auth
def get_contests():
    """Get all contests"""
    try:
        result = contest_service.get_contests()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@contest_bp.route("/contest", methods=["POST"])
@require_auth
def create_contest():
    """Create a new contest"""
    try:
        data = request.json
        name = data.get("name")
        description = data.get("description", "")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        problems = data.get("problems", [])

        if not name or not start_time or not end_time:
            return (
                jsonify({"message": "Name, start_time, and end_time are required"}),
                400,
            )

        result = contest_service.create_contest(
            name, description, start_time, end_time, problems
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@contest_bp.route("/contest/<contest_id>", methods=["GET"])
def get_contest(contest_id):
    """Get a contest"""
    print("contest_id===", contest_id, flush=True)
    problemData = contest_service.get_problem_data(contest_id)
    print("problem DATA===\n", problemData, flush=True)
    print("problem DATA===\n", problemData, flush=True)
    return jsonify(problemData)
