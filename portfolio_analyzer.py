"""
Portfolio Analyzer with real data from free APIs
"""
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from typing import Dict, List
from Utils.utils_api_client import APIClient
import logging

logging.basicConfig(
    filename='traderiser.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class PortfolioAnalyzer:
    def __init__(self):
        """Initialize with API client"""
        self.api_client = APIClient()
        self.logger = logging.getLogger(__name__)
        self.risk_free_rate = 0.045
        self.base_urls = {
            'yahoo_summary': 'https://query1.finance.yahoo.com/v10/finance/quoteSummary',
            'yahoo_chart': 'https://query1.finance.yahoo.com/v8/finance/chart'
        }

    def analyze_portfolio(self, holdings: Dict[str, float], nav: float = 100000) -> Dict:
        """Analyze portfolio using real data"""
        try:
            if not self._validate_portfolio(holdings):
                self.logger.error("Invalid portfolio weights")
                return {'error': 'Invalid portfolio weights'}
            portfolio_data = {}
            for ticker, weight in holdings.items():
                stock_data = self._fetch_stock_data(ticker)
                if stock_data:
                    stock_data['weight'] = weight
                    portfolio_data[ticker] = stock_data
            if not portfolio_data:
                self.logger.error("No valid stock data found")
                return {'error': 'No valid stock data found'}
            analysis = {
                'portfolio_summary': self._calculate_portfolio_summary(portfolio_data, nav),
                'fundamental_analysis': self._analyze_portfolio_fundamentals(portfolio_data),
                'technical_analysis': self._analyze_portfolio_technicals(portfolio_data),
                'risk_analysis': self._analyze_portfolio_risk(portfolio_data),
                'macro_analysis': self._analyze_macro_environment(portfolio_data),
                'sector_analysis': self._analyze_sector_allocation(portfolio_data),
                'generated_at': datetime.now().isoformat()
            }
            self.logger.info("Portfolio analysis completed")
            return analysis
        except Exception as e:
            self.logger.error(f"Portfolio analysis failed: {str(e)}")
            return {'error': f'Portfolio analysis failed: {str(e)}'}

    def _validate_portfolio(self, holdings: Dict[str, float]) -> bool:
        """Validate portfolio weights"""
        if not holdings:
            return False
        total_weight = sum(holdings.values())
        return abs(total_weight - 1.0) <= 0.01

    def _fetch_stock_data(self, ticker: str) -> Dict:
        """Fetch comprehensive stock data"""
        try:
            fundamental_data = self.api_client.get_alpha_vantage_fundamentals(ticker)
            quote_data = self.api_client.get_alpha_vantage_quote(ticker)
            alternative_data = self._fetch_alternative_data(ticker)
            technical_data = self._fetch_technical_data(ticker)
            data = {
                'ticker': ticker,
                'company_name': fundamental_data.get('company_name', ticker),
                'sector': fundamental_data.get('sector', 'Unknown'),
                'fundamental_data': fundamental_data,
                'technical_data': technical_data,
                'alternative_data': alternative_data
            }
            self.logger.info(f"Fetched stock data for {ticker}")
            return data
        except Exception as e:
            self.logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return {}

    def _fetch_technical_data(self, ticker: str) -> Dict:
        """Fetch technical data from Yahoo Finance"""
        try:
            cache_key = f"technical:{ticker}"
            cached = self.api_client._cache_get(cache_key)
            if cached:
                return cached
            url = f"{self.base_urls['yahoo_chart']}/{ticker}"
            response = requests.get(url, params={'interval': '1d', 'range': '1y'}, timeout=10)
            response.raise_for_status()
            chart_data = response.json().get('chart', {}).get('result', [{}])[0]
            closes = [c for c in chart_data.get('indicators', {}).get('quote', [{}])[0].get('close', []) if c]
            if len(closes) < 50:
                self.logger.warning(f"Insufficient technical data for {ticker}")
                return {}
            closes_array = np.array(closes)
            result = {
                'current_price': closes[-1],
                'price_change_1m': (closes[-1] - closes[-21]) / closes[-21] * 100 if len(closes) > 21 else 0,
                'rsi': self._calculate_rsi(closes_array),
                'historical_volatility_30d': np.std(closes_array[-30:]) * np.sqrt(252) if len(closes_array) >= 30 else 0
            }
            self.api_client._cache_set(cache_key, result, 300)  # Cache for 5 minutes
            self.logger.info(f"Fetched technical data for {ticker}")
            return result
        except Exception as e:
            self.logger.error(f"Error fetching technical data for {ticker}: {str(e)}")
            return {}

    def _fetch_alternative_data(self, ticker: str) -> Dict:
        """Fetch alternative data from Twitter and Google Trends"""
        try:
            return {
                'social_sentiment_score': self.api_client.get_twitter_sentiment(ticker),
                'google_trends_score': self.api_client.get_google_trends(ticker),
                'news_sentiment': 'Neutral'  # No free news API
            }
        except Exception as e:
            self.logger.error(f"Error fetching alternative data for {ticker}: {str(e)}")
            return {'social_sentiment_score': 0.5, 'google_trends_score': 0.5, 'news_sentiment': 'Neutral'}

    def _analyze_macro_environment(self, portfolio_data: Dict) -> Dict:
        """Analyze macro environment with FRED data"""
        try:
            cpi = self.api_client.get_fred_data('CPIAUCSL')
            interest_rate = self.api_client.get_fred_data('FEDFUNDS')
            return {
                'interest_rate_sensitivity': 'High' if interest_rate > 3 else 'Medium' if interest_rate > 1 else 'Low',
                'inflation_sensitivity': 'High' if cpi > 3 else 'Medium' if cpi > 2 else 'Low',
                'macro_risk_score': min(1.0, (cpi / 100 + interest_rate / 100))
            }
        except Exception as e:
            self.logger.error(f"Error analyzing macro environment: {str(e)}")
            return {'macro_risk_score': 0.5}

    def _calculate_portfolio_summary(self, portfolio_data: Dict, nav: float) -> Dict:
        """Calculate portfolio summary metrics"""
        total_value = 0
        weighted_pe = 0
        for ticker, data in portfolio_data.items():
            weight = data['weight']
            current_price = data['technical_data'].get('current_price', 0)
            shares = (nav * weight) / max(current_price, 1)
            total_value += shares * current_price
            weighted_pe += data['fundamental_data'].get('pe_ratio', 0) * weight
        return {
            'total_portfolio_value': total_value,
            'number_of_holdings': len(portfolio_data),
            'weighted_pe_ratio': weighted_pe
        }

    def _analyze_portfolio_fundamentals(self, portfolio_data: Dict) -> Dict:
        """Analyze portfolio fundamentals"""
        fundamentals = []
        for ticker, data in portfolio_data.items():
            fundamentals.append({
                'ticker': ticker,
                'weight': data['weight'],
                'pe_ratio': data['fundamental_data'].get('pe_ratio', 0),
                'revenue': data['fundamental_data'].get('revenue', 0)
            })
        total_weight = sum(f['weight'] for f in fundamentals)
        return {
            'holdings_fundamentals': fundamentals,
            'portfolio_weighted_pe': sum(f['pe_ratio'] * f['weight'] for f in fundamentals) / total_weight
        }

    def _analyze_portfolio_risk(self, portfolio_data: Dict) -> Dict:
        """Analyze portfolio risk"""
        portfolio_volatility = sum(
            data['technical_data'].get('historical_volatility_30d', 0) * data['weight']
            for data in portfolio_data.values()
        )
        return {
            'portfolio_volatility': portfolio_volatility,
            'sharpe_ratio_estimate': (0.08 - self.risk_free_rate) / max(portfolio_volatility, 0.01)
        }

    def _analyze_portfolio_technicals(self, portfolio_data: Dict) -> Dict:
        """Analyze portfolio technicals"""
        technical_summary = [
            {
                'ticker': ticker,
                'weight': data['weight'],
                'rsi': data['technical_data'].get('rsi', 50),
                'price_change_1m': data['technical_data'].get('price_change_1m', 0)
            }
            for ticker, data in portfolio_data.items()
        ]
        total_weight = sum(t['weight'] for t in technical_summary)
        return {
            'portfolio_rsi': sum(t['rsi'] * t['weight'] for t in technical_summary) / total_weight,
            'portfolio_1m_performance': sum(t['price_change_1m'] * t['weight'] for t in technical_summary) / total_weight
        }

    def _analyze_sector_allocation(self, portfolio_data: Dict) -> Dict:
        """Analyze sector allocation"""
        sector_weights = {}
        for ticker, data in portfolio_data.items():
            sector = data.get('sector', 'Unknown')
            sector_weights[sector] = sector_weights.get(sector, 0) + data['weight']
        return {
            'sector_allocation': sector_weights,
            'most_weighted_sector': max(sector_weights, key=sector_weights.get) if sector_weights else 'Unknown'
        }

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        return 100 - (100 / (1 + avg_gain / max(avg_loss, 1)))