"""
Risk management system for real-time trading
"""
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..strategies.realtime import TradingSignal, SignalType
from ..data.streaming import MarketDataMessage

class RiskLevel(Enum):
    """Risk levels for positions and portfolio"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RiskMetrics:
    """Risk metrics for positions and portfolio"""
    position_risk: float  # Risk per position (0.0 to 1.0)
    portfolio_risk: float  # Overall portfolio risk
    max_drawdown: float  # Maximum drawdown percentage
    var_1day: float  # 1-day Value at Risk
    concentration_risk: float  # Position concentration risk
    risk_level: RiskLevel
    timestamp: datetime

class PositionSizer:
    """Dynamic position sizing based on risk parameters"""
    
    def __init__(self, max_position_size: float = 0.25, max_portfolio_risk: float = 0.15):
        self.max_position_size = max_position_size  # Max 25% per position
        self.max_portfolio_risk = max_portfolio_risk  # Max 15% portfolio risk
        self.kelly_multiplier = 0.25  # Conservative Kelly fraction
        self.logger = logging.getLogger('PositionSizer')
    
    def calculate_position_size(
        self, 
        signal: TradingSignal, 
        portfolio_value: float,
        current_positions: Dict[str, Any],
        volatility: float = 0.02
    ) -> int:
        """Calculate optimal position size based on risk parameters"""
        
        try:
            # Base position size
            base_size = portfolio_value * self.max_position_size / signal.price
            
            # Adjust for signal confidence
            confidence_adjusted = base_size * signal.confidence
            
            # Adjust for volatility (higher volatility = smaller position)
            volatility_factor = max(0.1, 1 - (volatility * 10))
            volatility_adjusted = confidence_adjusted * volatility_factor
            
            # Check portfolio concentration
            symbol_exposure = self._calculate_symbol_exposure(signal.symbol, current_positions, portfolio_value)
            if symbol_exposure > self.max_position_size:
                concentration_factor = max(0.1, (self.max_position_size * 2 - symbol_exposure) / self.max_position_size)
                volatility_adjusted *= concentration_factor
            
            # Apply Kelly criterion for growth optimization
            win_rate = 0.55  # Assume 55% win rate (could be dynamic)
            avg_win = 0.02   # Assume 2% average win (could be dynamic)
            avg_loss = 0.015 # Assume 1.5% average loss (could be dynamic)
            
            kelly_fraction = ((win_rate * avg_win) - ((1 - win_rate) * avg_loss)) / avg_win
            kelly_adjusted = volatility_adjusted * kelly_fraction * self.kelly_multiplier
            
            final_quantity = max(1, int(kelly_adjusted))
            
            self.logger.debug(f"Position sizing for {signal.symbol}: base={base_size:.0f}, final={final_quantity}")
            
            return final_quantity
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            # Return minimal position on error
            return max(1, int(portfolio_value * 0.01 / signal.price))
    
    def _calculate_symbol_exposure(self, symbol: str, positions: Dict[str, Any], portfolio_value: float) -> float:
        """Calculate current exposure to a symbol"""
        if symbol not in positions:
            return 0.0
        
        position = positions[symbol]
        position_value = abs(position.get('quantity', 0)) * position.get('current_price', 0)
        return position_value / portfolio_value

class StopLossManager:
    """Automated stop-loss and take-profit management"""
    
    def __init__(self, default_stop_pct: float = 0.05, default_target_pct: float = 0.10):
        self.default_stop_pct = default_stop_pct  # 5% stop loss
        self.default_target_pct = default_target_pct  # 10% take profit
        self.trailing_stops: Dict[str, Dict] = {}  # Trailing stop data
        self.logger = logging.getLogger('StopLossManager')
    
    def set_stop_loss(
        self, 
        symbol: str, 
        entry_price: float, 
        signal_type: SignalType,
        stop_pct: Optional[float] = None,
        target_pct: Optional[float] = None
    ):
        """Set stop loss and take profit for a position"""
        
        stop_pct = stop_pct or self.default_stop_pct
        target_pct = target_pct or self.default_target_pct
        
        if signal_type == SignalType.BUY:
            stop_price = entry_price * (1 - stop_pct)
            target_price = entry_price * (1 + target_pct)
        else:  # SELL/SHORT
            stop_price = entry_price * (1 + stop_pct)
            target_price = entry_price * (1 - target_pct)
        
        self.trailing_stops[symbol] = {
            'entry_price': entry_price,
            'stop_price': stop_price,
            'target_price': target_price,
            'signal_type': signal_type,
            'stop_pct': stop_pct,
            'target_pct': target_pct,
            'highest_price': entry_price if signal_type == SignalType.BUY else entry_price,
            'lowest_price': entry_price if signal_type == SignalType.SELL else entry_price,
            'created_at': datetime.now()
        }
        
        self.logger.info(f"Set stop loss for {symbol}: stop=${stop_price:.2f}, target=${target_price:.2f}")
    
    def check_stop_conditions(self, message: MarketDataMessage) -> Optional[TradingSignal]:
        """Check if stop loss or take profit should be triggered"""
        
        symbol = message.symbol
        if symbol not in self.trailing_stops:
            return None
        
        stop_data = self.trailing_stops[symbol]
        current_price = message.price
        signal_type = stop_data['signal_type']
        
        # Update trailing prices
        if signal_type == SignalType.BUY:
            stop_data['highest_price'] = max(stop_data['highest_price'], current_price)
            # Update trailing stop (only move up for long positions)
            trailing_stop = stop_data['highest_price'] * (1 - stop_data['stop_pct'])
            stop_data['stop_price'] = max(stop_data['stop_price'], trailing_stop)
        else:  # SHORT position
            stop_data['lowest_price'] = min(stop_data['lowest_price'], current_price)
            # Update trailing stop (only move down for short positions)
            trailing_stop = stop_data['lowest_price'] * (1 + stop_data['stop_pct'])
            stop_data['stop_price'] = min(stop_data['stop_price'], trailing_stop)
        
        # Check stop loss
        if ((signal_type == SignalType.BUY and current_price <= stop_data['stop_price']) or
            (signal_type == SignalType.SELL and current_price >= stop_data['stop_price'])):
            
            # Remove stop data
            del self.trailing_stops[symbol]
            
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.SELL if signal_type == SignalType.BUY else SignalType.BUY,
                quantity=0,  # Will be set by position manager
                price=current_price,
                confidence=1.0,  # High confidence for risk management
                timestamp=message.timestamp,
                strategy_name="StopLossManager",
                reason=f"Stop loss triggered at ${current_price:.2f} (stop: ${stop_data['stop_price']:.2f})",
                metadata=stop_data
            )
        
        # Check take profit
        if ((signal_type == SignalType.BUY and current_price >= stop_data['target_price']) or
            (signal_type == SignalType.SELL and current_price <= stop_data['target_price'])):
            
            # Remove stop data
            del self.trailing_stops[symbol]
            
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.SELL if signal_type == SignalType.BUY else SignalType.BUY,
                quantity=0,  # Will be set by position manager
                price=current_price,
                confidence=1.0,
                timestamp=message.timestamp,
                strategy_name="StopLossManager",
                reason=f"Take profit triggered at ${current_price:.2f} (target: ${stop_data['target_price']:.2f})",
                metadata=stop_data
            )
        
        return None
    
    def remove_stop(self, symbol: str):
        """Remove stop loss for a symbol"""
        if symbol in self.trailing_stops:
            del self.trailing_stops[symbol]
            self.logger.info(f"Removed stop loss for {symbol}")
    
    def get_stops(self) -> Dict[str, Dict]:
        """Get all active stops"""
        return self.trailing_stops.copy()

class PortfolioRiskManager:
    """Portfolio-level risk management"""
    
    def __init__(
        self, 
        max_portfolio_drawdown: float = 0.15,
        max_daily_loss: float = 0.05,
        max_position_count: int = 10
    ):
        self.max_portfolio_drawdown = max_portfolio_drawdown  # 15% max drawdown
        self.max_daily_loss = max_daily_loss  # 5% max daily loss
        self.max_position_count = max_position_count
        
        self.daily_start_value = 0.0
        self.portfolio_high_water_mark = 0.0
        self.risk_handlers: List[Callable] = []
        self.logger = logging.getLogger('PortfolioRiskManager')
    
    def add_risk_handler(self, handler: Callable[[RiskMetrics], None]):
        """Add handler for risk events"""
        self.risk_handlers.append(handler)
    
    def check_portfolio_risk(
        self, 
        current_portfolio_value: float,
        positions: Dict[str, Any],
        daily_start_value: Optional[float] = None
    ) -> RiskMetrics:
        """Check portfolio-level risk metrics"""
        
        if daily_start_value:
            self.daily_start_value = daily_start_value
        
        # Update high water mark
        self.portfolio_high_water_mark = max(self.portfolio_high_water_mark, current_portfolio_value)
        
        # Calculate drawdown
        if self.portfolio_high_water_mark > 0:
            drawdown = (self.portfolio_high_water_mark - current_portfolio_value) / self.portfolio_high_water_mark
        else:
            drawdown = 0.0
        
        # Calculate daily P&L
        if self.daily_start_value > 0:
            daily_pnl_pct = (current_portfolio_value - self.daily_start_value) / self.daily_start_value
        else:
            daily_pnl_pct = 0.0
        
        # Calculate concentration risk
        position_values = [
            abs(pos.get('quantity', 0)) * pos.get('current_price', 0)
            for pos in positions.values()
        ]
        
        if position_values and current_portfolio_value > 0:
            max_position_pct = max(position_values) / current_portfolio_value
            concentration_risk = max_position_pct
        else:
            concentration_risk = 0.0
        
        # Calculate overall portfolio risk
        portfolio_risk = max(drawdown, abs(daily_pnl_pct), concentration_risk)
        
        # Simple VaR calculation (assume 2% daily volatility)
        var_1day = current_portfolio_value * 0.02 * 1.65  # 95% confidence
        
        # Determine risk level
        if portfolio_risk > 0.10 or drawdown > 0.10:
            risk_level = RiskLevel.CRITICAL
        elif portfolio_risk > 0.05 or drawdown > 0.05:
            risk_level = RiskLevel.HIGH
        elif portfolio_risk > 0.025:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        metrics = RiskMetrics(
            position_risk=concentration_risk,
            portfolio_risk=portfolio_risk,
            max_drawdown=drawdown,
            var_1day=var_1day,
            concentration_risk=concentration_risk,
            risk_level=risk_level,
            timestamp=datetime.now()
        )
        
        # Check risk limits
        if drawdown > self.max_portfolio_drawdown:
            self.logger.warning(f"Portfolio drawdown exceeded: {drawdown:.2%} > {self.max_portfolio_drawdown:.2%}")
            self._notify_risk_handlers(metrics)
        
        if abs(daily_pnl_pct) > self.max_daily_loss:
            self.logger.warning(f"Daily loss exceeded: {daily_pnl_pct:.2%} > {self.max_daily_loss:.2%}")
            self._notify_risk_handlers(metrics)
        
        if len(positions) > self.max_position_count:
            self.logger.warning(f"Position count exceeded: {len(positions)} > {self.max_position_count}")
        
        return metrics
    
    def _notify_risk_handlers(self, metrics: RiskMetrics):
        """Notify risk handlers of risk events"""
        for handler in self.risk_handlers:
            try:
                handler(metrics)
            except Exception as e:
                self.logger.error(f"Error in risk handler: {e}")
    
    def should_halt_trading(self, metrics: RiskMetrics) -> bool:
        """Determine if trading should be halted due to risk"""
        return (
            metrics.risk_level == RiskLevel.CRITICAL or
            metrics.max_drawdown > self.max_portfolio_drawdown or
            abs(metrics.portfolio_risk) > self.max_daily_loss
        )
