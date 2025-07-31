from functools import wraps
from flask import request, jsonify
from services.auth import AuthService


def get_token_from_request():
    """
    Get the token from the request headers
    """
    return request.headers.get("Authorization")


def require_auth(f):
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
