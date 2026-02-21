"""
Trend Following Strategy
- 20 EMA > 50 EMA for trend
- Price > 200 EMA for long-term filter
- ADX > threshold for trend strength
- ATR for stop loss sizing
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from config.settings import StrategyConfig, get_config
from .base_strategy import BaseStrategy, SignalOutput

logger = logging.getLogger(__name__)


class TrendFollowingStrategy(BaseStrategy):
    """
    Trend following strategy using EMA crossovers and ADX confirmation.
    """
    
    def __init__(self, symbol: str, config: Optional[StrategyConfig] = None):
        """
        Initialize trend following strategy.
        
        Args:
            symbol: Ticker symbol
            config: StrategyConfig with parameters (uses system config if None)
        """
        super().__init__(name="Trend Following", symbol=symbol)
        
        self.config = config or get_config().strategy
        
        # Validate parameters
        assert self.config.ema_fast > 0
        assert self.config.ema_slow > self.config.ema_fast
        assert self.config.ema_long > self.config.ema_slow
        assert self.config.adx_threshold > 0
        assert self.config.atr_multiplier > 0
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trend following signals.
        
        Args:
            data: DataFrame with OHLCV data
        
        Returns:
            Series with signals (1=long, 0=flat, -1=short)
        """
        if len(data) < self.config.ema_long:
            return pd.Series(0, index=data.index)
        
        # Calculate indicators
        ema_fast = self._calc_ema(data["close"], self.config.ema_fast)
        ema_slow = self._calc_ema(data["close"], self.config.ema_slow)
        ema_long = self._calc_ema(data["close"], self.config.ema_long)
        adx = self._calc_adx(data)
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        buy_condition = (ema_fast > ema_slow) & (data["close"] > ema_long) & (adx > self.config.adx_threshold)
        sell_condition = (ema_fast < ema_slow) | (data["close"] < ema_long)
        
        signals[buy_condition] = 1
        signals[sell_condition] = 0
        
        return signals.fillna(0)
    
    @staticmethod
    def _calc_ema(close: pd.Series, period: int) -> pd.Series:
        """Calculate EMA."""
        return close.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def _calc_adx(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ADX (simplified)."""
        high = data["high"]
        low = data["low"]
        close = data["close"]
        
        plus_dm = high.diff()
        plus_dm[plus_dm < 0] = 0
        
        minus_dm = -low.diff()
        minus_dm[minus_dm < 0] = 0
        
        tr = np.maximum(
            high - low,
            np.maximum(
                abs(high - close.shift(1)),
                abs(low - close.shift(1)),
            ),
        )
        
        plus_di = 100 * (plus_dm.rolling(period).mean() / tr.rolling(period).mean())
        minus_di = 100 * (minus_dm.rolling(period).mean() / tr.rolling(period).mean())
        
        di_diff = abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        
        adx = 100 * (di_diff / di_sum).rolling(period).mean()
        
        return adx.fillna(0)
