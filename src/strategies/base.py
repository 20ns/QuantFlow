"""
Base strategy interface for all trading strategies
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

from ..execution.portfolio import Portfolio

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, name: str, parameters: Dict[str, Any] = None):
        self.name = name
        self.parameters = parameters or {}
        self.is_active = False
        self.created_at = datetime.now()
        self.last_signal_time = None
        self.performance_metrics = {}
    
    @abstractmethod
    async def generate_signals(self, data: pd.DataFrame, portfolio: Portfolio) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on market data
        
        Args:
            data: Market data DataFrame with OHLCV columns
            portfolio: Current portfolio state
            
        Returns:
            List of signal dictionaries with keys:
            - symbol: str
            - action: str ('buy', 'sell', 'hold')
            - quantity: float (number of shares)
            - confidence: float (0-1, signal strength)
            - reason: str (explanation for signal)
        """
        pass
    
    @abstractmethod
    def get_required_indicators(self) -> List[str]:
        """
        Get list of technical indicators required by this strategy
        
        Returns:
            List of indicator names (e.g., ['sma_20', 'rsi_14'])
        """
        pass
    
    def validate_parameters(self) -> bool:
        """
        Validate strategy parameters
        
        Returns:
            True if parameters are valid
        """
        return True
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get strategy parameter value"""
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any):
        """Set strategy parameter value"""
        self.parameters[key] = value
    
    def start(self):
        """Start the strategy"""
        if self.validate_parameters():
            self.is_active = True
            print(f"Strategy '{self.name}' started")
        else:
            raise ValueError(f"Invalid parameters for strategy '{self.name}'")
    
    def stop(self):
        """Stop the strategy"""
        self.is_active = False
        print(f"Strategy '{self.name}' stopped")
    
    def update_performance(self, metrics: Dict[str, float]):
        """Update strategy performance metrics"""
        self.performance_metrics.update(metrics)
    
    def get_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        return {
            'name': self.name,
            'parameters': self.parameters,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
            'performance_metrics': self.performance_metrics,
            'required_indicators': self.get_required_indicators()
        }
    
    def __str__(self) -> str:
        status = "ACTIVE" if self.is_active else "INACTIVE"
        return f"Strategy: {self.name} ({status})"
