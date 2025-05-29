"""
WebSocket streaming infrastructure for real-time market data
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
import websockets
from dataclasses import dataclass

@dataclass
class MarketDataMessage:
    """Standardized market data message"""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    provider: str = "unknown"

class WebSocketClient(ABC):
    """Abstract base class for WebSocket market data clients"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.is_connected = False
        self.websocket = None
        self.message_handlers: List[Callable] = []
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to WebSocket endpoint"""
        pass
    
    @abstractmethod
    async def subscribe(self, symbols: List[str]) -> bool:
        """Subscribe to symbols"""
        pass
    
    @abstractmethod
    async def parse_message(self, message: str) -> Optional[MarketDataMessage]:
        """Parse incoming message to standardized format"""
        pass
    
    def add_message_handler(self, handler: Callable[[MarketDataMessage], None]):
        """Add handler for incoming messages"""
        self.message_handlers.append(handler)
    
    async def start_streaming(self):
        """Start streaming and handle messages"""
        if not await self.connect():
            self.logger.error("Failed to connect to WebSocket")
            return
            
        if not await self.subscribe(self.symbols):
            self.logger.error("Failed to subscribe to symbols")
            return
        
        self.logger.info(f"Started streaming for symbols: {', '.join(self.symbols)}")
        
        try:
            async for message in self.websocket:
                try:
                    parsed_message = await self.parse_message(message)
                    if parsed_message:
                        # Notify all handlers
                        for handler in self.message_handlers:
                            try:
                                await handler(parsed_message) if asyncio.iscoroutinefunction(handler) else handler(parsed_message)
                            except Exception as e:
                                self.logger.error(f"Error in message handler: {e}")
                except Exception as e:
                    self.logger.error(f"Error parsing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
        finally:
            self.is_connected = False
    
    async def stop(self):
        """Stop streaming and close connection"""
        self.is_connected = False
        if self.websocket:
            await self.websocket.close()
            self.logger.info("WebSocket connection closed")
