import psycopg2
import psycopg2.extras
import bcrypt
import os
import jwt
import datetime


class AuthService:
    """
    Authentication service
    """

    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            database="mini_competition_db",
            user="postgres",
            password="postgres",
        )
        # Use RealDictCursor for dictionary-like access
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
        self.JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "3600"))

    def hash_password(self, password):
        """
        Hash a password
        """
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def generate_token(self, user_id, username):
        """
        Generate a JWT token
        """
        payload = {
            "user_id": user_id,
            "username": username,
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
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    def create_user(self, username, password):
        """
        Create a new user
        """
        if self.get_user(username):
            raise Exception("User already exists")

        hashed = self.hash_password(password)
        self.cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed.decode()),
        )
        self.conn.commit()
        return self.get_user(username)

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

        # Delete related submissions first (due to foreign key constraint)
        self.cursor.execute("DELETE FROM submissions WHERE user_id = %s", (user["id"],))

        # Delete the user
        self.cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        self.conn.commit()

        return True

    def delete_user_by_id(self, user_id):
        """
        Delete a user by ID
        """
        # Delete related submissions first (due to foreign key constraint)
        self.cursor.execute("DELETE FROM submissions WHERE user_id = %s", (user_id,))

        # Delete the user
        self.cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        self.conn.commit()

        return True

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
        if user and self.verify_password(password, user["password"].encode()):
            return self.generate_token(user["id"], user["username"])
        else:
            raise Exception("Invalid username or password")
