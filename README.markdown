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

5. **API Configuration**:

   The platform supports both **Free** and **Pro** subscription tiers:

   ### Free Tier (Default)
   Includes access to essential APIs with no cost:
   - **Alpha Vantage API** - Stock data and fundamentals
   - **FRED API** - Economic indicators
   - **Yahoo Finance** - Real-time stock data (via yfinance)
   - **CoinGecko** - Cryptocurrency data

   ### Pro Tier
   Unlocks premium APIs for enhanced analysis:
   - **Twitter API** - Social sentiment analysis
   - **Quandl API** - Alternative financial data
   - **Financial Modeling Prep** - Advanced fundamentals
   - **IEX Cloud** - Real-time market data
   - **Alpaca Trading** - Live trading capabilities

   ### Configuration
   1. Set `SUBSCRIPTION_TIER=free` or `SUBSCRIPTION_TIER=pro` in `.env`
   2. Add your API keys:

   **Free Tier APIs:**
   ```
   ALPHA_VANTAGE_API_KEY=your_key_here
   FRED_API_KEY=your_key_here
   ```

   **Pro Tier APIs (optional):**
   ```
   TWITTER_API_KEY=your_key_here
   QUANDL_API_KEY=your_key_here
   FMP_API_KEY=your_key_here
   IEX_CLOUD_API_KEY=your_key_here
   ALPACA_API_KEY=your_key_here
   ALPACA_SECRET_KEY=your_secret_here
   ```

   **Note:** The platform works fully with free APIs only. Pro APIs enhance analysis but are not required.

6. **Run Application**:
   ```bash
   python run.py
   ```
   Access at `http://localhost:5001`

## Production Deployment

```bash
# Using Gunicorn (recommended)
gunicorn -w 4 -b 0.0.0.0:5001 traderiser_integrated_platform:app

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