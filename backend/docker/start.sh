#!/bin/bash
set -e  # Exit on any error

# Run database setup
echo "Setting up database..."
if ! python setup_db.py; then
    echo "❌ Database setup failed! Exiting..."
    exit 1
fi

# Start the Flask application
echo "Starting Flask application..."
exec python main.py 