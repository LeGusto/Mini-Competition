#!/bin/bash

# Railway startup script for Mini-Competition platform
set -e

echo "🚀 Starting Mini-Competition Platform on Railway..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
until pg_isready -h postgres -p 5432 -U postgres; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "✅ Database is ready!"

# Initialize database if needed
echo "🔧 Setting up database..."
cd /app/backend
python setup_db.py

# Start the application
echo "🎯 Starting Flask application..."
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 main:app
