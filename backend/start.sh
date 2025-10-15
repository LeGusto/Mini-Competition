#!/bin/bash
set -e

echo "🚀 Starting Mini-Competition Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Start Flask backend
echo "🐍 Starting Flask backend..."
exec python main.py
