#!/usr/bin/env python3
"""
Railway Deployment Startup Script
Alternative entry point for Railway deployment
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Start the Flask application using waitress"""
    try:
        # Import waitress and the Flask app
        from waitress import serve
        from application import application
        
        # Get port from environment (Railway sets this)
        port = int(os.environ.get('PORT', 8000))
        host = '0.0.0.0'
        
        print(f"Starting TradeRiser AI server on {host}:{port}")
        
        # Start the server
        serve(application, host=host, port=port)
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure waitress and all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"Server startup error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()