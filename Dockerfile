# Dockerfile for Mini-Competition (connects to external Mini-Judge)
FROM python:3.11-slim

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy and install frontend dependencies
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# Create startup script
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

echo "🚀 Starting Mini-Competition Platform..."

# Start backend
cd /app
echo "🐍 Starting Flask backend..."
python main.py &
BACKEND_PID=\$!

# Wait for backend to be ready
echo "⏳ Waiting for backend..."
sleep 10

# Start frontend
cd /app/frontend
echo "⚡ Starting SvelteKit frontend..."
npm run preview -- --port 3000 --host 0.0.0.0 &
FRONTEND_PID=\$!

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down services..."
    kill \$BACKEND_PID \$FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Trap signals for graceful shutdown
trap cleanup SIGTERM SIGINT

# Wait for all services
wait \$BACKEND_PID \$FRONTEND_PID
EOF

RUN chmod +x /app/start.sh

# Create necessary directories
RUN mkdir -p /app/tmp

# Expose ports
EXPOSE 3000 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:5000/healthcheck || exit 1

# Start services
CMD ["/app/start.sh"]
