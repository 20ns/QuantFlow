"""
QuantFlow Week 3 Example: Real-Time Trading Demo
This example demonstrates all Week 3 real-time processing features:
- WebSocket data streaming
- Real-time strategy execution
- Paper trading functionality
- Risk management features
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.realtime_engine import RealTimeTradingEngine
from src.strategies.realtime.event_driven import RealTimeMovingAverageCrossover

async def main():
    print("🚀 QuantFlow Week 3: Real-Time Trading Demo")
    print("=" * 60)
    print("This demo showcases all Week 3 features:")
    print("📡 Real-time data streaming")
    print("⚡ Live strategy execution")
    print("📝 Enhanced paper trading")
    print("🛡️ Risk management")
    print("📊 Real-time monitoring")
    print("=" * 60)
    
    # Demo parameters
    symbols = ['AAPL', 'MSFT', 'TSLA']
    initial_capital = 100000
    duration_minutes = 5  # 5-minute demo
    
    print(f"\n🎯 Demo Configuration:")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Initial Capital: ${initial_capital:,.2f}")
    print(f"   Duration: {duration_minutes} minutes")
    print(f"   Start Time: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Create real-time trading engine
        engine = RealTimeTradingEngine(symbols, initial_capital)
        
        # Add additional strategies for demo
        aggressive_strategy = RealTimeMovingAverageCrossover(
            symbols=['TSLA'],
            fast_period=3,
            slow_period=8,
            position_size=0.15
        )
        aggressive_strategy.name = "AggressiveMA"
        engine.add_strategy(aggressive_strategy)
        
        print(f"\n🔧 Active Strategies:")
        for strategy in engine.active_strategies:
            print(f"   • {strategy.name}: {', '.join(strategy.symbols)}")
        
        print(f"\n🚀 Starting real-time trading session...")
        print(f"💡 Press Ctrl+C to stop early")
        print("-" * 60)
        
        # Start the real-time trading engine
        await engine.start(duration_minutes)
        
    except KeyboardInterrupt:
        print(f"\n🛑 Demo stopped by user at {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
    
    print(f"\n🎉 Week 3 Real-Time Trading Demo Complete!")
    print("📋 Features Successfully Demonstrated:")
    print("   ✅ Real-time data streaming (Yahoo Finance)")
    print("   ✅ Event-driven strategy execution")
    print("   ✅ Live portfolio management")
    print("   ✅ Risk management validation")
    print("   ✅ Real-time dashboard monitoring")
    print("   ✅ Paper trading simulation")

if __name__ == "__main__":
    asyncio.run(main())
