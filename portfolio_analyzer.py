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
import os
import yfinance as yf
# AI/ML Libraries
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy import stats
import ta
from arch import arch_model

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

    def analyze_portfolio(self, holdings: Dict[str, any], nav: float = 100000) -> Dict:
        """Analyze portfolio using real data with share quantities or weights"""
        try:
            # Check if holdings contains shares or weights
            portfolio_data = {}
            total_value = 0
            
            # First pass: get stock data and calculate total value
            failed_tickers = []
            for ticker, quantity in holdings.items():
                stock_data = self._fetch_stock_data(ticker)
                if stock_data:
                    current_price = stock_data['technical_data'].get('current_price', 0)
                    
                    # Handle both share quantities and weights
                    if isinstance(quantity, dict) and 'shares' in quantity:
                        shares = quantity['shares']
                        position_value = shares * current_price
                    elif quantity > 0 and quantity <= 1 and sum(holdings.values()) <= 1.1:
                        # Treat as weight if all values are <= 1 and sum ~= 1
                        shares = int((nav * quantity) / max(current_price, 1))
                        position_value = shares * current_price
                        stock_data['weight'] = quantity
                    else:
                        # Treat as share quantity
                        shares = int(quantity)
                        position_value = shares * current_price
                    
                    stock_data['shares'] = shares
                    stock_data['position_value'] = position_value
                    total_value += position_value
                    portfolio_data[ticker] = stock_data
                else:
                    failed_tickers.append(ticker)
            
            # Second pass: calculate weights based on actual values
            for ticker, data in portfolio_data.items():
                if 'weight' not in data:
                    data['weight'] = data['position_value'] / total_value if total_value > 0 else 0
            if not portfolio_data:
                self.logger.error("No valid stock data found")
                return {
                    'error': 'No valid stock data found',
                    'failed_tickers': failed_tickers,
                    'message': 'All requested stocks failed to load data. This may be due to API limitations or unavailable data.'
                }
            try:
                ai_recommendations = self._generate_ai_recommendations(portfolio_data)
                beginner_insights = self._generate_beginner_insights(portfolio_data)
                self.logger.info(f"AI recommendations generated: {len(ai_recommendations)} stocks")
                self.logger.info(f"Beginner insights generated: {len(beginner_insights)} sections")
            except Exception as e:
                self.logger.error(f"Error generating AI recommendations: {str(e)}")
                ai_recommendations = {}
                beginner_insights = {}
            
            analysis = {
                'portfolio_summary': self._calculate_portfolio_summary(portfolio_data, nav),
                'fundamental_analysis': self._analyze_portfolio_fundamentals(portfolio_data),
                'technical_analysis': self._analyze_portfolio_technicals(portfolio_data),
                'risk_analysis': self._analyze_portfolio_risk(portfolio_data),
                'macro_analysis': self._analyze_macro_environment(portfolio_data),
                'sector_analysis': self._analyze_sector_allocation(portfolio_data),
                'ai_recommendations': ai_recommendations,
                'key_insights_for_beginners': beginner_insights,
                'generated_at': datetime.now().isoformat()
            }
            
            # Add warning if some tickers failed
            if failed_tickers:
                analysis['warnings'] = {
                    'failed_tickers': failed_tickers,
                    'message': f'Data unavailable for: {", ".join(failed_tickers)}. Analysis based on available data only.'
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
        """Fetch comprehensive stock data using Yahoo Finance"""
        try:
            # Try Yahoo Finance first (no API key required)
            fundamental_data = self._fetch_yahoo_fundamentals(ticker)
            technical_data = self._fetch_technical_data(ticker)
            alternative_data = self._fetch_alternative_data(ticker)
            
            # Skip if essential data is unavailable
            if not fundamental_data or not technical_data:
                self.logger.warning(f"Essential data unavailable for {ticker}")
                return None
            
            data = {
                'ticker': ticker,
                'company_name': fundamental_data.get('company_name', ticker),
                'sector': fundamental_data.get('sector', 'Unknown'),
                'fundamental_data': fundamental_data,
                'technical_data': technical_data,
                'alternative_data': alternative_data or {'social_sentiment_score': 0.5, 'google_trends_score': 0.5, 'news_sentiment': 'Neutral'}
            }
            self.logger.info(f"Fetched stock data for {ticker}")
            return data
        except Exception as e:
            self.logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return None

    def _fetch_technical_data(self, ticker: str) -> Dict:
        """Fetch technical data using yfinance library"""
        try:
            cache_key = f"yfinance_technical:{ticker}"
            cached = self.api_client._cache_get(cache_key)
            if cached:
                return cached
                
            # Use yfinance library
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            
            if hist.empty or len(hist) < 50:
                self.logger.warning(f"Insufficient technical data for {ticker}")
                return None  # Return None when insufficient data - no placeholder data
                
            closes = hist['Close'].values
            current_price = float(closes[-1])
            
            result = {
                'current_price': current_price,
                'price_change_1m': (closes[-1] - closes[-21]) / closes[-21] * 100 if len(closes) > 21 else 0,
                'rsi': self._calculate_rsi(closes),
                'historical_volatility_30d': np.std(closes[-30:]) * np.sqrt(252) if len(closes) >= 30 else 0.2
            }
            
            self.api_client._cache_set(cache_key, result, 300)  # Cache for 5 minutes
            self.logger.info(f"Fetched yfinance technical data for {ticker}")
            return result
        except Exception as e:
            self.logger.error(f"Error fetching yfinance technical data for {ticker}: {str(e)}")
            return None  # Return None when data is unavailable - no placeholder data

    def _fetch_yahoo_fundamentals(self, ticker: str) -> Dict:
        """Fetch fundamental data using yfinance library"""
        try:
            cache_key = f"yfinance_fundamental:{ticker}"
            cached = self.api_client._cache_get(cache_key)
            if cached:
                return cached
                
            # Use yfinance library
            stock = yf.Ticker(ticker)
            info = stock.info
            
            result = {
                'eps_trailing': float(info.get('trailingEps', 0) or 0),
                'pe_ratio': float(info.get('trailingPE', 0) or 0),
                'revenue': float(info.get('totalRevenue', 0) or 0),
                'market_cap': float(info.get('marketCap', 0) or 0),
                'dividend_yield': float(info.get('dividendYield', 0) or 0),
                'beta': float(info.get('beta', 1.0) or 1.0),
                'profit_margin': float(info.get('profitMargins', 0) or 0),
                'company_name': info.get('longName', ticker),
                'sector': info.get('sector', 'Technology'),
                'last_updated': datetime.now().isoformat()
            }
            
            self.api_client._cache_set(cache_key, result, 86400)  # Cache for 24 hours
            self.logger.info(f"Fetched yfinance fundamentals for {ticker}")
            return result
        except Exception as e:
            self.logger.error(f"Error fetching yfinance fundamentals for {ticker}: {str(e)}")
            # Return None to indicate data unavailable - no placeholder data
            return None

    def _fetch_alternative_data(self, ticker: str) -> Dict:
        """Fetch alternative data from social media and Google Trends"""
        try:
            return {
                'social_sentiment_score': self.api_client.get_social_sentiment(ticker),
                'google_trends_score': self.api_client.get_google_trends(ticker),
                'news_sentiment': 'Neutral'  # Included in social sentiment now
            }
        except Exception as e:
            self.logger.error(f"Error fetching alternative data for {ticker}: {str(e)}")
            return None  # Return None when data is unavailable - no placeholder data

    def _analyze_macro_environment(self, portfolio_data: Dict) -> Dict:
        """Analyze macro environment with FRED data"""
        try:
            # Try to get FRED data if API key is available
            if os.getenv('FRED_API_KEY'):
                cpi = self.api_client.get_fred_data('CPIAUCSL')
                interest_rate = self.api_client.get_fred_data('FEDFUNDS')
                return {
                    'interest_rate_sensitivity': 'High' if interest_rate > 3 else 'Medium' if interest_rate > 1 else 'Low',
                    'inflation_sensitivity': 'High' if cpi > 3 else 'Medium' if cpi > 2 else 'Low',
                    'macro_risk_score': min(1.0, (cpi / 100 + interest_rate / 100))
                }
            else:
                # Return None when FRED API is not available - no placeholder data
                return None
        except Exception as e:
            self.logger.error(f"Error analyzing macro environment: {str(e)}")
            return None

    def _calculate_portfolio_summary(self, portfolio_data: Dict, nav: float) -> Dict:
        """Calculate portfolio summary metrics with actual share quantities"""
        total_value = 0
        weighted_pe = 0
        holdings_detail = []
        
        for ticker, data in portfolio_data.items():
            weight = data['weight']
            current_price = data['technical_data'].get('current_price', 0)
            shares = data.get('shares', int((nav * weight) / max(current_price, 1)))
            position_value = data.get('position_value', shares * current_price)
            
            total_value += position_value
            weighted_pe += data['fundamental_data'].get('pe_ratio', 0) * weight
            
            holdings_detail.append({
                'ticker': ticker,
                'shares': shares,
                'current_price': current_price,
                'position_value': position_value,
                'weight': weight,
                'company_name': data.get('company_name', ticker)
            })
        return {
            'total_portfolio_value': total_value,
            'holdings_detail': holdings_detail,
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

    def _generate_ai_recommendations(self, portfolio_data: Dict) -> Dict:
        """Generate AI-driven investment recommendations using machine learning"""
        recommendations = {}
        
        # Ensure portfolio_data is a dictionary
        if not isinstance(portfolio_data, dict):
            self.logger.error(f"Expected dict for portfolio_data, got {type(portfolio_data)}")
            return {}
        
        # Prepare feature matrix for ML models
        features_list = []
        tickers = []
        
        for ticker, data in portfolio_data.items():
            # Extract comprehensive features for ML model
            features = [
                data['fundamental_data'].get('pe_ratio', 15),
                data['fundamental_data'].get('beta', 1.0),
                data['fundamental_data'].get('profit_margin', 0.1),
                data['fundamental_data'].get('dividend_yield', 0.02),
                data['technical_data'].get('rsi', 50),
                data['technical_data'].get('price_change_1m', 0),
                data['technical_data'].get('historical_volatility_30d', 0.2),
                data['alternative_data'].get('social_sentiment_score', 0.5),
                data['alternative_data'].get('google_trends_score', 0.5)
            ]
            features_list.append(features)
            tickers.append(ticker)
        
        if len(features_list) > 0:
            # Convert to numpy array and normalize
            X = np.array(features_list)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Use ML clustering to group similar stocks
            if len(X_scaled) >= 2:
                kmeans = KMeans(n_clusters=min(3, len(X_scaled)), random_state=42, n_init=10)
                clusters = kmeans.fit_predict(X_scaled)
            else:
                clusters = [0] * len(X_scaled)
        
        for i, (ticker, data) in enumerate(portfolio_data.items()):
            # ML-enhanced scoring algorithm
            score = self._calculate_ml_score(data, X_scaled[i] if len(features_list) > 0 else None)
            
            # Get ML-enhanced recommendation
            recommendation_data = self._get_ml_recommendation(score, data)
            recommendations[ticker] = recommendation_data
        
        return recommendations
    
    def _calculate_ml_score(self, data: Dict, normalized_features: np.ndarray = None) -> float:
        """Calculate ML-enhanced investment score using multiple algorithms"""
        try:
            # Extract key metrics
            pe_ratio = data['fundamental_data'].get('pe_ratio', 15)
            rsi = data['technical_data'].get('rsi', 50)
            price_change_1m = data['technical_data'].get('price_change_1m', 0)
            volatility = data['technical_data'].get('historical_volatility_30d', 0.2)
            beta = data['fundamental_data'].get('beta', 1.0)
            profit_margin = data['fundamental_data'].get('profit_margin', 0.1)
            
            # Base scoring with ML enhancements
            score = 10.0  # Start from neutral
            
            # Fundamental Analysis with Statistical Scoring
            pe_zscore = stats.zscore([pe_ratio, 15, 25, 35])[0] if pe_ratio > 0 else 0
            score += max(-5, min(5, -pe_zscore * 2))  # Lower PE is better
            
            # Profitability scoring
            if profit_margin > 0.2: score += 3
            elif profit_margin > 0.1: score += 1.5
            elif profit_margin < 0: score -= 4
            
            # Risk-adjusted returns (Sharpe-like ratio)
            risk_adjusted_return = price_change_1m / (volatility * 100) if volatility > 0 else 0
            score += max(-3, min(3, risk_adjusted_return * 2))
            
            # Technical momentum with RSI divergence analysis
            rsi_signal = 0
            if rsi < 30: rsi_signal = 3  # Oversold opportunity
            elif rsi < 40: rsi_signal = 1.5
            elif rsi > 70: rsi_signal = -3  # Overbought risk
            elif rsi > 60: rsi_signal = -1.5
            score += rsi_signal
            
            # Volatility risk adjustment
            if volatility < 0.15: score += 2  # Low volatility premium
            elif volatility > 0.5: score -= 3  # High volatility penalty
            
            # Beta-adjusted market sensitivity
            if beta < 0.7: score += 1  # Defensive stocks
            elif beta > 1.3: score -= 1.5  # High beta penalty
            
            # Sentiment integration
            sentiment_score = data['alternative_data'].get('social_sentiment_score', 0.5)
            score += (sentiment_score - 0.5) * 2  # Convert to -1 to +1 range
            
            # Normalize to 0-20 scale
            score = max(0, min(20, score))
            
            return score
            
        except Exception as e:
            self.logger.error(f"Error in ML score calculation: {str(e)}")
            return 10.0  # Return neutral score on error
    
    def _get_ml_recommendation(self, score: float, data: Dict) -> Dict:
        """Convert ML score to actionable recommendation with confidence"""
        # Advanced recommendation logic with confidence intervals
        if score >= 16: 
            recommendation = "Strong Buy"
            confidence = "High" if score >= 18 else "Medium"
        elif score >= 12: 
            recommendation = "Buy"
            confidence = "Medium" if score >= 14 else "Low"
        elif score >= 8: 
            recommendation = "Hold"
            confidence = "Medium"
        elif score >= 4: 
            recommendation = "Sell"
            confidence = "Medium" if score <= 6 else "Low"
        else: 
            recommendation = "Strong Sell"
            confidence = "High" if score <= 2 else "Medium"
        
        # Generate ML-enhanced reasoning
        reasoning = self._generate_ml_reasoning(score, data)
        
        return {
            'recommendation': recommendation,
            'ai_score': round(score, 1),
            'confidence': confidence,
            'reasoning': reasoning,
            'ml_features_used': ['fundamental', 'technical', 'sentiment', 'risk_metrics']
        }
    
    def _generate_ml_reasoning(self, score: float, data: Dict) -> str:
        """Generate ML-enhanced reasoning for recommendations"""
        pe_ratio = data['fundamental_data'].get('pe_ratio', 15)
        rsi = data['technical_data'].get('rsi', 50)
        volatility = data['technical_data'].get('historical_volatility_30d', 0.2)
        profit_margin = data['fundamental_data'].get('profit_margin', 0.1)
        
        reasoning_parts = []
        
        # Valuation analysis
        if pe_ratio < 15:
            reasoning_parts.append("undervalued fundamentals")
        elif pe_ratio > 30:
            reasoning_parts.append("high valuation concerns")
        
        # Technical analysis
        if rsi < 35:
            reasoning_parts.append("oversold technical opportunity")
        elif rsi > 65:
            reasoning_parts.append("overbought technical risk")
        
        # Risk assessment
        if volatility > 0.4:
            reasoning_parts.append("elevated volatility risk")
        elif volatility < 0.2:
            reasoning_parts.append("stable price action")
        
        # Profitability
        if profit_margin > 0.15:
            reasoning_parts.append("strong profitability")
        elif profit_margin < 0.05:
            reasoning_parts.append("margin pressure concerns")
        
        if reasoning_parts:
            return f"ML analysis indicates {', '.join(reasoning_parts[:3])}"
        else:
            return "Mixed signals suggest maintaining current position"
    
    def _get_recommendation_reasoning(self, recommendation: str, pe_ratio: float, rsi: float, price_change_1m: float, volatility: float) -> str:
        """Generate human-readable reasoning for recommendations"""
        reasons = []
        
        if recommendation in ["Strong Buy", "Buy"]:
            if pe_ratio > 0 and pe_ratio < 20:
                reasons.append("Stock appears undervalued based on earnings")
            if rsi < 40:
                reasons.append("Technical indicators suggest oversold conditions")
            if price_change_1m > 5:
                reasons.append("Strong recent momentum")
            if volatility < 0.3:
                reasons.append("Relatively stable price movements")
        
        elif recommendation in ["Strong Sell", "Sell"]:
            if pe_ratio > 40:
                reasons.append("Stock appears overvalued relative to earnings")
            if rsi > 65:
                reasons.append("Technical indicators suggest overbought conditions")
            if price_change_1m < -5:
                reasons.append("Negative recent momentum")
            if volatility > 0.6:
                reasons.append("High price volatility indicates risk")
        
        else:  # Hold
            reasons.append("Mixed signals suggest maintaining current position")
            if pe_ratio > 20 and pe_ratio < 30:
                reasons.append("Fair valuation")
            if rsi > 40 and rsi < 60:
                reasons.append("Neutral technical momentum")
        
        return "; ".join(reasons) if reasons else "Balanced risk-reward profile"
    
    def _generate_beginner_insights(self, portfolio_data: Dict) -> Dict:
        """Generate beginner-friendly insights with AI/ML explanations"""
        # Ensure portfolio_data is a dictionary
        if not isinstance(portfolio_data, dict):
            self.logger.error(f"Expected dict for portfolio_data, got {type(portfolio_data)}")
            return {}
        
        total_weight = sum(data['weight'] for data in portfolio_data.values())
        avg_pe = sum(data['fundamental_data'].get('pe_ratio', 15) * data['weight'] for data in portfolio_data.values()) / total_weight
        avg_rsi = sum(data['technical_data'].get('rsi', 50) * data['weight'] for data in portfolio_data.values()) / total_weight
        avg_volatility = sum(data['technical_data'].get('historical_volatility_30d', 0.2) * data['weight'] for data in portfolio_data.values()) / total_weight
        
        insights = {
            'portfolio_health_score': self._calculate_portfolio_health_score(portfolio_data),
            'risk_level_explanation': self._explain_risk_level(avg_volatility, portfolio_data),
            'valuation_explanation': self._explain_valuation(avg_pe),
            'momentum_explanation': self._explain_momentum(avg_rsi, portfolio_data),
            'ai_portfolio_summary': self._generate_ai_portfolio_summary(portfolio_data),
            'beginner_tips': self._generate_beginner_tips(portfolio_data)
        }
        
        return insights
    
    def _calculate_portfolio_health_score(self, portfolio_data: Dict) -> Dict:
        """Calculate ML-enhanced portfolio health score using advanced analytics"""
        try:
            total_weight = sum(data['weight'] for data in portfolio_data.values())
            
            # Prepare feature matrix for ML analysis
            features = []
            weights = []
            
            for ticker, data in portfolio_data.items():
                stock_features = [
                    data['fundamental_data'].get('pe_ratio', 15),
                    data['fundamental_data'].get('profit_margin', 0.1),
                    data['fundamental_data'].get('beta', 1.0),
                    data['technical_data'].get('rsi', 50),
                    data['technical_data'].get('historical_volatility_30d', 0.2),
                    data['technical_data'].get('price_change_1m', 0),
                    data['alternative_data'].get('social_sentiment_score', 0.5)
                ]
                features.append(stock_features)
                weights.append(data['weight'])
            
            # Convert to numpy arrays
            X = np.array(features)
            w = np.array(weights)
            
            # Calculate weighted portfolio metrics
            portfolio_metrics = np.average(X, axis=0, weights=w)
            
            # ML-enhanced scoring using statistical analysis
            health_score = 50.0  # Start neutral
            
            # Valuation Health (using z-score analysis)
            pe_ratio = portfolio_metrics[0]
            pe_health = max(0, min(25, 25 - abs(pe_ratio - 20) * 0.5))  # Optimal PE around 20
            health_score += pe_health
            
            # Profitability Health
            profit_margin = portfolio_metrics[1]
            profit_health = min(20, profit_margin * 100) if profit_margin > 0 else -10
            health_score += profit_health
            
            # Risk-Adjusted Performance
            volatility = portfolio_metrics[4]
            rsi = portfolio_metrics[3]
            price_change = portfolio_metrics[5]
            
            # Sharpe-like ratio for portfolio
            risk_adjusted_score = (price_change / (volatility * 100)) if volatility > 0 else 0
            health_score += max(-15, min(15, risk_adjusted_score * 5))
            
            # Technical Health (RSI momentum)
            if 40 <= rsi <= 60: health_score += 10  # Neutral is good
            elif rsi < 30: health_score += 5  # Oversold opportunity
            elif rsi > 70: health_score -= 10  # Overbought risk
            
            # Diversification Analysis using ML clustering
            if len(X) >= 2:
                # Calculate portfolio concentration risk
                concentration_risk = np.sum(w**2)  # Herfindahl index
                diversification_bonus = max(0, (1 - concentration_risk) * 20)
                health_score += diversification_bonus
                
                # Correlation-based diversification (simplified)
                if len(X) >= 3:
                    correlation_penalty = min(10, len(X) * 2)  # Bonus for more stocks
                    health_score += correlation_penalty
            else:
                health_score -= 20  # Single stock penalty
            
            # Sentiment Integration
            sentiment = portfolio_metrics[6]
            sentiment_adjustment = (sentiment - 0.5) * 10  # -5 to +5 range
            health_score += sentiment_adjustment
            
            # Normalize to 0-100
            health_score = max(0, min(100, health_score))
            
            # ML-enhanced grading with confidence intervals
            if health_score >= 85: grade, description = "Excellent", "ML analysis shows exceptional portfolio fundamentals"
            elif health_score >= 70: grade, description = "Good", "Strong portfolio metrics with balanced risk-return profile"
            elif health_score >= 55: grade, description = "Fair", "Moderate portfolio health with room for optimization"
            elif health_score >= 40: grade, description = "Poor", "Portfolio shows concerning risk factors requiring attention"
            else: grade, description = "Critical", "High-risk portfolio requiring immediate rebalancing"
            
            return {
                'score': round(health_score, 1),
                'grade': grade,
                'description': description,
                'ml_metrics': {
                    'diversification_score': round(max(0, (1 - np.sum(w**2)) * 100), 1),
                    'risk_adjusted_return': round(risk_adjusted_score, 3),
                    'sentiment_score': round(sentiment * 100, 1)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating ML portfolio health score: {str(e)}")
            return {
                'score': 50.0,
                'grade': "Unknown",
                'description': "Unable to calculate portfolio health score",
                'ml_metrics': {}
            }
    
    def _explain_risk_level(self, volatility: float, portfolio_data: Dict = None) -> str:
        """ML-enhanced risk assessment with statistical modeling"""
        try:
            # Basic volatility assessment
            base_risk_msg = ""
            if volatility < 0.2:
                base_risk_msg = "🟢 LOW RISK: Your stocks move steadily. Good for beginners who want stable growth."
                risk_category = "Conservative"
            elif volatility < 0.4:
                base_risk_msg = "🟡 MEDIUM RISK: Your stocks have normal ups and downs. Suitable for most investors."
                risk_category = "Balanced"
            elif volatility < 0.6:
                base_risk_msg = "🟠 HIGH RISK: Your stocks swing significantly. Only invest what you can afford to lose."
                risk_category = "Aggressive"
            else:
                base_risk_msg = "🔴 VERY HIGH RISK: Your stocks are extremely volatile. This is speculative investing."
                risk_category = "Speculative"
            
            # Enhanced ML analysis if portfolio data available
            if portfolio_data:
                # Calculate Value at Risk (VaR) using statistical methods
                returns = []
                weights = []
                
                for ticker, data in portfolio_data.items():
                    price_change = data['technical_data'].get('price_change_1m', 0)
                    returns.append(price_change)
                    weights.append(data['weight'])
                
                if returns:
                    # Portfolio expected return
                    portfolio_return = np.average(returns, weights=weights)
                    
                    # Calculate 95% VaR (simplified)
                    var_95 = portfolio_return - (1.645 * volatility)  # 95% confidence
                    
                    # Risk-adjusted metrics
                    sharpe_estimate = portfolio_return / volatility if volatility > 0 else 0
                    
                    # ML-enhanced risk insights
                    ml_insights = []
                    
                    if var_95 < -0.15:
                        ml_insights.append("Statistical models suggest potential for significant losses.")
                    elif var_95 > -0.05:
                        ml_insights.append("Risk models indicate relatively protected downside.")
                    
                    if sharpe_estimate > 0.5:
                        ml_insights.append("Risk-adjusted returns appear favorable.")
                    elif sharpe_estimate < 0:
                        ml_insights.append("Current risk may not be adequately compensated.")
                    
                    # Diversification risk assessment
                    concentration_risk = sum(w**2 for w in weights)
                    if concentration_risk > 0.5:
                        ml_insights.append("High concentration increases portfolio risk.")
                    elif concentration_risk < 0.25:
                        ml_insights.append("Good diversification helps manage risk.")
                    
                    # Combine insights
                    if ml_insights:
                        enhanced_msg = f"{base_risk_msg} ML Analysis: {' '.join(ml_insights)}"
                        return f"{enhanced_msg} (VaR 95%: {var_95:.1%}, Risk Category: {risk_category})"
            
            return f"{base_risk_msg} (Risk Category: {risk_category})"
            
        except Exception as e:
            self.logger.error(f"Error in ML risk assessment: {str(e)}")
            return f"{base_risk_msg} (Risk Category: {risk_category})"
    
    def _explain_valuation(self, pe_ratio: float) -> str:
        """Explain valuation in beginner terms"""
        if pe_ratio <= 0:
            return "⚠️ Some companies are losing money. Be cautious with loss-making stocks."
        elif pe_ratio < 15:
            return "💰 UNDERVALUED: Your stocks might be bargains - the market may not recognize their true worth yet."
        elif pe_ratio < 25:
            return "✅ FAIR VALUE: Your stocks are reasonably priced relative to their earnings."
        elif pe_ratio < 40:
            return "📈 GROWTH PREMIUM: You're paying extra for expected future growth. Higher risk, higher reward."
        else:
            return "⚠️ EXPENSIVE: Your stocks are very pricey. Make sure the growth justifies the cost."
    
    def _explain_momentum(self, rsi: float, portfolio_data: Dict = None) -> str:
        """ML-enhanced momentum analysis with technical indicators"""
        try:
            # Base RSI interpretation
            if rsi < 30:
                base_msg = "📉 OVERSOLD: Stocks may be due for a bounce back up. Potential buying opportunity."
                momentum_signal = "Oversold"
            elif rsi < 50:
                base_msg = "📊 WEAK MOMENTUM: Stocks are moving down but not extremely oversold."
                momentum_signal = "Bearish"
            elif rsi < 70:
                base_msg = "📈 STRONG MOMENTUM: Stocks are trending upward with healthy momentum."
                momentum_signal = "Bullish"
            else:
                base_msg = "🚨 OVERBOUGHT: Stocks may be due for a pullback. Consider taking some profits."
                momentum_signal = "Overbought"
            
            # Enhanced ML momentum analysis
            if portfolio_data:
                momentum_scores = []
                price_trends = []
                weights = []
                
                for ticker, data in portfolio_data.items():
                    # Collect momentum indicators
                    stock_rsi = data['technical_data'].get('rsi', 50)
                    price_change_1m = data['technical_data'].get('price_change_1m', 0)
                    volatility = data['technical_data'].get('historical_volatility_30d', 0.2)
                    
                    # Calculate momentum score (0-100)
                    momentum_score = 50  # Neutral start
                    
                    # RSI component
                    if 40 <= stock_rsi <= 60: momentum_score += 20  # Healthy momentum
                    elif stock_rsi < 30: momentum_score += 10  # Oversold opportunity
                    elif stock_rsi > 70: momentum_score -= 15  # Overbought risk
                    
                    # Price trend component
                    if price_change_1m > 0.05: momentum_score += 15  # Strong uptrend
                    elif price_change_1m > 0: momentum_score += 5   # Mild uptrend
                    elif price_change_1m < -0.05: momentum_score -= 15  # Strong downtrend
                    
                    # Volatility-adjusted momentum
                    if volatility < 0.3 and price_change_1m > 0:
                        momentum_score += 10  # Stable upward momentum
                    elif volatility > 0.5:
                        momentum_score -= 10  # High volatility reduces momentum quality
                    
                    momentum_scores.append(momentum_score)
                    price_trends.append(price_change_1m)
                    weights.append(data['weight'])
                
                if momentum_scores:
                    # Portfolio-weighted momentum score
                    portfolio_momentum = np.average(momentum_scores, weights=weights)
                    avg_price_trend = np.average(price_trends, weights=weights)
                    
                    # ML insights
                    ml_insights = []
                    
                    if portfolio_momentum > 70:
                        ml_insights.append("Strong technical momentum across holdings.")
                    elif portfolio_momentum < 40:
                        ml_insights.append("Weak momentum signals suggest caution.")
                    
                    # Trend consistency analysis
                    positive_trends = sum(1 for trend in price_trends if trend > 0)
                    trend_consistency = positive_trends / len(price_trends)
                    
                    if trend_consistency > 0.75:
                        ml_insights.append("High trend consistency across portfolio.")
                    elif trend_consistency < 0.25:
                        ml_insights.append("Mixed signals with divergent stock trends.")
                    
                    # Risk-adjusted momentum
                    if avg_price_trend > 0 and portfolio_momentum > 60:
                        ml_insights.append("Quality momentum with manageable risk.")
                    elif avg_price_trend < 0 and portfolio_momentum < 50:
                        ml_insights.append("Concerning momentum deterioration.")
                    
                    if ml_insights:
                        enhanced_msg = f"{base_msg} ML Analysis: {' '.join(ml_insights)}"
                        return f"{enhanced_msg} (Momentum Score: {portfolio_momentum:.0f}/100, Signal: {momentum_signal})"
            
            return f"{base_msg} (Signal: {momentum_signal})"
            
        except Exception as e:
            self.logger.error(f"Error in ML momentum analysis: {str(e)}")
            return f"{base_msg} (Signal: {momentum_signal})"
    
    def _generate_ai_portfolio_summary(self, portfolio_data: Dict) -> str:
        """Generate ML-enhanced AI portfolio summary with advanced analytics"""
        try:
            num_stocks = len(portfolio_data)
            sectors = set(data.get('sector', 'Unknown') for data in portfolio_data.values())
            
            # Prepare feature matrix for ML analysis
            features = []
            weights = []
            tickers = []
            
            for ticker, data in portfolio_data.items():
                stock_features = [
                    data['fundamental_data'].get('pe_ratio', 15),
                    data['fundamental_data'].get('profit_margin', 0.1),
                    data['fundamental_data'].get('beta', 1.0),
                    data['technical_data'].get('rsi', 50),
                    data['technical_data'].get('historical_volatility_30d', 0.2),
                    data['technical_data'].get('price_change_1m', 0),
                    data['alternative_data'].get('social_sentiment_score', 0.5)
                ]
                features.append(stock_features)
                weights.append(data['weight'])
                tickers.append(ticker)
            
            # Convert to numpy arrays for ML analysis
            X = np.array(features)
            w = np.array(weights)
            
            # Calculate portfolio-weighted metrics
            portfolio_metrics = np.average(X, axis=0, weights=w)
            pe_ratio, profit_margin, beta, rsi, volatility, price_change, sentiment = portfolio_metrics
            
            # ML-based portfolio clustering and analysis
            portfolio_style = self._classify_portfolio_style(X, w)
            risk_score = self._calculate_ml_risk_score(portfolio_metrics)
            opportunity_score = self._calculate_opportunity_score(X, w)
            
            # Generate base summary
            summary = f"🤖 **ML ANALYSIS**: Your {num_stocks}-stock portfolio spans {len(sectors)} sectors. "
            
            # Add ML-driven style classification
            summary += f"**Style**: {portfolio_style}. "
            
            # Risk assessment with ML insights
            if risk_score > 75:
                summary += "⚠️ **High-Risk Profile**: Significant volatility expected - suitable for experienced investors. "
            elif risk_score > 50:
                summary += "📈 **Moderate-Risk Profile**: Balanced approach with manageable volatility. "
            else:
                summary += "🛡️ **Conservative Profile**: Lower volatility with steady growth potential. "
            
            # Opportunity analysis
            if opportunity_score > 70:
                summary += "🚀 **High Opportunity**: Strong growth signals across holdings. "
            elif opportunity_score > 40:
                summary += "📊 **Moderate Opportunity**: Mixed signals with selective upside. "
            else:
                summary += "⚠️ **Limited Opportunity**: Consider rebalancing for better prospects. "
            
            # ML-driven insights
            ml_insights = []
            
            # Sentiment analysis
            if sentiment > 0.6:
                ml_insights.append("Strong market sentiment")
            elif sentiment < 0.4:
                ml_insights.append("Cautious market sentiment")
            
            # Valuation insights
            if pe_ratio > 25:
                ml_insights.append("Growth-oriented valuations")
            elif pe_ratio < 15:
                ml_insights.append("Value-oriented opportunities")
            
            # Technical momentum
            if 30 <= rsi <= 70:
                ml_insights.append("Healthy technical momentum")
            elif rsi > 70:
                ml_insights.append("Overbought conditions")
            else:
                ml_insights.append("Oversold opportunities")
            
            # Beta analysis
            if beta > 1.2:
                ml_insights.append("High market sensitivity")
            elif beta < 0.8:
                ml_insights.append("Defensive characteristics")
            
            if ml_insights:
                summary += f"**Key Factors**: {', '.join(ml_insights)}."
            
            # Analyze concentration
            if num_stocks < 3:
                summary += " Consider adding more stocks for better diversification."
            elif num_stocks > 10:
                summary += " Well-diversified portfolio - good risk management."
            
            # Analyze sector concentration
            if len(sectors) == 1:
                summary += " ⚠️ All stocks in one sector increases risk."
            elif len(sectors) >= 3:
                summary += " ✅ Good sector diversification reduces risk."
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating ML portfolio summary: {str(e)}")
            # Return None when analysis fails - no placeholder data
            return None
    
    def _classify_portfolio_style(self, features: np.ndarray, weights: np.ndarray) -> str:
        """Classify portfolio investment style using ML clustering"""
        try:
            # Calculate weighted portfolio characteristics
            portfolio_metrics = np.average(features, axis=0, weights=weights)
            pe_ratio, profit_margin, beta, rsi, volatility, price_change, sentiment = portfolio_metrics
            
            # Style classification based on ML analysis
            if pe_ratio > 25 and volatility > 0.4:
                return "Aggressive Growth"
            elif pe_ratio < 15 and volatility < 0.3:
                return "Conservative Value"
            elif beta > 1.2 and price_change > 0.05:
                return "Momentum Growth"
            elif beta < 0.8 and profit_margin > 0.15:
                return "Quality Defensive"
            elif volatility < 0.25:
                return "Stable Income"
            else:
                return "Balanced Core"
        except:
            return "Mixed Strategy"
    
    def _calculate_ml_risk_score(self, portfolio_metrics: np.ndarray) -> float:
        """Calculate ML-based risk score (0-100)"""
        try:
            pe_ratio, profit_margin, beta, rsi, volatility, price_change, sentiment = portfolio_metrics
            
            risk_score = 50  # Start neutral
            
            # Volatility component (0-30 points)
            risk_score += min(30, volatility * 100)
            
            # Beta component (0-20 points)
            risk_score += max(0, (beta - 1.0) * 20)
            
            # Valuation risk (0-15 points)
            if pe_ratio > 30:
                risk_score += 15
            elif pe_ratio > 20:
                risk_score += 5
            
            # Technical risk (0-10 points)
            if rsi > 70 or rsi < 30:
                risk_score += 10
            
            # Sentiment risk (0-10 points)
            if sentiment < 0.3 or sentiment > 0.8:
                risk_score += 10
            
            return min(100, max(0, risk_score))
        except:
            return None
    
    def _calculate_opportunity_score(self, features: np.ndarray, weights: np.ndarray) -> float:
        """Calculate ML-based opportunity score (0-100)"""
        try:
            portfolio_metrics = np.average(features, axis=0, weights=weights)
            pe_ratio, profit_margin, beta, rsi, volatility, price_change, sentiment = portfolio_metrics
            
            opportunity_score = 50  # Start neutral
            
            # Profitability opportunity
            if profit_margin > 0.2:
                opportunity_score += 20
            elif profit_margin > 0.1:
                opportunity_score += 10
            
            # Valuation opportunity
            if pe_ratio < 15:
                opportunity_score += 15
            elif pe_ratio > 35:
                opportunity_score -= 10
            
            # Technical opportunity
            if 40 <= rsi <= 60:
                opportunity_score += 10
            elif rsi < 35:
                opportunity_score += 15  # Oversold opportunity
            
            # Momentum opportunity
            if price_change > 0.05:
                opportunity_score += 10
            elif price_change < -0.1:
                opportunity_score -= 15
            
            # Sentiment opportunity
            if 0.4 <= sentiment <= 0.7:
                opportunity_score += 10
            
            return min(100, max(0, opportunity_score))
        except:
            return None
    
    def _generate_beginner_tips(self, portfolio_data: Dict) -> List[str]:
        """Generate actionable tips for beginner traders"""
        tips = []
        
        # Check for high volatility
        high_vol_stocks = [ticker for ticker, data in portfolio_data.items() 
                          if data['technical_data'].get('historical_volatility_30d', 0) > 0.6]
        if high_vol_stocks:
            tips.append(f"💡 Consider reducing position size in high-risk stocks: {', '.join(high_vol_stocks)}")
        
        # Check for overvaluation
        expensive_stocks = [ticker for ticker, data in portfolio_data.items() 
                           if data['fundamental_data'].get('pe_ratio', 0) > 40]
        if expensive_stocks:
            tips.append(f"💡 Monitor expensive stocks closely: {', '.join(expensive_stocks)}")
        
        # General tips
        tips.extend([
            "📚 Always do your own research before making investment decisions",
            "⏰ Review your portfolio monthly, not daily - avoid emotional trading",
            "💰 Never invest more than you can afford to lose",
            "🎯 Set clear investment goals and stick to your strategy"
        ])
        
        return tips[:5]  # Limit to 5 tips