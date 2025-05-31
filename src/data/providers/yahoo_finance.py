"""
Yahoo Finance data provider
"""
import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, date
import asyncio
from .base import DataProvider

class YahooFinanceProvider(DataProvider):
    """Yahoo Finance data provider (free tier)"""
    
    def __init__(self):
        self.name = "yahoo_finance"
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        Get historical market data from Yahoo Finance
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval ('1d', '1h', '5m', etc.)
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, 
                self._fetch_historical_data, 
                symbol, start_date, end_date, interval
            )
            
            if data.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            # Standardize column names
            data = data.rename(columns={
                'Open': 'open_price',
                'High': 'high_price',
                'Low': 'low_price',
                'Close': 'close_price',
                'Volume': 'volume'
            })
            
            # Add metadata
            data['symbol'] = symbol
            data['provider'] = self.name
            data.reset_index(inplace=True)
            data = data.rename(columns={'Date': 'timestamp'})
            
            return data
            
        except Exception as e:
            raise Exception(f"Error fetching data for {symbol}: {str(e)}")
    
    def _fetch_historical_data(self, symbol: str, start_date: date, end_date: date, interval: str) -> pd.DataFrame:
        """Synchronous data fetch for executor"""
        ticker = yf.Ticker(symbol)
        data = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval
        )
        return data
    
    async def get_real_time_price(self, symbol: str) -> Dict[str, float]:
        """
        Get current market price
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with current price data
        """
        try:
            loop = asyncio.get_event_loop()
            ticker_data = await loop.run_in_executor(
                None, 
                self._fetch_real_time_price, 
                symbol
            )
            
            return {
                'symbol': symbol,
                'price': float(ticker_data.get('regularMarketPrice', 0)),
                'change': float(ticker_data.get('regularMarketChange', 0)),
                'change_percent': float(ticker_data.get('regularMarketChangePercent', 0)),
                'volume': float(ticker_data.get('regularMarketVolume', 0)),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            raise Exception(f"Error fetching real-time price for {symbol}: {str(e)}")
    
    def _fetch_real_time_price(self, symbol: str) -> Dict:
        """Synchronous price fetch for executor"""
        ticker = yf.Ticker(symbol)
        return ticker.info
    
    async def get_symbols_info(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get basic information about symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary with symbol information
        """
        result = {}
        
        for symbol in symbols:
            try:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(
                    None, 
                    self._fetch_symbol_info, 
                    symbol
                )
                result[symbol] = info
                
            except Exception as e:
                result[symbol] = {'error': str(e)}
        
        return result
    
    def _fetch_symbol_info(self, symbol: str) -> Dict:
        """Synchronous symbol info fetch for executor"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            'name': info.get('longName', symbol),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'currency': info.get('currency', 'USD'),
            'exchange': info.get('exchange', 'Unknown')
        }
