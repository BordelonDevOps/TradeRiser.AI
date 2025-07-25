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
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import re
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
        """Initialize with Redis or in-memory fallback and tier-based API access"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize subscription tier
        self.subscription_tier = os.getenv('SUBSCRIPTION_TIER', 'free').lower()
        self.is_pro_tier = self.subscription_tier == 'pro'
        
        # Redis configuration
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
            self.redis.ping()  # Test connection
            self.logger.info("Connected to Redis")
        except redis.ConnectionError:
            self.logger.warning("Redis connection failed, using in-memory cache")
            self.redis = None
            self.in_memory_cache = {}
        
        # Free tier APIs (always available)
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.fred_api_key = os.getenv('FRED_API_KEY')
        
        # Pro tier APIs (only available for pro subscribers)
        if self.is_pro_tier:
            self.twitter_api_key = os.getenv('TWITTER_API_KEY')
            self.quandl_api_key = os.getenv('QUANDL_API_KEY')
            self.fmp_api_key = os.getenv('FMP_API_KEY')
            self.iex_cloud_api_key = os.getenv('IEX_CLOUD_API_KEY')
            self.logger.info("Pro tier APIs initialized")
        else:
            self.logger.info("Free tier mode - using free APIs only")
        
        # Alternative sentiment analysis setup (no API keys required)
        self.sentiment_enabled = True
        self.logger.info("Alternative sentiment analysis initialized")
        
        self.pytrends = TrendReq()
    
    def is_api_available(self, api_name: str) -> bool:
        """Check if a specific API is available based on subscription tier"""
        free_tier_apis = ['alpha_vantage', 'fred', 'coingecko', 'pytrends', 'yfinance']
        pro_tier_apis = ['twitter', 'quandl', 'fmp', 'iex_cloud', 'alpaca']
        
        if api_name in free_tier_apis:
            return True
        elif api_name in pro_tier_apis:
            return self.is_pro_tier
        else:
            return False
    
    def get_tier_info(self) -> dict:
        """Get current subscription tier information"""
        return {
            'tier': self.subscription_tier,
            'is_pro': self.is_pro_tier,
            'available_apis': self._get_available_apis(),
            'rate_limits': self._get_rate_limits()
        }
    
    def _get_available_apis(self) -> list:
        """Get list of available APIs for current tier"""
        free_apis = ['Alpha Vantage', 'FRED', 'CoinGecko', 'Google Trends', 'Yahoo Finance']
        pro_apis = ['Twitter', 'Quandl', 'Financial Modeling Prep', 'IEX Cloud', 'Alpaca Trading']
        
        if self.is_pro_tier:
            return free_apis + pro_apis
        else:
            return free_apis
    
    def _get_rate_limits(self) -> dict:
        """Get rate limits for current tier"""
        if self.is_pro_tier:
            return {
                'alpha_vantage': '25 calls/minute (Pro)',
                'twitter': '300 calls/15min (Pro)',
                'fred': '120 calls/minute',
                'coingecko': '50 calls/minute (Pro)',
                'note': 'Pro tier includes higher rate limits and premium APIs'
            }
        else:
            return {
                'alpha_vantage': '5 calls/minute (Free)',
                'fred': '120 calls/minute',
                'coingecko': '10-50 calls/minute (Free)',
                'note': 'Free tier with standard rate limits. Upgrade to Pro for premium features.'
            }

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
    @limits(calls=10, period=60)  # Conservative limit for web scraping
    def get_social_sentiment(self, query: str) -> float:
        """Calculate sentiment score from multiple sources using web scraping"""
        cache_key = f"social_sentiment:{query}"
        cached = self._cache_get(cache_key)
        if cached:
            return float(cached)
        
        try:
            sentiment_scores = []
            
            # Method 1: Reddit sentiment scraping
            reddit_sentiment = self._scrape_reddit_sentiment(query)
            if reddit_sentiment is not None:
                sentiment_scores.append(reddit_sentiment)
            
            # Method 2: News headlines sentiment
            news_sentiment = self._scrape_news_sentiment(query)
            if news_sentiment is not None:
                sentiment_scores.append(news_sentiment)
            
            # Method 3: Yahoo Finance discussions
            yahoo_sentiment = self._scrape_yahoo_discussions(query)
            if yahoo_sentiment is not None:
                sentiment_scores.append(yahoo_sentiment)
            
            # Calculate average sentiment or return neutral if no data
            if sentiment_scores:
                final_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            else:
                final_sentiment = 0.5  # Neutral sentiment
            
            self._cache_set(cache_key, final_sentiment, 3600)  # Cache for 1 hour
            self.logger.info(f"Calculated social sentiment for {query}: {final_sentiment}")
            return final_sentiment
            
        except Exception as e:
            self.logger.error(f"Error calculating social sentiment for {query}: {str(e)}")
            return 0.5  # Return neutral sentiment on error

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

    def _scrape_reddit_sentiment(self, query: str) -> float:
        """Scrape Reddit sentiment for a given query"""
        try:
            # Use Reddit's JSON API (no authentication required for public posts)
            url = f"https://www.reddit.com/search.json?q={query}&sort=hot&limit=25"
            headers = {'User-Agent': 'TradeRiser/1.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
                
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            if not posts:
                return None
                
            sentiments = []
            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                
                # Analyze sentiment of title and text
                text_to_analyze = f"{title} {selftext}"
                if text_to_analyze.strip():
                    sentiment = TextBlob(text_to_analyze).sentiment.polarity
                    sentiments.append(sentiment)
            
            if sentiments:
                # Convert from [-1, 1] to [0, 1] scale
                avg_sentiment = sum(sentiments) / len(sentiments)
                return (avg_sentiment + 1) / 2
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping Reddit sentiment: {str(e)}")
            return None
    
    def _scrape_news_sentiment(self, query: str) -> float:
        """Scrape news headlines sentiment using Google News"""
        try:
            # Use Google News RSS feed
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            headers = {'User-Agent': 'TradeRiser/1.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
                
            # Parse RSS feed
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            if not items:
                return None
                
            sentiments = []
            for item in items[:20]:  # Limit to first 20 headlines
                title = item.find('title')
                if title and title.text:
                    sentiment = TextBlob(title.text).sentiment.polarity
                    sentiments.append(sentiment)
            
            if sentiments:
                # Convert from [-1, 1] to [0, 1] scale
                avg_sentiment = sum(sentiments) / len(sentiments)
                return (avg_sentiment + 1) / 2
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping news sentiment: {str(e)}")
            return None
    
    def _scrape_yahoo_discussions(self, query: str) -> float:
        """Scrape Yahoo Finance discussions for sentiment"""
        try:
            # Yahoo Finance conversations API
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}"
            headers = {'User-Agent': 'TradeRiser/1.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
                
            data = response.json()
            quotes = data.get('quotes', [])
            
            if not quotes:
                return None
            
            # For now, return neutral sentiment as Yahoo Finance discussions
            # require more complex scraping. This is a placeholder.
            # In a real implementation, you'd scrape the actual discussion pages
            return 0.5
            
        except Exception as e:
            self.logger.error(f"Error scraping Yahoo discussions: {str(e)}")
            return None