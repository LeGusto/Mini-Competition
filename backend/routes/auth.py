from flask import Blueprint, request, jsonify, Response
from models.solution import Solution
from werkzeug.utils import secure_filename
from services.decorators import require_auth
from services.auth import AuthService
import os
import uuid
import requests
import pathlib

auth_bp = Blueprint("auth", __name__)

auth_service = AuthService()


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Login a user"""
    data = request.json
    username = data.get("username")
    password = data.get("password")

    try:
        result = auth_service.login_user(username, password)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 401


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Register a user"""
    data = request.json
    username = data.get("username")
    password = data.get("password")

    try:
        result = auth_service.register_user(username, password)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 400


@auth_bp.route("/auth/verify", methods=["POST"])
def verify_token():
    """Verify a token"""
    data = request.get_json()
    token = data.get("token") if data else None

    try:
        result = auth_service.verify_user_token(token)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 401
