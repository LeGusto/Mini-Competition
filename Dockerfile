# Use Python base image with Node.js
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

WORKDIR /app

# Copy backend requirements and install
COPY backend/requirements.txt ./backend/
RUN pip install -r backend/requirements.txt

# Copy frontend package files and install dependencies
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm ci

# Copy all source code
WORKDIR /app
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Build frontend for production
WORKDIR /app/frontend
RUN npm run build

# Copy built frontend to backend static folder
WORKDIR /app
RUN cp -r frontend/build/* backend/static/ || (mkdir -p backend/static && cp -r frontend/build/* backend/static/)

WORKDIR /app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:5000/healthcheck || exit 1

CMD ["bash", "-c", "cd backend && python setup_db.py && exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 main:app"]
