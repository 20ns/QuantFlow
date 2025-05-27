#!/usr/bin/env python3
"""
QuantFlow Week 2 - Advanced Backtesting Example

This script demonstrates the enhanced backtesting capabilities including:
- Comprehensive performance metrics calculation
- Parameter optimization (grid search and Bayesian)
- Walk-forward analysis
- Monte Carlo simulation
- Professional reporting with charts
"""

import sys
import os
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from backtesting.optimizer import ParameterOptimizer, ParameterSpace
from backtesting.reporter import BacktestReporter
from data.providers.yahoo_finance import YahooFinanceProvider
from strategies.technical.moving_average import MovingAverageCrossover

def main():
    """Run comprehensive Week 2 backtesting demo"""
    
    print("🚀 QuantFlow Week 2 - Advanced Backtesting Demo")
    print("=" * 60)
    
    # Initialize data provider
    print("\n📊 Fetching market data...")
    provider = YahooFinanceProvider()
    
    # Get 2 years of data for multiple symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    all_data = []
    for symbol in symbols:
        try:
            data = provider.get_historical_data(symbol, start_date, end_date)
            if not data.empty:
                all_data.append(data)
                print(f"✅ {symbol}: {len(data)} data points")
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
    
    if not all_data:
        print("❌ No data available for backtesting")
        return
    
    # Combine all data
    market_data = pd.concat(all_data, ignore_index=True)
    print(f"\n📈 Total data points: {len(market_data)}")
    
    # Demo 1: Basic Enhanced Backtesting
    print("\n" + "="*60)
    print("📊 Demo 1: Enhanced Backtesting with Comprehensive Metrics")
    print("="*60)
    
    # Configure backtest
    config = BacktestConfig(
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005,
        max_position_size=0.3,
        allow_short_selling=False
    )
    
    # Create strategy
    strategy = MovingAverageCrossover(
        name="MA_Cross_20_50",
        fast_period=20,
        slow_period=50
    )
    
    # Run backtest
    engine = BacktestEngine(config)
    result = engine.run_backtest(
        strategy=strategy,
        data=market_data[market_data['symbol'] == 'AAPL'],
        start_date=start_date,
        end_date=end_date
    )
    
    # Display results
    print(f"\n📈 Strategy: {result.strategy_name}")
    print(f"💰 Initial Capital: ${result.initial_capital:,.2f}")
    print(f"💰 Final Value: ${result.final_value:,.2f}")
    print(f"📊 Total Return: {result.total_return:.2f}%")
    print(f"📊 Annual Return: {result.annual_return:.2f}%")
    print(f"📊 Volatility: {result.volatility:.2f}%")
    print(f"📊 Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"📊 Max Drawdown: {result.max_drawdown:.2f}%")
    print(f"📊 Calmar Ratio: {result.calmar_ratio:.2f}")
    print(f"🎯 Win Rate: {result.win_rate:.1f}%")
    print(f"🎯 Total Trades: {result.total_trades}")
    
    # Demo 2: Parameter Optimization
    print("\n" + "="*60)
    print("🔧 Demo 2: Parameter Optimization")
    print("="*60)
    
    # Define parameter space
    param_space = ParameterSpace()
    param_space.add_parameter('fast_period', 'integer', (5, 25))
    param_space.add_parameter('slow_period', 'integer', (30, 70))
    
    # Create optimizer
    optimizer = ParameterOptimizer(engine)
    
    # Grid search optimization
    print("\n🔍 Running Grid Search Optimization...")
    grid_results = optimizer.grid_search_optimize(
        strategy_class=MovingAverageCrossover,
        param_space=param_space,
        data=market_data[market_data['symbol'] == 'AAPL'],
        start_date=start_date,
        end_date=end_date,
        objective='sharpe_ratio',
        max_combinations=20  # Limit for demo
    )
    
    if grid_results:
        best_params = grid_results['best_parameters']
        best_score = grid_results['best_score']
        print(f"🏆 Best Parameters: {best_params}")
        print(f"🏆 Best Sharpe Ratio: {best_score:.3f}")
        
        # Show top 5 results
        print("\n📊 Top 5 Parameter Combinations:")
        results_df = pd.DataFrame(grid_results['all_results'])
        top_5 = results_df.nlargest(5, 'score')
        for i, (_, row) in enumerate(top_5.iterrows(), 1):
            print(f"{i}. Fast: {row['fast_period']}, Slow: {row['slow_period']}, "
                  f"Sharpe: {row['score']:.3f}")
    
    # Demo 3: Walk-Forward Analysis
    print("\n" + "="*60)
    print("📅 Demo 3: Walk-Forward Analysis")
    print("="*60)
    
    print("\n🔄 Running Walk-Forward Analysis...")
    wf_results = optimizer.walk_forward_analysis(
        strategy_class=MovingAverageCrossover,
        param_space=param_space,
        data=market_data[market_data['symbol'] == 'AAPL'],
        start_date=start_date,
        end_date=end_date,
        train_period_months=6,
        test_period_months=2,
        objective='sharpe_ratio'
    )
    
    if wf_results and wf_results['periods']:
        print(f"📊 Walk-Forward Periods: {len(wf_results['periods'])}")
        print(f"📊 Average Out-of-Sample Return: {wf_results['avg_oos_return']:.2f}%")
        print(f"📊 Average Out-of-Sample Sharpe: {wf_results['avg_oos_sharpe']:.3f}")
        
        # Show period details
        print("\n📈 Period-by-Period Results:")
        for i, period in enumerate(wf_results['periods'][:3], 1):  # Show first 3
            print(f"Period {i}: Return: {period['oos_return']:.2f}%, "
                  f"Sharpe: {period['oos_sharpe']:.3f}")
    
    # Demo 4: Monte Carlo Analysis
    print("\n" + "="*60)
    print("🎲 Demo 4: Monte Carlo Robustness Testing")
    print("="*60)
    
    print("\n🎲 Running Monte Carlo Analysis...")
    mc_results = optimizer.monte_carlo_analysis(
        strategy_class=MovingAverageCrossover,
        param_space=param_space,
        data=market_data[market_data['symbol'] == 'AAPL'],
        start_date=start_date,
        end_date=end_date,
        n_simulations=50,  # Reduced for demo
        objective='total_return'
    )
    
    if mc_results:
        returns = [r['total_return'] for r in mc_results['results']]
        print(f"📊 Monte Carlo Simulations: {len(returns)}")
        print(f"📊 Mean Return: {np.mean(returns):.2f}%")
        print(f"📊 Std Return: {np.std(returns):.2f}%")
        print(f"📊 Best Return: {np.max(returns):.2f}%")
        print(f"📊 Worst Return: {np.min(returns):.2f}%")
        print(f"📊 Win Rate: {len([r for r in returns if r > 0]) / len(returns) * 100:.1f}%")
    
    # Demo 5: Multi-Strategy Comparison
    print("\n" + "="*60)
    print("⚔️ Demo 5: Multi-Strategy Comparison")
    print("="*60)
    
    # Create multiple strategies with different parameters
    strategies = [
        MovingAverageCrossover("MA_10_30", fast_period=10, slow_period=30),
        MovingAverageCrossover("MA_20_50", fast_period=20, slow_period=50),
        MovingAverageCrossover("MA_15_40", fast_period=15, slow_period=40)
    ]
    
    print(f"\n⚔️ Comparing {len(strategies)} strategies...")
    multi_results = engine.run_multiple_backtests(
        strategies=strategies,
        data=market_data[market_data['symbol'] == 'AAPL'],
        start_date=start_date,
        end_date=end_date,
        parallel=True
    )
    
    # Display comparison
    print("\n📊 Strategy Comparison:")
    comparison_data = []
    for name, result in multi_results.items():
        comparison_data.append({
            'Strategy': name,
            'Total Return (%)': f"{result.total_return:.2f}",
            'Annual Return (%)': f"{result.annual_return:.2f}",
            'Sharpe Ratio': f"{result.sharpe_ratio:.3f}",
            'Max Drawdown (%)': f"{result.max_drawdown:.2f}",
            'Win Rate (%)': f"{result.win_rate:.1f}",
            'Total Trades': result.total_trades
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print(comparison_df.to_string(index=False))
    
    # Demo 6: Generate Comprehensive Report
    print("\n" + "="*60)
    print("📄 Demo 6: Professional Report Generation")
    print("="*60)
    
    # Use best performing strategy for detailed report
    best_strategy_name = max(multi_results.keys(), 
                           key=lambda x: multi_results[x].sharpe_ratio)
    best_result = multi_results[best_strategy_name]
    
    print(f"\n📄 Generating report for best strategy: {best_strategy_name}")
    
    try:
        reporter = BacktestReporter("results")
        
        # Generate comprehensive report
        report_path = reporter.generate_full_report(
            backtest_result=best_result,
            strategy_name=best_strategy_name,
            include_plots=True,
            include_trades=True
        )
        
        print(f"✅ Report generated: {report_path}")
        
        # Generate comparison report
        comparison_path = reporter.generate_comparison_report(
            results=multi_results,
            report_name="strategy_comparison"
        )
        
        print(f"✅ Comparison report: {comparison_path}")
        
    except Exception as e:
        print(f"⚠️ Report generation error (likely missing matplotlib): {e}")
        print("💡 Install matplotlib for full reporting: pip install matplotlib seaborn")
    
    print("\n" + "="*60)
    print("🎉 Week 2 Advanced Backtesting Demo Complete!")
    print("="*60)
    print("\n📁 Check the 'results' folder for generated reports")
    print("🔧 Try different parameters with the CLI: python -m src.backtesting.cli")
    print("📖 See documentation for more advanced features")

if __name__ == "__main__":
    main()
