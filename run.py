#!/usr/bin/env python3
"""
TradeRiser - Enhanced Professional Investment Platform
Main application runner with environment setup and error handling
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def load_environment():
    """Load environment variables from .env file if it exists"""
    env_file = project_root / '.env'
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("✓ Environment variables loaded from .env file")
        except ImportError:
            print("⚠ python-dotenv not installed. Install with: pip install python-dotenv")
            print("⚠ Falling back to system environment variables")
    else:
        print("⚠ .env file not found. Copy .env.example to .env and configure your API keys")

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'flask', 'flask_cors', 'pandas', 'numpy', 'requests', 
        'yfinance', 'alpha_vantage', 'redis', 'ortools'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('_', '-').replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    print("✓ All required dependencies are installed")
    return True

def check_api_keys():
    """Check if required API keys are configured"""
    required_keys = ['ALPHA_VANTAGE_API_KEY']
    optional_keys = ['TWITTER_API_KEY', 'FRED_API_KEY']
    
    missing_required = []
    for key in required_keys:
        if not os.getenv(key):
            missing_required.append(key)
    
    if missing_required:
        print(f"❌ Missing required API keys: {', '.join(missing_required)}")
        print("Please configure them in your .env file")
        return False
    
    print("✓ Required API keys are configured")
    
    missing_optional = [key for key in optional_keys if not os.getenv(key)]
    if missing_optional:
        print(f"⚠ Optional API keys not configured: {', '.join(missing_optional)}")
        print("Some features may be limited")
    
    return True

def setup_logging():
    """Setup logging configuration"""
    log_file = project_root / 'traderiser.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    print(f"✓ Logging configured. Log file: {log_file}")

def main():
    """Main application entry point"""
    print("🚀 Starting TradeRiser.AI - Professional Investment Platform")
    print("=" * 60)
    
    # Load environment
    load_environment()
    
    # Setup logging
    setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check API keys
    if not check_api_keys():
        sys.exit(1)
    
    # Import and run the application
    try:
        from traderiser_integrated_platform import app
        
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        print(f"✓ Starting Flask application on http://{host}:{port}")
        print(f"✓ Debug mode: {debug}")
        print("=" * 60)
        
        app.run(host=host, port=port, debug=debug)
        
    except ImportError as e:
        print(f"❌ Failed to import application: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()