"""
Strategy Parameter Optimization for Backtesting

This module provides sophisticated parameter optimization capabilities including:
- Grid search optimization
- Random search optimization  
- Bayesian optimization (using scikit-optimize)
- Walk-forward analysis
- Monte Carlo simulation for robustness testing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from datetime import date, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import product
import warnings
warnings.filterwarnings('ignore')

try:
    from skopt import gp_minimize
    from skopt.space import Real, Integer, Categorical
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False

from .engine import BacktestEngine, BacktestConfig

class ParameterSpace:
    """Define parameter space for optimization"""
    
    def __init__(self):
        self.parameters = {}
    
    def add_parameter(self, name: str, param_type: str, values: Any):
        """
        Add a parameter to optimize
        
        Args:
            name: Parameter name
            param_type: 'range', 'choice', 'integer', 'real'
            values: Range tuple, list of choices, or bounds
        """
        self.parameters[name] = {
            'type': param_type,
            'values': values
        }
    
    def get_grid_combinations(self) -> List[Dict[str, Any]]:
        """Generate all parameter combinations for grid search"""
        param_names = list(self.parameters.keys())
        param_values = []
        
        for param_name in param_names:
            param_info = self.parameters[param_name]
            
            if param_info['type'] == 'range':
                start, end, step = param_info['values']
                values = np.arange(start, end + step, step)
            elif param_info['type'] == 'choice':
                values = param_info['values']
            elif param_info['type'] in ['integer', 'real']:
                start, end = param_info['values']
                if param_info['type'] == 'integer':
                    values = list(range(int(start), int(end) + 1))
                else:
                    # For real values, create reasonable sampling
                    values = np.linspace(start, end, 10)
            else:
                values = [param_info['values']]
            
            param_values.append(values)
        
        # Generate all combinations
        combinations = []
        for combo in product(*param_values):
            param_dict = dict(zip(param_names, combo))
            combinations.append(param_dict)
        
        return combinations
    
    def get_random_sample(self, n_samples: int = 100) -> List[Dict[str, Any]]:
        """Generate random parameter combinations"""
        combinations = []
        
        for _ in range(n_samples):
            param_dict = {}
            
            for param_name, param_info in self.parameters.items():
                if param_info['type'] == 'range':
                    start, end, _ = param_info['values']
                    value = np.random.uniform(start, end)
                elif param_info['type'] == 'choice':
                    value = np.random.choice(param_info['values'])
                elif param_info['type'] == 'integer':
                    start, end = param_info['values']
                    value = np.random.randint(start, end + 1)
                elif param_info['type'] == 'real':
                    start, end = param_info['values']
                    value = np.random.uniform(start, end)
                else:
                    value = param_info['values']
                
                param_dict[param_name] = value
            
            combinations.append(param_dict)
        
        return combinations

class ParameterOptimizer:
    """Advanced parameter optimization for trading strategies"""
    
    def __init__(self, backtesting_engine: BacktestEngine = None):
        """
        Initialize parameter optimizer
        
        Args:
            backtesting_engine: BacktestEngine instance for running backtests
        """
        self.engine = backtesting_engine or BacktestEngine()
        self.logger = logging.getLogger(__name__)
        
    def grid_search(
        self,
        strategy_class,
        parameter_space: ParameterSpace,
        data: pd.DataFrame,
        optimization_metric: str = 'sharpe_ratio',
        n_jobs: int = 1,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Perform grid search optimization
        
        Args:
            strategy_class: Strategy class to optimize
            parameter_space: ParameterSpace defining optimization space
            data: Historical data for backtesting
            optimization_metric: Metric to optimize ('sharpe_ratio', 'total_return', etc.)
            n_jobs: Number of parallel jobs
            start_date: Start date for backtesting
            end_date: End date for backtesting
            
        Returns:
            Dictionary with optimization results
        """
        self.logger.info("Starting grid search optimization")
        
        combinations = parameter_space.get_grid_combinations()
        self.logger.info(f"Testing {len(combinations)} parameter combinations")
        
        if n_jobs == 1:
            results = []
            for i, params in enumerate(combinations):
                self.logger.info(f"Testing combination {i+1}/{len(combinations)}: {params}")
                result = self._evaluate_parameters(
                    strategy_class, params, data, optimization_metric, start_date, end_date
                )
                results.append(result)
        else:
            results = self._parallel_optimization(
                strategy_class, combinations, data, optimization_metric, 
                n_jobs, start_date, end_date
            )
        
        return self._process_optimization_results(results, optimization_metric)
    
    def random_search(
        self,
        strategy_class,
        parameter_space: ParameterSpace,
        data: pd.DataFrame,
        n_iterations: int = 100,
        optimization_metric: str = 'sharpe_ratio',
        n_jobs: int = 1,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Perform random search optimization
        
        Args:
            strategy_class: Strategy class to optimize
            parameter_space: ParameterSpace defining optimization space
            data: Historical data for backtesting
            n_iterations: Number of random combinations to test
            optimization_metric: Metric to optimize
            n_jobs: Number of parallel jobs
            start_date: Start date for backtesting
            end_date: End date for backtesting
            
        Returns:
            Dictionary with optimization results
        """
        self.logger.info(f"Starting random search optimization with {n_iterations} iterations")
        
        combinations = parameter_space.get_random_sample(n_iterations)
        
        if n_jobs == 1:
            results = []
            for i, params in enumerate(combinations):
                self.logger.info(f"Testing combination {i+1}/{len(combinations)}: {params}")
                result = self._evaluate_parameters(
                    strategy_class, params, data, optimization_metric, start_date, end_date
                )
                results.append(result)
        else:
            results = self._parallel_optimization(
                strategy_class, combinations, data, optimization_metric,
                n_jobs, start_date, end_date
            )
        
        return self._process_optimization_results(results, optimization_metric)
    
    def bayesian_optimization(
        self,
        strategy_class,
        parameter_space: ParameterSpace,
        data: pd.DataFrame,
        n_calls: int = 50,
        optimization_metric: str = 'sharpe_ratio',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Perform Bayesian optimization using Gaussian Process
        
        Args:
            strategy_class: Strategy class to optimize
            parameter_space: ParameterSpace defining optimization space
            data: Historical data for backtesting
            n_calls: Number of optimization iterations
            optimization_metric: Metric to optimize
            start_date: Start date for backtesting
            end_date: End date for backtesting
            
        Returns:
            Dictionary with optimization results
        """
        if not SKOPT_AVAILABLE:
            raise ImportError("scikit-optimize not available. Install with: pip install scikit-optimize")
        
        self.logger.info(f"Starting Bayesian optimization with {n_calls} calls")
        
        # Convert parameter space to skopt format
        dimensions = []
        param_names = []
        
        for param_name, param_info in parameter_space.parameters.items():
            param_names.append(param_name)
            
            if param_info['type'] == 'real' or param_info['type'] == 'range':
                if param_info['type'] == 'range':
                    start, end, _ = param_info['values']
                else:
                    start, end = param_info['values']
                dimensions.append(Real(start, end, name=param_name))
            elif param_info['type'] == 'integer':
                start, end = param_info['values']
                dimensions.append(Integer(start, end, name=param_name))
            elif param_info['type'] == 'choice':
                dimensions.append(Categorical(param_info['values'], name=param_name))
        
        def objective(params):
            """Objective function for Bayesian optimization"""
            param_dict = dict(zip(param_names, params))
            result = self._evaluate_parameters(
                strategy_class, param_dict, data, optimization_metric, start_date, end_date
            )
            # Return negative value for minimization (we want to maximize our metric)
            return -result['metric_value'] if result['metric_value'] is not None else 1e6
        
        # Run optimization
        result = gp_minimize(objective, dimensions, n_calls=n_calls, random_state=42)
        
        # Process results
        best_params = dict(zip(param_names, result.x))
        best_result = self._evaluate_parameters(
            strategy_class, best_params, data, optimization_metric, start_date, end_date
        )
        
        return {
            'best_parameters': best_params,
            'best_metric_value': best_result['metric_value'],
            'best_backtest_result': best_result['backtest_result'],
            'optimization_history': [
                {'parameters': dict(zip(param_names, x)), 'metric_value': -y}
                for x, y in zip(result.x_iters, result.func_vals)
            ],
            'n_iterations': len(result.x_iters),
            'optimization_metric': optimization_metric
        }
    
    def walk_forward_analysis(
        self,
        strategy_class,
        best_parameters: Dict[str, Any],
        data: pd.DataFrame,
        optimization_window: int = 252,  # Trading days
        test_window: int = 63,  # Trading days
        step_size: int = 21,  # Trading days
        optimization_metric: str = 'sharpe_ratio'
    ) -> Dict[str, Any]:
        """
        Perform walk-forward analysis to test strategy robustness
        
        Args:
            strategy_class: Strategy class to test
            best_parameters: Best parameters from optimization
            data: Historical data
            optimization_window: Days for optimization period
            test_window: Days for testing period
            step_size: Days to step forward each iteration
            optimization_metric: Metric to optimize in each window
            
        Returns:
            Walk-forward analysis results
        """
        self.logger.info("Starting walk-forward analysis")
        
        # Get unique dates
        dates = sorted(data['timestamp'].dt.date.unique())
        
        if len(dates) < optimization_window + test_window:
            raise ValueError("Insufficient data for walk-forward analysis")
        
        results = []
        
        for i in range(0, len(dates) - optimization_window - test_window + 1, step_size):
            # Define periods
            opt_start_idx = i
            opt_end_idx = i + optimization_window
            test_start_idx = opt_end_idx
            test_end_idx = min(test_start_idx + test_window, len(dates))
            
            opt_start_date = dates[opt_start_idx]
            opt_end_date = dates[opt_end_idx - 1]
            test_start_date = dates[test_start_idx]
            test_end_date = dates[test_end_idx - 1]
            
            self.logger.info(f"Optimization: {opt_start_date} to {opt_end_date}")
            self.logger.info(f"Testing: {test_start_date} to {test_end_date}")
            
            # Get data for periods
            opt_data = data[
                (data['timestamp'].dt.date >= opt_start_date) &
                (data['timestamp'].dt.date <= opt_end_date)
            ]
            test_data = data[
                (data['timestamp'].dt.date >= test_start_date) &
                (data['timestamp'].dt.date <= test_end_date)
            ]
            
            # Use provided parameters for testing (in real implementation, you might re-optimize)
            test_result = self._evaluate_parameters(
                strategy_class, best_parameters, test_data, optimization_metric,
                test_start_date, test_end_date
            )
            
            results.append({
                'optimization_period': (opt_start_date, opt_end_date),
                'test_period': (test_start_date, test_end_date),
                'parameters': best_parameters,
                'test_result': test_result
            })
        
        # Analyze walk-forward results
        metric_values = [r['test_result']['metric_value'] for r in results if r['test_result']['metric_value'] is not None]
        
        return {
            'walk_forward_results': results,
            'average_metric': np.mean(metric_values) if metric_values else 0,
            'std_metric': np.std(metric_values) if metric_values else 0,
            'best_period': max(results, key=lambda x: x['test_result']['metric_value'] or -np.inf),
            'worst_period': min(results, key=lambda x: x['test_result']['metric_value'] or np.inf),
            'consistency_ratio': len([v for v in metric_values if v > 0]) / len(metric_values) if metric_values else 0
        }
    
    def monte_carlo_analysis(
        self,
        strategy_class,
        parameters: Dict[str, Any],
        data: pd.DataFrame,
        n_simulations: int = 1000,
        noise_level: float = 0.001,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Perform Monte Carlo analysis by adding noise to price data
        
        Args:
            strategy_class: Strategy class to test
            parameters: Strategy parameters
            data: Historical data
            n_simulations: Number of Monte Carlo simulations
            noise_level: Level of noise to add to prices
            start_date: Start date for backtesting
            end_date: End date for backtesting
            
        Returns:
            Monte Carlo analysis results
        """
        self.logger.info(f"Starting Monte Carlo analysis with {n_simulations} simulations")
        
        results = []
        
        for i in range(n_simulations):
            if i % 100 == 0:
                self.logger.info(f"Simulation {i}/{n_simulations}")
            
            # Add noise to price data
            noisy_data = data.copy()
            price_columns = ['open_price', 'high_price', 'low_price', 'close_price']
            
            for col in price_columns:
                if col in noisy_data.columns:
                    noise = np.random.normal(0, noise_level, len(noisy_data))
                    noisy_data[col] = noisy_data[col] * (1 + noise)
            
            # Run backtest with noisy data
            result = self._evaluate_parameters(
                strategy_class, parameters, noisy_data, 'total_return', start_date, end_date
            )
            
            if result['backtest_result']:
                results.append(result['backtest_result'])
        
        if not results:
            return {'error': 'No successful simulations'}
        
        # Analyze results
        returns = [r.total_return for r in results]
        sharpe_ratios = [r.sharpe_ratio for r in results if r.sharpe_ratio is not None]
        max_drawdowns = [r.max_drawdown for r in results if r.max_drawdown is not None]
        
        return {
            'n_simulations': len(results),
            'return_statistics': {
                'mean': np.mean(returns),
                'std': np.std(returns),
                'min': np.min(returns),
                'max': np.max(returns),
                'percentile_5': np.percentile(returns, 5),
                'percentile_95': np.percentile(returns, 95)
            },
            'sharpe_statistics': {
                'mean': np.mean(sharpe_ratios) if sharpe_ratios else 0,
                'std': np.std(sharpe_ratios) if sharpe_ratios else 0,
                'min': np.min(sharpe_ratios) if sharpe_ratios else 0,
                'max': np.max(sharpe_ratios) if sharpe_ratios else 0
            },
            'drawdown_statistics': {
                'mean': np.mean(max_drawdowns) if max_drawdowns else 0,
                'std': np.std(max_drawdowns) if max_drawdowns else 0,
                'worst': np.min(max_drawdowns) if max_drawdowns else 0
            },
            'probability_positive': len([r for r in returns if r > 0]) / len(returns),
            'probability_sharpe_gt_1': len([s for s in sharpe_ratios if s > 1]) / len(sharpe_ratios) if sharpe_ratios else 0
        }
    
    def _evaluate_parameters(
        self,
        strategy_class,
        parameters: Dict[str, Any],
        data: pd.DataFrame,
        optimization_metric: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Evaluate a single parameter combination"""
        try:
            # Create strategy instance with parameters
            strategy = strategy_class(**parameters)
            
            # Run backtest
            result = self.engine.run_backtest(
                strategy, data, start_date, end_date
            )
            
            # Extract optimization metric
            metric_value = getattr(result, optimization_metric, None)
            
            return {
                'parameters': parameters,
                'metric_value': metric_value,
                'backtest_result': result
            }
            
        except Exception as e:
            self.logger.warning(f"Error evaluating parameters {parameters}: {e}")
            return {
                'parameters': parameters,
                'metric_value': None,
                'backtest_result': None,
                'error': str(e)
            }
    
    def _parallel_optimization(
        self,
        strategy_class,
        combinations: List[Dict[str, Any]],
        data: pd.DataFrame,
        optimization_metric: str,
        n_jobs: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Run optimization in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=n_jobs) as executor:
            # Submit all jobs
            future_to_params = {
                executor.submit(
                    self._evaluate_parameters,
                    strategy_class, params, data, optimization_metric, start_date, end_date
                ): params
                for params in combinations
            }
            
            # Collect results
            for i, future in enumerate(as_completed(future_to_params)):
                result = future.result()
                results.append(result)
                
                if i % 10 == 0:
                    self.logger.info(f"Completed {i+1}/{len(combinations)} combinations")
        
        return results
    
    def _process_optimization_results(
        self,
        results: List[Dict[str, Any]],
        optimization_metric: str
    ) -> Dict[str, Any]:
        """Process and summarize optimization results"""
        # Filter successful results
        successful_results = [r for r in results if r['metric_value'] is not None]
        
        if not successful_results:
            return {'error': 'No successful optimizations'}
        
        # Find best result
        best_result = max(successful_results, key=lambda x: x['metric_value'])
        
        # Calculate statistics
        metric_values = [r['metric_value'] for r in successful_results]
        
        return {
            'best_parameters': best_result['parameters'],
            'best_metric_value': best_result['metric_value'],
            'best_backtest_result': best_result['backtest_result'],
            'optimization_statistics': {
                'total_combinations': len(results),
                'successful_combinations': len(successful_results),
                'success_rate': len(successful_results) / len(results),
                'metric_mean': np.mean(metric_values),
                'metric_std': np.std(metric_values),
                'metric_min': np.min(metric_values),
                'metric_max': np.max(metric_values)
            },
            'all_results': successful_results,
            'optimization_metric': optimization_metric
        }
