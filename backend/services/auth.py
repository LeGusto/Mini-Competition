import psycopg2
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
        self.cursor = self.conn.cursor(dictionary=True)
        self.JWT_SECRET = os.getenv("JWT_SECRET")
        self.JWT_EXPIRATION = os.getenv("JWT_EXPIRATION")

    def hash_password(self, password):
        """
        Hash a password
        """
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def generate_token(self, username, user_id):
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
        return bcrypt.checkpw(password.encode(), hashed_password)

    def create_user(self, username, password):
        """
        Create a new user
        """

        if self.get_user(username):
            raise Exception("User already exists")

        self.cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, self.hash_password(password)),
        )
        self.conn.commit()
        return self.get_user(username)

    def get_user(self, username):
        """
        Get a user by username
        """
        self.cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return self.cursor.fetchone()

    def authenticate_user(self, username, password):
        """
        Authenticate a user and return a JWT token
        """
        user = self.get_user(username)
        if user and self.verify_password(password, user["password"].encode()):
            return self.generate_token(username, user["id"])
        else:
            raise Exception("Invalid username or password")
