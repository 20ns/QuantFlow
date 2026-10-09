# QuantFlow

QuantFlow is an experimental Python project for market-data ingestion, strategy backtesting, and paper trading. It explores how data providers, trading strategies, portfolio tracking, and historical simulations fit together.

End-to-end operation has not been verified, and some integration work remains.

## What is included

- Yahoo Finance and Alpha Vantage data-provider modules.
- Historical data storage using SQLite.
- A moving-average crossover strategy and a strategy interface.
- Portfolio and position tracking.
- Backtesting, performance-metric calculations, parameter optimisation, and reporting modules.
- Streaming and paper-trading entry points.
- A Rich terminal status display.

The status display is a terminal component, not a Streamlit web dashboard. Performance benchmarks, strategy returns, test coverage, and production readiness have not been verified.

## Setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/20ns/QuantFlow.git
cd QuantFlow
python -m venv .venv
```

Activate the environment:

```bash
source .venv/bin/activate
```

On Windows, use `.venv\Scripts\activate` instead.

Install the dependencies:

```bash
pip install -r requirements.txt
```

See `.env.example` for configuration options and optional provider credentials.

## Exploring the code

`main.py` provides the command-line entry point. Inspect its available commands with:

```bash
python main.py --help
```

The `examples/` directory contains data-analysis, backtesting, optimisation, and paper-trading examples. These are starting points for inspecting the implementation; some workflows remain incomplete.

## Checking components

```bash
python test_week2.py
```

This manual smoke script checks component setup. It does not measure coverage or establish end-to-end correctness.

See [Week 2 implementation status](WEEK2_IMPLEMENTATION_STATUS.md) for the documented integration limits, including unresolved asynchronous signal generation.
