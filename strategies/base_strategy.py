"""
Abstract base strategy class defining the strategy interface.
All strategies must inherit from BaseStrategy.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class SignalOutput:
    """Output from strategy signal generation."""
    signal: int  # 1 (long), 0 (flat), -1 (short)
    stop_loss: float | None = None
    take_profit: float | None = None
    confidence: float = 1.0  # 0-1, how confident in signal


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Strategies must implement generate_signals() which takes a DataFrame
    and returns a Series of signals (1, 0, -1).
    """
    
    def __init__(self, name: str, symbol: str):
        """
        Initialize strategy.
        
        Args:
            name: Strategy name
            symbol: Ticker symbol this strategy trades
        """
        self.name = name
        self.symbol = symbol
        logger.info(f"Initialized strategy: {name} for {symbol}")
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals from price data.
        
        Args:
            data: DataFrame with columns [open, high, low, close, volume]
                  Index: datetime
        
        Returns:
            Series with index=datetime, values=signal (1, 0, -1)
        """
        pass
    
    def validate(self) -> bool:
        """Validate strategy parameters. Override if needed."""
        return True
