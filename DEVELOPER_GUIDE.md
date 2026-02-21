# Developer Guide

Advanced guide for extending and customizing the trading engine.

---

## 🏗️ Adding a New Strategy

### Step 1: Create Strategy File

Create `strategies/strategy3_yourname.py`:

```python
from typing import Optional
import pandas as pd
import numpy as np
from strategies.base_strategy import BaseStrategy, SignalOutput
from config.settings import StrategyConfig

class YourStrategy(BaseStrategy):
    """Your strategy description"""
    
    def __init__(self, symbol: str, config: StrategyConfig = None):
        self.symbol = symbol
        self.config = config or StrategyConfig()
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals
        
        Args:
            data: OHLCV dataframe with columns [open, high, low, close, volume]
        
        Returns:
            Series with signals: 1 (buy), 0 (hold), -1 (sell)
        """
        # Your indicator calculations here
        close = data['close']
        
        # Example: Simple momentum strategy
        returns = close.pct_change()
        momentum = returns.rolling(window=20).mean()
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        signals[momentum > 0.001] = 1    # Buy signal
        signals[momentum < -0.001] = -1  # Sell signal
        
        return signals
```

### Step 2: Add to Backtesting

Edit `main.py`:

```python
from strategies.strategy3_yourname import YourStrategy

# In run_backtests() function, add:
strategies = {
    "Trend Following": TrendFollowingStrategy,
    "Mean Reversion": MeanReversionStrategy,
    "Your Strategy": YourStrategy,  # Add here
}
```

### Step 3: Run

```bash
python main.py
```

Your strategy will be tested on all symbols.

---

## 📊 Using Indicators

### Built-in Helper Methods

```python
# EMA (Exponential Moving Average)
def _calc_ema(data: pd.Series, period: int) -> pd.Series:
    return data.ewm(span=period, adjust=False).mean()

# SMA (Simple Moving Average)
def simple_moving_average(data: pd.Series, period: int) -> pd.Series:
    return data.rolling(window=period).mean()

# RSI (Relative Strength Index)
def _calc_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Bollinger Bands
def _calc_bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0):
    sma = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower

# MACD (Moving Average Convergence Divergence)
def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = data.ewm(span=fast).mean()
    ema_slow = data.ewm(span=slow).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram
```

### Example: Custom Strategy with MACD

```python
class MACDStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        close = data['close']
        
        # Calculate MACD
        macd_line, signal_line, histogram = self.macd(close)
        
        # Generate signals on crossover
        signals = pd.Series(0, index=data.index)
        signals[macd_line > signal_line] = 1  # Buy
        signals[macd_line < signal_line] = -1  # Sell
        
        return signals
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
```

---

## 🛡️ Adding Risk Constraints

### Current Constraints

The portfolio manager enforces 5 constraints. To add more:

Edit `risk/portfolio.py`:

```python
class PortfolioRiskManager:
    def validate_trade(self, trade_request: TradeRequest) -> TradeApproval:
        # Existing constraints...
        
        # Add new constraint:
        if self.Your_Constraint_Check():
            return TradeApproval(
                approved=False,
                reason="Your constraint violated"
            )
        
        return TradeApproval(approved=True)
    
    def Your_Constraint_Check(self) -> bool:
        # Your logic here
        return True  # or False
```

### Example: Sector Concentration Limit

```python
def validate_sector_concentration(self, trade_request: TradeRequest) -> bool:
    """Max 30% in any sector"""
    sector = self.get_sector(trade_request.symbol)
    sector_exposure = sum(
        pos.shares * pos.current_price 
        for pos in self.active_positions.values() 
        if self.get_sector(pos.symbol) == sector
    )
    potential_exposure = sector_exposure + (trade_request.shares * trade_request.entry_price)
    
    return potential_exposure <= self.portfolio_value * 0.30
```

---

## 🎯 Modifying Backtesting Metrics

### Add Custom Metric

Edit `backtesting/engine.py`:

```python
@dataclass
class BacktestResult:
    # ... existing fields ...
    
    # Add new metric:
    recovery_factor: float = 0.0  # Profit / Max Drawdown

def _calculate_metrics(self, trades: List[Trade], equity_curve: pd.Series):
    # ... existing calculations ...
    
    # Add new calculation:
    total_profit = equity_curve.iloc[-1] - equity_curve.iloc[0]
    max_dd_amount = equity_curve.min() - equity_curve.iloc[0]
    recovery_factor = abs(total_profit / max_dd_amount) if max_dd_amount != 0 else 0
```

### Example: Calmar Ratio

