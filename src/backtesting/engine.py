"""
Enhanced Backtesting Engine with Historical Replay

This module provides a sophisticated backtesting framework that can:
- Replay historical data tick-by-tick or daily
- Support multiple strategies simultaneously
- Calculate comprehensive performance metrics
- Handle realistic trading constraints and costs
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
import logging
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

@dataclass
class BacktestConfig:
    """Configuration for backtesting"""
    initial_capital: float = 100000.0
    commission: float = 0.001  # 0.1% commission
    slippage: float = 0.0005   # 0.05% slippage
    max_position_size: float = 0.25  # 25% max position
    allow_short_selling: bool = False
    rebalance_frequency: str = 'daily'  # 'daily', 'weekly', 'monthly'
    benchmark_symbol: str = 'SPY'  # Benchmark for comparison
    risk_free_rate: float = 0.02  # 2% annual risk-free rate

@dataclass  
class BacktestResult:
    """Results from a backtest run"""
    strategy_name: str
    start_date: date
    end_date: date
    initial_capital: float
    final_value: float
    total_return: float
    annual_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: float
    portfolio_history: pd.DataFrame = field(default_factory=pd.DataFrame)
    trade_history: pd.DataFrame = field(default_factory=pd.DataFrame)
    metrics: Dict[str, Any] = field(default_factory=dict)

class BacktestEngine:
    """
    Advanced backtesting engine with historical replay capabilities
    """
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.logger = logging.getLogger(__name__)
        
    def run_backtest(
        self,
        strategy,
        data: pd.DataFrame,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        symbols: Optional[List[str]] = None
    ) -> BacktestResult:
        """
        Run a comprehensive backtest
        
        Args:
            strategy: Strategy instance to test
            data: Historical market data
            start_date: Start date for backtest
            end_date: End date for backtest  
            symbols: List of symbols to trade
            
        Returns:
            BacktestResult with comprehensive metrics
        """
        self.logger.info(f"Starting backtest for strategy: {strategy.name}")
        
        # Prepare data
        if start_date:
            data = data[data['timestamp'].dt.date >= start_date]
        if end_date:
            data = data[data['timestamp'].dt.date <= end_date]
        if symbols:
            data = data[data['symbol'].isin(symbols)]
            
        if data.empty:
            raise ValueError("No data available for backtesting")
        
        # Initialize tracking variables
        portfolio_value = self.config.initial_capital
        cash = self.config.initial_capital
        positions = {}  # symbol -> {'quantity': int, 'avg_price': float}
        portfolio_history = []
        trade_history = []
        
        # Get unique dates for iteration
        dates = sorted(data['timestamp'].dt.date.unique())
        
        # Historical replay - day by day
        for current_date in dates:
            # Get data up to current date
            historical_data = data[data['timestamp'].dt.date <= current_date]
            current_day_data = data[data['timestamp'].dt.date == current_date]
            
            if current_day_data.empty:
                continue
                
            # Update current prices for portfolio valuation
            current_prices = {}
            for symbol in current_day_data['symbol'].unique():
                symbol_data = current_day_data[current_day_data['symbol'] == symbol]
                current_prices[symbol] = symbol_data['close_price'].iloc[-1]
            
            # Calculate portfolio value
            positions_value = sum(
                pos['quantity'] * current_prices.get(symbol, 0)
                for symbol, pos in positions.items()
            )
            portfolio_value = cash + positions_value
            
            # Generate signals from strategy
            try:
                signals = strategy.generate_signals(historical_data, {
                    'cash': cash,
                    'positions': positions,
                    'portfolio_value': portfolio_value
                })
                
                # Execute signals
                for signal in signals:
                    trade_result = self._execute_trade(
                        signal, cash, positions, current_prices, current_date
                    )
                    
                    if trade_result:
                        cash = trade_result['new_cash']
                        positions = trade_result['new_positions']
                        trade_history.append(trade_result['trade_record'])
                        
            except Exception as e:
                self.logger.warning(f"Error generating signals for {current_date}: {e}")
            
            # Record daily portfolio state
            portfolio_history.append({
                'date': current_date,
                'portfolio_value': portfolio_value,
                'cash': cash,
                'positions_value': positions_value,
                'num_positions': len(positions)
            })
        
        # Calculate final metrics
        result = self._calculate_results(
            strategy.name,
            dates[0] if dates else start_date,
            dates[-1] if dates else end_date,
            portfolio_history,
            trade_history
        )
        
        self.logger.info(f"Backtest completed. Final return: {result.total_return:.2f}%")
        return result
    
    def _execute_trade(
        self,
        signal: Dict[str, Any],
        cash: float,
        positions: Dict[str, Dict],
        current_prices: Dict[str, float],
        trade_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a trade signal with realistic constraints
        
        Returns:
            Dictionary with updated cash, positions, and trade record
        """
        symbol = signal['symbol']
        action = signal['action']
        
        if symbol not in current_prices:
            return None
            
        price = current_prices[symbol]
        
        # Apply slippage
        if action == 'buy':
            execution_price = price * (1 + self.config.slippage)
        else:
            execution_price = price * (1 - self.config.slippage)
        
        # Determine quantity
        if 'quantity' in signal:
            quantity = signal['quantity']
        else:
            # Calculate quantity based on position size
            position_size = signal.get('position_size', 0.1)
            if action == 'buy':
                max_value = cash * position_size
                quantity = int(max_value / execution_price)
            else:
                quantity = positions.get(symbol, {}).get('quantity', 0)
        
        if quantity <= 0:
            return None
        
        # Calculate trade value and commission
        trade_value = quantity * execution_price
        commission = trade_value * self.config.commission
        
        # Execute trade
        new_cash = cash
        new_positions = positions.copy()
        
        if action == 'buy':
            total_cost = trade_value + commission
            if total_cost <= cash:
                new_cash -= total_cost
                
                if symbol in new_positions:
                    # Update existing position
                    old_qty = new_positions[symbol]['quantity']
                    old_avg = new_positions[symbol]['avg_price']
                    new_qty = old_qty + quantity
                    new_avg = ((old_qty * old_avg) + trade_value) / new_qty
                    
                    new_positions[symbol] = {
                        'quantity': new_qty,
                        'avg_price': new_avg
                    }
                else:
                    # New position
                    new_positions[symbol] = {
                        'quantity': quantity,
                        'avg_price': execution_price
                    }
            else:
                return None  # Insufficient funds
                
        elif action == 'sell':
            if symbol in new_positions and new_positions[symbol]['quantity'] >= quantity:
                new_cash += trade_value - commission
                new_positions[symbol]['quantity'] -= quantity
                
                if new_positions[symbol]['quantity'] == 0:
                    del new_positions[symbol]
            else:
                return None  # Insufficient shares
        
        # Create trade record
        trade_record = {
            'date': trade_date,
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': execution_price,
            'value': trade_value,
            'commission': commission,
            'strategy': signal.get('strategy', 'Unknown'),
            'reason': signal.get('reason', ''),
            'confidence': signal.get('confidence', 0.0)
        }
        
        return {
            'new_cash': new_cash,
            'new_positions': new_positions,
            'trade_record': trade_record
        }
    
    def _calculate_results(
        self,
        strategy_name: str,
        start_date: date,
        end_date: date,
        portfolio_history: List[Dict],
        trade_history: List[Dict]
    ) -> BacktestResult:
        """Calculate comprehensive backtest results"""
        
        if not portfolio_history:
            return BacktestResult(
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.config.initial_capital,
                final_value=self.config.initial_capital,
                total_return=0.0,
                annual_return=0.0,
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                calmar_ratio=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                total_trades=0,
                avg_trade_duration=0.0
            )
        
        # Convert to DataFrames
        portfolio_df = pd.DataFrame(portfolio_history)
        portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
        portfolio_df = portfolio_df.set_index('date')
        
        trade_df = pd.DataFrame(trade_history) if trade_history else pd.DataFrame()
        
        # Basic metrics
        initial_value = self.config.initial_capital
        final_value = portfolio_df['portfolio_value'].iloc[-1]
        total_return = ((final_value - initial_value) / initial_value) * 100
        
        # Time-based metrics
        days = (end_date - start_date).days
        years = days / 365.25
        annual_return = ((final_value / initial_value) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        # Risk metrics
        daily_returns = portfolio_df['portfolio_value'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100  # Annualized
        
        # Sharpe ratio
        excess_returns = daily_returns - (self.config.risk_free_rate / 252)
        sharpe_ratio = (excess_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + daily_returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        # Calmar ratio
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Trade metrics
        total_trades = len(trade_df)
        win_rate = 0.0
        profit_factor = 0.0
        avg_trade_duration = 0.0
        
        if not trade_df.empty and 'action' in trade_df.columns:
            # Calculate P&L for completed trades
            buy_trades = trade_df[trade_df['action'] == 'buy'].copy()
            sell_trades = trade_df[trade_df['action'] == 'sell'].copy()
            
            completed_trades = []
            for symbol in buy_trades['symbol'].unique():
                symbol_buys = buy_trades[buy_trades['symbol'] == symbol].sort_values('date')
                symbol_sells = sell_trades[sell_trades['symbol'] == symbol].sort_values('date')
                
                # Match buys and sells (FIFO)
                buy_queue = []
                for _, buy in symbol_buys.iterrows():
                    buy_queue.append(buy)
                
                for _, sell in symbol_sells.iterrows():
                    sell_qty = sell['quantity']
                    while sell_qty > 0 and buy_queue:
                        buy = buy_queue[0]
                        trade_qty = min(sell_qty, buy['quantity'])
                        
                        pnl = (sell['price'] - buy['price']) * trade_qty
                        duration = (sell['date'] - buy['date']).days
                        
                        completed_trades.append({
                            'symbol': symbol,
                            'pnl': pnl,
                            'duration': duration,
                            'buy_date': buy['date'],
                            'sell_date': sell['date']
                        })
                        
                        buy['quantity'] -= trade_qty
                        sell_qty -= trade_qty
                        
                        if buy['quantity'] <= 0:
                            buy_queue.pop(0)
            
            if completed_trades:
                trade_pnls = [t['pnl'] for t in completed_trades]
                winning_trades = [pnl for pnl in trade_pnls if pnl > 0]
                losing_trades = [pnl for pnl in trade_pnls if pnl < 0]
                
                win_rate = len(winning_trades) / len(trade_pnls) * 100
                
                if losing_trades:
                    avg_win = np.mean(winning_trades) if winning_trades else 0
                    avg_loss = abs(np.mean(losing_trades))
                    profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf')
                
                avg_trade_duration = np.mean([t['duration'] for t in completed_trades])
        
        return BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_value,
            final_value=final_value,
            total_return=total_return,
            annual_return=annual_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            avg_trade_duration=avg_trade_duration,
            portfolio_history=portfolio_df,
            trade_history=trade_df,
            metrics={
                'days_traded': days,
                'years': years,
                'total_commission': trade_df['commission'].sum() if not trade_df.empty else 0,
                'avg_daily_return': daily_returns.mean() * 100,
                'return_std': daily_returns.std() * 100,
                'best_day': daily_returns.max() * 100,
                'worst_day': daily_returns.min() * 100
            }
        )
    
    def run_multiple_backtests(
        self,
        strategies: List,
        data: pd.DataFrame,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        parallel: bool = True
    ) -> Dict[str, BacktestResult]:
        """
        Run backtests for multiple strategies
        
        Args:
            strategies: List of strategy instances
            data: Historical market data
            start_date: Start date for backtests
            end_date: End date for backtests
            parallel: Whether to run strategies in parallel
            
        Returns:
            Dictionary mapping strategy names to results
        """
        results = {}
        
        if parallel:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(
                        self.run_backtest, strategy, data, start_date, end_date
                    ): strategy.name
                    for strategy in strategies
                }
                
                for future in futures:
                    try:
                        result = future.result()
                        results[futures[future]] = result
                    except Exception as e:
                        self.logger.error(f"Strategy {futures[future]} failed: {e}")
        else:
            for strategy in strategies:
                try:
                    result = self.run_backtest(strategy, data, start_date, end_date)
                    results[strategy.name] = result
                except Exception as e:
                    self.logger.error(f"Strategy {strategy.name} failed: {e}")
        
        return results
