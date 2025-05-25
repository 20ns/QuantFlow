# QuantFlow: Algorithmic Trading Engine

🚀 **Professional-grade algorithmic trading system for retail traders**

QuantFlow is a high-performance, open-source algorithmic trading engine that combines real-time market data processing, sophisticated backtesting capabilities, and automated strategy execution. Built with Python, it provides institutional-grade tools without the enterprise cost.

## 🌟 Features

### ✅ Week 1 Implementation (Current)
- **Data Providers**: Yahoo Finance (free) & Alpha Vantage integration
- **Portfolio Management**: Complete position tracking with P&L calculation
- **Database Storage**: SQLite-based historical data storage
- **Strategy Engine**: Moving Average Crossover strategy implemented
- **Backtesting Framework**: Historical strategy testing with performance metrics
- **Paper Trading**: Live simulation without real money
- **CLI Interface**: Easy-to-use command-line tools

### 🔮 Coming Soon
- Real-time WebSocket data streams
- Advanced strategies (RSI, MACD, Mean Reversion)
- Web dashboard with Streamlit
- Strategy optimization and walk-forward analysis
- Risk management system
- Multiple asset class support (crypto, forex)

## 🚀 Quick Start

### 1. Setup
```bash
# Clone and navigate to the project
cd QuantFlow

# Activate your virtual environment (you should already have this)
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Run the setup script
python setup.py
```

### 2. Configuration (Optional)
Edit `.env` file to add your API keys:
```bash
# Get free API key from: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY=your_api_key_here
```
*Note: Yahoo Finance works without API keys, Alpha Vantage is optional*

### 3. Try the Examples

**📊 Example 1: Data Analysis**
```bash
python examples/example_1_data_analysis.py
```

**🔙 Example 2: Backtest**
```bash
python examples/example_2_backtest.py
```

**📝 Example 3: Paper Trading**
```bash
python examples/example_3_paper_trading.py
```

### 4. Use the CLI

**Get real-time prices:**
```bash
python main.py prices -s AAPL MSFT GOOGL
```

**Run a backtest:**
```bash
python main.py backtest -s AAPL MSFT --days 90 --short-ma 10 --long-ma 20
```

**Start paper trading:**
```bash
python main.py paper-trade -s AAPL TSLA --duration 30
```

**Check status:**
```bash
python main.py status
```

## 📊 Sample Output

### Backtest Results
```
📈 BACKTEST RESULTS
════════════════════
Total Return: 12.45%
Total P&L: $12,450.00
Sharpe Ratio: 1.234
Max Drawdown: 8.20%
Win Rate: 65.2%
Total Trades: 23
```

### Portfolio Status
```
💼 PORTFOLIO
═══════════
Total Value: $112,450.00
Cash: $45,230.00
Positions: 3
P&L: $12,450.00 (12.45%)
```

## 🏗️ Architecture

```
QuantFlow/
├── src/
│   ├── data/
│   │   ├── providers/        # Yahoo Finance, Alpha Vantage
│   │   └── storage/          # SQLite database
│   ├── strategies/
│   │   └── technical/        # Moving Average, RSI, MACD
│   ├── execution/
│   │   ├── portfolio.py      # Portfolio management
│   │   └── position.py       # Position tracking
│   ├── backtesting/          # Historical testing
│   └── utils/                # Technical indicators
├── examples/                 # Example scripts
├── data/                     # Historical data storage
└── main.py                   # CLI interface
```

## 🎯 Strategy Example

```python
from src.strategies.technical.moving_average import MovingAverageCrossover

# Create strategy
strategy = MovingAverageCrossover(
    short_window=10,    # 10-day MA
    long_window=20,     # 20-day MA
    position_size=0.1   # 10% of portfolio per trade
)

# Add to engine
engine.add_strategy(strategy)
strategy.start()

# Run backtest
results = await engine.run_backtest(['AAPL'], start_date, end_date)
```

## 📈 Technical Indicators Included

- **Moving Averages**: Simple (SMA) and Exponential (EMA)
- **RSI**: Relative Strength Index
- **MACD**: Moving Average Convergence Divergence
- **Bollinger Bands**: Price volatility bands
- **Stochastic Oscillator**: Momentum indicator
- **ATR**: Average True Range (volatility)

## 🔧 API Keys Setup

### Alpha Vantage (Optional)
1. Visit: https://www.alphavantage.co/support/#api-key
2. Get free API key (5 calls/minute)
3. Add to `.env` file: `ALPHA_VANTAGE_API_KEY=your_key`

### Yahoo Finance
- No API key required
- Free unlimited access
- Primary data source

## 📦 Dependencies

- **Data**: `yfinance`, `alpha-vantage`, `pandas`, `numpy`
- **Database**: `sqlalchemy` (SQLite)
- **Technical Analysis**: Custom indicators
- **Async**: `asyncio`, `aiohttp`
- **CLI**: `click`, `rich`

## 🛡️ Risk Management

- **Paper Trading**: Test strategies without real money
- **Position Sizing**: Configurable risk per trade
- **Stop Loss**: Automated loss protection (coming soon)
- **Drawdown Monitoring**: Real-time risk tracking
- **Portfolio Limits**: Maximum exposure controls

## 📊 Performance Metrics

- **Returns**: Total and annualized returns
- **Risk**: Sharpe ratio, maximum drawdown
- **Trade Analysis**: Win rate, profit factor
- **Benchmark**: Compare against market indices
- **Visualization**: Performance charts (coming soon)

## 🔍 Week 1 Deliverables ✅

- [x] Set up data providers (Yahoo Finance, Alpha Vantage)
- [x] Implement basic portfolio and position classes
- [x] Create SQLite database schema for historical data
- [x] Build simple moving average strategy
- [x] Basic backtesting framework
- [x] Command-line interface
- [x] Example scripts and documentation

## 🚧 Coming in Week 2

- Real-time data streaming
- Advanced technical strategies
- Web dashboard with Streamlit
- Strategy optimization tools
- Enhanced risk management
- Performance visualization

## 📚 Examples Directory

- `example_1_data_analysis.py` - Fetch and analyze market data
- `example_2_backtest.py` - Complete backtesting workflow
- `example_3_paper_trading.py` - Live paper trading simulation

## 🤝 Contributing

This is a personal/educational project, but feel free to:
- Report issues
- Suggest improvements
- Share your strategies
- Add new indicators

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading involves substantial risk of loss. Never trade with money you cannot afford to lose. Past performance does not guarantee future results.

## 📄 License

MIT License - Feel free to use and modify for personal/educational use.

---

**Built with ❤️ for the trading community**