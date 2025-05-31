"""
Technical indicators for strategy calculations
"""
import pandas as pd
import numpy as np
from typing import Union

def sma(data: pd.Series, window: int) -> pd.Series:
    """
    Simple Moving Average
    
    Args:
        data: Price series
        window: Period for moving average
        
    Returns:
        Simple moving average series
    """
    return data.rolling(window=window).mean()

def ema(data: pd.Series, window: int) -> pd.Series:
    """
    Exponential Moving Average
    
    Args:
        data: Price series
        window: Period for moving average
        
    Returns:
        Exponential moving average series
    """
    return data.ewm(span=window).mean()

def rsi(data: pd.Series, window: int = 14) -> pd.Series:
    """
    Relative Strength Index
    
    Args:
        data: Price series
        window: Period for RSI calculation
        
    Returns:
        RSI series (0-100)
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    MACD (Moving Average Convergence Divergence)
    
    Args:
        data: Price series
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line EMA period
        
    Returns:
        DataFrame with MACD, Signal, and Histogram columns
    """
    ema_fast = ema(data, fast)
    ema_slow = ema(data, slow)
    
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    })

def bollinger_bands(data: pd.Series, window: int = 20, num_std: float = 2) -> pd.DataFrame:
    """
    Bollinger Bands
    
    Args:
        data: Price series
        window: Period for moving average
        num_std: Number of standard deviations for bands
        
    Returns:
        DataFrame with upper, middle (SMA), and lower bands
    """
    sma_line = sma(data, window)
    std_dev = data.rolling(window=window).std()
    
    upper_band = sma_line + (std_dev * num_std)
    lower_band = sma_line - (std_dev * num_std)
    
    return pd.DataFrame({
        'upper': upper_band,
        'middle': sma_line,
        'lower': lower_band
    })

def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_window: int = 14, d_window: int = 3) -> pd.DataFrame:
    """
    Stochastic Oscillator
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        k_window: Period for %K calculation
        d_window: Period for %D smoothing
        
    Returns:
        DataFrame with %K and %D lines
    """
    lowest_low = low.rolling(window=k_window).min()
    highest_high = high.rolling(window=k_window).max()
    
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_window).mean()
    
    return pd.DataFrame({
        'k_percent': k_percent,
        'd_percent': d_percent
    })

def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """
    Average True Range
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        window: Period for ATR calculation
        
    Returns:
        ATR series
    """
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=window).mean()

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add commonly used technical indicators to a DataFrame
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with additional indicator columns
    """
    df = df.copy()
    
    # Moving averages
    df['sma_10'] = sma(df['close_price'], 10)
    df['sma_20'] = sma(df['close_price'], 20)
    df['sma_50'] = sma(df['close_price'], 50)
    df['ema_10'] = ema(df['close_price'], 10)
    df['ema_20'] = ema(df['close_price'], 20)
    
    # RSI
    df['rsi'] = rsi(df['close_price'])
    
    # MACD
    macd_data = macd(df['close_price'])
    df['macd'] = macd_data['macd']
    df['macd_signal'] = macd_data['signal']
    df['macd_histogram'] = macd_data['histogram']
    
    # Bollinger Bands
    bb_data = bollinger_bands(df['close_price'])
    df['bb_upper'] = bb_data['upper']
    df['bb_middle'] = bb_data['middle']
    df['bb_lower'] = bb_data['lower']
    
    # Stochastic
    stoch_data = stochastic(df['high_price'], df['low_price'], df['close_price'])
    df['stoch_k'] = stoch_data['k_percent']
    df['stoch_d'] = stoch_data['d_percent']
    
    # ATR
    df['atr'] = atr(df['high_price'], df['low_price'], df['close_price'])
    
    # Volume indicators
    df['volume_sma'] = sma(df['volume'], 20)
    
    return df
