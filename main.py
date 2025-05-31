"""
Command-line interface for QuantFlow
"""
import click
import asyncio
from datetime import date, datetime, timedelta
import json
from typing import List

from src.engine import QuantFlowEngine
from src.strategies.technical.moving_average import MovingAverageCrossover
from src.realtime_engine import RealTimeTradingEngine

@click.group()
def cli():
    """QuantFlow - Algorithmic Trading Engine"""
    click.echo("🚀 QuantFlow - Your Personal Algorithmic Trading System")

@cli.command()
@click.option('--symbols', '-s', multiple=True, required=True, help='Stock symbols to trade (e.g., AAPL MSFT)')
@click.option('--days', '-d', default=30, help='Number of days of historical data to fetch')
@click.option('--provider', '-p', default='yahoo', type=click.Choice(['yahoo', 'alpha_vantage']), help='Data provider')
def fetch_data(symbols: tuple, days: int, provider: str):
    """Fetch historical market data"""
    async def _fetch_data():
        engine = QuantFlowEngine()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        click.echo(f"📊 Fetching {days} days of data for {', '.join(symbols)} from {provider}...")
        
        try:
            data = await engine.get_historical_data(list(symbols), start_date, end_date, provider)
            
            if not data.empty:
                click.echo(f"✅ Successfully fetched {len(data)} data points")
                click.echo(f"📈 Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
                
                # Show sample data
                click.echo("\n📋 Sample data:")
                for symbol in symbols:
                    symbol_data = data[data['symbol'] == symbol]
                    if not symbol_data.empty:
                        latest = symbol_data.iloc[-1]
                        click.echo(f"  {symbol}: ${latest['close_price']:.2f} (Volume: {latest['volume']:,})")
            else:
                click.echo("❌ No data fetched")
                
        except Exception as e:
            click.echo(f"❌ Error: {str(e)}")
    
    asyncio.run(_fetch_data())

@cli.command()
@click.option('--symbols', '-s', multiple=True, required=True, help='Stock symbols to backtest')
@click.option('--days', '-d', default=90, help='Number of days to backtest')
@click.option('--strategy', default='MA_Crossover', help='Strategy name to test')
@click.option('--short-ma', default=10, help='Short moving average period')
@click.option('--long-ma', default=20, help='Long moving average period')
@click.option('--position-size', default=0.1, type=float, help='Position size (0.1 = 10%)')
def backtest(symbols: tuple, days: int, strategy: str, short_ma: int, long_ma: int, position_size: float):
    """Run backtest on historical data"""
    async def _backtest():
        engine = QuantFlowEngine()
        
        # Configure strategy
        if strategy == 'MA_Crossover':
            ma_strategy = MovingAverageCrossover(short_ma, long_ma, position_size)
            engine.add_strategy(ma_strategy)
            ma_strategy.start()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        click.echo(f"🔙 Running backtest for {days} days on {', '.join(symbols)}")
        click.echo(f"📊 Strategy: {strategy} (Short MA: {short_ma}, Long MA: {long_ma})")
        click.echo(f"💰 Position Size: {position_size*100}%")
        click.echo(f"📅 Period: {start_date} to {end_date}")
        
        try:
            results = await engine.run_backtest(list(symbols), start_date, end_date, strategy)
            
            # Display results
            metrics = results['final_metrics']
            trades = results['trades']
            
            click.echo(f"\n📈 BACKTEST RESULTS")
            click.echo(f"════════════════════")
            click.echo(f"Total Return: {metrics.get('total_return', 0):.2f}%")
            click.echo(f"Total P&L: ${metrics.get('total_return_dollars', 0):,.2f}")
            click.echo(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
            click.echo(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
            click.echo(f"Win Rate: {metrics.get('win_rate', 0):.1f}%")
            click.echo(f"Total Trades: {metrics.get('total_trades', 0)}")
            
            if trades:
                click.echo(f"\n🔄 TRADE SUMMARY")
                click.echo(f"═══════════════")
                for trade in trades[-5:]:  # Show last 5 trades
                    click.echo(f"{trade['date']} | {trade['action'].upper()} {trade['quantity']} {trade['symbol']} @ ${trade['price']:.2f}")
                
                if len(trades) > 5:
                    click.echo(f"... and {len(trades) - 5} more trades")
            
        except Exception as e:
            click.echo(f"❌ Backtest failed: {str(e)}")
    
    asyncio.run(_backtest())

@cli.command()
@click.option('--symbols', '-s', multiple=True, required=True, help='Stock symbols to trade')
@click.option('--duration', '-t', default=60, help='Duration in minutes')
@click.option('--strategy', default='MA_Crossover', help='Strategy to use')
def paper_trade(symbols: tuple, duration: int, strategy: str):
    """Run paper trading simulation"""
    async def _paper_trade():
        engine = QuantFlowEngine()
        
        # Start strategies
        for strat in engine.strategies:
            if strat.name == strategy:
                strat.start()
        
        click.echo(f"📝 Starting paper trading simulation")
        click.echo(f"🎯 Symbols: {', '.join(symbols)}")
        click.echo(f"⏱️  Duration: {duration} minutes")
        click.echo(f"🤖 Strategy: {strategy}")
        click.echo(f"💵 Starting Capital: ${engine.portfolio.initial_cash:,.2f}")
        click.echo(f"\n🟢 Simulation started... Press Ctrl+C to stop early")
        
        try:
            await engine.run_paper_trading(list(symbols), duration)
        except KeyboardInterrupt:
            click.echo("\n🛑 Simulation stopped by user")
        finally:
            # Show final results
            portfolio = engine.get_portfolio_summary()
            click.echo(f"\n📊 FINAL RESULTS")
            click.echo(f"═══════════════")
            click.echo(f"Final Value: ${portfolio['total_value']:,.2f}")
            click.echo(f"Total P&L: ${portfolio['total_pnl']:,.2f} ({portfolio['total_pnl_percent']:.2f}%)")
            click.echo(f"Cash: ${portfolio['cash']:,.2f}")
            click.echo(f"Positions Value: ${portfolio['positions_value']:,.2f}")
            click.echo(f"Open Positions: {portfolio['num_positions']}")
    
    asyncio.run(_paper_trade())

@cli.command()
@click.option('--symbols', '-s', multiple=True, required=True, help='Stock symbols to check')
def prices(symbols: tuple):
    """Get real-time stock prices"""
    async def _get_prices():
        engine = QuantFlowEngine()
        
        click.echo(f"💹 Getting current prices for {', '.join(symbols)}...")
        
        try:
            prices = await engine.get_real_time_prices(list(symbols))
            
            click.echo(f"\n📈 CURRENT PRICES")
            click.echo(f"═════════════════")
            for symbol, price in prices.items():
                click.echo(f"{symbol}: ${price:.2f}")
                
        except Exception as e:
            click.echo(f"❌ Error: {str(e)}")
    
    asyncio.run(_get_prices())

@cli.command()
def status():
    """Show QuantFlow engine status"""
    engine = QuantFlowEngine()
    status = engine.get_engine_status()
    
    click.echo(f"🎛️  QUANTFLOW STATUS")
    click.echo(f"══════════════════")
    click.echo(f"Running: {'🟢 Yes' if status['is_running'] else '🔴 No'}")
    click.echo(f"Paper Trading: {'🟢 Enabled' if status['paper_trading'] else '🔴 Disabled'}")
    click.echo(f"Initial Capital: ${status['initial_capital']:,.2f}")
    click.echo(f"Data Providers: {', '.join(status['data_providers'])}")
    
    click.echo(f"\n🤖 STRATEGIES ({len(status['strategies'])})")
    click.echo(f"═══════════════")
    for strategy in status['strategies']:
        status_icon = "🟢" if strategy['is_active'] else "🔴"
        click.echo(f"{status_icon} {strategy['name']}")
    
    portfolio = status['portfolio_summary']
    click.echo(f"\n💼 PORTFOLIO")
    click.echo(f"═══════════")
    click.echo(f"Total Value: ${portfolio['total_value']:,.2f}")
    click.echo(f"Cash: ${portfolio['cash']:,.2f}")
    click.echo(f"Positions: {portfolio['num_positions']}")
    click.echo(f"P&L: ${portfolio['total_pnl']:,.2f} ({portfolio['total_pnl_percent']:.2f}%)")

@cli.command()
@click.option('--symbols', '-s', multiple=True, default=['AAPL', 'MSFT', 'GOOGL'], help='Stock symbols for real-time trading')
@click.option('--duration', '-d', default=10, help='Duration in minutes for real-time session')
@click.option('--capital', '-c', default=100000, help='Initial capital for paper trading')
def realtime(symbols: tuple, duration: int, capital: float):
    """Start real-time trading session (Week 3 feature)"""
    async def _start_realtime():
        click.echo(f"🚀 Starting Real-Time Trading Session")
        click.echo(f"═══════════════════════════════════")
        click.echo(f"Symbols: {', '.join(symbols)}")
        click.echo(f"Duration: {duration} minutes")
        click.echo(f"Capital: ${capital:,.2f}")
        click.echo(f"Start: {datetime.now().strftime('%H:%M:%S')}")
        click.echo(f"\n💡 Press Ctrl+C to stop early\n")
        
        try:
            engine = RealTimeTradingEngine(list(symbols), capital)
            await engine.start(duration)
        except KeyboardInterrupt:
            click.echo(f"\n🛑 Session stopped by user")
        except Exception as e:
            click.echo(f"❌ Error: {str(e)}")
    
    asyncio.run(_start_realtime())

@cli.command()
@click.option('--symbols', '-s', multiple=True, default=['AAPL', 'MSFT'], help='Symbols to stream')
@click.option('--duration', '-d', default=5, help='Duration in minutes')
def stream(symbols: tuple, duration: int):
    """Stream real-time price data (Week 3 feature)"""
    async def _stream_data():
        from src.data.streaming.websocket_client import YahooFinanceWebSocket
        
        click.echo(f"📡 Streaming real-time data for {', '.join(symbols)}")
        click.echo(f"Duration: {duration} minutes")
        click.echo(f"Press Ctrl+C to stop\n")
        
        def price_handler(message):
            timestamp = message.timestamp.strftime('%H:%M:%S')
            change_emoji = "🟢" if message.change >= 0 else "🔴"
            click.echo(f"{timestamp} | {change_emoji} {message.symbol}: ${message.price:.2f} "
                      f"({message.change:+.2f}, {message.change_percent:+.2f}%)")
        
        try:
            client = YahooFinanceWebSocket(list(symbols))
            client.add_message_handler(price_handler)
            
            # Start streaming with timeout
            await asyncio.wait_for(client.start_streaming(), timeout=duration*60)
            
        except asyncio.TimeoutError:
            click.echo(f"\n⏰ Streaming completed after {duration} minutes")
        except KeyboardInterrupt:
            click.echo(f"\n🛑 Streaming stopped by user")
        except Exception as e:
            click.echo(f"❌ Error: {str(e)}")
    
    asyncio.run(_stream_data())

if __name__ == '__main__':
    cli()
