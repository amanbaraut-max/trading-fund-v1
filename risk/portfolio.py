"""
Portfolio risk management - applies portfolio-level constraints.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

from config.settings import RiskConfig, get_config

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open trade position."""
    symbol: str
    shares: int
    entry_price: float
    stop_loss: float
    entry_date: str
    current_price: Optional[float] = None
    pnl: Optional[float] = None


@dataclass
class TradeRequest:
    """Request to open a position."""
    symbol: str
    shares: int
    entry_price: float
    stop_loss: float
    take_profit: Optional[float] = None


@dataclass
class TradeApproval:
    """Decision on whether to approve a trade."""
    approved: bool
    reason: str
    adjusted_shares: Optional[int] = None


class PortfolioRiskManager:
    """
    Manages portfolio-level risk constraints:
    - Max concurrent positions
    - Max daily loss
    - Max position size
    - Drawdown kill switch
    """
    
    def __init__(self, config: Optional[RiskConfig] = None):
        """
        Initialize risk manager.
        
        Args:
            config: RiskConfig with parameters
        """
        self.config = config or get_config().risk
        
        self.positions: Dict[str, Position] = {}
        self.daily_loss = 0.0
        self.monthly_loss = 0.0
        self.starting_capital = self.config.starting_capital
        self.current_capital = self.config.starting_capital
        
        logger.info(f"Initialized PortfolioRiskManager (capital: ${self.current_capital:,.0f})")
    
    def validate_trade(self, request: TradeRequest) -> TradeApproval:
        """
        Validate trade against portfolio constraints.
        
        Args:
            request: TradeRequest object
        
        Returns:
            TradeApproval with decision and reason
        """
        # Check max concurrent trades
        if len(self.positions) >= self.config.max_concurrent_trades:
            return TradeApproval(
                approved=False,
                reason=f"Max {self.config.max_concurrent_trades} concurrent trades reached"
            )
        
        # Check position size
        position_value = request.shares * request.entry_price
        position_pct = position_value / self.current_capital
        
        if position_pct > self.config.max_position_size:
            # Suggest resizing
            max_shares = int((self.current_capital * self.config.max_position_size) / request.entry_price)
            return TradeApproval(
                approved=True,
                reason=f"Position resized: {request.shares} → {max_shares} shares",
                adjusted_shares=max_shares
            )
        
        # Check daily loss limit
        if self.daily_loss >= self.current_capital * self.config.daily_loss_limit:
            return TradeApproval(
                approved=False,
                reason=f"Daily loss limit ({self.config.daily_loss_limit:.1%}) exceeded"
            )
        
        # Check risk per trade
        stop_distance = abs(request.entry_price - request.stop_loss)
        trade_risk = request.shares * stop_distance
        max_risk = self.current_capital * self.config.risk_per_trade
        
        if trade_risk > max_risk:
            return TradeApproval(
                approved=False,
                reason=f"Trade risk ${trade_risk:.0f} > max ${max_risk:.0f}"
            )
        
        return TradeApproval(approved=True, reason="Trade approved")
    
    def open_position(self, request: TradeRequest) -> bool:
        """
        Open a new position.
        
        Args:
            request: TradeRequest object
        
        Returns:
            True if successfully opened
        """
        approval = self.validate_trade(request)
        
        if not approval.approved:
            logger.warning(f"Trade rejected: {approval.reason}")
            return False
        
        # Use adjusted shares if provided
        shares = approval.adjusted_shares or request.shares
        
        position = Position(
            symbol=request.symbol,
            shares=shares,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            entry_date="",  # Will be set by execution engine
        )
        
        self.positions[request.symbol] = position
        logger.info(f"Position opened: {shares} {request.symbol} @ ${request.entry_price:.2f}")
        
        return True
    
    def close_position(self, symbol: str, exit_price: float) -> float:
        """
        Close a position and calculate P&L.
        
        Args:
            symbol: Symbol to close
            exit_price: Exit price
        
        Returns:
            P&L amount
        """
        if symbol not in self.positions:
            logger.warning(f"Position {symbol} not found")
            return 0.0
        
        pos = self.positions[symbol]
        pnl = (exit_price - pos.entry_price) * pos.shares
        
        # Update capital and loss tracking
        self.current_capital += pnl
        
        if pnl < 0:
            self.daily_loss += abs(pnl)
            self.monthly_loss += abs(pnl)
        
        del self.positions[symbol]
        logger.info(f"Position closed: {symbol} | P&L: ${pnl:.2f}")
        
        return pnl
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """
        Update current prices for open positions.
        
        Args:
            prices: Dict of {symbol: price}
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value (capital + open P&L)."""
        unrealized_pnl = sum(
            (pos.current_price - pos.entry_price) * pos.shares
            for pos in self.positions.values()
            if pos.current_price is not None
        )
        return self.current_capital + unrealized_pnl
    
    def get_exposure(self) -> float:
        """Get current portfolio exposure (% of capital)."""
        total_exposure = sum(
            pos.shares * pos.entry_price
            for pos in self.positions.values()
        )
        return total_exposure / self.current_capital
    
    def check_kill_switch(self) -> bool:
        """
        Check if drawdown exceeds limit (kill switch).
        
        Returns:
            False if kill switch triggered
        """
        portfolio_value = self.get_portfolio_value()
        drawdown = (self.starting_capital - portfolio_value) / self.starting_capital
        
        if drawdown > self.config.monthly_drawdown_limit:
            logger.critical(f"🚨 KILL SWITCH: Drawdown {drawdown:.1%} > {self.config.monthly_drawdown_limit:.1%}")
            return False
        
        return True
