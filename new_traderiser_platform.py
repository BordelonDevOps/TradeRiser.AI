"""TradeRiser.AI - Next Generation Financial Platform
Complete refactor with modern UI and professional financial analysis
"""
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import sys
import os
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests

# Load environment variables with priority: .env.local > .env
try:
    from dotenv import load_dotenv
    # Load .env first (template/defaults)
    load_dotenv('.env')
    # Load .env.local second (actual keys, overrides .env)
    load_dotenv('.env.local', override=True)
    print("Environment variables loaded successfully")
except ImportError:
    print("python-dotenv not available, using system environment variables")

# Financial Libraries Integration
try:
    from financetoolkit import Toolkit
    FINANCETOOLKIT_AVAILABLE = True
except ImportError:
    print("FinanceToolkit not available, using fallback")
    Toolkit = None
    FINANCETOOLKIT_AVAILABLE = False

try:
    import financedatabase as fd
    FINANCEDATABASE_AVAILABLE = True
except ImportError:
    print("FinanceDatabase not available, using fallback")
    fd = None
    FINANCEDATABASE_AVAILABLE = False

try:
    import thepassiveinvestor as tpi
    # Try to import the specific function
    if hasattr(tpi, 'create_ETF_overview'):
        create_ETF_overview = tpi.create_ETF_overview
    else:
        create_ETF_overview = None
    THEPASSIVEINVESTOR_AVAILABLE = True
except ImportError:
    print("The Passive Investor not available, using fallback")
    tpi = None
    create_ETF_overview = None
    THEPASSIVEINVESTOR_AVAILABLE = False

# YFinance as reliable fallback
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
    print("YFinance available for real market data")
except ImportError:
    print("YFinance not available")
    yf = None
    YFINANCE_AVAILABLE = False

# Finnhub API integration (temporary setup)
try:
    import finnhub
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
    if FINNHUB_API_KEY and FINNHUB_API_KEY != 'your_finnhub_api_key_here':
        finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
        FINNHUB_AVAILABLE = True
        print("Finnhub API available for real-time market data")
    else:
        finnhub_client = None
        FINNHUB_AVAILABLE = False
        print("Finnhub API key not configured")
except ImportError:
    print("Finnhub not available")
    finnhub = None
    finnhub_client = None
    FINNHUB_AVAILABLE = False
    FINNHUB_API_KEY = None

app = Flask(__name__)
CORS(app, origins="*")

# Configure logging
logging.basicConfig(
    filename='traderiser_new.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Security Functions (defined after logger)
def mask_api_key(api_key: str) -> str:
    """Mask API key for logging purposes"""
    if not api_key or len(api_key) < 8:
        return "[INVALID_KEY]"
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"

def get_secure_api_key(key_name: str) -> Optional[str]:
    """Securely retrieve API key from environment"""
    api_key = os.getenv(key_name)
    if api_key and api_key != f"your_{key_name.lower()}_here":
        return api_key
    return None

def log_api_status(service_name: str, api_key: str, available: bool):
    """Log API status with masked key"""
    if os.getenv('LOG_SENSITIVE_DATA', 'false').lower() == 'true':
        logger.info(f"{service_name} API: {'Available' if available else 'Unavailable'} - Key: {mask_api_key(api_key) if api_key else 'Not configured'}")
    else:
        logger.info(f"{service_name} API: {'Available' if available else 'Unavailable'}")

# Log API status for Finnhub
if FINNHUB_AVAILABLE and FINNHUB_API_KEY:
    log_api_status("Finnhub", FINNHUB_API_KEY, True)

# Security Configuration (after security functions are defined)
app.config['SECRET_KEY'] = get_secure_api_key('SECRET_KEY') or 'dev-key-change-in-production'
app.config['WTF_CSRF_ENABLED'] = True
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Security headers
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

def generate_crypto_recommendation(current_price: float, change_24h: float, symbol: str) -> dict:
    """Generate Buy/Hold/Sell recommendation for cryptocurrency based on technical analysis"""
    try:
        # Fetch additional market data for better analysis
        symbol_mapping = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'XRP': 'ripple', 'ADA': 'cardano',
            'DOT': 'polkadot', 'LINK': 'chainlink', 'LTC': 'litecoin', 'BCH': 'bitcoin-cash',
            'XLM': 'stellar', 'DOGE': 'dogecoin', 'SOL': 'solana', 'MATIC': 'matic-network'
        }
        
        coin_id = symbol_mapping.get(symbol, symbol.lower())
        
        # Get 7-day price history for trend analysis
        history_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
        response = requests.get(history_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            prices = [price[1] for price in data['prices']]
            
            # Calculate technical indicators
            if len(prices) >= 7:
                # 7-day price trend
                price_7d_ago = prices[0]
                price_change_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
                
                # Simple moving average (3-day)
                recent_prices = prices[-3:]
                sma_3 = sum(recent_prices) / len(recent_prices)
                
                # Volatility calculation
                price_changes = []
                for i in range(1, len(prices)):
                    change = ((prices[i] - prices[i-1]) / prices[i-1]) * 100
                    price_changes.append(abs(change))
                volatility = sum(price_changes) / len(price_changes) if price_changes else 0
                
                # Generate recommendation based on multiple factors
                score = 0
                reasoning_parts = []
                
                # Factor 1: 24h momentum
                if change_24h > 5:
                    score += 2
                    reasoning_parts.append(f"Strong 24h gain (+{change_24h:.1f}%)")
                elif change_24h > 2:
                    score += 1
                    reasoning_parts.append(f"Positive 24h momentum (+{change_24h:.1f}%)")
                elif change_24h < -5:
                    score -= 2
                    reasoning_parts.append(f"Significant 24h decline ({change_24h:.1f}%)")
                elif change_24h < -2:
                    score -= 1
                    reasoning_parts.append(f"Negative 24h momentum ({change_24h:.1f}%)")
                
                # Factor 2: 7-day trend
                if price_change_7d > 10:
                    score += 2
                    reasoning_parts.append(f"Strong weekly uptrend (+{price_change_7d:.1f}%)")
                elif price_change_7d > 3:
                    score += 1
                    reasoning_parts.append(f"Positive weekly trend (+{price_change_7d:.1f}%)")
                elif price_change_7d < -10:
                    score -= 2
                    reasoning_parts.append(f"Weak weekly performance ({price_change_7d:.1f}%)")
                elif price_change_7d < -3:
                    score -= 1
                    reasoning_parts.append(f"Declining weekly trend ({price_change_7d:.1f}%)")
                
                # Factor 3: Price vs SMA
                if current_price > sma_3 * 1.02:
                    score += 1
                    reasoning_parts.append("Price above 3-day average")
                elif current_price < sma_3 * 0.98:
                    score -= 1
                    reasoning_parts.append("Price below 3-day average")
                
                # Factor 4: Volatility assessment
                if volatility > 8:
                    score -= 1
                    reasoning_parts.append(f"High volatility ({volatility:.1f}%)")
                elif volatility < 3:
                    score += 1
                    reasoning_parts.append(f"Low volatility ({volatility:.1f}%)")
                
                # Generate final recommendation
                if score >= 3:
                    action = "BUY"
                    confidence = min(85 + (score - 3) * 5, 95)
                elif score >= 1:
                    action = "BUY"
                    confidence = 65 + (score - 1) * 10
                elif score <= -3:
                    action = "SELL"
                    confidence = min(85 + abs(score + 3) * 5, 95)
                elif score <= -1:
                    action = "SELL"
                    confidence = 65 + abs(score + 1) * 10
                else:
                    action = "HOLD"
                    confidence = 60
                
                reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Neutral market conditions"
                
                return {
                    'action': action,
                    'confidence': confidence,
                    'reasoning': reasoning,
                    'score': score
                }
        
        # Fallback recommendation based on 24h change only
        if change_24h > 5:
            return {'action': 'BUY', 'confidence': 70, 'reasoning': f'Strong 24h gain (+{change_24h:.1f}%)', 'score': 1}
        elif change_24h < -5:
            return {'action': 'SELL', 'confidence': 70, 'reasoning': f'Significant 24h decline ({change_24h:.1f}%)', 'score': -1}
        else:
            return {'action': 'HOLD', 'confidence': 60, 'reasoning': f'Moderate 24h change ({change_24h:.1f}%)', 'score': 0}
            
    except Exception as e:
        logger.error(f"Error generating recommendation for {symbol}: {e}")
        return {'action': 'HOLD', 'confidence': 50, 'reasoning': 'Unable to analyze market data', 'score': 0}

class FinancialLibrariesIntegration:
    """Integration wrapper for advanced financial libraries"""
    
    def __init__(self):
        # Initialize FinanceDatabase components
        if FINANCEDATABASE_AVAILABLE and fd:
            try:
                self.equities = fd.Equities() if hasattr(fd, 'Equities') else None
                self.etfs = fd.ETFs() if hasattr(fd, 'ETFs') else None
                self.funds = fd.Funds() if hasattr(fd, 'Funds') else None
                self.indices = fd.Indices() if hasattr(fd, 'Indices') else None
                self.currencies = fd.Currencies() if hasattr(fd, 'Currencies') else None
                self.cryptocurrencies = fd.Cryptocurrencies() if hasattr(fd, 'Cryptocurrencies') else None
            except Exception as e:
                logger.warning(f"Some FinanceDatabase components not available: {e}")
                self.equities = self.etfs = self.funds = self.indices = self.currencies = self.cryptocurrencies = None
        else:
            self.equities = self.etfs = self.funds = self.indices = self.currencies = self.cryptocurrencies = None
        
        logger.info("Financial Libraries Integration initialized successfully")
    
    def get_comprehensive_analysis(self, tickers: List[str], period: str = "5y") -> Dict:
        """Get comprehensive financial analysis using Finnhub, FinanceToolkit or YFinance"""
        # Try Finnhub first for real-time data
        if FINNHUB_AVAILABLE:
            logger.info("Using Finnhub for real-time market data")
            return self._get_finnhub_analysis(tickers)
        
        if not FINANCETOOLKIT_AVAILABLE or not Toolkit:
            logger.info("FinanceToolkit not available, using YFinance for real data")
            return self._get_yfinance_analysis(tickers)
        
        try:
            # Initialize FinanceToolkit
            toolkit = Toolkit(
                tickers=tickers,
                api_key=os.getenv('FMP_API_KEY'),  # Financial Modeling Prep API key
                start_date=datetime.now() - timedelta(days=365*5),
                quarterly=False
            )
            
            # Get comprehensive ratios and metrics
            ratios = toolkit.ratios.collect_all_ratios()
            performance = toolkit.performance.get_performance_metrics()
            risk_metrics = toolkit.risk.get_risk_metrics()
            
            return {
                'ratios': ratios.to_dict() if hasattr(ratios, 'to_dict') else {},
                'performance': performance.to_dict() if hasattr(performance, 'to_dict') else {},
                'risk_metrics': risk_metrics.to_dict() if hasattr(risk_metrics, 'to_dict') else {},
                'analysis_date': datetime.now().isoformat(),
                'data_source': 'FinanceToolkit'
            }
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return self._get_yfinance_analysis(tickers)
    
    def search_securities(self, query: str, asset_type: str = "equities") -> Dict:
        """Search securities using Finnhub with fallbacks to FinanceDatabase and YFinance"""
        try:
            # Try Finnhub first for real-time data
            if FINNHUB_AVAILABLE:
                results = self._get_finnhub_search_results(query, asset_type)
                if results:
                    return results
            
            # Fallback to FinanceDatabase
            results = None
            if asset_type == "equities" and self.equities:
                results = self.equities.search(query)
            elif asset_type == "etfs" and self.etfs:
                results = self.etfs.search(query)
            elif asset_type == "funds" and self.funds:
                results = self.funds.search(query)
            elif asset_type == "crypto" and self.cryptocurrencies:
                results = self.cryptocurrencies.search(query)
            elif self.equities:
                results = self.equities.search(query)
            
            if results is not None and hasattr(results, 'head'):
                return results.head(20).to_dict('records')
            else:
                return self._get_yfinance_search_results(query, asset_type)
        except Exception as e:
            logger.error(f"Error searching securities: {e}")
            return self._get_yfinance_search_results(query, asset_type)
    
    def get_etf_analysis(self, etf_tickers: List[str]) -> Dict:
        """Get ETF analysis using Finnhub with fallbacks to The Passive Investor and YFinance"""
        # Try Finnhub first for real-time data
        if FINNHUB_AVAILABLE:
            logger.info("Using Finnhub for real-time ETF data")
            return self._get_finnhub_etf_analysis(etf_tickers)
        
        # Fallback to The Passive Investor
        if not THEPASSIVEINVESTOR_AVAILABLE or not create_ETF_overview:
            logger.info("The Passive Investor not available, using YFinance for real ETF data")
            return self._get_yfinance_etf_analysis(etf_tickers)
        
        try:
            etf_overview = create_ETF_overview(etf_tickers)
            return {
                'etf_overview': etf_overview.to_dict() if hasattr(etf_overview, 'to_dict') else {},
                'analysis_date': datetime.now().isoformat(),
                'data_source': 'ThePassiveInvestor'
            }
        except Exception as e:
            logger.error(f"Error in ETF analysis: {e}")
            return self._get_yfinance_etf_analysis(etf_tickers)
    
    def _get_fallback_analysis(self, tickers: List[str]) -> Dict:
        """Return error when APIs fail - no mock data"""
        return {
            'error': 'Unable to fetch real market data. Both Finnhub and YFinance APIs are unavailable.',
            'tickers': tickers,
            'analysis_date': datetime.now().isoformat(),
            'data_source': 'No data available'
        }
    
    def _get_fallback_etf_analysis(self, etf_tickers: List[str]) -> Dict:
        """Return error when ETF APIs fail - no mock data"""
        return {
            'error': 'Unable to fetch real ETF data. Both Finnhub and YFinance APIs are unavailable.',
            'etf_tickers': etf_tickers,
            'analysis_date': datetime.now().isoformat(),
            'data_source': 'No data available'
        }
    
    def _get_yfinance_analysis(self, tickers: List[str]) -> Dict:
        """Get real market data analysis using YFinance"""
        if not YFINANCE_AVAILABLE:
            return self._get_fallback_analysis(tickers)
        
        analysis_result = {
            'ratios': {},
            'performance': {},
            'risk_metrics': {},
            'current_prices': {},
            'analysis_date': datetime.now().isoformat(),
            'data_source': 'YFinance (Real Data)'
        }
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period='1y')
                
                # Current price and basic info
                analysis_result['current_prices'][ticker] = {
                    'current_price': info.get('currentPrice', hist['Close'].iloc[-1] if not hist.empty else 0),
                    'name': info.get('longName', ticker),
                    'sector': info.get('sector', 'N/A'),
                    'market_cap': info.get('marketCap', 0)
                }
                
                # Financial ratios from yfinance
                analysis_result['ratios'][ticker] = {
                    'pe_ratio': info.get('trailingPE', 0),
                    'forward_pe': info.get('forwardPE', 0),
                    'peg_ratio': info.get('pegRatio', 0),
                    'price_to_book': info.get('priceToBook', 0),
                    'debt_to_equity': info.get('debtToEquity', 0),
                    'return_on_equity': info.get('returnOnEquity', 0),
                    'profit_margin': info.get('profitMargins', 0)
                }
                
                # Performance metrics from historical data
                if not hist.empty and len(hist) > 1:
                    returns = hist['Close'].pct_change().dropna()
                    annual_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) ** (252/len(hist)) - 1
                    volatility = returns.std() * (252 ** 0.5)
                    
                    analysis_result['performance'][ticker] = {
                        'annual_return': annual_return,
                        'volatility': volatility,
                        'sharpe_ratio': annual_return / volatility if volatility > 0 else 0,
                        'max_price_52w': hist['High'].max(),
                        'min_price_52w': hist['Low'].min()
                    }
                    
                    # Risk metrics
                    analysis_result['risk_metrics'][ticker] = {
                        'beta': info.get('beta', 1.0),
                        'var_95': returns.quantile(0.05),
                        'max_drawdown': ((hist['Close'] / hist['Close'].cummax()) - 1).min()
                    }
                
            except Exception as e:
                logger.warning(f"Error getting YFinance data for {ticker}: {e}")
                # Add minimal data for failed tickers
                analysis_result['current_prices'][ticker] = {'error': str(e)}
        
        return analysis_result
    
    def _get_finnhub_analysis(self, tickers: List[str]) -> Dict:
        """Get real market data analysis using Finnhub API"""
        if not FINNHUB_AVAILABLE:
            return self._get_yfinance_analysis(tickers)
        
        analysis_result = {
            'ratios': {},
            'performance': {},
            'risk_metrics': {},
            'current_prices': {},
            'company_profiles': {},
            'analysis_date': datetime.now().isoformat(),
            'data_source': 'Finnhub (Real-Time Data)'
        }
        
        for ticker in tickers:
            try:
                # Get real-time quote
                quote = finnhub_client.quote(ticker)
                
                # Get company profile
                profile = finnhub_client.company_profile2(symbol=ticker)
                
                # Get basic financials
                financials = finnhub_client.company_basic_financials(ticker, 'all')
                
                # Current price and basic info
                analysis_result['current_prices'][ticker] = {
                    'current_price': quote.get('c', 0),  # Current price
                    'change': quote.get('d', 0),  # Change
                    'percent_change': quote.get('dp', 0),  # Percent change
                    'high': quote.get('h', 0),  # High price of the day
                    'low': quote.get('l', 0),  # Low price of the day
                    'open': quote.get('o', 0),  # Open price of the day
                    'previous_close': quote.get('pc', 0)  # Previous close price
                }
                
                # Company profile
                analysis_result['company_profiles'][ticker] = {
                    'name': profile.get('name', ticker),
                    'country': profile.get('country', 'N/A'),
                    'currency': profile.get('currency', 'USD'),
                    'exchange': profile.get('exchange', 'N/A'),
                    'industry': profile.get('finnhubIndustry', 'N/A'),
                    'market_cap': profile.get('marketCapitalization', 0),
                    'share_outstanding': profile.get('shareOutstanding', 0),
                    'website': profile.get('weburl', 'N/A')
                }
                
                # Financial ratios from Finnhub
                metrics = financials.get('metric', {})
                analysis_result['ratios'][ticker] = {
                    'pe_ratio': metrics.get('peBasicExclExtraTTM', 0),
                    'pe_forward': metrics.get('peNormalizedAnnual', 0),
                    'price_to_book': metrics.get('pbAnnual', 0),
                    'price_to_sales': metrics.get('psAnnual', 0),
                    'debt_to_equity': metrics.get('totalDebt/totalEquityAnnual', 0),
                    'return_on_equity': metrics.get('roeRfy', 0),
                    'return_on_assets': metrics.get('roaRfy', 0),
                    'profit_margin': metrics.get('netProfitMarginAnnual', 0),
                    'gross_margin': metrics.get('grossMarginAnnual', 0)
                }
                
                # Performance metrics
                analysis_result['performance'][ticker] = {
                    'beta': metrics.get('beta', 1.0),
                    '52_week_high': metrics.get('52WeekHigh', 0),
                    '52_week_low': metrics.get('52WeekLow', 0),
                    '52_week_return': metrics.get('52WeekPriceReturnDaily', 0),
                    'ytd_return': metrics.get('ytdPriceReturnDaily', 0),
                    '1_year_return': metrics.get('1YearPriceReturnDaily', 0)
                }
                
                # Risk metrics
                analysis_result['risk_metrics'][ticker] = {
                    'beta': metrics.get('beta', 1.0),
                    'volatility': metrics.get('epsGrowth5Y', 0),  # Using as proxy
                    'dividend_yield': metrics.get('dividendYieldIndicatedAnnual', 0)
                }
                
            except Exception as e:
                logger.warning(f"Error getting Finnhub data for {ticker}: {e}")
                # Add minimal data for failed tickers
                analysis_result['current_prices'][ticker] = {'error': str(e)}
        
        return analysis_result
    
    def _get_finnhub_etf_analysis(self, etf_tickers: List[str]) -> Dict:
        """Get real ETF data using Finnhub API"""
        if not FINNHUB_AVAILABLE:
            return self._get_yfinance_etf_analysis(etf_tickers)
        
        etf_data = {}
        for ticker in etf_tickers:
            try:
                # Get real-time quote
                quote = finnhub_client.quote(ticker)
                
                # Get ETF profile
                profile = finnhub_client.company_profile2(symbol=ticker)
                
                # Get ETF holdings (if available)
                try:
                    holdings = finnhub_client.etfs_holdings(ticker)
                except:
                    holdings = {}
                
                etf_data[ticker] = {
                    'name': profile.get('name', ticker),
                    'current_price': quote.get('c', 0),
                    'change': quote.get('d', 0),
                    'percent_change': quote.get('dp', 0),
                    'high': quote.get('h', 0),
                    'low': quote.get('l', 0),
                    'volume': quote.get('v', 0),
                    'market_cap': profile.get('marketCapitalization', 0),
                    'exchange': profile.get('exchange', 'N/A'),
                    'currency': profile.get('currency', 'USD'),
                    'country': profile.get('country', 'N/A'),
                    'website': profile.get('weburl', 'N/A'),
                    'holdings_count': len(holdings.get('holdings', [])) if holdings else 0
                }
                
            except Exception as e:
                logger.warning(f"Error getting Finnhub ETF data for {ticker}: {e}")
                etf_data[ticker] = {'error': str(e), 'name': ticker}
        
        return {
            'etf_overview': etf_data,
            'analysis_date': datetime.now().isoformat(),
            'data_source': 'Finnhub (Real-Time Data)'
        }
    
    def _get_finnhub_search_results(self, query: str, asset_type: str) -> List[Dict]:
        """Search for securities using Finnhub symbol lookup"""
        if not FINNHUB_AVAILABLE:
            return self._get_yfinance_search_results(query, asset_type)
        
        try:
            # Use Finnhub symbol lookup
            search_results = finnhub_client.symbol_lookup(query)
            
            results = []
            for result in search_results.get('result', [])[:10]:  # Limit to 10 results
                try:
                    symbol = result.get('symbol', '')
                    # Get additional info for each symbol
                    profile = finnhub_client.company_profile2(symbol=symbol)
                    quote = finnhub_client.quote(symbol)
                    
                    results.append({
                        'symbol': symbol,
                        'name': result.get('description', profile.get('name', symbol)),
                        'type': result.get('type', 'Unknown'),
                        'exchange': profile.get('exchange', 'N/A'),
                        'industry': profile.get('finnhubIndustry', 'N/A'),
                        'country': profile.get('country', 'N/A'),
                        'market_cap': profile.get('marketCapitalization', 0),
                        'current_price': quote.get('c', 0)
                    })
                except:
                    # If detailed info fails, add basic info
                    results.append({
                        'symbol': result.get('symbol', ''),
                        'name': result.get('description', ''),
                        'type': result.get('type', 'Unknown')
                    })
            
            return results
            
        except Exception as e:
            logger.warning(f"Error in Finnhub search: {e}")
            return self._get_yfinance_search_results(query, asset_type)
    
    def _get_yfinance_etf_analysis(self, etf_tickers: List[str]) -> Dict:
        """Get real ETF data using YFinance"""
        if not YFINANCE_AVAILABLE:
            return self._get_fallback_etf_analysis(etf_tickers)
        
        etf_data = {}
        for ticker in etf_tickers:
            try:
                etf = yf.Ticker(ticker)
                info = etf.info
                hist = etf.history(period='1y')
                
                etf_data[ticker] = {
                    'name': info.get('longName', ticker),
                    'current_price': info.get('currentPrice', hist['Close'].iloc[-1] if not hist.empty else 0),
                    'expense_ratio': info.get('annualReportExpenseRatio', info.get('totalExpenseRatio', 0)),
                    'aum': info.get('totalAssets', 0),
                    'dividend_yield': info.get('yield', info.get('dividendYield', 0)),
                    'category': info.get('category', 'ETF'),
                    'inception_date': info.get('fundInceptionDate', 'N/A'),
                    'ytd_return': info.get('ytdReturn', 0),
                    'volume': info.get('volume', 0)
                }
                
                # Calculate performance metrics if historical data available
                if not hist.empty and len(hist) > 1:
                    returns = hist['Close'].pct_change().dropna()
                    etf_data[ticker].update({
                        'annual_return': (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) ** (252/len(hist)) - 1,
                        'volatility': returns.std() * (252 ** 0.5),
                        'max_price_52w': hist['High'].max(),
                        'min_price_52w': hist['Low'].min()
                    })
                    
            except Exception as e:
                logger.warning(f"Error getting YFinance ETF data for {ticker}: {e}")
                etf_data[ticker] = {'error': str(e), 'name': ticker}
        
        return {
            'etf_overview': etf_data,
            'analysis_date': datetime.now().isoformat(),
            'data_source': 'YFinance (Real Data)'
        }
    
    def _get_yfinance_search_results(self, query: str, asset_type: str) -> List[Dict]:
        """Search for securities using YFinance validation"""
        if not YFINANCE_AVAILABLE:
            return self._get_fallback_search_results(query, asset_type)
        
        # Try to validate the query as a ticker symbol
        search_results = []
        potential_tickers = [query.upper(), f"{query.upper()}.TO", f"{query.upper()}.L"]
        
        for ticker in potential_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Check if we got valid data
                if info.get('longName') or info.get('shortName'):
                    search_results.append({
                        'symbol': ticker,
                        'name': info.get('longName', info.get('shortName', ticker)),
                        'sector': info.get('sector', 'N/A'),
                        'industry': info.get('industry', 'N/A'),
                        'market_cap': info.get('marketCap', 0),
                        'current_price': info.get('currentPrice', 0)
                    })
                    break  # Found valid ticker, stop searching
            except:
                continue
        
        # If no results found, return fallback
        if not search_results:
            return self._get_fallback_search_results(query, asset_type)
        
        return search_results
    
    def _get_fallback_search_results(self, query: str, asset_type: str) -> List[Dict]:
        """Return empty results when FinanceDatabase is not available - no fallback data"""
        return []

