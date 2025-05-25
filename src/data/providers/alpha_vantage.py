"""
Alpha Vantage data provider
"""
import aiohttp
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, date
import asyncio
from .base import DataProvider

class AlphaVantageProvider(DataProvider):
    """Alpha Vantage data provider (free tier: 5 calls/minute)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.name = "alpha_vantage"
        self.base_url = "https://www.alphavantage.co/query"
        self._last_call_time = 0
        self._call_interval = 12  # 5 calls per minute = 12 seconds between calls
    
    async def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = asyncio.get_event_loop().time()
        time_since_last_call = current_time - self._last_call_time
        
        if time_since_last_call < self._call_interval:
            await asyncio.sleep(self._call_interval - time_since_last_call)
        
        self._last_call_time = asyncio.get_event_loop().time()
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        Get historical market data from Alpha Vantage
        
        Args:
            symbol: Stock symbol
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval ('1d' only for free tier)
        
        Returns:
            DataFrame with OHLCV data
        """
        await self._rate_limit()
        
        # Map interval to Alpha Vantage function
        function_map = {
            '1d': 'TIME_SERIES_DAILY',
            'daily': 'TIME_SERIES_DAILY'
        }
        
        function = function_map.get(interval, 'TIME_SERIES_DAILY')
        
        params = {
            'function': function,
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'full'  # Get full historical data
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    data = await response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                raise ValueError(f"Alpha Vantage API Error: {data['Error Message']}")
            
            if 'Note' in data:
                raise ValueError(f"Alpha Vantage Rate Limit: {data['Note']}")
            
            # Extract time series data
            time_series_key = 'Time Series (Daily)'
            if time_series_key not in data:
                raise ValueError(f"No time series data found for {symbol}")
            
            time_series = data[time_series_key]
            
            # Convert to DataFrame
            df_data = []
            for date_str, values in time_series.items():
                df_data.append({
                    'timestamp': pd.to_datetime(date_str),
                    'open_price': float(values['1. open']),
                    'high_price': float(values['2. high']),
                    'low_price': float(values['3. low']),
                    'close_price': float(values['4. close']),
                    'volume': float(values['5. volume']),
                    'symbol': symbol,
                    'provider': self.name
                })
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Filter by date range
            df = df[
                (df['timestamp'].dt.date >= start_date) & 
                (df['timestamp'].dt.date <= end_date)
            ]
            
            return df
            
        except Exception as e:
            raise Exception(f"Error fetching Alpha Vantage data for {symbol}: {str(e)}")
    
    async def get_real_time_price(self, symbol: str) -> Dict[str, float]:
        """
        Get current market price using Global Quote
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with current price data
        """
        await self._rate_limit()
        
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    data = await response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                raise ValueError(f"Alpha Vantage API Error: {data['Error Message']}")
            
            if 'Note' in data:
                raise ValueError(f"Alpha Vantage Rate Limit: {data['Note']}")
            
            quote = data.get('Global Quote', {})
            
            if not quote:
                raise ValueError(f"No quote data found for {symbol}")
            
            return {
                'symbol': symbol,
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': float(quote.get('10. change percent', '0%').replace('%', '')),
                'volume': float(quote.get('06. volume', 0)),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            raise Exception(f"Error fetching Alpha Vantage real-time price for {symbol}: {str(e)}")
    
    async def get_symbols_info(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get basic information about symbols
        Note: Alpha Vantage has limited company overview on free tier
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary with symbol information
        """
        result = {}
        
        for symbol in symbols:
            await self._rate_limit()
            
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.base_url, params=params) as response:
                        data = await response.json()
                
                if 'Error Message' in data:
                    result[symbol] = {'error': data['Error Message']}
                    continue
                
                if 'Note' in data:
                    result[symbol] = {'error': 'Rate limit exceeded'}
                    continue
                
                result[symbol] = {
                    'name': data.get('Name', symbol),
                    'sector': data.get('Sector', 'Unknown'),
                    'industry': data.get('Industry', 'Unknown'),
                    'market_cap': int(data.get('MarketCapitalization', 0)) if data.get('MarketCapitalization') else 0,
                    'currency': data.get('Currency', 'USD'),
                    'exchange': data.get('Exchange', 'Unknown')
                }
                
            except Exception as e:
                result[symbol] = {'error': str(e)}
        
        return result
