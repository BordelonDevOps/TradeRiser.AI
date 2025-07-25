#!/usr/bin/env python3
"""
Test script to verify Yahoo Finance API functionality
"""

import requests
import json
from datetime import datetime

def test_yahoo_finance(ticker):
    """Test Yahoo Finance API for a given ticker"""
    print(f"Testing Yahoo Finance API for {ticker}...")
    
    # Test Yahoo Finance Summary API
    base_url = 'https://query1.finance.yahoo.com/v10/finance/quoteSummary'
    url = f"{base_url}/{ticker}"
    params = {'modules': 'summaryDetail,defaultKeyStatistics,financialData'}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response received successfully!")
            
            # Extract data
            result = data.get('quoteSummary', {}).get('result', [{}])[0]
            summary = result.get('summaryDetail', {})
            key_stats = result.get('defaultKeyStatistics', {})
            financial = result.get('financialData', {})
            
            # Parse key metrics
            current_price = summary.get('regularMarketPrice', {}).get('raw', 0)
            pe_ratio = summary.get('trailingPE', {}).get('raw', 0)
            market_cap = summary.get('marketCap', {}).get('raw', 0)
            
            print(f"Current Price: ${current_price}")
            print(f"P/E Ratio: {pe_ratio}")
            print(f"Market Cap: ${market_cap:,.0f}" if market_cap else "Market Cap: N/A")
            
            return True
        else:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return False

def test_yahoo_chart(ticker):
    """Test Yahoo Finance Chart API for price data"""
    print(f"\nTesting Yahoo Finance Chart API for {ticker}...")
    
    base_url = 'https://query1.finance.yahoo.com/v8/finance/chart'
    url = f"{base_url}/{ticker}"
    params = {'interval': '1d', 'range': '5d'}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            chart_data = data.get('chart', {}).get('result', [{}])[0]
            
            # Get current price
            meta = chart_data.get('meta', {})
            current_price = meta.get('regularMarketPrice', 0)
            
            print(f"Current Price from Chart API: ${current_price}")
            print(f"Currency: {meta.get('currency', 'USD')}")
            print(f"Exchange: {meta.get('exchangeName', 'Unknown')}")
            
            return True
        else:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    # Test with popular stocks
    test_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    
    print("=" * 50)
    print("Yahoo Finance API Test")
    print("=" * 50)
    
    for ticker in test_tickers:
        print(f"\n{'='*20} {ticker} {'='*20}")
        
        # Test both APIs
        summary_success = test_yahoo_finance(ticker)
        chart_success = test_yahoo_chart(ticker)
        
        if summary_success and chart_success:
            print(f"✅ {ticker}: All tests passed")
        else:
            print(f"❌ {ticker}: Some tests failed")
    
    print("\n" + "="*50)
    print("Test completed!")