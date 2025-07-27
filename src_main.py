```python
#!/usr/bin/env python3
"""
TradeRiser - Enhanced Professional Investment Platform
Main Flask application entry point for deployment
"""
import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from traderiser_integrated_platform import app

# Configure logging
logging.basicConfig(
    filename='traderiser.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

if __name__ == '__main__':
    logging.info("Starting TradeRiser Integrated Platform")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)), debug=False)
```