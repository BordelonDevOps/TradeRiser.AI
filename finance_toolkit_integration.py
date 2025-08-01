#!/usr/bin/env python3
"""
FinanceToolkit Integration Module
Core financial analysis engine using FinanceToolkit
Provides 100+ financial ratios, indicators, and performance measurements
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from financetoolkit import Toolkit
except ImportError:
    logging.warning("FinanceToolkit not installed. Install with: pip install financetoolkit")
    Toolkit = None

class FinanceToolkitAnalyzer:
    """
    Advanced financial analysis using FinanceToolkit
    Provides comprehensive financial ratios, performance metrics, and analysis
    """
    
    def __init__(self, api_key: Optional[str] = None, start_date: str = "2020-01-01"):
        """
        Initialize FinanceToolkit Analyzer
        
        Args:
            api_key: Financial Modeling Prep API key (optional, uses free tier if None)
            start_date: Start date for historical data analysis
        """
        self.api_key = api_key
        self.start_date = start_date
        self.logger = logging.getLogger(__name__)
        
        if Toolkit is None:
            self.logger.error("FinanceToolkit not available. Please install: pip install financetoolkit")
            self.toolkit = None
        else:
            try:
                # Initialize toolkit with or without API key
                if api_key:
                    self.toolkit = Toolkit(
                        tickers=[],  # Will be set per analysis
                        api_key=api_key,
                        start_date=start_date
                    )
                else:
                    # Use free tier (Yahoo Finance fallback)
                    self.toolkit = Toolkit(
                        tickers=[],
                        start_date=start_date
                    )
                self.logger.info("FinanceToolkit initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize FinanceToolkit: {e}")
                self.toolkit = None
    
    def analyze_company(self, ticker: str, include_ratios: bool = True, 
                       include_performance: bool = True) -> Dict[str, Any]:
        """
        Comprehensive company analysis using FinanceToolkit
        
        Args:
            ticker: Stock ticker symbol
            include_ratios: Include financial ratios analysis
            include_performance: Include performance metrics
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        if not self.toolkit:
            return {
                'ticker': ticker.upper(),
                'analysis_date': datetime.now().isoformat(),
                'data_source': 'Error',
                'success': False,
                'error': 'FinanceToolkit not available - no analysis possible',
                'message': 'No analysis available. FinanceToolkit required for comprehensive analysis.'
            }
        
        try:
            # Create toolkit instance for specific ticker
            company_toolkit = Toolkit(
                tickers=[ticker.upper()],
                api_key=self.api_key,
                start_date=self.start_date
            )
            
            analysis_result = {
                'ticker': ticker.upper(),
                'analysis_date': datetime.now().isoformat(),
                'data_source': 'FinanceToolkit',
                'success': True
            }
            
            # Get basic company information
            try:
                profile = company_toolkit.get_profile()
                if not profile.empty:
                    analysis_result['company_profile'] = {
                        'name': profile.get('companyName', {}).get(ticker.upper(), 'N/A'),
                        'sector': profile.get('sector', {}).get(ticker.upper(), 'N/A'),
                        'industry': profile.get('industry', {}).get(ticker.upper(), 'N/A'),
                        'market_cap': profile.get('mktCap', {}).get(ticker.upper(), 0),
                        'description': profile.get('description', {}).get(ticker.upper(), 'N/A')[:200] + '...'
                    }
            except Exception as e:
                self.logger.warning(f"Could not fetch company profile for {ticker}: {e}")
                analysis_result['company_profile'] = {'error': str(e)}
            
            # Financial Ratios Analysis
            if include_ratios:
                analysis_result['financial_ratios'] = self._get_financial_ratios(company_toolkit, ticker)
            
            # Performance Metrics
            if include_performance:
                analysis_result['performance_metrics'] = self._get_performance_metrics(company_toolkit, ticker)
            
            # Risk Metrics
            analysis_result['risk_metrics'] = self._get_risk_metrics(company_toolkit, ticker)
            
            # Valuation Metrics
            analysis_result['valuation_metrics'] = self._get_valuation_metrics(company_toolkit, ticker)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error analyzing company {ticker}: {e}")
            return {
                'ticker': ticker.upper(),
                'analysis_date': datetime.now().isoformat(),
                'data_source': 'Error',
                'success': False,
                'error': str(e),
                'message': 'Analysis failed. FinanceToolkit error occurred.'
            }
    
    def _get_financial_ratios(self, toolkit, ticker: str) -> Dict[str, Any]:
        """
        Extract comprehensive financial ratios
        """
        ratios = {}
        
        try:
            # Liquidity Ratios
            liquidity = toolkit.ratios.collect_liquidity_ratios()
            if not liquidity.empty and ticker.upper() in liquidity.columns:
                latest_liquidity = liquidity[ticker.upper()].dropna().tail(1)
                if not latest_liquidity.empty:
                    ratios['liquidity'] = {
                        'current_ratio': float(latest_liquidity.get('Current Ratio', 0)),
                        'quick_ratio': float(latest_liquidity.get('Quick Ratio', 0)),
                        'cash_ratio': float(latest_liquidity.get('Cash Ratio', 0))
                    }
            
            # Profitability Ratios
            profitability = toolkit.ratios.collect_profitability_ratios()
            if not profitability.empty and ticker.upper() in profitability.columns:
                latest_profit = profitability[ticker.upper()].dropna().tail(1)
                if not latest_profit.empty:
                    ratios['profitability'] = {
                        'gross_margin': float(latest_profit.get('Gross Margin', 0)),
                        'operating_margin': float(latest_profit.get('Operating Margin', 0)),
                        'net_margin': float(latest_profit.get('Net Margin', 0)),
                        'return_on_equity': float(latest_profit.get('Return on Equity', 0)),
                        'return_on_assets': float(latest_profit.get('Return on Assets', 0))
                    }
            
            # Leverage Ratios
            leverage = toolkit.ratios.collect_leverage_ratios()
            if not leverage.empty and ticker.upper() in leverage.columns:
                latest_leverage = leverage[ticker.upper()].dropna().tail(1)
                if not latest_leverage.empty:
                    ratios['leverage'] = {
                        'debt_to_equity': float(latest_leverage.get('Debt to Equity Ratio', 0)),
                        'debt_to_assets': float(latest_leverage.get('Debt to Assets Ratio', 0)),
                        'interest_coverage': float(latest_leverage.get('Interest Coverage Ratio', 0))
                    }
            
            # Efficiency Ratios
            efficiency = toolkit.ratios.collect_efficiency_ratios()
            if not efficiency.empty and ticker.upper() in efficiency.columns:
                latest_efficiency = efficiency[ticker.upper()].dropna().tail(1)
                if not latest_efficiency.empty:
                    ratios['efficiency'] = {
                        'asset_turnover': float(latest_efficiency.get('Asset Turnover Ratio', 0)),
                        'inventory_turnover': float(latest_efficiency.get('Inventory Turnover Ratio', 0)),
                        'receivables_turnover': float(latest_efficiency.get('Receivables Turnover Ratio', 0))
                    }
                    
        except Exception as e:
            self.logger.warning(f"Error calculating financial ratios for {ticker}: {e}")
            ratios['error'] = str(e)
        
        return ratios
    
    def _get_performance_metrics(self, toolkit, ticker: str) -> Dict[str, Any]:
        """
        Calculate performance metrics
        """
        performance = {}
        
        try:
            # Get historical prices for performance calculation
            prices = toolkit.get_historical_data()
            if not prices.empty and ticker.upper() in prices.columns:
                ticker_prices = prices[ticker.upper()].dropna()
                
                if len(ticker_prices) > 1:
                    # Calculate returns
                    returns = ticker_prices.pct_change().dropna()
                    
                    performance['returns'] = {
                        'total_return': float((ticker_prices.iloc[-1] / ticker_prices.iloc[0] - 1) * 100),
                        'annualized_return': float(returns.mean() * 252 * 100),
                        'volatility': float(returns.std() * np.sqrt(252) * 100),
                        'sharpe_ratio': float((returns.mean() * 252) / (returns.std() * np.sqrt(252))) if returns.std() > 0 else 0
                    }
                    
                    # Calculate maximum drawdown
                    cumulative = (1 + returns).cumprod()
                    rolling_max = cumulative.expanding().max()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    performance['risk_metrics'] = {
                        'max_drawdown': float(drawdown.min() * 100),
                        'current_drawdown': float(drawdown.iloc[-1] * 100)
                    }
                    
        except Exception as e:
            self.logger.warning(f"Error calculating performance metrics for {ticker}: {e}")
            performance['error'] = str(e)
        
        return performance
    
    def _get_risk_metrics(self, toolkit, ticker: str) -> Dict[str, Any]:
        """
        Calculate risk metrics
        """
        risk_metrics = {}
        
        try:
            # Get risk ratios if available
            risk = toolkit.ratios.collect_risk_ratios()
            if not risk.empty and ticker.upper() in risk.columns:
                latest_risk = risk[ticker.upper()].dropna().tail(1)
                if not latest_risk.empty:
                    risk_metrics = {
                        'beta': float(latest_risk.get('Beta', 1.0)),
                        'value_at_risk': float(latest_risk.get('Value at Risk', 0)),
                        'conditional_var': float(latest_risk.get('Conditional Value at Risk', 0))
                    }
                    
        except Exception as e:
            self.logger.warning(f"Error calculating risk metrics for {ticker}: {e}")
            risk_metrics['error'] = str(e)
        
        return risk_metrics
    
    def _get_valuation_metrics(self, toolkit, ticker: str) -> Dict[str, Any]:
        """
        Calculate valuation metrics
        """
        valuation = {}
        
        try:
            # Get valuation ratios
            val_ratios = toolkit.ratios.collect_valuation_ratios()
            if not val_ratios.empty and ticker.upper() in val_ratios.columns:
                latest_val = val_ratios[ticker.upper()].dropna().tail(1)
                if not latest_val.empty:
                    valuation = {
                        'pe_ratio': float(latest_val.get('Price to Earnings Ratio', 0)),
                        'pb_ratio': float(latest_val.get('Price to Book Ratio', 0)),
                        'ps_ratio': float(latest_val.get('Price to Sales Ratio', 0)),
                        'peg_ratio': float(latest_val.get('Price to Earnings Growth Ratio', 0)),
                        'ev_ebitda': float(latest_val.get('Enterprise Value to EBITDA Ratio', 0))
                    }
                    
        except Exception as e:
            self.logger.warning(f"Error calculating valuation metrics for {ticker}: {e}")
            valuation['error'] = str(e)
        
        return valuation
    
    def analyze_portfolio(self, tickers: List[str], weights: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Analyze a portfolio of stocks using FinanceToolkit
        
        Args:
            tickers: List of stock ticker symbols
            weights: Portfolio weights (equal weight if None)
            
        Returns:
            Portfolio analysis results
        """
        if not self.toolkit:
            return {
                'tickers': [t.upper() for t in tickers],
                'analysis_date': datetime.now().isoformat(),
                'data_source': 'Error',
                'success': False,
                'error': 'FinanceToolkit not available - no portfolio analysis possible',
                'message': 'No portfolio analysis available. FinanceToolkit required for comprehensive portfolio analysis.'
            }
        
        try:
            # Clean and validate tickers
            clean_tickers = [t.upper().strip() for t in tickers if t.strip()]
            
            if not clean_tickers:
                return {'error': 'No valid tickers provided'}
            
            # Set equal weights if not provided
            if weights is None:
                weights = [1.0 / len(clean_tickers)] * len(clean_tickers)
            elif len(weights) != len(clean_tickers):
                return {'error': 'Number of weights must match number of tickers'}
            
            # Create portfolio toolkit
            portfolio_toolkit = Toolkit(
                tickers=clean_tickers,
                api_key=self.api_key,
                start_date=self.start_date
            )
            
            portfolio_analysis = {
                'tickers': clean_tickers,
                'weights': weights,
                'analysis_date': datetime.now().isoformat(),
                'data_source': 'FinanceToolkit',
                'success': True
            }
            
            # Portfolio performance metrics
            try:
                prices = portfolio_toolkit.get_historical_data()
                if not prices.empty:
                    returns = prices.pct_change().dropna()
                    
                    # Calculate portfolio returns
                    portfolio_returns = (returns * weights).sum(axis=1)
                    
                    portfolio_analysis['performance'] = {
                        'total_return': float((portfolio_returns + 1).prod() - 1) * 100,
                        'annualized_return': float(portfolio_returns.mean() * 252 * 100),
                        'volatility': float(portfolio_returns.std() * np.sqrt(252) * 100),
                        'sharpe_ratio': float((portfolio_returns.mean() * 252) / (portfolio_returns.std() * np.sqrt(252))) if portfolio_returns.std() > 0 else 0
                    }
                    
                    # Risk metrics
                    cumulative = (1 + portfolio_returns).cumprod()
                    rolling_max = cumulative.expanding().max()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    
                    portfolio_analysis['risk'] = {
                        'max_drawdown': float(drawdown.min() * 100),
                        'current_drawdown': float(drawdown.iloc[-1] * 100),
                        'var_95': float(np.percentile(portfolio_returns, 5) * 100),
                        'cvar_95': float(portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, 5)].mean() * 100)
                    }
                    
            except Exception as e:
                self.logger.warning(f"Error calculating portfolio performance: {e}")
                portfolio_analysis['performance_error'] = str(e)
            
            # Individual stock analysis
            portfolio_analysis['individual_analysis'] = {}
            for ticker in clean_tickers:
                try:
                    stock_analysis = self.analyze_company(ticker, include_ratios=False, include_performance=True)
                    portfolio_analysis['individual_analysis'][ticker] = stock_analysis
                except Exception as e:
                    portfolio_analysis['individual_analysis'][ticker] = {'error': str(e)}
            
            return portfolio_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing portfolio: {e}")
            return {
                'tickers': [t.upper() for t in tickers],
                'analysis_date': datetime.now().isoformat(),
                'data_source': 'Error',
                'success': False,
                'error': str(e),
                'message': 'Portfolio analysis failed. FinanceToolkit error occurred.'
            }
    

    
    def get_available_metrics(self) -> List[str]:
        """
        Get list of available financial metrics
        """
        if not self.toolkit:
            return ['FinanceToolkit not available - no metrics available']
        
        return [
            'Liquidity Ratios', 'Profitability Ratios', 'Leverage Ratios',
            'Efficiency Ratios', 'Valuation Ratios', 'Risk Metrics',
            'Performance Metrics', 'Portfolio Analysis'
        ]

# Global instance for easy access
finance_analyzer = None

def get_finance_analyzer(api_key: Optional[str] = None) -> FinanceToolkitAnalyzer:
    """
    Get or create global FinanceToolkit analyzer instance
    """
    global finance_analyzer
    if finance_analyzer is None:
        finance_analyzer = FinanceToolkitAnalyzer(api_key=api_key)
    return finance_analyzer

if __name__ == "__main__":
    # Test the integration
    analyzer = FinanceToolkitAnalyzer()
    
    # Test single stock analysis
    print("Testing AAPL analysis...")
    result = analyzer.analyze_company("AAPL")
    print(f"Analysis result: {result.get('success', False)}")
    
    # Test portfolio analysis
    print("\nTesting portfolio analysis...")
    portfolio_result = analyzer.analyze_portfolio(["AAPL", "MSFT", "GOOGL"])
    print(f"Portfolio analysis result: {portfolio_result.get('success', False)}")