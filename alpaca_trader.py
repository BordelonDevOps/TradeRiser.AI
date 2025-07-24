"""Alpaca Trading Integration for TradeRiser.AI
Professional-grade trading with SEC compliance and risk management
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from Utils.utils_api_client import APIClient

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logging.warning("Alpaca Trade API not installed. Install with: pip install alpaca-trade-api")

class AlpacaTrader:
    def __init__(self):
        """Initialize Alpaca trading client with proper error handling"""
        self.logger = logging.getLogger(__name__)
        self.api = None
        self.account = None
        self.is_connected = False
        
        # SEC Compliance settings
        self.max_position_size = 0.05  # Max 5% of portfolio per position
        self.max_daily_trades = 3      # Pattern day trader rule compliance
        self.min_account_value = 25000 # PDT rule minimum
        
        # Risk management settings
        self.max_portfolio_risk = 0.02  # Max 2% portfolio risk per trade
        self.stop_loss_pct = 0.05      # 5% stop loss
        self.take_profit_pct = 0.10    # 10% take profit
        
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize connection to Alpaca API"""
        try:
            if not ALPACA_AVAILABLE:
                self.logger.error("Alpaca Trade API not available")
                return
            
            # Get API credentials from environment
            api_key = os.getenv('ALPACA_API_KEY')
            secret_key = os.getenv('ALPACA_SECRET_KEY')
            base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')  # Default to paper trading
            
            if not api_key or not secret_key:
                self.logger.warning("Alpaca API credentials not found in environment variables")
                return
            
            # Initialize API connection
            self.api = tradeapi.REST(
                api_key,
                secret_key,
                base_url,
                api_version='v2'
            )
            
            # Test connection and get account info
            self.account = self.api.get_account()
            self.is_connected = True
            
            # Log connection status
            account_status = "LIVE" if "paper" not in base_url else "PAPER"
            self.logger.info(f"Connected to Alpaca {account_status} trading account")
            
            # Check account eligibility
            self._check_account_eligibility()
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Alpaca: {str(e)}")
            self.is_connected = False
    
    def _check_account_eligibility(self):
        """Check account eligibility for trading"""
        try:
            if not self.account:
                return
            
            account_value = float(self.account.portfolio_value)
            
            # Check PDT rule compliance
            if account_value < self.min_account_value:
                self.logger.warning(f"Account value ${account_value:,.2f} below PDT minimum ${self.min_account_value:,.2f}")
            
            # Check account status
            if self.account.trading_blocked:
                self.logger.error("Trading is blocked on this account")
            
            if self.account.account_blocked:
                self.logger.error("Account is blocked")
            
            # Log account info
            self.logger.info(f"Account Value: ${account_value:,.2f}")
            self.logger.info(f"Buying Power: ${float(self.account.buying_power):,.2f}")
            self.logger.info(f"Day Trade Count: {self.account.daytrade_count}")
            
        except Exception as e:
            self.logger.error(f"Error checking account eligibility: {str(e)}")
    
    def get_account_info(self) -> Dict:
        """Get comprehensive account information"""
        try:
            if not self.is_connected:
                return {'error': 'Not connected to Alpaca', 'connected': False}
            
            account = self.api.get_account()
            positions = self.api.list_positions()
            orders = self.api.list_orders(status='open')
            
            # Calculate portfolio metrics
            portfolio_value = float(account.portfolio_value)
            cash = float(account.cash)
            equity = float(account.equity)
            
            # Position analysis
            position_data = []
            total_position_value = 0
            
            for position in positions:
                pos_value = float(position.market_value)
                total_position_value += abs(pos_value)
                
                position_data.append({
                    'symbol': position.symbol,
                    'qty': float(position.qty),
                    'side': position.side,
                    'market_value': pos_value,
                    'cost_basis': float(position.cost_basis),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc),
                    'current_price': float(position.current_price)
                })
            
            return {
                'connected': True,
                'account_status': account.status,
                'trading_blocked': account.trading_blocked,
                'portfolio_value': portfolio_value,
                'cash': cash,
                'equity': equity,
                'buying_power': float(account.buying_power),
                'day_trade_count': int(account.daytrade_count),
                'positions': position_data,
                'open_orders': len(orders),
                'total_positions': len(positions),
                'position_concentration': total_position_value / portfolio_value if portfolio_value > 0 else 0,
                'cash_percentage': cash / portfolio_value if portfolio_value > 0 else 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting account info: {str(e)}")
            return {'error': str(e), 'connected': False}
    
    def place_order(self, symbol: str, qty: int, side: str, order_type: str = 'market', 
                   time_in_force: str = 'day', limit_price: float = None, 
                   stop_price: float = None) -> Dict:
        """Place a trading order with risk management"""
        try:
            if not self.is_connected:
                return {'error': 'Not connected to Alpaca'}
            
            # Pre-trade risk checks
            risk_check = self._pre_trade_risk_check(symbol, qty, side)
            if not risk_check['approved']:
                return {'error': f'Risk check failed: {risk_check["reason"]}'}
            
            # Place the order
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price
            )
            
            self.logger.info(f"Order placed: {side} {qty} {symbol} at {order_type}")
            
            return {
                'success': True,
                'order_id': order.id,
                'symbol': order.symbol,
                'qty': order.qty,
                'side': order.side,
                'type': order.type,
                'status': order.status,
                'submitted_at': order.submitted_at,
                'filled_qty': order.filled_qty if hasattr(order, 'filled_qty') else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
            return {'error': str(e)}
    
    def _pre_trade_risk_check(self, symbol: str, qty: int, side: str) -> Dict:
        """Comprehensive pre-trade risk assessment"""
        try:
            account = self.api.get_account()
            portfolio_value = float(account.portfolio_value)
            
            # Get current price
            try:
                latest_trade = self.api.get_latest_trade(symbol)
                current_price = float(latest_trade.price)
            except:
                # Fallback to last quote
                quote = self.api.get_latest_quote(symbol)
                current_price = (float(quote.bid_price) + float(quote.ask_price)) / 2
            
            position_value = abs(qty) * current_price
            position_percentage = position_value / portfolio_value
            
            # Check position size limit
            if position_percentage > self.max_position_size:
                return {
                    'approved': False,
                    'reason': f'Position size {position_percentage:.1%} exceeds limit {self.max_position_size:.1%}'
                }
            
            # Check day trading rules
            if int(account.daytrade_count) >= self.max_daily_trades and portfolio_value < self.min_account_value:
                return {
                    'approved': False,
                    'reason': 'Day trading limit reached for accounts under $25,000'
                }
            
            # Check buying power
            if side == 'buy' and position_value > float(account.buying_power):
                return {
                    'approved': False,
                    'reason': 'Insufficient buying power'
                }
            
            # Check if we already have a large position in this symbol
            try:
                existing_position = self.api.get_position(symbol)
                existing_value = abs(float(existing_position.market_value))
                total_exposure = (existing_value + position_value) / portfolio_value
                
                if total_exposure > self.max_position_size * 2:  # Allow up to 2x normal limit for existing positions
                    return {
                        'approved': False,
                        'reason': f'Total exposure {total_exposure:.1%} would exceed concentration limit'
                    }
            except:
                pass  # No existing position
            
            return {
                'approved': True,
                'position_value': position_value,
                'position_percentage': position_percentage,
                'current_price': current_price
            }
            
        except Exception as e:
            return {'approved': False, 'reason': f'Risk check error: {str(e)}'}
    
    def get_positions(self) -> List[Dict]:
        """Get all current positions"""
        try:
            if not self.is_connected:
                return []
            
            positions = self.api.list_positions()
            position_data = []
            
            for position in positions:
                position_data.append({
                    'symbol': position.symbol,
                    'qty': float(position.qty),
                    'side': position.side,
                    'market_value': float(position.market_value),
                    'cost_basis': float(position.cost_basis),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc),
                    'current_price': float(position.current_price),
                    'avg_entry_price': float(position.avg_entry_price)
                })
            
            return position_data
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {str(e)}")
            return []
    
    def get_orders(self, status: str = 'open') -> List[Dict]:
        """Get orders by status"""
        try:
            if not self.is_connected:
                return []
            
            orders = self.api.list_orders(status=status, limit=100)
            order_data = []
            
            for order in orders:
                order_data.append({
                    'id': order.id,
                    'symbol': order.symbol,
                    'qty': float(order.qty),
                    'side': order.side,
                    'type': order.type,
                    'status': order.status,
                    'time_in_force': order.time_in_force,
                    'limit_price': float(order.limit_price) if order.limit_price else None,
                    'stop_price': float(order.stop_price) if order.stop_price else None,
                    'filled_qty': float(order.filled_qty) if hasattr(order, 'filled_qty') else 0,
                    'submitted_at': order.submitted_at,
                    'updated_at': order.updated_at
                })
            
            return order_data
            
        except Exception as e:
            self.logger.error(f"Error getting orders: {str(e)}")
            return []
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an open order"""
        try:
            if not self.is_connected:
                return {'error': 'Not connected to Alpaca'}
            
            self.api.cancel_order(order_id)
            self.logger.info(f"Order {order_id} cancelled")
            
            return {'success': True, 'message': f'Order {order_id} cancelled'}
            
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return {'error': str(e)}
    
    def close_position(self, symbol: str, qty: str = None) -> Dict:
        """Close a position (partial or full)"""
        try:
            if not self.is_connected:
                return {'error': 'Not connected to Alpaca'}
            
            # Get current position
            position = self.api.get_position(symbol)
            current_qty = float(position.qty)
            
            if current_qty == 0:
                return {'error': f'No position in {symbol}'}
            
            # Determine quantity to close
            if qty is None:
                close_qty = abs(current_qty)  # Close entire position
            else:
                close_qty = min(float(qty), abs(current_qty))
            
            # Determine side (opposite of current position)
            side = 'sell' if current_qty > 0 else 'buy'
            
            # Place closing order
            result = self.place_order(symbol, int(close_qty), side)
            
            if result.get('success'):
                self.logger.info(f"Closing position: {side} {close_qty} {symbol}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error closing position {symbol}: {str(e)}")
            return {'error': str(e)}
    
    def get_market_data(self, symbol: str, timeframe: str = '1Day', limit: int = 100) -> Dict:
        """Get market data for analysis"""
        try:
            if not self.is_connected:
                return {'error': 'Not connected to Alpaca'}
            
            # Get historical bars
            bars = self.api.get_bars(
                symbol,
                timeframe,
                limit=limit,
                adjustment='raw'
            ).df
            
            if bars.empty:
                return {'error': f'No data available for {symbol}'}
            
            # Get latest quote
            quote = self.api.get_latest_quote(symbol)
            
            return {
                'symbol': symbol,
                'current_bid': float(quote.bid_price),
                'current_ask': float(quote.ask_price),
                'current_spread': float(quote.ask_price) - float(quote.bid_price),
                'bars': bars.to_dict('records'),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {str(e)}")
            return {'error': str(e)}
    
    def generate_compliance_report(self) -> Dict:
        """Generate SEC compliance and risk management report"""
        try:
            if not self.is_connected:
                return {'error': 'Not connected to Alpaca'}
            
            account_info = self.get_account_info()
            positions = self.get_positions()
            orders = self.get_orders('all')
            
            # Calculate risk metrics
            portfolio_value = account_info['portfolio_value']
            total_exposure = sum(abs(pos['market_value']) for pos in positions)
            
            # Position concentration analysis
            position_concentrations = []
            for pos in positions:
                concentration = abs(pos['market_value']) / portfolio_value
                position_concentrations.append({
                    'symbol': pos['symbol'],
                    'concentration': concentration,
                    'compliant': concentration <= self.max_position_size
                })
            
            # Day trading analysis
            today_orders = [o for o in orders if o['submitted_at'].startswith(datetime.now().strftime('%Y-%m-%d'))]
            day_trades_today = len([o for o in today_orders if o['side'] == 'sell'])
            
            return {
                'timestamp': datetime.now().isoformat(),
                'account_value': portfolio_value,
                'pdt_compliant': portfolio_value >= self.min_account_value,
                'day_trades_today': day_trades_today,
                'day_trade_limit': self.max_daily_trades,
                'total_exposure': total_exposure,
                'exposure_ratio': total_exposure / portfolio_value if portfolio_value > 0 else 0,
                'position_concentrations': position_concentrations,
                'concentration_violations': [p for p in position_concentrations if not p['compliant']],
                'risk_summary': {
                    'max_position_size': self.max_position_size,
                    'max_portfolio_risk': self.max_portfolio_risk,
                    'stop_loss_pct': self.stop_loss_pct,
                    'take_profit_pct': self.take_profit_pct
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating compliance report: {str(e)}")
            return {'error': str(e)}
    
    def get_connection_status(self) -> Dict:
        """Get connection and API status"""
        return {
            'connected': self.is_connected,
            'alpaca_available': ALPACA_AVAILABLE,
            'account_active': self.account is not None,
            'paper_trading': 'paper' in os.getenv('ALPACA_BASE_URL', ''),
            'timestamp': datetime.now().isoformat()
        }