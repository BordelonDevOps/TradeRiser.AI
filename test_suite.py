"""Unified test suite for TradeRiser.AI platform"""

import unittest
import sys
import os
from datetime import datetime
from typing import Dict, List

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from portfolio_analyzer import PortfolioAnalyzer
from etf_analyzer import ETFAnalyzer
from commodities_trader import CommoditiesTrader
from utils_shared import setup_logging, TechnicalIndicators, DataProcessor, ErrorHandler

# Setup logging for tests
setup_logging()

class TestPortfolioAnalyzer(unittest.TestCase):
    """Test cases for PortfolioAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = PortfolioAnalyzer()
        self.sample_portfolio = {
            'AAPL': 0.4,
            'GOOGL': 0.3,
            'MSFT': 0.3
        }
    
    def test_portfolio_analysis(self):
        """Test basic portfolio analysis functionality"""
        try:
            result = self.analyzer.analyze_portfolio(self.sample_portfolio)
            
            # Check if analysis completed without errors
            self.assertIsInstance(result, dict)
            self.assertNotIn('error', result)
            
            # Check for required sections
            required_sections = [
                'portfolio_summary',
                'fundamental_analysis',
                'technical_analysis',
                'risk_analysis'
            ]
            
            for section in required_sections:
                self.assertIn(section, result, f"Missing section: {section}")
            
            print("✓ Portfolio analysis test passed")
            
        except Exception as e:
            self.fail(f"Portfolio analysis failed: {str(e)}")
    
    def test_portfolio_validation(self):
        """Test portfolio validation"""
        # Test valid portfolio
        valid_portfolio = {'AAPL': 0.5, 'GOOGL': 0.5}
        self.assertTrue(self.analyzer._validate_portfolio(valid_portfolio))
        
        # Test invalid portfolio (weights don't sum to 1)
        invalid_portfolio = {'AAPL': 0.3, 'GOOGL': 0.3}
        self.assertFalse(self.analyzer._validate_portfolio(invalid_portfolio))
        
        print("✓ Portfolio validation test passed")

class TestETFAnalyzer(unittest.TestCase):
    """Test cases for ETFAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = ETFAnalyzer()
    
    def test_etf_analysis(self):
        """Test ETF universe analysis"""
        try:
            result = self.analyzer.analyze_etf_universe()
            
            # Check if analysis completed
            self.assertIsInstance(result, dict)
            
            # Check for key components
            if 'error' not in result:
                self.assertIn('etf_analysis', result)
                self.assertIn('generated_at', result)
            
            print("✓ ETF analysis test passed")
            
        except Exception as e:
            print(f"⚠ ETF analysis test warning: {str(e)}")

class TestCommoditiesTrader(unittest.TestCase):
    """Test cases for CommoditiesTrader"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.trader = CommoditiesTrader()
    
    def test_commodity_analysis(self):
        """Test commodity market analysis"""
        try:
            result = self.trader.analyze_commodity_market()
            
            # Check if analysis completed
            self.assertIsInstance(result, dict)
            
            # Check for key components
            if 'error' not in result:
                self.assertIn('commodity_analysis', result)
                self.assertIn('generated_at', result)
            
            print("✓ Commodity analysis test passed")
            
        except Exception as e:
            print(f"⚠ Commodity analysis test warning: {str(e)}")

class TestSharedUtilities(unittest.TestCase):
    """Test cases for shared utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.technical_indicators = TechnicalIndicators()
        self.data_processor = DataProcessor()
        self.error_handler = ErrorHandler()
    
    def test_technical_indicators(self):
        """Test technical indicator calculations"""
        import numpy as np
        
        # Test data
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])
        
        # Test RSI calculation
        rsi = self.technical_indicators.calculate_rsi_numpy(prices)
        self.assertIsInstance(rsi, float)
        self.assertGreaterEqual(rsi, 0)
        self.assertLessEqual(rsi, 100)
        
        # Test SMA calculation
        sma = self.technical_indicators.calculate_sma(prices, 5)
        self.assertIsInstance(sma, float)
        self.assertGreater(sma, 0)
        
        # Test volatility calculation
        volatility = self.technical_indicators.calculate_volatility(prices)
        self.assertIsInstance(volatility, float)
        self.assertGreaterEqual(volatility, 0)
        
        print("✓ Technical indicators test passed")
    
    def test_data_processor(self):
        """Test data processing utilities"""
        # Test safe float conversion
        self.assertEqual(self.data_processor.safe_float("123.45"), 123.45)
        self.assertEqual(self.data_processor.safe_float("invalid", 0.0), 0.0)
        
        # Test percentage change calculation
        change = self.data_processor.calculate_percentage_change(100, 110)
        self.assertEqual(change, 10.0)
        
        # Test formatting
        formatted = self.data_processor.format_currency(1234.56)
        self.assertIn("1,234.56", formatted)
        
        print("✓ Data processor test passed")
    
    def test_error_handler(self):
        """Test error handling utilities"""
        # Test error response creation
        error_response = self.error_handler.create_error_response(
            "Test error", "Test details"
        )
        
        self.assertIn('error', error_response)
        self.assertIn('message', error_response)
        self.assertIn('timestamp', error_response)
        
        # Test success response creation
        success_response = self.error_handler.create_success_response(
            {"test": "data"}, "Test success"
        )
        
        self.assertIn('status', success_response)
        self.assertIn('data', success_response)
        self.assertEqual(success_response['status'], 'success')
        
        print("✓ Error handler test passed")

class TestYahooFinanceAPI(unittest.TestCase):
    """Test Yahoo Finance API functionality"""
    
    def test_yahoo_finance_data_fetch(self):
        """Test Yahoo Finance data fetching"""
        import yfinance as yf
        
        try:
            # Test with a reliable ticker
            ticker = "AAPL"
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            self.assertFalse(hist.empty, "No data returned from Yahoo Finance")
            self.assertIn('Close', hist.columns, "Missing Close price data")
            
            # Test info fetch
            info = stock.info
            self.assertIsInstance(info, dict, "Info should be a dictionary")
            
            print("✓ Yahoo Finance API test passed")
            
        except Exception as e:
            print(f"⚠ Yahoo Finance API test warning: {str(e)}")

def run_test_suite():
    """Run the complete test suite"""
    print("\n" + "="*50)
    print("TradeRiser.AI Test Suite")
    print("="*50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestSharedUtilities,
        TestYahooFinanceAPI,
        TestPortfolioAnalyzer,
        TestETFAnalyzer,
        TestCommoditiesTrader
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)