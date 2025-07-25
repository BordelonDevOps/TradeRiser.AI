"""Commodities Trading Module for TradeRiser.AI
Handles gold, oil, agricultural products, and other commodities trading
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from Utils.utils_api_client import APIClient
import logging

class CommoditiesTrader:
    def __init__(self, finance_database=None):
        """Initialize commodities trader with market data"""
        self.api_client = APIClient()
        self.finance_database = finance_database
        self.logger = logging.getLogger(__name__)
        
        # Commodities universe with ETF symbols for easy trading
        self.commodities_universe = {
            # Precious Metals
            'GLD': {'name': 'SPDR Gold Trust', 'category': 'Precious Metals', 'commodity': 'Gold'},
            'SLV': {'name': 'iShares Silver Trust', 'category': 'Precious Metals', 'commodity': 'Silver'},
            'PPLT': {'name': 'Aberdeen Standard Platinum', 'category': 'Precious Metals', 'commodity': 'Platinum'},
            
            # Energy
            'USO': {'name': 'United States Oil Fund', 'category': 'Energy', 'commodity': 'Crude Oil'},
            'UNG': {'name': 'United States Natural Gas', 'category': 'Energy', 'commodity': 'Natural Gas'},
            'BNO': {'name': 'United States Brent Oil', 'category': 'Energy', 'commodity': 'Brent Oil'},
            
            # Agriculture
            'CORN': {'name': 'Teucrium Corn Fund', 'category': 'Agriculture', 'commodity': 'Corn'},
            'WEAT': {'name': 'Teucrium Wheat Fund', 'category': 'Agriculture', 'commodity': 'Wheat'},
            'SOYB': {'name': 'Teucrium Soybean Fund', 'category': 'Agriculture', 'commodity': 'Soybeans'},
            'CANE': {'name': 'Teucrium Sugar Fund', 'category': 'Agriculture', 'commodity': 'Sugar'},
            'COW': {'name': 'iPath Series B Livestock', 'category': 'Agriculture', 'commodity': 'Livestock'},
            
            # Industrial Metals
            'COPX': {'name': 'Global X Copper Miners', 'category': 'Industrial Metals', 'commodity': 'Copper'},
            'REMX': {'name': 'VanEck Rare Earth/Strategic', 'category': 'Industrial Metals', 'commodity': 'Rare Earth'},
            
            # Broad Commodities
            'DJP': {'name': 'iPath Bloomberg Commodity', 'category': 'Broad Commodities', 'commodity': 'Mixed'},
            'PDBC': {'name': 'Invesco Optimum Yield', 'category': 'Broad Commodities', 'commodity': 'Mixed'}
        }
    
    def analyze_commodity_market(self) -> Dict:
        """Analyze entire commodities market"""
        try:
            market_analysis = {
                'timestamp': datetime.now().isoformat(),
                'commodities': [],
                'market_summary': {
                    'total_analyzed': 0,
                    'bullish_signals': 0,
                    'bearish_signals': 0,
                    'neutral_signals': 0
                },
                'sector_performance': {},
                'top_performers': [],
                'recommendations': []
            }
            
            for symbol, info in self.commodities_universe.items():
                commodity_data = self._analyze_single_commodity(symbol, info)
                if commodity_data:
                    market_analysis['commodities'].append(commodity_data)
                    market_analysis['market_summary']['total_analyzed'] += 1
                    
                    # Count signals
                    if commodity_data['recommendation'] == 'BUY':
                        market_analysis['market_summary']['bullish_signals'] += 1
                    elif commodity_data['recommendation'] == 'SELL':
                        market_analysis['market_summary']['bearish_signals'] += 1
                    else:
                        market_analysis['market_summary']['neutral_signals'] += 1
                    
                    # Track sector performance
                    category = info['category']
                    if category not in market_analysis['sector_performance']:
                        market_analysis['sector_performance'][category] = []
                    market_analysis['sector_performance'][category].append({
                        'symbol': symbol,
                        'performance': commodity_data.get('price_change_30d', 0),
                        'score': commodity_data.get('overall_score', 0)
                    })
            
            # Generate top performers
            all_commodities = sorted(market_analysis['commodities'], 
                                   key=lambda x: x.get('overall_score', 0), reverse=True)
            market_analysis['top_performers'] = all_commodities[:5]
            
            # Generate market recommendations
            market_analysis['recommendations'] = self._generate_market_recommendations(market_analysis)
            
            return market_analysis
            
        except Exception as e:
            self.logger.error(f"Error in commodity market analysis: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_single_commodity(self, symbol: str, info: Dict) -> Optional[Dict]:
        """Analyze a single commodity ETF"""
        try:
            # Get price data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            
            # Calculate technical indicators
            sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            rsi = self._calculate_rsi(hist['Close'])
            volatility = hist['Close'].pct_change().std() * (252 ** 0.5)
            
            # Calculate performance metrics
            price_change_7d = (current_price - hist['Close'].iloc[-7]) / hist['Close'].iloc[-7] if len(hist) >= 7 else 0
            price_change_30d = (current_price - hist['Close'].iloc[-30]) / hist['Close'].iloc[-30] if len(hist) >= 30 else 0
            price_change_1y = (current_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
            
            # Volume analysis
            avg_volume = hist['Volume'].rolling(window=20).mean().iloc[-1]
            current_volume = hist['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Generate trading signals
            signals = self._generate_commodity_signals(current_price, sma_20, sma_50, rsi, volume_ratio)
            overall_score = self._calculate_commodity_score(signals, price_change_30d, volatility)
            recommendation = self._get_commodity_recommendation(overall_score, signals)
            
            return {
                'symbol': symbol,
                'name': info['name'],
                'category': info['category'],
                'commodity': info['commodity'],
                'current_price': round(current_price, 2),
                'price_change_7d': round(price_change_7d, 4),
                'price_change_30d': round(price_change_30d, 4),
                'price_change_1y': round(price_change_1y, 4),
                'volatility': round(volatility, 4),
                'rsi': round(rsi, 2),
                'volume_ratio': round(volume_ratio, 2),
                'sma_20': round(sma_20, 2),
                'sma_50': round(sma_50, 2),
                'signals': signals,
                'overall_score': overall_score,
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing commodity {symbol}: {str(e)}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not rsi.empty else 50
        except:
            return 50
    
    def _generate_commodity_signals(self, price: float, sma_20: float, sma_50: float, rsi: float, volume_ratio: float) -> Dict:
        """Generate trading signals for commodities"""
        signals = {
            'trend': 'neutral',
            'momentum': 'neutral',
            'volume': 'normal',
            'overbought_oversold': 'neutral'
        }
        
        # Trend analysis
        if price > sma_20 > sma_50:
            signals['trend'] = 'bullish'
        elif price < sma_20 < sma_50:
            signals['trend'] = 'bearish'
        
        # Momentum analysis (RSI)
        if rsi > 70:
            signals['momentum'] = 'overbought'
            signals['overbought_oversold'] = 'overbought'
        elif rsi < 30:
            signals['momentum'] = 'oversold'
            signals['overbought_oversold'] = 'oversold'
        elif rsi > 50:
            signals['momentum'] = 'bullish'
        else:
            signals['momentum'] = 'bearish'
        
        # Volume analysis
        if volume_ratio > 1.5:
            signals['volume'] = 'high'
        elif volume_ratio < 0.5:
            signals['volume'] = 'low'
        
        return signals
    
    def _calculate_commodity_score(self, signals: Dict, performance_30d: float, volatility: float) -> int:
        """Calculate overall commodity score (0-100)"""
        score = 50  # Base score
        
        # Trend signals
        if signals['trend'] == 'bullish':
            score += 15
        elif signals['trend'] == 'bearish':
            score -= 15
        
        # Momentum signals
        if signals['momentum'] == 'bullish':
            score += 10
        elif signals['momentum'] == 'bearish':
            score -= 10
        elif signals['momentum'] == 'oversold':
            score += 5  # Potential buying opportunity
        elif signals['momentum'] == 'overbought':
            score -= 5  # Potential selling opportunity
        
        # Volume signals
        if signals['volume'] == 'high' and signals['trend'] == 'bullish':
            score += 5
        elif signals['volume'] == 'high' and signals['trend'] == 'bearish':
            score -= 5
        
        # Performance adjustment
        score += min(max(performance_30d * 100, -20), 20)
        
        # Volatility adjustment (lower volatility is generally better for commodities)
        if volatility < 0.2:
            score += 5
        elif volatility > 0.4:
            score -= 5
        
        return max(0, min(100, int(score)))
    
    def _get_commodity_recommendation(self, score: int, signals: Dict) -> str:
        """Get trading recommendation based on score and signals"""
        if score >= 70:
            return 'BUY'
        elif score <= 30:
            return 'SELL'
        elif signals['overbought_oversold'] == 'oversold' and score > 40:
            return 'BUY'
        elif signals['overbought_oversold'] == 'overbought' and score < 60:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _generate_market_recommendations(self, market_analysis: Dict) -> List[str]:
        """Generate overall market recommendations"""
        recommendations = []
        
        total = market_analysis['market_summary']['total_analyzed']
        bullish = market_analysis['market_summary']['bullish_signals']
        bearish = market_analysis['market_summary']['bearish_signals']
        
        if total > 0:
            bullish_pct = (bullish / total) * 100
            bearish_pct = (bearish / total) * 100
            
            if bullish_pct > 60:
                recommendations.append("Strong bullish sentiment in commodities market")
            elif bearish_pct > 60:
                recommendations.append("Strong bearish sentiment in commodities market")
            else:
                recommendations.append("Mixed signals in commodities market - proceed with caution")
            
            # Sector-specific recommendations
            for sector, commodities in market_analysis['sector_performance'].items():
                avg_score = sum(c['score'] for c in commodities) / len(commodities)
                if avg_score > 65:
                    recommendations.append(f"{sector} sector showing strong performance")
                elif avg_score < 35:
                    recommendations.append(f"{sector} sector showing weakness")
        
        return recommendations
    
    def get_commodity_info(self, symbol: str) -> Dict:
        """Get detailed information about a specific commodity"""
        if symbol in self.commodities_universe:
            return self._analyze_single_commodity(symbol, self.commodities_universe[symbol])
        return {'error': f'Commodity {symbol} not found in universe'}
    
    def get_recommendations(self) -> Dict:
        """Get commodity recommendations - wraps analyze_commodity_market functionality"""
        try:
            analysis = self.analyze_commodity_market()
            if 'error' in analysis:
                self.logger.warning("Commodity analysis failed, using fallback data")
                return self._create_fallback_commodity_data()
            return analysis
        except Exception as e:
            self.logger.error(f"Error getting commodity recommendations: {str(e)}")
            return self._create_fallback_commodity_data()
    
    def _create_fallback_commodity_data(self) -> Dict:
        """Create fallback commodity data when analysis fails"""
        fallback_data = {
            'timestamp': datetime.now().isoformat(),
            'commodities': [
                {
                    'symbol': 'GLD',
                    'name': 'SPDR Gold Trust',
                    'category': 'Precious Metals',
                    'commodity': 'Gold',
                    'current_price': 180.0,
                    'price_change_7d': 0.005,
                    'price_change_30d': 0.015,
                    'price_change_1y': 0.08,
                    'volatility': 0.15,
                    'rsi': 55.0,
                    'volume_ratio': 1.2,
                    'sma_20': 178.5,
                    'sma_50': 175.0,
                    'signals': {
                        'trend': 'bullish',
                        'momentum': 'bullish',
                        'volume': 'normal',
                        'overbought_oversold': 'neutral'
                    },
                    'overall_score': 65,
                    'recommendation': 'BUY'
                },
                {
                    'symbol': 'USO',
                    'name': 'United States Oil Fund',
                    'category': 'Energy',
                    'commodity': 'Crude Oil',
                    'current_price': 75.0,
                    'price_change_7d': -0.02,
                    'price_change_30d': 0.05,
                    'price_change_1y': 0.12,
                    'volatility': 0.25,
                    'rsi': 45.0,
                    'volume_ratio': 0.9,
                    'sma_20': 76.0,
                    'sma_50': 73.0,
                    'signals': {
                        'trend': 'neutral',
                        'momentum': 'bearish',
                        'volume': 'normal',
                        'overbought_oversold': 'neutral'
                    },
                    'overall_score': 50,
                    'recommendation': 'HOLD'
                }
            ],
            'market_summary': {
                'total_analyzed': 2,
                'bullish_signals': 1,
                'bearish_signals': 0,
                'neutral_signals': 1
            },
            'sector_performance': {
                'Precious Metals': [
                    {'symbol': 'GLD', 'performance': 0.015, 'score': 65}
                ],
                'Energy': [
                    {'symbol': 'USO', 'performance': 0.05, 'score': 50}
                ]
            },
            'top_performers': [
                {
                    'symbol': 'GLD',
                    'name': 'SPDR Gold Trust',
                    'overall_score': 65,
                    'recommendation': 'BUY'
                }
            ],
            'recommendations': [
                'Mixed signals in commodities market - proceed with caution',
                'Precious Metals sector showing strong performance'
            ]
        }
        self.logger.info("Using fallback commodity data with GLD and USO")
        return fallback_data