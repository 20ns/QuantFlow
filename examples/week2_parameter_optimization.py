#!/usr/bin/env python3
"""
QuantFlow Week 2 - Parameter Optimization Deep Dive

This script demonstrates advanced parameter optimization techniques:
- Grid Search with comprehensive parameter spaces
- Bayesian Optimization for efficient parameter exploration
- Multi-objective optimization
- Robust parameter selection with Monte Carlo validation
- Parameter sensitivity analysis
"""

import sys
import os
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.optimizer import ParameterOptimizer, ParameterSpace
from backtesting.reporter import BacktestReporter
from data.providers.yahoo_finance import YahooFinanceProvider
from strategies.technical.moving_average import MovingAverageCrossover

def run_comprehensive_optimization():
    """Run comprehensive parameter optimization analysis"""
    
    print("🔧 QuantFlow Week 2 - Parameter Optimization Deep Dive")
    print("=" * 65)
    
    # Setup
    provider = YahooFinanceProvider()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)  # 1 year
    
    # Get data for optimization
    print("\n📊 Fetching market data for optimization...")
    symbols = ['AAPL', 'MSFT', 'TSLA']
    
    for symbol in symbols:
        print(f"\n🔍 Optimizing parameters for {symbol}")
        print("-" * 40)
        
        try:
            data = provider.get_historical_data(symbol, start_date, end_date)
            if data.empty:
                continue
                
            print(f"✅ Data points: {len(data)}")
            
            # Configure optimization
            config = BacktestConfig(
                initial_capital=100000,
                commission=0.001,
                slippage=0.0005
            )
            
            engine = BacktestEngine(config)
            optimizer = ParameterOptimizer(engine)
            
            # 1. Comprehensive Grid Search
            print("\n🔍 1. Comprehensive Grid Search")
            print("-" * 30)
            
            param_space = ParameterSpace()
            param_space.add_parameter('fast_period', 'choice', [5, 8, 10, 12, 15, 20])
            param_space.add_parameter('slow_period', 'choice', [25, 30, 35, 40, 50, 60])
            
            grid_results = optimizer.grid_search_optimize(
                strategy_class=MovingAverageCrossover,
                param_space=param_space,
                data=data,
                start_date=start_date,
                end_date=end_date,
                objective='sharpe_ratio'
            )
            
            if grid_results:
                print(f"🏆 Best Sharpe Ratio: {grid_results['best_score']:.3f}")
                print(f"🏆 Best Parameters: {grid_results['best_parameters']}")
                
                # Show parameter distribution
                results_df = pd.DataFrame(grid_results['all_results'])
                print(f"\n📊 Results Summary:")
                print(f"   Mean Sharpe: {results_df['score'].mean():.3f}")
                print(f"   Std Sharpe: {results_df['score'].std():.3f}")
                print(f"   Best 10% avg: {results_df.nlargest(int(len(results_df)*0.1), 'score')['score'].mean():.3f}")
            
            # 2. Random Search for comparison
            print(f"\n🎲 2. Random Search Optimization")
            print("-" * 30)
            
            random_space = ParameterSpace()
            random_space.add_parameter('fast_period', 'integer', (5, 25))
            random_space.add_parameter('slow_period', 'integer', (30, 80))
            
            random_results = optimizer.random_search_optimize(
                strategy_class=MovingAverageCrossover,
                param_space=random_space,
                data=data,
                start_date=start_date,
                end_date=end_date,
                n_iterations=50,
                objective='sharpe_ratio'
            )
            
            if random_results:
                print(f"🎲 Random Search Best: {random_results['best_score']:.3f}")
                print(f"🎲 Best Parameters: {random_results['best_parameters']}")
            
            # 3. Bayesian Optimization (if available)
            print(f"\n🧠 3. Bayesian Optimization")
            print("-" * 30)
            
            try:
                bayes_results = optimizer.bayesian_optimize(
                    strategy_class=MovingAverageCrossover,
                    param_space=random_space,
                    data=data,
                    start_date=start_date,
                    end_date=end_date,
                    n_calls=30,
                    objective='sharpe_ratio'
                )
                
                if bayes_results:
                    print(f"🧠 Bayesian Best: {bayes_results['best_score']:.3f}")
                    print(f"🧠 Best Parameters: {bayes_results['best_parameters']}")
                    print(f"🧠 Convergence: {len(bayes_results['optimization_history'])} iterations")
                    
            except Exception as e:
                print(f"⚠️ Bayesian optimization not available: {e}")
                print("💡 Install scikit-optimize: pip install scikit-optimize")
            
            # 4. Multi-objective optimization
            print(f"\n🎯 4. Multi-Objective Analysis")
            print("-" * 30)
            
            # Optimize for different objectives
            objectives = ['total_return', 'sharpe_ratio', 'calmar_ratio', 'win_rate']
            multi_obj_results = {}
            
            for obj in objectives:
                result = optimizer.grid_search_optimize(
                    strategy_class=MovingAverageCrossover,
                    param_space=param_space,
                    data=data,
                    start_date=start_date,
                    end_date=end_date,
                    objective=obj,
                    max_combinations=20  # Limit for speed
                )
                
                if result:
                    multi_obj_results[obj] = result
                    print(f"🎯 Best {obj}: {result['best_score']:.3f} "
                          f"(Fast: {result['best_parameters']['fast_period']}, "
                          f"Slow: {result['best_parameters']['slow_period']})")
            
            # 5. Robustness Testing
            print(f"\n🛡️ 5. Parameter Robustness Testing")
            print("-" * 35)
            
            if grid_results:
                best_params = grid_results['best_parameters']
                
                # Test parameter sensitivity
                sensitivity_results = []
                base_fast = best_params['fast_period']
                base_slow = best_params['slow_period']
                
                for fast_adj in [-2, -1, 0, 1, 2]:
                    for slow_adj in [-5, 0, 5]:
                        test_fast = max(5, base_fast + fast_adj)
                        test_slow = max(test_fast + 5, base_slow + slow_adj)
                        
                        test_strategy = MovingAverageCrossover(
                            f"Test_{test_fast}_{test_slow}",
                            fast_period=test_fast,
                            slow_period=test_slow
                        )
                        
                        try:
                            test_result = engine.run_backtest(
                                strategy=test_strategy,
                                data=data,
                                start_date=start_date,
                                end_date=end_date
                            )
                            
                            sensitivity_results.append({
                                'fast_period': test_fast,
                                'slow_period': test_slow,
                                'fast_adj': fast_adj,
                                'slow_adj': slow_adj,
                                'sharpe_ratio': test_result.sharpe_ratio,
                                'total_return': test_result.total_return
                            })
                            
                        except Exception as e:
                            continue
                
                if sensitivity_results:
                    sens_df = pd.DataFrame(sensitivity_results)
                    base_sharpe = sens_df[
                        (sens_df['fast_adj'] == 0) & (sens_df['slow_adj'] == 0)
                    ]['sharpe_ratio'].iloc[0]
                    
                    print(f"🛡️ Base Sharpe Ratio: {base_sharpe:.3f}")
                    print(f"🛡️ Parameter Sensitivity:")
                    
                    # Calculate sensitivity metrics
                    sharpe_std = sens_df['sharpe_ratio'].std()
                    sharpe_range = sens_df['sharpe_ratio'].max() - sens_df['sharpe_ratio'].min()
                    robust_score = 1 - (sharpe_std / abs(base_sharpe)) if base_sharpe != 0 else 0
                    
                    print(f"   Sharpe Std: {sharpe_std:.3f}")
                    print(f"   Sharpe Range: {sharpe_range:.3f}")
                    print(f"   Robustness Score: {robust_score:.3f}")
                    
                    # Show best and worst sensitivity results
                    best_sens = sens_df.loc[sens_df['sharpe_ratio'].idxmax()]
                    worst_sens = sens_df.loc[sens_df['sharpe_ratio'].idxmin()]
                    
                    print(f"   Best variation: Fast {best_sens['fast_period']}, "
                          f"Slow {best_sens['slow_period']} → Sharpe {best_sens['sharpe_ratio']:.3f}")
                    print(f"   Worst variation: Fast {worst_sens['fast_period']}, "
                          f"Slow {worst_sens['slow_period']} → Sharpe {worst_sens['sharpe_ratio']:.3f}")
            
            # 6. Save optimization results
            print(f"\n💾 6. Saving Optimization Results")
            print("-" * 32)
            
            results_summary = {
                'symbol': symbol,
                'optimization_date': datetime.now().isoformat(),
                'data_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': (end_date - start_date).days
                },
                'grid_search': grid_results,
                'random_search': random_results,
                'multi_objective': multi_obj_results,
                'sensitivity_analysis': sensitivity_results if 'sensitivity_results' in locals() else None
            }
            
            # Save to file
            output_file = f"results/optimization_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs("results", exist_ok=True)
            
            # Convert numpy types for JSON serialization
            def convert_numpy(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return obj
            
            # Clean results for JSON
            def clean_for_json(data):
                if isinstance(data, dict):
                    return {k: clean_for_json(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [clean_for_json(item) for item in data]
                else:
                    return convert_numpy(data)
            
            clean_results = clean_for_json(results_summary)
            
            with open(output_file, 'w') as f:
                json.dump(clean_results, f, indent=2, default=str)
            
            print(f"💾 Results saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error optimizing {symbol}: {e}")
            continue
    
    print("\n" + "="*65)
    print("🎉 Parameter Optimization Analysis Complete!")
    print("="*65)
    print("\n📊 Key Takeaways:")
    print("• Grid search provides systematic parameter exploration")
    print("• Random search can find good parameters with fewer evaluations")
    print("• Bayesian optimization efficiently navigates parameter space")
    print("• Multi-objective optimization reveals trade-offs")
    print("• Robustness testing ensures parameter stability")
    print("\n📁 Check 'results' folder for detailed optimization reports")

def analyze_parameter_stability():
    """Analyze parameter stability across different market conditions"""
    
    print("\n🔬 Parameter Stability Analysis")
    print("=" * 40)
    
    provider = YahooFinanceProvider()
    symbol = 'AAPL'
    
    # Test across different market periods
    periods = [
        ('Bull Market', date(2020, 4, 1), date(2021, 4, 1)),
        ('Volatile Period', date(2022, 1, 1), date(2023, 1, 1)),
        ('Recent Period', date(2023, 6, 1), date(2024, 6, 1))
    ]
    
    config = BacktestConfig(initial_capital=100000)
    engine = BacktestEngine(config)
    optimizer = ParameterOptimizer(engine)
    
    param_space = ParameterSpace()
    param_space.add_parameter('fast_period', 'choice', [10, 15, 20])
    param_space.add_parameter('slow_period', 'choice', [30, 40, 50])
    
    period_results = {}
    
    for period_name, start_date, end_date in periods:
        print(f"\n📈 Testing {period_name} ({start_date} to {end_date})")
        
        try:
            data = provider.get_historical_data(symbol, start_date, end_date)
            if data.empty:
                continue
            
            result = optimizer.grid_search_optimize(
                strategy_class=MovingAverageCrossover,
                param_space=param_space,
                data=data,
                start_date=start_date,
                end_date=end_date,
                objective='sharpe_ratio'
            )
            
            if result:
                period_results[period_name] = result
                print(f"   Best Sharpe: {result['best_score']:.3f}")
                print(f"   Best Params: {result['best_parameters']}")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    # Analyze consistency
    if len(period_results) >= 2:
        print(f"\n🔍 Parameter Consistency Analysis:")
        
        all_params = []
        for period_name, result in period_results.items():
            params = result['best_parameters']
            all_params.append({
                'period': period_name,
                'fast_period': params['fast_period'],
                'slow_period': params['slow_period'],
                'sharpe': result['best_score']
            })
        
        params_df = pd.DataFrame(all_params)
        print(params_df.to_string(index=False))
        
        # Check parameter stability
        fast_std = params_df['fast_period'].std()
        slow_std = params_df['slow_period'].std()
        
        print(f"\n📊 Parameter Stability:")
        print(f"   Fast Period Std: {fast_std:.2f}")
        print(f"   Slow Period Std: {slow_std:.2f}")
        print(f"   Stability Score: {max(0, 1 - (fast_std + slow_std) / 20):.3f}")

if __name__ == "__main__":
    run_comprehensive_optimization()
    analyze_parameter_stability()
