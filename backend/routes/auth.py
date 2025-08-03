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


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Login a user"""
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    auth_service = AuthService()
    user = auth_service.get_user(username)
    if not user:
        return jsonify({"message": "Invalid username or password"}), 401

    if not auth_service.verify_password(password, user["password"]):
        return jsonify({"message": "Invalid username or password"}), 401

    token = auth_service.generate_token(user["id"], user["username"])
    return (
        jsonify(
            {
                "message": "Login successful",
                "token": token,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                },
            }
        ),
        200,
    )


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Register a user"""
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    try:
        auth_service = AuthService()
        user = auth_service.create_user(username, password)
        return (
            jsonify(
                {
                    "message": "User created successfully",
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "role": user["role"],
                    },
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"message": str(e)}), 400


@auth_bp.route("/auth/verify", methods=["POST"])
def verify_token():
    """Verify a token"""
    data = request.get_json()

    if not data or "token" not in data:
        return jsonify({"valid": False, "error": "Token required"}), 400

    try:
        auth_service = AuthService()
        payload = auth_service.verify_token(data["token"])
        return jsonify({"valid": True, "user": payload}), 200
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 401
