#!/usr/bin/env python3
"""
Render.com Entry Point
This file serves as a fallback entry point for Render deployment
Imports the main Flask application from application.py
"""

# Import the Flask application from application.py
from application import application

# Create app alias for gunicorn compatibility
app = application

if __name__ == '__main__':
    # For local testing
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)