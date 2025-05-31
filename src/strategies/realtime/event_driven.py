"""
Event-driven strategy implementations
"""
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta
import statistics

from . import RealTimeStrategy, TradingSignal, SignalType, MarketDataMessage

class RealTimeMovingAverageCrossover(RealTimeStrategy):
    """Real-time moving average crossover strategy"""
    
    def __init__(self, symbols: List[str], fast_period: int = 10, slow_period: int = 20, position_size: float = 0.1):
        super().__init__("RealTimeMA", symbols)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.position_size = position_size
        self.min_data_points = max(fast_period, slow_period) + 5
    
    async def analyze_market_data(self, message: MarketDataMessage) -> Optional[TradingSignal]:
        """Analyze price data for moving average crossover signals"""
        symbol = message.symbol
        
        # Get recent price data
        recent_data = self.get_market_data_window(symbol, minutes=30)  # 30 minutes of data
        
        if len(recent_data) < self.min_data_points:
            return None
        
        prices = [msg.price for msg in recent_data]
        
        # Calculate moving averages
        fast_ma = statistics.mean(prices[-self.fast_period:])
        slow_ma = statistics.mean(prices[-self.slow_period:])
        
        # Previous MAs for crossover detection
        if len(prices) > max(self.fast_period, self.slow_period):
            prev_fast_ma = statistics.mean(prices[-self.fast_period-1:-1])
            prev_slow_ma = statistics.mean(prices[-self.slow_period-1:-1])
        else:
            return None
        
        # Detect crossover
        current_price = message.price
        signal_type = None
        confidence = 0.0
        reason = ""
        
        # Bullish crossover (fast MA crosses above slow MA)
        if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma:
            signal_type = SignalType.BUY
            confidence = min(0.8, abs(fast_ma - slow_ma) / slow_ma * 10)  # Higher confidence for bigger spread
            reason = f"Bullish MA crossover: Fast({fast_ma:.2f}) > Slow({slow_ma:.2f})"
        
        # Bearish crossover (fast MA crosses below slow MA)
        elif prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma:
            signal_type = SignalType.SELL
            confidence = min(0.8, abs(fast_ma - slow_ma) / slow_ma * 10)
            reason = f"Bearish MA crossover: Fast({fast_ma:.2f}) < Slow({slow_ma:.2f})"
        
        if signal_type:
            # Calculate position size
            quantity = int(10000 * self.position_size / current_price)  # $10k * position_size / price
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                quantity=max(1, quantity),
                price=current_price,
                confidence=confidence,
                timestamp=message.timestamp,
                strategy_name=self.name,
                reason=reason,
                metadata={
                    'fast_ma': fast_ma,
                    'slow_ma': slow_ma,
                    'prev_fast_ma': prev_fast_ma,
                    'prev_slow_ma': prev_slow_ma
                }
            )
        
        return None

