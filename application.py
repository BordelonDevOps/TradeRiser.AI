#!/usr/bin/env python3
"""
AWS Amplify Entry Point for TradeRiser Platform
This file serves as the main application entry point for AWS deployment
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def load_environment():
    """Load environment variables for AWS deployment"""
    # Set default environment variables for production
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('HOST', '0.0.0.0')
    # Let AWS Amplify handle port assignment automatically
    
    # Load .env file if it exists
    env_file = project_root / '.env'
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            pass

# Load environment
load_environment()

# Import the Flask application
try:
    from new_traderiser_platform import app
    
    # AWS Amplify expects the application object to be named 'application'
    application = app
    
    if __name__ == '__main__':
        # For local testing
        port = int(os.environ.get('PORT', 5000))
        application.run(host='0.0.0.0', port=port, debug=False)
        
except ImportError as e:
    print(f"Error importing application: {e}")
    sys.exit(1)