"""Integrated Finance Database using JerBouma's Finance Database and Toolkit"""
import os
import pandas as pd
import requests
from datetime import datetime
from typing import Dict, List, Optional
from Utils.utils_api_client import APIClient
import logging
from financedatabase import Equities, ETFs, Funds, Indices, Currencies, Moneymarkets
from financetoolkit import Toolkit

logging.basicConfig(
    filename='traderiser.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class IntegratedFinanceDatabase:
    def __init__(self):
        """Initialize the integrated finance database using JerBouma's Finance Database"""
        self.api_client = APIClient()
        self.logger = logging.getLogger(__name__)
        
        # Initialize JerBouma's Finance Database components
        try:
            self.equities = Equities()
            self.etfs = ETFs()
            self.funds = Funds()
            self.indices = Indices()
            self.currencies = Currencies()
            self.money_markets = Moneymarkets()
            self.logger.info("Successfully initialized JerBouma's Finance Database")
        except Exception as e:
            self.logger.error(f"Error initializing Finance Database: {str(e)}")
            # Fallback to basic data
            self.equities = None
            self.etfs = None
        
        self.base_urls = {
            'yahoo_options': 'https://query1.finance.yahoo.com/v7/finance/options',
            'sec_edgar': 'https://www.sec.gov/files/company_tickers.json'
        }
        self._initialize_symbol_database()

    def _initialize_symbol_database(self):
        """Initialize comprehensive symbol database using Finance Database"""
        try:
            symbol_db = {
                'US_STOCKS': {},
                'ETFS': {},
                'CRYPTO': {},
                'INDICES': {},
                'CURRENCIES': {}
            }
            
            # Get equities data from Finance Database
            if self.equities is not None:
                try:
                    # Get a subset of US equities (limit to avoid memory issues)
                    us_equities = self.equities.select(country='United States')
                    # Take first 100 for performance
                    for symbol, data in list(us_equities.items())[:100]:
                        if symbol and isinstance(data, dict):
                            symbol_db['US_STOCKS'][symbol] = {
                                'name': data.get('name', ''),
                                'sector': data.get('sector', ''),
                                'industry': data.get('industry', ''),
                                'market_cap': data.get('market_cap', ''),
                                'country': data.get('country', ''),
                                'has_options': True  # Assume major US stocks have options
                            }
                    self.logger.info(f"Loaded {len(symbol_db['US_STOCKS'])} US equities")
                except Exception as e:
                    self.logger.error(f"Error loading equities: {str(e)}")
            
            # Get ETFs data
            if self.etfs is not None:
                try:
                    us_etfs = self.etfs.select(country='United States')
                    # Take first 50 ETFs for performance
                    for symbol, data in list(us_etfs.items())[:50]:
                        if symbol and isinstance(data, dict):
                            symbol_db['ETFS'][symbol] = {
                                'name': data.get('name', ''),
                                'category': data.get('category', ''),
                                'family': data.get('family', ''),
                                'expense_ratio': data.get('expense_ratio', 0),
                                'total_assets': data.get('total_assets', 0)
                            }
                    self.logger.info(f"Loaded {len(symbol_db['ETFS'])} ETFs")
                except Exception as e:
                    self.logger.error(f"Error loading ETFs: {str(e)}")
            
            # Add some popular cryptocurrencies
            symbol_db['CRYPTO'] = {
                'BTC-USD': {'name': 'Bitcoin', 'category': 'Cryptocurrency', 'market_cap': 'Large'},
                'ETH-USD': {'name': 'Ethereum', 'category': 'Cryptocurrency', 'market_cap': 'Large'},
                'ADA-USD': {'name': 'Cardano', 'category': 'Cryptocurrency', 'market_cap': 'Large'},
                'SOL-USD': {'name': 'Solana', 'category': 'Cryptocurrency', 'market_cap': 'Large'}
            }
            
            # No fallback placeholder data - use only real data from Finance Database
            
            self.symbol_database = symbol_db
            
            # Update has_options for stocks (limit to avoid rate limits)
            for symbol in list(self.symbol_database['US_STOCKS'].keys())[:20]:  # Reduced limit
                options_data = self._get_options_data(symbol)
                self.symbol_database['US_STOCKS'][symbol]['has_options'] = options_data.get('has_options', False)
            
            self.logger.info("Initialized comprehensive symbol database")
            
        except Exception as e:
            self.logger.error(f"Error initializing symbol database: {str(e)}")
            # Return minimal fallback data
            self.symbol_database = {
                'US_STOCKS': {
                    'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'market_cap': 'Large', 'has_options': True},
                    'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology', 'market_cap': 'Large', 'has_options': True}
                },
                'ETFS': {'SPY': {'name': 'SPDR S&P 500 ETF Trust', 'category': 'Large Cap Blend', 'expense_ratio': 0.0945}},
                'CRYPTO': {'BTC-USD': {'name': 'Bitcoin', 'category': 'Cryptocurrency', 'market_cap': 'Large'}}
            }

    def search_instruments(self, query: str, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Search for financial instruments"""
        try:
            results = []
            query_lower = query.lower()
            for db_category, instruments in self.symbol_database.items():
                if category and category.lower() not in db_category.lower():
                    continue
                for symbol, info in instruments.items():
                    if query_lower in symbol.lower() or query_lower in info.get('name', '').lower():
                        result = {
                            'symbol': symbol,
                            'name': info.get('name', ''),
                            'category': info.get('category', db_category),
                            'sector': info.get('sector', ''),
                            'market_cap': info.get('market_cap', ''),
                            'exchange': self._get_exchange_from_symbol(symbol),
                            'currency': 'USD',
                            'has_options': info.get('has_options', False)
                        }
                        results.append(result)
            self.logger.info(f"Searched instruments with query: {query}")
            return sorted(results, key=lambda x: x['symbol'] == query_lower, reverse=True)[:limit]
        except Exception as e:
            self.logger.error(f"Error searching instruments: {str(e)}")
            return []

    def get_instrument_details(self, symbol: str) -> Dict:
        """Get detailed information about a financial instrument"""
        try:
            for db_category, instruments in self.symbol_database.items():
                if symbol in instruments:
                    base_info = instruments[symbol].copy()
                    base_info['database_category'] = db_category
                    base_info['symbol'] = symbol
                    market_data = self.api_client.get_alpha_vantage_quote(symbol)
                    fundamental_data = self.api_client.get_alpha_vantage_fundamentals(symbol)
                    base_info.update(market_data)
                    base_info.update(fundamental_data)
                    if self._has_options(symbol):
                        options_data = self._get_options_data(symbol)
                        base_info['options'] = options_data
                    self.logger.info(f"Fetched details for {symbol}")
                    return base_info
            self.logger.warning(f"Instrument {symbol} not found")
            return {'error': f'Instrument {symbol} not found'}
        except Exception as e:
            self.logger.error(f"Error getting instrument details: {str(e)}")
            return {'error': str(e)}

    def _get_options_data(self, symbol: str) -> Dict:
        """Get options data for a symbol"""
        try:
            cache_key = f"options:{symbol}"
            cached = self.api_client._cache_get(cache_key)
            if cached:
                return cached
            url = f"{self.base_urls['yahoo_options']}/{symbol}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json().get('optionChain', {}).get('result', [{}])[0]
            calls = data.get('options', [{}])[0].get('calls', [])
            puts = data.get('options', [{}])[0].get('puts', [])
            call_ivs = [opt.get('impliedVolatility', 0) for opt in calls]
            put_ivs = [opt.get('impliedVolatility', 0) for opt in puts]
            result = {
                'has_options': bool(calls or puts),
                'implied_volatility_avg': sum(call_ivs + put_ivs) / max(len(call_ivs + put_ivs), 1),
                'expiration_dates': data.get('expirationDates', []),
                'call_options': calls[:10],  # Limit to avoid large responses
                'put_options': puts[:10]
            }
            self.api_client._cache_set(cache_key, result, 3600)  # Cache for 1 hour
            self.logger.info(f"Fetched options data for {symbol}")
            return result
        except Exception as e:
            self.logger.error(f"Error getting options data for {symbol}: {str(e)}")
            return {'has_options': False}

    def _has_options(self, symbol: str) -> bool:
        """Check if symbol has options trading"""
        return self.symbol_database.get('US_STOCKS', {}).get(symbol, {}).get('has_options', False)

    def _get_exchange_from_symbol(self, symbol: str) -> str:
        """Determine exchange from symbol"""
        if symbol.endswith('-USD'):
            return 'CRYPTO'
        return 'NYSE/NASDAQ'