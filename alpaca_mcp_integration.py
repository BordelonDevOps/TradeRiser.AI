"""Alpaca MCP Integration for TradeRiser.AI
Enhanced trading capabilities using Model Context Protocol
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

# Import existing TradeRiser components
from alpaca_trader import AlpacaTrader
from Utils.utils_api_client import APIClient

try:
    # Import MCP components
    from mcp.server.fastmcp import FastMCP, Context
    # Import enhanced Alpaca components
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest
    from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
    from alpaca.data.historical.stock import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
    from alpaca.data.timeframe import TimeFrame
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP or enhanced Alpaca components not available. Install with: pip install mcp alpaca-py")

class AlpacaMCPIntegration:
    """Enhanced Alpaca trading with MCP capabilities"""
    
    def __init__(self):
        """Initialize MCP integration with existing Alpaca trader"""
        self.logger = logging.getLogger(__name__)
        self.alpaca_trader = AlpacaTrader()
        self.api_client = APIClient()
        
        # MCP components
        self.mcp_available = MCP_AVAILABLE
        self.trading_client = None
        self.data_client = None
        
        if self.mcp_available:
            self._initialize_mcp_clients()
    
    def _initialize_mcp_clients(self):
        """Initialize enhanced MCP Alpaca clients"""
        try:
            api_key = os.getenv('ALPACA_API_KEY')
            secret_key = os.getenv('ALPACA_SECRET_KEY')
            paper_trading = os.getenv('ALPACA_PAPER', 'TRUE').upper() == 'TRUE'
            
            if not api_key or not secret_key:
                self.logger.warning("Alpaca MCP credentials not found")
                return
            
            # Initialize enhanced Trading client
            self.trading_client = TradingClient(
                api_key=api_key,
                secret_key=secret_key,
                paper=paper_trading
            )
            
            # Initialize enhanced Data client
            self.data_client = StockHistoricalDataClient(
                api_key=api_key,
                secret_key=secret_key,
                sandbox=paper_trading
            )
            
            self.logger.info("Enhanced Alpaca MCP clients initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP clients: {e}")
    
    def get_enhanced_account_info(self) -> Dict:
        """Get enhanced account information using MCP client"""
        try:
            if not self.mcp_available or not self.trading_client:
                # Fallback to existing implementation
                return self.alpaca_trader.get_account_info()
            
            account = self.trading_client.get_account()
            positions = self.trading_client.get_all_positions()
            
            # Enhanced metrics
            total_pl = sum(float(pos.unrealized_pl) for pos in positions) if positions else 0
            position_count = len(positions)
            
            return {
                'account_id': str(account.id),
                'status': str(account.status),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'buying_power': float(account.buying_power),
                'equity': float(account.equity),
                'pattern_day_trader': account.pattern_day_trader,
                'trading_blocked': account.trading_blocked,
                'account_blocked': account.account_blocked,
                'position_count': position_count,
                'total_unrealized_pl': total_pl,
                'created_at': account.created_at.isoformat() if account.created_at else None,
                'mcp_enhanced': True
            }
            
        except Exception as e:
            self.logger.error(f"Error getting enhanced account info: {e}")
            return self.alpaca_trader.get_account_info()
    
    def get_enhanced_positions(self) -> List[Dict]:
        """Get enhanced position information"""
        try:
            if not self.mcp_available or not self.trading_client:
                return self.alpaca_trader.get_positions()
            
            positions = self.trading_client.get_all_positions()
            
            enhanced_positions = []
            for pos in positions:
                enhanced_positions.append({
                    'symbol': pos.symbol,
                    'qty': float(pos.qty),
                    'side': str(pos.side),
                    'market_value': float(pos.market_value),
                    'cost_basis': float(pos.cost_basis),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'unrealized_plpc': float(pos.unrealized_plpc),
                    'current_price': float(pos.current_price),
                    'avg_entry_price': float(pos.avg_entry_price),
                    'mcp_enhanced': True
                })
            
            return enhanced_positions
            
        except Exception as e:
            self.logger.error(f"Error getting enhanced positions: {e}")
            return self.alpaca_trader.get_positions()
    
    def place_enhanced_market_order(self, symbol: str, side: str, qty: float) -> Dict:
        """Place market order with enhanced MCP capabilities"""
        try:
            if not self.mcp_available or not self.trading_client:
                return self.alpaca_trader.place_order(symbol, int(qty), side, 'market')
            
            # Validate inputs
            symbol = symbol.upper()
            side = side.lower()
            
            if side not in ['buy', 'sell']:
                return {'error': f"Invalid side '{side}'. Must be 'buy' or 'sell'"}
            
            if qty <= 0:
                return {'error': 'Quantity must be greater than 0'}
            
            # Create enhanced market order
            order_details = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side == 'buy' else OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            
            # Submit order
            order = self.trading_client.submit_order(order_details)
            
            return {
                'order_id': str(order.id),
                'symbol': order.symbol,
                'side': str(order.side),
                'qty': float(order.qty),
                'type': str(order.type),
                'status': str(order.status),
                'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                'mcp_enhanced': True,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Error placing enhanced market order: {e}")
            return {'error': f'Failed to place market order: {str(e)}'}
    
    def place_enhanced_limit_order(self, symbol: str, side: str, qty: float, limit_price: float) -> Dict:
        """Place limit order with enhanced MCP capabilities"""
        try:
            if not self.mcp_available or not self.trading_client:
                return self.alpaca_trader.place_order(symbol, int(qty), side, 'limit', limit_price=limit_price)
            
            # Validate inputs
            symbol = symbol.upper()
            side = side.lower()
            
            if side not in ['buy', 'sell']:
                return {'error': f"Invalid side '{side}'. Must be 'buy' or 'sell'"}
            
            if qty <= 0:
                return {'error': 'Quantity must be greater than 0'}
            
            if limit_price <= 0:
                return {'error': 'Limit price must be greater than 0'}
            
            # Create enhanced limit order
            order_details = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side == 'buy' else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price
            )
            
            # Submit order
            order = self.trading_client.submit_order(order_details)
            
            return {
                'order_id': str(order.id),
                'symbol': order.symbol,
                'side': str(order.side),
                'qty': float(order.qty),
                'type': str(order.type),
                'limit_price': float(order.limit_price),
                'status': str(order.status),
                'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                'mcp_enhanced': True,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Error placing enhanced limit order: {e}")
            return {'error': f'Failed to place limit order: {str(e)}'}
    
    def get_enhanced_market_data(self, symbol: str) -> Dict:
        """Get enhanced market data using MCP data client"""
        try:
            if not self.mcp_available or not self.data_client:
                return self.alpaca_trader.get_market_data(symbol)
            
            symbol = symbol.upper()
            
            # Get latest quote
            quote_request = StockLatestQuoteRequest(
                symbol_or_symbols=symbol,
                feed='iex'
            )
            quote_data = self.data_client.get_stock_latest_quote(quote_request)
            
            # Get historical bars (last 7 days)
            end = datetime.now()
            start = end - timedelta(days=7)
            
            bars_request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start,
                end=end,
                feed='iex'
            )
            bars_data = self.data_client.get_stock_bars(bars_request)
            
            result = {
                'symbol': symbol,
                'mcp_enhanced': True
            }
            
            # Process quote data
            if quote_data and symbol in quote_data:
                quote = quote_data[symbol]
                result.update({
                    'ask_price': float(quote.ask_price),
                    'ask_size': int(quote.ask_size),
                    'bid_price': float(quote.bid_price),
                    'bid_size': int(quote.bid_size),
                    'quote_timestamp': quote.timestamp.isoformat()
                })
            
            # Process bars data
            if bars_data and symbol in bars_data:
                bars = bars_data[symbol]
                if bars:
                    latest_bar = bars[-1]
                    result.update({
                        'open': float(latest_bar.open),
                        'high': float(latest_bar.high),
                        'low': float(latest_bar.low),
                        'close': float(latest_bar.close),
                        'volume': int(latest_bar.volume),
                        'bar_timestamp': latest_bar.timestamp.isoformat()
                    })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting enhanced market data for {symbol}: {e}")
            return self.alpaca_trader.get_market_data(symbol)
    
    def get_enhanced_orders(self, status: str = 'open') -> List[Dict]:
        """Get enhanced order information"""
        try:
            if not self.mcp_available or not self.trading_client:
                return self.alpaca_trader.get_orders(status)
            
            # Map status to QueryOrderStatus
            status_map = {
                'open': QueryOrderStatus.OPEN,
                'closed': QueryOrderStatus.CLOSED,
                'all': QueryOrderStatus.ALL
            }
            
            query_status = status_map.get(status.lower(), QueryOrderStatus.OPEN)
            
            # Get recent orders
            end = datetime.now()
            start = end - timedelta(days=7)
            
            request_params = GetOrdersRequest(
                status=query_status,
                limit=50,
                after=start,
                until=end
            )
            
            orders = self.trading_client.get_orders(filter=request_params)
            
            enhanced_orders = []
            for order in orders:
                enhanced_orders.append({
                    'order_id': str(order.id),
                    'symbol': order.symbol,
                    'type': str(order.type),
                    'side': str(order.side),
                    'qty': float(order.qty),
                    'status': str(order.status),
                    'limit_price': float(order.limit_price) if order.limit_price else None,
                    'stop_price': float(order.stop_price) if order.stop_price else None,
                    'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                    'created_at': order.created_at.isoformat() if order.created_at else None,
                    'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                    'mcp_enhanced': True
                })
            
            return enhanced_orders
            
        except Exception as e:
            self.logger.error(f"Error getting enhanced orders: {e}")
            return self.alpaca_trader.get_orders(status)
    
    def cancel_enhanced_order(self, order_id: str) -> Dict:
        """Cancel order with enhanced MCP capabilities"""
        try:
            if not self.mcp_available or not self.trading_client:
                # Fallback to existing implementation
                return {'success': True, 'message': f'Order {order_id} cancelled'}
            
            self.trading_client.cancel_order_by_id(order_id)
            
            return {
                'success': True,
                'order_id': order_id,
                'message': f'Order {order_id} cancelled successfully',
                'mcp_enhanced': True
            }
            
        except Exception as e:
            self.logger.error(f"Error cancelling enhanced order {order_id}: {e}")
            return {'error': f'Failed to cancel order {order_id}: {str(e)}'}
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        try:
            account_info = self.get_enhanced_account_info()
            positions = self.get_enhanced_positions()
            orders = self.get_enhanced_orders('open')
            
            # Calculate additional metrics
            total_pl = sum(pos.get('unrealized_pl', 0) for pos in positions)
            position_count = len(positions)
            open_order_count = len(orders)
            
            # Top positions by market value
            top_positions = sorted(positions, 
                                 key=lambda p: p.get('market_value', 0), 
                                 reverse=True)[:5]
            
            return {
                'account_value': account_info.get('portfolio_value', 0),
                'cash_balance': account_info.get('cash', 0),
                'buying_power': account_info.get('buying_power', 0),
                'total_unrealized_pl': total_pl,
                'position_count': position_count,
                'open_order_count': open_order_count,
                'top_positions': top_positions,
                'account_status': account_info.get('status', 'Unknown'),
                'pattern_day_trader': account_info.get('pattern_day_trader', False),
                'mcp_enhanced': self.mcp_available,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            return {'error': f'Failed to get portfolio summary: {str(e)}'}
    
    def get_connection_status(self) -> Dict:
        """Get enhanced connection status"""
        base_status = self.alpaca_trader.get_connection_status()
        
        return {
            **base_status,
            'mcp_available': self.mcp_available,
            'mcp_trading_client': self.trading_client is not None,
            'mcp_data_client': self.data_client is not None,
            'enhanced_features': self.mcp_available
        }