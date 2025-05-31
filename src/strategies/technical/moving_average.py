"""
Simple Moving Average Crossover Strategy
"""
from typing import Dict, List, Any
import pandas as pd
from datetime import datetime

from ..base import BaseStrategy
from ...execution.portfolio import Portfolio
from ...utils.indicators import sma

class MovingAverageCrossover(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy
    
    Generates buy signals when short MA crosses above long MA
    Generates sell signals when short MA crosses below long MA
    """
    
    def __init__(self, short_window: int = 10, long_window: int = 20, position_size: float = 0.1):
        """
        Initialize Moving Average Crossover strategy
        
        Args:
            short_window: Period for short moving average
            long_window: Period for long moving average
            position_size: Position size as fraction of portfolio (0.1 = 10%)
        """
        parameters = {
            'short_window': short_window,
            'long_window': long_window,
            'position_size': position_size
        }
        super().__init__("MA_Crossover", parameters)
    
    def validate_parameters(self) -> bool:
        """Validate strategy parameters"""
        short_window = self.get_parameter('short_window')
        long_window = self.get_parameter('long_window')
        position_size = self.get_parameter('position_size')
        
        if not isinstance(short_window, int) or short_window <= 0:
            print(f"Error: short_window must be positive integer, got {short_window}")
            return False
        
        if not isinstance(long_window, int) or long_window <= 0:
            print(f"Error: long_window must be positive integer, got {long_window}")
            return False
        
        if short_window >= long_window:
            print(f"Error: short_window ({short_window}) must be less than long_window ({long_window})")
            return False
        
        if not isinstance(position_size, (int, float)) or position_size <= 0 or position_size > 1:
            print(f"Error: position_size must be between 0 and 1, got {position_size}")
            return False
        
        return True
    
    def get_required_indicators(self) -> List[str]:
        """Get required indicators for this strategy"""
        short_window = self.get_parameter('short_window', 10)
        long_window = self.get_parameter('long_window', 20)
        return [f'sma_{short_window}', f'sma_{long_window}']
    
    async def generate_signals(self, data: pd.DataFrame, portfolio: Portfolio) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on moving average crossover
        
        Args:
            data: Market data DataFrame with OHLCV columns
            portfolio: Current portfolio state
            
        Returns:
            List of trading signals
        """
        if data.empty or len(data) < self.get_parameter('long_window', 20):
            return []
        
        signals = []
        short_window = self.get_parameter('short_window', 10)
        long_window = self.get_parameter('long_window', 20)
        position_size = self.get_parameter('position_size', 0.1)
        
        # Get unique symbols in the data
        symbols = data['symbol'].unique() if 'symbol' in data.columns else ['UNKNOWN']
        
        for symbol in symbols:
            # Filter data for this symbol
            symbol_data = data[data['symbol'] == symbol].copy() if 'symbol' in data.columns else data.copy()
            
            if len(symbol_data) < long_window:
                continue
            
            # Calculate moving averages
            symbol_data[f'sma_{short_window}'] = sma(symbol_data['close_price'], short_window)
            symbol_data[f'sma_{long_window}'] = sma(symbol_data['close_price'], long_window)
            
            # Remove NaN values
            symbol_data = symbol_data.dropna()
            
            if len(symbol_data) < 2:
                continue
            
            # Get current and previous values
            current = symbol_data.iloc[-1]
            previous = symbol_data.iloc[-2]
            
            current_short_ma = current[f'sma_{short_window}']
            current_long_ma = current[f'sma_{long_window}']
            prev_short_ma = previous[f'sma_{short_window}']
            prev_long_ma = previous[f'sma_{long_window}']
            
            current_price = current['close_price']
            current_position = portfolio.get_position(symbol)
            
            # Check for crossover signals
            signal = None
            
            # Bullish crossover: short MA crosses above long MA
            if (prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma):
                if not portfolio.has_position(symbol):
                    # Calculate position size
                    max_investment = portfolio.total_value * position_size
                    quantity = int(max_investment / current_price)
                    
                    if quantity > 0 and portfolio.can_afford(symbol, quantity, current_price):
                        signal = {
                            'symbol': symbol,
                            'action': 'buy',
                            'quantity': quantity,
                            'price': current_price,
                            'confidence': 0.7,
                            'reason': f'Bullish MA crossover: SMA({short_window}) crossed above SMA({long_window})',
                            'timestamp': datetime.now()
                        }
            
            # Bearish crossover: short MA crosses below long MA
            elif (prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma):
                if portfolio.has_position(symbol) and current_position.is_long:
                    signal = {
                        'symbol': symbol,
                        'action': 'sell',
                        'quantity': current_position.quantity,
                        'price': current_price,
                        'confidence': 0.7,
                        'reason': f'Bearish MA crossover: SMA({short_window}) crossed below SMA({long_window})',
                        'timestamp': datetime.now()
                    }
            
            if signal:
                signals.append(signal)
                self.last_signal_time = datetime.now()
        
        return signals
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get detailed strategy information"""
        info = self.get_info()
        info.update({
            'description': 'Simple Moving Average Crossover Strategy',
            'logic': {
                'buy_condition': f"SMA({self.get_parameter('short_window')}) crosses above SMA({self.get_parameter('long_window')})",
                'sell_condition': f"SMA({self.get_parameter('short_window')}) crosses below SMA({self.get_parameter('long_window')})",
                'position_sizing': f"{self.get_parameter('position_size') * 100}% of portfolio value"
            },
            'risk_characteristics': {
                'trend_following': True,
                'mean_reverting': False,
                'suitable_for': ['trending markets', 'stocks', 'ETFs'],
                'not_suitable_for': ['choppy/sideways markets', 'very volatile assets']
            }
        })
        return info
