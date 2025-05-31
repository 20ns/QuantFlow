"""
Position management for individual holdings
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Position:
    """Represents a single position in a security"""
    symbol: str
    quantity: float
    avg_price: float
    current_price: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    @property
    def market_value(self) -> float:
        """Current market value of the position"""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Total cost basis of the position"""
        return abs(self.quantity) * self.avg_price
    
    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss"""
        if self.quantity > 0:  # Long position
            return (self.current_price - self.avg_price) * self.quantity
        else:  # Short position
            return (self.avg_price - self.current_price) * abs(self.quantity)
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Unrealized P&L as percentage"""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100
    
    @property
    def is_long(self) -> bool:
        """True if long position"""
        return self.quantity > 0
    
    @property
    def is_short(self) -> bool:
        """True if short position"""
        return self.quantity < 0
    
    def update_price(self, new_price: float):
        """Update current market price"""
        self.current_price = new_price
        self.last_updated = datetime.now()
    
    def add_shares(self, quantity: float, price: float):
        """
        Add shares to position (buy more or cover short)
        Updates average price using weighted average
        """
        if self.quantity == 0:
            # Opening new position
            self.quantity = quantity
            self.avg_price = price
        elif (self.quantity > 0 and quantity > 0) or (self.quantity < 0 and quantity < 0):
            # Adding to existing position (same direction)
            total_cost = (self.quantity * self.avg_price) + (quantity * price)
            self.quantity += quantity
            self.avg_price = total_cost / self.quantity
        else:
            # Reducing position (opposite direction)
            self.quantity += quantity
            # Don't update avg_price when reducing position
        
        self.last_updated = datetime.now()
    
    def close_position(self) -> float:
        """
        Close the entire position
        
        Returns:
            Realized P&L from closing
        """
        realized_pnl = self.unrealized_pnl
        self.quantity = 0
        self.last_updated = datetime.now()
        return realized_pnl
    
    def to_dict(self) -> dict:
        """Convert position to dictionary"""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'avg_price': self.avg_price,
            'current_price': self.current_price,
            'market_value': self.market_value,
            'cost_basis': self.cost_basis,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_percent': self.unrealized_pnl_percent,
            'is_long': self.is_long,
            'is_short': self.is_short,
            'last_updated': self.last_updated.isoformat()
        }
    
    def __str__(self) -> str:
        direction = "LONG" if self.is_long else "SHORT"
        return f"{direction} {abs(self.quantity)} {self.symbol} @ ${self.avg_price:.2f} (Current: ${self.current_price:.2f}, P&L: ${self.unrealized_pnl:.2f})"
