from flask import Blueprint, request, jsonify, Response
from models.solution import Solution
from werkzeug.utils import secure_filename
from services.decorators import require_auth
from services.general import GeneralService
import os
import uuid
import requests
import pathlib

general_bp = Blueprint("general", __name__)
general_service = GeneralService()


@general_bp.route("/general/problems", methods=["GET"])
@require_auth
def get_problems():
    """Proxy to the judge server to get problem ids"""
    try:
        result = general_service.get_problems()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@general_bp.route("/general/problem/<problem_id>/statement", methods=["GET"])
@require_auth
def get_problem_statement(problem_id):
    """Proxy to the judge server to get problem statement PDF"""
    try:
        result = general_service.get_problem_statement(problem_id)

        # Stream the PDF response
        return Response(
            result["content"],
            content_type=result["content_type"],
            headers={"Content-Disposition": result["content_disposition"]},
        )
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@general_bp.route("/general/problem/<problem_id>/metadata", methods=["GET"])
@require_auth
def get_problem_metadata(problem_id):
    """Get metadata for a specific problem"""
    try:
        result = general_service.get_problem_metadata(problem_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@general_bp.route("/healthcheck", methods=["GET"])
def healthcheck():
    try:
        result = general_service.health_check()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
