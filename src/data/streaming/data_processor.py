"""
Real-time data processor for handling streaming market data
"""
import asyncio
import logging
from collections import defaultdict, deque
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime, timedelta
import statistics

from . import MarketDataMessage

class DataProcessor:
    """Process and aggregate real-time market data"""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.price_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=buffer_size))
        self.volume_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=buffer_size))
        self.message_handlers: List[Callable] = []
        self.latest_prices: Dict[str, float] = {}
        self.price_changes: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.logger = logging.getLogger('DataProcessor')
    
    def add_handler(self, handler: Callable[[MarketDataMessage], None]):
        """Add handler for processed messages"""
        self.message_handlers.append(handler)
    
    async def process_message(self, message: MarketDataMessage):
        """Process incoming market data message"""
        try:
            symbol = message.symbol
            
            # Update latest price
            old_price = self.latest_prices.get(symbol, message.price)
            self.latest_prices[symbol] = message.price
            
            # Calculate price change
            price_change = message.price - old_price
            price_change_pct = (price_change / old_price * 100) if old_price > 0 else 0
            
            # Update price changes
            self.price_changes[symbol] = {
                'change': price_change,
                'change_percent': price_change_pct,
                'timestamp': message.timestamp
            }
            
            # Add to buffers
            self.price_buffers[symbol].append({
                'price': message.price,
                'timestamp': message.timestamp
            })
            
            self.volume_buffers[symbol].append({
                'volume': message.volume,
                'timestamp': message.timestamp
            })
            
            # Create enhanced message with calculated metrics
            enhanced_message = MarketDataMessage(
                symbol=symbol,
                price=message.price,
                volume=message.volume,
                timestamp=message.timestamp,
                bid=message.bid,
                ask=message.ask,
                change=price_change,
                change_percent=price_change_pct,
                provider=message.provider
            )
            
            # Notify handlers
            for handler in self.message_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(enhanced_message)
                    else:
                        handler(enhanced_message)
                except Exception as e:
                    self.logger.error(f"Error in message handler: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error processing message for {message.symbol}: {e}")
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for symbol"""
        return self.latest_prices.get(symbol)
    
    def get_price_change(self, symbol: str) -> Dict[str, float]:
        """Get price change information for symbol"""
        return self.price_changes.get(symbol, {})
    
    def get_price_statistics(self, symbol: str, minutes: int = 5) -> Dict[str, float]:
        """Get price statistics for the last N minutes"""
        if symbol not in self.price_buffers:
            return {}
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_prices = [
            entry['price'] for entry in self.price_buffers[symbol]
            if entry['timestamp'] >= cutoff_time
        ]
        
        if not recent_prices:
            return {}
        
        return {
            'min_price': min(recent_prices),
            'max_price': max(recent_prices),
            'avg_price': statistics.mean(recent_prices),
            'median_price': statistics.median(recent_prices),
            'price_std': statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0,
            'sample_count': len(recent_prices)
        }
    
    def get_volume_statistics(self, symbol: str, minutes: int = 5) -> Dict[str, float]:
        """Get volume statistics for the last N minutes"""
        if symbol not in self.volume_buffers:
            return {}
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_volumes = [
            entry['volume'] for entry in self.volume_buffers[symbol]
            if entry['timestamp'] >= cutoff_time
        ]
        
        if not recent_volumes:
            return {}
        
        return {
            'total_volume': sum(recent_volumes),
            'avg_volume': statistics.mean(recent_volumes),
            'max_volume': max(recent_volumes),
            'sample_count': len(recent_volumes)
        }
    
    def get_all_symbols(self) -> List[str]:
        """Get all symbols being tracked"""
        return list(self.latest_prices.keys())
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked symbols"""
        summary = {}
        for symbol in self.get_all_symbols():
            summary[symbol] = {
                'latest_price': self.get_latest_price(symbol),
                'price_change': self.get_price_change(symbol),
                'price_stats_5min': self.get_price_statistics(symbol, 5),
                'volume_stats_5min': self.get_volume_statistics(symbol, 5)
            }
        return summary
