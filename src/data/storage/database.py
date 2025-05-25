"""
Database models and schema for QuantFlow
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional
import os

Base = declarative_base()

class MarketData(Base):
    """Historical market data storage"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    provider = Column(String(50), default='yahoo')
    created_at = Column(DateTime, default=datetime.utcnow)

class Trade(Base):
    """Trade execution records"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # 'buy' or 'sell'
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    order_type = Column(String(20), default='market')
    paper_trade = Column(Boolean, default=True)
    commission = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Portfolio(Base):
    """Portfolio state snapshots"""
    __tablename__ = 'portfolio_snapshots'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    total_value = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    positions_value = Column(Float, nullable=False)
    daily_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    drawdown = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Position(Base):
    """Current position holdings"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, unique=True)
    quantity = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    market_value = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

class StrategyPerformance(Base):
    """Strategy performance metrics"""
    __tablename__ = 'strategy_performance'
    
    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    total_return = Column(Float, default=0.0)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer, default=0)
    is_backtest = Column(Boolean, default=False)
    parameters = Column(Text)  # JSON string of strategy parameters
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        # Ensure data directory exists
        if 'sqlite:///' in self.database_url:
            db_path = self.database_url.replace('sqlite:///', '')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
