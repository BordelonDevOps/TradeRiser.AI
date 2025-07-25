#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from portfolio_analyzer import PortfolioAnalyzer
import json

def test_portfolio_analysis():
    """Test the portfolio analyzer with sample data"""
    print("Testing Portfolio Analyzer...")
    
    # Initialize analyzer
    analyzer = PortfolioAnalyzer()
    
    # Test data - holdings should be a dictionary with ticker as key and weight as value
    holdings = {
        'AAPL': 0.4,
        'GOOGL': 0.3,
        'MSFT': 0.3
    }
    nav = 100000
    
    try:
        print("\nAnalyzing portfolio...")
        result = analyzer.analyze_portfolio(holdings, nav)
        
        print("\n=== Portfolio Analysis Results ===")
        print(json.dumps(result, indent=2, default=str))
        
        if 'error' not in result and 'portfolio_summary' in result:
            print("\n✅ Portfolio analysis completed successfully!")
            portfolio_value = result.get('portfolio_summary', {}).get('total_portfolio_value', 0)
            portfolio_pe = result.get('fundamental_analysis', {}).get('portfolio_weighted_pe', 0)
            portfolio_rsi = result.get('technical_analysis', {}).get('portfolio_rsi', 0)
            print(f"Portfolio Value: ${portfolio_value:,.2f}")
            print(f"Weighted P/E Ratio: {portfolio_pe:.2f}")
            print(f"Portfolio RSI: {portfolio_rsi:.2f}")
        else:
            print("\n❌ Portfolio analysis failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_portfolio_analysis()