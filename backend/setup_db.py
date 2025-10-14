#!/usr/bin/env python3
"""
Database setup script for Mini-Competition
This script will create the database and tables for the application.
"""

import psycopg2
import os
import sys
import time
from pathlib import Path
from services.auth import AuthService
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD


def wait_for_postgres(max_retries=30, delay=1):
    """Wait for PostgreSQL to be ready"""
    print("⏳ Waiting for PostgreSQL to be ready...")
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, database="postgres", user=DB_USER, password=DB_PASSWORD
            )
            conn.close()
            print("✅ PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError as e:
            if i < max_retries - 1:
                print(
                    f"   Attempt {i+1}/{max_retries}: PostgreSQL not ready yet, waiting {delay}s..."
                )
                time.sleep(delay)
            else:
                print(
                    f"❌ PostgreSQL failed to become ready after {max_retries} attempts"
                )
                print(f"   Last error: {e}")
                return False
    return False


def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=DB_HOST, database="postgres", user=DB_USER, password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = 'mini_competition_db'"
        )
        exists = cursor.fetchone()

        if not exists:
            print("Creating database 'mini_competition_db'...")
            cursor.execute("CREATE DATABASE mini_competition_db")
            print("✅ Database created successfully!")
        else:
            print("✅ Database 'mini_competition_db' already exists!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error creating database: {e}")
        sys.exit(1)


def setup_tables():
    """Create tables in the database"""
    try:
        # Connect to mini_competition_db
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Read and execute the SQL setup script
        script_path = Path(__file__).parent / "utils" / "db_setup.sql"

        if not script_path.exists():
            print(f"❌ SQL script not found at {script_path}")
            sys.exit(1)

        print("Setting up database tables...")

        with open(script_path, "r") as f:
            sql_content = f.read()

        # Remove comments from SQL
        lines = sql_content.split("\n")
        cleaned_lines = []
        for line in lines:
            # Remove inline comments
            if "--" in line:
                line = line[: line.index("--")]
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        cleaned_sql = "\n".join(cleaned_lines)

        # Split by semicolon to get individual statements
        raw_statements = cleaned_sql.split(";")
        statements = []

        for statement in raw_statements:
            statement = statement.strip()
            if statement:
                statements.append(statement + ";")

        print(f"Found {len(statements)} SQL statements to execute")

        # Execute each statement
        for i, statement in enumerate(statements, 1):
            try:
                print(f"Executing statement {i}/{len(statements)}...")
                cursor.execute(statement)
                conn.commit()
            except Exception as e:
                print(f"❌ Error executing statement {i}:")
                print(f"   Statement preview: {statement[:150]}...")
                print(f"   Error: {e}")
                raise

        print("✅ Tables created successfully!")

        # Create or update admin user
        import bcrypt

        try:
            auth_service = AuthService()

            # Check if admin user exists
            existing_admin = auth_service.get_user("admin")

            if existing_admin:
                print("ℹ️  Admin user already exists, updating password and role...")
                # Update the password and role directly
                hashed = auth_service.hash_password("admin")
                cursor.execute(
                    "UPDATE users SET password = %s, role = %s WHERE username = %s",
                    (hashed.decode(), "admin", "admin"),
                )
                conn.commit()
                print(
                    "✅ Admin user updated (username: admin, password: admin, role: admin)"
                )
            else:
                # Create new admin user
                auth_service.create_user("admin", "admin")
                # Update role to admin
                cursor.execute(
                    "UPDATE users SET role = %s WHERE username = %s",
                    ("admin", "admin"),
                )
                conn.commit()
                print(
                    "✅ Default admin user created (username: admin, password: admin, role: admin)"
                )
        except Exception as e:
            print(f"⚠️  Warning: Could not create/update admin user: {e}")
            import traceback

            traceback.print_exc()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error setting up tables: {e}")
        sys.exit(1)


def main():
    """Main setup function"""
    print("🚀 Setting up Mini-Competition Database...")
    print("=" * 50)

    # Wait for PostgreSQL to be ready
    if not wait_for_postgres():
        print("❌ Cannot connect to PostgreSQL!")
        print("Make sure PostgreSQL is running and accessible with:")
        print(f"  - Host: {DB_HOST}")
        print(f"  - User: {DB_USER}")
        print(f"  - Password: {DB_PASSWORD}")
        sys.exit(1)

    create_database()
    setup_tables()

    print("=" * 50)
    print("🎉 Database setup completed successfully!")
    print("\nYou can now run your Flask backend:")
    print("  cd backend")
    print("  python main.py")
    print("\nDefault admin credentials:")
    print("  Username: admin")
    print("  Password: admin")


if __name__ == "__main__":
    main()
