from flask import Blueprint, jsonify
from services.contest import ContestService

contest_bp = Blueprint("contest", __name__)
contest_service = ContestService()


@contest_bp.route("/contest/<contest_id>", methods=["GET"])
def get_contest(contest_id):
    """Get a contest"""
    print("contest_id===", contest_id, flush=True)
    problemData = contest_service.get_problem_data(contest_id)
    print("problem DATA===\n", problemData, flush=True)
    print("problem DATA===\n", problemData, flush=True)
    return jsonify(problemData)
