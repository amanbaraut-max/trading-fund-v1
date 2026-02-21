"""
AI Sentiment Overlay - advisory signals only.
Never directly executes trades.
Can be removed if it doesn't improve performance.
"""

import logging
from typing import Optional

import pandas as pd

from config.settings import get_config

logger = logging.getLogger(__name__)


class SentimentOverlay:
    """
    Sentiment analysis for filtering/confidence adjustment.
    
    Returns sentiment scoring between -1 (bearish) and +1 (bullish).
    
    Phase 1: Stub implementation
    Phase 2: Integrate with news API, social media, etc.
    """
    
    def __init__(self, sentiment_threshold: float = -0.2):
        """
        Initialize sentiment overlay.
        
        Args:
            sentiment_threshold: Only allow longs if sentiment > threshold
        """
        self.sentiment_threshold = sentiment_threshold
        self.sentiment_cache = {}
        logger.info(f"Initialized SentimentOverlay (threshold: {sentiment_threshold})")
    
    def get_sentiment(
        self,
        symbol: str,
        date: Optional[pd.Timestamp] = None,
    ) -> float:
        """
        Get sentiment score for a symbol.
        
        Args:
            symbol: Ticker symbol
            date: Date for historical sentiment (optional)
        
        Returns:
            Sentiment score between -1 and +1
        """
        # TODO: Implement real sentiment sources:
        # - News API sentiment analysis
        # - Financial news scraping
        # - Social media sentiment
        # - VIX levels
        # - Market breadth indicators
        
        cache_key = f"{symbol}_{date}"
        if cache_key in self.sentiment_cache:
            return self.sentiment_cache[cache_key]
        
        # Stub: Return neutral sentiment for now
        sentiment_score = 0.0
        
        logger.debug(f"Sentiment for {symbol}: {sentiment_score:.2f}")
        self.sentiment_cache[cache_key] = sentiment_score
        
        return sentiment_score
    
    def evaluate_signal(self, symbol: str, signal: int, sentiment_score: Optional[float] = None) -> (bool, float):
        """
        Evaluate if signal should be executed based on sentiment.
        
        Args:
            symbol: Ticker symbol
            signal: 1 (long), 0 (flat), -1 (short)
            sentiment_score: Sentiment score (-1 to +1)
        
        Returns:
            (approved: bool, confidence_adjustment: float)
            - approved: Whether signal can proceed
            - confidence_adjustment: Adjustment to signal confidence
        """
        if sentiment_score is None:
            sentiment_score = self.get_sentiment(symbol)
        
        # Only allow LONG trades if sentiment is not too bearish
        if signal == 1:
            if sentiment_score < self.sentiment_threshold:
                return False, -0.5  # Reject signal
            else:
                # Boost confidence if sentiment agrees
                adjustment = min(0.3, sentiment_score * 0.5)
                return True, adjustment
        
        # Always allow SHORT trades
        if signal == -1:
            return True, 0.0
        
        # Flat (hold)
        return True, 0.0
    
    def calibrate(
        self,
        backtest_results_with_ai: dict,
        backtest_results_without_ai: dict,
    ) -> bool:
        """
        Determine if AI improves system performance.
        
        If improvement < threshold, recommend removing AI.
        
        Args:
            backtest_results_with_ai: Backtest with sentiment overlay
            backtest_results_without_ai: Backtest without sentiment
        
        Returns:
            True if AI should be kept, False if removed
        """
        sharpe_improvement = (
            backtest_results_with_ai.get("sharpe", 0)
            - backtest_results_without_ai.get("sharpe", 0)
        )
        
        dd_improvement = (
            backtest_results_without_ai.get("max_drawdown", 1)
            - backtest_results_with_ai.get("max_drawdown", 1)
        )
        
        keep = (sharpe_improvement > 0.1) or (dd_improvement > 0.02)
        
        logger.info(f"AI Calibration:")
        logger.info(f"  Sharpe improvement: {sharpe_improvement:+.2f}")
        logger.info(f"  Drawdown improvement: {dd_improvement:+.2%}")
        logger.info(f"  Result: {'KEEP AI' if keep else 'REMOVE AI'}")
        
        return keep
