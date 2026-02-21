"""
Position sizing module - calculates position size based on risk parameters.
"""

import logging
from typing import Optional

from config.settings import RiskConfig, get_config

logger = logging.getLogger(__name__)


class PositionSizer:
    """
    Calculates position size using risk-based formula.
    
    Position Size = (Risk Amount) / (Stop Distance)
    Risk Amount = Portfolio Value × Risk %
    """
    
    def __init__(self, config: Optional[RiskConfig] = None):
        """
        Initialize position sizer.
        
        Args:
            config: RiskConfig with parameters
        """
        self.config = config or get_config().risk
        logger.info(f"Initialized PositionSizer (risk: {self.config.risk_per_trade:.1%})")
    
    def calculate_position_size(
        self,
        portfolio_value: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> int:
        """
        Calculate position size (shares to buy).
        
        Formula:
            risk_amount = portfolio_value × risk_per_trade
            position_size = risk_amount / (entry_price - stop_loss)
        
        Args:
            portfolio_value: Current portfolio value
            entry_price: Entry price
            stop_loss_price: Stop loss price
        
        Returns:
            Number of shares to buy
        """
        stop_distance = abs(entry_price - stop_loss_price)
        
        if stop_distance == 0:
            logger.warning("Stop distance is 0, cannot size position")
            return 0
        
        risk_amount = portfolio_value * self.config.risk_per_trade
        position_size = risk_amount / stop_distance
        
        # Cap by max position size (10% of capital)
        max_position_value = portfolio_value * self.config.max_position_size
        max_shares = max_position_value / entry_price
        
        position_size = min(position_size, max_shares)
        
        return int(position_size)
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        atr_multiplier: float = 2.0,
    ) -> float:
        """
        Calculate stop loss price using ATR.
        
        Args:
            entry_price: Entry price
            atr: Average True Range
            atr_multiplier: Multiplier (typically 2.0)
        
        Returns:
            Stop loss price
        """
        return entry_price - (atr * atr_multiplier)
    
    def calculate_take_profit(
        self,
        entry_price: float,
        risk_reward_ratio: float = 2.0,
        atr: float = None,
        atr_multiplier: float = 2.0,
    ) -> float:
        """
        Calculate take profit price.
        
        Args:
            entry_price: Entry price
            risk_reward_ratio: Reward/Risk ratio (e.g., 2.0 = 2:1)
            atr: Average True Range (if using ATR method)
            atr_multiplier: Multiplier
        
        Returns:
            Take profit price
        """
        if atr is not None:
            stop_distance = atr * atr_multiplier
        else:
            stop_distance = entry_price * 0.02  # Default 2% stop
        
        reward_distance = stop_distance * risk_reward_ratio
        return entry_price + reward_distance
