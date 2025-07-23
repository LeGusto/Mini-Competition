from flask import Blueprint, request, jsonify
from models.solution import Solution
from werkzeug.utils import secure_filename
import os
import uuid
import requests
import pathlib

general_bp = Blueprint("general", __name__)


@general_bp.route("/general/problems", methods=["GET"])
def get_problems():
    judge_url = "http://localhost:3000/problems"

    try:
        judge_response = requests.get(judge_url)
        judge_response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"message": f"Failed to contact judge server: {e}"}), 500

    return jsonify({"problems": judge_response.json()["problems"]})
