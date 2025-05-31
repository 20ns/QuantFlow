"""
Enhanced CLI Interface for QuantFlow Week 2 Backtesting Features

This module provides a comprehensive command-line interface for:
- Running advanced backtests with performance metrics
- Parameter optimization (grid search, random search, Bayesian)
- Walk-forward analysis and Monte Carlo testing
- Generating comprehensive reports
"""

import click
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import json
import os
import sys
import logging
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backtesting.engine import BacktestEngine, BacktestConfig
from src.backtesting.metrics import PerformanceMetrics
from src.backtesting.optimizer import ParameterOptimizer, ParameterSpace
from src.backtesting.reporter import BacktestReporter
from src.data.providers.yahoo_finance import YahooFinanceProvider
from src.strategies.technical.moving_average import MovingAverageCrossover
from src.engine import QuantFlowEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """QuantFlow Week 2 - Advanced Backtesting CLI"""
    click.echo("🚀 QuantFlow Week 2 - Advanced Backtesting Engine")
    click.echo("=" * 50)

@cli.command()
@click.option('--symbol', '-s', default='AAPL', help='Stock symbol to backtest')
@click.option('--start-date', '-sd', default='2023-01-01', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-ed', default='2024-01-01', help='End date (YYYY-MM-DD)')
@click.option('--initial-capital', '-ic', default=100000, help='Initial capital')
@click.option('--fast-period', '-fp', default=10, help='Fast MA period')
@click.option('--slow-period', '-sp', default=30, help='Slow MA period')
@click.option('--commission', '-c', default=0.001, help='Commission rate')
@click.option('--generate-report', '-r', is_flag=True, help='Generate HTML report')
def backtest(symbol, start_date, end_date, initial_capital, fast_period, slow_period, commission, generate_report):
    """Run advanced backtest with comprehensive metrics"""
    click.echo(f"📊 Running Advanced Backtest for {symbol}")
    
    try:
        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
          # Setup data provider
        provider = YahooFinanceProvider()
        click.echo(f"📈 Fetching historical data for {symbol}...")
        
        data = asyncio.run(provider.get_historical_data(symbol, start_dt, end_dt))
        if data.empty:
            click.echo("❌ No data available for the specified period")
            return
        
        click.echo(f"✅ Retrieved {len(data)} data points")
        
        # Setup backtest configuration
        config = BacktestConfig(
            initial_capital=initial_capital,
            commission=commission,
            slippage=0.0005,
            max_position_size=0.25
        )
          # Create strategy
        strategy = MovingAverageCrossover(
            short_window=fast_period,
            long_window=slow_period
        )
        
        # Run backtest
        engine = BacktestEngine(config)
        click.echo("🔄 Running backtest...")
        
        result = engine.run_backtest(strategy, data, start_dt, end_dt, [symbol])
        
        # Display results
        click.echo("\\n" + "=" * 60)
        click.echo("📈 BACKTEST RESULTS")
        click.echo("=" * 60)
        click.echo(f"Strategy: {result.strategy_name}")
        click.echo(f"Period: {result.start_date} to {result.end_date}")
        click.echo(f"Initial Capital: ${result.initial_capital:,.2f}")
        click.echo(f"Final Value: ${result.final_value:,.2f}")
        click.echo(f"Total Return: {result.total_return:.2f}%")
        click.echo(f"Annual Return: {result.annual_return:.2f}%")
        click.echo(f"Volatility: {result.volatility:.2f}%")
        click.echo(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        click.echo(f"Max Drawdown: {result.max_drawdown:.2f}%")
        click.echo(f"Calmar Ratio: {result.calmar_ratio:.2f}")
        click.echo(f"Win Rate: {result.win_rate:.2f}%")
        click.echo(f"Total Trades: {result.total_trades}")
        click.echo("=" * 60)
        
        # Generate report if requested
        if generate_report:
            click.echo("\\n📝 Generating comprehensive report...")
            reporter = BacktestReporter()
            report_files = reporter.generate_full_report(result, strategy.name)
            
            click.echo("✅ Report generated!")
            for report_type, file_path in report_files.items():
                click.echo(f"  {report_type}: {file_path}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Backtest error: {e}", exc_info=True)

@cli.command()
@click.option('--symbol', '-s', default='AAPL', help='Stock symbol to optimize')
@click.option('--start-date', '-sd', default='2023-01-01', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-ed', default='2024-01-01', help='End date (YYYY-MM-DD)')
@click.option('--method', '-m', type=click.Choice(['grid', 'random', 'bayesian']), default='grid', help='Optimization method')
@click.option('--metric', default='sharpe_ratio', help='Optimization metric')
@click.option('--iterations', '-i', default=50, help='Number of iterations (for random/bayesian)')
@click.option('--fast-min', default=5, help='Fast period minimum')
@click.option('--fast-max', default=20, help='Fast period maximum')
@click.option('--slow-min', default=20, help='Slow period minimum')
@click.option('--slow-max', default=50, help='Slow period maximum')
@click.option('--parallel', '-p', is_flag=True, help='Use parallel processing')
def optimize(symbol, start_date, end_date, method, metric, iterations, fast_min, fast_max, slow_min, slow_max, parallel):
    """Optimize strategy parameters using various methods"""
    click.echo(f"🔧 Optimizing Parameters for {symbol} using {method.upper()}")
    
    try:
        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Setup data provider
        provider = YahooFinanceProvider()
        click.echo(f"📈 Fetching historical data...")
        
        data = asyncio.run(provider.get_historical_data(symbol, start_dt, end_dt))
        if data.empty:
            click.echo("❌ No data available for the specified period")
            return
        
        # Setup parameter space
        param_space = ParameterSpace()
        param_space.add_parameter('fast_period', 'integer', (fast_min, fast_max))
        param_space.add_parameter('slow_period', 'integer', (slow_min, slow_max))
        param_space.add_parameter('symbol', 'choice', [symbol])
        
        # Create optimizer
        optimizer = ParameterOptimizer()
        
        click.echo(f"🔄 Running {method} optimization...")
        
        if method == 'grid':
            result = optimizer.grid_search(
                MovingAverageCrossover,
                param_space,
                data,
                optimization_metric=metric,
                n_jobs=4 if parallel else 1,
                start_date=start_dt,
                end_date=end_dt
            )
        elif method == 'random':
            result = optimizer.random_search(
                MovingAverageCrossover,
                param_space,
                data,
                n_iterations=iterations,
                optimization_metric=metric,
                n_jobs=4 if parallel else 1,
                start_date=start_dt,
                end_date=end_dt
            )
        elif method == 'bayesian':
            result = optimizer.bayesian_optimization(
                MovingAverageCrossover,
                param_space,
                data,
                n_calls=iterations,
                optimization_metric=metric,
                start_date=start_dt,
                end_date=end_dt
            )
        
        # Display results
        click.echo("\\n" + "=" * 60)
        click.echo("🏆 OPTIMIZATION RESULTS")
        click.echo("=" * 60)
        click.echo(f"Method: {method.upper()}")
        click.echo(f"Optimization Metric: {metric}")
        
        if 'best_parameters' in result:
            click.echo(f"Best Parameters: {result['best_parameters']}")
            click.echo(f"Best {metric}: {result['best_metric_value']:.4f}")
            
            if 'optimization_statistics' in result:
                stats = result['optimization_statistics']
                click.echo(f"Total Combinations Tested: {stats['total_combinations']}")
                click.echo(f"Success Rate: {stats['success_rate']:.2%}")
                click.echo(f"Metric Range: {stats['metric_min']:.4f} to {stats['metric_max']:.4f}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"optimization_{symbol}_{method}_{timestamp}.json"
        
        with open(result_file, 'w') as f:
            # Convert any non-serializable objects
            serializable_result = {}
            for key, value in result.items():
                if key == 'best_backtest_result':
                    if value:
                        serializable_result[key] = {
                            'total_return': value.total_return,
                            'sharpe_ratio': value.sharpe_ratio,
                            'max_drawdown': value.max_drawdown
                        }
                else:
                    serializable_result[key] = value
            
            json.dump(serializable_result, f, indent=2, default=str)
        
        click.echo(f"💾 Results saved to: {result_file}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Optimization error: {e}", exc_info=True)

@cli.command()
@click.option('--symbol', '-s', default='AAPL', help='Stock symbol to analyze')
@click.option('--start-date', '-sd', default='2022-01-01', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-ed', default='2024-01-01', help='End date (YYYY-MM-DD)')
@click.option('--fast-period', '-fp', default=10, help='Fast MA period')
@click.option('--slow-period', '-sp', default=30, help='Slow MA period')
@click.option('--optimization-window', '-ow', default=252, help='Optimization window (days)')
@click.option('--test-window', '-tw', default=63, help='Test window (days)')
@click.option('--step-size', '-ss', default=21, help='Step size (days)')
def walkforward(symbol, start_date, end_date, fast_period, slow_period, optimization_window, test_window, step_size):
    """Perform walk-forward analysis"""
    click.echo(f"🚶 Running Walk-Forward Analysis for {symbol}")
    
    try:
        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Setup data provider
        provider = YahooFinanceProvider()
        click.echo(f"📈 Fetching historical data...")
        
        data = asyncio.run(provider.get_historical_data(symbol, start_dt, end_dt))
        if data.empty:
            click.echo("❌ No data available for the specified period")
            return
        
        # Setup optimizer
        optimizer = ParameterOptimizer()
        
        # Best parameters (in practice, these would come from optimization)
        best_params = {
            'fast_period': fast_period,
            'slow_period': slow_period,
            'symbol': symbol
        }
        
        click.echo(f"🔄 Running walk-forward analysis...")
        click.echo(f"  Optimization Window: {optimization_window} days")
        click.echo(f"  Test Window: {test_window} days")
        click.echo(f"  Step Size: {step_size} days")
        
        result = optimizer.walk_forward_analysis(
            MovingAverageCrossover,
            best_params,
            data,
            optimization_window=optimization_window,
            test_window=test_window,
            step_size=step_size
        )
        
        # Display results
        click.echo("\\n" + "=" * 60)
        click.echo("📊 WALK-FORWARD ANALYSIS RESULTS")
        click.echo("=" * 60)
        click.echo(f"Total Periods: {len(result['walk_forward_results'])}")
        click.echo(f"Average Metric: {result['average_metric']:.4f}")
        click.echo(f"Metric Std Dev: {result['std_metric']:.4f}")
        click.echo(f"Consistency Ratio: {result['consistency_ratio']:.2%}")
        
        if result['best_period']:
            best = result['best_period']
            click.echo(f"Best Period: {best['test_period'][0]} to {best['test_period'][1]}")
            click.echo(f"Best Metric Value: {best['test_result']['metric_value']:.4f}")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"walkforward_{symbol}_{timestamp}.json"
        
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        click.echo(f"💾 Detailed results saved to: {result_file}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Walk-forward error: {e}", exc_info=True)

@cli.command()
@click.option('--symbol', '-s', default='AAPL', help='Stock symbol to analyze')
@click.option('--start-date', '-sd', default='2023-01-01', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-ed', default='2024-01-01', help='End date (YYYY-MM-DD)')
@click.option('--fast-period', '-fp', default=10, help='Fast MA period')
@click.option('--slow-period', '-sp', default=30, help='Slow MA period')
@click.option('--simulations', '-n', default=1000, help='Number of Monte Carlo simulations')
@click.option('--noise-level', '-nl', default=0.001, help='Noise level for price data')
def montecarlo(symbol, start_date, end_date, fast_period, slow_period, simulations, noise_level):
    """Perform Monte Carlo analysis for strategy robustness"""
    click.echo(f"🎲 Running Monte Carlo Analysis for {symbol}")
    
    try:
        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Setup data provider
        provider = YahooFinanceProvider()
        click.echo(f"📈 Fetching historical data...")
        
        data = asyncio.run(provider.get_historical_data(symbol, start_dt, end_dt))
        if data.empty:
            click.echo("❌ No data available for the specified period")
            return
        
        # Setup optimizer
        optimizer = ParameterOptimizer()
        
        # Strategy parameters
        params = {
            'fast_period': fast_period,
            'slow_period': slow_period,
            'symbol': symbol
        }
        
        click.echo(f"🔄 Running {simulations} Monte Carlo simulations...")
        click.echo(f"  Noise Level: {noise_level}")
        
        result = optimizer.monte_carlo_analysis(
            MovingAverageCrossover,
            params,
            data,
            n_simulations=simulations,
            noise_level=noise_level,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Display results
        click.echo("\\n" + "=" * 60)
        click.echo("🎲 MONTE CARLO ANALYSIS RESULTS")
        click.echo("=" * 60)
        click.echo(f"Successful Simulations: {result['n_simulations']}")
        
        returns = result['return_statistics']
        click.echo(f"\\n📊 Return Statistics:")
        click.echo(f"  Mean: {returns['mean']:.2%}")
        click.echo(f"  Std Dev: {returns['std']:.2%}")
        click.echo(f"  Min: {returns['min']:.2%}")
        click.echo(f"  Max: {returns['max']:.2%}")
        click.echo(f"  5th Percentile: {returns['percentile_5']:.2%}")
        click.echo(f"  95th Percentile: {returns['percentile_95']:.2%}")
        
        click.echo(f"\\n📈 Probabilities:")
        click.echo(f"  Positive Return: {result['probability_positive']:.2%}")
        click.echo(f"  Sharpe > 1.0: {result['probability_sharpe_gt_1']:.2%}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"montecarlo_{symbol}_{timestamp}.json"
        
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        click.echo(f"💾 Results saved to: {result_file}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Monte Carlo error: {e}", exc_info=True)

@cli.command()
@click.option('--symbols', '-s', default='AAPL,MSFT,GOOGL', help='Comma-separated symbols to compare')
@click.option('--start-date', '-sd', default='2023-01-01', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', '-ed', default='2024-01-01', help='End date (YYYY-MM-DD)')
@click.option('--fast-period', '-fp', default=10, help='Fast MA period')
@click.option('--slow-period', '-sp', default=30, help='Slow MA period')
def compare(symbols, start_date, end_date, fast_period, slow_period):
    """Compare strategy performance across multiple symbols"""
    symbol_list = [s.strip() for s in symbols.split(',')]
    click.echo(f"⚖️ Comparing Strategy Performance: {', '.join(symbol_list)}")
    
    try:
        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
          # Setup
        provider = YahooFinanceProvider()
        engine = BacktestEngine()
        results = []
        
        # Run backtest for each symbol
        for symbol in symbol_list:
            click.echo(f"📈 Testing {symbol}...")
            
            data = asyncio.run(provider.get_historical_data(symbol, start_dt, end_dt))
            if data.empty:
                click.echo(f"⚠️ No data for {symbol}, skipping...")
                continue
            
            strategy = MovingAverageCrossover(
                short_window=fast_period,
                long_window=slow_period
            )
            
            result = engine.run_backtest(strategy, data, start_dt, end_dt, [symbol])
            results.append((f"{symbol}_MA_{fast_period}_{slow_period}", result))
        
        if not results:
            click.echo("❌ No successful backtests")
            return
        
        # Generate comparison report
        reporter = BacktestReporter()
        report_path = reporter.generate_comparison_report(results)
        
        # Display summary
        click.echo("\\n" + "=" * 80)
        click.echo("📊 STRATEGY COMPARISON RESULTS")
        click.echo("=" * 80)
        click.echo(f"{'Symbol':<10} {'Return':<10} {'Sharpe':<8} {'Drawdown':<10} {'Trades':<8}")
        click.echo("-" * 80)
        
        for strategy_name, result in results:
            symbol = strategy_name.split('_')[0]
            click.echo(f"{symbol:<10} {result.total_return:>8.2f}% {result.sharpe_ratio:>7.2f} {result.max_drawdown:>8.2f}% {result.total_trades:>7}")
        
        click.echo("=" * 80)
        click.echo(f"📝 Detailed comparison report: {report_path}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Comparison error: {e}", exc_info=True)

@cli.command()
def demo():
    """Run a comprehensive demo of all Week 2 features"""
    click.echo("🎯 QuantFlow Week 2 - Complete Feature Demo")
    click.echo("=" * 50)
    
    symbol = 'AAPL'
    start_date = '2023-01-01'
    end_date = '2024-01-01'
    
    click.echo(f"Running demo with {symbol} from {start_date} to {end_date}")
    click.echo("\\n1️⃣ Basic Backtest...")
    
    # Run each command programmatically
    from click.testing import CliRunner
    runner = CliRunner()
    
    # 1. Basic backtest
    result = runner.invoke(backtest, [
        '--symbol', symbol,
        '--start-date', start_date,
        '--end-date', end_date,
        '--generate-report'
    ])
    click.echo("✅ Basic backtest completed")
    
    # 2. Parameter optimization
    click.echo("\\n2️⃣ Parameter Optimization...")
    result = runner.invoke(optimize, [
        '--symbol', symbol,
        '--start-date', start_date,
        '--end-date', end_date,
        '--method', 'random',
        '--iterations', '20'
    ])
    click.echo("✅ Parameter optimization completed")
    
    # 3. Walk-forward analysis
    click.echo("\\n3️⃣ Walk-Forward Analysis...")
    result = runner.invoke(walkforward, [
        '--symbol', symbol,
        '--start-date', start_date,
        '--end-date', end_date,
        '--optimization-window', '126',
        '--test-window', '21'
    ])
    click.echo("✅ Walk-forward analysis completed")
    
    # 4. Monte Carlo analysis
    click.echo("\\n4️⃣ Monte Carlo Analysis...")
    result = runner.invoke(montecarlo, [
        '--symbol', symbol,
        '--start-date', start_date,
        '--end-date', end_date,
        '--simulations', '100'
    ])
    click.echo("✅ Monte Carlo analysis completed")
    
    # 5. Strategy comparison
    click.echo("\\n5️⃣ Strategy Comparison...")
    result = runner.invoke(compare, [
        '--symbols', 'AAPL,MSFT',
        '--start-date', start_date,
        '--end-date', end_date
    ])
    click.echo("✅ Strategy comparison completed")
    
    click.echo("\\n🎉 Demo completed! Check the results/ directory for outputs.")

@cli.command()
@click.option('--symbol', '-s', default='AAPL', help='Stock symbol for demo')
@click.option('--days', '-d', default=365, help='Number of days of historical data')
@click.option('--quick', '-q', is_flag=True, help='Run quick demo (reduced iterations)')
def week2_demo(symbol, days, quick):
    """
    🚀 Run comprehensive Week 2 backtesting demo
    
    This command demonstrates all Week 2 features:
    - Enhanced backtesting with comprehensive metrics
    - Parameter optimization (grid search, random, Bayesian)
    - Walk-forward analysis
    - Monte Carlo simulation
    - Professional reporting
    """
    click.echo("🚀 QuantFlow Week 2 - Comprehensive Demo")
    click.echo("=" * 50)
      # Initialize components
    provider = YahooFinanceProvider()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    click.echo(f"\n📊 Fetching {days} days of data for {symbol}...")
    
    try:
        data = asyncio.run(provider.get_historical_data(symbol, start_date, end_date))
        if data.empty:
            click.echo(f"❌ No data available for {symbol}")
            return
        
        click.echo(f"✅ Retrieved {len(data)} data points")
        
        # Configure backtesting
        config = BacktestConfig(
            initial_capital=100000,
            commission=0.001,
            slippage=0.0005,
            max_position_size=0.3
        )
        
        engine = BacktestEngine(config)
        metrics_calc = PerformanceMetrics()
        optimizer = ParameterOptimizer(engine)
        reporter = BacktestReporter()
        
        # 1. Enhanced Backtesting Demo
        click.echo("\n" + "="*50)
        click.echo("📊 1. Enhanced Backtesting with Comprehensive Metrics")
        click.echo("="*50)
        
        strategy = MovingAverageCrossover(short_window=20, long_window=50)
        
        with click.progressbar(length=100, label='Running backtest') as bar:
            result = engine.run_backtest(strategy, data, start_date, end_date)
            bar.update(100)
        
        # Display enhanced metrics
        click.echo(f"\n📈 Enhanced Backtest Results:")
        click.echo(f"   💰 Total Return: {result.total_return:.2f}%")
        click.echo(f"   📊 Annual Return: {result.annual_return:.2f}%")
        click.echo(f"   📊 Volatility: {result.volatility:.2f}%")
        click.echo(f"   📊 Sharpe Ratio: {result.sharpe_ratio:.3f}")
        click.echo(f"   📊 Max Drawdown: {result.max_drawdown:.2f}%")
        click.echo(f"   📊 Calmar Ratio: {result.calmar_ratio:.3f}")
        click.echo(f"   🎯 Win Rate: {result.win_rate:.1f}%")
        click.echo(f"   🎯 Profit Factor: {result.profit_factor:.3f}")
        click.echo(f"   🎯 Total Trades: {result.total_trades}")
        click.echo(f"   ⏱️ Avg Trade Duration: {result.avg_trade_duration:.1f} days")
        
        # 2. Parameter Optimization Demo
        click.echo("\n" + "="*50)
        click.echo("🔧 2. Parameter Optimization")
        click.echo("="*50)
        
        param_space = ParameterSpace()
        param_space.add_parameter('fast_period', 'choice', [10, 15, 20, 25] if quick else [5, 8, 10, 12, 15, 20, 25])
        param_space.add_parameter('slow_period', 'choice', [30, 40, 50] if quick else [25, 30, 35, 40, 50, 60])
        
        # Grid Search
        click.echo("\n🔍 Running Grid Search Optimization...")
        with click.progressbar(length=100, label='Grid search') as bar:
            grid_results = optimizer.grid_search_optimize(
                strategy_class=MovingAverageCrossover,
                param_space=param_space,
                data=data,
                start_date=start_date,
                end_date=end_date,
                objective='sharpe_ratio',
                max_combinations=12 if quick else None
            )
            bar.update(100)
        
        if grid_results:
            click.echo(f"🏆 Best Sharpe Ratio: {grid_results['best_score']:.3f}")
            click.echo(f"🏆 Best Parameters: {grid_results['best_parameters']}")
            
            # Show top results
            results_df = pd.DataFrame(grid_results['all_results'])
            top_3 = results_df.nlargest(3, 'score')
            click.echo("\n📊 Top 3 Parameter Combinations:")
            for i, (_, row) in enumerate(top_3.iterrows(), 1):
                click.echo(f"   {i}. Fast: {row['fast_period']}, Slow: {row['slow_period']}, "
                          f"Sharpe: {row['score']:.3f}")
        
        # Random Search
        click.echo("\n🎲 Running Random Search Optimization...")
        random_space = ParameterSpace()
        random_space.add_parameter('fast_period', 'integer', (5, 25))
        random_space.add_parameter('slow_period', 'integer', (30, 70))
        
        with click.progressbar(length=100, label='Random search') as bar:
            random_results = optimizer.random_search_optimize(
                strategy_class=MovingAverageCrossover,
                param_space=random_space,
                data=data,
                start_date=start_date,
                end_date=end_date,
                n_iterations=20 if quick else 50,
                objective='sharpe_ratio'
            )
            bar.update(100)
        
        if random_results:
            click.echo(f"🎲 Random Search Best: {random_results['best_score']:.3f}")
            click.echo(f"🎲 Best Parameters: {random_results['best_parameters']}")
        
        # 3. Walk-Forward Analysis Demo
        if not quick:
            click.echo("\n" + "="*50)
            click.echo("📅 3. Walk-Forward Analysis")
            click.echo("="*50)
            
            click.echo("\n🔄 Running Walk-Forward Analysis...")
            with click.progressbar(length=100, label='Walk-forward') as bar:
                wf_results = optimizer.walk_forward_analysis(
                    strategy_class=MovingAverageCrossover,
                    param_space=param_space,
                    data=data,
                    start_date=start_date,
                    end_date=end_date,
                    train_period_months=4,
                    test_period_months=2,
                    objective='sharpe_ratio'
                )
                bar.update(100)
            
            if wf_results and wf_results['periods']:
                click.echo(f"📊 Walk-Forward Periods: {len(wf_results['periods'])}")
                click.echo(f"📊 Avg OOS Return: {wf_results['avg_oos_return']:.2f}%")
                click.echo(f"📊 Avg OOS Sharpe: {wf_results['avg_oos_sharpe']:.3f}")
                click.echo(f"📊 OOS Win Rate: {wf_results['oos_win_rate']:.1f}%")
                
                # Show overfitting analysis
                periods = wf_results['periods']
                is_sharpes = [p['is_sharpe'] for p in periods]
                oos_sharpes = [p['oos_sharpe'] for p in periods]
                
                is_mean = np.mean(is_sharpes)
                oos_mean = np.mean(oos_sharpes)
                degradation = (is_mean - oos_mean) / is_mean * 100 if is_mean != 0 else 0
                
                click.echo(f"\n🚨 Overfitting Analysis:")
                click.echo(f"   In-Sample Sharpe: {is_mean:.3f}")
                click.echo(f"   Out-of-Sample Sharpe: {oos_mean:.3f}")
                click.echo(f"   Performance Degradation: {degradation:.1f}%")
                
                if degradation > 30:
                    click.echo("   🚨 HIGH overfitting risk!")
                elif degradation > 15:
                    click.echo("   ⚠️ MODERATE overfitting risk")
                else:
                    click.echo("   ✅ LOW overfitting risk")
        
        # 4. Monte Carlo Simulation Demo
        click.echo("\n" + "="*50)
        click.echo("🎲 4. Monte Carlo Robustness Testing")
        click.echo("="*50)
        
        click.echo("\n🎲 Running Monte Carlo Analysis...")
        with click.progressbar(length=100, label='Monte Carlo') as bar:
            mc_results = optimizer.monte_carlo_analysis(
                strategy_class=MovingAverageCrossover,
                param_space=random_space,
                data=data,
                start_date=start_date,
                end_date=end_date,
                n_simulations=25 if quick else 100,
                objective='total_return'
            )
            bar.update(100)
        
        if mc_results:
            returns = [r['total_return'] for r in mc_results['results']]
            click.echo(f"🎲 Monte Carlo Simulations: {len(returns)}")
            click.echo(f"🎲 Mean Return: {np.mean(returns):.2f}%")
            click.echo(f"🎲 Std Return: {np.std(returns):.2f}%")
            click.echo(f"🎲 Best Return: {np.max(returns):.2f}%")
            click.echo(f"🎲 Worst Return: {np.min(returns):.2f}%")
            click.echo(f"🎲 Positive Return Rate: {len([r for r in returns if r > 0]) / len(returns) * 100:.1f}%")
            
            # Risk metrics
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            click.echo(f"\n📊 Risk Metrics:")
            click.echo(f"   VaR (95%): {var_95:.2f}%")
            click.echo(f"   VaR (99%): {var_99:.2f}%")
        
        # 5. Multi-Strategy Comparison Demo
        click.echo("\n" + "="*50)
        click.echo("⚔️ 5. Multi-Strategy Comparison")
        click.echo("="*50)
          # Create multiple strategies
        if grid_results:
            best_params = grid_results['best_parameters']
            strategies = [
                MovingAverageCrossover(short_window=15, long_window=50),
                MovingAverageCrossover(short_window=12, long_window=40),
                MovingAverageCrossover(short_window=8, long_window=30),
                MovingAverageCrossover(**best_params)
            ]
        else:
            strategies = [
                MovingAverageCrossover(short_window=15, long_window=50),
                MovingAverageCrossover(short_window=12, long_window=40),
                MovingAverageCrossover(short_window=8, long_window=30)
            ]
        
        click.echo(f"\n⚔️ Comparing {len(strategies)} strategies...")
        with click.progressbar(length=100, label='Multi-strategy test') as bar:
            multi_results = engine.run_multiple_backtests(
                strategies=strategies,
                data=data,
                start_date=start_date,
                end_date=end_date,
                parallel=True
            )
            bar.update(100)
        
        # Display comparison
        click.echo("\n📊 Strategy Comparison:")
        comparison_data = []
        for name, result in multi_results.items():
            comparison_data.append({
                'Strategy': name,
                'Return (%)': f"{result.total_return:.2f}",
                'Sharpe': f"{result.sharpe_ratio:.3f}",
                'Max DD (%)': f"{result.max_drawdown:.2f}",
                'Win Rate (%)': f"{result.win_rate:.1f}",
                'Trades': result.total_trades
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        click.echo(comparison_df.to_string(index=False))
        
        # 6. Professional Report Generation Demo
        click.echo("\n" + "="*50)
        click.echo("📄 6. Professional Report Generation")
        click.echo("="*50)
        
        # Use best performing strategy
        best_strategy_name = max(multi_results.keys(), 
                               key=lambda x: multi_results[x].sharpe_ratio)
        best_result = multi_results[best_strategy_name]
        
        click.echo(f"\n📄 Generating comprehensive report for: {best_strategy_name}")
        
        try:
            with click.progressbar(length=100, label='Generating report') as bar:
                report_path = reporter.generate_full_report(
                    backtest_result=best_result,
                    strategy_name=best_strategy_name,
                    include_plots=True,
                    include_trades=True
                )
                bar.update(50)
                
                comparison_path = reporter.generate_comparison_report(
                    results=multi_results,
                    report_name=f"week2_demo_{symbol}"
                )
                bar.update(100)
            
            click.echo(f"✅ Individual report: {report_path}")
            click.echo(f"✅ Comparison report: {comparison_path}")
            
        except Exception as e:
            click.echo(f"⚠️ Report generation warning: {e}")
            click.echo("💡 For full reporting, install: pip install matplotlib seaborn")
        
        # Summary and Next Steps
        click.echo("\n" + "="*50)
        click.echo("🎉 Week 2 Demo Complete!")
        click.echo("="*50)
        
        click.echo(f"\n📊 Demo Summary for {symbol}:")
        click.echo(f"   📈 Data Period: {days} days")
        click.echo(f"   🎯 Best Strategy: {best_strategy_name}")
        click.echo(f"   💰 Best Return: {best_result.total_return:.2f}%")
        click.echo(f"   📊 Best Sharpe: {best_result.sharpe_ratio:.3f}")
        
        if grid_results:
            click.echo(f"   🔧 Optimal Params: {grid_results['best_parameters']}")
        
        click.echo(f"\n📁 Reports saved in: results/")
        click.echo(f"🔧 Try other commands:")
        click.echo(f"   quantflow-backtest optimize --symbol {symbol}")
        click.echo(f"   quantflow-backtest walk-forward --symbol {symbol}")
        click.echo(f"   quantflow-backtest monte-carlo --symbol {symbol}")
        
    except Exception as e:
        click.echo(f"❌ Demo error: {e}")
        logger.error(f"Week 2 demo error: {e}", exc_info=True)

if __name__ == '__main__':
    cli()
