```markdown
# TradeRiser.AI - Enhanced Professional Investment Platform

## Overview
TradeRiser.AI is a Flask-based investment analysis platform for portfolio management, cryptocurrency analysis, commodities trading, ETF analysis, and backtesting with Alpaca trading integration, using free APIs (Alpha Vantage, CoinGecko, FRED, pytrends, Twitter).

## Features
- **Portfolio Analysis**: Risk-return optimization, asset allocation, performance attribution
- **Cryptocurrency Analysis**: Market sentiment, technical analysis, AML compliance
- **Commodities Trading**: Gold, oil, agricultural products analysis and trading
- **ETF Analysis**: Exchange-traded funds screening and performance analysis
- **Alpaca Trading**: Live trading integration with commission-free stock trading
- **Backtesting**: Optimal trade selection with sector diversification and volatility constraints
- **Real-time Data**: Integration with multiple free financial APIs
- **Modern UI**: Responsive web interface with interactive charts

## Quick Setup

### Automated Setup (Recommended)

**Windows:**
```cmd
# Run the automated setup script
setup.bat
```

**Unix/Linux/macOS:**
```bash
# Make script executable and run
chmod +x setup.sh
./setup.sh
```

### Manual Setup

1. **Clone Repository**:
   ```bash
   git clone <repository-url>
   cd TradeRiser.AI
   ```

2. **Create Virtual Environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Unix/Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env file and add your API keys
   # Required: ALPHA_VANTAGE_API_KEY
   # Optional: TWITTER_API_KEY, FRED_API_KEY
   ```

5. **Get API Keys**:
   - **Alpha Vantage** (Required): [Get free key](https://www.alphavantage.co/support/#api-key)
   - **Twitter** (Optional): [Developer Portal](https://developer.twitter.com/)
   - **FRED** (Optional): [Economic Data API](https://fred.stlouisfed.org/docs/api/api_key.html)

6. **Run Application**:
   ```bash
   python run.py
   ```
   Access at `http://localhost:5000`

## Production Deployment

```bash
# Using Gunicorn (recommended)
gunicorn -w 4 -b 0.0.0.0:5000 traderiser_integrated_platform:app

# Or using the built-in Flask server
FLASK_ENV=production python run.py
```

## API Endpoints
- `POST /api/portfolio/analyze`: Analyze a portfolio with holdings (e.g., `{"tickers": ["AAPL", "MSFT"], "weights": [0.5, 0.5]}`)
- `GET /api/crypto/analyze`: Analyze cryptocurrency market
- `GET /api/backtest`: Run backtest to select optimal trades
- `GET /health`: Check platform health

## Notes
- **Rate Limits**: Alpha Vantage (5 calls/minute), CoinGecko (10–50 calls/minute). Handled by `ratelimit` and Redis caching.
- **AML Compliance**: Uses volatility-based proxy due to no free sanctioned address API.
- **Logging**: Logs are written to `traderiser.log`. Optional Sentry integration for monitoring.
- **Dependencies**: All required libraries are in `requirements.txt`. No Seaborn; uses Matplotlib for plotting.
- **License**: All Rights Reserved
```