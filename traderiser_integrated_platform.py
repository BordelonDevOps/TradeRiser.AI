"""TradeRiser.AI - Integrated Investment Platform
Core Flask application for portfolio, crypto, commodities, ETFs, and backtest analysis with Alpaca trading
"""
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import sys
import os
from typing import Dict, List
import logging
from integrated_finance_database import IntegratedFinanceDatabase
from portfolio_analyzer import PortfolioAnalyzer
from enhanced_crypto_trader import EnhancedCryptoTrader
from backtest_solver import BacktestSolver
from commodities_trader import CommoditiesTrader
from etf_analyzer import ETFAnalyzer
from alpaca_trader import AlpacaTrader
from alpaca_mcp_integration import AlpacaMCPIntegration
from werkzeug.exceptions import BadRequest, TooManyRequests, InternalServerError
from datetime import datetime

app = Flask(__name__)
CORS(app, origins="*")

# Configure logging
logging.basicConfig(
    filename='traderiser.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize systems
finance_database = IntegratedFinanceDatabase()
portfolio_analyzer = PortfolioAnalyzer()
crypto_trader = EnhancedCryptoTrader(finance_database=finance_database)
backtest_solver = BacktestSolver(finance_database=finance_database)
commodities_trader = CommoditiesTrader(finance_database=finance_database)
etf_analyzer = ETFAnalyzer(finance_database=finance_database)
alpaca_trader = AlpacaTrader()
alpaca_mcp = AlpacaMCPIntegration()

@app.route('/')
def index():
    """Main TradeRiser platform interface"""
    logger.info("Rendering main interface")
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradeRiser.AI - Professional Investment Platform</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 40px; color: white; }
        .header h1 { font-size: 3.5rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2rem; opacity: 0.9; }
        .platform-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px; margin-bottom: 40px; }
        .platform-card { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); transition: transform 0.3s ease, box-shadow 0.3s ease; }
        .platform-card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0,0,0,0.15); }
        .platform-card h3 { color: #667eea; font-size: 1.8rem; margin-bottom: 15px; }
        .platform-card p { color: #666; margin-bottom: 20px; line-height: 1.6; }
        .feature-list { list-style: none; margin-bottom: 25px; }
        .feature-list li { padding: 8px 0; color: #555; position: relative; padding-left: 25px; }
        .feature-list li:before { content: "✓"; position: absolute; left: 0; color: #4CAF50; font-weight: bold; }
        .action-button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 25px; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 600; transition: all 0.3s ease; width: 100%; }
        .action-button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        .results-section { background: white; border-radius: 15px; padding: 30px; margin-top: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); display: none; }
        .results-section.active { display: block; }
        .results-header { color: #667eea; font-size: 1.8rem; margin-bottom: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .loading::after { content: ""; display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin-left: 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .analysis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .analysis-card { background: #f8f9fa; border-radius: 10px; padding: 20px; border-left: 4px solid #667eea; }
        .analysis-card h4 { color: #333; margin-bottom: 10px; }
        .metric { display: flex; justify-content: space-between; margin: 8px 0; padding: 5px 0; border-bottom: 1px solid #eee; }
        .metric:last-child { border-bottom: none; }
        .metric-label { color: #666; font-weight: 500; }
        .metric-value { color: #333; font-weight: 600; }
        .positive { color: #4CAF50; }
        .negative { color: #f44336; }
        .neutral { color: #ff9800; }
        .input-section { background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
        .input-group { margin-bottom: 15px; }
        .input-group label { display: block; margin-bottom: 5px; color: #555; font-weight: 500; }
        .input-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 1rem; }
        .footer { text-align: center; margin-top: 50px; color: white; opacity: 0.8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 TradeRiser</h1>
            <p>Professional Investment Analysis Platform</p>
            <p><span class="status-indicator" style="background-color: #4CAF50; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px;"></span>All Systems Online</p>
            
            <!-- SEC Compliance Notice -->
            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <h4 style="color: #856404; margin: 0 0 10px 0;">⚠️ Important Disclaimer</h4>
                <p style="color: #856404; margin: 0; font-size: 14px;">
                    This platform is for informational and educational purposes only. Not investment advice. 
                    Trading involves substantial risk. <a href="/api/compliance/disclaimer" target="_blank">Read full disclaimer</a>
                </p>
            </div>
        </div>
        
        <div class="platform-grid">
            <div class="platform-card">
                <h3>📊 Portfolio Analyzer</h3>
                <p>Advanced portfolio analysis with risk metrics and performance attribution.</p>
                <ul class="feature-list">
                    <li>Risk-return optimization</li>
                    <li>Asset allocation analysis</li>
                    <li>Performance attribution</li>
                    <li>Sector analysis</li>
                </ul>
                <button class="action-button" onclick="showPortfolioAnalyzer()">Analyze Portfolio</button>
            </div>
            <div class="platform-card">
                <h3>₿ Cryptocurrency</h3>
                <p>Advanced cryptocurrency analysis with market sentiment.</p>
                <ul class="feature-list">
                    <li>Major cryptocurrencies</li>
                    <li>Market sentiment</li>
                    <li>Technical analysis</li>
                    <li>AML compliance</li>
                </ul>
                <button class="action-button" onclick="analyzeCrypto()">Analyze Crypto</button>
            </div>
            <div class="platform-card">
                <h3>🔄 Backtest</h3>
                <p>Optimize trade selection with sector and volatility constraints.</p>
                <ul class="feature-list">
                    <li>Optimal trade selection</li>
                    <li>Sector diversification</li>
                    <li>Volatility constraints</li>
                    <li>Return maximization</li>
                </ul>
                <button class="action-button" onclick="runBacktest()">Run Backtest</button>
            </div>
            <div class="platform-card">
                <h3>🥇 Commodities Trading</h3>
                <p>Gold, oil, agriculture, and industrial metals analysis.</p>
                <ul class="feature-list">
                    <li>Precious metals analysis</li>
                    <li>Energy commodities</li>
                    <li>Agricultural futures</li>
                    <li>Market screening</li>
                </ul>
                <button class="action-button" onclick="analyzeCommodities()">Analyze Commodities</button>
            </div>
            <div class="platform-card">
                <h3>📈 ETF Analysis</h3>
                <p>Comprehensive ETF screening and comparison tools.</p>
                <ul class="feature-list">
                    <li>ETF screening</li>
                    <li>Expense ratio analysis</li>
                    <li>Performance comparison</li>
                    <li>Sector allocation</li>
                </ul>
                <button class="action-button" onclick="analyzeETF()">Analyze ETFs</button>
            </div>
            <div class="platform-card">
                <h3>🦙 Alpaca Trading</h3>
                <p>Live trading integration with risk management.</p>
                <ul class="feature-list">
                    <li>Live account data</li>
                    <li>Order management</li>
                    <li>Position tracking</li>
                    <li>Market data</li>
                </ul>
                <button class="action-button" onclick="showAlpacaTrading()">Alpaca Trading</button>
            </div>
        </div>
        
        <div id="results" class="results-section">
            <div class="results-header">Analysis Results</div>
            <div id="results-content">
                <div class="loading">Initializing analysis...</div>
            </div>
        </div>
        
        <div class="footer">
            <p>TradeRiser © 2025 - Professional Investment Analysis Platform</p>
            <p>Real-time market data • Advanced financial modeling • Risk management</p>
        </div>
    </div>
    
    <script>
        function showPortfolioAnalyzer() {
            showResults('Portfolio Analysis');
            document.getElementById('results-content').innerHTML = `
                <div class="input-section">
                    <h4>Portfolio Input</h4>
                    <div class="input-group">
                        <label>Portfolio Tickers (comma-separated):</label>
                        <input type="text" id="portfolio-tickers" placeholder="AAPL,MSFT,GOOGL,TSLA,SPY" value="AAPL,MSFT,GOOGL,TSLA,SPY">
                    </div>
                    <div class="input-group">
                        <label>Weights (comma-separated, optional):</label>
                        <input type="text" id="portfolio-weights" placeholder="0.2,0.2,0.2,0.2,0.2">
                    </div>
                    <button class="action-button" onclick="runPortfolioAnalysis()">Run Analysis</button>
                </div>
                <div id="portfolio-results"></div>
            `;
        }
        
        function runPortfolioAnalysis() {
            const tickers = document.getElementById('portfolio-tickers').value;
            const weights = document.getElementById('portfolio-weights').value;
            
            document.getElementById('portfolio-results').innerHTML = '<div class="loading">Analyzing portfolio...</div>';
            
            const payload = { tickers: tickers.split(',').map(t => t.trim()) };
            if (weights) {
                payload.holdings = Object.fromEntries(
                    tickers.split(',').map((t, i) => [t.trim(), parseFloat(weights.split(',')[i]?.trim() || 1/tickers.length)])
                );
            }
            
            fetch('/api/portfolio/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    document.getElementById('portfolio-results').innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
                } else {
                    displayPortfolioResults(data);
                }
            })
            .catch(error => {
                document.getElementById('portfolio-results').innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
            });
        }
        
        function displayPortfolioResults(data) {
            const summary = data.portfolio_summary || {};
            const risk = data.risk_analysis || {};
            document.getElementById('portfolio-results').innerHTML = `
                <div class="analysis-grid">
                    <div class="analysis-card">
                        <h4>Portfolio Summary</h4>
                        <div class="metric">
                            <span class="metric-label">Total Value:</span>
                            <span class="metric-value">$${summary.total_portfolio_value?.toFixed(2) || 0}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Holdings:</span>
                            <span class="metric-value">${summary.number_of_holdings || 0}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Weighted P/E:</span>
                            <span class="metric-value">${summary.weighted_pe_ratio?.toFixed(2) || 0}</span>
                        </div>
                    </div>
                    <div class="analysis-card">
                        <h4>Risk Analysis</h4>
                        <div class="metric">
                            <span class="metric-label">Volatility:</span>
                            <span class="metric-value">${(risk.portfolio_volatility * 100)?.toFixed(2) || 0}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Sharpe Ratio:</span>
                            <span class="metric-value ${risk.sharpe_ratio_estimate > 1 ? 'positive' : 'neutral'}">${risk.sharpe_ratio_estimate?.toFixed(3) || 0}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        function analyzeCrypto() {
            showResults('Cryptocurrency Analysis');
            document.getElementById('results-content').innerHTML = '<div class="loading">Analyzing cryptocurrency markets...</div>';
            fetch('/api/crypto/analyze')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
                } else {
                    displayCryptoResults(data);
                }
            })
            .catch(error => {
                document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
            });
        }
        
        function displayCryptoResults(data) {
            const analysis = data.crypto_analysis || [];
            let html = '<div class="analysis-grid">';
            analysis.forEach(crypto => {
                html += `
                    <div class="analysis-card">
                        <h4>${crypto.symbol} - ${crypto.name}</h4>
                        <div class="metric">
                            <span class="metric-label">Current Price:</span>
                            <span class="metric-value">$${crypto.current_price?.toFixed(2)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">7d Change:</span>
                            <span class="metric-value ${crypto.price_change_7d > 0 ? 'positive' : 'negative'}">${(crypto.price_change_7d * 100)?.toFixed(2)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Market Cap:</span>
                            <span class="metric-value">$${crypto.market_cap?.toLocaleString()}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Recommendation:</span>
                            <span class="metric-value ${crypto.recommendation === 'BUY' ? 'positive' : crypto.recommendation.includes('AVOID') ? 'negative' : 'neutral'}">${crypto.recommendation}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Score:</span>
                            <span class="metric-value">${crypto.overall_score?.toFixed(1)}/100</span>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            document.getElementById('results-content').innerHTML = html;
        }
        
        function runBacktest() {
            showResults('Backtest Results');
            document.getElementById('results-content').innerHTML = '<div class="loading">Running backtest...</div>';
            fetch('/api/backtest')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
                } else {
                    displayBacktestResults(data);
                }
            })
            .catch(error => {
                document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
            });
        }
        
        function displayBacktestResults(data) {
            const trades = data.trades || [];
            let html = '<div class="analysis-grid">';
            trades.forEach(trade => {
                html += `
                    <div class="analysis-card">
                        <h4>${trade.symbol}</h4>
                        <div class="metric">
                            <span class="metric-label">Expected Return:</span>
                            <span class="metric-value positive">${(trade.expected_return * 100).toFixed(2)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Volatility:</span>
                            <span class="metric-value">${(trade.volatility * 100).toFixed(2)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Sector:</span>
                            <span class="metric-value">${trade.sector}</span>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            document.getElementById('results-content').innerHTML = html;
        }
        
        function analyzeCommodities() {
            showResults('Commodities Analysis');
            document.getElementById('results-content').innerHTML = '<div class="loading">Analyzing commodities markets...</div>';
            fetch('/api/commodities/recommendations')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
                } else {
                    displayCommoditiesResults(data);
                }
            })
            .catch(error => {
                document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
            });
        }
        
        function displayCommoditiesResults(data) {
            const recommendations = data.recommendations || [];
            let html = '<div class="analysis-grid">';
            recommendations.forEach(commodity => {
                html += `
                    <div class="analysis-card">
                        <h4>${commodity.symbol} - ${commodity.name}</h4>
                        <div class="metric">
                            <span class="metric-label">Current Price:</span>
                            <span class="metric-value">$${commodity.current_price?.toFixed(2)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Recommendation:</span>
                            <span class="metric-value ${commodity.recommendation === 'BUY' ? 'positive' : commodity.recommendation === 'SELL' ? 'negative' : 'neutral'}">${commodity.recommendation}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Volatility:</span>
                            <span class="metric-value">${(commodity.volatility * 100)?.toFixed(2)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Score:</span>
                            <span class="metric-value">${commodity.score?.toFixed(1)}/100</span>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            document.getElementById('results-content').innerHTML = html;
        }
        
        function analyzeETF() {
            showResults('ETF Analysis');
            document.getElementById('results-content').innerHTML = '<div class="loading">Analyzing ETF markets...</div>';
            fetch('/api/etf/recommendations')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
                } else {
                    displayETFResults(data);
                }
            })
            .catch(error => {
                document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
            });
        }
        
        function displayETFResults(data) {
            const recommendations = data.recommendations || [];
            let html = '<div class="analysis-grid">';
            recommendations.forEach(etf => {
                html += `
                    <div class="analysis-card">
                        <h4>${etf.symbol} - ${etf.name}</h4>
                        <div class="metric">
                            <span class="metric-label">Current Price:</span>
                            <span class="metric-value">$${etf.current_price?.toFixed(2)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Expense Ratio:</span>
                            <span class="metric-value">${(etf.expense_ratio * 100)?.toFixed(2)}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">AUM:</span>
                            <span class="metric-value">$${etf.aum?.toLocaleString()}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Recommendation:</span>
                            <span class="metric-value ${etf.recommendation === 'BUY' ? 'positive' : etf.recommendation === 'SELL' ? 'negative' : 'neutral'}">${etf.recommendation}</span>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            document.getElementById('results-content').innerHTML = html;
        }
        
        function showAlpacaTrading() {
            showResults('Enhanced Alpaca Trading Dashboard (MCP)');
            document.getElementById('results-content').innerHTML = '<div class="loading">Loading enhanced Alpaca account data...</div>';
            
            // Load both account info and portfolio summary
            Promise.all([
                fetch('/api/alpaca/account').then(r => r.json()),
                fetch('/api/alpaca/portfolio-summary').then(r => r.json()),
                fetch('/api/alpaca/status').then(r => r.json())
            ])
            .then(([accountData, portfolioData, statusData]) => {
                if (accountData.error || portfolioData.error || statusData.error) {
                    const error = accountData.error || portfolioData.error || statusData.error;
                    document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${error}</div>`;
                } else {
                    displayEnhancedAlpacaResults(accountData, portfolioData, statusData);
                }
            })
            .catch(error => {
                document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
            });
        }
        
        function displayEnhancedAlpacaResults(accountData, portfolioData, statusData) {
            const mcpStatus = statusData.mcp_available ? '🟢 MCP Enhanced' : '🟡 Standard Mode';
            const mcpBadge = accountData.mcp_enhanced ? '<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; margin-left: 10px;">MCP</span>' : '';
            
            document.getElementById('results-content').innerHTML = `
                <div class="analysis-grid">
                    <div class="analysis-card">
                        <h4>Account Information ${mcpBadge}</h4>
                        <div class="metric">
                            <span class="metric-label">Status:</span>
                            <span class="metric-value ${mcpStatus.includes('Enhanced') ? 'positive' : 'neutral'}">${mcpStatus}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Account Status:</span>
                            <span class="metric-value ${accountData.status === 'ACTIVE' ? 'positive' : 'neutral'}">${accountData.status || 'Unknown'}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Portfolio Value:</span>
                            <span class="metric-value">$${(accountData.portfolio_value || 0).toFixed(2)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Cash Balance:</span>
                            <span class="metric-value">$${(accountData.cash || 0).toFixed(2)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Buying Power:</span>
                            <span class="metric-value">$${(accountData.buying_power || 0).toFixed(2)}</span>
                        </div>
                        ${accountData.pattern_day_trader ? '<div class="metric"><span class="metric-label">PDT Status:</span><span class="metric-value warning">Pattern Day Trader</span></div>' : ''}
                    </div>
                    <div class="analysis-card">
                        <h4>Portfolio Summary</h4>
                        <div class="metric">
                            <span class="metric-label">Total P&L:</span>
                            <span class="metric-value ${(portfolioData.total_unrealized_pl || 0) >= 0 ? 'positive' : 'negative'}">$${(portfolioData.total_unrealized_pl || 0).toFixed(2)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Positions:</span>
                            <span class="metric-value">${portfolioData.position_count || 0}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Open Orders:</span>
                            <span class="metric-value">${portfolioData.open_order_count || 0}</span>
                        </div>
                    </div>
                    <div class="analysis-card">
                        <h4>Enhanced Trading Controls</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                            <button class="action-button" onclick="loadEnhancedPositions()">📊 Positions</button>
                            <button class="action-button" onclick="loadEnhancedOrders()">📋 Orders</button>
                            <button class="action-button" onclick="showQuickTrade()">⚡ Quick Trade</button>
                            <button class="action-button" onclick="showMarketData()">📈 Market Data</button>
                        </div>
                        <div style="font-size: 0.9em; color: #666; text-align: center;">
                            Enhanced with Model Context Protocol
                        </div>
                    </div>
                </div>
            `;
        }
        
        function loadEnhancedPositions() {
            showResults('Enhanced Positions (MCP)');
            document.getElementById('results-content').innerHTML = '<div class="loading">Loading enhanced positions...</div>';
            fetch('/api/alpaca/positions')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
                    return;
                }
                
                if (!data || data.length === 0) {
                    document.getElementById('results-content').innerHTML = '<div class="analysis-card"><h4>No Positions</h4><p>You currently have no open positions.</p></div>';
                    return;
                }
                
                let html = '<div class="analysis-grid">';
                data.forEach(position => {
                    const plClass = position.unrealized_pl >= 0 ? 'positive' : 'negative';
                    const mcpBadge = position.mcp_enhanced ? '<span style="background: #28a745; color: white; padding: 1px 4px; border-radius: 2px; font-size: 0.7em;">MCP</span>' : '';
                    html += `
                        <div class="analysis-card">
                            <h4>${position.symbol} ${mcpBadge}</h4>
                            <div class="metric">
                                <span class="metric-label">Quantity:</span>
                                <span class="metric-value">${position.qty} ${position.side}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Market Value:</span>
                                <span class="metric-value">$${position.market_value.toFixed(2)}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Current Price:</span>
                                <span class="metric-value">$${position.current_price.toFixed(2)}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Unrealized P&L:</span>
                                <span class="metric-value ${plClass}">$${position.unrealized_pl.toFixed(2)} (${(position.unrealized_plpc * 100).toFixed(2)}%)</span>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                document.getElementById('results-content').innerHTML = html;
            })
            .catch(error => {
                document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
            });
        }
        
        function loadEnhancedOrders() {
            showResults('Enhanced Orders (MCP)');
            document.getElementById('results-content').innerHTML = '<div class="loading">Loading enhanced orders...</div>';
            fetch('/api/alpaca/orders?status=open')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
                    return;
                }
                
                if (!data || data.length === 0) {
                    document.getElementById('results-content').innerHTML = '<div class="analysis-card"><h4>No Open Orders</h4><p>You currently have no open orders.</p></div>';
                    return;
                }
                
                let html = '<div class="analysis-grid">';
                data.forEach(order => {
                    const mcpBadge = order.mcp_enhanced ? '<span style="background: #28a745; color: white; padding: 1px 4px; border-radius: 2px; font-size: 0.7em;">MCP</span>' : '';
                    html += `
                        <div class="analysis-card">
                            <h4>${order.symbol} ${mcpBadge}</h4>
                            <div class="metric">
                                <span class="metric-label">Type:</span>
                                <span class="metric-value">${order.type} ${order.side}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Quantity:</span>
                                <span class="metric-value">${order.qty}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Status:</span>
                                <span class="metric-value">${order.status}</span>
                            </div>
                            ${order.limit_price ? `<div class="metric"><span class="metric-label">Limit Price:</span><span class="metric-value">$${order.limit_price.toFixed(2)}</span></div>` : ''}
                            <button class="action-button" onclick="cancelOrder('${order.order_id}')" style="margin-top: 10px; background: #dc3545;">Cancel Order</button>
                        </div>
                    `;
                });
                html += '</div>';
                document.getElementById('results-content').innerHTML = html;
            })
            .catch(error => {
                document.getElementById('results-content').innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
            });
        }
        
        function showQuickTrade() {
            showResults('Quick Trade (MCP Enhanced)');
            document.getElementById('results-content').innerHTML = `
                <div class="analysis-card">
                    <h4>Quick Trade Order</h4>
                    <div style="display: grid; gap: 15px;">
                        <div>
                            <label>Symbol:</label>
                            <input type="text" id="trade-symbol" placeholder="e.g., AAPL" style="width: 100%; padding: 8px; margin-top: 5px;">
                        </div>
                        <div>
                            <label>Quantity:</label>
                            <input type="number" id="trade-quantity" placeholder="Number of shares" style="width: 100%; padding: 8px; margin-top: 5px;">
                        </div>
                        <div>
                            <label>Order Type:</label>
                            <select id="trade-type" style="width: 100%; padding: 8px; margin-top: 5px;">
                                <option value="market">Market Order</option>
                                <option value="limit">Limit Order</option>
                            </select>
                        </div>
                        <div id="limit-price-container" style="display: none;">
                            <label>Limit Price:</label>
                            <input type="number" id="trade-limit-price" step="0.01" placeholder="Limit price" style="width: 100%; padding: 8px; margin-top: 5px;">
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                            <button class="action-button" onclick="placeQuickOrder('buy')" style="background: #28a745;">Buy</button>
                            <button class="action-button" onclick="placeQuickOrder('sell')" style="background: #dc3545;">Sell</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('trade-type').addEventListener('change', function() {
                const limitContainer = document.getElementById('limit-price-container');
                limitContainer.style.display = this.value === 'limit' ? 'block' : 'none';
            });
        }
        
        function showMarketData() {
            showResults('Market Data (MCP Enhanced)');
            document.getElementById('results-content').innerHTML = `
                <div class="analysis-card">
                    <h4>Get Market Data</h4>
                    <div style="display: grid; gap: 15px;">
                        <div>
                            <label>Symbol:</label>
                            <input type="text" id="market-symbol" placeholder="e.g., AAPL" style="width: 100%; padding: 8px; margin-top: 5px;">
                        </div>
                        <button class="action-button" onclick="getMarketData()">Get Market Data</button>
                    </div>
                    <div id="market-data-results" style="margin-top: 20px;"></div>
                </div>
            `;
        }
        
        function placeQuickOrder(side) {
            const symbol = document.getElementById('trade-symbol').value.toUpperCase();
            const quantity = parseFloat(document.getElementById('trade-quantity').value);
            const orderType = document.getElementById('trade-type').value;
            const limitPrice = parseFloat(document.getElementById('trade-limit-price').value);
            
            if (!symbol || !quantity) {
                alert('Please enter symbol and quantity');
                return;
            }
            
            if (orderType === 'limit' && !limitPrice) {
                alert('Please enter limit price for limit orders');
                return;
            }
            
            const orderData = {
                symbol: symbol,
                qty: quantity,
                side: side,
                type: orderType
            };
            
            if (orderType === 'limit') {
                orderData.limit_price = limitPrice;
            }
            
            fetch('/api/alpaca/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(orderData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(`Error: ${data.error}`);
                } else {
                    alert(`Order placed successfully! Order ID: ${data.order_id}`);
                    loadEnhancedOrders();
                }
            })
            .catch(error => {
                alert(`Error: ${error.message}`);
            });
        }
        
        function cancelOrder(orderId) {
            if (!confirm('Are you sure you want to cancel this order?')) {
                return;
            }
            
            fetch(`/api/alpaca/orders/${orderId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(`Error: ${data.error}`);
                } else {
                    alert('Order cancelled successfully!');
                    loadEnhancedOrders();
                }
            })
            .catch(error => {
                alert(`Error: ${error.message}`);
            });
        }
        
        function getMarketData() {
            const symbol = document.getElementById('market-symbol').value.toUpperCase();
            if (!symbol) {
                alert('Please enter a symbol');
                return;
            }
            
            document.getElementById('market-data-results').innerHTML = '<div class="loading">Loading market data...</div>';
            
            fetch(`/api/alpaca/market-data/${symbol}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('market-data-results').innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
                    return;
                }
                
                const mcpBadge = data.mcp_enhanced ? '<span style="background: #28a745; color: white; padding: 1px 4px; border-radius: 2px; font-size: 0.7em;">MCP</span>' : '';
                
                document.getElementById('market-data-results').innerHTML = `
                    <div class="analysis-card">
                        <h4>${data.symbol} Market Data ${mcpBadge}</h4>
                        ${data.bid_price ? `<div class="metric"><span class="metric-label">Bid:</span><span class="metric-value">$${data.bid_price.toFixed(2)} x ${data.bid_size}</span></div>` : ''}
                        ${data.ask_price ? `<div class="metric"><span class="metric-label">Ask:</span><span class="metric-value">$${data.ask_price.toFixed(2)} x ${data.ask_size}</span></div>` : ''}
                        ${data.close ? `<div class="metric"><span class="metric-label">Last Close:</span><span class="metric-value">$${data.close.toFixed(2)}</span></div>` : ''}
                        ${data.volume ? `<div class="metric"><span class="metric-label">Volume:</span><span class="metric-value">${data.volume.toLocaleString()}</span></div>` : ''}
                        ${data.high ? `<div class="metric"><span class="metric-label">Day High:</span><span class="metric-value">$${data.high.toFixed(2)}</span></div>` : ''}
                        ${data.low ? `<div class="metric"><span class="metric-label">Day Low:</span><span class="metric-value">$${data.low.toFixed(2)}</span></div>` : ''}
                    </div>
                `;
            })
            .catch(error => {
                document.getElementById('market-data-results').innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
            });
        }
        
        function showResults(title) {
            document.getElementById('results').classList.add('active');
            document.querySelector('.results-header').textContent = title;
            document.getElementById('results-content').innerHTML = '<div class="loading">Initializing...</div>';
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            console.log('TradeRiser Platform Initialized');
        });
    </script>
</body>
</html>
    """)

@app.route('/api/portfolio/analyze', methods=['POST'])
def analyze_portfolio():
    """Portfolio analysis endpoint"""
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data provided for portfolio analysis")
            raise BadRequest("No JSON data provided")
        holdings = data.get('holdings', {})
        if not holdings:
            tickers = data.get('tickers', [])
            weights = data.get('weights', None)
            if not tickers:
                logger.error("No tickers or holdings provided")
                raise BadRequest("No tickers or holdings provided")
            holdings = {t: w for t, w in zip(tickers, weights or [1/len(tickers)]*len(tickers))}
        
        analysis = portfolio_analyzer.analyze_portfolio(holdings)
        if 'error' in analysis:
            logger.error(f"Portfolio analysis error: {analysis['error']}")
            raise BadRequest(analysis['error'])
        logger.info("Portfolio analysis completed successfully")
        return jsonify(analysis)
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except TooManyRequests:
        logger.error("Rate limit exceeded for portfolio analysis")
        return jsonify({'error': 'Rate limit exceeded'}), 429
    except Exception as e:
        logger.error(f"Internal error in portfolio analysis: {str(e)}")
        raise InternalServerError(str(e))

@app.route('/api/crypto/analyze', methods=['GET'])
def analyze_crypto_api():
    """Cryptocurrency analysis endpoint"""
    try:
        analysis = crypto_trader.analyze_crypto_market()
        if not analysis:
            logger.warning("No crypto analysis results returned")
            raise BadRequest("No analysis results available")
        logger.info("Crypto analysis completed successfully")
        return jsonify({'crypto_analysis': analysis})
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except TooManyRequests:
        logger.error("Rate limit exceeded for crypto analysis")
        return jsonify({'error': 'Rate limit exceeded'}), 429
    except Exception as e:
        logger.error(f"Internal error in crypto analysis: {str(e)}")
        raise InternalServerError(str(e))

@app.route('/api/backtest', methods=['GET'])
def run_backtest():
    """Backtest endpoint for optimal trade selection"""
    try:
        trades = backtest_solver.select_trades()
        if not trades:
            logger.warning("No trades selected in backtest")
            raise BadRequest("No trades selected")
        logger.info("Backtest completed successfully")
        return jsonify({'trades': trades})
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except TooManyRequests:
        logger.error("Rate limit exceeded for backtest")
        return jsonify({'error': 'Rate limit exceeded'}), 429
    except Exception as e:
        logger.error(f"Internal error in backtest: {str(e)}")
        raise InternalServerError(str(e))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        logger.info("Health check requested")
        return jsonify({
            'status': 'healthy',
            'platform': 'TradeRiser.AI',
            'version': '3.0.0',
            'systems': {
                'portfolio_analyzer': 'online',
                'crypto_trader': 'online',
                'backtest_solver': 'online'
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Commodities Trading Endpoints
@app.route('/api/commodities/analyze/<symbol>')
def analyze_commodity(symbol):
    """Analyze a specific commodity"""
    try:
        analysis = commodities_trader.analyze_commodity(symbol)
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error analyzing commodity {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/commodities/screen')
def screen_commodities():
    """Screen commodities based on criteria"""
    try:
        min_volume = request.args.get('min_volume', 1000000, type=int)
        max_volatility = request.args.get('max_volatility', 0.3, type=float)
        
        screened = commodities_trader.screen_commodities(
            min_volume=min_volume,
            max_volatility=max_volatility
        )
        return jsonify(screened)
    except Exception as e:
        logger.error(f"Error screening commodities: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/commodities/recommendations')
def get_commodity_recommendations():
    """Get commodity trading recommendations"""
    try:
        recommendations = commodities_trader.get_recommendations()
        return jsonify(recommendations)
    except Exception as e:
        logger.error(f"Error getting commodity recommendations: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ETF Analysis Endpoints
@app.route('/api/etf/analyze/<symbol>')
def analyze_etf(symbol):
    """Analyze a specific ETF"""
    try:
        analysis = etf_analyzer.analyze_etf(symbol)
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error analyzing ETF {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/etf/screen')
def screen_etfs():
    """Screen ETFs based on criteria"""
    try:
        min_aum = request.args.get('min_aum', 100000000, type=float)  # $100M minimum
        max_expense_ratio = request.args.get('max_expense_ratio', 0.01, type=float)  # 1% max
        min_avg_volume = request.args.get('min_avg_volume', 100000, type=int)
        
        screened = etf_analyzer.screen_etfs(
            min_aum=min_aum,
            max_expense_ratio=max_expense_ratio,
            min_avg_volume=min_avg_volume
        )
        return jsonify(screened)
    except Exception as e:
        logger.error(f"Error screening ETFs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/etf/compare')
def compare_etfs():
    """Compare multiple ETFs"""
    try:
        symbols = request.args.get('symbols', '').split(',')
        if len(symbols) < 2:
            return jsonify({'error': 'At least 2 symbols required for comparison'}), 400
        
        comparison = etf_analyzer.compare_etfs(symbols)
        return jsonify(comparison)
    except Exception as e:
        logger.error(f"Error comparing ETFs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/etf/recommendations')
def get_etf_recommendations():
    """Get ETF recommendations"""
    try:
        recommendations = etf_analyzer.get_recommendations()
        return jsonify(recommendations)
    except Exception as e:
        logger.error(f"Error getting ETF recommendations: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Alpaca Trading Endpoints
@app.route('/api/alpaca/account')
def get_alpaca_account():
    """Get enhanced Alpaca account information"""
    try:
        account_info = alpaca_mcp.get_enhanced_account_info()
        return jsonify(account_info)
    except Exception as e:
        logger.error(f"Error getting enhanced Alpaca account info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alpaca/positions')
def get_alpaca_positions():
    """Get enhanced Alpaca positions"""
    try:
        positions = alpaca_mcp.get_enhanced_positions()
        return jsonify(positions)
    except Exception as e:
        logger.error(f"Error getting enhanced Alpaca positions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alpaca/orders', methods=['GET', 'POST'])
def handle_alpaca_orders():
    """Get enhanced orders or place new order"""
    try:
        if request.method == 'GET':
            status = request.args.get('status', 'open')
            orders = alpaca_mcp.get_enhanced_orders(status)
            return jsonify(orders)
        else:  # POST
            data = request.get_json()
            required_fields = ['symbol', 'qty', 'side', 'type']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Use enhanced MCP order placement
            if data['type'] == 'limit' and data.get('limit_price'):
                order = alpaca_mcp.place_enhanced_limit_order(
                    data['symbol'], 
                    data['side'], 
                    float(data['qty']), 
                    float(data['limit_price'])
                )
            else:
                order = alpaca_mcp.place_enhanced_market_order(
                    data['symbol'], 
                    data['side'], 
                    float(data['qty'])
                )
            
            return jsonify(order)
    except Exception as e:
        logger.error(f"Error handling enhanced Alpaca orders: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alpaca/market-data/<symbol>')
def get_alpaca_market_data(symbol):
    """Get enhanced market data for a symbol"""
    try:
        market_data = alpaca_mcp.get_enhanced_market_data(symbol)
        return jsonify(market_data)
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alpaca/compliance', methods=['GET'])
def get_alpaca_compliance():
    """Get Alpaca compliance report"""
    try:
        compliance_report = alpaca_trader.generate_compliance_report()
        return jsonify(compliance_report)
    except Exception as e:
        logger.error(f"Error getting Alpaca compliance report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alpaca/portfolio-summary', methods=['GET'])
def get_alpaca_portfolio_summary():
    """Get enhanced portfolio summary with MCP capabilities"""
    try:
        summary = alpaca_mcp.get_portfolio_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alpaca/orders/<order_id>', methods=['DELETE'])
def cancel_alpaca_order(order_id):
    """Cancel an Alpaca order"""
    try:
        result = alpaca_mcp.cancel_enhanced_order(order_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alpaca/status', methods=['GET'])
def get_alpaca_status():
    """Get enhanced Alpaca connection status"""
    try:
        status = alpaca_mcp.get_connection_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting Alpaca status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/compliance/disclaimer')
def get_compliance_disclaimer():
    """Get SEC compliance disclaimer"""
    disclaimer = {
        'title': 'Important Legal Disclaimer',
        'content': [
            'TradeRiser.AI is for informational and educational purposes only.',
            'This platform does not provide investment advice, financial advice, trading advice, or any other sort of advice.',
            'All content is provided for informational purposes only and should not be construed as investment advice.',
            'Trading and investing in financial markets involves substantial risk of loss and is not suitable for every investor.',
            'Past performance is not indicative of future results.',
            'You should consult with a licensed financial advisor before making any investment decisions.',
            'TradeRiser.AI and its creators are not registered investment advisors and do not provide investment advice.',
            'By using this platform, you acknowledge that you understand these risks and agree to trade at your own risk.',
            'All trading decisions are your own responsibility.',
            'This platform complies with SEC regulations regarding financial information dissemination.'
        ],
        'last_updated': datetime.now().isoformat(),
        'version': '1.0'
    }
    return jsonify(disclaimer)

if __name__ == '__main__':
    logger.info("Starting TradeRiser Integrated Platform")
    app.run(host='0.0.0.0', port=5000, debug=False)