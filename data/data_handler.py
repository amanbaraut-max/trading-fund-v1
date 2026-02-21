"""
Data loader module - fetches and validates OHLCV data.
Supports yfinance and CSV sources.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """Abstract base for data sources."""
    
    @abstractmethod
    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with index=date, columns=[open, high, low, close, volume]
        """
        pass


class YFinanceLoader(DataSource):
    """Load data from yfinance."""
    
    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """Fetch data from yfinance."""
        try:
            import yfinance as yf
            
            data = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                progress=False,
            )
            
            # Handle column names - yfinance can return tuple columns for single symbols
            if isinstance(data.columns, pd.MultiIndex):
                # MultiIndex columns - flatten them
                data.columns = [col[0].lower() if isinstance(col, tuple) else col.lower() 
                               for col in data.columns]
            else:
                # Regular columns - convert to lowercase
                data.columns = [col.lower() if isinstance(col, str) else str(col).lower() 
                               for col in data.columns]
            
            if data.empty:
                raise ValueError(f"No data found for {symbol}")
            
            logger.info(f"Loaded {len(data)} rows for {symbol}")
            return data
        
        except ImportError:
            logger.error("yfinance not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to load data for {symbol}: {e}")
            raise


class DataLoader:
    """Main data loading interface."""
    
    def __init__(self, source_type: str = "yfinance"):
        """
        Initialize data loader.
        
        Args:
            source_type: 'yfinance' or 'csv'
        """
        if source_type.lower() == "yfinance":
            self.source = YFinanceLoader()
        else:
            raise ValueError(f"Unknown source type: {source_type}")
        
        self._cache: Dict[str, pd.DataFrame] = {}
        logger.info(f"Initialized DataLoader with source: {source_type}")
    
    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data with caching.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Use cached data if available
        
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol}_{start_date}_{end_date}"
        
        if use_cache and cache_key in self._cache:
            logger.info(f"Using cached data for {symbol}")
            return self._cache[cache_key].copy()
        
        data = self.source.fetch(symbol, start_date, end_date)
        
        # Validate data
        self._validate_data(data, symbol)
        
        if use_cache:
            self._cache[cache_key] = data.copy()
        
        return data
    
    def fetch_multiple(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols.
        
        Args:
            symbols: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dictionary {symbol: DataFrame}
        """
        data_dict = {}
        
        for symbol in symbols:
            try:
                data_dict[symbol] = self.fetch(symbol, start_date, end_date)
            except Exception as e:
                logger.warning(f"Failed to load {symbol}: {e}")
        
        return data_dict
    
    @staticmethod
    def _validate_data(data: pd.DataFrame, symbol: str) -> None:
        """Validate OHLCV data integrity."""
        required_cols = {"open", "high", "low", "close", "volume"}
        missing = required_cols - set(data.columns)
        
        if missing:
            raise ValueError(f"Missing columns for {symbol}: {missing}")
        
        # Check for NaN values
        if data.isnull().any().any():
            logger.warning(f"Data contains NaN values for {symbol}")
            data.fillna(method="ffill", inplace=True)
        
        # Check for outliers (price should be positive)
        if (data[["open", "high", "low", "close"]] <= 0).any().any():
            raise ValueError(f"Invalid price data for {symbol}")
        
        logger.info(f"Validated data for {symbol}: {len(data)} rows")
