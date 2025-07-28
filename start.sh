#!/bin/bash

# Start script for TradeRiser AI Flask Application
echo "Starting TradeRiser AI Platform..."

# Set environment variables
export FLASK_APP=application.py
export FLASK_ENV=production
export PORT=${PORT:-8000}

# Install dependencies if not already installed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start the application with Waitress
echo "Starting Flask application on port $PORT..."
waitress-serve --host=0.0.0.0 --port=$PORT application:application