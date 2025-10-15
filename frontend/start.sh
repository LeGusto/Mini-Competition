#!/bin/bash
set -e

echo "🚀 Starting Mini-Competition Frontend..."

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Build the frontend
echo "🔨 Building frontend..."
npm run build

# Start the preview server
echo "⚡ Starting SvelteKit preview server..."
exec npm run preview -- --port 3000 --host 0.0.0.0
