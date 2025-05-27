#!/usr/bin/env python3
"""
QuantFlow Week 2 - Walk-Forward Analysis Example

This script demonstrates walk-forward analysis for strategy validation:
- Rolling optimization and out-of-sample testing
- Parameter stability over time
- Overfitting detection
- Real-world trading simulation
"""

import sys
import os
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.optimizer import ParameterOptimizer, ParameterSpace
from data.providers.yahoo_finance import YahooFinanceProvider
from strategies.technical.moving_average import MovingAverageCrossover

def run_walk_forward_analysis():
    """Run comprehensive walk-forward analysis"""
    
    print("📅 QuantFlow Week 2 - Walk-Forward Analysis")
    print("=" * 50)
    
    # Setup
    provider = YahooFinanceProvider()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    symbol = 'AAPL'
    print(f"\n📊 Analyzing {symbol} from {start_date} to {end_date}")
    
    # Get data
    data = provider.get_historical_data(symbol, start_date, end_date)
    if data.empty:
        print("❌ No data available")
        return
    
    print(f"✅ Data points: {len(data)}")
    
    # Configure analysis
    config = BacktestConfig(
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005
    )
    
    engine = BacktestEngine(config)
    optimizer = ParameterOptimizer(engine)
    
    # Define parameter space
    param_space = ParameterSpace()
    param_space.add_parameter('fast_period', 'choice', [5, 8, 10, 12, 15, 20])
    param_space.add_parameter('slow_period', 'choice', [25, 30, 35, 40, 50, 60])
    
    # 1. Standard Walk-Forward Analysis
    print("\n📅 1. Standard Walk-Forward Analysis")
    print("-" * 40)
    
    wf_results = optimizer.walk_forward_analysis(
        strategy_class=MovingAverageCrossover,
        param_space=param_space,
        data=data,
        start_date=start_date,
        end_date=end_date,
        train_period_months=6,
        test_period_months=2,
        objective='sharpe_ratio'
    )
    
    if wf_results and wf_results['periods']:
        print(f"📊 Walk-Forward Periods: {len(wf_results['periods'])}")
        print(f"📊 Avg OOS Return: {wf_results['avg_oos_return']:.2f}%")
        print(f"📊 Avg OOS Sharpe: {wf_results['avg_oos_sharpe']:.3f}")
        print(f"📊 OOS Win Rate: {wf_results['oos_win_rate']:.1f}%")
        
        # Detailed period analysis
        print(f"\n📈 Period-by-Period Results:")
        print("-" * 30)
        
        for i, period in enumerate(wf_results['periods'], 1):
            train_start = period['train_start'].strftime('%Y-%m-%d')
            train_end = period['train_end'].strftime('%Y-%m-%d')
            test_start = period['test_start'].strftime('%Y-%m-%d')
            test_end = period['test_end'].strftime('%Y-%m-%d')
            
            print(f"Period {i}:")
            print(f"  Train: {train_start} to {train_end}")
            print(f"  Test:  {test_start} to {test_end}")
            print(f"  Best Params: Fast {period['best_params']['fast_period']}, "
                  f"Slow {period['best_params']['slow_period']}")
            print(f"  IS Sharpe: {period['is_sharpe']:.3f}")
            print(f"  OOS Return: {period['oos_return']:.2f}%")
            print(f"  OOS Sharpe: {period['oos_sharpe']:.3f}")
            print()
        
        # 2. Parameter Stability Analysis
        print("🔧 2. Parameter Stability Analysis")
        print("-" * 35)
        
        # Extract parameters for analysis
        fast_periods = [p['best_params']['fast_period'] for p in wf_results['periods']]
        slow_periods = [p['best_params']['slow_period'] for p in wf_results['periods']]
        
        print(f"📊 Fast Period Statistics:")
        print(f"   Mean: {np.mean(fast_periods):.1f}")
        print(f"   Std:  {np.std(fast_periods):.1f}")
        print(f"   Range: {min(fast_periods)} - {max(fast_periods)}")
        
        print(f"📊 Slow Period Statistics:")
        print(f"   Mean: {np.mean(slow_periods):.1f}")
        print(f"   Std:  {np.std(slow_periods):.1f}")
        print(f"   Range: {min(slow_periods)} - {max(slow_periods)}")
        
        # Parameter consistency score
        fast_consistency = 1 - (np.std(fast_periods) / np.mean(fast_periods))
        slow_consistency = 1 - (np.std(slow_periods) / np.mean(slow_periods))
        overall_consistency = (fast_consistency + slow_consistency) / 2
        
        print(f"📊 Parameter Consistency Score: {overall_consistency:.3f}")
        
        # 3. Overfitting Detection
        print("🚨 3. Overfitting Detection")
        print("-" * 27)
        
        is_sharpes = [p['is_sharpe'] for p in wf_results['periods']]
        oos_sharpes = [p['oos_sharpe'] for p in wf_results['periods']]
        
        is_mean = np.mean(is_sharpes)
        oos_mean = np.mean(oos_sharpes)
        degradation = (is_mean - oos_mean) / is_mean * 100 if is_mean != 0 else 0
        
        print(f"📊 In-Sample Sharpe: {is_mean:.3f}")
        print(f"📊 Out-of-Sample Sharpe: {oos_mean:.3f}")
        print(f"📊 Performance Degradation: {degradation:.1f}%")
        
        if degradation > 30:
            print("🚨 HIGH overfitting risk detected!")
        elif degradation > 15:
            print("⚠️ MODERATE overfitting risk")
        else:
            print("✅ LOW overfitting risk")
        
        # 4. Rolling Statistics
        print("📈 4. Rolling Performance Statistics")
        print("-" * 34)
        
        # Calculate rolling metrics
        window_size = 3
        if len(wf_results['periods']) >= window_size:
            rolling_returns = []
            rolling_sharpes = []
            
            for i in range(len(wf_results['periods']) - window_size + 1):
                window_periods = wf_results['periods'][i:i+window_size]
                window_returns = [p['oos_return'] for p in window_periods]
                window_sharpes = [p['oos_sharpe'] for p in window_periods]
                
                rolling_returns.append(np.mean(window_returns))
                rolling_sharpes.append(np.mean(window_sharpes))
            
            print(f"📊 Rolling {window_size}-Period Averages:")
            for i, (ret, sharpe) in enumerate(zip(rolling_returns, rolling_sharpes)):
                print(f"   Window {i+1}: Return {ret:.2f}%, Sharpe {sharpe:.3f}")
        
        # 5. Trend Analysis
        print("📊 5. Performance Trend Analysis")
        print("-" * 31)
        
        # Check if performance is trending up or down
        oos_returns = [p['oos_return'] for p in wf_results['periods']]
        
        if len(oos_returns) >= 3:
            # Simple linear trend
            x = np.arange(len(oos_returns))
            trend_coef = np.polyfit(x, oos_returns, 1)[0]
            
            print(f"📊 Return Trend Coefficient: {trend_coef:.3f}")
            
            if trend_coef > 0.5:
                print("📈 IMPROVING performance trend")
            elif trend_coef < -0.5:
                print("📉 DECLINING performance trend")
            else:
                print("➡️ STABLE performance trend")
        
        # 6. Create visualization (if matplotlib available)
        try:
            create_walk_forward_plots(wf_results)
            print("📊 Walk-forward plots saved to results/walk_forward_analysis.png")
        except ImportError:
            print("⚠️ Matplotlib not available for plotting")
        except Exception as e:
            print(f"⚠️ Plotting error: {e}")
    
    # 7. Compare with Buy-and-Hold
    print("📊 6. Benchmark Comparison")
    print("-" * 25)
    
    # Calculate buy-and-hold return
    first_price = data['close_price'].iloc[0]
    last_price = data['close_price'].iloc[-1]
    bnh_return = ((last_price - first_price) / first_price) * 100
    
    if wf_results:
        strategy_return = wf_results['total_oos_return']
        outperformance = strategy_return - bnh_return
        
        print(f"📊 Buy-and-Hold Return: {bnh_return:.2f}%")
        print(f"📊 Strategy Return: {strategy_return:.2f}%")
        print(f"📊 Outperformance: {outperformance:.2f}%")
        
        if outperformance > 0:
            print("🏆 Strategy OUTPERFORMED buy-and-hold")
        else:
            print("📉 Strategy UNDERPERFORMED buy-and-hold")

