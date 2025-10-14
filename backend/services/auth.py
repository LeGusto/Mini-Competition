import psycopg2
import psycopg2.extras
import bcrypt
import os
import jwt
import datetime
from config import (
    JWT_SECRET,
    JWT_EXPIRATION,
)
from services.connection import get_connection


class AuthService:
    """
    Authentication service
    """

    def __init__(self):
        self.JWT_SECRET = JWT_SECRET
        self.JWT_EXPIRATION = JWT_EXPIRATION
        self.conn = get_connection()
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def hash_password(self, password):
        """
        Hash a password
        """
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def generate_token(self, user_id, username, role="user"):
        """
        Generate a JWT token
        """
        payload = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=self.JWT_EXPIRATION),
            "iat": datetime.datetime.now(datetime.timezone.utc),
        }
        return jwt.encode(payload, self.JWT_SECRET, algorithm="HS256")

    def verify_token(self, token):
        """
        Verify a JWT token
        """
        try:
            payload = jwt.decode(token, self.JWT_SECRET, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")

    def verify_password(self, password, hashed_password):
        """
        Verify a password against a hashed password
        """
        # Handle both string and bytes for hashed_password
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode()
        return bcrypt.checkpw(password.encode(), hashed_password)

    def create_user(self, username, password):
        """
        Create a new user
        """
        if self.get_user(username):
            raise Exception("User already exists")

        try:
            hashed = self.hash_password(password)
            self.cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed.decode()),
            )
            self.conn.commit()
            return self.get_user(username)
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_user(self, username):
        """
        Get a user by username
        """
        self.cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return self.cursor.fetchone()

    def get_user_by_username(self, username):
        """
        Get a user by username (alias for get_user for compatibility)
        """
        return self.get_user(username)

    def delete_user(self, username):
        """
        Delete a user by username
        """
        user = self.get_user(username)
        if not user:
            raise Exception("User not found")

        try:
            # Delete related submissions first (due to foreign key constraint)
            self.cursor.execute(
                "DELETE FROM submissions WHERE user_id = %s", (user["id"],)
            )
            # Delete the user
            self.cursor.execute("DELETE FROM users WHERE username = %s", (username,))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_user_by_id(self, user_id):
        """
        Delete a user by ID
        """
        try:
            # Delete related submissions first (due to foreign key constraint)
            self.cursor.execute(
                "DELETE FROM submissions WHERE user_id = %s", (user_id,)
            )
            # Delete the user
            self.cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def list_users(self):
        """
        List all users (for admin purposes)
        """
        self.cursor.execute(
            "SELECT id, username, role, created_at FROM users ORDER BY id"
        )
        return self.cursor.fetchall()

    def authenticate_user(self, username, password):
        """
        Authenticate a user and return a JWT token
        """
        user = self.get_user(username)
        if user and self.verify_password(password, user["password"]):
            return self.generate_token(user["id"], user["username"], user["role"])
        else:
            raise Exception("Invalid username or password")

    def login_user(self, username, password, timezone):
        """
        Complete login flow - validates credentials and returns user data with token
        """
        if not username or not password:
            raise Exception("Username and password are required")

        user = self.get_user(username)
        if not user:
            raise Exception("Invalid username or password")

        if not self.verify_password(password, user["password"]):
            raise Exception("Invalid username or password")

        token = self.generate_token(user["id"], user["username"], user["role"])

        return {
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "timezone": timezone,
            },
        }

    def register_user(self, username, password, timezone=None):
        """
        Complete registration flow - creates new user and returns user data with token
        """
        if not username or not password:
            raise Exception("Username and password are required")

        user = self.create_user(username, password)
        token = self.generate_token(user["id"], user["username"], user["role"])

        return {
            "message": "User created successfully",
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "timezone": timezone,
            },
        }

    def verify_user_token(self, token):
        """
        Complete token verification flow - validates token and returns user data
        """
        if not token:
            raise Exception("Token required")

        payload = self.verify_token(token)

        return {"valid": True, "user": payload}
