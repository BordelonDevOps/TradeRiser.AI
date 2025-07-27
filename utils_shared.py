"""
Shared utility functions for TradeRiser.AI platform
Consolidates common functions to reduce code duplication
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging once for the entire application
def setup_logging(log_file: str = 'traderiser.log', level: int = logging.INFO) -> logging.Logger:
    """
    Centralized logging configuration for TradeRiser.AI
    """
    logging.basicConfig(
        filename=log_file,
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

# Technical Analysis Utilities
class TechnicalIndicators:
    """
    Shared technical analysis indicators to eliminate code duplication
    """
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)
        Consolidated from multiple analyzer classes
        """
        try:
            if len(prices) < period + 1:
                return 50.0
            
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not rsi.empty else 50.0
        except Exception:
            return 50.0
    
    @staticmethod
    def calculate_rsi_numpy(prices: np.ndarray, period: int = 14) -> float:
        """
        Calculate RSI using numpy arrays (for portfolio_analyzer compatibility)
        """
        try:
            if len(prices) < period + 1:
                return 50.0
            
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
        except Exception:
            return 50.0
    
    @staticmethod
    def calculate_sma(prices: np.ndarray, window: int) -> float:
        """
        Calculate Simple Moving Average
        """
        try:
            if len(prices) < window:
                return 0.0
            return float(np.mean(prices[-window:]))
        except Exception:
            return 0.0
    
    @staticmethod
    def calculate_volatility(prices: pd.Series, annualize: bool = True) -> float:
        """
        Calculate historical volatility
        """
        try:
            returns = prices.pct_change().dropna()
            volatility = returns.std()
            
            if annualize:
                volatility *= np.sqrt(252)  # Annualize assuming 252 trading days
            
            return float(volatility)
        except Exception:
            return 0.0
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio
        """
        try:
            excess_returns = returns.mean() * 252 - risk_free_rate
            return excess_returns / (returns.std() * np.sqrt(252))
        except Exception:
            return 0.0
    
    @staticmethod
    def calculate_max_drawdown(prices: pd.Series) -> float:
        """
        Calculate maximum drawdown
        """
        try:
            cumulative = (1 + prices.pct_change()).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            return float(drawdown.min())
        except Exception:
            return 0.0

# Common Data Processing Utilities
class DataProcessor:
    """
    Shared data processing utilities
    """
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """
        Safely convert value to float with fallback
        """
        try:
            if value is None or value == '':
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def calculate_percentage_change(old_value: float, new_value: float) -> float:
        """
        Calculate percentage change between two values
        """
        try:
            if old_value == 0:
                return 0.0
            return ((new_value - old_value) / old_value) * 100
        except Exception:
            return 0.0
    
    @staticmethod
    def format_currency(value: float, currency: str = 'USD') -> str:
        """
        Format value as currency string
        """
        try:
            if currency == 'USD':
                return f"${value:,.2f}"
            else:
                return f"{value:,.2f} {currency}"
        except Exception:
            return "N/A"
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 2) -> str:
        """
        Format value as percentage string
        """
        try:
            return f"{value * 100:.{decimal_places}f}%"
        except Exception:
            return "N/A"

# Error Handling Utilities
class ErrorHandler:
    """
    Standardized error handling patterns
    """
    
    @staticmethod
    def create_error_response(error_message: str, context: str = "") -> Dict:
        """
        Create standardized error response
        """
        return {
            'error': error_message,
            'message': error_message,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
    
    @staticmethod
    def create_success_response(data: Dict, message: str = "Success") -> Dict:
        """
        Create standardized success response
        """
        return {
            'status': 'success',
            'data': data,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'success': True
        }
    
    @staticmethod
    def log_and_return_error(logger: logging.Logger, error: Exception, context: str) -> Dict:
        """
        Log error and return standardized error response
        """
        error_msg = f"Error in {context}: {str(error)}"
        logger.error(error_msg)
        return ErrorHandler.create_error_response(error_msg, context)

# Common Analysis Patterns
class AnalysisBase:
    """
    Base class for all analyzers to reduce code duplication
    """
    
    def __init__(self, logger_name: str = None):
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)
        self.technical_indicators = TechnicalIndicators()
        self.data_processor = DataProcessor()
        self.error_handler = ErrorHandler()
    
    def _validate_ticker(self, ticker: str) -> bool:
        """
        Validate ticker symbol format
        """
        if not ticker or not isinstance(ticker, str):
            return False
        return len(ticker.strip()) > 0 and ticker.isalnum()
    
    def _create_fallback_data(self, ticker: str, error_message: str) -> Dict:
        """
        Create fallback data structure when analysis fails
        """
        return {
            'ticker': ticker,
            'error': error_message,
            'timestamp': datetime.now().isoformat(),
            'data_available': False
        }
    
    def _generate_recommendation(self, score: float, thresholds: Dict = None) -> str:
        """
        Generate standardized recommendation based on score
        """
        if thresholds is None:
            thresholds = {'strong_buy': 80, 'buy': 60, 'sell': 40, 'strong_sell': 20}
        
        if score >= thresholds['strong_buy']:
            return 'STRONG BUY'
        elif score >= thresholds['buy']:
            return 'BUY'
        elif score >= thresholds['sell']:
            return 'HOLD'
        elif score >= thresholds['strong_sell']:
            return 'SELL'
        else:
            return 'STRONG SELL'

# Constants
COMMON_CONSTANTS = {
    'TRADING_DAYS_PER_YEAR': 252,
    'DEFAULT_RSI_PERIOD': 14,
    'DEFAULT_SMA_SHORT': 20,
    'DEFAULT_SMA_LONG': 50,
    'DEFAULT_RISK_FREE_RATE': 0.02,
    'CACHE_TTL_SECONDS': 300,  # 5 minutes
    'MAX_RETRIES': 3,
    'REQUEST_TIMEOUT': 10
}