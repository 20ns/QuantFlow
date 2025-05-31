"""
Message queue system for buffering and managing real-time data streams
"""
import asyncio
import logging
from collections import deque
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

from . import MarketDataMessage

@dataclass
class QueuedMessage:
    """Wrapper for queued messages with metadata"""
    message: MarketDataMessage
    queue_time: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    priority: int = 1  # 1 = normal, 0 = high priority

class MessageQueue:
    """Async message queue for real-time data processing"""
    
    def __init__(self, max_size: int = 10000, max_age_seconds: int = 300):
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
        self.queue = asyncio.Queue(maxsize=max_size)
        self.processed_count = 0
        self.dropped_count = 0
        self.error_count = 0
        self.handlers: List[Callable] = []
        self.is_running = False
        self.logger = logging.getLogger('MessageQueue')
        
    def add_handler(self, handler: Callable[[MarketDataMessage], None]):
        """Add message handler"""
        self.handlers.append(handler)
        
    async def enqueue(self, message: MarketDataMessage, priority: int = 1) -> bool:
        """Add message to queue"""
        try:
            queued_msg = QueuedMessage(message=message, priority=priority)
            
            if self.queue.full():
                self.logger.warning("Queue is full, dropping oldest message")
                try:
                    # Try to get and drop oldest message
                    await asyncio.wait_for(self.queue.get(), timeout=0.1)
                    self.dropped_count += 1
                except asyncio.TimeoutError:
                    pass
            
            await self.queue.put(queued_msg)
            return True
            
        except Exception as e:
            self.logger.error(f"Error enqueuing message: {e}")
            self.error_count += 1
            return False
    
    async def start_processing(self):
        """Start processing messages from queue"""
        self.is_running = True
        self.logger.info("Message queue processing started")
        
        try:
            while self.is_running:
                try:
                    # Get message with timeout
                    queued_msg = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                    
                    # Check message age
                    age = (datetime.now() - queued_msg.queue_time).total_seconds()
                    if age > self.max_age_seconds:
                        self.logger.warning(f"Dropping stale message (age: {age:.1f}s)")
                        self.dropped_count += 1
                        continue
                    
                    # Process message with all handlers
                    success = True
                    for handler in self.handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(queued_msg.message)
                            else:
                                handler(queued_msg.message)
                        except Exception as e:
                            self.logger.error(f"Handler error: {e}")
                            success = False
                            self.error_count += 1
                    
                    if success:
                        self.processed_count += 1
                    else:
                        # Retry logic
                        if queued_msg.retry_count < 3:
                            queued_msg.retry_count += 1
                            await self.queue.put(queued_msg)
                        else:
                            self.logger.error("Max retries exceeded, dropping message")
                            self.dropped_count += 1
                            
                except asyncio.TimeoutError:
                    # No message available, continue
                    continue
                except Exception as e:
                    self.logger.error(f"Processing error: {e}")
                    self.error_count += 1
                    
        except Exception as e:
            self.logger.error(f"Queue processing error: {e}")
        finally:
            self.is_running = False
            self.logger.info("Message queue processing stopped")
    
    async def stop(self):
        """Stop processing messages"""
        self.is_running = False
        
        # Process remaining messages with timeout
        try:
            while not self.queue.empty():
                try:
                    queued_msg = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                    self.processed_count += 1
                except asyncio.TimeoutError:
                    break
        except Exception as e:
            self.logger.error(f"Error processing remaining messages: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            'queue_size': self.queue.qsize(),
            'max_size': self.max_size,
            'processed_count': self.processed_count,
            'dropped_count': self.dropped_count,
            'error_count': self.error_count,
            'is_running': self.is_running,
            'handler_count': len(self.handlers)
        }
    
    def clear_stats(self):
        """Reset statistics"""
        self.processed_count = 0
        self.dropped_count = 0
        self.error_count = 0

class PriorityMessageQueue(MessageQueue):
    """Priority-based message queue"""
    
    def __init__(self, max_size: int = 10000, max_age_seconds: int = 300):
        super().__init__(max_size, max_age_seconds)
        self.high_priority_queue = asyncio.Queue(maxsize=max_size // 4)
        self.normal_priority_queue = asyncio.Queue(maxsize=max_size)
    
    async def enqueue(self, message: MarketDataMessage, priority: int = 1) -> bool:
        """Add message to appropriate priority queue"""
        try:
            queued_msg = QueuedMessage(message=message, priority=priority)
            
            if priority == 0:  # High priority
                if self.high_priority_queue.full():
                    self.logger.warning("High priority queue full, dropping message")
                    self.dropped_count += 1
                    return False
                await self.high_priority_queue.put(queued_msg)
            else:  # Normal priority
                if self.normal_priority_queue.full():
                    self.logger.warning("Normal priority queue full, dropping oldest")
                    try:
                        await asyncio.wait_for(self.normal_priority_queue.get(), timeout=0.1)
                        self.dropped_count += 1
                    except asyncio.TimeoutError:
                        pass
                await self.normal_priority_queue.put(queued_msg)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error enqueuing priority message: {e}")
            self.error_count += 1
            return False
    
    async def start_processing(self):
        """Start processing with priority handling"""
        self.is_running = True
        self.logger.info("Priority message queue processing started")
        
        try:
            while self.is_running:
                try:
                    # Process high priority first
                    queued_msg = None
                    
                    try:
                        queued_msg = await asyncio.wait_for(
                            self.high_priority_queue.get(), timeout=0.1
                        )
                    except asyncio.TimeoutError:
                        # No high priority messages, try normal
                        try:
                            queued_msg = await asyncio.wait_for(
                                self.normal_priority_queue.get(), timeout=1.0
                            )
                        except asyncio.TimeoutError:
                            continue
                    
                    if queued_msg:
                        # Process message (same logic as parent class)
                        age = (datetime.now() - queued_msg.queue_time).total_seconds()
                        if age > self.max_age_seconds:
                            self.logger.warning(f"Dropping stale message (age: {age:.1f}s)")
                            self.dropped_count += 1
                            continue
                        
                        success = True
                        for handler in self.handlers:
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(queued_msg.message)
                                else:
                                    handler(queued_msg.message)
                            except Exception as e:
                                self.logger.error(f"Handler error: {e}")
                                success = False
                                self.error_count += 1
                        
                        if success:
                            self.processed_count += 1
                        else:
                            # Retry logic
                            if queued_msg.retry_count < 3:
                                queued_msg.retry_count += 1
                                await self.enqueue(
                                    queued_msg.message, 
                                    queued_msg.priority
                                )
                            else:
                                self.logger.error("Max retries exceeded")
                                self.dropped_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Priority processing error: {e}")
                    self.error_count += 1
                    
        except Exception as e:
            self.logger.error(f"Priority queue processing error: {e}")
        finally:
            self.is_running = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get priority queue statistics"""
        base_stats = super().get_stats()
        base_stats.update({
            'high_priority_size': self.high_priority_queue.qsize(),
            'normal_priority_size': self.normal_priority_queue.qsize(),
        })
        return base_stats
