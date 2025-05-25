"""
Market data provider interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import pandas as pd

class DataProvider(ABC):
    """Abstract base class for market data providers"""
    
    @abstractmethod
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        interval: str = '1d'
    ) -> pd.DataFrame:
        """Get historical market data"""
        pass
    
    @abstractmethod
    async def get_real_time_price(self, symbol: str) -> Dict[str, float]:
        """Get current market price"""
        pass
    
    @abstractmethod
    async def get_symbols_info(self, symbols: List[str]) -> Dict[str, Any]:
        """Get basic information about symbols"""
        pass
