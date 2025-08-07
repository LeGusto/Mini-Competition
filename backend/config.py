import os

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mini_competition_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Judge service configuration
JUDGE_HOST = os.getenv("JUDGE_HOST", "localhost")
JUDGE_PORT = os.getenv("JUDGE_PORT", "3000")

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "3600"))

# Flask configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

# Database connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Judge service URL
JUDGE_BASE_URL = f"http://{JUDGE_HOST}:{JUDGE_PORT}"
