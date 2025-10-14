from functools import wraps
from flask import request, jsonify
from services.auth import AuthService


def get_token_from_request():
    """
    Get the token from the request headers
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    # Handle Bearer token format
    if auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix

    return auth_header


def require_auth(f):
    """
    Decorator to verify a JWT token
    add user_id and username to the request object
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            print(f"[AUTH DEBUG] No token found. Headers: {dict(request.headers)}")
            return jsonify({"message": "Token is missing"}), 401
        try:
            payload = AuthService().verify_token(token)

            if payload["user_id"] is None:
                return jsonify({"message": "Unauthorized"}), 401
            else:
                request.user_id = payload["user_id"]
                request.username = payload["username"]

            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"message": str(e)}), 401

    return decorated


def require_admin(f):
    """
    Decorator to verify a JWT token
    add user_id and username to the request object
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        try:
            payload = AuthService().verify_token(token)

            if payload["user_id"] is None:
                return jsonify({"message": "Unauthorized"}), 401
            else:
                request.user_id = payload["user_id"]
                request.username = payload["username"]

            if payload["role"] != "admin":
                return jsonify({"message": "Unauthorized"}), 401

            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"message": str(e)}), 401

    return decorated
