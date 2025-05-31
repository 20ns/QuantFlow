"""
Main QuantFlow trading engine
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
import pandas as pd

from .config import config
from .data.providers.yahoo_finance import YahooFinanceProvider
from .data.providers.alpha_vantage import AlphaVantageProvider
from .data.storage.database import DatabaseManager, MarketData, Trade, Portfolio as PortfolioSnapshot
from .execution.portfolio import Portfolio
from .strategies.base import BaseStrategy
from .strategies.technical.moving_average import MovingAverageCrossover
from .utils.indicators import add_technical_indicators

class QuantFlowEngine:
    """Main trading engine for QuantFlow"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(config.DATABASE_URL)
        self.portfolio = Portfolio(config.INITIAL_CAPITAL)
        self.strategies: List[BaseStrategy] = []
        self.data_providers = {}
        self.is_running = False
        self.logger = self._setup_logging()
        
        # Initialize data providers
        self._initialize_data_providers()
        
        # Default strategies
        self._setup_default_strategies()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('QuantFlow')
    
    def _initialize_data_providers(self):
        """Initialize market data providers"""
        # Yahoo Finance (primary, free)
        self.data_providers['yahoo'] = YahooFinanceProvider()
        self.logger.info("Yahoo Finance provider initialized")
        
        # Alpha Vantage (secondary, rate limited)
        if config.ALPHA_VANTAGE_API_KEY and config.ALPHA_VANTAGE_API_KEY != 'demo':
            self.data_providers['alpha_vantage'] = AlphaVantageProvider(config.ALPHA_VANTAGE_API_KEY)
            self.logger.info("Alpha Vantage provider initialized")
        else:
            self.logger.warning("Alpha Vantage API key not configured, using demo key (limited functionality)")
    
    def _setup_default_strategies(self):
        """Setup default trading strategies"""
        # Add a default moving average crossover strategy
        ma_strategy = MovingAverageCrossover(short_window=10, long_window=20, position_size=0.1)
        self.add_strategy(ma_strategy)
    
    def add_strategy(self, strategy: BaseStrategy):
        """Add a trading strategy"""
        if strategy.validate_parameters():
            self.strategies.append(strategy)
            self.logger.info(f"Added strategy: {strategy.name}")
        else:
            raise ValueError(f"Invalid strategy parameters for {strategy.name}")
    
    def remove_strategy(self, strategy_name: str):
        """Remove a trading strategy"""
        self.strategies = [s for s in self.strategies if s.name != strategy_name]
        self.logger.info(f"Removed strategy: {strategy_name}")
    
    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """Get strategy by name"""
        return next((s for s in self.strategies if s.name == strategy_name), None)
    
    async def get_historical_data(
        self, 
        symbols: List[str], 
        start_date: date, 
        end_date: date, 
        provider: str = 'yahoo'
    ) -> pd.DataFrame:
        """
        Get historical market data for symbols
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for data
            end_date: End date for data
            provider: Data provider to use ('yahoo' or 'alpha_vantage')
            
        Returns:
            Combined DataFrame with historical data for all symbols
        """
        if provider not in self.data_providers:
            raise ValueError(f"Data provider '{provider}' not available")
        
        data_provider = self.data_providers[provider]
        all_data = []
        
        for symbol in symbols:
            try:
                self.logger.info(f"Fetching historical data for {symbol} from {provider}")
                symbol_data = await data_provider.get_historical_data(symbol, start_date, end_date)
                
                if not symbol_data.empty:
                    # Add technical indicators
                    symbol_data = add_technical_indicators(symbol_data)
                    all_data.append(symbol_data)
                    
                    # Store in database
                    await self._store_historical_data(symbol_data)
                    
            except Exception as e:
                self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
        
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            combined_data = combined_data.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
            return combined_data
        else:
            return pd.DataFrame()
    
    async def get_real_time_prices(self, symbols: List[str], provider: str = 'yahoo') -> Dict[str, float]:
        """
        Get real-time prices for symbols
        
        Args:
            symbols: List of stock symbols
            provider: Data provider to use
            
        Returns:
            Dictionary mapping symbol to current price
        """
        if provider not in self.data_providers:
            raise ValueError(f"Data provider '{provider}' not available")
        
        data_provider = self.data_providers[provider]
        prices = {}
        
        for symbol in symbols:
            try:
                price_data = await data_provider.get_real_time_price(symbol)
                prices[symbol] = price_data['price']
            except Exception as e:
                self.logger.error(f"Error fetching real-time price for {symbol}: {str(e)}")
        
        return prices
    
    async def _store_historical_data(self, data: pd.DataFrame):
        """Store historical data in database"""
        session = self.db_manager.get_session()
        try:
            for _, row in data.iterrows():
                market_data = MarketData(
                    symbol=row['symbol'],
                    timestamp=row['timestamp'],
                    open_price=row['open_price'],
                    high_price=row['high_price'],
                    low_price=row['low_price'],
                    close_price=row['close_price'],
                    volume=row['volume'],
                    provider=row.get('provider', 'unknown')
                )
                session.merge(market_data)  # Use merge to handle duplicates
            
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error storing historical data: {str(e)}")
        finally:
            session.close()
    
    async def run_backtest(
        self, 
        symbols: List[str], 
        start_date: date, 
        end_date: date, 
        strategy_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run backtest for strategies
        
        Args:
            symbols: List of symbols to trade
            start_date: Backtest start date
            end_date: Backtest end date
            strategy_name: Specific strategy to test (None for all)
            
        Returns:
            Backtest results
        """
        self.logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # Get historical data
        data = await self.get_historical_data(symbols, start_date, end_date)
        
        if data.empty:
            raise ValueError("No historical data available for backtest")
        
        # Reset portfolio for backtest
        backtest_portfolio = Portfolio(config.INITIAL_CAPITAL)
        
        # Get strategies to test
        strategies_to_test = []
        if strategy_name:
            strategy = self.get_strategy(strategy_name)
            if strategy:
                strategies_to_test.append(strategy)
            else:
                raise ValueError(f"Strategy '{strategy_name}' not found")
        else:
            strategies_to_test = [s for s in self.strategies if s.is_active]
        
        if not strategies_to_test:
            raise ValueError("No active strategies to test")
        
        # Run backtest day by day
        dates = sorted(data['timestamp'].dt.date.unique())
        results = {
            'start_date': start_date,
            'end_date': end_date,
            'symbols': symbols,
            'strategies_tested': [s.name for s in strategies_to_test],
            'daily_portfolio_values': [],
            'trades': [],
            'final_metrics': {}
        }
        
        for current_date in dates:
            # Get data up to current date
            historical_data = data[data['timestamp'].dt.date <= current_date]
            
            # Update portfolio with current prices
            current_day_data = data[data['timestamp'].dt.date == current_date]
            if not current_day_data.empty:
                current_prices = current_day_data.groupby('symbol')['close_price'].last().to_dict()
                backtest_portfolio.update_all_prices(current_prices)
            
            # Generate signals from all strategies
            for strategy in strategies_to_test:
                try:
                    signals = await strategy.generate_signals(historical_data, backtest_portfolio)
                    
                    # Execute signals
                    for signal in signals:
                        if signal['action'] in ['buy', 'sell']:
                            success = backtest_portfolio.execute_trade(
                                symbol=signal['symbol'],
                                quantity=signal['quantity'] if signal['action'] == 'buy' else -signal['quantity'],
                                price=signal['price'],
                                strategy_name=strategy.name,
                                timestamp=signal.get('timestamp', datetime.combine(current_date, datetime.min.time()))
                            )
                            
                            if success:
                                trade_record = {
                                    'date': current_date,
                                    'strategy': strategy.name,
                                    'symbol': signal['symbol'],
                                    'action': signal['action'],
                                    'quantity': signal['quantity'],
                                    'price': signal['price'],
                                    'reason': signal.get('reason', ''),
                                    'confidence': signal.get('confidence', 0)
                                }
                                results['trades'].append(trade_record)
                                
                except Exception as e:
                    self.logger.error(f"Error running strategy {strategy.name}: {str(e)}")
            
            # Record daily portfolio value
            results['daily_portfolio_values'].append({
                'date': current_date,
                'total_value': backtest_portfolio.total_value,
                'cash': backtest_portfolio.cash,
                'positions_value': backtest_portfolio.positions_value
            })
        
        # Calculate final metrics
        results['final_metrics'] = backtest_portfolio.get_performance_metrics()
        results['final_portfolio'] = backtest_portfolio.to_dict()
        
        self.logger.info(f"Backtest completed. Final portfolio value: ${backtest_portfolio.total_value:,.2f}")
        return results
    
    async def run_paper_trading(self, symbols: List[str], duration_minutes: int = 60):
        """
        Run paper trading simulation
        
        Args:
            symbols: List of symbols to trade
            duration_minutes: How long to run simulation
        """
        if not config.PAPER_TRADING:
            raise ValueError("Paper trading is disabled in configuration")
        
        self.logger.info(f"Starting paper trading for {duration_minutes} minutes with symbols: {symbols}")
        self.is_running = True
        
        # Start active strategies
        for strategy in self.strategies:
            if not strategy.is_active:
                strategy.start()
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        try:
            while self.is_running and datetime.now() < end_time:
                # Get current prices
                current_prices = await self.get_real_time_prices(symbols)
                
                # Update portfolio prices
                self.portfolio.update_all_prices(current_prices)
                
                # Get recent historical data for signal generation
                end_date = date.today()
                start_date = end_date - timedelta(days=30)  # 30 days of history
                historical_data = await self.get_historical_data(symbols, start_date, end_date)
                
                # Generate and execute signals
                for strategy in self.strategies:
                    if strategy.is_active:
                        try:
                            signals = await strategy.generate_signals(historical_data, self.portfolio)
                            
                            for signal in signals:
                                if signal['action'] in ['buy', 'sell']:
                                    success = self.portfolio.execute_trade(
                                        symbol=signal['symbol'],
                                        quantity=signal['quantity'] if signal['action'] == 'buy' else -signal['quantity'],
                                        price=signal['price'],
                                        strategy_name=strategy.name
                                    )
                                    
                                    if success:
                                        self.logger.info(f"Executed {signal['action']} {signal['quantity']} {signal['symbol']} @ ${signal['price']:.2f}")
                                        self.logger.info(f"Reason: {signal.get('reason', 'No reason provided')}")
                                    else:
                                        self.logger.warning(f"Failed to execute trade: {signal}")
                        
                        except Exception as e:
                            self.logger.error(f"Error in strategy {strategy.name}: {str(e)}")
                
                # Log portfolio status
                self.logger.info(f"Portfolio Value: ${self.portfolio.total_value:,.2f} | P&L: ${self.portfolio.total_pnl:,.2f} ({self.portfolio.total_pnl_percent:.2f}%)")
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("Paper trading stopped by user")
        finally:
            self.is_running = False
            # Stop all strategies
            for strategy in self.strategies:
                strategy.stop()
    
    def stop(self):
        """Stop the trading engine"""
        self.is_running = False
        for strategy in self.strategies:
            strategy.stop()
        self.logger.info("QuantFlow engine stopped")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        return self.portfolio.to_dict()
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get engine status and information"""
        return {
            'is_running': self.is_running,
            'paper_trading': config.PAPER_TRADING,
            'initial_capital': config.INITIAL_CAPITAL,
            'data_providers': list(self.data_providers.keys()),
            'strategies': [s.get_info() for s in self.strategies],
            'portfolio_summary': self.get_portfolio_summary(),
            'created_at': datetime.now().isoformat()
        }
