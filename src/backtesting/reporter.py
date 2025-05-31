"""
Backtesting Report Generator

This module provides comprehensive reporting capabilities for backtesting results including:
- HTML reports with charts and metrics
- CSV exports of trades and performance
- Risk analysis reports
- Comparison reports for multiple strategies
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime
import logging
import json
import os

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

from .metrics import PerformanceMetrics

class BacktestReporter:
    """Generate comprehensive backtesting reports"""
    
    def __init__(self, output_dir: str = "results"):
        """
        Initialize reporter
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_full_report(
        self,
        backtest_result,
        strategy_name: str,
        include_plots: bool = True,
        include_trades: bool = True
    ) -> Dict[str, str]:
        """
        Generate a comprehensive backtest report
        
        Args:
            backtest_result: BacktestResult object
            strategy_name: Name of the strategy
            include_plots: Whether to include plots
            include_trades: Whether to include trade details
            
        Returns:
            Dictionary with file paths of generated reports
        """
        self.logger.info(f"Generating full report for {strategy_name}")
        
        report_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{strategy_name}_{timestamp}"
        
        # Generate HTML report
        html_file = os.path.join(self.output_dir, f"{base_filename}_report.html")
        self._generate_html_report(backtest_result, html_file, include_plots)
        report_files['html'] = html_file
        
        # Generate CSV exports
        if include_trades and not backtest_result.trade_history.empty:
            trades_file = os.path.join(self.output_dir, f"{base_filename}_trades.csv")
            backtest_result.trade_history.to_csv(trades_file, index=False)
            report_files['trades_csv'] = trades_file
        
        # Portfolio history CSV
        if not backtest_result.portfolio_history.empty:
            portfolio_file = os.path.join(self.output_dir, f"{base_filename}_portfolio.csv")
            backtest_result.portfolio_history.to_csv(portfolio_file, index=False)
            report_files['portfolio_csv'] = portfolio_file
        
        # Metrics JSON
        metrics_file = os.path.join(self.output_dir, f"{base_filename}_metrics.json")
        with open(metrics_file, 'w') as f:
            json.dump(backtest_result.metrics, f, indent=2, default=str)
        report_files['metrics_json'] = metrics_file
        
        # Generate plots if requested
        if include_plots and PLOTTING_AVAILABLE:
            plots_dir = os.path.join(self.output_dir, f"{base_filename}_plots")
            os.makedirs(plots_dir, exist_ok=True)
            plot_files = self._generate_plots(backtest_result, plots_dir)
            report_files.update(plot_files)
        
        self.logger.info(f"Report generated: {report_files}")
        return report_files
    
    def generate_comparison_report(
        self,
        backtest_results: List[Tuple[str, Any]],
        output_filename: str = None
    ) -> str:
        """
        Generate a comparison report for multiple strategies
        
        Args:
            backtest_results: List of (strategy_name, backtest_result) tuples
            output_filename: Custom output filename
            
        Returns:
            Path to generated comparison report
        """
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"strategy_comparison_{timestamp}.html"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Create comparison DataFrame
        comparison_data = []
        for strategy_name, result in backtest_results:
            row = {
                'Strategy': strategy_name,
                'Total Return': f"{result.total_return:.2%}",
                'Annual Return': f"{result.annual_return:.2%}",
                'Volatility': f"{result.volatility:.2%}",
                'Sharpe Ratio': f"{result.sharpe_ratio:.2f}",
                'Max Drawdown': f"{result.max_drawdown:.2%}",
                'Calmar Ratio': f"{result.calmar_ratio:.2f}",
                'Win Rate': f"{result.win_rate:.2%}",
                'Total Trades': result.total_trades,
                'Final Value': f"${result.final_value:,.2f}"
            }
            comparison_data.append(row)
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Generate HTML
        html_content = self._create_comparison_html(comparison_df, backtest_results)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_html_report(
        self,
        backtest_result,
        output_path: str,
        include_plots: bool = True
    ):
        """Generate comprehensive HTML report"""
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backtest Report - {backtest_result.strategy_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .metric-card {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #007acc; }}
                .metric-title {{ font-weight: bold; color: #333; }}
                .metric-value {{ font-size: 1.2em; color: #007acc; }}
                .section {{ margin: 30px 0; }}
                .section h2 {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 5px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                .plot-container {{ text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Backtest Report: {backtest_result.strategy_name}</h1>
                <p><strong>Period:</strong> {backtest_result.start_date} to {backtest_result.end_date}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        # Add key metrics
        html_content += self._create_metrics_section(backtest_result)
        
        # Add performance summary
        html_content += self._create_performance_section(backtest_result)
        
        # Add risk metrics
        html_content += self._create_risk_section(backtest_result)
        
        # Add trade analysis
        if not backtest_result.trade_history.empty:
            html_content += self._create_trade_analysis_section(backtest_result)
        
        # Add plots section placeholder
        if include_plots and PLOTTING_AVAILABLE:
            html_content += """
            <div class="section">
                <h2>📊 Performance Charts</h2>
                <p>Charts saved separately in plots directory</p>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _create_metrics_section(self, backtest_result) -> str:
        """Create key metrics section"""
        return f"""
        <div class="section">
            <h2>📈 Key Performance Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">Total Return</div>
                    <div class="metric-value {'positive' if backtest_result.total_return > 0 else 'negative'}">
                        {backtest_result.total_return:.2%}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Annual Return</div>
                    <div class="metric-value {'positive' if backtest_result.annual_return > 0 else 'negative'}">
                        {backtest_result.annual_return:.2%}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Volatility</div>
                    <div class="metric-value">{backtest_result.volatility:.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Sharpe Ratio</div>
                    <div class="metric-value {'positive' if backtest_result.sharpe_ratio > 0 else 'negative'}">
                        {backtest_result.sharpe_ratio:.2f}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Max Drawdown</div>
                    <div class="metric-value negative">{backtest_result.max_drawdown:.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Calmar Ratio</div>
                    <div class="metric-value">{backtest_result.calmar_ratio:.2f}</div>
                </div>
            </div>
        </div>
        """
    
    def _create_performance_section(self, backtest_result) -> str:
        """Create performance summary section"""
        return f"""
        <div class="section">
            <h2>💰 Performance Summary</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Initial Capital</td><td>${backtest_result.initial_capital:,.2f}</td></tr>
                <tr><td>Final Value</td><td>${backtest_result.final_value:,.2f}</td></tr>
                <tr><td>Total Profit/Loss</td><td class="{'positive' if backtest_result.final_value > backtest_result.initial_capital else 'negative'}">${backtest_result.final_value - backtest_result.initial_capital:,.2f}</td></tr>
                <tr><td>Win Rate</td><td>{backtest_result.win_rate:.2%}</td></tr>
                <tr><td>Profit Factor</td><td>{backtest_result.profit_factor:.2f}</td></tr>
                <tr><td>Total Trades</td><td>{backtest_result.total_trades}</td></tr>
                <tr><td>Avg Trade Duration</td><td>{backtest_result.avg_trade_duration:.1f} days</td></tr>
            </table>
        </div>
        """
    
    def _create_risk_section(self, backtest_result) -> str:
        """Create risk analysis section"""
        metrics = backtest_result.metrics
        
        return f"""
        <div class="section">
            <h2>⚠️ Risk Analysis</h2>
            <table>
                <tr><th>Risk Metric</th><th>Value</th></tr>
                <tr><td>Value at Risk (95%)</td><td>{metrics.get('var_95', 'N/A')}</td></tr>
                <tr><td>Conditional VaR (95%)</td><td>{metrics.get('cvar_95', 'N/A')}</td></tr>
                <tr><td>Skewness</td><td>{metrics.get('skewness', 'N/A')}</td></tr>
                <tr><td>Kurtosis</td><td>{metrics.get('kurtosis', 'N/A')}</td></tr>
                <tr><td>Sortino Ratio</td><td>{metrics.get('sortino_ratio', 'N/A')}</td></tr>
                <tr><td>Maximum Drawdown Duration</td><td>{metrics.get('max_drawdown_duration', 'N/A')} days</td></tr>
            </table>
        </div>
        """
    
    def _create_trade_analysis_section(self, backtest_result) -> str:
        """Create trade analysis section"""
        trades = backtest_result.trade_history
        
        if trades.empty:
            return ""
        
        # Calculate trade statistics
        winning_trades = trades[trades['pnl'] > 0]
        losing_trades = trades[trades['pnl'] < 0]
        
        return f"""
        <div class="section">
            <h2>📊 Trade Analysis</h2>
            <table>
                <tr><th>Trade Statistic</th><th>Value</th></tr>
                <tr><td>Total Trades</td><td>{len(trades)}</td></tr>
                <tr><td>Winning Trades</td><td>{len(winning_trades)}</td></tr>
                <tr><td>Losing Trades</td><td>{len(losing_trades)}</td></tr>
                <tr><td>Win Rate</td><td>{len(winning_trades)/len(trades):.2%}</td></tr>
                <tr><td>Average Win</td><td class="positive">${winning_trades['pnl'].mean():.2f}</td></tr>
                <tr><td>Average Loss</td><td class="negative">${losing_trades['pnl'].mean():.2f}</td></tr>
                <tr><td>Largest Win</td><td class="positive">${winning_trades['pnl'].max():.2f}</td></tr>
                <tr><td>Largest Loss</td><td class="negative">${losing_trades['pnl'].min():.2f}</td></tr>
            </table>
            
            <h3>Recent Trades</h3>
            {trades.tail(10).to_html(classes='table', table_id='trades-table')}
        </div>
        """
    
    def _create_comparison_html(
        self,
        comparison_df: pd.DataFrame,
        backtest_results: List[Tuple[str, Any]]
    ) -> str:
        """Create HTML for strategy comparison"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Strategy Comparison Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
                th {{ background-color: #f2f2f2; }}
                .best {{ background-color: #d4edda; }}
                .worst {{ background-color: #f8d7da; }}
                .section {{ margin: 30px 0; }}
                .section h2 {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Strategy Comparison Report</h1>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Strategies Compared:</strong> {len(backtest_results)}</p>
            </div>
            
            <div class="section">
                <h2>📊 Performance Comparison</h2>
                {comparison_df.to_html(classes='table', table_id='comparison-table', escape=False)}
            </div>
            
            <div class="section">
                <h2>📈 Analysis Summary</h2>
                <p>Best performing strategy by total return: <strong>{comparison_df.loc[comparison_df['Total Return'].str.rstrip('%').astype(float).idxmax(), 'Strategy']}</strong></p>
                <p>Best Sharpe ratio: <strong>{comparison_df.loc[comparison_df['Sharpe Ratio'].astype(float).idxmax(), 'Strategy']}</strong></p>
                <p>Lowest drawdown: <strong>{comparison_df.loc[comparison_df['Max Drawdown'].str.rstrip('%').astype(float).idxmin(), 'Strategy']}</strong></p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_plots(self, backtest_result, plots_dir: str) -> Dict[str, str]:
        """Generate performance plots"""
        if not PLOTTING_AVAILABLE:
            return {}
        
        plot_files = {}
        
        # Set style
        plt.style.use('seaborn-v0_8')
        
        # 1. Portfolio value over time
        if not backtest_result.portfolio_history.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            portfolio_data = backtest_result.portfolio_history
            ax.plot(pd.to_datetime(portfolio_data['date']), portfolio_data['portfolio_value'])
            ax.set_title('Portfolio Value Over Time')
            ax.set_xlabel('Date')
            ax.set_ylabel('Portfolio Value ($)')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            portfolio_plot = os.path.join(plots_dir, 'portfolio_value.png')
            plt.savefig(portfolio_plot, dpi=300, bbox_inches='tight')
            plt.close()
            plot_files['portfolio_value'] = portfolio_plot
        
        # 2. Drawdown chart
        if not backtest_result.portfolio_history.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            portfolio_data = backtest_result.portfolio_history
            portfolio_values = portfolio_data['portfolio_value']
            running_max = portfolio_values.expanding().max()
            drawdown = (portfolio_values - running_max) / running_max
            
            ax.fill_between(pd.to_datetime(portfolio_data['date']), drawdown, 0, alpha=0.3, color='red')
            ax.plot(pd.to_datetime(portfolio_data['date']), drawdown, color='red')
            ax.set_title('Drawdown Over Time')
            ax.set_xlabel('Date')
            ax.set_ylabel('Drawdown (%)')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            drawdown_plot = os.path.join(plots_dir, 'drawdown.png')
            plt.savefig(drawdown_plot, dpi=300, bbox_inches='tight')
            plt.close()
            plot_files['drawdown'] = drawdown_plot
        
        # 3. Monthly returns heatmap
        if not backtest_result.portfolio_history.empty:
            portfolio_data = backtest_result.portfolio_history
            portfolio_data['date'] = pd.to_datetime(portfolio_data['date'])
            monthly_returns = portfolio_data.set_index('date')['portfolio_value'].resample('M').last().pct_change().dropna()
            
            if len(monthly_returns) > 12:
                # Create pivot table for heatmap
                returns_df = monthly_returns.to_frame('returns')
                returns_df['year'] = returns_df.index.year
                returns_df['month'] = returns_df.index.month
                heatmap_data = returns_df.pivot('year', 'month', 'returns')
                
                fig, ax = plt.subplots(figsize=(12, 8))
                sns.heatmap(heatmap_data, annot=True, fmt='.2%', cmap='RdYlGn', center=0, ax=ax)
                ax.set_title('Monthly Returns Heatmap')
                plt.tight_layout()
                
                heatmap_plot = os.path.join(plots_dir, 'monthly_returns_heatmap.png')
                plt.savefig(heatmap_plot, dpi=300, bbox_inches='tight')
                plt.close()
                plot_files['monthly_heatmap'] = heatmap_plot
        
        # 4. Trade distribution
        if not backtest_result.trade_history.empty:
            trades = backtest_result.trade_history
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # PnL distribution
            ax1.hist(trades['pnl'], bins=30, alpha=0.7, edgecolor='black')
            ax1.axvline(x=0, color='red', linestyle='--', alpha=0.7)
            ax1.set_title('Trade P&L Distribution')
            ax1.set_xlabel('P&L ($)')
            ax1.set_ylabel('Frequency')
            ax1.grid(True, alpha=0.3)
            
            # Trade returns
            if 'return_pct' in trades.columns:
                ax2.hist(trades['return_pct'], bins=30, alpha=0.7, edgecolor='black')
                ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7)
                ax2.set_title('Trade Return Distribution')
                ax2.set_xlabel('Return (%)')
                ax2.set_ylabel('Frequency')
            else:
                ax2.text(0.5, 0.5, 'Return data not available', ha='center', va='center', transform=ax2.transAxes)
            
            ax2.grid(True, alpha=0.3)
            plt.tight_layout()
            
            trade_dist_plot = os.path.join(plots_dir, 'trade_distribution.png')
            plt.savefig(trade_dist_plot, dpi=300, bbox_inches='tight')
            plt.close()
            plot_files['trade_distribution'] = trade_dist_plot
        
        return plot_files
    
    def export_to_csv(
        self,
        backtest_result,
        strategy_name: str,
        include_portfolio: bool = True,
        include_trades: bool = True
    ) -> Dict[str, str]:
        """
        Export backtest results to CSV files
        
        Args:
            backtest_result: BacktestResult object
            strategy_name: Name of the strategy
            include_portfolio: Export portfolio history
            include_trades: Export trade history
            
        Returns:
            Dictionary with paths to exported files
        """
        exported_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if include_portfolio and not backtest_result.portfolio_history.empty:
            portfolio_file = os.path.join(
                self.output_dir, 
                f"{strategy_name}_portfolio_{timestamp}.csv"
            )
            backtest_result.portfolio_history.to_csv(portfolio_file, index=False)
            exported_files['portfolio'] = portfolio_file
        
        if include_trades and not backtest_result.trade_history.empty:
            trades_file = os.path.join(
                self.output_dir,
                f"{strategy_name}_trades_{timestamp}.csv"
            )
            backtest_result.trade_history.to_csv(trades_file, index=False)
            exported_files['trades'] = trades_file
        
        # Export summary metrics
        summary_data = {
            'Strategy': [strategy_name],
            'Start Date': [backtest_result.start_date],
            'End Date': [backtest_result.end_date],
            'Initial Capital': [backtest_result.initial_capital],
            'Final Value': [backtest_result.final_value],
            'Total Return': [backtest_result.total_return],
            'Annual Return': [backtest_result.annual_return],
            'Volatility': [backtest_result.volatility],
            'Sharpe Ratio': [backtest_result.sharpe_ratio],
            'Max Drawdown': [backtest_result.max_drawdown],
            'Calmar Ratio': [backtest_result.calmar_ratio],
            'Win Rate': [backtest_result.win_rate],
            'Profit Factor': [backtest_result.profit_factor],
            'Total Trades': [backtest_result.total_trades]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_file = os.path.join(
            self.output_dir,
            f"{strategy_name}_summary_{timestamp}.csv"
        )
        summary_df.to_csv(summary_file, index=False)
        exported_files['summary'] = summary_file
        
        return exported_files
