#!/bin/bash

echo "========================================"
echo "TradeRiser Setup Script for Unix/Linux"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed"
    echo "Please install Python 3 from your package manager or https://python.org"
    exit 1
fi

echo "✓ Python 3 is installed"
echo

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to create virtual environment"
    exit 1
fi
echo "✓ Virtual environment created"
echo

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to activate virtual environment"
    exit 1
fi
echo "✓ Virtual environment activated"
echo

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip
echo "✓ Pip upgraded"
echo

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to install requirements"
    exit 1
fi
echo "✓ Requirements installed"
echo

# Copy environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp ".env.example" ".env"
    echo "✓ .env file created"
    echo
    echo "IMPORTANT: Please edit .env file and add your API keys!"
    echo "Required: ALPHA_VANTAGE_API_KEY"
    echo "Optional: TWITTER_API_KEY, FRED_API_KEY"
    echo
else
    echo "✓ .env file already exists"
    echo
fi

# Check if Redis is available (optional)
if ! command -v redis-server &> /dev/null; then
    echo "⚠ Redis is not installed (optional for caching)"
    echo "You can install Redis from your package manager"
    echo "The application will use in-memory caching instead"
    echo
else
    echo "✓ Redis is available"
    echo
fi

echo "========================================"
echo "Setup completed successfully!"
echo "========================================"
echo
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Run: python run.py"
echo "3. Open http://localhost:5000 in your browser"
echo
echo "For API keys:"
echo "- Alpha Vantage: https://www.alphavantage.co/support/#api-key"
echo "- Twitter: https://developer.twitter.com/"
echo "- FRED: https://fred.stlouisfed.org/docs/api/api_key.html"
echo