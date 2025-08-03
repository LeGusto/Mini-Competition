FROM node:20-slim

WORKDIR /app/frontend

# Copy package files (including package-lock.json)
COPY package*.json ./

# Install dependencies WITHOUT deleting package-lock.json
RUN npm ci 
# Copy the frontend code
COPY . .

# Expose the port the app runs on
EXPOSE 5173

# Command to run the application with host binding
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
