"""
Real-Time Trading Engine - Integration of all Week 3 components
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .data.streaming.websocket_client import YahooFinanceWebSocket, AlphaVantageWebSocket
from .data.streaming.message_queue import MessageQueue
from .data.streaming.data_processor import DataProcessor
from .strategies.realtime import RealTimeStrategy
from .strategies.realtime.event_driven import RealTimeMovingAverageCrossover
from .risk import RiskManager
from .monitoring.dashboard import RealTimeDashboard
from .monitoring.metrics_tracker import MetricsTracker
from .execution.portfolio import Portfolio
from .config import config

class RealTimeTradingEngine:
    """
    Comprehensive real-time trading engine for Week 3
    Integrates streaming data, strategies, risk management, and monitoring
    """
    
    def __init__(self, symbols: List[str], initial_capital: float = 100000):
        self.symbols = symbols
        self.initial_capital = initial_capital
        
        # Core components
        self.portfolio = Portfolio(initial_capital)
        self.message_queue = MessageQueue()
        self.data_processor = DataProcessor()
        self.risk_manager = RiskManager()
        self.dashboard = RealTimeDashboard()
        self.metrics_tracker = MetricsTracker()
        
        # WebSocket clients
        self.websocket_clients = {}
        self.active_strategies: List[RealTimeStrategy] = []
        
        # Control flags
        self.is_running = False
        self.logger = self._setup_logging()
        
        # Initialize components
        self._setup_websocket_clients()
        self._setup_default_strategies()
        self._setup_message_handlers()
    
    def _setup_logging(self):
        """Setup logging for real-time engine"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('RealTimeTradingEngine')
    
    def _setup_websocket_clients(self):
        """Initialize WebSocket clients for different providers"""
        # Yahoo Finance WebSocket (polling-based)
        self.websocket_clients['yahoo'] = YahooFinanceWebSocket(self.symbols)
        
        # Alpha Vantage WebSocket (if API key available)
        if config.ALPHA_VANTAGE_API_KEY and config.ALPHA_VANTAGE_API_KEY != 'demo':
            self.websocket_clients['alpha_vantage'] = AlphaVantageWebSocket(
                self.symbols, 
                config.ALPHA_VANTAGE_API_KEY
            )
    
    def _setup_default_strategies(self):
        """Setup default real-time strategies"""
        # Real-time moving average crossover
        ma_strategy = RealTimeMovingAverageCrossover(
            symbols=self.symbols,
            fast_period=5,
            slow_period=15,
            position_size=0.1
        )
        self.add_strategy(ma_strategy)
    
    def _setup_message_handlers(self):
        """Setup message handlers for data processing"""
        # Add data processor as message handler
        for client in self.websocket_clients.values():
            client.add_message_handler(self._handle_market_data)
    
    async def _handle_market_data(self, message):
        """Handle incoming market data messages"""
        try:
            # Process through data processor
            await self.data_processor.process_message(message)
            
            # Update metrics
            self.metrics_tracker.update(f"{message.symbol}_price", message.price)
            self.metrics_tracker.update(f"{message.symbol}_volume", message.volume)
            self.metrics_tracker.update("last_data_update", datetime.now())
            
            # Send to active strategies
            for strategy in self.active_strategies:
                if message.symbol in strategy.symbols:
                    signal = await strategy.analyze_market_data(message)
                    if signal:
                        await self._handle_trading_signal(signal)
                        
        except Exception as e:
            self.logger.error(f"Error handling market data: {e}")
    
    async def _handle_trading_signal(self, signal):
        """Handle trading signals from strategies"""
        try:
            # Risk management check
            if not await self.risk_manager.validate_signal(signal, self.portfolio):
                self.logger.warning(f"Signal rejected by risk manager: {signal}")
                return
            
            # Execute trade (paper trading)
            success = self.portfolio.execute_trade(
                symbol=signal.symbol,
                quantity=signal.quantity if signal.signal_type.value == 'buy' else -signal.quantity,
                price=signal.price,
                strategy_name=signal.strategy_name
            )
            
            if success:
                self.logger.info(f"✅ Executed: {signal.signal_type.value.upper()} {signal.quantity} {signal.symbol} @ ${signal.price:.2f}")
                self.logger.info(f"   Reason: {signal.reason}")
                
                # Update metrics
                self.metrics_tracker.update("total_trades", 
                    self.metrics_tracker.get_metrics().get("total_trades", 0) + 1)
                
        except Exception as e:
            self.logger.error(f"Error handling trading signal: {e}")
    
    def add_strategy(self, strategy: RealTimeStrategy):
        """Add a real-time trading strategy"""
        self.active_strategies.append(strategy)
        self.logger.info(f"Added strategy: {strategy.name}")
    
    async def start(self, duration_minutes: int = 60):
        """Start the real-time trading engine"""
        self.logger.info(f"🚀 Starting Real-Time Trading Engine for {duration_minutes} minutes")
        self.logger.info(f"   Symbols: {', '.join(self.symbols)}")
        self.logger.info(f"   Initial Capital: ${self.initial_capital:,.2f}")
        self.logger.info(f"   Strategies: {[s.name for s in self.active_strategies]}")
        
        self.is_running = True
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        # Start WebSocket clients
        websocket_tasks = []
        for name, client in self.websocket_clients.items():
            task = asyncio.create_task(client.start_streaming())
            websocket_tasks.append(task)
            self.logger.info(f"Started {name} WebSocket client")
        
        # Start dashboard updates
        dashboard_task = asyncio.create_task(self._update_dashboard())
        
        try:
            # Main trading loop
            while self.is_running and datetime.now() < end_time:
                # Update portfolio with current prices
                await self._update_portfolio_prices()
                
                # Update risk metrics
                await self._update_risk_metrics()
                
                # Brief pause
                await asyncio.sleep(1.0)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Trading engine stopped by user")
        finally:
            await self.stop()
        
        # Show final results
        await self._show_final_results()
    
    async def _update_portfolio_prices(self):
        """Update portfolio with current market prices"""
        try:
            current_prices = {}
            for symbol in self.symbols:
                price = self.metrics_tracker.get_metrics().get(f"{symbol}_price")
                if price:
                    current_prices[symbol] = price
            
            if current_prices:
                self.portfolio.update_all_prices(current_prices)
                
        except Exception as e:
            self.logger.error(f"Error updating portfolio prices: {e}")
    
    async def _update_risk_metrics(self):
        """Update risk management metrics"""
        try:
            portfolio_value = self.portfolio.total_value
            total_pnl = self.portfolio.total_pnl
            
            self.metrics_tracker.update("portfolio_value", portfolio_value)
            self.metrics_tracker.update("total_pnl", total_pnl)
            self.metrics_tracker.update("pnl_percent", self.portfolio.total_pnl_percent)
            
        except Exception as e:
            self.logger.error(f"Error updating risk metrics: {e}")
    
    async def _update_dashboard(self):
        """Update real-time dashboard"""
        while self.is_running:
            try:
                # Get current metrics
                metrics = self.metrics_tracker.get_metrics()
                portfolio_summary = self.portfolio.to_dict()
                
                # Combine status information
                status = {
                    "🕐 Time": datetime.now().strftime("%H:%M:%S"),
                    "💼 Portfolio Value": f"${portfolio_summary.get('total_value', 0):,.2f}",
                    "📈 Total P&L": f"${portfolio_summary.get('total_pnl', 0):,.2f}",
                    "📊 P&L %": f"{portfolio_summary.get('total_pnl_percent', 0):.2f}%",
                    "💰 Cash": f"${portfolio_summary.get('cash', 0):,.2f}",
                    "📍 Positions": portfolio_summary.get('num_positions', 0),
                    "🔄 Total Trades": metrics.get("total_trades", 0),
                    "📡 Data Updates": "Active" if metrics.get("last_data_update") else "None"
                }
                
                # Add symbol prices
                for symbol in self.symbols:
                    price = metrics.get(f"{symbol}_price")
                    if price:
                        status[f"💹 {symbol}"] = f"${price:.2f}"
                
                # Display dashboard
                await self.dashboard.display_status(status)
                
                await asyncio.sleep(2.0)  # Update every 2 seconds
                
            except Exception as e:
                self.logger.error(f"Dashboard update error: {e}")
                await asyncio.sleep(5.0)
    
    async def stop(self):
        """Stop the trading engine"""
        self.logger.info("🛑 Stopping Real-Time Trading Engine...")
        self.is_running = False
        
        # Stop WebSocket clients
        for name, client in self.websocket_clients.items():
            await client.stop()
            self.logger.info(f"Stopped {name} WebSocket client")
    
    async def _show_final_results(self):
        """Show final trading results"""
        portfolio_summary = self.portfolio.to_dict()
        metrics = self.metrics_tracker.get_metrics()
        
        print("\n" + "="*60)
        print("🏁 REAL-TIME TRADING SESSION COMPLETE")
        print("="*60)
        print(f"⏰ Session End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💼 Final Portfolio Value: ${portfolio_summary['total_value']:,.2f}")
        print(f"📈 Total P&L: ${portfolio_summary['total_pnl']:,.2f} ({portfolio_summary['total_pnl_percent']:.2f}%)")
        print(f"💰 Cash Balance: ${portfolio_summary['cash']:,.2f}")
        print(f"📍 Open Positions: {portfolio_summary['num_positions']}")
        print(f"🔄 Total Trades Executed: {metrics.get('total_trades', 0)}")
        
        # Show positions
        if portfolio_summary['positions']:
            print(f"\n📍 FINAL POSITIONS:")
            print("-" * 40)
            for symbol, pos in portfolio_summary['positions'].items():
                pnl_emoji = "🟢" if pos['unrealized_pnl'] >= 0 else "🔴"
                print(f"{pnl_emoji} {symbol}: {pos['quantity']} shares @ ${pos['avg_price']:.2f}")
                print(f"    Market Value: ${pos['market_value']:,.2f}")
                print(f"    Unrealized P&L: ${pos['unrealized_pnl']:,.2f} ({pos['unrealized_pnl_percent']:.1f}%)")
        
        print("="*60)

# Helper function to run the real-time engine
async def run_realtime_demo(symbols: List[str] = None, duration_minutes: int = 5):
    """Run a real-time trading demo"""
    if symbols is None:
        symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    engine = RealTimeTradingEngine(symbols)
    await engine.start(duration_minutes)

if __name__ == "__main__":
    # Quick demo
    asyncio.run(run_realtime_demo(['AAPL', 'TSLA'], 3))
