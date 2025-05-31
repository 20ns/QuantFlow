"""
Configuration management for QuantFlow
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for QuantFlow"""
    
    # API Keys
    ALPHA_VANTAGE_API_KEY: str = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
    BINANCE_API_KEY: Optional[str] = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET_KEY: Optional[str] = os.getenv('BINANCE_SECRET_KEY')
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./data/quantflow.db')
      # Risk Management
    MAX_POSITION_SIZE: float = float((os.getenv('MAX_POSITION_SIZE', '0.1')).split('#')[0].strip())
    MAX_DAILY_LOSS: float = float((os.getenv('MAX_DAILY_LOSS', '0.05')).split('#')[0].strip())
    MAX_DRAWDOWN: float = float((os.getenv('MAX_DRAWDOWN', '0.15')).split('#')[0].strip())
    
    # Trading
    PAPER_TRADING: bool = (os.getenv('PAPER_TRADING', 'true')).split('#')[0].strip().lower() == 'true'
    INITIAL_CAPITAL: float = float((os.getenv('INITIAL_CAPITAL', '100000')).split('#')[0].strip())
    
    # Data refresh intervals (in seconds)
    REAL_TIME_INTERVAL: int = 1
    HISTORICAL_DATA_REFRESH: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', './logs/quantflow.log')

# Global config instance
config = Config()
