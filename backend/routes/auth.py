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

    user = AuthService().get_user_by_username(username)
    if not user:
        return jsonify({"message": "Invalid username or password"}), 401

    if not AuthService().verify_password(password, user[2]):
        return jsonify({"message": "Invalid username or password"}), 401

    token = AuthService().generate_token(user[0], user[1], user[3])
    return jsonify({"message": "Login successful", "token": token, "user": user}), 200


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Register a user"""
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    user = AuthService().create_user(username, password)
    return jsonify({"message": "User created successfully", "user": user}), 201


@auth_bp.route("/auth/verify", methods=["POST"])
def verify_token():
    """Verify a token"""
    data = request.get_json()

    if not data or "token" not in data:
        return jsonify({"valid": False, "error": "Token required"}), 400

    try:
        payload = AuthService().verify_token(data["token"])
        return jsonify({"valid": True, "user": payload}), 200
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 401
