"""ETF Analysis Module for TradeRiser.AI
Based on professional finance toolkit methodologies
Provides comprehensive ETF screening, analysis, and comparison tools
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from Utils.utils_api_client import APIClient
import logging
import requests
from utils_shared import AnalysisBase, TechnicalIndicators, setup_logging

# Setup centralized logging
setup_logging()

class ETFAnalyzer(AnalysisBase):
    def __init__(self, finance_database=None):
        """Initialize ETF analyzer with comprehensive database"""
        super().__init__('ETFAnalyzer')
        self.api_client = APIClient()
        self.finance_database = finance_database
        
        # Comprehensive ETF universe based on Finance Database methodology
        self.etf_universe = {
            # Broad Market ETFs
            'SPY': {'name': 'SPDR S&P 500 ETF', 'category': 'Large Cap Blend', 'expense_ratio': 0.0945, 'aum': 400000},
            'QQQ': {'name': 'Invesco QQQ Trust', 'category': 'Technology', 'expense_ratio': 0.20, 'aum': 200000},
            'IWM': {'name': 'iShares Russell 2000 ETF', 'category': 'Small Cap Blend', 'expense_ratio': 0.19, 'aum': 60000},
            'VTI': {'name': 'Vanguard Total Stock Market', 'category': 'Total Market', 'expense_ratio': 0.03, 'aum': 300000},
            
            # International ETFs
            'EFA': {'name': 'iShares MSCI EAFE ETF', 'category': 'International Developed', 'expense_ratio': 0.32, 'aum': 80000},
            'EEM': {'name': 'iShares MSCI Emerging Markets', 'category': 'Emerging Markets', 'expense_ratio': 0.68, 'aum': 25000},
            'VEA': {'name': 'Vanguard FTSE Developed Markets', 'category': 'International Developed', 'expense_ratio': 0.05, 'aum': 100000},
            'VWO': {'name': 'Vanguard FTSE Emerging Markets', 'category': 'Emerging Markets', 'expense_ratio': 0.10, 'aum': 80000},
            
            # Sector ETFs
            'XLK': {'name': 'Technology Select Sector SPDR', 'category': 'Technology', 'expense_ratio': 0.10, 'aum': 50000},
            'XLF': {'name': 'Financial Select Sector SPDR', 'category': 'Financial', 'expense_ratio': 0.10, 'aum': 40000},
            'XLE': {'name': 'Energy Select Sector SPDR', 'category': 'Energy', 'expense_ratio': 0.10, 'aum': 25000},
            'XLV': {'name': 'Health Care Select Sector SPDR', 'category': 'Healthcare', 'expense_ratio': 0.10, 'aum': 35000},
            'XLI': {'name': 'Industrial Select Sector SPDR', 'category': 'Industrial', 'expense_ratio': 0.10, 'aum': 20000},
            
            # Bond ETFs
            'AGG': {'name': 'iShares Core US Aggregate Bond', 'category': 'Aggregate Bond', 'expense_ratio': 0.03, 'aum': 90000},
            'TLT': {'name': 'iShares 20+ Year Treasury Bond', 'category': 'Long-Term Treasury', 'expense_ratio': 0.15, 'aum': 20000},
            'HYG': {'name': 'iShares iBoxx High Yield Corporate', 'category': 'High Yield Bond', 'expense_ratio': 0.49, 'aum': 15000},
            'LQD': {'name': 'iShares iBoxx Investment Grade', 'category': 'Investment Grade Bond', 'expense_ratio': 0.14, 'aum': 30000},
            
            # Thematic ETFs
            'ARKK': {'name': 'ARK Innovation ETF', 'category': 'Innovation', 'expense_ratio': 0.75, 'aum': 8000},
            'ICLN': {'name': 'iShares Global Clean Energy', 'category': 'Clean Energy', 'expense_ratio': 0.42, 'aum': 5000},
            'ROBO': {'name': 'ROBO Global Robotics and Automation', 'category': 'Robotics', 'expense_ratio': 0.95, 'aum': 2000},
            'FINX': {'name': 'Global X FinTech ETF', 'category': 'FinTech', 'expense_ratio': 0.68, 'aum': 1500},
            
            # Factor ETFs
            'MTUM': {'name': 'iShares MSCI USA Momentum Factor', 'category': 'Momentum', 'expense_ratio': 0.15, 'aum': 15000},
            'QUAL': {'name': 'iShares MSCI USA Quality Factor', 'category': 'Quality', 'expense_ratio': 0.15, 'aum': 12000},
            'SIZE': {'name': 'iShares MSCI USA Size Factor', 'category': 'Size', 'expense_ratio': 0.15, 'aum': 8000},
            'USMV': {'name': 'iShares MSCI USA Min Vol Factor', 'category': 'Low Volatility', 'expense_ratio': 0.15, 'aum': 25000}
        }
    
    def analyze_etf_universe(self) -> Dict:
        """Comprehensive ETF universe analysis"""
        try:
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'etfs': [],
                'market_summary': {
                    'total_analyzed': 0,
                    'avg_expense_ratio': 0,
                    'total_aum': 0,
                    'top_performers': [],
                    'worst_performers': []
                },
                'category_analysis': {},
                'factor_analysis': {},
                'recommendations': []
            }
            
            expense_ratios = []
            total_aum = 0
            
            for symbol, info in self.etf_universe.items():
                etf_data = self._analyze_single_etf(symbol, info)
                if etf_data:
                    analysis['etfs'].append(etf_data)
                    analysis['market_summary']['total_analyzed'] += 1
                    expense_ratios.append(info['expense_ratio'])
                    total_aum += info['aum']
                    
                    # Category analysis
                    category = info['category']
                    if category not in analysis['category_analysis']:
                        analysis['category_analysis'][category] = {
                            'count': 0,
                            'avg_performance': 0,
                            'avg_expense_ratio': 0,
                            'total_aum': 0,
                            'etfs': []
                        }
                    
                    analysis['category_analysis'][category]['count'] += 1
                    analysis['category_analysis'][category]['etfs'].append({
                        'symbol': symbol,
                        'performance_1y': etf_data.get('performance_1y', 0),
                        'sharpe_ratio': etf_data.get('sharpe_ratio', 0)
                    })
                    analysis['category_analysis'][category]['total_aum'] += info['aum']
            
            # Calculate averages
            if expense_ratios:
                analysis['market_summary']['avg_expense_ratio'] = sum(expense_ratios) / len(expense_ratios)
            analysis['market_summary']['total_aum'] = total_aum
            
            # Calculate category averages
            for category, data in analysis['category_analysis'].items():
                if data['etfs']:
                    data['avg_performance'] = sum(etf['performance_1y'] for etf in data['etfs']) / len(data['etfs'])
                    category_etfs = [etf['symbol'] for etf in data['etfs']]
                    category_expense_ratios = [self.etf_universe[symbol]['expense_ratio'] for symbol in category_etfs]
                    data['avg_expense_ratio'] = sum(category_expense_ratios) / len(category_expense_ratios)
            
            # Top and worst performers
            sorted_etfs = sorted(analysis['etfs'], key=lambda x: x.get('performance_1y', 0), reverse=True)
            analysis['market_summary']['top_performers'] = sorted_etfs[:5]
            analysis['market_summary']['worst_performers'] = sorted_etfs[-5:]
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_etf_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in ETF universe analysis: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_single_etf(self, symbol: str, info: Dict) -> Optional[Dict]:
        """Comprehensive single ETF analysis with financial ratios"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2y")
            
            if hist.empty:
                return None
            
            # Basic price metrics
            current_price = hist['Close'].iloc[-1]
            
            # Performance calculations
            performance_1d = self._calculate_return(hist['Close'], 1)
            performance_1w = self._calculate_return(hist['Close'], 7)
            performance_1m = self._calculate_return(hist['Close'], 30)
            performance_3m = self._calculate_return(hist['Close'], 90)
            performance_6m = self._calculate_return(hist['Close'], 180)
            performance_1y = self._calculate_return(hist['Close'], 252)
            
            # Risk metrics
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            downside_deviation = self._calculate_downside_deviation(returns)
            max_drawdown = self._calculate_max_drawdown(hist['Close'])
            
            # Risk-adjusted returns
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            sortino_ratio = self._calculate_sortino_ratio(returns, downside_deviation)
            calmar_ratio = performance_1y / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # Technical indicators
            sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
            rsi = self.technical_indicators.calculate_rsi(hist['Close'])
            
            # Volume analysis
            avg_volume = hist['Volume'].rolling(window=20).mean().iloc[-1]
            volume_trend = self._calculate_volume_trend(hist['Volume'])
            
            # Relative strength vs SPY
            relative_strength = self._calculate_relative_strength(symbol, 'SPY')
            
            # ETF-specific metrics
            premium_discount = self._estimate_premium_discount(ticker)
            
            return {
                'symbol': symbol,
                'name': info['name'],
                'category': info['category'],
                'current_price': round(current_price, 2),
                'expense_ratio': info['expense_ratio'],
                'aum_millions': info['aum'],
                
                # Performance metrics
                'performance_1d': round(performance_1d, 4),
                'performance_1w': round(performance_1w, 4),
                'performance_1m': round(performance_1m, 4),
                'performance_3m': round(performance_3m, 4),
                'performance_6m': round(performance_6m, 4),
                'performance_1y': round(performance_1y, 4),
                
                # Risk metrics
                'volatility': round(volatility, 4),
                'max_drawdown': round(max_drawdown, 4),
                'downside_deviation': round(downside_deviation, 4),
                
                # Risk-adjusted returns
                'sharpe_ratio': round(sharpe_ratio, 3),
                'sortino_ratio': round(sortino_ratio, 3),
                'calmar_ratio': round(calmar_ratio, 3),
                
                # Technical indicators
                'rsi': round(rsi, 2),
                'price_vs_sma50': round((current_price - sma_50) / sma_50, 4),
                'price_vs_sma200': round((current_price - sma_200) / sma_200, 4),
                
                # Volume and liquidity
                'avg_volume': int(avg_volume),
                'volume_trend': volume_trend,
                
                # Relative performance
                'relative_strength_vs_spy': round(relative_strength, 4),
                
                # ETF-specific
                'estimated_premium_discount': round(premium_discount, 4),
                
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing ETF {symbol}: {str(e)}")
            return None
    
    def _calculate_return(self, prices: pd.Series, periods: int) -> float:
        """Calculate return over specified periods"""
        try:
            if len(prices) < periods:
                return 0
            return (prices.iloc[-1] - prices.iloc[-periods]) / prices.iloc[-periods]
        except:
            return 0
    
    def _calculate_downside_deviation(self, returns: pd.Series, target_return: float = 0) -> float:
        """Calculate downside deviation"""
        try:
            downside_returns = returns[returns < target_return]
            return downside_returns.std() * np.sqrt(252)
        except:
            return 0
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        try:
            cumulative = (1 + prices.pct_change()).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            return drawdown.min()
        except:
            return 0
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        try:
            excess_returns = returns.mean() * 252 - risk_free_rate
            return excess_returns / (returns.std() * np.sqrt(252))
        except:
            return 0
    
    def _calculate_sortino_ratio(self, returns: pd.Series, downside_deviation: float, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio"""
        try:
            excess_returns = returns.mean() * 252 - risk_free_rate
            return excess_returns / downside_deviation if downside_deviation != 0 else 0
        except:
            return 0
    
    # RSI calculation moved to shared utilities
    
    def _calculate_volume_trend(self, volume: pd.Series) -> str:
        """Calculate volume trend"""
        try:
            recent_avg = volume.tail(10).mean()
            historical_avg = volume.tail(50).mean()
            if recent_avg > historical_avg * 1.2:
                return 'increasing'
            elif recent_avg < historical_avg * 0.8:
                return 'decreasing'
            else:
                return 'stable'
        except:
            return 'stable'
    
    def _calculate_relative_strength(self, symbol: str, benchmark: str) -> float:
        """Calculate relative strength vs benchmark"""
        try:
            etf_data = yf.Ticker(symbol).history(period="1y")
            benchmark_data = yf.Ticker(benchmark).history(period="1y")
            
            if etf_data.empty or benchmark_data.empty:
                return 0
            
            etf_return = (etf_data['Close'].iloc[-1] - etf_data['Close'].iloc[0]) / etf_data['Close'].iloc[0]
            benchmark_return = (benchmark_data['Close'].iloc[-1] - benchmark_data['Close'].iloc[0]) / benchmark_data['Close'].iloc[0]
            
            return etf_return - benchmark_return
        except:
            return 0
    
    def _estimate_premium_discount(self, ticker) -> float:
        """Estimate premium/discount to NAV (simplified)"""
        try:
            # This is a simplified estimation - in practice, you'd need real NAV data
            info = ticker.info
            nav = info.get('navPrice', info.get('regularMarketPrice', 0))
            market_price = info.get('regularMarketPrice', 0)
            
            if nav > 0 and market_price > 0:
                return (market_price - nav) / nav
            return 0
        except:
            return 0
    
    def _generate_etf_recommendations(self, analysis: Dict) -> List[str]:
        """Generate ETF investment recommendations"""
        recommendations = []
        
        try:
            # Best risk-adjusted returns
            best_sharpe = max(analysis['etfs'], key=lambda x: x.get('sharpe_ratio', 0))
            recommendations.append(f"Best risk-adjusted returns: {best_sharpe['symbol']} (Sharpe: {best_sharpe['sharpe_ratio']})")
            
            # Lowest cost options
            lowest_cost = min(analysis['etfs'], key=lambda x: x.get('expense_ratio', 1))
            recommendations.append(f"Lowest cost option: {lowest_cost['symbol']} (Expense ratio: {lowest_cost['expense_ratio']}%)")
            
            # Category recommendations
            for category, data in analysis['category_analysis'].items():
                if data['avg_performance'] > 0.1:  # 10% annual return
                    recommendations.append(f"{category} sector showing strong performance ({data['avg_performance']:.1%} avg return)")
            
            # Risk warnings
            high_vol_etfs = [etf for etf in analysis['etfs'] if etf.get('volatility', 0) > 0.3]
            if high_vol_etfs:
                recommendations.append(f"High volatility warning: {len(high_vol_etfs)} ETFs show >30% volatility")
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
        
        return recommendations
    
    def screen_etfs(self, criteria: Dict) -> List[Dict]:
        """Screen ETFs based on specific criteria"""
        try:
            analysis = self.analyze_etf_universe()
            filtered_etfs = analysis['etfs']
            
            # Apply filters
            if 'min_aum' in criteria:
                filtered_etfs = [etf for etf in filtered_etfs if etf['aum_millions'] >= criteria['min_aum']]
            
            if 'max_expense_ratio' in criteria:
                filtered_etfs = [etf for etf in filtered_etfs if etf['expense_ratio'] <= criteria['max_expense_ratio']]
            
            if 'min_performance_1y' in criteria:
                filtered_etfs = [etf for etf in filtered_etfs if etf['performance_1y'] >= criteria['min_performance_1y']]
            
            if 'min_sharpe_ratio' in criteria:
                filtered_etfs = [etf for etf in filtered_etfs if etf['sharpe_ratio'] >= criteria['min_sharpe_ratio']]
            
            if 'category' in criteria:
                filtered_etfs = [etf for etf in filtered_etfs if etf['category'] == criteria['category']]
            
            # Sort by specified metric
            sort_by = criteria.get('sort_by', 'sharpe_ratio')
            reverse = criteria.get('sort_descending', True)
            
            return sorted(filtered_etfs, key=lambda x: x.get(sort_by, 0), reverse=reverse)
            
        except Exception as e:
            self.logger.error(f"Error screening ETFs: {str(e)}")
            return []
    
    def compare_etfs(self, symbols: List[str]) -> Dict:
        """Compare multiple ETFs side by side"""
        try:
            comparison = {
                'symbols': symbols,
                'comparison_data': [],
                'summary': {},
                'timestamp': datetime.now().isoformat()
            }
            
            for symbol in symbols:
                if symbol in self.etf_universe:
                    etf_data = self._analyze_single_etf(symbol, self.etf_universe[symbol])
                    if etf_data:
                        comparison['comparison_data'].append(etf_data)
            
            # Generate comparison summary
            if comparison['comparison_data']:
                comparison['summary'] = {
                    'best_performer_1y': max(comparison['comparison_data'], key=lambda x: x['performance_1y']),
                    'lowest_cost': min(comparison['comparison_data'], key=lambda x: x['expense_ratio']),
                    'best_sharpe': max(comparison['comparison_data'], key=lambda x: x['sharpe_ratio']),
                    'lowest_volatility': min(comparison['comparison_data'], key=lambda x: x['volatility'])
                }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing ETFs: {str(e)}")
            return {'error': str(e)}
    
    def get_etf_info(self, symbol: str) -> Dict:
        """Get detailed information about a specific ETF"""
        if symbol in self.etf_universe:
            return self._analyze_single_etf(symbol, self.etf_universe[symbol])
        return {'error': f'ETF {symbol} not found in universe'}
    
    def get_recommendations(self) -> Dict:
        """Get ETF recommendations - wraps analyze_etf_universe functionality"""
        try:
            analysis = self.analyze_etf_universe()
            if 'error' in analysis:
                self.logger.warning("ETF analysis failed, using fallback data")
                return self._create_fallback_etf_data()
            return analysis
        except Exception as e:
            self.logger.error(f"Error getting ETF recommendations: {str(e)}")
            return self._create_fallback_etf_data()
    
    def _create_fallback_etf_data(self) -> Dict:
        """Return error when ETF analysis fails - no placeholder data"""
        return {
            'timestamp': datetime.now().isoformat(),
            'error': 'ETF analysis failed - no data available',
            'message': 'Unable to fetch real ETF data. All APIs are unavailable.',
            'etfs': [],
            'market_summary': {},
            'category_analysis': {},
            'recommendations': []
        }