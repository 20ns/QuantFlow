"""
Example 3: Paper Trading Simulation
This example shows how to run a live paper trading simulation
"""
import asyncio
from datetime import datetime

from src.engine import QuantFlowEngine
from src.strategies.technical.moving_average import MovingAverageCrossover

async def main():
    print("📝 QuantFlow Example 3: Paper Trading")
    print("=" * 50)
    
    # Initialize the engine
    engine = QuantFlowEngine()
    
    # Trading parameters
    symbols = ['AAPL', 'TSLA']  # Two volatile stocks for demo
    duration_minutes = 5  # Short demo duration
    
    print(f"🎯 Symbols: {', '.join(symbols)}")
    print(f"⏱️  Duration: {duration_minutes} minutes")
    print(f"💵 Starting Capital: ${engine.portfolio.initial_cash:,.2f}")
    
    # Create and configure strategy
    strategy = MovingAverageCrossover(
        short_window=5,     # Shorter for more signals in demo
        long_window=15,     # 
        position_size=0.2   # 20% position size for more action
    )
    
    # Remove default strategies and add our custom one
    engine.strategies.clear()
    engine.add_strategy(strategy)
    strategy.start()
    
    print(f"🤖 Strategy: {strategy.name}")
    print(f"   Short MA: {strategy.get_parameter('short_window')} periods")
    print(f"   Long MA: {strategy.get_parameter('long_window')} periods")
    print(f"   Position Size: {strategy.get_parameter('position_size')*100}%")
    
    print(f"\n🔴 LIVE PAPER TRADING SIMULATION")
    print(f"Press Ctrl+C to stop early...")
    print(f"Starting at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"═" * 60)
    
    try:
        # Show initial portfolio
        portfolio = engine.get_portfolio_summary()
        print(f"💼 Initial Portfolio: ${portfolio['total_value']:,.2f}")
        
        # Get initial prices
        print(f"\n💹 Getting initial prices...")
        prices = await engine.get_real_time_prices(symbols)
        for symbol, price in prices.items():
            print(f"   {symbol}: ${price:.2f}")
        
        # Run paper trading
        await engine.run_paper_trading(symbols, duration_minutes)
        
    except KeyboardInterrupt:
        print(f"\n🛑 Simulation stopped by user at {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"❌ Error during simulation: {str(e)}")
    finally:
        # Show final results
        portfolio = engine.get_portfolio_summary()
        
        print(f"\n📊 SIMULATION RESULTS")
        print(f"════════════════════")
        print(f"🏁 End Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"💼 Final Portfolio Value: ${portfolio['total_value']:,.2f}")
        print(f"💰 Total P&L: ${portfolio['total_pnl']:,.2f}")
        print(f"📈 Return: {portfolio['total_pnl_percent']:.2f}%")
        print(f"💵 Cash: ${portfolio['cash']:,.2f}")
        print(f"📊 Positions Value: ${portfolio['positions_value']:,.2f}")
        print(f"🔢 Open Positions: {portfolio['num_positions']}")
        
        # Show positions
        if portfolio['positions']:
            print(f"\n📍 CURRENT POSITIONS")
            print(f"═══════════════════")
            for symbol, pos in portfolio['positions'].items():
                pnl_emoji = "🟢" if pos['unrealized_pnl'] >= 0 else "🔴"
                direction = "LONG" if pos['quantity'] > 0 else "SHORT"
                print(f"{pnl_emoji} {direction} {abs(pos['quantity'])} {symbol}")
                print(f"      Avg Price: ${pos['avg_price']:.2f} | Current: ${pos['current_price']:.2f}")
                print(f"      Market Value: ${pos['market_value']:,.2f}")
                print(f"      P&L: ${pos['unrealized_pnl']:,.2f} ({pos['unrealized_pnl_percent']:.1f}%)")
        
        # Show performance metrics if available
        if 'performance_metrics' in portfolio and portfolio['performance_metrics']:
            metrics = portfolio['performance_metrics']
            print(f"\n📈 PERFORMANCE METRICS")
            print(f"═════════════════════")
            if 'total_trades' in metrics:
                print(f"🔄 Total Trades: {metrics['total_trades']}")
            if 'win_rate' in metrics:
                print(f"🎯 Win Rate: {metrics['win_rate']:.1f}%")
            if 'realized_pnl' in metrics:
                print(f"💰 Realized P&L: ${metrics['realized_pnl']:,.2f}")
            if 'unrealized_pnl' in metrics:
                print(f"📊 Unrealized P&L: ${metrics['unrealized_pnl']:,.2f}")
    
    print(f"\n🏁 Paper trading simulation completed!")

if __name__ == "__main__":
    asyncio.run(main())
