#!/bin/bash

# Loglify Setup Script

echo "🚀 Setting up Loglify..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from database import init_db; init_db(); print('Database initialized!')"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your TELEGRAM_TOKEN and OPENAI_API_KEY"
echo "2. Run: python3 run.py"
echo "   Or: uvicorn main:app --reload (for API only)"
echo "   Or: python3 telegram_bot.py (for bot only)"
echo "   Or: python3 cli.py --help (for CLI)"

