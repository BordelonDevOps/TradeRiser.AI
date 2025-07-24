"""
Utility module for handling API calls and caching in TradeRiser platform
"""
import os
import json
import requests
import pandas as pd
from datetime import datetime
import redis
from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.timeseries import TimeSeries
from pytrends.request import TrendReq
import tweepy
from textblob import TextBlob
from ratelimit import limits, sleep_and_retry
import logging

logging.basicConfig(
    filename='traderiser.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class APIClient:
    _twitter_warning_shown = False  # Class variable to track warning
    
    def __init__(self):
        """Initialize with Redis or in-memory fallback"""
        self.logger = logging.getLogger(__name__)
        try:
            self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis.ping()  # Test connection
            self.logger.info("Connected to Redis")
        except redis.ConnectionError:
            self.logger.warning("Redis connection failed, using in-memory cache")
            self.redis = None
            self.in_memory_cache = {}
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        # Twitter API setup (optional)
        twitter_api_key = os.getenv('TWITTER_API_KEY')
        twitter_api_secret = os.getenv('TWITTER_API_SECRET')
        twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        twitter_access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        if all([twitter_api_key, twitter_api_secret, twitter_access_token, twitter_access_token_secret]):
            self.twitter_auth = tweepy.OAuthHandler(twitter_api_key, twitter_api_secret)
            self.twitter_auth.set_access_token(twitter_access_token, twitter_access_token_secret)
            self.twitter_api = tweepy.API(self.twitter_auth, wait_on_rate_limit=True)
            self.twitter_enabled = True
        else:
            self.twitter_api = None
            self.twitter_enabled = False
            # Only show warning once across all instances
            if not APIClient._twitter_warning_shown:
                print("Warning: Twitter API credentials not found. Twitter sentiment analysis disabled.")
                APIClient._twitter_warning_shown = True
        
        self.pytrends = TrendReq()

    def _cache_get(self, key: str) -> dict:
        """Get from cache (Redis or in-memory)"""
        if self.redis:
            cached = self.redis.get(key)
            return json.loads(cached) if cached else None
        return self.in_memory_cache.get(key)

    def _cache_set(self, key: str, value: dict, ttl: int):
        """Set cache (Redis or in-memory)"""
        if self.redis:
            self.redis.setex(key, ttl, json.dumps(value))
        else:
            self.in_memory_cache[key] = value

    @sleep_and_retry
    @limits(calls=5, period=60)  # Alpha Vantage: 5 calls/minute
    def get_alpha_vantage_fundamentals(self, symbol: str) -> dict:
        """Fetch fundamental data from Alpha Vantage"""
        cache_key = f"fundamental:{symbol}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached
        try:
            fd = FundamentalData(key=self.alpha_vantage_key)
            overview, _ = fd.get_company_overview(symbol=symbol)
            data = {
                'eps_trailing': float(overview.get('EPS', 0)),
                'pe_ratio': float(overview.get('PERatio', 0)),
                'revenue': float(overview.get('RevenueTTM', 0)),
                'market_cap': float(overview.get('MarketCapitalization', 0)),
                'dividend_yield': float(overview.get('DividendYield', 0)),
                'beta': float(overview.get('Beta', 1.0)),
                'profit_margin': float(overview.get('ProfitMargin', 0)),
                'last_updated': datetime.now().isoformat()
            }
            self._cache_set(cache_key, data, 86400)  # Cache for 24 hours
            self.logger.info(f"Fetched Alpha Vantage fundamentals for {symbol}")
            return data
        except Exception as e:
            self.logger.error(f"Error fetching Alpha Vantage fundamentals for {symbol}: {str(e)}")
            raise

    @sleep_and_retry
    @limits(calls=5, period=60)  # Alpha Vantage: 5 calls/minute
    def get_alpha_vantage_quote(self, symbol: str) -> dict:
        """Fetch real-time quote from Alpha Vantage"""
        cache_key = f"quote:{symbol}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached
        try:
            ts = TimeSeries(key=self.alpha_vantage_key)
            data, _ = ts.get_quote_endpoint(symbol=symbol)
            result = {
                'price': float(data.get('05. price', 0)),
                'volume': int(data.get('06. volume', 0)),
                'change': float(data.get('09. change', 0)),
                'change_percent': float(data.get('10. change percent', 0).replace('%', '')),
                'last_updated': datetime.now().isoformat()
            }
            self._cache_set(cache_key, result, 300)  # Cache for 5 minutes
            self.logger.info(f"Fetched Alpha Vantage quote for {symbol}")
            return result
        except Exception as e:
            self.logger.error(f"Error fetching Alpha Vantage quote for {symbol}: {str(e)}")
            raise

    @sleep_and_retry
    @limits(calls=30, period=60)  # CoinGecko: conservative 30 calls/minute
    def get_coingecko_data(self, coin_id: str) -> dict:
        """Fetch cryptocurrency data from CoinGecko"""
        cache_key = f"coingecko:{coin_id}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            result = {
                'price': data.get('market_data', {}).get('current_price', {}).get('usd', 0),
                'volume_24h': data.get('market_data', {}).get('total_volume', {}).get('usd', 0),
                'market_cap': data.get('market_data', {}).get('market_cap', {}).get('usd', 0),
                'circulating_supply': data.get('market_data', {}).get('circulating_supply', 0),
                'price_change_24h': data.get('market_data', {}).get('price_change_percentage_24h', 0),
                'last_updated': datetime.now().isoformat()
            }
            self._cache_set(cache_key, result, 3600)  # Cache for 1 hour
            self.logger.info(f"Fetched CoinGecko data for {coin_id}")
            return result
        except Exception as e:
            self.logger.error(f"Error fetching CoinGecko data for {coin_id}: {str(e)}")
            raise

    @sleep_and_retry
    @limits(calls=10, period=60)  # Twitter: conservative limit
    def get_twitter_sentiment(self, query: str) -> float:
        """Calculate sentiment score from Twitter data"""
        if not self.twitter_enabled:
            self.logger.warning("Twitter API not configured, returning neutral sentiment")
            return 0.5
        
        cache_key = f"twitter_sentiment:{query}"
        cached = self._cache_get(cache_key)
        if cached:
            return float(cached)
        try:
            tweets = self.twitter_api.search_tweets(q=query, count=50, lang='en')
            sentiment_score = sum(TextBlob(tweet.text).sentiment.polarity for tweet in tweets) / max(len(tweets), 1) * 0.5 + 0.5
            self._cache_set(cache_key, sentiment_score, 3600)  # Cache for 1 hour
            self.logger.info(f"Fetched Twitter sentiment for {query}")
            return sentiment_score
        except Exception as e:
            self.logger.error(f"Error fetching Twitter sentiment for {query}: {str(e)}")
            raise

    @sleep_and_retry
    @limits(calls=10, period=60)  # pytrends: conservative limit
    def get_google_trends(self, keyword: str) -> float:
        """Fetch Google Trends score"""
        cache_key = f"trends:{keyword}"
        cached = self._cache_get(cache_key)
        if cached:
            return float(cached)
        try:
            self.pytrends.build_payload(kw_list=[keyword], timeframe='now 7-d')
            trends_data = self.pytrends.interest_over_time()
            score = trends_data[keyword].mean() / 100 if keyword in trends_data else 0.5
            self._cache_set(cache_key, score, 86400)  # Cache for 24 hours
            self.logger.info(f"Fetched Google Trends for {keyword}")
            return score
        except Exception as e:
            self.logger.error(f"Error fetching Google Trends for {keyword}: {str(e)}")
            raise

    @sleep_and_retry
    @limits(calls=10, period=60)  # FRED: conservative limit
    def get_fred_data(self, series_id: str) -> float:
        """Fetch economic data from FRED"""
        cache_key = f"fred:{series_id}"
        cached = self._cache_get(cache_key)
        if cached:
            return float(cached)
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={os.getenv('FRED_API_KEY')}&file_type=json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            value = float(response.json()['observations'][-1]['value'])
            self._cache_set(cache_key, value, 86400)  # Cache for 24 hours
            self.logger.info(f"Fetched FRED data for {series_id}")
            return value
        except Exception as e:
            self.logger.error(f"Error fetching FRED data for {series_id}: {str(e)}")
            raise