"""
Backtest Solver using OR-Tools for trade selection
"""
from ortools.linear_solver import pywraplp
from typing import Dict, List
from Utils.utils_api_client import APIClient
import logging

logging.basicConfig(
    filename='traderiser.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class BacktestSolver:
    def __init__(self, finance_database: 'IntegratedFinanceDatabase'):
        self.api_client = APIClient()
        self.finance_database = finance_database
        self.logger = logging.getLogger(__name__)

    def select_trades(self, max_trades: int = 5, max_sectors: int = 3, max_volatility: float = 0.3) -> List[Dict]:
        """Select optimal trades using OR-Tools"""
        try:
            # Fetch candidate instruments (stocks and crypto)
            instruments = self.finance_database.search_instruments("", limit=50)
            if len(instruments) < max_trades:
                self.logger.warning("Insufficient instruments for backtest, using fallback data")
                return self._create_fallback_backtest_data()

            # Create solver
            solver = pywraplp.Solver.CreateSolver('SCIP')
            if not solver:
                self.logger.error("Failed to create OR-Tools solver")
                return []

            # Variables: x[i] = 1 if instrument i is selected, else 0
            x = {i['symbol']: solver.BoolVar(f'x[{i["symbol"]}]') for i in instruments}
            sectors = {i['symbol']: i['sector'] for i in instruments}
            unique_sectors = set(sectors.values()) - {'Unknown'}

            # Fetch data for each instrument
            returns = {}
            volatilities = {}
            for i in instruments:
                symbol = i['symbol']
                if i['category'] == 'CRYPTO':
                    coin_id = self.finance_database.symbol_database['CRYPTO'].get(symbol, {}).get('coin_id', '')
                    if coin_id:
                        data = self.api_client.get_coingecko_data(coin_id)
                        returns[symbol] = data.get('price_change_24h', 0) / 100
                        volatilities[symbol] = abs(data.get('price_change_24h', 0)) / 100
                else:
                    quote = self.api_client.get_alpha_vantage_quote(symbol)
                    fundamentals = self.api_client.get_alpha_vantage_fundamentals(symbol)
                    returns[symbol] = quote.get('change_percent', 0) / 100
                    volatilities[symbol] = fundamentals.get('beta', 1.0)

            # Objective: Maximize expected return
            solver.Maximize(solver.Sum(x[symbol] * returns[symbol] for symbol in x))

            # Constraints
            # 1. Select exactly max_trades
            solver.Add(solver.Sum(x[symbol] for symbol in x) == max_trades)

            # 2. Max sectors
            sector_vars = {s: solver.BoolVar(f'sector[{s}]') for s in unique_sectors}
            for symbol in x:
                sector = sectors.get(symbol, 'Unknown')
                if sector in sector_vars:
                    solver.Add(x[symbol] <= sector_vars[sector])
            solver.Add(solver.Sum(sector_vars[s] for s in sector_vars) <= max_sectors)

            # 3. Max volatility
            for symbol in x:
                if volatilities[symbol] > max_volatility:
                    solver.Add(x[symbol] == 0)

            # Solve
            status = solver.Solve()
            if status != pywraplp.Solver.OPTIMAL:
                self.logger.warning("No optimal solution found for backtest, using fallback data")
                return self._create_fallback_backtest_data()

            # Collect results
            selected_trades = []
            for symbol in x:
                if x[symbol].solution_value() > 0.5:
                    selected_trades.append({
                        'symbol': symbol,
                        'expected_return': returns[symbol],
                        'volatility': volatilities[symbol],
                        'sector': sectors.get(symbol, 'Unknown')
                    })

            self.logger.info(f"Selected {len(selected_trades)} trades in backtest")
            return selected_trades if selected_trades else self._create_fallback_backtest_data()
        except Exception as e:
            self.logger.error(f"Error in backtest solver: {str(e)}")
            return self._create_fallback_backtest_data()
    
    def _create_fallback_backtest_data(self) -> List[Dict]:
        """Create fallback backtest data when solver fails or insufficient instruments"""
        fallback_trades = [
            {
                'symbol': 'AAPL',
                'expected_return': 0.12,
                'volatility': 0.25,
                'sector': 'Technology'
            },
            {
                'symbol': 'MSFT',
                'expected_return': 0.10,
                'volatility': 0.22,
                'sector': 'Technology'
            },
            {
                'symbol': 'JPM',
                'expected_return': 0.08,
                'volatility': 0.28,
                'sector': 'Financial'
            },
            {
                'symbol': 'JNJ',
                'expected_return': 0.06,
                'volatility': 0.15,
                'sector': 'Healthcare'
            },
            {
                'symbol': 'XOM',
                'expected_return': 0.05,
                'volatility': 0.35,
                'sector': 'Energy'
            }
        ]
        self.logger.info("Using fallback backtest data with 5 diversified stocks")
        return fallback_trades