class RealTimeMomentumStrategy(RealTimeStrategy):
    """Real-time momentum-based strategy"""
    
    def __init__(self, symbols: List[str], lookback_minutes: int = 5, momentum_threshold: float = 2.0):
        super().__init__("RealTimeMomentum", symbols)
        self.lookback_minutes = lookback_minutes
        self.momentum_threshold = momentum_threshold  # Minimum % change to trigger signal
    
    async def analyze_market_data(self, message: MarketDataMessage) -> Optional[TradingSignal]:
        """Analyze price momentum for trading signals"""
        symbol = message.symbol
        
        # Get recent price data
        recent_data = self.get_market_data_window(symbol, minutes=self.lookback_minutes)
        
        if len(recent_data) < 10:  # Need at least 10 data points
            return None
        
        prices = [msg.price for msg in recent_data]
        current_price = message.price
        
        # Calculate momentum
        start_price = prices[0]
        momentum_pct = ((current_price - start_price) / start_price) * 100
        
        # Calculate volatility for confidence
        price_changes = [
            ((prices[i] - prices[i-1]) / prices[i-1]) * 100 
            for i in range(1, len(prices))
        ]
        volatility = statistics.stdev(price_changes) if len(price_changes) > 1 else 0
        
        signal_type = None
        confidence = 0.0
        reason = ""
        
        # Strong upward momentum
        if momentum_pct > self.momentum_threshold:
            signal_type = SignalType.BUY
            confidence = min(0.9, abs(momentum_pct) / 10)  # Higher momentum = higher confidence
            reason = f"Strong upward momentum: {momentum_pct:.2f}% in {self.lookback_minutes}min"
        
        # Strong downward momentum
        elif momentum_pct < -self.momentum_threshold:
            signal_type = SignalType.SELL
            confidence = min(0.9, abs(momentum_pct) / 10)
            reason = f"Strong downward momentum: {momentum_pct:.2f}% in {self.lookback_minutes}min"
        
        # Adjust confidence based on volatility (lower volatility = higher confidence)
        if signal_type and volatility > 0:
            volatility_factor = max(0.1, 1 - (volatility / 5))  # Reduce confidence for high volatility
            confidence *= volatility_factor
        
        if signal_type and confidence > self.min_confidence_threshold:
            # Calculate position size based on momentum strength
            base_quantity = int(5000 / current_price)  # Base $5k position
            momentum_multiplier = min(2.0, abs(momentum_pct) / self.momentum_threshold)
            quantity = int(base_quantity * momentum_multiplier)
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                quantity=max(1, quantity),
                price=current_price,
                confidence=confidence,
                timestamp=message.timestamp,
                strategy_name=self.name,
                reason=reason,
                metadata={
                    'momentum_pct': momentum_pct,
                    'volatility': volatility,
                    'lookback_minutes': self.lookback_minutes,
                    'data_points': len(recent_data)
                }
            )
        
        return None

class RealTimeMeanReversionStrategy(RealTimeStrategy):
    """Real-time mean reversion strategy"""
    
    def __init__(self, symbols: List[str], window_minutes: int = 10, deviation_threshold: float = 1.5):
        super().__init__("RealTimeMeanReversion", symbols)
        self.window_minutes = window_minutes
        self.deviation_threshold = deviation_threshold  # Standard deviations from mean
    
    async def analyze_market_data(self, message: MarketDataMessage) -> Optional[TradingSignal]:
        """Analyze price for mean reversion opportunities"""
        symbol = message.symbol
        
        # Get recent price data
        recent_data = self.get_market_data_window(symbol, minutes=self.window_minutes)
        
        if len(recent_data) < 20:  # Need at least 20 data points
            return None
        
        prices = [msg.price for msg in recent_data]
        current_price = message.price
        
        # Calculate statistics
        mean_price = statistics.mean(prices)
        std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
        
        if std_dev == 0:
            return None
        
        # Calculate z-score (how many standard deviations from mean)
        z_score = (current_price - mean_price) / std_dev
        
        signal_type = None
        confidence = 0.0
        reason = ""
        
        # Price significantly below mean (oversold, expect reversion up)
        if z_score < -self.deviation_threshold:
            signal_type = SignalType.BUY
            confidence = min(0.8, abs(z_score) / 3)  # Higher deviation = higher confidence
            reason = f"Oversold condition: {z_score:.2f} std devs below mean (${mean_price:.2f})"
        
        # Price significantly above mean (overbought, expect reversion down)
        elif z_score > self.deviation_threshold:
            signal_type = SignalType.SELL
            confidence = min(0.8, abs(z_score) / 3)
            reason = f"Overbought condition: {z_score:.2f} std devs above mean (${mean_price:.2f})"
        
        if signal_type and confidence > self.min_confidence_threshold:
            # Position size based on deviation strength
            base_quantity = int(7500 / current_price)  # Base $7.5k position
            deviation_multiplier = min(1.5, abs(z_score) / self.deviation_threshold)
            quantity = int(base_quantity * deviation_multiplier)
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                quantity=max(1, quantity),
                price=current_price,
                confidence=confidence,
                timestamp=message.timestamp,
                strategy_name=self.name,
                reason=reason,
                metadata={
                    'z_score': z_score,
                    'mean_price': mean_price,
                    'std_dev': std_dev,
                    'window_minutes': self.window_minutes,
                    'data_points': len(recent_data)
                }
            )
        
        return None
