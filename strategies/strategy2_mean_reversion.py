"""
Mean Reversion Strategy
- RSI < 30 for entry
- Bollinger Band breach for confirmation
- Exit at RSI > 55 or upper band
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from config.settings import StrategyConfig, get_config
from .base_strategy import BaseStrategy, SignalOutput

logger = logging.getLogger(__name__)


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion strategy using RSI and Bollinger Bands.
    """
    
    def __init__(self, symbol: str, config: Optional[StrategyConfig] = None):
        """
        Initialize mean reversion strategy.
        
        Args:
            symbol: Ticker symbol
            config: StrategyConfig with parameters (uses system config if None)
        """
        super().__init__(name="Mean Reversion", symbol=symbol)
        
        self.config = config or get_config().strategy
        
        # Validate parameters
        assert self.config.rsi_period > 0
        assert self.config.rsi_entry < 50
        assert self.config.rsi_exit > 50
        assert self.config.bb_period > 0
        assert self.config.bb_std_dev > 0
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate mean reversion signals.
        
        Args:
            data: DataFrame with OHLCV data
        
        Returns:
            Series with signals (1=long, 0=flat, -1=short)
        """
        if len(data) < max(self.config.rsi_period, self.config.bb_period):
            return pd.Series(0, index=data.index)
        
        # Calculate indicators
        rsi = self._calc_rsi(data["close"], self.config.rsi_period)
        upper_bb, middle_bb, lower_bb = self._calc_bollinger_bands(
            data["close"],
            self.config.bb_period,
            self.config.bb_std_dev,
        )
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        buy_condition = (rsi < self.config.rsi_entry) & (data["close"] < lower_bb)
        exit_condition = (rsi > self.config.rsi_exit) | (data["close"] > upper_bb)
        
        signals[buy_condition] = 1
        signals[exit_condition] = 0
        
        return signals.fillna(0)
    
    @staticmethod
    def _calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI (Relative Strength Index)."""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)
    
    @staticmethod
    def _calc_bollinger_bands(
        close: pd.Series,
        period: int,
        std_dev: float,
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        sma = close.rolling(period).mean()
        std = close.rolling(period).std()
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        return upper, sma, lower
