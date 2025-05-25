"""
Portfolio management for tracking overall account state
"""
from typing import Dict, List, Optional
from datetime import datetime, date
from dataclasses import dataclass, field
import pandas as pd

from .position import Position

@dataclass
class PortfolioSnapshot:
    """Snapshot of portfolio state at a point in time"""
    timestamp: datetime
    total_value: float
    cash: float
    positions_value: float
    daily_pnl: float = 0.0
    total_pnl: float = 0.0
    drawdown: float = 0.0
    peak_value: float = 0.0

class Portfolio:
    """Portfolio management class"""
    
    def __init__(self, initial_cash: float = 100000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.trades_history: List[dict] = []
        self.snapshots: List[PortfolioSnapshot] = []
        self.peak_value = initial_cash
        self.created_at = datetime.now()
        
        # Take initial snapshot
        self._take_snapshot()
    
    @property
    def total_value(self) -> float:
        """Total portfolio value (cash + positions)"""
        return self.cash + self.positions_value
    
    @property
    def positions_value(self) -> float:
        """Total value of all positions"""
        return sum(pos.market_value for pos in self.positions.values())
    
    @property
    def total_pnl(self) -> float:
        """Total profit/loss since inception"""
        return self.total_value - self.initial_cash
    
    @property
    def total_pnl_percent(self) -> float:
        """Total P&L as percentage"""
        return (self.total_pnl / self.initial_cash) * 100
    
    @property
    def unrealized_pnl(self) -> float:
        """Total unrealized P&L from open positions"""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    @property
    def realized_pnl(self) -> float:
        """Total realized P&L from closed trades"""
        return sum(trade.get('realized_pnl', 0) for trade in self.trades_history)
    
    @property
    def current_drawdown(self) -> float:
        """Current drawdown from peak"""
        if self.peak_value == 0:
            return 0.0
        return ((self.peak_value - self.total_value) / self.peak_value) * 100
    
    @property
    def num_positions(self) -> int:
        """Number of open positions"""
        return len([pos for pos in self.positions.values() if pos.quantity != 0])
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol"""
        return self.positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """Check if portfolio has position in symbol"""
        pos = self.positions.get(symbol)
        return pos is not None and pos.quantity != 0
    
    def get_position_value(self, symbol: str) -> float:
        """Get market value of position in symbol"""
        pos = self.positions.get(symbol)
        return pos.market_value if pos else 0.0
    
    def update_position_price(self, symbol: str, price: float):
        """Update market price for a position"""
        if symbol in self.positions:
            self.positions[symbol].update_price(price)
    
    def update_all_prices(self, price_data: Dict[str, float]):
        """Update prices for all positions"""
        for symbol, price in price_data.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)
    
    def can_afford(self, symbol: str, quantity: float, price: float) -> bool:
        """
        Check if portfolio can afford a trade
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares (positive for buy, negative for sell)
            price: Price per share
            
        Returns:
            True if trade is affordable
        """
        trade_value = abs(quantity * price)
        
        if quantity > 0:  # Buying
            return self.cash >= trade_value
        else:  # Selling
            pos = self.positions.get(symbol)
            if pos is None:
                return False  # Can't sell what we don't have
            return abs(quantity) <= pos.quantity
    
    def execute_trade(
        self, 
        symbol: str, 
        quantity: float, 
        price: float, 
        strategy_name: str = "manual",
        commission: float = 0.0,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Execute a trade (buy/sell)
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares (positive for buy, negative for sell)
            price: Price per share
            strategy_name: Name of strategy executing trade
            commission: Trading commission/fees
            timestamp: Trade timestamp (defaults to now)
            
        Returns:
            True if trade was executed successfully
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Check if we can afford the trade
        if not self.can_afford(symbol, quantity, price):
            return False
        
        trade_value = quantity * price
        total_cost = abs(trade_value) + commission
        
        # Update cash
        self.cash -= trade_value + commission
        
        # Update or create position
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol, 0, 0, price)
        
        old_quantity = self.positions[symbol].quantity
        self.positions[symbol].add_shares(quantity, price)
        
        # Calculate realized P&L if closing/reducing position
        realized_pnl = 0.0
        if old_quantity != 0 and (
            (old_quantity > 0 and quantity < 0) or  # Selling long
            (old_quantity < 0 and quantity > 0)     # Covering short
        ):
            # Calculate realized P&L for the portion being closed
            shares_closed = min(abs(quantity), abs(old_quantity))
            if old_quantity > 0:  # Closing long position
                realized_pnl = (price - self.positions[symbol].avg_price) * shares_closed
            else:  # Closing short position
                realized_pnl = (self.positions[symbol].avg_price - price) * shares_closed
        
        # Record trade
        trade_record = {
            'timestamp': timestamp,
            'symbol': symbol,
            'side': 'buy' if quantity > 0 else 'sell',
            'quantity': abs(quantity),
            'price': price,
            'total_value': abs(trade_value),
            'commission': commission,
            'strategy_name': strategy_name,
            'realized_pnl': realized_pnl
        }
        self.trades_history.append(trade_record)
        
        return True
    
    def close_position(self, symbol: str, price: float, strategy_name: str = "manual") -> bool:
        """
        Close entire position in a symbol
        
        Args:
            symbol: Stock symbol to close
            price: Current market price
            strategy_name: Name of strategy closing position
            
        Returns:
            True if position was closed successfully
        """
        pos = self.positions.get(symbol)
        if pos is None or pos.quantity == 0:
            return False
        
        # Execute trade to close position
        return self.execute_trade(symbol, -pos.quantity, price, strategy_name)
    
    def close_all_positions(self, price_data: Dict[str, float], strategy_name: str = "manual"):
        """
        Close all open positions
        
        Args:
            price_data: Dictionary of symbol -> current price
            strategy_name: Name of strategy closing positions
        """
        symbols_to_close = [symbol for symbol, pos in self.positions.items() if pos.quantity != 0]
        
        for symbol in symbols_to_close:
            if symbol in price_data:
                self.close_position(symbol, price_data[symbol], strategy_name)
    
    def _take_snapshot(self) -> PortfolioSnapshot:
        """Take a snapshot of current portfolio state"""
        now = datetime.now()
        
        # Calculate daily P&L (if we have previous snapshot)
        daily_pnl = 0.0
        if self.snapshots:
            last_snapshot = self.snapshots[-1]
            daily_pnl = self.total_value - last_snapshot.total_value
        
        # Update peak value
        if self.total_value > self.peak_value:
            self.peak_value = self.total_value
        
        snapshot = PortfolioSnapshot(
            timestamp=now,
            total_value=self.total_value,
            cash=self.cash,
            positions_value=self.positions_value,
            daily_pnl=daily_pnl,
            total_pnl=self.total_pnl,
            drawdown=self.current_drawdown,
            peak_value=self.peak_value
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Calculate portfolio performance metrics"""
        if len(self.snapshots) < 2:
            return {}
        
        # Get daily returns
        daily_returns = []
        for i in range(1, len(self.snapshots)):
            prev_value = self.snapshots[i-1].total_value
            curr_value = self.snapshots[i].total_value
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                daily_returns.append(daily_return)
        
        if not daily_returns:
            return {}
        
        # Calculate metrics
        returns_series = pd.Series(daily_returns)
        
        # Total return
        total_return = (self.total_value - self.initial_cash) / self.initial_cash
        
        # Sharpe ratio (assuming risk-free rate of 2% annually)
        risk_free_rate = 0.02 / 252  # Daily risk-free rate
        excess_returns = returns_series - risk_free_rate
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * (252 ** 0.5) if excess_returns.std() > 0 else 0
        
        # Maximum drawdown
        values = [snapshot.total_value for snapshot in self.snapshots]
        peak = values[0]
        max_drawdown = 0
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        # Win rate
        winning_trades = len([trade for trade in self.trades_history if trade.get('realized_pnl', 0) > 0])
        total_trades = len([trade for trade in self.trades_history if trade.get('realized_pnl') is not None])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': total_return * 100,
            'total_return_dollars': self.total_pnl,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'current_drawdown': self.current_drawdown,
            'win_rate': win_rate * 100,
            'total_trades': total_trades,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl
        }
    
    def to_dict(self) -> Dict:
        """Convert portfolio to dictionary"""
        return {
            'total_value': self.total_value,
            'cash': self.cash,
            'positions_value': self.positions_value,
            'total_pnl': self.total_pnl,
            'total_pnl_percent': self.total_pnl_percent,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'current_drawdown': self.current_drawdown,
            'num_positions': self.num_positions,
            'positions': {symbol: pos.to_dict() for symbol, pos in self.positions.items() if pos.quantity != 0},
            'performance_metrics': self.get_performance_metrics(),
            'created_at': self.created_at.isoformat()
        }
