"""
Performance Metrics Calculator for Backtesting

This module provides comprehensive performance metrics calculation including:
- Return-based metrics (total return, CAGR, volatility)
- Risk-adjusted metrics (Sharpe, Sortino, Calmar ratios)
- Drawdown analysis
- Trade-based metrics
- Benchmark comparison
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import date, timedelta
import logging

class PerformanceMetrics:
    """Calculate comprehensive performance metrics for backtesting results"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize performance metrics calculator
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
    
    def calculate_all_metrics(
        self,
        portfolio_values: pd.Series,
        trades: pd.DataFrame,
        benchmark_values: Optional[pd.Series] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calculate all performance metrics
        
        Args:
            portfolio_values: Time series of portfolio values
            trades: DataFrame with trade history
            benchmark_values: Benchmark values for comparison
            start_date: Start date of the period
            end_date: End date of the period
            
        Returns:
            Dictionary with all calculated metrics
        """
        metrics = {}
        
        # Basic return metrics
        metrics.update(self._calculate_return_metrics(portfolio_values, start_date, end_date))
        
        # Risk metrics
        metrics.update(self._calculate_risk_metrics(portfolio_values))
        
        # Drawdown metrics
        metrics.update(self._calculate_drawdown_metrics(portfolio_values))
        
        # Trade-based metrics
        if not trades.empty:
            metrics.update(self._calculate_trade_metrics(trades))
        
        # Benchmark comparison
        if benchmark_values is not None:
            metrics.update(self._calculate_benchmark_metrics(portfolio_values, benchmark_values))
        
        # Advanced risk metrics
        metrics.update(self._calculate_advanced_risk_metrics(portfolio_values))
        
        return metrics
    
    def _calculate_return_metrics(
        self, 
        portfolio_values: pd.Series,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, float]:
        """Calculate return-based metrics"""
        if portfolio_values.empty:
            return {}
        
        initial_value = portfolio_values.iloc[0]
        final_value = portfolio_values.iloc[-1]
        
        # Total return
        total_return = (final_value - initial_value) / initial_value
        
        # Calculate returns
        returns = portfolio_values.pct_change().dropna()
        
        # Annualized return (CAGR)
        if start_date and end_date:
            days = (end_date - start_date).days
            years = days / 365.25
        else:
            years = len(portfolio_values) / 252  # Approximate trading days per year
        
        if years > 0:
            annual_return = (final_value / initial_value) ** (1 / years) - 1
        else:
            annual_return = 0
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'daily_returns_mean': returns.mean(),
            'daily_returns_std': returns.std()
        }
    
    def _calculate_risk_metrics(self, portfolio_values: pd.Series) -> Dict[str, float]:
        """Calculate risk-adjusted metrics"""
        returns = portfolio_values.pct_change().dropna()
        
        if len(returns) < 2:
            return {}
        
        # Sharpe Ratio
        excess_returns = returns.mean() - (self.risk_free_rate / 252)
        sharpe_ratio = (excess_returns / returns.std() * np.sqrt(252)) if returns.std() != 0 else 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_deviation = downside_returns.std() * np.sqrt(252)
            sortino_ratio = (returns.mean() * 252 - self.risk_free_rate) / downside_deviation
        else:
            sortino_ratio = float('inf')
        
        # Information Ratio (assuming benchmark is risk-free rate)
        tracking_error = returns.std() * np.sqrt(252)
        information_ratio = (returns.mean() * 252 - self.risk_free_rate) / tracking_error if tracking_error != 0 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'information_ratio': information_ratio
        }
    
    def _calculate_drawdown_metrics(self, portfolio_values: pd.Series) -> Dict[str, float]:
        """Calculate drawdown-related metrics"""
        if portfolio_values.empty:
            return {}
        
        # Calculate running maximum
        running_max = portfolio_values.expanding().max()
        
        # Calculate drawdown
        drawdown = (portfolio_values - running_max) / running_max
        
        # Maximum drawdown
        max_drawdown = drawdown.min()
        
        # Calmar ratio (annual return / max drawdown)
        returns = portfolio_values.pct_change().dropna()
        if len(returns) > 0:
            annual_return = returns.mean() * 252
            calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        else:
            calmar_ratio = 0
        
        # Average drawdown
        negative_drawdowns = drawdown[drawdown < 0]
        avg_drawdown = negative_drawdowns.mean() if len(negative_drawdowns) > 0 else 0
        
        # Drawdown duration
        in_drawdown = drawdown < 0
        drawdown_periods = []
        current_period = 0
        
        for is_in_dd in in_drawdown:
            if is_in_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0
        
        # Add final period if still in drawdown
        if current_period > 0:
            drawdown_periods.append(current_period)
        
        max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0
        avg_drawdown_duration = np.mean(drawdown_periods) if drawdown_periods else 0
        
        return {
            'max_drawdown': max_drawdown,
            'avg_drawdown': avg_drawdown,
            'calmar_ratio': calmar_ratio,
            'max_drawdown_duration': max_drawdown_duration,
            'avg_drawdown_duration': avg_drawdown_duration,
            'num_drawdown_periods': len(drawdown_periods)
        }
    
    def _calculate_trade_metrics(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trade-based performance metrics"""
        if trades.empty:
            return {}
        
        # Ensure we have required columns
        required_cols = ['pnl', 'entry_date', 'exit_date']
        if not all(col in trades.columns for col in required_cols):
            return {}
        
        total_trades = len(trades)
        winning_trades = len(trades[trades['pnl'] > 0])
        losing_trades = len(trades[trades['pnl'] < 0])
        
        # Win rate
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = trades[trades['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(trades[trades['pnl'] < 0]['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
        
        # Average trade metrics
        avg_win = trades[trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades[trades['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        avg_trade = trades['pnl'].mean()
        
        # Trade duration
        trades_with_dates = trades.dropna(subset=['entry_date', 'exit_date'])
        if not trades_with_dates.empty:
            durations = (pd.to_datetime(trades_with_dates['exit_date']) - 
                        pd.to_datetime(trades_with_dates['entry_date'])).dt.days
            avg_trade_duration = durations.mean()
            max_trade_duration = durations.max()
        else:
            avg_trade_duration = 0
            max_trade_duration = 0
        
        # Consecutive wins/losses
        pnl_signs = np.sign(trades['pnl'].values)
        consecutive_sequences = []
        current_seq = 1
        
        for i in range(1, len(pnl_signs)):
            if pnl_signs[i] == pnl_signs[i-1]:
                current_seq += 1
            else:
                consecutive_sequences.append((pnl_signs[i-1], current_seq))
                current_seq = 1
        
        if len(pnl_signs) > 0:
            consecutive_sequences.append((pnl_signs[-1], current_seq))
        
        max_consecutive_wins = max([seq[1] for seq in consecutive_sequences if seq[0] > 0], default=0)
        max_consecutive_losses = max([seq[1] for seq in consecutive_sequences if seq[0] < 0], default=0)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_trade': avg_trade,
            'avg_trade_duration': avg_trade_duration,
            'max_trade_duration': max_trade_duration,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss
        }
    
    def _calculate_benchmark_metrics(
        self, 
        portfolio_values: pd.Series, 
        benchmark_values: pd.Series
    ) -> Dict[str, float]:
        """Calculate metrics relative to benchmark"""
        if portfolio_values.empty or benchmark_values.empty:
            return {}
        
        # Align series
        common_index = portfolio_values.index.intersection(benchmark_values.index)
        if len(common_index) < 2:
            return {}
        
        portfolio_aligned = portfolio_values.loc[common_index]
        benchmark_aligned = benchmark_values.loc[common_index]
        
        # Calculate returns
        portfolio_returns = portfolio_aligned.pct_change().dropna()
        benchmark_returns = benchmark_aligned.pct_change().dropna()
        
        if len(portfolio_returns) != len(benchmark_returns):
            return {}
        
        # Alpha and Beta
        covariance = np.cov(portfolio_returns, benchmark_returns)[0][1]
        benchmark_variance = np.var(benchmark_returns)
        
        if benchmark_variance != 0:
            beta = covariance / benchmark_variance
            alpha = portfolio_returns.mean() - beta * benchmark_returns.mean()
        else:
            beta = 0
            alpha = 0
        
        # Tracking error
        excess_returns = portfolio_returns - benchmark_returns
        tracking_error = excess_returns.std() * np.sqrt(252)
        
        # Information ratio
        info_ratio = excess_returns.mean() * 252 / tracking_error if tracking_error != 0 else 0
        
        # Up/Down capture ratios
        up_market = benchmark_returns > 0
        down_market = benchmark_returns < 0
        
        up_capture = (portfolio_returns[up_market].mean() / 
                     benchmark_returns[up_market].mean()) if up_market.any() else 0
        down_capture = (portfolio_returns[down_market].mean() / 
                       benchmark_returns[down_market].mean()) if down_market.any() else 0
        
        return {
            'alpha': alpha * 252,  # Annualized
            'beta': beta,
            'tracking_error': tracking_error,
            'information_ratio_vs_benchmark': info_ratio,
            'up_capture_ratio': up_capture,
            'down_capture_ratio': down_capture
        }
    
    def _calculate_advanced_risk_metrics(self, portfolio_values: pd.Series) -> Dict[str, float]:
        """Calculate advanced risk metrics"""
        returns = portfolio_values.pct_change().dropna()
        
        if len(returns) < 10:
            return {}
        
        # Value at Risk (VaR)
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # Conditional Value at Risk (CVaR/Expected Shortfall)
        cvar_95 = returns[returns <= var_95].mean()
        cvar_99 = returns[returns <= var_99].mean()
        
        # Skewness and Kurtosis
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        # Tail ratio
        tail_ratio = abs(np.percentile(returns, 95)) / abs(np.percentile(returns, 5))
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'tail_ratio': tail_ratio
        }
