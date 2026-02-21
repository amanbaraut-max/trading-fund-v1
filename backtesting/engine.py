"""
Backtesting engine - simulates strategy trading on historical data.
Includes portfolio constraints, transaction costs, and slippage.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from config.settings import BacktestConfig, RiskConfig, get_config
from risk.position_sizing import PositionSizer
from risk.portfolio import PortfolioRiskManager, TradeRequest
from strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Record of a single trade."""
    symbol: str
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    shares: int = 0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    reason: str = ""


@dataclass
class BacktestResult:
    """Complete backtesting results."""
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    
    equity_curve: pd.Series  # Daily portfolio value
    trades: List[Trade]  # Trade list
    
    # Performance metrics
    starting_capital: float
    final_value: float
    total_return: float
    cagr: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    win_rate: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    consecutive_wins: int
    consecutive_losses: int


class BacktestEngine:
    """
    Backtesting simulation engine.
    
    Simulates:
    - Strategy signals
    - Position sizing
    - Portfolio constraints
    - Transaction costs (0.1%)
    - Slippage (1 bps)
    """
    
    def __init__(
        self,
        backtest_config: Optional[BacktestConfig] = None,
        risk_config: Optional[RiskConfig] = None,
    ):
        """
        Initialize backtesting engine.
        
        Args:
            backtest_config: Backtesting parameters
            risk_config: Risk management parameters
        """
        self.backtest_cfg = backtest_config or get_config().backtest
        self.risk_cfg = risk_config or get_config().risk
        
        self.position_sizer = PositionSizer(self.risk_cfg)
        logger.info("Initialized BacktestEngine")
    
    def run(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
    ) -> BacktestResult:
        """
        Run backtest for a strategy.
        
        Args:
            strategy: Strategy instance
            data: DataFrame with OHLCV data
        
        Returns:
            BacktestResult object
        """
        logger.info(f"Running backtest: {strategy.name} ({strategy.symbol})")
        
        if len(data) < 100:
            raise ValueError("Insufficient data for backtesting")
        
        # Generate signals
        signals = strategy.generate_signals(data)
        
        # Simulate trading
        trades, equity_curve = self._simulate_trades(
            data=data,
            signals=signals,
            strategy_name=strategy.name,
            symbol=strategy.symbol,
        )
        
        # Calculate metrics
        result = self._calculate_metrics(
            trades=trades,
            equity_curve=equity_curve,
            data=data,
            strategy_name=strategy.name,
            symbol=strategy.symbol,
        )
        
        logger.info(f"Backtest complete. Return: {result.total_return:.1%}, Sharpe: {result.sharpe_ratio:.2f}")
        
        return result
    
    def _simulate_trades(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        strategy_name: str,
        symbol: str,
    ) -> tuple[List[Trade], pd.Series]:
        """
        Simulate trading based on signals.
        
        Args:
            data: OHLCV DataFrame
            signals: Signal series (1=long, 0=flat)
            strategy_name: Strategy name
            symbol: Ticker symbol
        
        Returns:
            (trades list, equity curve Series)
        """
        trades: List[Trade] = []
        equity = [self.risk_cfg.starting_capital]
        current_position: Optional[Trade] = None
        
        # Fill NaN values in signals with 0 (no signal)
        signals = signals.fillna(0).astype(int)
        
        for i in range(1, len(data)):
            current_signal = signals.iloc[i]
            prev_signal = signals.iloc[i - 1]
            current_price = data["close"].iloc[i]
            
            # Entry signal
            if current_signal == 1 and prev_signal != 1 and current_position is None:
                # Calculate position size (simplified - using ATR approximation)
                atr = data["high"].iloc[i] - data["low"].iloc[i]
                stop_loss = current_price - (2 * atr)
                
                # Create trade request
                request = TradeRequest(
                    symbol=symbol,
                    shares=self.position_sizer.calculate_position_size(
                        portfolio_value=equity[-1],
                        entry_price=current_price,
                        stop_loss_price=stop_loss,
                    ),
                    entry_price=current_price,
                    stop_loss=stop_loss,
                )
                
                # Apply entry slippage
                request.entry_price *= (1 + self.risk_cfg.slippage_bps / 10000)
                
                current_position = Trade(
                    symbol=symbol,
                    entry_date=data.index[i],
                    entry_price=request.entry_price,
                    shares=request.shares,
                    reason="Signal entry",
                )
                
                # Append equity (no P&L yet, just opened position)
                equity.append(equity[-1])
            
            # Exit signal
            elif (current_signal == 0 or (current_signal != 1 and current_position is not None)) and current_position is not None:
                # Apply exit slippage
                exit_price = current_price * (1 - self.risk_cfg.slippage_bps / 10000)
                
                # Apply transaction costs
                exit_price *= (1 - self.risk_cfg.transaction_cost)
                
                current_position.exit_date = data.index[i]
                current_position.exit_price = exit_price
                current_position.pnl = (exit_price - current_position.entry_price) * current_position.shares
                current_position.pnl_pct = (exit_price - current_position.entry_price) / current_position.entry_price
                current_position.reason = "Signal exit"
                
                trades.append(current_position)
                equity.append(equity[-1] + current_position.pnl)
                current_position = None
            
            else:
                equity.append(equity[-1])
        
        # Close any open position
        if current_position is not None:
            exit_price = data["close"].iloc[-1]
            current_position.exit_date = data.index[-1]
            current_position.exit_price = exit_price
            current_position.pnl = (exit_price - current_position.entry_price) * current_position.shares
            current_position.pnl_pct = (exit_price - current_position.entry_price) / current_position.entry_price
            current_position.reason = "End of backtest"
            trades.append(current_position)
        
        return trades, pd.Series(equity, index=data.index)
    
    def _calculate_metrics(
        self,
        trades: List[Trade],
        equity_curve: pd.Series,
        data: pd.DataFrame,
        strategy_name: str,
        symbol: str,
    ) -> BacktestResult:
        """Calculate performance metrics."""
        starting_capital = self.risk_cfg.starting_capital
        final_value = equity_curve.iloc[-1]
        total_return = (final_value - starting_capital) / starting_capital
        
        # CAGR
        days = (data.index[-1] - data.index[0]).days
        years = days / 365.25
        cagr = ((final_value / starting_capital) ** (1 / years) - 1) if years > 0 else 0
        
        # Sharpe Ratio
        daily_returns = equity_curve.pct_change().dropna()
        sharpe = (daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0
        
        # Max Drawdown
        cummax = equity_curve.cummax()
        drawdown = (equity_curve - cummax) / cummax
        max_drawdown = abs(drawdown.min())
        
        # Trade Statistics
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        return BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=str(data.index[0].date()),
            end_date=str(data.index[-1].date()),
            equity_curve=equity_curve,
            trades=trades,
            starting_capital=starting_capital,
            final_value=final_value,
            total_return=total_return,
            cagr=cagr,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            profit_factor=profit_factor,
            win_rate=win_rate,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            avg_loss=sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0,
            consecutive_wins=self._max_consecutive(winning_trades),
            consecutive_losses=self._max_consecutive(losing_trades),
        )
    
    @staticmethod
    def _max_consecutive(trades: List[Trade]) -> int:
        """Calculate max consecutive wins/losses."""
        if not trades:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for trade in trades:
            if trade.pnl > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