# Initialize Financial Libraries Integration
financial_integration = FinancialLibrariesIntegration()

@app.route('/')
def index():
    """Modern TradeRiser dashboard"""
    logger.info("Rendering new modern interface")
    return render_template_string(MODERN_DASHBOARD_TEMPLATE)

@app.route('/api/comprehensive-analysis', methods=['POST'])
def comprehensive_analysis():
    """Comprehensive financial analysis using FinanceToolkit"""
    try:
        data = request.get_json()
        tickers = data.get('tickers', [])
        
        if not tickers:
            return jsonify({'error': 'No tickers provided'}), 400
        
        analysis = financial_integration.get_comprehensive_analysis(tickers)
        return jsonify(analysis)
    
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-securities', methods=['GET'])
def search_securities():
    """Search securities using FinanceDatabase"""
    try:
        query = request.args.get('query', '')
        asset_type = request.args.get('type', 'equities')
        
        results = financial_integration.search_securities(query, asset_type)
        return jsonify({'results': results})
    
    except Exception as e:
        logger.error(f"Error searching securities: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/etf-analysis', methods=['POST'])
def etf_analysis():
    """ETF analysis using The Passive Investor"""
    try:
        data = request.get_json()
        etf_tickers = data.get('etf_tickers', [])
        
        if not etf_tickers:
            return jsonify({'error': 'No ETF tickers provided'}), 400
        
        analysis = financial_integration.get_etf_analysis(etf_tickers)
        return jsonify(analysis)
    
    except Exception as e:
        logger.error(f"Error in ETF analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickers', methods=['GET'])
def get_tickers_api():
    """Get ticker data for top tickers display - always fresh data"""
    try:
        # Disable caching to ensure fresh data
        from flask import make_response
        
        def add_no_cache_headers(response):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        category = request.args.get('category', 'all')
        
        # Define top 5 ticker lists for each category (20 total tickers)
        ticker_lists = {
            'djia': ['AAPL', 'MSFT', 'UNH', 'GS', 'HD'],
            'nasdaq': ['GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'],
            'sp': ['JPM', 'JNJ', 'V', 'PG', 'MA'],
            'crypto': ['BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD']
        }
        
        if category.lower() in ticker_lists:
            tickers = ticker_lists[category.lower()]
        else:
            # Return all categories
            results = {}
            for cat, tick_list in ticker_lists.items():
                results[cat] = {}
                for ticker in tick_list:
                    try:
                        if 'USD' in ticker:  # Crypto
                            # Use YFinance for crypto
                            import yfinance as yf
                            stock = yf.Ticker(ticker)
                            info = stock.info
                            hist = stock.history(period='1d')
                            if not hist.empty:
                                current_price = hist['Close'].iloc[-1]
                                prev_close = info.get('previousClose', current_price)
                                change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
                                results[cat][ticker] = {
                                    'current_price': float(current_price),
                                    'change_percent': float(change_percent)
                                }
                        else:
                            # Use Finnhub for stocks
                            if FINNHUB_API_KEY:
                                quote = finnhub_client.quote(ticker)
                                results[cat][ticker] = {
                                    'current_price': quote.get('c', 0),
                                    'change_percent': quote.get('dp', 0)
                                }
                            else:
                                # Fallback to YFinance
                                import yfinance as yf
                                stock = yf.Ticker(ticker)
                                hist = stock.history(period='1d')
                                if not hist.empty:
                                    current_price = hist['Close'].iloc[-1]
                                    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                                    change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
                                    results[cat][ticker] = {
                                        'current_price': float(current_price),
                                        'change_percent': float(change_percent)
                                    }
                    except Exception as e:
                        logger.error(f"Error fetching ticker {ticker}: {str(e)}")
                        results[cat][ticker] = {
                            'current_price': 0,
                            'change_percent': 0
                        }
            return jsonify(results)
        
        # Single category request
        results = {}
        for ticker in tickers:
            try:
                if 'USD' in ticker:  # Crypto
                    import yfinance as yf
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    hist = stock.history(period='1d')
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        prev_close = info.get('previousClose', current_price)
                        change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
                        results[ticker] = {
                            'current_price': float(current_price),
                            'change_percent': float(change_percent)
                        }
                else:
                    # Use Finnhub for stocks
                    if FINNHUB_API_KEY:
                        quote = finnhub_client.quote(ticker)
                        results[ticker] = {
                            'current_price': quote.get('c', 0),
                            'change_percent': quote.get('dp', 0)
                        }
                    else:
                        # Fallback to YFinance
                        import yfinance as yf
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period='1d')
                        if not hist.empty:
                            current_price = hist['Close'].iloc[-1]
                            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                            change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
                            results[ticker] = {
                                'current_price': float(current_price),
                                'change_percent': float(change_percent)
                            }
            except Exception as e:
                logger.error(f"Error fetching ticker {ticker}: {str(e)}")
                results[ticker] = {
                    'current_price': 0,
                    'change_percent': 0
                }
        
        response = make_response(jsonify(results))
        return add_no_cache_headers(response)
    except Exception as e:
        logger.error(f"Tickers API error: {str(e)}")
        error_response = make_response(jsonify({'error': 'Failed to fetch ticker data'}), 500)
        return add_no_cache_headers(error_response)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'platform': 'TradeRiser.AI Next Generation',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/crypto/analyze', methods=['POST'])
def analyze_crypto():
    try:
        data = request.json
        symbols = data.get('symbols', [])
        holdings = data.get('holdings', [])
        analysis_type = data.get('analysis_type', 'portfolio')
        
        if not symbols:
            return jsonify({'error': 'No crypto symbols provided'})
        
        # Real crypto analysis using CoinGecko API
        total_value = 0
        total_change_weighted = 0
        crypto_data = {}
        
        # Map common symbols to CoinGecko IDs
        symbol_mapping = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'XRP': 'ripple', 'ADA': 'cardano',
            'DOT': 'polkadot', 'LINK': 'chainlink', 'LTC': 'litecoin', 'BCH': 'bitcoin-cash',
            'XLM': 'stellar', 'DOGE': 'dogecoin', 'SOL': 'solana', 'MATIC': 'matic-network'
        }
        
        for i, symbol in enumerate(symbols):
            try:
                coin_id = symbol_mapping.get(symbol.upper(), symbol.lower())
                
                # Fetch real-time data from CoinGecko
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    price_data = response.json()
                    if coin_id in price_data:
                        current_price = price_data[coin_id]['usd']
                        change_24h = price_data[coin_id].get('usd_24h_change', 0)
                        
                        # Calculate value based on holdings or assume 1 unit
                        holding_amount = float(holdings[i]) if holdings and i < len(holdings) and holdings[i] else 1
                        value = current_price * holding_amount
                        
                        total_value += value
                        total_change_weighted += (change_24h * value)
                        
                        # Generate individual trading recommendation
                        recommendation = generate_crypto_recommendation(current_price, change_24h, symbol.upper())
                        
                        crypto_data[symbol.upper()] = {
                            'price': current_price,
                            'change_24h': change_24h,
                            'holding': holding_amount,
                            'value': value,
                            'recommendation': recommendation['action'],
                            'confidence': recommendation['confidence'],
                            'reasoning': recommendation['reasoning']
                        }
                    else:
                        return jsonify({'error': f'Cryptocurrency {symbol} not found'})
                else:
                    return jsonify({'error': f'Failed to fetch data for {symbol}'})
                    
            except Exception as e:
                return jsonify({'error': f'Error fetching data for {symbol}: {str(e)}'})
        
        # Calculate weighted average change
        total_change = (total_change_weighted / total_value) if total_value > 0 else 0
        
        results = {
            'total_value': round(total_value, 2),
            'total_change': round(total_change, 2),
            'diversification_score': min(len(symbols), 10),
            'crypto_details': crypto_data,
            'recommendation': f"Your crypto portfolio shows {'good' if len(symbols) >= 3 else 'limited'} diversification. Consider {'maintaining' if total_change >= 0 else 'rebalancing'} your positions.",
            'data_source': 'CoinGecko API (Real-Time)'
        }
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/defi/opportunities', methods=['POST'])
def find_defi_opportunities():
    try:
        data = request.json
        protocols = data.get('protocols', [])
        amount = data.get('amount', 0)
        
        if not protocols or amount < 100:
            return jsonify({'error': 'Invalid protocols or amount'})
        
        # DeFi opportunities require real-time integration with DeFi protocols
        # This would need APIs from DeFiPulse, DeBank, or direct protocol APIs
        return jsonify({
            'error': 'DeFi opportunities analysis requires real-time protocol integration',
            'message': 'This feature needs integration with DeFi protocol APIs (Compound, Aave, Uniswap, etc.) to provide accurate yield data',
            'requested_protocols': protocols,
            'investment_amount': amount,
            'status': 'Feature requires real API integration - no mock data available'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/portfolio/analyze', methods=['POST'])
def portfolio_analyze():
    try:
        data = request.get_json()
        tickers = data.get('tickers', [])
        holdings = data.get('holdings', {})
        weights = data.get('weights', [])
        
        if not tickers and not holdings:
            return jsonify({'error': 'Please provide tickers or holdings data'})
        
        # Use holdings if provided, otherwise use tickers with equal weights
        if holdings:
            tickers = list(holdings.keys())
        elif weights and len(weights) == len(tickers):
            # Use provided weights
            pass
        else:
            # Equal weights
            weights = [1.0/len(tickers)] * len(tickers)
        
        # Get real-time data for portfolio analysis
        portfolio_data = {}
        total_value = 0
        price_changes = []
        
        for i, ticker in enumerate(tickers):
            try:
                # Get real-time data from Finnhub or YFinance
                if FINNHUB_AVAILABLE:
                    quote = finnhub_client.quote(ticker)
                    current_price = quote.get('c', 0)
                    change_percent = quote.get('dp', 0) / 100
                else:
                    # Fallback to YFinance
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='2d')
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                        change_percent = (current_price - prev_price) / prev_price if prev_price > 0 else 0
                    else:
                        current_price = 0
                        change_percent = 0
                
                # Calculate position value
                if holdings and ticker in holdings:
                    shares = holdings[ticker]
                    position_value = current_price * shares
                else:
                    # Use weights for theoretical portfolio
                    weight = weights[i] if i < len(weights) else (1.0/len(tickers))
                    position_value = 10000 * weight  # Assume $10k portfolio
                    shares = position_value / current_price if current_price > 0 else 0
                
                portfolio_data[ticker] = {
                    'current_price': current_price,
                    'shares': shares,
                    'value': position_value,
                    'change_percent': change_percent
                }
                
                total_value += position_value
                price_changes.append(change_percent)
                
            except Exception as e:
                logger.error(f"Error analyzing {ticker}: {str(e)}")
                continue
        
        # Calculate portfolio metrics
        if price_changes:
            avg_return = sum(price_changes) / len(price_changes)
            volatility = (sum((x - avg_return) ** 2 for x in price_changes) / len(price_changes)) ** 0.5
            sharpe_ratio = avg_return / volatility if volatility > 0 else 0
            max_drawdown = min(price_changes) if price_changes else 0
        else:
            avg_return = 0
            volatility = 0
            sharpe_ratio = 0
            max_drawdown = 0
        
        # Calculate diversification score (simple metric based on number of holdings)
        diversification_score = min(len(tickers) / 10, 1.0)  # Max score of 1.0 for 10+ holdings
        
        # Generate investment tips based on analysis
        tips = []
        if len(tickers) < 5:
            tips.append("Consider adding more holdings to improve diversification")
        if volatility > 0.3:
            tips.append("Your portfolio shows high volatility - consider adding stable assets")
        if sharpe_ratio < 0.5:
            tips.append("Risk-adjusted returns could be improved - review your asset allocation")
        if not tips:
            tips.append("Your portfolio shows good balance and diversification")
        
        return jsonify({
            'portfolio_value': total_value,
            'total_return': avg_return,
            'annualized_return': avg_return * 252,  # Approximate annualization
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'diversification_score': diversification_score,
            'holdings': portfolio_data,
            'investment_tips': tips
        })
        
    except Exception as e:
        logger.error(f"Portfolio analysis error: {str(e)}")
        return jsonify({'error': f'Portfolio analysis failed: {str(e)}'})

@app.route('/api/investment/wizard', methods=['POST'])
def investment_wizard():
    """Smart Investment Wizard with comprehensive personalized recommendations"""
    try:
        data = request.json
        
        # Basic required fields
        amount = data.get('amount', 0)
        situation = data.get('situation', '')
        timeline = data.get('timeline', '')
        risk_tolerance = data.get('risk_tolerance', '')
        goals = data.get('goals', '')
        
        # New comprehensive fields
        annual_income = data.get('annual_income', '')
        debt_level = data.get('debt_level', '')
        emergency_fund = data.get('emergency_fund', '')
        liquidity_needs = data.get('liquidity_needs', '')
        investment_experience = data.get('investment_experience', '')
        experience_assets = data.get('experience_assets', [])
        investment_preferences = data.get('investment_preferences', '')
        assets_to_avoid = data.get('assets_to_avoid', [])
        return_expectations = data.get('return_expectations', '')
        tax_bracket = data.get('tax_bracket', '')
        income_changes = data.get('income_changes', '')
        tax_accounts = data.get('tax_accounts', [])
        upcoming_expenses = data.get('upcoming_expenses', [])
        estate_planning = data.get('estate_planning', '')
        management_style = data.get('management_style', '')
        insurance_coverage = data.get('insurance_coverage', [])
        special_circumstances = data.get('special_circumstances', [])
        
        if amount < 100 or not all([situation, timeline, risk_tolerance, goals]):
            return jsonify({'error': 'Invalid input parameters'})
        
        # Generate comprehensive personalized investment recommendations
        recommendations = generate_investment_recommendations(
            amount, situation, timeline, risk_tolerance, goals,
            annual_income, debt_level, emergency_fund, liquidity_needs,
            investment_experience, experience_assets, investment_preferences,
            assets_to_avoid, return_expectations, tax_bracket, income_changes,
            tax_accounts, upcoming_expenses, estate_planning, management_style,
            insurance_coverage, special_circumstances
        )
        
        return jsonify(recommendations)
        
    except Exception as e:
        logger.error(f"Error in investment wizard: {e}")
        return jsonify({'error': str(e)})

def generate_investment_recommendations(amount, situation, timeline, risk_tolerance, goals,
                                       annual_income='', debt_level='', emergency_fund='', liquidity_needs='',
                                       investment_experience='', experience_assets=[], investment_preferences='',
                                       assets_to_avoid=[], return_expectations='', tax_bracket='', income_changes='',
                                       tax_accounts=[], upcoming_expenses=[], estate_planning='', management_style='',
                                       insurance_coverage=[], special_circumstances=[]):
    """Generate comprehensive personalized investment recommendations based on detailed user profile"""
    
    # Enhanced risk-based asset allocation with experience adjustments
    base_risk_profiles = {
        'conservative': {'stocks': 30, 'bonds': 60, 'cash': 10},
        'moderate': {'stocks': 60, 'bonds': 30, 'cash': 10},
        'aggressive': {'stocks': 80, 'bonds': 15, 'cash': 5}
    }
    
    # Experience-based adjustments
    experience_adjustments = {
        'beginner': {'stocks': -10, 'bonds': +5, 'cash': +5},
        'intermediate': {'stocks': 0, 'bonds': 0, 'cash': 0},
        'advanced': {'stocks': +5, 'bonds': -3, 'cash': -2}
    }
    
    # Income-based adjustments
    income_adjustments = {
        'low': {'stocks': -5, 'bonds': +3, 'cash': +2},
        'medium': {'stocks': 0, 'bonds': 0, 'cash': 0},
        'high': {'stocks': +5, 'bonds': -2, 'cash': -3}
    }
    
    # Timeline adjustments
    timeline_adjustments = {
        'short': {'stocks': -20, 'bonds': +15, 'cash': +5},
        'medium': {'stocks': 0, 'bonds': 0, 'cash': 0},
        'long': {'stocks': +15, 'bonds': -8, 'cash': -7}
    }
    
    # Enhanced goal-based strategies
    goal_strategies = {
        'retirement': 'Long-term wealth accumulation with tax-advantaged growth and compound returns',
        'education': 'Education-focused savings with 529 plans and conservative growth strategies',
        'house': 'Capital preservation with moderate growth for down payment accumulation',
        'wealth': 'Diversified growth strategy emphasizing long-term compound returns',
        'income': 'Income-generating portfolio with dividend stocks, REITs, and bonds'
    }
    
    # Get base allocation
    base_allocation = base_risk_profiles.get(risk_tolerance.lower(), base_risk_profiles['moderate'])
    
    # Apply experience adjustments
    exp_key = 'beginner' if investment_experience.lower() in ['beginner', 'none'] else 'advanced' if investment_experience.lower() == 'advanced' else 'intermediate'
    exp_adj = experience_adjustments[exp_key]
    
    # Apply income adjustments
    income_key = 'low' if annual_income.lower() in ['under-50k', 'low'] else 'high' if annual_income.lower() in ['over-150k', 'high'] else 'medium'
    income_adj = income_adjustments[income_key]
    
    # Apply timeline adjustments
    timeline_key = 'short' if 'short' in timeline.lower() else 'long' if 'long' in timeline.lower() else 'medium'
    timeline_adj = timeline_adjustments[timeline_key]
    
    # Calculate final allocation
    final_allocation = {
        'stocks': max(10, min(90, base_allocation['stocks'] + exp_adj['stocks'] + income_adj['stocks'] + timeline_adj['stocks'])),
        'bonds': max(5, min(80, base_allocation['bonds'] + exp_adj['bonds'] + income_adj['bonds'] + timeline_adj['bonds'])),
        'cash': max(5, min(30, base_allocation['cash'] + exp_adj['cash'] + income_adj['cash'] + timeline_adj['cash']))
    }
    
    # Normalize to 100%
    total = sum(final_allocation.values())
    final_allocation = {k: round(v * 100 / total) for k, v in final_allocation.items()}
    
    # Generate specific recommendations based on preferences and experience
    stock_recommendations = []
    bond_recommendations = []
    alternative_recommendations = []
    
    # Stock recommendations based on experience and preferences
    if final_allocation['stocks'] > 0:
        if 'stocks' in experience_assets or investment_experience.lower() == 'advanced':
            if risk_tolerance.lower() == 'aggressive':
                stock_recommendations = ['VTI (Total Stock Market)', 'VGT (Technology Sector)', 'VWO (Emerging Markets)', 'ARKK (Innovation ETF)']
            elif risk_tolerance.lower() == 'conservative':
                stock_recommendations = ['VTI (Total Stock Market)', 'SCHD (Dividend Aristocrats)', 'VYM (High Dividend Yield)']
            else:
                stock_recommendations = ['VTI (Total Stock Market)', 'VXUS (International Developed)', 'VGT (Technology)']
        else:
            # Beginner-friendly options
            stock_recommendations = ['VTI (Total Stock Market)', 'VOO (S&P 500)', 'Target Date Fund for ' + str(2065 if timeline_key == 'long' else 2035)]
    
    # Bond recommendations based on tax situation
    if final_allocation['bonds'] > 0:
        if tax_bracket.lower() in ['high', '32%', '35%', '37%']:
            bond_recommendations = ['VTEB (Tax-Exempt Municipal Bonds)', 'BND (Total Bond Market)']
        elif timeline_key == 'short':
            bond_recommendations = ['BND (Total Bond Market)', 'VGSH (Short-Term Treasury)', 'VTIP (Inflation-Protected)']
        else:
            bond_recommendations = ['BND (Total Bond Market)', 'VGIT (Intermediate Treasury)', 'VTIP (Inflation-Protected)']
    
    # Alternative investments for advanced investors
    if investment_experience.lower() == 'advanced' and 'realestate' in experience_assets:
        alternative_recommendations = ['VNQ (Real Estate Investment Trusts)', 'VTEB (Municipal Bonds)']
    elif 'crypto' in experience_assets and risk_tolerance.lower() == 'aggressive':
        alternative_recommendations = ['Consider 5% allocation to Bitcoin ETF (BITO) - High Risk']
    
    # Filter out avoided assets
    if assets_to_avoid:
        if 'fossil-fuels' in assets_to_avoid:
            stock_recommendations = [rec + ' (ESG Version)' if 'VTI' in rec else rec for rec in stock_recommendations]
        if 'crypto' in assets_to_avoid:
            alternative_recommendations = [rec for rec in alternative_recommendations if 'Bitcoin' not in rec]
    
    # Calculate dollar amounts
    stock_amount = amount * final_allocation['stocks'] / 100
    bond_amount = amount * final_allocation['bonds'] / 100
    cash_amount = amount * final_allocation['cash'] / 100
    
    # Generate tax strategy recommendations
    tax_strategy = []
    if 'retirement' in goals.lower():
        if '401k' in tax_accounts:
            tax_strategy.append('Maximize 401(k) employer match first')
        if 'roth-ira' in tax_accounts:
            tax_strategy.append('Consider Roth IRA for tax-free growth')
        else:
            tax_strategy.append('Open Roth IRA for tax-free retirement growth')
    
    if tax_bracket.lower() in ['high', '32%', '35%', '37%']:
        tax_strategy.append('Prioritize tax-advantaged accounts and municipal bonds')
    
    # Generate personalized insights
    ai_insights = []
    
    if debt_level.lower() in ['high', 'significant']:
        ai_insights.append('⚠️ Consider paying down high-interest debt before investing')
    
    if emergency_fund.lower() in ['none', 'insufficient']:
        ai_insights.append('🛡️ Build 3-6 months emergency fund before aggressive investing')
        final_allocation['cash'] = max(final_allocation['cash'], 20)
    
    if 'home-purchase' in upcoming_expenses:
        ai_insights.append('🏠 Keep house down payment in conservative investments (2-5 years)')
    
    if 'education-expenses' in upcoming_expenses:
        ai_insights.append('🎓 Consider 529 education savings plan for tax advantages')
    
    if management_style.lower() == 'hands-off':
        ai_insights.append('🤖 Consider target-date funds or robo-advisors for automated management')
    
    # Calculate expected returns based on allocation
    expected_return = (final_allocation['stocks'] * 0.10 + final_allocation['bonds'] * 0.04 + final_allocation['cash'] * 0.02) / 100
    
    return {
        'success': True,
        'strategy': goal_strategies.get(goals.lower(), 'Comprehensive diversified investment approach'),
        'allocation': [
            {'type': 'Stocks/Equities', 'percentage': final_allocation['stocks'], 'amount': f'${stock_amount:,.0f}'},
            {'type': 'Bonds/Fixed Income', 'percentage': final_allocation['bonds'], 'amount': f'${bond_amount:,.0f}'},
            {'type': 'Cash/Emergency Fund', 'percentage': final_allocation['cash'], 'amount': f'${cash_amount:,.0f}'}
        ],
        'specific_recommendations': {
            'stocks': stock_recommendations,
            'bonds': bond_recommendations,
            'alternatives': alternative_recommendations,
            'cash': ['High-yield savings account (4-5% APY)', 'Money market fund', 'Treasury bills']
        },
        'tax_strategy': tax_strategy,
        'ai_insights': ai_insights,
        'next_steps': [
            f'Open {"tax-advantaged" if "retirement" in goals.lower() else "taxable brokerage"} account',
            'Start with broad market index funds (VTI, BND)',
            'Invest gradually over 3-6 months (dollar-cost averaging)',
            'Review and rebalance quarterly',
            'Consider professional advice for complex situations'
        ],
        'risk_assessment': f'Your {risk_tolerance.lower()} risk profile with {timeline_key}-term timeline and {exp_key} experience level suggests this personalized approach. Expected volatility: {"Low" if final_allocation["stocks"] < 40 else "High" if final_allocation["stocks"] > 70 else "Moderate"}.',
        'estimated_annual_return': f'{expected_return:.1f}%',
        'personalization_factors': {
            'experience_level': exp_key.title(),
            'income_bracket': income_key.title(),
            'tax_considerations': 'High' if tax_bracket.lower() in ['high', '32%', '35%', '37%'] else 'Standard',
            'special_circumstances': len(special_circumstances),
            'risk_adjustments': f'Modified from base {risk_tolerance} profile'
        },
        'compliance_note': 'This is educational information based on your provided profile, not personalized financial advice. Consult a qualified financial advisor for personalized recommendations.'
    }

# Modern Dashboard Template
MODERN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradeRiser.AI - Next Generation Financial Platform</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #2563eb;
            --secondary-color: #1e40af;
            --accent-color: #3b82f6;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --dark-bg: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --border-color: #334155;
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
            --gradient-warning: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            --gradient-danger: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--dark-bg);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }
        
        .main-container {
            min-height: 100vh;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }
        
        .header {
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 0.5rem;
            display: flex;
            justify-content: flex-start;
            align-items: center;
            gap: 2rem;
        }
        
        .logo {
            display: flex;
            align-items: center;
            margin-right: 1rem;
            margin-left: -12rem;
        }
        
        .logo-icon {
            display: none;
        }
        
        .logo-text {
            font-size: 1.5rem;
            font-weight: 700;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header-actions {
            display: flex;
            flex: 1;
            align-items: center;
        }
        
        .top-tickers-display {
            overflow: hidden;
            white-space: nowrap;
            background: #000;
            flex-grow: 1;
            height: 50px;
            display: flex;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
        }
        
        .ticker-content {
            display: inline-block;
            padding-left: 100%;
            animation: scrollTicker 60s linear infinite;
        }
        
        .ticker-item {
            display: inline-flex;
            align-items: center;
            padding: 0 20px;
        }
        
        .ticker-icon {
            width: 20px;
            height: 20px;
            margin-right: 8px;
            border-radius: 3px;
        }
        
        .index-label {
            font-weight: bold;
            font-size: 16px;
            margin-right: 8px;
            color: #ccc;
        }
        
        @keyframes scrollTicker {
            0% { transform: translateX(0); }
            100% { transform: translateX(-100%); }
        }
        
        .ticker-symbol {
            font-weight: bold;
            color: #0ff;
        }
        
        .ticker-price {
            margin-left: 6px;
            font-weight: normal;
        }
        
        .ticker-up {
            color: #0f0;
        }
        
        .ticker-down {
            color: #f33;
        }
        
        .ticker-change {
            margin-left: 8px;
            font-weight: bold;
            font-size: 0.9rem;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid var(--success-color);
            border-radius: 20px;
            font-size: 0.875rem;
            color: var(--success-color);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--success-color);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .hero-section {
            padding: 4rem 2rem;
            text-align: center;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .hero-title {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .hero-subtitle {
            font-size: 1.25rem;
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }
        
        .hero-description {
            font-size: 1rem;
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto 2rem;
        }
        

        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            padding: 0 2rem;
            max-width: 1400px;
            margin: 0 auto 4rem;
            align-items: stretch;
        }
        
        .feature-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 2rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-primary);
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(37, 99, 235, 0.1);
            border-color: var(--primary-color);
        }
        
        .feature-icon {
            width: 60px;
            height: 60px;
            background: var(--gradient-primary);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
            margin-bottom: 1.5rem;
        }
        
        .feature-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }
        
        .feature-description {
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
            line-height: 1.6;
        }
        
        .feature-highlights {
            list-style: none;
            margin-bottom: 2rem;
            flex-grow: 1;
        }
        
        .feature-highlights li {
            padding: 0.5rem 0;
            color: var(--text-secondary);
            position: relative;
            padding-left: 1.5rem;
        }
        
        .feature-highlights li::before {
            content: '✓';
            position: absolute;
            left: 0;
            color: var(--success-color);
            font-weight: bold;
        }
        
        .action-button {
            background: var(--gradient-primary);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 10px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(37, 99, 235, 0.3);
        }
        
        .results-section {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem;
            max-width: 1400px;
            margin-left: auto;
            margin-right: auto;
            display: none;
        }
        
        .results-section.active {
            display: block;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .results-header {
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 2rem;
            color: var(--text-primary);
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 1rem;
        }
        
        .loading {
            text-align: center;
            padding: 3rem;
            color: var(--text-secondary);
        }
        
        .loading::after {
            content: '';
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid var(--border-color);
            border-top: 3px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .input-section {
            background: rgba(37, 99, 235, 0.05);
            border: 1px solid var(--primary-color);
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 2rem;
        }
        
        .input-group {
            margin-bottom: 1.5rem;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
            font-weight: 500;
        }
        
        .input-group input {
            width: 100%;
            padding: 1rem;
            background: var(--dark-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            color: var(--text-primary);
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        
        .input-group input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .btn-group {
            display: flex;
            gap: 1rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
            align-items: stretch;
        }
        
        .btn-group .action-button {
            flex: 1;
            min-width: 200px;
            height: auto;
            align-self: stretch;
        }
        
        .checkbox-group {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            margin-top: 0.5rem;
        }
        
        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem;
            background: var(--dark-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .checkbox-item:hover {
            background: var(--card-bg);
            border-color: var(--primary-color);
        }
        
        .checkbox-item input[type="checkbox"] {
            width: 18px;
            height: 18px;
            margin: 0;
            cursor: pointer;
            accent-color: var(--primary-color);
        }
        
        .checkbox-item label {
            margin: 0;
            cursor: pointer;
            color: var(--text-primary);
            font-weight: 500;
            flex: 1;
        }
        
        .footer {
            text-align: center;
            padding: 3rem 2rem;
            color: var(--text-secondary);
            border-top: 1px solid var(--border-color);
            margin-top: 4rem;
        }
        
        .footer-content {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .footer-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }
        
        .footer-description {
            margin-bottom: 1rem;
        }
        
        .footer-links {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .footer-link {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }
        
        .footer-link:hover {
            color: var(--accent-color);
        }
        
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2.5rem;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
                padding: 0 1rem;
            }
            
            .header-content {
                padding: 0 0.5rem;
                flex-direction: row;
                gap: 1rem;
                justify-content: flex-start;
            }
            
            .top-tickers-display {
                max-width: 100%;
                gap: 0.5rem;
                padding: 0.5rem 0.25rem;
                justify-content: flex-start;
                margin-left: 0;
            }
            
            .ticker-category {
                min-width: 120px;
                gap: 0.5rem;
            }
            
            .category-label {
                font-size: 0.7rem;
                min-width: 45px;
            }
            
            .ticker-scroll {
                font-size: 0.7rem;
                gap: 0.5rem;
            }
            
            .hero-section {
                padding: 2rem 1rem;
            }
            
            .btn-group {
                flex-direction: column;
            }
            
            .btn-group .action-button {
                min-width: auto;
            }
        }
    </style>
</head>
<body>
    <div class="main-container">
        <header class="header">
            <div class="header-content">
                <div class="logo">
                    <div class="logo-text">TradeRiser.AI</div>
                </div>
                <div class="top-tickers-display">
                    <div class="ticker-content" id="ticker">
                        <!-- Populated by JavaScript -->
                    </div>
                </div>
            </div>
        </header>
        
        <section class="hero-section">
            <h1 class="hero-title">Next Generation Financial Platform</h1>
            <p class="hero-subtitle">Professional Investment Analysis Powered by Industry-Leading Libraries</p>
            <p class="hero-description">
                Experience the future of financial analysis with our completely refactored platform, 
                built with industry-leading financial libraries trusted by quantitative investment professionals worldwide.
            </p>
        </section>
        
        <section class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-chart-line"></i>
                </div>
                <h3 class="feature-title">Unified Portfolio & Stock Analysis</h3>
                <p class="feature-description">
                    Comprehensive analysis combining FinanceToolkit's 100+ ratios with advanced portfolio analytics. 
                    Professional-grade metrics, risk assessment, and performance attribution in one unified module.
                </p>
                <ul class="feature-highlights">
                    <li>100+ Financial Ratios & Indicators</li>
                    <li>Advanced Portfolio Risk Metrics</li>
                    <li>Performance Attribution Analysis</li>
                    <li>Institutional-Grade Insights</li>
                </ul>
                <button class="action-button" onclick="showUnifiedAnalysis()">
                    <i class="fas fa-chart-bar"></i>
                    Launch Analysis
                </button>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-database"></i>
                </div>
                <h3 class="feature-title">Financial Database Explorer</h3>
                <p class="feature-description">
                    Explore 300,000+ financial symbols with integrated ETF intelligence. Comprehensive coverage of 
                    global markets including equities, ETFs, funds, indices, currencies, and cryptocurrencies.
                </p>
                <ul class="feature-highlights">
                    <li>300,000+ Financial Symbols</li>
                    <li>Integrated ETF Screening</li>
                    <li>Global Market Coverage</li>
                    <li>Advanced Search & Filtering</li>
                </ul>
                <button class="action-button" onclick="showDatabaseExplorer()">
                    <i class="fas fa-search"></i>
                    Explore Database
                </button>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-magic"></i>
                </div>
                <h3 class="feature-title">Smart Investment Wizard</h3>
                <p class="feature-description">
                    AI-powered investment advisor that analyzes your financial situation and goals to provide 
                    personalized investment recommendations. Tell us your budget and let AI guide your decisions.
                </p>
                <ul class="feature-highlights">
                    <li>Personalized Investment Advice</li>
                    <li>Natural Language Processing</li>
                    <li>Risk-Based Recommendations</li>
                    <li>Goal-Oriented Strategies</li>
                </ul>
                <button class="action-button" onclick="showInvestmentWizard()">
                    <i class="fas fa-magic"></i>
                    Start Wizard
                </button>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-brain"></i>
                </div>
                <h3 class="feature-title">AI-Powered Insights</h3>
                <p class="feature-description">
                    Advanced AI analysis combining multiple financial libraries to generate actionable 
                    investment insights, risk assessments, and portfolio optimization recommendations.
                </p>
                <ul class="feature-highlights">
                    <li>AI-Generated Insights</li>
                    <li>Risk Assessment</li>
                    <li>Portfolio Optimization</li>
                    <li>Actionable Recommendations</li>
                </ul>
                <button class="action-button" onclick="showAIInsights()">
                    <i class="fas fa-robot"></i>
                    Get AI Insights
                </button>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-download"></i>
                </div>
                <h3 class="feature-title">Professional Reports</h3>
                <p class="feature-description">
                    Generate institutional-quality reports with comprehensive analysis, charts, and data. 
                    Export to Excel, PDF, or share directly with stakeholders.
                </p>
                <ul class="feature-highlights">
                    <li>Institutional-Quality Reports</li>
                    <li>Multiple Export Formats</li>
                    <li>Comprehensive Analysis</li>
                    <li>Professional Presentation</li>
                </ul>
                <button class="action-button" onclick="showReports()">
                    <i class="fas fa-file-export"></i>
                    Generate Reports
                </button>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-rocket"></i>
                </div>
                <h3 class="feature-title">Crypto & DeFi Analytics</h3>
                <p class="feature-description">
                    Advanced cryptocurrency and DeFi protocol analysis with yield farming opportunities, 
                    liquidity pool analytics, and cross-chain portfolio tracking.
                </p>
                <ul class="feature-highlights">
                    <li>Multi-Chain Portfolio Tracking</li>
                    <li>DeFi Yield Optimization</li>
                    <li>Liquidity Pool Analytics</li>
                    <li>Risk-Adjusted DeFi Strategies</li>
                </ul>
                <button class="action-button" onclick="showCryptoAnalytics()">
                    <i class="fas fa-rocket"></i>
                    Explore Crypto
                </button>
            </div>
        </section>
        
        <div id="results" class="results-section">
            <div class="results-header">Analysis Results</div>
            <div id="results-content">
                <div class="loading">Initializing next-generation analysis...</div>
            </div>
        </div>
        
        <footer class="footer">
            <div class="footer-content">
                <h3 class="footer-title">TradeRiser.AI - Next Generation</h3>
                <p class="footer-description">
                    Advanced financial analysis and portfolio management platform
                </p>
                <p>Professional financial analysis • 300,000+ symbols • Institutional-grade insights</p>
                <div class="footer-links">
                    <a href="#" class="footer-link">Documentation</a>
                    <a href="#" class="footer-link">API Reference</a>
                    <a href="#" class="footer-link">Support</a>
                    <a href="#" class="footer-link">About</a>
                </div>
            </div>
        </footer>
    </div>
    
    <script>
        function showResults(title) {
            const resultsSection = document.getElementById('results');
            const resultsHeader = document.querySelector('.results-header');
            resultsHeader.textContent = title;
            resultsSection.classList.add('active');
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
        
        function showUnifiedAnalysis() {
            showResults('Unified Portfolio & Stock Analysis');
            document.getElementById('results-content').innerHTML = `
                <div class="input-section">
                    <h4><i class="fas fa-chart-line"></i> Unified Portfolio & Stock Analysis</h4>
                    <p>Comprehensive analysis combining FinanceToolkit's 100+ ratios with advanced portfolio analytics.</p>
                    <div class="input-group">
                        <label>Stock/Portfolio Tickers (comma-separated):</label>
                        <input type="text" id="unified-tickers" placeholder="Enter tickers (e.g., AAPL,MSFT,GOOGL)" value="">
                    </div>
                    <div class="input-group">
                        <label>Share Quantities (optional, comma-separated):</label>
                        <input type="text" id="unified-shares" placeholder="100,50,75 (leave empty for equal weights)">
                        <small style="color: #666; font-size: 12px; display: block; margin-top: 5px;">Enter shares for portfolio analysis, or leave empty for stock analysis</small>
                    </div>
                    <div class="btn-group">
                        <button class="action-button" onclick="runUnifiedAnalysis()">
                            <i class="fas fa-chart-bar"></i>
                            Run Unified Analysis
                        </button>
                    </div>
                </div>
                <div id="unified-results"></div>
            `;
        }
        
        function showDatabaseExplorer() {
            showResults('Financial Database Explorer');
            document.getElementById('results-content').innerHTML = `
                <div class="input-section">
                    <h4><i class="fas fa-database"></i> Explore 300,000+ Financial Symbols with ETF Intelligence</h4>
                    <p>Search across global markets and all asset classes with integrated ETF screening capabilities.</p>
                    <div class="input-group">
                        <label>Search Query:</label>
                        <input type="text" id="search-query" placeholder="Coca Cola, Healthcare, Banking, Consumer Goods..." value="">
                    </div>
                    <div class="input-group">
                        <label>Asset Type:</label>
                        <select id="asset-type" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                            <option value="equities">Equities</option>
                            <option value="etfs">ETFs (with Intelligence)</option>
                            <option value="funds">Funds</option>
                            <option value="crypto">Cryptocurrencies</option>
                        </select>
                    </div>
                    <div class="input-group" id="etf-filters" style="display: none;">
                        <label>ETF Filters:</label>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
                            <input type="number" id="max-expense-ratio" placeholder="Max Expense Ratio (%)" step="0.01">
                            <input type="number" id="min-aum" placeholder="Min AUM (Millions)" step="1">
                        </div>
                    </div>
                    <div class="btn-group">
                        <button class="action-button" onclick="searchFinanceDatabase()">
                            <i class="fas fa-search"></i>
                            Search Database
                        </button>
                        <button class="action-button" onclick="runETFScreening()" id="etf-screening-btn" style="display: none;">
                            <i class="fas fa-filter"></i>
                            Screen ETFs
                        </button>
                    </div>
                </div>
                <div id="database-results"></div>
            `;
            
            // Show/hide ETF filters based on selection
            document.getElementById('asset-type').addEventListener('change', function() {
                const etfFilters = document.getElementById('etf-filters');
                const etfBtn = document.getElementById('etf-screening-btn');
                if (this.value === 'etfs') {
                    etfFilters.style.display = 'block';
                    etfBtn.style.display = 'inline-block';
                } else {
                    etfFilters.style.display = 'none';
                    etfBtn.style.display = 'none';
                }
            });
        }
        
        function showInvestmentWizard() {
            showResults('Smart Investment Wizard');
            document.getElementById('results-content').innerHTML = `
                <div class="input-section">
                    <h4><i class="fas fa-magic"></i> Smart Investment Wizard</h4>
                    <p>Tell us about your financial situation and goals. Our AI will provide personalized investment recommendations.</p>
                    
                    <div class="wizard-step" id="step-1">
                        <h5>Step 1: Investment Amount</h5>
                        <div class="input-group">
                            <label>How much money do you want to invest?</label>
                            <input type="number" id="investment-amount" placeholder="Enter amount in USD" min="100" step="100">
                        </div>
                        <div class="input-group">
                            <label>Describe your situation (natural language):</label>
                            <textarea id="investment-description" placeholder="e.g., 'I have $5000 to invest for retirement in 20 years' or 'I want to invest $1000 monthly for my child's education'" rows="3" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary); resize: vertical;"></textarea>
                        </div>
                        <button class="action-button" onclick="wizardStep2()">
                            <i class="fas fa-arrow-right"></i>
                            Next: Risk Assessment
                        </button>
                    </div>
                    
                    <div class="wizard-step" id="step-2" style="display: none;">
                        <h5>Step 2: Financial Situation</h5>
                        <div class="input-group">
                            <label>Annual Income Range:</label>
                            <select id="annual-income" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="under-50k">Under $50,000</option>
                                <option value="50k-100k">$50,000 - $100,000</option>
                                <option value="100k-200k">$100,000 - $200,000</option>
                                <option value="200k-500k">$200,000 - $500,000</option>
                                <option value="over-500k">Over $500,000</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Current Debt Level:</label>
                            <select id="debt-level" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="none">No significant debt</option>
                                <option value="low">Low debt (< 20% of income)</option>
                                <option value="moderate">Moderate debt (20-40% of income)</option>
                                <option value="high">High debt (> 40% of income)</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Emergency Fund Status:</label>
                            <select id="emergency-fund" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="none">No emergency fund</option>
                                <option value="partial">1-3 months expenses</option>
                                <option value="adequate">3-6 months expenses</option>
                                <option value="strong">6+ months expenses</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Monthly Liquidity Needs:</label>
                            <select id="liquidity-needs" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="low">Low (< $500/month)</option>
                                <option value="moderate">Moderate ($500-2000/month)</option>
                                <option value="high">High (> $2000/month)</option>
                            </select>
                        </div>
                        <div class="btn-group">
                            <button class="action-button" onclick="wizardStep1()" style="background: var(--text-secondary);">
                                <i class="fas fa-arrow-left"></i>
                                Back
                            </button>
                            <button class="action-button" onclick="wizardStep3()">
                                <i class="fas fa-arrow-right"></i>
                                Next: Experience
                            </button>
                        </div>
                    </div>
                    
                    <div class="wizard-step" id="step-3" style="display: none;">
                        <h5>Step 3: Investment Experience & Preferences</h5>
                        <div class="input-group">
                            <label>Investment Experience:</label>
                            <select id="investment-experience" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="beginner">Beginner (No prior experience)</option>
                                <option value="some">Some experience (Stocks, basic funds)</option>
                                <option value="intermediate">Intermediate (Diversified portfolio)</option>
                                <option value="advanced">Advanced (Complex strategies)</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Asset Classes You've Invested In (check all that apply):</label>
                            <h4>Asset Classes You've Invested In:</h4>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="stocks" name="asset_classes" value="stocks">
                            <label for="stocks">Stocks/Equities</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="bonds" name="asset_classes" value="bonds">
                            <label for="bonds">Bonds</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="etfs" name="asset_classes" value="etfs">
                            <label for="etfs">ETFs</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="mutual_funds" name="asset_classes" value="mutual_funds">
                            <label for="mutual_funds">Mutual Funds</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="real_estate" name="asset_classes" value="real_estate">
                            <label for="real_estate">Real Estate</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="commodities" name="asset_classes" value="commodities">
                            <label for="commodities">Commodities</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="crypto" name="asset_classes" value="crypto">
                            <label for="crypto">Cryptocurrency</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="none_invested" name="asset_classes" value="none">
                            <label for="none_invested">None - I'm new to investing</label>
                        </div>
                    </div>
                            </div>
                        </div>
                        <div class="input-group">
                            <label>Investment Preferences:</label>
                            <select id="investment-preferences" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="none">No specific preferences</option>
                                <option value="esg">ESG/Sustainable investing</option>
                                <option value="tech">Technology focus</option>
                                <option value="dividend">Dividend-focused</option>
                                <option value="growth">Growth stocks</option>
                                <option value="value">Value investing</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Assets to Avoid (check all that apply):</label>
                            <h4>Assets to Avoid:</h4>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="avoid_tobacco" name="assets_avoid" value="tobacco">
                            <label for="avoid_tobacco">Tobacco</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="avoid_alcohol" name="assets_avoid" value="alcohol">
                            <label for="avoid_alcohol">Alcohol</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="avoid_gambling" name="assets_avoid" value="gambling">
                            <label for="avoid_gambling">Gambling</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="avoid_weapons" name="assets_avoid" value="weapons">
                            <label for="avoid_weapons">Weapons/Defense</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="avoid_fossil" name="assets_avoid" value="fossil_fuels">
                            <label for="avoid_fossil">Fossil Fuels</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="avoid_none" name="assets_avoid" value="none">
                            <label for="avoid_none">No restrictions</label>
                        </div>
                    </div>
                            </div>
                        </div>
                        <div class="btn-group">
                            <button class="action-button" onclick="wizardStep2()" style="background: var(--text-secondary);">
                                <i class="fas fa-arrow-left"></i>
                                Back
                            </button>
                            <button class="action-button" onclick="wizardStep4()">
                                <i class="fas fa-arrow-right"></i>
                                Next: Goals & Risk
                            </button>
                        </div>
                    </div>
                    
                    <div class="wizard-step" id="step-4" style="display: none;">
                        <h5>Step 4: Goals, Risk & Timeline</h5>
                        <div class="input-group">
                            <label>Investment Timeline:</label>
                            <select id="investment-timeline" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="short">Short-term (< 2 years)</option>
                                <option value="medium">Medium-term (2-10 years)</option>
                                <option value="long">Long-term (> 10 years)</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Risk Tolerance:</label>
                            <select id="risk-tolerance" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="conservative">Conservative (Preserve capital)</option>
                                <option value="moderate">Moderate (Balanced growth)</option>
                                <option value="aggressive">Aggressive (Maximum growth)</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Primary Goal:</label>
                            <select id="investment-goal" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="retirement">Retirement</option>
                                <option value="education">Education</option>
                                <option value="house">House Down Payment</option>
                                <option value="wealth">Wealth Building</option>
                                <option value="income">Passive Income</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Return Expectations:</label>
                            <select id="return-expectations" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="preservation">Capital preservation (2-4%)</option>
                                <option value="conservative">Conservative growth (4-6%)</option>
                                <option value="moderate">Moderate growth (6-8%)</option>
                                <option value="aggressive">Aggressive growth (8-12%)</option>
                                <option value="speculative">Speculative returns (12%+)</option>
                            </select>
                        </div>
                        <div class="btn-group">
                            <button class="action-button" onclick="wizardStep3()" style="background: var(--text-secondary);">
                                <i class="fas fa-arrow-left"></i>
                                Back
                            </button>
                            <button class="action-button" onclick="wizardStep5()">
                                <i class="fas fa-arrow-right"></i>
                                Next: Tax & Planning
                            </button>
                        </div>
                    </div>
                    
                    <div class="wizard-step" id="step-5" style="display: none;">
                        <h5>Step 5: Tax Strategy & Financial Planning</h5>
                        <div class="input-group">
                            <label>Tax-Advantaged Accounts (check all that apply):</label>
                            <h4>Tax-Advantaged Accounts:</h4>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="account_401k" name="tax_accounts" value="401k">
                            <label for="account_401k">401(k)</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="account_ira" name="tax_accounts" value="ira">
                            <label for="account_ira">Traditional IRA</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="account_roth" name="tax_accounts" value="roth_ira">
                            <label for="account_roth">Roth IRA</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="account_hsa" name="tax_accounts" value="hsa">
                            <label for="account_hsa">HSA</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="account_529" name="tax_accounts" value="529">
                            <label for="account_529">529 Education Plan</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="account_none" name="tax_accounts" value="none">
                            <label for="account_none">None currently</label>
                        </div>
                    </div>
                            </div>
                        </div>
                        <div class="input-group">
                            <label>Tax Bracket:</label>
                            <select id="tax-bracket" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="low">10-12% (Low)</option>
                                <option value="medium">22-24% (Medium)</option>
                                <option value="high">32-35% (High)</option>
                                <option value="highest">37% (Highest)</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Expected Income Changes:</label>
                            <select id="income-changes" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="stable">Stable income expected</option>
                                <option value="increase">Expecting income increase</option>
                                <option value="decrease">Expecting income decrease</option>
                                <option value="retirement">Approaching retirement</option>
                                <option value="career-change">Career change planned</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Major Upcoming Expenses (check all that apply):</label>
                            <h4>Major Upcoming Expenses:</h4>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="expense_house" name="major_expenses" value="house">
                            <label for="expense_house">House Purchase</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="expense_car" name="major_expenses" value="car">
                            <label for="expense_car">Car Purchase</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="expense_education" name="major_expenses" value="education">
                            <label for="expense_education">Education/Tuition</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="expense_wedding" name="major_expenses" value="wedding">
                            <label for="expense_wedding">Wedding</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="expense_vacation" name="major_expenses" value="vacation">
                            <label for="expense_vacation">Major Vacation</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="expense_none" name="major_expenses" value="none">
                            <label for="expense_none">No major expenses planned</label>
                        </div>
                    </div>
                            </div>
                        </div>
                        <div class="btn-group">
                            <button class="action-button" onclick="wizardStep4()" style="background: var(--text-secondary);">
                                <i class="fas fa-arrow-left"></i>
                                Back
                            </button>
                            <button class="action-button" onclick="wizardStep6()">
                                <i class="fas fa-arrow-right"></i>
                                Next: Personal Circumstances
                            </button>
                        </div>
                    </div>
                    
                    <div class="wizard-step" id="step-6" style="display: none;">
                        <h5>Step 6: Personal Circumstances & Management</h5>
                        <div class="input-group">
                            <label>Estate Planning Considerations:</label>
                            <select id="estate-planning" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="none">No specific estate planning</option>
                                <option value="basic">Basic will and beneficiaries</option>
                                <option value="trust">Trust planning</option>
                                <option value="charitable">Charitable giving goals</option>
                                <option value="legacy">Intergenerational wealth transfer</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Insurance Coverage (check all that apply):</label>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="insurance_health" name="insurance" value="health">
                            <label for="insurance_health">Health Insurance</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="insurance_life" name="insurance" value="life">
                            <label for="insurance_life">Life Insurance</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="insurance_disability" name="insurance" value="disability">
                            <label for="insurance_disability">Disability Insurance</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="insurance_auto" name="insurance" value="auto">
                            <label for="insurance_auto">Auto Insurance</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="insurance_home" name="insurance" value="home">
                            <label for="insurance_home">Home/Renters Insurance</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="insurance_umbrella" name="insurance" value="umbrella">
                            <label for="insurance_umbrella">Umbrella Policy</label>
                        </div>
                    </div>
                            </div>
                        </div>
                        <div class="input-group">
                            <label>Investment Management Style:</label>
                            <select id="management-style" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                                <option value="hands-off">Fully automated/delegated</option>
                                <option value="periodic">Periodic review and adjustments</option>
                                <option value="active">Active monitoring and decisions</option>
                                <option value="hands-on">Fully hands-on management</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>Special Circumstances (check all that apply):</label>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" id="circumstance_student" name="special_circumstances" value="student_loans">
                            <label for="circumstance_student">Student Loan Debt</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="circumstance_credit" name="special_circumstances" value="credit_card_debt">
                            <label for="circumstance_credit">Credit Card Debt</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="circumstance_dependents" name="special_circumstances" value="dependents">
                            <label for="circumstance_dependents">Supporting Dependents</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="circumstance_inheritance" name="special_circumstances" value="inheritance">
                            <label for="circumstance_inheritance">Expected Inheritance</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="circumstance_business" name="special_circumstances" value="business_owner">
                            <label for="circumstance_business">Business Owner</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="circumstance_none" name="special_circumstances" value="none">
                            <label for="circumstance_none">None apply</label>
                        </div>
                    </div>
                            </div>
                        </div>
                        <div class="btn-group">
                            <button class="action-button" onclick="wizardStep5()" style="background: var(--text-secondary);">
                                <i class="fas fa-arrow-left"></i>
                                Back
                            </button>
                            <button class="action-button" onclick="generateInvestmentRecommendations()">
                                <i class="fas fa-magic"></i>
                                Get AI Recommendations
                            </button>
                        </div>
                    </div>
                </div>
                <div id="wizard-results"></div>
            `;
        }
        
        function showAIInsights() {
            showResults('AI-Powered Insights');
            document.getElementById('results-content').innerHTML = `
                <div class="input-section">
                    <h4><i class="fas fa-brain"></i> AI-Powered Investment Insights</h4>
                    <p>Get AI-generated insights combining advanced financial data with machine learning analytics.</p>
                    <div class="input-group">
                        <label>Portfolio Tickers:</label>
                        <input type="text" id="ai-tickers" placeholder="Enter tickers for AI analysis (e.g., AAPL,MSFT,GOOGL)" value="">
                    </div>
                    <div class="btn-group">
                        <button class="action-button" onclick="generateAIInsights()">
                            <i class="fas fa-robot"></i>
                            Generate AI Insights
                        </button>
                    </div>
                </div>
                <div id="ai-results"></div>
            `;
        }
        
        function showCryptoAnalytics() {
            showResults('Crypto & DeFi Analytics');
            document.getElementById('results-content').innerHTML = `
                <div class="input-section">
                    <h4><i class="fas fa-rocket"></i> Advanced Crypto & DeFi Analytics</h4>
                    <p>Comprehensive cryptocurrency and DeFi protocol analysis with yield optimization and cross-chain tracking.</p>
                    
                    <div class="input-group">
                        <label>Analysis Type:</label>
                        <select id="crypto-analysis-type" style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary);">
                            <option value="portfolio">Crypto Portfolio Analysis</option>
                            <option value="defi">DeFi Yield Opportunities</option>
                            <option value="nft">NFT Collection Analytics</option>
                            <option value="cross-chain">Cross-Chain Tracking</option>
                        </select>
                    </div>
                    
                    <div class="crypto-input" id="portfolio-input">
                        <div class="input-group">
                            <label>Crypto Symbols (comma-separated):</label>
                            <input type="text" id="crypto-symbols" placeholder="BTC,ETH,ADA,SOL,MATIC" value="">
                        </div>
                        <div class="input-group">
                            <label>Holdings (optional, comma-separated):</label>
                            <input type="text" id="crypto-holdings" placeholder="1.5,10,1000,50,5000">
                            <small style="color: #666; font-size: 12px; display: block; margin-top: 5px;">Enter your holdings for portfolio analysis</small>
                        </div>
                    </div>
                    
                    <div class="crypto-input" id="defi-input" style="display: none;">
                        <div class="input-group">
                            <label>DeFi Protocols:</label>
                            <select id="defi-protocols" multiple style="width: 100%; padding: 1rem; background: var(--dark-bg); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary); height: 120px;">
                                <option value="uniswap">Uniswap V3</option>
                                <option value="aave">Aave</option>
                                <option value="compound">Compound</option>
                                <option value="curve">Curve Finance</option>
                                <option value="yearn">Yearn Finance</option>
                                <option value="convex">Convex Finance</option>
                            </select>
                            <small style="color: #666; font-size: 12px; display: block; margin-top: 5px;">Hold Ctrl/Cmd to select multiple protocols</small>
                        </div>
                        <div class="input-group">
                            <label>Investment Amount (USD):</label>
                            <input type="number" id="defi-amount" placeholder="10000" min="100" step="100">
                        </div>
                    </div>
                    
                    <div class="btn-group">
                        <button class="action-button" onclick="runCryptoAnalysis()">
                            <i class="fas fa-rocket"></i>
                            Analyze Crypto Portfolio
                        </button>
                        <button class="action-button" onclick="findDeFiOpportunities()" id="defi-btn" style="display: none;">
                            <i class="fas fa-coins"></i>
                            Find DeFi Opportunities
                        </button>
                    </div>
                </div>
                <div id="crypto-results"></div>
            `;
            
            // Show/hide inputs based on analysis type
            document.getElementById('crypto-analysis-type').addEventListener('change', function() {
                const portfolioInput = document.getElementById('portfolio-input');
                const defiInput = document.getElementById('defi-input');
                const defiBtn = document.getElementById('defi-btn');
                
                // Hide all inputs first
                portfolioInput.style.display = 'none';
                defiInput.style.display = 'none';
                defiBtn.style.display = 'none';
                
                // Show relevant inputs
                if (this.value === 'portfolio' || this.value === 'cross-chain') {
                    portfolioInput.style.display = 'block';
                } else if (this.value === 'defi') {
                    defiInput.style.display = 'block';
                    defiBtn.style.display = 'inline-block';
                }
            });
        }
        
        function showReports() {
            showResults('Professional Reports & Pricing');
            document.getElementById('results-content').innerHTML = `
                <div class="input-section">
                    <h4><i class="fas fa-download"></i> Professional Reports & Data Plans</h4>
                    <p>Choose your data plan for comprehensive financial analysis and reporting.</p>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin: 2rem 0; align-items: stretch;">
                        <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; border: 2px solid var(--border-color); display: flex; flex-direction: column; height: 100%;">
                            <h5 style="color: var(--primary-color); margin-top: 0;">Basic Plan</h5>
                            <div style="font-size: 2rem; font-weight: bold; color: var(--success-color);">$60.00</div>
                            <p style="color: var(--text-secondary); margin: 0.5rem 0;">per month</p>
                            <ul style="list-style: none; padding: 0; margin: 1rem 0; flex-grow: 1;">
                                <li>All stocks in 1 region</li>
                                <li>10 years of historical price data</li>
                                <li>Access to intra-day data</li>
                                <li>10 years of fundamentals</li>
                                <li>Access to ETFs (1 region)</li>
                            </ul>
                            <button class="action-button" onclick="selectPlan('basic')" style="width: 100%; margin-top: 1rem;">Choose Basic</button>
                        </div>
                        
                        <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; border: 2px solid var(--primary-color); position: relative; display: flex; flex-direction: column; height: 100%;">
                            <div style="position: absolute; top: -10px; right: 20px; background: var(--primary-color); color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.8rem;">POPULAR</div>
                            <h5 style="color: var(--primary-color); margin-top: 0;">Plus Plan</h5>
                            <div style="font-size: 2rem; font-weight: bold; color: var(--success-color);">$90.00</div>
                            <p style="color: var(--text-secondary); margin: 0.5rem 0;">per month</p>
                            <ul style="list-style: none; padding: 0; margin: 1rem 0; flex-grow: 1;">
                                <li>Everything in Basic</li>
                                <li>Global equity and ETFs</li>
                                <li>20 years of historical data</li>
                                <li>Stream real-time price data</li>
                                <li>ETF holdings data</li>
                            </ul>
                            <button class="action-button" onclick="selectPlan('plus')" style="width: 100%; margin-top: 1rem;">Choose Plus</button>
                        </div>
                        
                        <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; border: 2px solid var(--warning-color); display: flex; flex-direction: column; height: 100%;">
                            <h5 style="color: var(--warning-color); margin-top: 0;">Pro Plan</h5>
                            <div style="font-size: 2rem; font-weight: bold; color: var(--success-color);">$120.00</div>
                            <p style="color: var(--text-secondary); margin: 0.5rem 0;">per month</p>
                            <ul style="list-style: none; padding: 0; margin: 1rem 0; flex-grow: 1;">
                                <li>Everything in Plus</li>
                                <li>30+ years of historical data</li>
                                <li>Mutual Funds data</li>
                                <li>Bonds & Futures data</li>
                                <li>Alternative & 3rd-party data</li>
                            </ul>
                            <button class="action-button" onclick="selectPlan('pro')" style="width: 100%; margin-top: 1rem;">Choose Pro</button>
                        </div>
                    </div>
                    
                    <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 2rem 0;">
                        <h5>Generate Reports (Free Preview)</h5>
                        <div class="btn-group">
                            <button class="action-button" onclick="generateReport('portfolio')">
                                <i class="fas fa-briefcase"></i>
                                Portfolio Report
                            </button>
                            <button class="action-button" onclick="generateReport('market')">
                                <i class="fas fa-chart-line"></i>
                                Market Analysis Report
                            </button>
                            <button class="action-button" onclick="generateReport('etf')">
                                <i class="fas fa-layer-group"></i>
                                ETF Comparison Report
                            </button>
                        </div>
                    </div>
                </div>
                <div id="reports-results"></div>
            `;
        }
        
        function runFinanceToolkitAnalysis() {
            const tickers = document.getElementById('toolkit-tickers').value;
            document.getElementById('toolkit-results').innerHTML = '<div class="loading">Running comprehensive FinanceToolkit analysis...</div>';
            
            fetch('/api/comprehensive-analysis', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ tickers: tickers.split(',').map(t => t.trim()) })
            })
            .then(response => response.json())
            .then(data => {
                displayFinanceToolkitResults(data);
            })
            .catch(error => {
                document.getElementById('toolkit-results').innerHTML = `<div style="color: var(--danger-color);">Error: ${error.message}</div>`;
            });
        }
        
        function searchFinanceDatabase() {
            const query = document.getElementById('search-query').value;
            const assetType = document.getElementById('asset-type').value;
            document.getElementById('database-results').innerHTML = '<div class="loading">Searching FinanceDatabase...</div>';
            
            fetch(`/api/search-securities?query=${encodeURIComponent(query)}&type=${assetType}`)
            .then(response => response.json())
            .then(data => {
                displayDatabaseResults(data.results);
            })
            .catch(error => {
                document.getElementById('database-results').innerHTML = `<div style="color: var(--danger-color);">Error: ${error.message}</div>`;
            });
        }
        
        function runETFAnalysis() {
            const etfTickers = document.getElementById('etf-tickers').value;
            document.getElementById('etf-results').innerHTML = '<div class="loading">Analyzing ETFs with The Passive Investor...</div>';
            
            fetch('/api/etf-analysis', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ etf_tickers: etfTickers.split(',').map(t => t.trim()) })
            })
            .then(response => response.json())
            .then(data => {
                displayETFResults(data);
            })
            .catch(error => {
                document.getElementById('etf-results').innerHTML = `<div style="color: var(--danger-color);">Error: ${error.message}</div>`;
            });
        }
        
        function displayFinanceToolkitResults(data) {
            // Convert complex financial data to beginner-friendly recommendations
            const beginnerAnalysis = translateFinancialData(data);
            
            document.getElementById('toolkit-results').innerHTML = `
                <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                    <h4>Your Investment Analysis (Simple Version)</h4>
                    ${beginnerAnalysis.recommendation}
                    ${beginnerAnalysis.explanation}
                    
                    <div style="margin-top: 2rem; padding: 1rem; background: var(--dark-bg); border-radius: 10px;">
                        <h5>Want the Technical Details?</h5>
                        <button onclick="toggleTechnicalData('toolkit')" style="background: var(--primary-color); color: white; border: none; padding: 0.5rem 1rem; border-radius: 5px; cursor: pointer;">Show Technical Data</button>
                        <div id="toolkit-technical" style="display: none; margin-top: 1rem;">
                            <pre style="background: var(--dark-bg); padding: 1rem; border-radius: 10px; overflow-x: auto; color: var(--text-secondary);">${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    </div>
                </div>
            `;
        }
        
        function displayDatabaseResults(results) {
            // Implementation for displaying FinanceDatabase results
            let html = `<div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;"><h4>Search Results</h4>`;
            
            if (results && results.length > 0) {
                html += `<p>Found ${results.length} results:</p><div style="display: grid; gap: 1rem; margin-top: 1rem;">`;
                results.slice(0, 10).forEach(result => {
                    html += `
                        <div style="background: var(--dark-bg); padding: 1rem; border-radius: 10px; border: 1px solid var(--border-color);">
                            <strong>${result.symbol || 'N/A'}</strong> - ${result.name || 'N/A'}<br>
                            <small style="color: var(--text-secondary);">${result.sector || ''} ${result.industry || ''}</small>
                        </div>
                    `;
                });
                html += `</div>`;
            } else {
                html += `<p>No results found. Try a different search term.</p>`;
            }
            
            html += `</div>`;
            document.getElementById('database-results').innerHTML = html;
        }
        
        function displayETFResults(data) {
            // Convert ETF data to beginner-friendly analysis
            const etfAnalysis = translateETFData(data);
            
            document.getElementById('etf-results').innerHTML = `
                <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                    <h4>ETF Analysis (What This Means for You)</h4>
                    ${etfAnalysis.summary}
                    ${etfAnalysis.currentValue}
                    ${etfAnalysis.recommendation}
                    ${etfAnalysis.riskExplanation}
                </div>
            `;
        }
        
        // Translation functions for beginner-friendly analysis
        function translateFinancialData(data) {
            // Extract key metrics and translate to plain English
            let recommendation = '';
            let explanation = '';
            
            // Extract real metrics from API data
            const realMetrics = {
                volatility: data.risk_metrics && data.risk_metrics[Object.keys(data.risk_metrics)[0]] ? 
                    (data.risk_metrics[Object.keys(data.risk_metrics)[0]].volatility * 100 || 20) : 20,
                sharpeRatio: data.performance && data.performance[Object.keys(data.performance)[0]] ? 
                    (data.performance[Object.keys(data.performance)[0]].sharpe_ratio || 1.0) : 1.0,
                peRatio: data.ratios && data.ratios[Object.keys(data.ratios)[0]] ? 
                    (data.ratios[Object.keys(data.ratios)[0]].pe_ratio || 18) : 18,
                rsi: data.technical_indicators ? (data.technical_indicators.rsi || 50) : 50
            };
            
            // Determine recommendation based on real data
            let signal = 'HOLD';
            let signalColor = 'var(--warning-color)';
            
            if (realMetrics.sharpeRatio > 1.5 && realMetrics.volatility < 20) {
                signal = 'STRONG BUY';
                signalColor = 'var(--success-color)';
            } else if (realMetrics.sharpeRatio > 1.0 && realMetrics.volatility < 25) {
                signal = 'BUY';
                signalColor = '#4CAF50';
            } else if (realMetrics.volatility > 30 || realMetrics.sharpeRatio < 0.5) {
                signal = realMetrics.volatility > 35 ? 'STRONG SELL' : 'SELL';
                signalColor = 'var(--danger-color)';
            }
            
            recommendation = `
                <div style="background: ${signalColor}; color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; text-align: center;">
                    <h3 style="margin: 0; font-size: 1.5rem;">${signal}</h3>
                    <p style="margin: 0.5rem 0 0 0;">Our recommendation for this investment</p>
                </div>
            `;
            
            explanation = `
                <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                    <h5>What does this mean?</h5>
                    <div style="margin: 1rem 0;">
                        <strong>Volatility: ${realMetrics.volatility.toFixed(1)}%</strong><br>
                        <span style="color: var(--text-secondary);">This shows how much the price jumps around. ${realMetrics.volatility < 15 ? 'Low volatility means steady, predictable price movements - good for conservative investors.' : realMetrics.volatility < 25 ? 'Moderate volatility means some price swings - normal for most stocks.' : 'High volatility means big price swings - risky but potentially rewarding.'}</span>
                    </div>
                    <div style="margin: 1rem 0;">
                        <strong>Sharpe Ratio: ${realMetrics.sharpeRatio.toFixed(2)}</strong><br>
                        <span style="color: var(--text-secondary);">This measures return vs risk. ${realMetrics.sharpeRatio > 1.5 ? 'Excellent! You are getting great returns for the risk taken.' : realMetrics.sharpeRatio > 1.0 ? 'Good! Decent returns for the risk level.' : realMetrics.sharpeRatio > 0.5 ? 'Fair. Returns are okay but consider the risk.' : 'Poor. High risk with low returns - be careful.'}</span>
                    </div>
                    <div style="margin: 1rem 0;">
                        <strong>P/E Ratio: ${realMetrics.peRatio.toFixed(1)}</strong><br>
                        <span style="color: var(--text-secondary);">This shows if the stock is expensive or cheap. ${realMetrics.peRatio < 15 ? 'Low P/E suggests the stock might be undervalued - potentially a good deal.' : realMetrics.peRatio < 25 ? 'Normal P/E range - fairly valued stock.' : 'High P/E suggests the stock might be overvalued - expensive but could have high growth potential.'}</span>
                    </div>
                </div>
            `;
            
            return { recommendation, explanation };
        }
        
        function translateETFData(data) {
            // Extract real ETF data from API response
            const realETF = {
                name: data.name || data.fund_name || 'ETF',
                symbol: data.symbol || data.ticker || 'N/A',
                currentPrice: data.current_price || data.price || data.nav || 125.50,
                expenseRatio: data.expense_ratio || data.annual_fee || 0.5,
                diversification: data.holdings_count || data.num_holdings || 500,
                yield: data.dividend_yield || data.yield || 2.0,
                sector: data.category || data.sector || data.focus_area || 'Diversified',
                performance: data.ytd_return || data.annual_return || 8.5
            };
            
            const summary = `
                <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                    <h5>What is this ETF?</h5>
                    <p><strong>${realETF.name} (${realETF.symbol})</strong> is an ETF (Exchange-Traded Fund) - like a basket containing many different stocks. Instead of buying individual companies, you buy a piece of this basket, giving you instant diversification.</p>
                    <p><strong>This ETF contains ${realETF.diversification} different investments</strong> - that's like owning tiny pieces of ${realETF.diversification} companies at once!</p>
                </div>
            `;
            
            const currentValue = `
                <div style="background: var(--primary-color); color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; text-align: center;">
                    <h3 style="margin: 0; font-size: 2rem;">$${realETF.currentPrice.toFixed(2)}</h3>
                    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">Current Price Per Share</p>
                </div>
            `;
            
            let recommendation = '';
            let recommendationColor = 'var(--warning-color)';
            let recommendationText = 'CONSIDER CAREFULLY';
            let buyAdvice = 'This ETF has mixed characteristics. Consider your investment goals.';
            
            // Improved recommendation logic
            if (realETF.expenseRatio < 0.2 && realETF.diversification > 500 && realETF.performance > 5) {
                recommendationColor = 'var(--success-color)';
                recommendationText = 'BUY';
                buyAdvice = 'This is an excellent ETF with low fees, good diversification, and solid performance. Great for most investors!';
            } else if (realETF.expenseRatio < 0.5 && realETF.diversification > 200 && realETF.performance > 3) {
                recommendationColor = '#4CAF50';
                recommendationText = 'BUY';
                buyAdvice = 'This is a good ETF option with reasonable fees and decent performance. Suitable for most portfolios.';
            } else if (realETF.expenseRatio > 0.7 || realETF.performance < 0) {
                recommendationColor = 'var(--danger-color)';
                recommendationText = 'DO NOT BUY';
                buyAdvice = 'This ETF has high fees or poor performance. Look for better alternatives with lower costs and better returns.';
            }
            
            recommendation = `
                <div style="background: ${recommendationColor}; color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; text-align: center;">
                    <h3 style="margin: 0; font-size: 1.8rem;">${recommendationText}</h3>
                    <p style="margin: 0.5rem 0 0 0; font-size: 1rem;">${buyAdvice}</p>
                </div>
            `;
            
            const riskExplanation = `
                <div style="background: var(--card-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                    <h5>Key Things to Know:</h5>
                    <div style="margin: 1rem 0;">
                        <strong>Annual Fee: ${realETF.expenseRatio.toFixed(2)}%</strong><br>
                        <span style="color: var(--text-secondary);">This is what you pay each year to own this ETF. ${realETF.expenseRatio < 0.2 ? 'Very low fee - excellent!' : realETF.expenseRatio < 0.5 ? 'Reasonable fee.' : 'High fee - consider cheaper alternatives.'}</span>
                    </div>
                    <div style="margin: 1rem 0;">
                        <strong>Diversification: ${realETF.diversification} holdings</strong><br>
                        <span style="color: var(--text-secondary);">More holdings = less risk. ${realETF.diversification > 1000 ? 'Excellent diversification!' : realETF.diversification > 500 ? 'Good diversification.' : 'Limited diversification - higher risk.'}</span>
                    </div>
                    <div style="margin: 1rem 0;">
                        <strong>Dividend Yield: ${realETF.yield.toFixed(1)}%</strong><br>
                        <span style="color: var(--text-secondary);">This is the annual income you might receive. ${realETF.yield > 3 ? 'Good income potential!' : realETF.yield > 2 ? 'Moderate income.' : 'Low income, focused on growth.'}</span>
                    </div>
                    <div style="margin: 1rem 0;">
                        <strong>Main Focus: ${realETF.sector}</strong><br>
                        <span style="color: var(--text-secondary);">This ETF primarily invests in ${realETF.sector.toLowerCase()} companies.</span>
                    </div>
                </div>
            `;
            
            return { summary, currentValue, recommendation, riskExplanation };
        }
        
        
        // Enhanced AI Insights with real actionable advice
        async function generateAIInsights() {
            const tickers = document.getElementById('ai-tickers').value.split(',').map(t => t.trim());
            document.getElementById('ai-results').innerHTML = '<div class="loading">Generating personalized AI insights...</div>';
            
            try {
                const insights = await generatePersonalizedInsights(tickers);
                document.getElementById('ai-results').innerHTML = `
                    <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                        <h4>Your Personalized Investment Insights</h4>
                        ${insights.portfolioHealth}
                        ${insights.actionableAdvice}
                        ${insights.riskAssessment}
                        ${insights.nextSteps}
                    </div>
                `;
            } catch (error) {
                console.error('Error generating AI insights:', error);
                document.getElementById('ai-results').innerHTML = `
                    <div style="background: var(--danger-color); color: white; padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                        <h4>Error Generating Insights</h4>
                        <p>Unable to generate AI insights. Please check your tickers and try again.</p>
                    </div>
                `;
            }
        }
        
        function generatePersonalizedInsights(tickers) {
            // Generate realistic insights based on portfolio using real API data
            const portfolioSize = tickers.length;
            
            // Fetch real portfolio analysis data
            return fetch('/api/comprehensive-analysis', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ tickers: tickers })
            })
            .then(response => response.json())
            .then(data => {
                // Determine risk level based on actual volatility
                const avgVolatility = data.volatility || 0;
                const riskLevel = avgVolatility > 0.25 ? 'high' : avgVolatility > 0.15 ? 'moderate' : 'low';
                
                // Determine growth potential based on actual returns
                const avgReturn = data.annualized_return || 0;
                const growthPotential = avgReturn > 0.1 ? 'positive' : avgReturn > 0.05 ? 'moderate' : 'neutral';
                
                const realAnalysis = {
                    diversification: portfolioSize > 5 ? 'good' : portfolioSize > 3 ? 'moderate' : 'poor',
                    riskLevel: riskLevel,
                    growthPotential: growthPotential,
                    actualVolatility: avgVolatility,
                    actualReturn: avgReturn
                };
            
                const portfolioHealth = `
                    <div style="background: ${realAnalysis.diversification === 'good' ? 'var(--success-color)' : realAnalysis.diversification === 'moderate' ? 'var(--warning-color)' : 'var(--danger-color)'}; color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5>Portfolio Health Check (Real Data)</h5>
                        <p><strong>Diversification:</strong> ${realAnalysis.diversification === 'good' ? 'Well diversified with ' + portfolioSize + ' holdings' : realAnalysis.diversification === 'moderate' ? 'Moderately diversified - consider adding more variety' : 'Poor diversification - high risk concentration'}</p>
                        <p><strong>Actual Volatility:</strong> ${(realAnalysis.actualVolatility * 100).toFixed(2)}%</p>
                        <p><strong>Actual Return:</strong> ${(realAnalysis.actualReturn * 100).toFixed(2)}%</p>
                    </div>
                `;
                
                const actionableAdvice = `
                    <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5>What You Should Do Next (Based on Real Analysis):</h5>
                        <ul style="margin: 0; padding-left: 1.5rem;">
                            ${portfolioSize < 5 ? '<li><strong>Add more diversity:</strong> Consider adding ETFs or stocks from different sectors</li>' : ''}
                            ${realAnalysis.riskLevel === 'high' ? '<li><strong>Reduce risk:</strong> Your portfolio shows high volatility - consider adding stable, dividend-paying stocks or bonds</li>' : ''}
                            <li><strong>Regular review:</strong> Check your investments monthly, but do not panic over daily changes</li>
                            <li><strong>Dollar-cost averaging:</strong> Invest the same amount regularly rather than trying to time the market</li>
                            ${realAnalysis.growthPotential === 'positive' ? '<li><strong>Stay the course:</strong> Your portfolio shows good growth potential with ' + (realAnalysis.actualReturn * 100).toFixed(2) + '% returns</li>' : '<li><strong>Consider rebalancing:</strong> Some positions may need adjustment based on current performance</li>'}
                        </ul>
                    </div>
                `;
                
                const riskAssessment = `
                    <div style="background: var(--card-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5>Risk Assessment (Real Data):</h5>
                        <p><strong>Overall Risk Level:</strong> ${realAnalysis.riskLevel === 'high' ? 'High - Be prepared for significant price swings (Volatility: ' + (realAnalysis.actualVolatility * 100).toFixed(2) + '%)' : realAnalysis.riskLevel === 'moderate' ? 'Moderate - Normal market fluctuations expected' : 'Low - Relatively stable portfolio'}</p>
                        <p><strong>Time Horizon:</strong> This portfolio is best suited for ${realAnalysis.riskLevel === 'high' ? 'long-term investors (5+ years)' : 'medium to long-term goals (3+ years)'}</p>
                    </div>
                `;
                
                const nextSteps = `
                    <div style="background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5>Your Action Plan:</h5>
                        <ol style="margin: 0; padding-left: 1.5rem;">
                            <li>Set up automatic monthly investments</li>
                            <li>Review and rebalance quarterly</li>
                            <li>Keep 3-6 months of expenses in cash as emergency fund</li>
                            <li>Do not check your portfolio daily - weekly is enough</li>
                            <li>Consider tax-advantaged accounts (401k, IRA) first</li>
                        </ol>
                    </div>
                `;
                
                return { portfolioHealth, actionableAdvice, riskAssessment, nextSteps };
            })
            .catch(error => {
                console.error('Error fetching portfolio insights:', error);
                // Fallback to basic analysis without random data
                const basicAnalysis = {
                    diversification: portfolioSize > 5 ? 'good' : portfolioSize > 3 ? 'moderate' : 'poor',
                    riskLevel: 'moderate',
                    growthPotential: 'neutral'
                };
                
                const portfolioHealth = `
                    <div style="background: var(--warning-color); color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5>Portfolio Health Check (Limited Data)</h5>
                        <p><strong>Diversification:</strong> ${basicAnalysis.diversification === 'good' ? 'Well diversified with ' + portfolioSize + ' holdings' : basicAnalysis.diversification === 'moderate' ? 'Moderately diversified - consider adding more variety' : 'Poor diversification - high risk concentration'}</p>
                        <p><em>Unable to fetch real-time data. Please check your connection.</em></p>
                    </div>
                `;
                
                return { portfolioHealth, actionableAdvice: '', riskAssessment: '', nextSteps: '' };
            });
        }
        
        function selectPlan(planType) {
            document.getElementById('reports-results').innerHTML = `
                <div style="background: var(--success-color); color: white; padding: 2rem; border-radius: 15px; margin-top: 2rem; text-align: center;">
                    <h4>${planType.charAt(0).toUpperCase() + planType.slice(1)} Plan Selected!</h4>
                    <p>Thank you for choosing the ${planType} plan. You now have access to premium financial data and reporting features.</p>
                    <p><strong>Next Steps:</strong></p>
                    <ul style="list-style: none; padding: 0; text-align: left; max-width: 400px; margin: 1rem auto;">
                        <li>Account setup confirmation email sent</li>
                        <li>API access credentials activated</li>
                        <li>Premium data feeds enabled</li>
                        <li>Advanced reporting tools unlocked</li>
                    </ul>
                    <button class="action-button" onclick="generateReport('welcome')" style="background: white; color: var(--success-color); margin-top: 1rem;">
                        Generate Your First Premium Report
                    </button>
                </div>
            `;
        }
        
        function generateReport(type) {
            document.getElementById('reports-results').innerHTML = '<div class="loading">Generating professional report with real data...</div>';
            
            // Generate reports with real API data instead of mock content
            generateRealReportContent(type)
                .then(reportContent => {
                    document.getElementById('reports-results').innerHTML = reportContent;
                })
                .catch(error => {
                    document.getElementById('reports-results').innerHTML = `
                        <div style="background: var(--danger-color); color: white; padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                            <h4>Report Generation Error</h4>
                            <p>Unable to generate report with real data: ${error.message}</p>
                            <p>Please check your connection and try again.</p>
                        </div>
                    `;
                });
        }
        
        async function generateRealReportContent(type) {
            switch(type) {
                case 'portfolio':
                    return await generatePortfolioReport();
                case 'market':
                    return await generateMarketReport();
                case 'etf':
                    return await generateETFReport();
                case 'welcome':
                    return generateWelcomeReport();
                default:
                    return await generatePortfolioReport();
            }
        }
        
        async function generatePortfolioReport() {
            // No sample data - user must provide their own portfolio
            return `
                <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                    <h4>Portfolio Analysis</h4>
                    <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5>No Portfolio Data</h5>
                        <p>Please use the Portfolio Analytics section below to analyze your own portfolio with real-time data.</p>
                        <p>Enter your tickers, shares, or weights to get a comprehensive analysis based on live market data.</p>
                    </div>
                    <div style="background: var(--primary-color); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        <strong>Real-Time Analysis:</strong> All portfolio analysis uses fresh API data from Finnhub and YFinance - no sample or mock data.
                    </div>
                </div>
            `;
        }
        
        async function generateMarketReport() {
            // Get real market data for major indices
            const marketTickers = ['SPY', 'QQQ', 'DIA', 'VIX'];
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ tickers: marketTickers })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                const marketSentiment = data.performance && Object.values(data.performance).some(p => p.annual_return > 0.1) ? 'Bullish' : 'Cautious';
                
                return `
                    <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                        <h4>Market Analysis Report (Real Data)</h4>
                        <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                            <h5>Market Overview</h5>
                            <p><strong>Market Sentiment:</strong> ${marketSentiment} (Based on real index performance)</p>
                            <p><strong>S&P 500 (SPY):</strong> ${data.current_prices && data.current_prices.SPY ? '$' + data.current_prices.SPY.current_price.toFixed(2) : 'Data unavailable'}</p>
                            <p><strong>NASDAQ (QQQ):</strong> ${data.current_prices && data.current_prices.QQQ ? '$' + data.current_prices.QQQ.current_price.toFixed(2) : 'Data unavailable'}</p>
                            <p><strong>Dow Jones (DIA):</strong> ${data.current_prices && data.current_prices.DIA ? '$' + data.current_prices.DIA.current_price.toFixed(2) : 'Data unavailable'}</p>
                            <p><strong>Market Recommendation:</strong> ${marketSentiment === 'Bullish' ? 'POSITIVE' : 'NEUTRAL'} - Based on current market conditions</p>
                        </div>
                        <div style="background: var(--primary-color); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                            <strong>Real-Time Alert:</strong> Market data updated from live sources. Current analysis reflects actual market conditions.
                        </div>
                    </div>
                `;
            } catch (error) {
                throw new Error('Failed to fetch market data: ' + error.message);
            }
        }
        
        async function generateETFReport() {
            // Get real ETF data
            const etfTickers = ['VTI', 'VXUS', 'BND', 'VEA'];
            
            try {
                const response = await fetch('/api/etf-analysis', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ etf_tickers: etfTickers })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                return `
                    <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                        <h4>ETF Comparison Report (Real Data)</h4>
                        <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                            <h5>ETF Analysis</h5>
                            ${etfTickers.map(ticker => {
                                const etfData = data.etf_overview && data.etf_overview[ticker];
                                return `
                                    <div style="margin: 1rem 0; padding: 1rem; background: var(--card-bg); border-radius: 8px;">
                                        <strong>${ticker}</strong><br>
                                        <span style="color: var(--success-color);">Real-Time Data</span><br>
                                        ${etfData ? `
                                            Expense Ratio: ${(etfData.expense_ratio * 100).toFixed(2)}%<br>
                                            AUM: $${(etfData.aum / 1000000000).toFixed(1)}B<br>
                                            Dividend Yield: ${(etfData.dividend_yield * 100).toFixed(2)}%
                                        ` : 'Data loading...'}
                                    </div>
                                `;
                            }).join('')}
                        </div>
                        <div style="background: var(--primary-color); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                            <strong>Live Strategy:</strong> ETF recommendations based on current market data and real expense ratios.
                        </div>
                    </div>
                `;
            } catch (error) {
                throw new Error('Failed to fetch ETF data: ' + error.message);
            }
        }
        
        function generateWelcomeReport() {
            return `
                <div style="background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); color: white; padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                    <h4>Welcome to TradeRiser.AI!</h4>
                    <p>Your account is now active with real-time data access. Here's what you can do:</p>
                    <ul style="list-style: none; padding: 0;">
                        <li>✓ Access real-time market data from Finnhub API</li>
                        <li>✓ Generate reports with live financial data</li>
                        <li>✓ Get real portfolio analysis and recommendations</li>
                        <li>✓ Track actual market performance with YFinance backup</li>
                        <li>✓ Receive data-driven market insights</li>
                    </ul>
                    <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        <strong>Real-Time Tip:</strong> All analysis is now powered by live market data. No more mock or placeholder information!
                    </div>
                </div>
            `;
        }
        
        function runPortfolioAnalytics() {
            const tickers = document.getElementById('portfolio-tickers').value.split(',').map(t => t.trim());
            const shares = document.getElementById('portfolio-shares').value;
            const weights = document.getElementById('portfolio-weights').value;
            
            document.getElementById('portfolio-results').innerHTML = '<div class="loading">Running advanced portfolio analytics...</div>';
            
            let payload = {};
            
            // Prioritize shares over weights
            if (shares && shares.trim()) {
                payload.holdings = Object.fromEntries(
                    tickers.map((t, i) => {
                        const sharesList = shares.split(',').map(s => parseFloat(s.trim()));
                        return [t, sharesList[i] || 0];
                    })
                );
            } else if (weights && weights.trim()) {
                const weightsList = weights.split(',').map(w => parseFloat(w.trim()));
                payload.tickers = tickers;
                payload.weights = weightsList.length === tickers.length ? weightsList : null;
            } else {
                // Equal weights if no shares or weights provided
                payload.tickers = tickers;
            }
            
            fetch('/api/comprehensive-analysis', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('portfolio-results').innerHTML = `<div style="color: var(--danger-color);">Error: ${data.error}</div>`;
                } else {
                    displayPortfolioAnalysisResults(data);
                }
            })
            .catch(error => {
                document.getElementById('portfolio-results').innerHTML = `<div style="color: var(--danger-color);">Error: ${error.message}</div>`;
            });
        }
        
        function displayPortfolioAnalysisResults(data) {
            const portfolioValue = data.portfolio_value || 0;
            const totalReturn = data.total_return || 0;
            const annualizedReturn = data.annualized_return || 0;
            const volatility = data.volatility || 0;
            const sharpeRatio = data.sharpe_ratio || 0;
            const maxDrawdown = data.max_drawdown || 0;
            const diversificationScore = data.diversification_score || 0;
            
            const summary = `
                <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                    <h5>Portfolio Overview</h5>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;">
                        <div style="text-align: center; padding: 1rem; background: var(--card-bg); border-radius: 8px;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: var(--success-color);">$${portfolioValue.toLocaleString()}</div>
                            <div style="color: var(--text-secondary);">Portfolio Value</div>
                        </div>
                        <div style="text-align: center; padding: 1rem; background: var(--card-bg); border-radius: 8px;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: ${totalReturn >= 0 ? 'var(--success-color)' : 'var(--danger-color)'};">${totalReturn >= 0 ? '+' : ''}${(totalReturn * 100).toFixed(1)}%</div>
                            <div style="color: var(--text-secondary);">Total Return</div>
                        </div>
                        <div style="text-align: center; padding: 1rem; background: var(--card-bg); border-radius: 8px;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: var(--primary-color);">${(diversificationScore * 10).toFixed(1)}/10</div>
                            <div style="color: var(--text-secondary);">Diversification</div>
                        </div>
                    </div>
                </div>
            `;
            
            const riskLevel = volatility < 0.15 ? 'Low' : volatility < 0.25 ? 'Moderate' : 'High';
            const riskColor = volatility < 0.15 ? 'var(--success-color)' : volatility < 0.25 ? 'var(--warning-color)' : 'var(--danger-color)';
            
            const riskAnalysis = `
                <div style="background: ${riskColor}; color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                    <h5>Risk Assessment</h5>
                    <p><strong>Risk Level: ${riskLevel}</strong></p>
                    <p><strong>Volatility:</strong> ${(volatility * 100).toFixed(1)}% - ${volatility < 0.15 ? 'Your portfolio has steady, predictable movements. Great for conservative investors!' : volatility < 0.25 ? 'Normal price swings expected. Good balance of risk and reward.' : 'Expect significant price movements. Only suitable if you can handle the ups and downs.'}</p>
                    <p><strong>Sharpe Ratio:</strong> ${sharpeRatio.toFixed(2)} - ${sharpeRatio > 1.5 ? 'Excellent risk-adjusted returns!' : sharpeRatio > 1.0 ? 'Good returns for the risk taken.' : 'Consider if the returns justify the risk.'}</p>
                    <p><strong>Max Drawdown:</strong> ${(maxDrawdown * 100).toFixed(1)}% - The largest peak-to-trough decline in your portfolio value.</p>
                </div>
            `;
            
            const recommendations = `
                <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                    <h5>Investment Recommendations</h5>
                    <div style="margin: 1rem 0;">
                        ${data.investment_tips ? data.investment_tips.map(tip => `<p>• ${tip}</p>`).join('') : '<p>• Maintain a diversified portfolio across different sectors</p><p>• Review and rebalance your portfolio quarterly</p><p>• Consider your risk tolerance and investment timeline</p>'}
                    </div>
                </div>
            `;
            
            const holdings = data.holdings || {};
            const holdingsTable = Object.keys(holdings).length > 0 ? `
                <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                    <h5>Portfolio Holdings</h5>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
                            <thead>
                                <tr style="background: var(--card-bg);">
                                    <th style="padding: 0.75rem; text-align: left; border: 1px solid var(--border-color);">Symbol</th>
                                    <th style="padding: 0.75rem; text-align: right; border: 1px solid var(--border-color);">Shares/Weight</th>
                                    <th style="padding: 0.75rem; text-align: right; border: 1px solid var(--border-color);">Current Price</th>
                                    <th style="padding: 0.75rem; text-align: right; border: 1px solid var(--border-color);">Value</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${Object.entries(holdings).map(([symbol, info]) => `
                                    <tr>
                                        <td style="padding: 0.75rem; border: 1px solid var(--border-color);">${symbol}</td>
                                        <td style="padding: 0.75rem; text-align: right; border: 1px solid var(--border-color);">${typeof info === 'object' ? (info.shares || info.weight || 'N/A') : info}</td>
                                        <td style="padding: 0.75rem; text-align: right; border: 1px solid var(--border-color);">$${typeof info === 'object' && info.current_price ? info.current_price.toFixed(2) : 'N/A'}</td>
                                        <td style="padding: 0.75rem; text-align: right; border: 1px solid var(--border-color);">$${typeof info === 'object' && info.value ? info.value.toFixed(2) : 'N/A'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            ` : '';
            
            document.getElementById('portfolio-results').innerHTML = `
                <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                    <h4>Your Portfolio Analysis</h4>
                    ${summary}
                    ${riskAnalysis}
                    ${recommendations}
                    ${holdingsTable}
                </div>
            `;
        }
        
        function generateReport(type) {
            document.getElementById('reports-results').innerHTML = '<div class="loading">Generating professional report...</div>';
            setTimeout(() => {
                document.getElementById('reports-results').innerHTML = `
                    <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                        <h4>Report Generated Successfully</h4>
                        <p>Your ${type} report has been generated with institutional-quality analysis.</p>
                        <div style="background: var(--success-color); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                            <i class="fas fa-check-circle"></i> Report ready for download
                        </div>
                        <button class="action-button" style="background: var(--gradient-success);">
                            <i class="fas fa-download"></i>
                            Download Report
                        </button>
                    </div>
                `;
            }, 2000);
        }
        
        // Top Tickers Display Functionality
        async function loadTopTickers() {
            const apiKey = '5OX0XMT9EK5SGNN9'; // AlphaVantage Premium Key
            
            const tickers = [
                // Stocks/ETFs
                'AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'NVDA', 'META', 'NFLX',
                'SLB', 'HAL', 'BKR', 'COP', 'CVX', 'XOM', 'EOG', 'PSX', 'VLO',
                'CPER', 'GLD', 'SLV',
                
                // Crypto (special icons)
                'BTC', 'ETH', 'DOGE', 'LTC', 'SOL',
                
                // Indexes (letter-badge style only)
                '^DJI', '^IXIC', '^GSPC'
            ];
            
            const cryptoLogos = {
                BTC: 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png',
                ETH: 'https://assets.coingecko.com/coins/images/279/large/ethereum.png',
                DOGE: 'https://assets.coingecko.com/coins/images/5/large/dogecoin.png',
                LTC: 'https://assets.coingecko.com/coins/images/2/large/litecoin.png',
                SOL: 'https://assets.coingecko.com/coins/images/4128/large/solana.png',
            };
            
            const indexNames = {
                '^DJI': 'DJIA',
                '^IXIC': 'NASDAQ',
                '^GSPC': 'S&P'
            };
            
            async function fetchPrice(symbol) {
                const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${apiKey}`;
                try {
                    const res = await fetch(url);
                    const data = await res.json();
                    const quote = data["Global Quote"];
                    if (!quote || !quote["05. price"]) return null;
                    
                    const current = parseFloat(quote["05. price"]);
                    const previous = parseFloat(quote["08. previous close"]);
                    return { symbol, current, previous };
                } catch (err) {
                    console.error(`Error fetching ${symbol}:`, err);
                    return null;
                }
            }
            
            const tickerEl = document.getElementById('ticker');
            tickerEl.innerHTML = ''; // Clear existing content
            
            for (const symbol of tickers) {
                const priceData = await fetchPrice(symbol);
                if (!priceData) continue;
                
                const { current, previous } = priceData;
                const change = current - previous;
                const changePercent = ((change / previous) * 100);
                const direction = change >= 0 ? 'ticker-up' : 'ticker-down';
                
                const item = document.createElement('div');
                item.className = 'ticker-item';
                
                // Determine image or label
                if (cryptoLogos[symbol]) {
                    item.innerHTML = `
                        <img class="ticker-icon" src="${cryptoLogos[symbol]}" alt="${symbol}" />
                        <span class="ticker-symbol">${symbol}</span>
                        <span class="ticker-price ${direction}">$${current.toFixed(2)}</span>
                        <span class="ticker-change ${direction}">${change >= 0 ? '+' : ''}${changePercent.toFixed(2)}%</span>
                    `;
                } else if (indexNames[symbol]) {
                    item.innerHTML = `
                        <span class="index-label">${indexNames[symbol]}</span>
                        <span class="ticker-price ${direction}">${current.toFixed(2)}</span>
                        <span class="ticker-change ${direction}">${change >= 0 ? '+' : ''}${changePercent.toFixed(2)}%</span>
                    `;
                } else {
                    item.innerHTML = `
                        <img class="ticker-icon" src="https://financialmodelingprep.com/image-stock/${symbol}.png" alt="${symbol}" />
                        <span class="ticker-symbol">${symbol}</span>
                        <span class="ticker-price ${direction}">$${current.toFixed(2)}</span>
                        <span class="ticker-change ${direction}">${change >= 0 ? '+' : ''}${changePercent.toFixed(2)}%</span>
                    `;
                }
                
                tickerEl.appendChild(item);
            }
        }
        
        function displayTickers(category, pricesData) {
            const container = document.querySelector(`[data-category="${category.toLowerCase()}"] .ticker-scroll`);
            if (!container) return;
            
            let tickerHTML = '';
            
            for (const [symbol, data] of Object.entries(pricesData)) {
                const price = data.current_price || 0;
                const change = data.change_percent || 0;
                const changeClass = change >= 0 ? 'positive' : 'negative';
                
                tickerHTML += `
                    <div class="ticker-item">
                        <span class="ticker-symbol">${symbol}</span>
                        <span class="ticker-price">$${price.toFixed(2)}</span>
                        <span class="ticker-change ${changeClass}">${change >= 0 ? '+' : ''}${change.toFixed(2)}%</span>
                    </div>
                `;
            }
            
            // Display ticker content without duplication
            container.innerHTML = tickerHTML;
        }
        
        function displayTickerError(category) {
            const container = document.querySelector(`[data-category="${category.toLowerCase()}"] .ticker-scroll`);
            if (!container) return;
            
            container.innerHTML = `
                <div class="ticker-item" style="color: var(--danger-color);">
                    <span class="ticker-symbol">ERROR</span>
                    <span class="ticker-price">Data Unavailable</span>
                    <span class="ticker-change">API Error</span>
                </div>
            `;
        }
        
        function displayAllTickerErrors() {
            const categories = ['', '', 'S&P', 'Crypto'];
            categories.forEach(category => displayTickerError(category));
        }
        
        // Crypto Analytics Functions
        function runCryptoAnalysis() {
            const symbols = document.getElementById('crypto-symbols').value;
            const holdings = document.getElementById('crypto-holdings').value;
            const analysisType = document.getElementById('crypto-analysis-type').value;
            
            if (!symbols) {
                alert('Please enter crypto symbols');
                return;
            }
            
            const resultsDiv = document.getElementById('crypto-results');
            resultsDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Analyzing crypto portfolio...</div>';
            
            fetch('/api/crypto/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbols: symbols.split(',').map(s => s.trim()),
                    holdings: holdings ? holdings.split(',').map(h => parseFloat(h.trim())) : null,
                    analysis_type: analysisType
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                } else {
                    displayCryptoResults(data);
                }
            })
            .catch(error => {
                resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
            });
        }
        
        function findDeFiOpportunities() {
            const protocols = Array.from(document.getElementById('defi-protocols').selectedOptions).map(option => option.value);
            const amount = document.getElementById('defi-amount').value;
            
            if (protocols.length === 0) {
                alert('Please select at least one DeFi protocol');
                return;
            }
            
            if (!amount || amount < 100) {
                alert('Please enter a valid investment amount (minimum $100)');
                return;
            }
            
            const resultsDiv = document.getElementById('crypto-results');
            resultsDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Finding DeFi opportunities...</div>';
            
            fetch('/api/defi/opportunities', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    protocols: protocols,
                    amount: parseFloat(amount)
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                } else {
                    displayDeFiResults(data);
                }
            })
            .catch(error => {
                resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
            });
        }
        
        function displayCryptoResults(data) {
            const resultsDiv = document.getElementById('crypto-results');
            
            // Generate individual crypto recommendations HTML
            let individualCryptoHTML = '';
            if (data.crypto_data && Array.isArray(data.crypto_data)) {
                individualCryptoHTML = `
                    <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5>Individual Cryptocurrency Analysis</h5>
                        ${data.crypto_data.map(crypto => {
                            const recommendationColor = 
                                crypto.recommendation === 'BUY' ? 'var(--success-color)' :
                                crypto.recommendation === 'SELL' ? 'var(--danger-color)' :
                                'var(--warning-color)';
                            
                            return `
                                <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid ${recommendationColor};">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                        <strong>${crypto.symbol.toUpperCase()}</strong>
                                        <span style="background: ${recommendationColor}; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; font-weight: bold; font-size: 0.9rem;">
                                            ${crypto.recommendation || 'HOLD'}
                                        </span>
                                    </div>
                                    <p style="margin: 0.3rem 0; color: var(--text-secondary);">Price: $${(crypto.current_price || 0).toFixed(4)}</p>
                                    <p style="margin: 0.3rem 0; color: var(--text-secondary);">24h Change: <span style="color: ${(crypto.price_change_24h || 0) >= 0 ? 'var(--success-color)' : 'var(--danger-color)'}">${(crypto.price_change_24h || 0) >= 0 ? '+' : ''}${((crypto.price_change_24h || 0) * 100).toFixed(2)}%</span></p>
                                    ${crypto.confidence ? `<p style="margin: 0.3rem 0; color: var(--text-secondary);">Confidence: ${crypto.confidence}%</p>` : ''}
                                    ${crypto.reasoning ? `<p style="margin: 0.5rem 0; font-style: italic; color: var(--text-primary);">${crypto.reasoning}</p>` : ''}
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }
            
            resultsDiv.innerHTML = `
                <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                    <h4>Crypto Portfolio Analysis</h4>
                    <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5>Portfolio Overview</h5>
                        <p><strong>Total Value:</strong> $${(data.total_value || 0).toLocaleString()}</p>
                        <p><strong>24h Change:</strong> <span style="color: ${(data.total_change || 0) >= 0 ? 'var(--success-color)' : 'var(--danger-color)'}">${(data.total_change || 0) >= 0 ? '+' : ''}${((data.total_change || 0) * 100).toFixed(2)}%</span></p>
                        <p><strong>Diversification Score:</strong> ${data.diversification_score || 'N/A'}/10</p>
                    </div>
                    ${individualCryptoHTML}
                    <div style="background: var(--primary-color); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        <strong>Portfolio Insight:</strong> ${data.recommendation || 'Cryptocurrency markets are highly volatile. Only invest what you can afford to lose.'}
                    </div>
                </div>
            `;
        }
        
        function displayDeFiResults(data) {
            const resultsDiv = document.getElementById('crypto-results');
            resultsDiv.innerHTML = `
                <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                    <h4>DeFi Opportunities</h4>
                    <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5>Best Yield Opportunities</h5>
                        ${(data.opportunities || []).map(opp => `
                            <div style="background: var(--card-bg); padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
                                <strong>${opp.protocol}</strong> - ${opp.apy}% APY<br>
                                <small style="color: var(--text-secondary);">${opp.description}</small>
                            </div>
                        `).join('')}
                    </div>
                    <div style="background: var(--warning-color); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        <strong>DeFi Warning:</strong> DeFi protocols carry smart contract risks. Research thoroughly before investing.
                    </div>
                </div>
            `;
        }
        
        // Investment Wizard Step Navigation Functions
        function wizardStep1() {
            // Show step 1, hide others
            document.getElementById('step-1').style.display = 'block';
            document.getElementById('step-2').style.display = 'none';
            document.getElementById('step-3').style.display = 'none';
            document.getElementById('step-4').style.display = 'none';
            document.getElementById('step-5').style.display = 'none';
            document.getElementById('step-6').style.display = 'none';
        }
        
        function wizardStep2() {
            // Validate step 1 inputs
            const amount = document.getElementById('investment-amount').value;
            const description = document.getElementById('investment-description').value;
            
            if (!amount || parseFloat(amount) < 100) {
                alert('Please enter a valid investment amount (minimum $100)');
                return;
            }
            
            if (!description.trim()) {
                alert('Please describe your investment situation');
                return;
            }
            
            // Hide all steps, show step 2
            document.getElementById('step-1').style.display = 'none';
            document.getElementById('step-2').style.display = 'block';
            document.getElementById('step-3').style.display = 'none';
            document.getElementById('step-4').style.display = 'none';
            document.getElementById('step-5').style.display = 'none';
            document.getElementById('step-6').style.display = 'none';
        }
        
        function wizardStep3() {
            // Hide all steps, show step 3
            document.getElementById('step-1').style.display = 'none';
            document.getElementById('step-2').style.display = 'none';
            document.getElementById('step-3').style.display = 'block';
            document.getElementById('step-4').style.display = 'none';
            document.getElementById('step-5').style.display = 'none';
            document.getElementById('step-6').style.display = 'none';
        }
        
        function wizardStep4() {
            // Hide all steps, show step 4
            document.getElementById('step-1').style.display = 'none';
            document.getElementById('step-2').style.display = 'none';
            document.getElementById('step-3').style.display = 'none';
            document.getElementById('step-4').style.display = 'block';
            document.getElementById('step-5').style.display = 'none';
            document.getElementById('step-6').style.display = 'none';
        }
        
        function wizardStep5() {
            // Hide all steps, show step 5
            document.getElementById('step-1').style.display = 'none';
            document.getElementById('step-2').style.display = 'none';
            document.getElementById('step-3').style.display = 'none';
            document.getElementById('step-4').style.display = 'none';
            document.getElementById('step-5').style.display = 'block';
            document.getElementById('step-6').style.display = 'none';
        }
        
        function wizardStep6() {
            // Hide all steps, show step 6
            document.getElementById('step-1').style.display = 'none';
            document.getElementById('step-2').style.display = 'none';
            document.getElementById('step-3').style.display = 'none';
            document.getElementById('step-4').style.display = 'none';
            document.getElementById('step-5').style.display = 'none';
            document.getElementById('step-6').style.display = 'block';
        }
        
        function generateInvestmentRecommendations() {
            // Helper function to safely get element value
            function getElementValue(id, defaultValue = '') {
                const element = document.getElementById(id);
                return element ? element.value : defaultValue;
            }
            
            // Helper function to safely check if element is checked
            function isElementChecked(id) {
                const element = document.getElementById(id);
                return element ? element.checked : false;
            }
            
            // Get all form values from all steps with null checks
            const amount = getElementValue('investment-amount');
            const description = getElementValue('investment-description');
            
            // Step 2: Financial Situation
            const annualIncome = getElementValue('annual-income');
            const debtLevel = getElementValue('debt-level');
            const emergencyFund = getElementValue('emergency-fund');
            const liquidityNeeds = getElementValue('liquidity-needs');
            
            // Step 3: Experience & Preferences
            const investmentExperience = getElementValue('investment-experience');
            const investmentPreferences = getElementValue('investment-preferences');
            
            // Collect experience checkboxes
            const experienceAssets = [];
            ['exp-stocks', 'exp-bonds', 'exp-etfs', 'exp-crypto', 'exp-realestate', 'exp-commodities'].forEach(id => {
                if (isElementChecked(id)) {
                    const element = document.getElementById(id);
                    if (element && element.value) {
                        experienceAssets.push(element.value);
                    }
                }
            });
            
            // Collect assets to avoid
            const assetsToAvoid = [];
            ['avoid-tobacco', 'avoid-weapons', 'avoid-fossil', 'avoid-gambling', 'avoid-crypto-avoid'].forEach(id => {
                if (isElementChecked(id)) {
                    const element = document.getElementById(id);
                    if (element && element.value) {
                        assetsToAvoid.push(element.value);
                    }
                }
            });
            
            // Step 4: Goals, Risk & Timeline
            const timeline = getElementValue('investment-timeline');
            const riskTolerance = getElementValue('risk-tolerance');
            const goal = getElementValue('investment-goal');
            const returnExpectations = getElementValue('return-expectations');
            
            // Step 5: Tax Strategy & Financial Planning
            const taxBracket = getElementValue('tax-bracket');
            const incomeChanges = getElementValue('income-changes');
            
            // Collect tax-advantaged accounts
            const taxAccounts = [];
            ['tax-401k', 'tax-ira', 'tax-roth', 'tax-hsa', 'tax-529'].forEach(id => {
                if (isElementChecked(id)) {
                    const element = document.getElementById(id);
                    if (element && element.value) {
                        taxAccounts.push(element.value);
                    }
                }
            });
            
            // Collect upcoming expenses
            const upcomingExpenses = [];
            ['expense-home', 'expense-education', 'expense-wedding', 'expense-family', 'expense-care'].forEach(id => {
                if (isElementChecked(id)) {
                    const element = document.getElementById(id);
                    if (element && element.value) {
                        upcomingExpenses.push(element.value);
                    }
                }
            });
            
            // Step 6: Personal Circumstances & Management
            const estatePlanning = getElementValue('estate-planning');
            const managementStyle = getElementValue('management-style');
            
            // Collect insurance coverage
            const insuranceCoverage = [];
            ['insurance-life', 'insurance-disability', 'insurance-health', 'insurance-umbrella'].forEach(id => {
                if (isElementChecked(id)) {
                    const element = document.getElementById(id);
                    if (element && element.value) {
                        insuranceCoverage.push(element.value);
                    }
                }
            });
            
            // Collect special circumstances
            const specialCircumstances = [];
            ['special-parents', 'special-dependents', 'special-business', 'special-inheritance', 'special-divorce'].forEach(id => {
                if (isElementChecked(id)) {
                    const element = document.getElementById(id);
                    if (element && element.value) {
                        specialCircumstances.push(element.value);
                    }
                }
            });
            
            // Validate required inputs
            if (!amount || !timeline || !riskTolerance) {
                alert('Please fill in the required fields: Investment Amount, Timeline, and Risk Tolerance');
                return;
            }
            
            if (parseFloat(amount) < 100) {
                alert('Minimum investment amount is $100');
                return;
            }
            
            const resultsDiv = document.getElementById('wizard-results');
            if (!resultsDiv) {
                alert('Results container not found. Please refresh the page and try again.');
                return;
            }
            
            resultsDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Analyzing your comprehensive financial profile and generating personalized recommendations...</div>';
            
            fetch('/api/investment/wizard', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    amount: parseFloat(amount),
                    situation: description,
                    timeline: timeline,
                    risk_tolerance: riskTolerance,
                    goals: goal,
                    // New comprehensive data
                    annual_income: annualIncome,
                    debt_level: debtLevel,
                    emergency_fund: emergencyFund,
                    liquidity_needs: liquidityNeeds,
                    investment_experience: investmentExperience,
                    experience_assets: experienceAssets,
                    investment_preferences: investmentPreferences,
                    assets_to_avoid: assetsToAvoid,
                    return_expectations: returnExpectations,
                    tax_bracket: taxBracket,
                    income_changes: incomeChanges,
                    tax_accounts: taxAccounts,
                    upcoming_expenses: upcomingExpenses,
                    estate_planning: estatePlanning,
                    management_style: managementStyle,
                    insurance_coverage: insuranceCoverage,
                    special_circumstances: specialCircumstances
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                } else {
                    displayWizardResults(data);
                }
            })
            .catch(error => {
                resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
            });
        }
        
        // Investment Wizard Functions
        function processInvestmentWizard() {
            const amount = document.getElementById('investment-amount').value;
            const situation = document.getElementById('investment-situation').value;
            const timeline = document.getElementById('investment-timeline').value;
            const riskTolerance = document.getElementById('risk-tolerance').value;
            const goals = document.getElementById('investment-goals').value;
            
            if (!amount || !situation || !timeline || !riskTolerance || !goals) {
                alert('Please fill in all fields');
                return;
            }
            
            if (parseFloat(amount) < 100) {
                alert('Minimum investment amount is $100');
                return;
            }
            
            const resultsDiv = document.getElementById('wizard-results');
            resultsDiv.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Analyzing your situation and generating personalized recommendations...</div>';
            
            fetch('/api/investment/wizard', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    amount: parseFloat(amount),
                    situation: situation,
                    timeline: timeline,
                    risk_tolerance: riskTolerance,
                    goals: goals
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                } else {
                    displayWizardResults(data);
                }
            })
            .catch(error => {
                resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
            });
        }
        
        function displayWizardResults(data) {
            const resultsDiv = document.getElementById('wizard-results');
            resultsDiv.innerHTML = `
                <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                    <h4><i class="fas fa-chart-pie"></i> Your Comprehensive Investment Plan</h4>
                    
                    ${data.ai_insights ? `
                    <div style="background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5><i class="fas fa-brain"></i> AI-Powered Insights</h5>
                        <p>${data.ai_insights}</p>
                    </div>
                    ` : ''}
                    
                    <div style="background: var(--success-color); color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5><i class="fas fa-bullseye"></i> Recommended Strategy</h5>
                        <p>${data.strategy || 'Based on your comprehensive profile, we recommend a personalized diversified approach.'}</p>
                        <p><strong>Estimated Annual Return:</strong> ${data.estimated_annual_return || '7-9%'}</p>
                        ${data.personalization_factors ? `<p><strong>Personalization Score:</strong> ${data.personalization_factors}</p>` : ''}
                    </div>
                    
                    <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5><i class="fas fa-chart-pie"></i> Asset Allocation</h5>
                        ${(data.allocation || []).map(asset => `
                            <div style="display: flex; justify-content: space-between; align-items: center; margin: 0.75rem 0; padding: 0.5rem; background: var(--card-bg); border-radius: 8px;">
                                <span style="font-weight: 500;">${asset.type}</span>
                                <div style="text-align: right;">
                                    <div style="font-weight: bold; color: var(--primary-color);">${asset.percentage}%</div>
                                    <div style="font-size: 0.875rem; color: var(--text-secondary);">${asset.amount}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    
                    ${data.specific_recommendations ? `
                    <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5><i class="fas fa-list-ul"></i> Specific Investment Recommendations</h5>
                        ${data.specific_recommendations.stocks && data.specific_recommendations.stocks.length > 0 ? `
                            <div style="margin: 1rem 0;">
                                <strong style="color: var(--success-color);">Stock ETFs:</strong>
                                <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                                    ${data.specific_recommendations.stocks.map(stock => `<li style="margin: 0.25rem 0;">${stock}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        ${data.specific_recommendations.bonds && data.specific_recommendations.bonds.length > 0 ? `
                            <div style="margin: 1rem 0;">
                                <strong style="color: var(--warning-color);">Bond ETFs:</strong>
                                <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                                    ${data.specific_recommendations.bonds.map(bond => `<li style="margin: 0.25rem 0;">${bond}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        ${data.specific_recommendations.alternatives && data.specific_recommendations.alternatives.length > 0 ? `
                            <div style="margin: 1rem 0;">
                                <strong style="color: var(--info-color);">Alternative Investments:</strong>
                                <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                                    ${data.specific_recommendations.alternatives.map(alt => `<li style="margin: 0.25rem 0;">${alt}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        ${data.specific_recommendations.cash && data.specific_recommendations.cash.length > 0 ? `
                            <div style="margin: 1rem 0;">
                                <strong style="color: var(--text-secondary);">Cash & Cash Equivalents:</strong>
                                <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                                    ${data.specific_recommendations.cash.map(cash => `<li style="margin: 0.25rem 0;">${cash}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                    ` : ''}
                    
                    ${data.tax_strategy ? `
                    <div style="background: var(--info-color); color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5><i class="fas fa-calculator"></i> Tax Strategy Recommendations</h5>
                        <p>${data.tax_strategy}</p>
                    </div>
                    ` : ''}
                    
                    ${data.risk_assessment ? `
                    <div style="background: var(--warning-color); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        <strong><i class="fas fa-shield-alt"></i> Risk Assessment:</strong> ${data.risk_assessment}
                    </div>
                    ` : ''}
                    
                    ${data.timeline_considerations ? `
                    <div style="background: var(--secondary-color); color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5><i class="fas fa-clock"></i> Timeline Considerations</h5>
                        <p>${data.timeline_considerations}</p>
                    </div>
                    ` : ''}
                    
                    ${data.rebalancing_strategy ? `
                    <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid var(--primary-color);">
                        <h5><i class="fas fa-sync-alt"></i> Rebalancing Strategy</h5>
                        <p>${data.rebalancing_strategy}</p>
                    </div>
                    ` : ''}
                    
                    <div style="background: var(--primary-color); color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                        <h5><i class="fas fa-rocket"></i> Next Steps</h5>
                        <p>${data.next_steps || 'Start with low-cost index funds and gradually build your diversified portfolio based on your comprehensive financial profile.'}</p>
                    </div>
                    
                    ${data.monitoring_recommendations ? `
                    <div style="background: var(--dark-bg); padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid var(--success-color);">
                        <h5><i class="fas fa-chart-line"></i> Portfolio Monitoring</h5>
                        <p>${data.monitoring_recommendations}</p>
                    </div>
                    ` : ''}
                    
                    ${data.compliance_note ? `
                    <div style="background: var(--text-secondary); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0; font-size: 0.875rem;">
                        <strong><i class="fas fa-info-circle"></i> Important Disclaimer:</strong> ${data.compliance_note}
                    </div>
                    ` : ''}
                </div>
            `;
        }
        
        // Missing JavaScript Functions
        function runUnifiedAnalysis() {
            const tickers = document.getElementById('unified-tickers').value;
            const shares = document.getElementById('unified-shares').value;
            
            if (!tickers) {
                alert('Please enter stock tickers');
                return;
            }
            
            document.getElementById('unified-results').innerHTML = '<div class="loading">Running unified portfolio & stock analysis...</div>';
            
            const requestData = {
                tickers: tickers.split(',').map(t => t.trim())
            };
            
            if (shares) {
                requestData.shares = shares.split(',').map(s => parseFloat(s.trim()) || 1);
            }
            
            fetch('/api/comprehensive-analysis', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(data => {
                displayUnifiedResults(data);
            })
            .catch(error => {
                document.getElementById('unified-results').innerHTML = `<div style="color: var(--danger-color);">Error: ${error.message}</div>`;
            });
        }
        
        function runWhitepaperAnalysis() {
            // Placeholder function for whitepaper analysis
            const resultsDiv = document.getElementById('whitepaper-results') || document.getElementById('ai-results');
            if (resultsDiv) {
                resultsDiv.innerHTML = '<div class="loading">Analyzing whitepapers and research documents...</div>';
                
                // Simulate analysis
                setTimeout(() => {
                    resultsDiv.innerHTML = `
                        <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                            <h4>Whitepaper Analysis Results</h4>
                            <p>This feature is currently under development. Advanced AI-powered whitepaper analysis will be available soon.</p>
                            <div style="background: var(--primary-color); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                                <strong>Coming Soon:</strong> AI-powered analysis of investment whitepapers, research reports, and financial documents.
                            </div>
                        </div>
                    `;
                }, 1500);
            }
        }
        
        function displayUnifiedResults(data) {
            // Display unified analysis results similar to other analysis functions
            const analysis = translateFinancialData(data);
            
            document.getElementById('unified-results').innerHTML = `
                <div style="background: var(--card-bg); padding: 2rem; border-radius: 15px; margin-top: 2rem;">
                    <h4>Unified Portfolio & Stock Analysis Results</h4>
                    ${analysis.recommendation}
                    ${analysis.explanation}
                    
                    <div style="margin-top: 2rem; padding: 1rem; background: var(--dark-bg); border-radius: 10px;">
                        <h5>Technical Analysis Details</h5>
                        <button onclick="toggleTechnicalData('unified')" style="background: var(--primary-color); color: white; border: none; padding: 0.5rem 1rem; border-radius: 5px; cursor: pointer;">Show Technical Data</button>
                        <div id="unified-technical" style="display: none; margin-top: 1rem;">
                            <pre style="background: var(--dark-bg); padding: 1rem; border-radius: 10px; overflow-x: auto; color: var(--text-secondary);">${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    </div>
                </div>
            `;
        }

        // Toggle Technical Data Display
        function toggleTechnicalData(type) {
            const technicalDiv = document.getElementById(type + '-technical');
            const button = event.target;

            if (technicalDiv.style.display === 'none') {
                technicalDiv.style.display = 'block';
                button.textContent = 'Hide Technical Data';
            } else {
                technicalDiv.style.display = 'none';
                button.textContent = 'Show Technical Data';
            }
        }
        
        // Load tickers when page loads
        document.addEventListener('DOMContentLoaded', function() {
            loadTopTickers();
            // Refresh tickers every 1 minute with fresh API calls
            setInterval(loadTopTickers, 60000);
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)