"""
Real-time strategy framework for event-driven trading
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ...data.streaming import MarketDataMessage

class SignalType(Enum):
    """Types of trading signals"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"

@dataclass
class TradingSignal:
    """Real-time trading signal"""
    symbol: str
    signal_type: SignalType
    quantity: int
    price: float
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    strategy_name: str
    reason: str = ""
    metadata: Dict[str, Any] = None

class RealTimeStrategy(ABC):
    """Abstract base class for real-time trading strategies"""
    
    def __init__(self, name: str, symbols: List[str]):
        self.name = name
        self.symbols = symbols
        self.is_active = False
        self.position_sizes: Dict[str, int] = {}
        self.last_signals: Dict[str, TradingSignal] = {}
        self.signal_history: List[TradingSignal] = []
        self.market_data_buffer: Dict[str, List[MarketDataMessage]] = {}
        self.signal_handlers: List[Callable] = []
        self.logger = logging.getLogger(f'Strategy.{name}')
        
        # Strategy parameters
        self.max_buffer_size = 1000
        self.min_confidence_threshold = 0.5
        self.cooldown_period = timedelta(minutes=1)  # Minimum time between signals
        
    @abstractmethod
    async def analyze_market_data(self, message: MarketDataMessage) -> Optional[TradingSignal]:
        """Analyze incoming market data and generate signals"""
        pass
    
    def add_signal_handler(self, handler: Callable[[TradingSignal], None]):
        """Add handler for generated signals"""
        self.signal_handlers.append(handler)
    
    async def process_market_data(self, message: MarketDataMessage):
        """Process incoming market data"""
        if not self.is_active:
            return
            
        try:
            # Add to buffer
            symbol = message.symbol
            if symbol not in self.market_data_buffer:
                self.market_data_buffer[symbol] = []
            
            self.market_data_buffer[symbol].append(message)
            
            # Maintain buffer size
            if len(self.market_data_buffer[symbol]) > self.max_buffer_size:
                self.market_data_buffer[symbol] = self.market_data_buffer[symbol][-self.max_buffer_size:]
            
            # Generate signal
            signal = await self.analyze_market_data(message)
            
            if signal and self._should_emit_signal(signal):
                await self._emit_signal(signal)
                
        except Exception as e:
            self.logger.error(f"Error processing market data: {e}")
    
    def _should_emit_signal(self, signal: TradingSignal) -> bool:
        """Check if signal should be emitted based on filters"""
        # Check confidence threshold
        if signal.confidence < self.min_confidence_threshold:
            return False
        
        # Check cooldown period
        last_signal = self.last_signals.get(signal.symbol)
        if last_signal:
            time_since_last = signal.timestamp - last_signal.timestamp
            if time_since_last < self.cooldown_period:
                return False
        
        return True
    
    async def _emit_signal(self, signal: TradingSignal):
        """Emit trading signal to handlers"""
        try:
            self.last_signals[signal.symbol] = signal
            self.signal_history.append(signal)
            
            # Limit signal history
            if len(self.signal_history) > 1000:
                self.signal_history = self.signal_history[-1000:]
            
            self.logger.info(f"Generated signal: {signal.signal_type.value} {signal.quantity} {signal.symbol} @ ${signal.price:.2f} (confidence: {signal.confidence:.2f})")
            
            # Notify handlers
            for handler in self.signal_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(signal)
                    else:
                        handler(signal)
                except Exception as e:
                    self.logger.error(f"Error in signal handler: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error emitting signal: {e}")
    
    def start(self):
        """Start the strategy"""
        self.is_active = True
        self.logger.info(f"Strategy {self.name} started for symbols: {', '.join(self.symbols)}")
    
    def stop(self):
        """Stop the strategy"""
        self.is_active = False
        self.logger.info(f"Strategy {self.name} stopped")
    
    def get_market_data_window(self, symbol: str, minutes: int = 5) -> List[MarketDataMessage]:
        """Get market data for the last N minutes"""
        if symbol not in self.market_data_buffer:
            return []
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            msg for msg in self.market_data_buffer[symbol]
            if msg.timestamp >= cutoff_time
        ]
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for symbol"""
        if symbol in self.market_data_buffer and self.market_data_buffer[symbol]:
            return self.market_data_buffer[symbol][-1].price
        return None
    
    def get_price_change(self, symbol: str, minutes: int = 5) -> Optional[float]:
        """Get price change over N minutes"""
        window_data = self.get_market_data_window(symbol, minutes)
        if len(window_data) < 2:
            return None
        
        old_price = window_data[0].price
        new_price = window_data[-1].price
        return ((new_price - old_price) / old_price) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """Get strategy statistics"""
        return {
            'name': self.name,
            'is_active': self.is_active,
            'symbols': self.symbols,
            'total_signals': len(self.signal_history),
            'buffer_sizes': {sym: len(buf) for sym, buf in self.market_data_buffer.items()},
            'last_signal_times': {
                sym: signal.timestamp.isoformat() 
                for sym, signal in self.last_signals.items()
            }
        }
