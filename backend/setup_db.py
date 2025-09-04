#!/usr/bin/env python3
"""
Database setup script for Mini-Competition
This script will create the database and tables for the application.
"""

import psycopg2
import os
import sys
from pathlib import Path
from services.auth import AuthService
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD


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

        # Execute each statement separately using a more robust parser
        statements = []

        # Split by semicolon and process each statement
        raw_statements = sql_content.split(";")

        for statement in raw_statements:
            # Clean up the statement
            statement = statement.strip()

            # Skip empty statements and comments
            if not statement or statement.startswith("--"):
                continue

            # Remove single-line comments
            lines = statement.split("\n")
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("--"):
                    cleaned_lines.append(line)

            if cleaned_lines:
                final_statement = " ".join(cleaned_lines)
                if final_statement.strip():
                    statements.append(final_statement)

        # Execute each statement
        for i, statement in enumerate(statements):
            if statement.strip():
                try:
                    print(f"Executing statement {i+1}/{len(statements)}...")
                    cursor.execute(statement)
                except Exception as e:
                    print(f"❌ Error executing statement {i+1}: {statement[:100]}...")
                    print(f"Error: {e}")
                    raise

        print("✅ Tables created successfully!")

        # Create a test user with proper password hashing
        import bcrypt

        auth_service = AuthService()
        auth_service.create_user("admin", "admin123")

        print("✅ Default admin user created (username: admin, password: admin123)")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error setting up tables: {e}")
        sys.exit(1)


def main():
    """Main setup function"""
    print("🚀 Setting up Mini-Competition Database...")
    print("=" * 50)

    # Check if PostgreSQL is running
    try:
        psycopg2.connect(
            host=DB_HOST, database="postgres", user=DB_USER, password=DB_PASSWORD
        )
    except Exception as e:
        print("❌ Cannot connect to PostgreSQL!")
        print("Make sure PostgreSQL is running and accessible with:")
        print(f"  - Host: {DB_HOST}")
        print(f"  - User: {DB_USER}")
        print(f"  - Password: {DB_PASSWORD}")
        print(f"Error: {e}")
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
    print("  Password: admin123")


if __name__ == "__main__":
    main()
