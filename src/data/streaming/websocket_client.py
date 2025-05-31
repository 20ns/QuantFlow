"""
WebSocket client implementations for various data providers
"""
import asyncio
import json
import logging
from typing import List, Optional
from datetime import datetime
import websockets

from . import WebSocketClient, MarketDataMessage

class YahooFinanceWebSocket(WebSocketClient):
    """Yahoo Finance WebSocket client (simulated - Yahoo doesn't have public WS)"""
    
    def __init__(self, symbols: List[str]):
        super().__init__(symbols)
        self.provider = "yahoo_websocket"
        # Since Yahoo doesn't have WebSocket, we'll simulate with polling
        self.poll_interval = 1.0  # 1 second polling
    
    async def connect(self) -> bool:
        """Simulate connection for Yahoo Finance polling"""
        self.logger.info("Initializing Yahoo Finance real-time data feed (polling mode)")
        self.is_connected = True
        return True
    
    async def subscribe(self, symbols: List[str]) -> bool:
        """Subscribe to symbols"""
        self.symbols.extend([s for s in symbols if s not in self.symbols])
        self.logger.info(f"Subscribed to symbols: {', '.join(symbols)}")
        return True
    
    async def parse_message(self, message: str) -> Optional[MarketDataMessage]:
        """Parse message (not used in polling mode)"""
        return None
    
    async def start_streaming(self):
        """Start polling-based streaming for Yahoo Finance"""
        from ...providers.yahoo_finance import YahooFinanceProvider
        
        provider = YahooFinanceProvider()
        self.logger.info(f"Started Yahoo Finance streaming for: {', '.join(self.symbols)}")
        
        try:
            while self.is_connected:
                for symbol in self.symbols:
                    try:
                        # Get real-time price
                        price_data = await provider.get_real_time_price(symbol)
                        
                        message = MarketDataMessage(
                            symbol=symbol,
                            price=price_data.get('price', 0.0),
                            volume=price_data.get('volume', 0.0),
                            timestamp=datetime.now(),
                            change=price_data.get('change', 0.0),
                            change_percent=price_data.get('change_percent', 0.0),
                            provider=self.provider
                        )
                        
                        # Notify handlers
                        for handler in self.message_handlers:
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(message)
                                else:
                                    handler(message)
                            except Exception as e:
                                self.logger.error(f"Error in message handler: {e}")
                                
                    except Exception as e:
                        self.logger.error(f"Error fetching data for {symbol}: {e}")
                
                await asyncio.sleep(self.poll_interval)
                
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
        finally:
            self.is_connected = False

class AlphaVantageWebSocket(WebSocketClient):
    """Alpha Vantage WebSocket client (simulated - uses polling)"""
    
    def __init__(self, symbols: List[str], api_key: str):
        super().__init__(symbols)
        self.api_key = api_key
        self.provider = "alpha_vantage_websocket"
        self.poll_interval = 12.0  # 12 seconds (5 calls per minute limit)
    
    async def connect(self) -> bool:
        """Simulate connection for Alpha Vantage polling"""
        self.logger.info("Initializing Alpha Vantage real-time data feed (polling mode)")
        self.is_connected = True
        return True
    
    async def subscribe(self, symbols: List[str]) -> bool:
        """Subscribe to symbols"""
        self.symbols.extend([s for s in symbols if s not in self.symbols])
        self.logger.info(f"Subscribed to symbols: {', '.join(symbols)}")
        return True
    
    async def parse_message(self, message: str) -> Optional[MarketDataMessage]:
        """Parse message (not used in polling mode)"""
        return None
    
    async def start_streaming(self):
        """Start polling-based streaming for Alpha Vantage"""
        from ...providers.alpha_vantage import AlphaVantageProvider
        
        provider = AlphaVantageProvider(self.api_key)
        self.logger.info(f"Started Alpha Vantage streaming for: {', '.join(self.symbols)}")
        
        symbol_index = 0  # Rotate through symbols to respect rate limits
        
        try:
            while self.is_connected and self.symbols:
                try:
                    # Get current symbol (rotate to respect rate limits)
                    symbol = self.symbols[symbol_index % len(self.symbols)]
                    symbol_index += 1
                    
                    # Get real-time price
                    price_data = await provider.get_real_time_price(symbol)
                    
                    message = MarketDataMessage(
                        symbol=symbol,
                        price=price_data.get('price', 0.0),
                        volume=price_data.get('volume', 0.0),
                        timestamp=datetime.now(),
                        change=price_data.get('change', 0.0),
                        change_percent=price_data.get('change_percent', 0.0),
                        provider=self.provider
                    )
                    
                    # Notify handlers
                    for handler in self.message_handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(message)
                            else:
                                handler(message)
                        except Exception as e:
                            self.logger.error(f"Error in message handler: {e}")
                            
                except Exception as e:
                    self.logger.error(f"Error fetching data for {symbol}: {e}")
                
                await asyncio.sleep(self.poll_interval)
                
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
        finally:
            self.is_connected = False

class BinanceWebSocket(WebSocketClient):
    """Binance WebSocket client for crypto data"""
    
    def __init__(self, symbols: List[str]):
        super().__init__(symbols)
        self.provider = "binance"
        self.base_url = "wss://stream.binance.com:9443/ws/"
    
    async def connect(self) -> bool:
        """Connect to Binance WebSocket"""
        try:
            # Create stream name for multiple symbols
            streams = []
            for symbol in self.symbols:
                # Convert to Binance format (e.g., AAPL -> Not applicable, BTCUSDT -> btcusdt@ticker)
                if 'USDT' in symbol or 'BTC' in symbol:
                    binance_symbol = symbol.lower()
                    streams.append(f"{binance_symbol}@ticker")
            
            if not streams:
                self.logger.warning("No valid crypto symbols for Binance WebSocket")
                return False
            
            stream_url = self.base_url + '/'.join(streams)
            self.websocket = await websockets.connect(stream_url)
            self.is_connected = True
            self.logger.info(f"Connected to Binance WebSocket: {stream_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Binance WebSocket: {e}")
            return False
    
    async def subscribe(self, symbols: List[str]) -> bool:
        """Subscribe to symbols (done in connect for Binance)"""
        return True
    
    async def parse_message(self, message: str) -> Optional[MarketDataMessage]:
        """Parse Binance ticker message"""
        try:
            data = json.loads(message)
            
            if 'c' in data and 's' in data:  # Current price and symbol
                return MarketDataMessage(
                    symbol=data['s'].upper(),
                    price=float(data['c']),
                    volume=float(data.get('v', 0)),
                    timestamp=datetime.now(),
                    bid=float(data.get('b', 0)),
                    ask=float(data.get('a', 0)),
                    change=float(data.get('P', 0)),
                    change_percent=float(data.get('p', 0)),
                    provider=self.provider
                )
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"Error parsing Binance message: {e}")
        
        return None
