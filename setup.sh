#!/bin/bash

# Mini-Competition Database Setup Script

echo "🚀 Setting up Mini-Competition Database..."
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Please run this script from the Mini-Competition root directory"
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed or not in PATH"
    echo "Please install PostgreSQL first:"
    echo "  - Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
    echo "  - macOS: brew install postgresql"
    echo "  - Arch: sudo pacman -S postgresql"
    exit 1
fi

# Check if PostgreSQL service is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "❌ PostgreSQL service is not running"
    echo "Please start PostgreSQL:"
    echo "  - Ubuntu/Debian: sudo systemctl start postgresql"
    echo "  - macOS: brew services start postgresql"
    echo "  - Arch: sudo systemctl start postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Install Python dependencies if needed
if [ ! -d "backend/venv" ]; then
    echo "📦 Setting up Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "✅ Python virtual environment already exists"
fi

# Run the database setup script
echo "🗄️  Setting up database..."
cd backend
source venv/bin/activate
python setup_db.py

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "To start the backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "To start the frontend:"
echo "  cd frontend"
echo "  npm install"
echo "  npm run dev"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: admin123" 