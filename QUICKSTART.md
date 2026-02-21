# Quick Start Guide

Get the trading engine running in 5 minutes.

## Prerequisites

- Python 3.8+
- pip

## 1. Activate Virtual Environment

Windows:
```bash
.\venv\Scripts\Activate.ps1
```

Linux/Mac:
```bash
source venv/bin/activate
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Takes 2-3 minutes. Tea break time ☕

## 3. Verify Setup

```bash
python verify_setup.py
```

Should show:
```
SUCCESS: All imports verified ✓
SUCCESS: Configuration verified ✓
SUCCESS: Data loading verified ✓
```

If errors, check:
- Are you in the right directory?
- Is virtual environment activated?
- Did all packages install? (`pip list`)

## 4. Run Backtests

```bash
python main.py
```

Output:
```
======================================================================
STARTING BACKTESTING
======================================================================

Testing strategies on SPY
Trend Following:
  Total Return: 45.3%
  CAGR: 4.2%
  Sharpe Ratio: 1.23
  Max Drawdown: 18.5%
  Profit Factor: 1.87
  Win Rate: 52.3%
  Trades: 42
...
```

## 5. View Dashboard

```bash
streamlit run dashboard/app.py
```

Opens browser to http://localhost:8501

## Configuration

Edit `config/settings.py` to change:
- Starting capital (default: $25,000)
- Risk per trade (default: 1%)
- Symbols to backtest
- Strategy parameters
- Date ranges

After changes, just re-run `python main.py`

## Troubleshooting

### "ModuleNotFoundError: numpy"
```bash
pip install -r requirements.txt
```

### "No module named 'streamlit'"
```bash
pip install streamlit plotly
```

### Data download takes too long
First run is slow (fetches 10 years of data). Cached after first run.

### IBKR connection fails
TWS not required for backtesting, only for live execution.

### My results look weird
Check `config/settings.py` - ensure dates/symbols match your intent.

## Next Steps

1. **Read** [README.md](README.md) for full documentation
2. **Explore** [PROJECT_STATUS.md](PROJECT_STATUS.md) for architecture details
3. **Modify** [config/settings.py](config/settings.py) for your parameters
4. **Extend** with your own strategies (see [strategies/base_strategy.py](strategies/base_strategy.py))

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Run backtests |
| `config/settings.py` | All parameters |
| `strategies/` | Strategy implementations |
| `dashboard/app.py` | View results |
| `verify_setup.py` | Test setup |

## Commands Reference

```bash
# Run backtests
python main.py

# View dashboard
streamlit run dashboard/app.py

# Verify setup
python verify_setup.py

# Format code
black .

# Type check
mypy .

# Lint
flake8 .

# Run tests
pytest tests/
```

## Architecture (Quick Version)

```
Data → Strategies → Risk Manager → Backtest Engine → Dashboard
```

- **Data**: yfinance (OHLCV)
- **Strategies**: Trend Following (EMA), Mean Reversion (RSI)
- **Risk**: Position sizing, portfolio constraints
- **Backtest**: Realistic simulation with costs
- **Dashboard**: Interactive Streamlit UI

## Success Indicators

✓ `verify_setup.py` runs without errors  
✓ `main.py` displays metrics  
✓ `streamlit run dashboard/app.py` opens in browser  
✓ Dashboard shows backtest results  

## Need Help?

1. Check [README.md](README.md)
2. Review logs: `cat logs/trading_fund.log`
3. Enable debug: Change `config.logging.level = "DEBUG"`
4. Read docstrings: `python -c "from strategies.base_strategy import BaseStrategy; help(BaseStrategy)"`

---

**Happy trading! 🚀**
