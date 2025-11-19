#!/bin/bash
set -e

echo "🚀 Setting up OriginStack..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install it first:"
    echo "   sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

echo "✅ PostgreSQL found"

# Create database and user
echo "📦 Creating database and user..."
sudo -u postgres psql << EOF
SELECT 'CREATE DATABASE originstack' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'originstack')\gexec
SELECT 'CREATE USER originstack WITH PASSWORD ''originstack''' WHERE NOT EXISTS (SELECT FROM pg_user WHERE usename = 'originstack')\gexec
GRANT ALL PRIVILEGES ON DATABASE originstack TO originstack;
EOF

echo "✅ Database created"

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "⚙️  Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file"
else
    echo "⚠️  .env file already exists, skipping..."
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "To start the backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Then visit http://localhost:8000/docs for API documentation"
