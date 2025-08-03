FROM python:3.10-slim

# Set working directory to backend folder
WORKDIR /app/backend

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the backend code
COPY . .

# Make the startup script executable
RUN chmod +x docker/start.sh

# Expose the port the app runs on
EXPOSE 5000

# Command to run the startup script
CMD ["bash", "docker/start.sh"]