```python
def _calculate_calmar_ratio(self, equity_curve: pd.Series) -> float:
    """Calmar Ratio = CAGR / Max DD"""
    cagr = self._calculate_cagr(equity_curve)
    max_dd = self._calculate_max_drawdown(equity_curve)
    
    return abs(cagr / max_dd) if max_dd != 0 else 0
```

---

## 🔌 Adding New Data Source

### For Cryptocurrency, Futures, etc.

Edit `data/data_handler.py`:

```python
class CryptoLoader(DataSource):
    """Load crypto data from Binance"""
    
    def fetch(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        # Your crypto loading logic
        import ccxt
        
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d', since=...)
        
        df = pd.DataFrame(
            ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df

class DataLoader:
    def __init__(self, source_type: str = "yfinance"):
        self.sources = {
            "yfinance": YFinanceLoader,
            "crypto": CryptoLoader,
            # Add more sources...
        }
        self.source = self.sources[source_type]()
```

---

## 🤖 Extending AI Overlay

### Phase 2: Real Sentiment Integration

Edit `ai/sentiment_overlay.py`:

```python
from newsapi import NewsApiClient  # Example API

class SentimentOverlay:
    def __init__(self, api_key: str, sentiment_threshold: float = -0.2):
        self.newsapi = NewsApiClient(api_key=api_key)
        self.sentiment_threshold = sentiment_threshold
    
    def get_sentiment(self, symbol: str) -> float:
        """Get sentiment from real news API"""
        try:
            # Fetch recent news
            articles = self.newsapi.get_everything(
                q=symbol,
                sortBy='publishedAt',
                language='en',
                page_size=10
            )
            
            # Analyze sentiment (implement your own NLP)
            sentiments = []
            for article in articles['articles']:
                sentiment = self.analyze_sentiment(article['title'])
                sentiments.append(sentiment)
            
            return np.mean(sentiments) if sentiments else 0.0
        except Exception as e:
            return 0.0  # Neutral if error
    
    def analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis (-1 to 1)"""
        from textblob import TextBlob
        
        analysis = TextBlob(text)
        return analysis.sentiment.polarity
```

---

## 📈 Advanced: Multi-Timeframe Analysis

### Combining Daily + Weekly Signals

```python
class MultiTimeFrameStrategy(BaseStrategy):
    def __init__(self, symbol: str, config: StrategyConfig = None):
        self.symbol = symbol
        self.config = config or StrategyConfig()
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Daily signals
        daily_signals = self.daily_strategy(data)
        
        # Weekly signals (resample to weekly)
        weekly_data = data.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        weekly_signals = self.weekly_strategy(weekly_data)
        
        # Combine: only take daily signal if weekly agrees
        # Resample weekly back to daily
        weekly_signals_daily = weekly_signals.reindex(data.index, method='ffill')
        
        combined = pd.Series(0, index=data.index)
        combined[(daily_signals == 1) & (weekly_signals_daily == 1)] = 1
        combined[(daily_signals == -1) & (weekly_signals_daily == -1)] = -1
        
        return combined
    
    def daily_strategy(self, data: pd.DataFrame) -> pd.Series:
        # Your daily strategy here
        pass
    
    def weekly_strategy(self, data: pd.DataFrame) -> pd.Series:
        # Your weekly strategy here
        pass
```

---

## 🧪 Testing Your Strategy

### Unit Test Example

Create `tests/test_my_strategy.py`:

```python
import pytest
import pandas as pd
import numpy as np
from strategies.strategy3_yourname import YourStrategy
from config.settings import StrategyConfig

class TestYourStrategy:
    
    def setup_method(self):
        """Setup before each test"""
        self.config = StrategyConfig()
        self.strategy = YourStrategy("TEST", self.config)
        
        # Create test data
        dates = pd.date_range('2024-01-01', periods=100)
        self.data = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 101,
            'low': np.random.randn(100).cumsum() + 99,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
    
    def test_signals_shape(self):
        """Test that output has same shape as input"""
        signals = self.strategy.generate_signals(self.data)
        assert len(signals) == len(self.data)
    
    def test_signals_valid_values(self):
        """Test that signals are 1, 0, or -1"""
        signals = self.strategy.generate_signals(self.data)
        assert all(s in [-1, 0, 1] for s in signals.values)
    
    def test_no_nan_signals(self):
        """Test that signals have no NaN values"""
        signals = self.strategy.generate_signals(self.data)
        assert not signals.isna().any()
    
    def test_performance(self):
        """Test strategy performance"""
        signals = self.strategy.generate_signals(self.data)
        
        # Calculate simple returns
        returns = self.data['close'].pct_change()
        strategy_returns = returns * signals.shift(1)
        
        # Cumulative return should be positive
        cumulative_return = (1 + strategy_returns).cumprod().iloc[-1] - 1
        print(f"Test strategy return: {cumulative_return:.2%}")
```

