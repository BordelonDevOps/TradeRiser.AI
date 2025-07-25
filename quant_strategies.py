#!/usr/bin/env python3
"""
Quantitative Trading Strategies Module
Integrated from je-suis-tm/quant-trading repository
Adapted for TradeRiser.AI platform
"""

import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class QuantStrategies:
    """
    Collection of quantitative trading strategies adapted from academic research
    and proven algorithmic trading methods.
    """
    
    def __init__(self):
        self.strategies = {
            'macd': self.macd_strategy,
            'rsi_pattern': self.rsi_pattern_strategy,
            'bollinger_bands': self.bollinger_bands_strategy,
            'parabolic_sar': self.parabolic_sar_strategy,
            'awesome_oscillator': self.awesome_oscillator_strategy
        }
    
    def analyze_ticker(self, ticker: str, period: str = "1y") -> Dict:
        """
        Run comprehensive quantitative analysis on a single ticker
        
        Args:
            ticker: Stock symbol
            period: Data period (1y, 6mo, 3mo, etc.)
            
        Returns:
            Dictionary containing all strategy results
        """
        try:
            # Fetch data
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            
            if data.empty:
                return {'error': f'No data available for {ticker}'}
            
            results = {
                'ticker': ticker,
                'period': period,
                'data_points': len(data),
                'strategies': {}
            }
            
            # Run all strategies
            for strategy_name, strategy_func in self.strategies.items():
                try:
                    strategy_result = strategy_func(data)
                    results['strategies'][strategy_name] = strategy_result
                except Exception as e:
                    results['strategies'][strategy_name] = {
                        'error': f'Strategy failed: {str(e)}',
                        'signal': 'HOLD',
                        'confidence': 0.0
                    }
            
            # Calculate overall recommendation
            results['overall_recommendation'] = self._calculate_overall_signal(results['strategies'])
            
            return results
            
        except Exception as e:
            return {'error': f'Analysis failed for {ticker}: {str(e)}'}
    
    def macd_strategy(self, data: pd.DataFrame) -> Dict:
        """
        MACD (Moving Average Convergence Divergence) Strategy
        Based on momentum trading using short and long term moving averages
        """
        try:
            close = data['Close']
            
            # Calculate MACD
            exp1 = close.ewm(span=12).mean()
            exp2 = close.ewm(span=26).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=9).mean()
            histogram = macd - signal_line
            
            # Generate signals
            current_macd = macd.iloc[-1]
            current_signal = signal_line.iloc[-1]
            prev_macd = macd.iloc[-2] if len(macd) > 1 else current_macd
            prev_signal = signal_line.iloc[-2] if len(signal_line) > 1 else current_signal
            
            # Signal logic
            if current_macd > current_signal and prev_macd <= prev_signal:
                signal = 'BUY'
                confidence = min(abs(current_macd - current_signal) / close.iloc[-1] * 100, 1.0)
            elif current_macd < current_signal and prev_macd >= prev_signal:
                signal = 'SELL'
                confidence = min(abs(current_macd - current_signal) / close.iloc[-1] * 100, 1.0)
            else:
                signal = 'HOLD'
                confidence = 0.5
            
            return {
                'signal': signal,
                'confidence': round(confidence, 3),
                'macd': round(current_macd, 4),
                'signal_line': round(current_signal, 4),
                'histogram': round(histogram.iloc[-1], 4),
                'description': 'MACD momentum analysis based on moving average convergence/divergence'
            }
            
        except Exception as e:
             return {
                 'error': str(e),
                 'signal': 'HOLD',
                 'confidence': 0.0
             }
    
    def _calculate_overall_signal(self, strategies: Dict) -> Dict:
        """
        Calculate overall recommendation based on all strategy signals
        """
        signals = []
        confidences = []
        
        for strategy_name, result in strategies.items():
            if 'error' not in result:
                signal = result.get('signal', 'HOLD')
                confidence = result.get('confidence', 0.0)
                
                # Weight signals
                if signal == 'BUY':
                    signals.append(1 * confidence)
                elif signal == 'SELL':
                    signals.append(-1 * confidence)
                else:
                    signals.append(0)
                
                confidences.append(confidence)
        
        if not signals:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'consensus': 'No valid signals'
            }
        
        # Calculate weighted average
        avg_signal = np.mean(signals)
        avg_confidence = np.mean(confidences)
        
        # Determine overall signal
        if avg_signal > 0.3:
            overall_signal = 'BUY'
        elif avg_signal < -0.3:
            overall_signal = 'SELL'
        else:
            overall_signal = 'HOLD'
        
        # Calculate consensus strength
        buy_signals = sum(1 for s in signals if s > 0)
        sell_signals = sum(1 for s in signals if s < 0)
        hold_signals = len(signals) - buy_signals - sell_signals
        
        consensus = f"{buy_signals} BUY, {sell_signals} SELL, {hold_signals} HOLD"
        
        return {
            'signal': overall_signal,
            'confidence': round(avg_confidence, 3),
            'consensus': consensus,
            'signal_strength': round(abs(avg_signal), 3)
        }
    
    def get_strategy_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all available strategies
        """
        return {
            'macd': 'Moving Average Convergence Divergence - Momentum strategy using short and long term moving averages',
            'rsi_pattern': 'Relative Strength Index Pattern Recognition - Identifies overbought/oversold conditions',
            'bollinger_bands': 'Bollinger Bands Pattern Recognition - Volatility and mean reversion analysis',
            'parabolic_sar': 'Parabolic Stop and Reverse - Trend following and reversal detection',
            'awesome_oscillator': 'Awesome Oscillator - Enhanced momentum analysis using high-low midpoint'
        }

# Example usage and testing
if __name__ == "__main__":
    quant = QuantStrategies()
    
    # Test with a sample ticker
    result = quant.analyze_ticker("AAPL", "6mo")
    print("Sample Analysis for AAPL:")
    print(f"Overall Recommendation: {result.get('overall_recommendation', {})}")
    
    for strategy, data in result.get('strategies', {}).items():
        print(f"\n{strategy.upper()}: {data.get('signal', 'N/A')} (Confidence: {data.get('confidence', 0)})")
        if 'description' in data:
            print(f"  {data['description']}")
    
    def parabolic_sar_strategy(self, data: pd.DataFrame) -> Dict:
        """
        Parabolic SAR (Stop and Reverse) Strategy
        Identifies trend direction and potential reversal points
        """
        try:
            high = data['High']
            low = data['Low']
            close = data['Close']
            
            # Simplified Parabolic SAR calculation
            af = 0.02  # Acceleration factor
            max_af = 0.2
            
            sar = [low.iloc[0]]  # Start with first low
            trend = 1  # 1 for uptrend, -1 for downtrend
            ep = high.iloc[0]  # Extreme point
            
            for i in range(1, len(data)):
                if trend == 1:  # Uptrend
                    sar_val = sar[-1] + af * (ep - sar[-1])
                    if low.iloc[i] <= sar_val:
                        trend = -1
                        sar_val = ep
                        ep = low.iloc[i]
                        af = 0.02
                    else:
                        if high.iloc[i] > ep:
                            ep = high.iloc[i]
                            af = min(af + 0.02, max_af)
                else:  # Downtrend
                    sar_val = sar[-1] - af * (sar[-1] - ep)
                    if high.iloc[i] >= sar_val:
                        trend = 1
                        sar_val = ep
                        ep = high.iloc[i]
                        af = 0.02
                    else:
                        if low.iloc[i] < ep:
                            ep = low.iloc[i]
                            af = min(af + 0.02, max_af)
                
                sar.append(sar_val)
            
            current_sar = sar[-1]
            current_price = close.iloc[-1]
            
            # Signal generation
            if trend == 1 and current_price > current_sar:
                signal = 'BUY'
                confidence = 0.7
                trend_direction = 'Uptrend'
            elif trend == -1 and current_price < current_sar:
                signal = 'SELL'
                confidence = 0.7
                trend_direction = 'Downtrend'
            else:
                signal = 'HOLD'
                confidence = 0.5
                trend_direction = 'Reversal Zone'
            
            return {
                'signal': signal,
                'confidence': confidence,
                'sar_value': round(current_sar, 2),
                'trend_direction': trend_direction,
                'description': 'Parabolic SAR trend following and reversal detection'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'signal': 'HOLD',
                'confidence': 0.0
            }
    
    def awesome_oscillator_strategy(self, data: pd.DataFrame) -> Dict:
        """
        Awesome Oscillator Strategy
        Enhanced version of MACD using high-low midpoint instead of close price
        """
        try:
            high = data['High']
            low = data['Low']
            
            # Calculate midpoint
            midpoint = (high + low) / 2
            
            # Calculate Awesome Oscillator
            sma5 = midpoint.rolling(window=5).mean()
            sma34 = midpoint.rolling(window=34).mean()
            ao = sma5 - sma34
            
            # Saucer pattern detection (simplified)
            current_ao = ao.iloc[-1]
            prev_ao = ao.iloc[-2] if len(ao) > 1 else current_ao
            prev2_ao = ao.iloc[-3] if len(ao) > 2 else prev_ao
            
            # Signal generation
            if current_ao > 0 and prev_ao <= 0:
                signal = 'BUY'
                confidence = 0.8
                pattern = 'Zero Line Cross Up'
            elif current_ao < 0 and prev_ao >= 0:
                signal = 'SELL'
                confidence = 0.8
                pattern = 'Zero Line Cross Down'
            elif current_ao > prev_ao > prev2_ao and current_ao > 0:
                signal = 'BUY'
                confidence = 0.6
                pattern = 'Bullish Saucer'
            elif current_ao < prev_ao < prev2_ao and current_ao < 0:
                signal = 'SELL'
                confidence = 0.6
                pattern = 'Bearish Saucer'
            else:
                signal = 'HOLD'
                confidence = 0.5
                pattern = 'No Clear Pattern'
            
            return {
                'signal': signal,
                'confidence': confidence,
                'ao_value': round(current_ao, 4),
                'pattern': pattern,
                'description': 'Awesome Oscillator momentum analysis using high-low midpoint'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'signal': 'HOLD',
                'confidence': 0.0
            }
    
    def bollinger_bands_strategy(self, data: pd.DataFrame) -> Dict:
        """
        Bollinger Bands Pattern Recognition Strategy
        Identifies volatility patterns and mean reversion opportunities
        """
        try:
            close = data['Close']
            
            # Calculate Bollinger Bands
            sma = close.rolling(window=20).mean()
            std = close.rolling(window=20).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            current_price = close.iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            current_sma = sma.iloc[-1]
            
            # Band position analysis
            band_width = (current_upper - current_lower) / current_sma
            price_position = (current_price - current_lower) / (current_upper - current_lower)
            
            # Signal generation
            if current_price >= current_upper:
                signal = 'SELL'
                confidence = min((current_price - current_upper) / current_upper, 1.0)
                pattern = 'Upper Band Breach'
            elif current_price <= current_lower:
                signal = 'BUY'
                confidence = min((current_lower - current_price) / current_lower, 1.0)
                pattern = 'Lower Band Breach'
            elif price_position > 0.8:
                signal = 'SELL'
                confidence = 0.6
                pattern = 'Near Upper Band'
            elif price_position < 0.2:
                signal = 'BUY'
                confidence = 0.6
                pattern = 'Near Lower Band'
            else:
                signal = 'HOLD'
                confidence = 0.5
                pattern = 'Within Bands'
            
            return {
                'signal': signal,
                'confidence': round(confidence, 3),
                'price_position': round(price_position, 3),
                'band_width': round(band_width, 4),
                'pattern': pattern,
                'upper_band': round(current_upper, 2),
                'lower_band': round(current_lower, 2),
                'description': 'Bollinger Bands volatility and mean reversion analysis'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'signal': 'HOLD',
                'confidence': 0.0
            }
    
    def rsi_pattern_strategy(self, data: pd.DataFrame) -> Dict:
        """
        RSI Pattern Recognition Strategy
        Identifies overbought/oversold conditions and divergence patterns
        """
        try:
            close = data['Close']
            
            # Calculate RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi.iloc[-1]
            
            # Pattern recognition
            if current_rsi > 70:
                signal = 'SELL'
                confidence = min((current_rsi - 70) / 30, 1.0)
                pattern = 'Overbought'
            elif current_rsi < 30:
                signal = 'BUY'
                confidence = min((30 - current_rsi) / 30, 1.0)
                pattern = 'Oversold'
            elif current_rsi > 50:
                signal = 'HOLD'
                confidence = 0.6
                pattern = 'Bullish Momentum'
            else:
                signal = 'HOLD'
                confidence = 0.4
                pattern = 'Bearish Momentum'
            
            return {
                'signal': signal,
                'confidence': round(confidence, 3),
                'rsi': round(current_rsi, 2),
                'pattern': pattern,
                'description': 'RSI pattern recognition for momentum and reversal signals'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'signal': 'HOLD',
                'confidence': 0.0
            }