def create_walk_forward_plots(wf_results):
    """Create visualization of walk-forward results"""
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Walk-Forward Analysis Results', fontsize=16, fontweight='bold')
    
    # Extract data
    periods = wf_results['periods']
    period_nums = list(range(1, len(periods) + 1))
    oos_returns = [p['oos_return'] for p in periods]
    oos_sharpes = [p['oos_sharpe'] for p in periods]
    is_sharpes = [p['is_sharpe'] for p in periods]
    fast_periods = [p['best_params']['fast_period'] for p in periods]
    slow_periods = [p['best_params']['slow_period'] for p in periods]
    
    # Plot 1: OOS Returns over time
    axes[0, 0].bar(period_nums, oos_returns, alpha=0.7, color='steelblue')
    axes[0, 0].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    axes[0, 0].set_title('Out-of-Sample Returns by Period')
    axes[0, 0].set_xlabel('Period')
    axes[0, 0].set_ylabel('Return (%)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: IS vs OOS Sharpe Ratios
    axes[0, 1].plot(period_nums, is_sharpes, marker='o', label='In-Sample', linewidth=2)
    axes[0, 1].plot(period_nums, oos_sharpes, marker='s', label='Out-of-Sample', linewidth=2)
    axes[0, 1].set_title('In-Sample vs Out-of-Sample Sharpe Ratios')
    axes[0, 1].set_xlabel('Period')
    axes[0, 1].set_ylabel('Sharpe Ratio')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Parameter Evolution
    axes[1, 0].plot(period_nums, fast_periods, marker='o', label='Fast Period', linewidth=2)
    axes[1, 0].plot(period_nums, slow_periods, marker='s', label='Slow Period', linewidth=2)
    axes[1, 0].set_title('Parameter Evolution Over Time')
    axes[1, 0].set_xlabel('Period')
    axes[1, 0].set_ylabel('Period Length')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Cumulative OOS Returns
    cumulative_returns = np.cumsum(oos_returns)
    axes[1, 1].plot(period_nums, cumulative_returns, marker='o', linewidth=2, color='green')
    axes[1, 1].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    axes[1, 1].set_title('Cumulative Out-of-Sample Returns')
    axes[1, 1].set_xlabel('Period')
    axes[1, 1].set_ylabel('Cumulative Return (%)')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    os.makedirs("results", exist_ok=True)
    plt.savefig("results/walk_forward_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()

def run_anchored_walk_forward():
    """Run anchored walk-forward analysis (expanding window)"""
    
    print("\n⚓ Anchored Walk-Forward Analysis")
    print("-" * 35)
    
    provider = YahooFinanceProvider()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=730)
    
    data = provider.get_historical_data('AAPL', start_date, end_date)
    if data.empty:
        return
    
    config = BacktestConfig(initial_capital=100000)
    engine = BacktestEngine(config)
    optimizer = ParameterOptimizer(engine)
    
    param_space = ParameterSpace()
    param_space.add_parameter('fast_period', 'choice', [10, 15, 20])
    param_space.add_parameter('slow_period', 'choice', [30, 40, 50])
    
    # Run anchored analysis
    anchored_results = optimizer.anchored_walk_forward_analysis(
        strategy_class=MovingAverageCrossover,
        param_space=param_space,
        data=data,
        start_date=start_date,
        end_date=end_date,
        initial_train_months=6,
        test_period_months=2,
        objective='sharpe_ratio'
    )
    
    if anchored_results and anchored_results['periods']:
        print(f"⚓ Anchored Periods: {len(anchored_results['periods'])}")
        print(f"⚓ Avg OOS Return: {anchored_results['avg_oos_return']:.2f}%")
        print(f"⚓ Avg OOS Sharpe: {anchored_results['avg_oos_sharpe']:.3f}")
        
        # Compare stability with rolling approach
        periods = anchored_results['periods']
        fast_periods = [p['best_params']['fast_period'] for p in periods]
        slow_periods = [p['best_params']['slow_period'] for p in periods]
        
        fast_stability = 1 - (np.std(fast_periods) / np.mean(fast_periods))
        slow_stability = 1 - (np.std(slow_periods) / np.mean(slow_periods))
        
        print(f"⚓ Parameter Stability:")
        print(f"   Fast Period: {fast_stability:.3f}")
        print(f"   Slow Period: {slow_stability:.3f}")

if __name__ == "__main__":
    try:
        run_walk_forward_analysis()
        run_anchored_walk_forward()
        
        print("\n" + "="*50)
        print("🎉 Walk-Forward Analysis Complete!")
        print("="*50)
        print("\n📊 Key Insights:")
        print("• Walk-forward analysis simulates real trading conditions")
        print("• Parameter stability indicates strategy robustness")
        print("• IS vs OOS performance gap reveals overfitting")
        print("• Rolling optimization adapts to changing market conditions")
        print("\n📁 Check 'results' folder for visualization plots")
        
    except Exception as e:
        print(f"❌ Error in walk-forward analysis: {e}")
        import traceback
        traceback.print_exc()
