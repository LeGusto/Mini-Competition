#!/bin/bash

# Run database setup
echo "Setting up database..."
python setup_db.py

# Start the Flask application
echo "Starting Flask application..."
python main.py 