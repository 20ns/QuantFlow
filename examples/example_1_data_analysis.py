"""
Example 1: Basic Data Fetching and Analysis
This example shows how to fetch historical data and perform basic analysis
"""
import asyncio
from datetime import date, timedelta
import pandas as pd

from src.engine import QuantFlowEngine

async def main():
    print("🚀 QuantFlow Example 1: Data Fetching")
    print("=" * 50)
    
    # Initialize the engine
    engine = QuantFlowEngine()
    
    # Define symbols to analyze
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    # Define date range (last 30 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    print(f"📊 Fetching data for: {', '.join(symbols)}")
    print(f"📅 Date range: {start_date} to {end_date}")
    
    try:
        # Fetch historical data
        data = await engine.get_historical_data(symbols, start_date, end_date)
        
        if not data.empty:
            print(f"\n✅ Successfully fetched {len(data)} data points")
            
            # Analyze each symbol
            for symbol in symbols:
                symbol_data = data[data['symbol'] == symbol].copy()
                
                if not symbol_data.empty:
                    # Calculate basic statistics
                    latest_price = symbol_data['close_price'].iloc[-1]
                    price_change = symbol_data['close_price'].iloc[-1] - symbol_data['close_price'].iloc[0]
                    price_change_pct = (price_change / symbol_data['close_price'].iloc[0]) * 100
                    avg_volume = symbol_data['volume'].mean()
                    volatility = symbol_data['close_price'].std()
                    
                    print(f"\n📈 {symbol} Analysis:")
                    print(f"   Current Price: ${latest_price:.2f}")
                    print(f"   30-day Change: ${price_change:.2f} ({price_change_pct:.2f}%)")
                    print(f"   Avg Volume: {avg_volume:,.0f}")
                    print(f"   Volatility (σ): ${volatility:.2f}")
                    
                    # Technical indicators
                    if 'sma_20' in symbol_data.columns:
                        sma_20 = symbol_data['sma_20'].iloc[-1]
                        print(f"   SMA(20): ${sma_20:.2f}")
                        print(f"   Price vs SMA: {'Above' if latest_price > sma_20 else 'Below'}")
                    
                    if 'rsi' in symbol_data.columns:
                        rsi = symbol_data['rsi'].iloc[-1]
                        rsi_signal = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"
                        print(f"   RSI: {rsi:.1f} ({rsi_signal})")
        
        # Get real-time prices
        print(f"\n💹 Current Market Prices:")
        real_time_prices = await engine.get_real_time_prices(symbols)
        for symbol, price in real_time_prices.items():
            print(f"   {symbol}: ${price:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print(f"\n🏁 Example completed!")

if __name__ == "__main__":
    asyncio.run(main())
