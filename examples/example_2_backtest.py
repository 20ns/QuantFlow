"""
Example 2: Simple Backtest
This example demonstrates how to run a backtest with the moving average strategy
"""
import asyncio
import sys
import os
from datetime import date, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import QuantFlowEngine
from src.strategies.technical.moving_average import MovingAverageCrossover

async def main():
    print("🔙 QuantFlow Example 2: Simple Backtest")
    print("=" * 50)
    
    # Initialize the engine
    engine = QuantFlowEngine()
    
    # Configure backtest parameters
    symbols = ['AAPL', 'MSFT']
    days_back = 90  # 3 months
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)
    
    print(f"🎯 Symbols: {', '.join(symbols)}")
    print(f"📅 Period: {start_date} to {end_date} ({days_back} days)")
    
    # Create and configure strategy
    strategy = MovingAverageCrossover(
        short_window=10,    # 10-day moving average
        long_window=20,     # 20-day moving average
        position_size=0.15  # 15% position size
    )
    
    print(f"🤖 Strategy: {strategy.name}")
    print(f"   Short MA: {strategy.get_parameter('short_window')} days")
    print(f"   Long MA: {strategy.get_parameter('long_window')} days")
    print(f"   Position Size: {strategy.get_parameter('position_size')*100}%")
    
    # Add strategy to engine
    engine.add_strategy(strategy)
    strategy.start()
    
    try:
        print(f"\n🚀 Running backtest...")
        
        # Run the backtest
        results = await engine.run_backtest(symbols, start_date, end_date, strategy.name)
        
        # Extract results
        metrics = results['final_metrics']
        trades = results['trades']
        portfolio = results['final_portfolio']
        
        # Display performance metrics
        print(f"\n📊 BACKTEST RESULTS")
        print(f"════════════════════")
        print(f"📈 Total Return: {metrics.get('total_return', 0):.2f}%")
        print(f"💰 Total P&L: ${metrics.get('total_return_dollars', 0):,.2f}")
        print(f"📉 Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
        print(f"⚡ Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
        print(f"🎯 Win Rate: {metrics.get('win_rate', 0):.1f}%")
        print(f"🔄 Total Trades: {metrics.get('total_trades', 0)}")
        print(f"💵 Final Cash: ${portfolio['cash']:,.2f}")
        print(f"📊 Positions Value: ${portfolio['positions_value']:,.2f}")
        
        # Show trade details
        if trades:
            print(f"\n🔄 TRADE HISTORY")
            print(f"═══════════════")
            for i, trade in enumerate(trades):
                action_emoji = "🟢" if trade['action'] == 'buy' else "🔴"
                print(f"{i+1:2d}. {action_emoji} {trade['date']} | {trade['action'].upper()} {trade['quantity']} {trade['symbol']} @ ${trade['price']:.2f}")
                if trade['reason']:
                    print(f"      💭 {trade['reason']}")
        
        # Show final positions
        if portfolio['positions']:
            print(f"\n📍 FINAL POSITIONS")
            print(f"═════════════════")
            for symbol, pos in portfolio['positions'].items():
                pnl_emoji = "🟢" if pos['unrealized_pnl'] >= 0 else "🔴"
                print(f"{pnl_emoji} {symbol}: {pos['quantity']} shares @ ${pos['avg_price']:.2f}")
                print(f"      Current: ${pos['current_price']:.2f} | P&L: ${pos['unrealized_pnl']:.2f} ({pos['unrealized_pnl_percent']:.1f}%)")
        
        # Performance analysis
        print(f"\n📈 PERFORMANCE ANALYSIS")
        print(f"═══════════════════════")
        
        # Risk-adjusted return
        annual_return = metrics.get('total_return', 0) * (365 / days_back)
        max_dd = metrics.get('max_drawdown', 0)
        calmar_ratio = annual_return / max_dd if max_dd > 0 else 0
        
        print(f"📊 Annualized Return: {annual_return:.2f}%")
        print(f"📉 Calmar Ratio: {calmar_ratio:.3f}")
        
        # Trade analysis
        if trades:
            winning_trades = [t for t in trades if 'realized_pnl' in t and t.get('realized_pnl', 0) > 0]
            losing_trades = [t for t in trades if 'realized_pnl' in t and t.get('realized_pnl', 0) < 0]
            
            if winning_trades or losing_trades:
                avg_win = sum(t.get('realized_pnl', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
                avg_loss = sum(t.get('realized_pnl', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0
                profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
                
                print(f"🎯 Average Win: ${avg_win:.2f}")
                print(f"📉 Average Loss: ${avg_loss:.2f}")
                print(f"⚖️  Profit Factor: {profit_factor:.2f}")
        
    except Exception as e:
        print(f"❌ Backtest failed: {str(e)}")
    
    print(f"\n🏁 Backtest completed!")

if __name__ == "__main__":
    asyncio.run(main())