Run tests:
```bash
pytest tests/test_my_strategy.py -v
```

---

## 🚀 Performance Optimization

### Vectorize Calculations

**Slow (loops)**:
```python
for i in range(len(data)):
    if close.iloc[i] > ema.iloc[i]:
        signals[i] = 1
```

**Fast (vectorized)**:
```python
signals = (close > ema).astype(int)
```

### Cache Expensive Calculations

```python
from functools import lru_cache

class OptimizedStrategy(BaseStrategy):
    @lru_cache(maxsize=128)
    def expensive_calculation(self, symbol: str) -> float:
        # Only calculates once, results cached
        pass
```

### Profile Your Code

```bash
python -m cProfile -s cumulative main.py | head -20
```

---

## 🔐 Handling Edge Cases

### Missing Data

```python
def generate_signals(self, data: pd.DataFrame) -> pd.Series:
    # Fill gaps
    data = data.fillna(method='ffill')
    
    # Or drop gaps
    data = data.dropna()
    
    # Your strategy...
```

### Invalid Data

```python
def generate_signals(self, data: pd.DataFrame) -> pd.Series:
    # Validate inputs
    assert len(data) > 0, "Empty data"
    assert all(col in data.columns for col in ['open', 'high', 'low', 'close', 'volume'])
    assert (data['high'] >= data['low']).all(), "Invalid OHLC"
    
    # Your strategy...
```

---

## 📝 Documentation Standards

### Docstring Format

```python
def calculate_metric(data: pd.DataFrame, period: int = 20) -> float:
    """
    Calculate metric from data.
    
    Args:
        data: OHLCV dataframe with 'close' column
        period: Lookback period (default: 20)
    
    Returns:
        Metric value as float
    
    Raises:
        ValueError: If data is empty or period invalid
    
    Example:
        >>> df = pd.DataFrame({'close': [1, 2, 3]})
        >>> calculate_metric(df, period=2)
        2.0
    """
    if len(data) == 0:
        raise ValueError("Data cannot be empty")
    
    if period < 1:
        raise ValueError("Period must be positive")
    
    # Implementation...
    return result
```

---

## 🎓 Code Review Checklist

Before submitting new code:

- [ ] Type hints on all functions
- [ ] Docstrings with Args/Returns/Example
- [ ] No hardcoded constants (use config)
- [ ] No global variables
- [ ] Handles edge cases (empty data, NaN)
- [ ] Error messages are clear
- [ ] Code is DRY (Don't Repeat Yourself)
- [ ] Methods have single responsibility
- [ ] No circular imports
- [ ] Passes `black .` formatting
- [ ] Passes `flake8 .` linting
- [ ] Passes `mypy .` type checking
- [ ] Includes unit tests
- [ ] Works with strategy tester

---

## 🔗 Integration Checklist

When adding new component to system:

- [ ] Import in `main.py`
- [ ] Add to config if has parameters
- [ ] Include error handling
- [ ] Add logging at key points
- [ ] Update docstrings
- [ ] Add type hints
- [ ] Write tests
- [ ] Update `FILE_INDEX.md`
- [ ] Document in `README.md`

---

## 🎯 Best Practices

### 1. Keep It Simple
```python
# Good
if price > ema:
    signal = 1

# Avoid
signal = 1 if (price > ema and price != 0) else (0 if price <= ema else -1)
```

### 2. Use Meaningful Names
```python
# Good
oversold_threshold = 30
max_daily_loss = 0.02

# Avoid
t1 = 30
x = 0.02
```

### 3. Document Your Logic
```python
# Calculate RSI to detect oversold conditions
# Entry when RSI < 30 (oversold)
rsi = self.calculate_rsi(close, period=14)
oversold = rsi < self.config.rsi_entry
```

### 4. Test Edge Cases
```python
# What if data is 1 bar? 0 bars? All NaN?
# Test your strategy with edge cases
```

### 5. Profile Before Optimizing
```python
# Don't optimize blindly - profile first
python -m cProfile -s cumulative main.py
```

---

**Happy extending! 🚀**

Questions? Check:
- [README.md](README.md) - Full architecture
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Status
- [FILE_INDEX.md](FILE_INDEX.md) - File reference
