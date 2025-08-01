"""Base analyzer class to standardize analyzer structure and reduce code duplication"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
from utils_shared import AnalysisBase, TechnicalIndicators, DataProcessor, ErrorHandler, setup_logging

# Setup centralized logging
setup_logging()

class BaseAnalyzer(AnalysisBase):
    """Base class for all financial analyzers"""
    
    def __init__(self, analyzer_name: str):
        """Initialize base analyzer"""
        super().__init__(analyzer_name)
        self.data_processor = DataProcessor()
        self.error_handler = ErrorHandler()
        
    def fetch_stock_data(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Fetch stock data using yfinance with error handling"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                self.logger.warning(f"No data available for {ticker}")
                return None
                
            self.logger.info(f"Successfully fetched data for {ticker}")
            return hist
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return None
    
    def fetch_stock_info(self, ticker: str) -> Optional[Dict]:
        """Fetch stock info using yfinance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                self.logger.warning(f"No info available for {ticker}")
                return None
                
            return info
            
        except Exception as e:
            self.logger.error(f"Error fetching info for {ticker}: {str(e)}")
            return None
    
    def calculate_basic_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate basic financial metrics"""
        try:
            closes = data['Close'].values
            current_price = float(closes[-1])
            
            # Calculate returns
            returns = data['Close'].pct_change().dropna()
            
            metrics = {
                'current_price': current_price,
                'volatility': self.technical_indicators.calculate_volatility(closes),
                'rsi': self.technical_indicators.calculate_rsi_numpy(closes),
                'sma_20': self.technical_indicators.calculate_sma(closes, 20),
                'sma_50': self.technical_indicators.calculate_sma(closes, 50),
                'sharpe_ratio': self.technical_indicators.calculate_sharpe_ratio(returns.values),
                'max_drawdown': self.technical_indicators.calculate_max_drawdown(closes)
            }
            
            # Calculate price changes
            if len(closes) > 21:
                metrics['price_change_1m'] = self.data_processor.calculate_percentage_change(
                    closes[-21], current_price
                )
            
            if len(closes) > 5:
                metrics['price_change_1w'] = self.data_processor.calculate_percentage_change(
                    closes[-5], current_price
                )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating basic metrics: {str(e)}")
            return {}
    
    def generate_recommendation(self, metrics: Dict[str, float], info: Dict = None) -> Dict[str, Any]:
        """Generate basic recommendation based on metrics"""
        try:
            score = 50  # Start neutral
            reasons = []
            
            # RSI analysis
            rsi = metrics.get('rsi', 50)
            if rsi < 30:
                score += 15
                reasons.append("Oversold conditions (RSI < 30)")
            elif rsi > 70:
                score -= 15
                reasons.append("Overbought conditions (RSI > 70)")
            
            # Volatility analysis
            volatility = metrics.get('volatility', 0.2)
            if volatility > 0.4:
                score -= 10
                reasons.append("High volatility risk")
            elif volatility < 0.15:
                score += 5
                reasons.append("Low volatility")
            
            # Price momentum
            price_change_1m = metrics.get('price_change_1m', 0)
            if price_change_1m > 10:
                score += 10
                reasons.append("Strong positive momentum")
            elif price_change_1m < -10:
                score -= 10
                reasons.append("Negative momentum")
            
            # Moving average analysis
            current_price = metrics.get('current_price', 0)
            sma_20 = metrics.get('sma_20', 0)
            sma_50 = metrics.get('sma_50', 0)
            
            if current_price > sma_20 > sma_50:
                score += 10
                reasons.append("Price above moving averages")
            elif current_price < sma_20 < sma_50:
                score -= 10
                reasons.append("Price below moving averages")
            
            # Determine recommendation
            if score >= 70:
                recommendation = "Strong Buy"
                confidence = "High"
            elif score >= 60:
                recommendation = "Buy"
                confidence = "Medium"
            elif score >= 40:
                recommendation = "Hold"
                confidence = "Medium"
            elif score >= 30:
                recommendation = "Sell"
                confidence = "Medium"
            else:
                recommendation = "Strong Sell"
                confidence = "High"
            
            return {
                'recommendation': recommendation,
                'confidence': confidence,
                'score': round(score, 1),
                'reasoning': reasons[:3],  # Limit to top 3 reasons
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation: {str(e)}")
            return self.error_handler.create_error_response(
                "Failed to generate recommendation", str(e)
            )
    
    @abstractmethod
    def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """Abstract method that must be implemented by subclasses"""
        pass
    
    def format_analysis_result(self, data: Dict[str, Any], ticker: str = None) -> Dict[str, Any]:
        """Format analysis result with standard structure"""
        return {
            'ticker': ticker,
            'analysis_type': self.__class__.__name__,
            'data': data,
            'generated_at': datetime.now().isoformat(),
            'status': 'success' if 'error' not in data else 'error'
        }