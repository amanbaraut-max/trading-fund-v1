"""
Centralized configuration using dataclasses.
No hardcoded constants anywhere else in codebase.
"""

from dataclasses import dataclass, field
from typing import List
from enum import Enum


class SignalType(Enum):
    """Trading signal types."""
    SHORT = -1
    FLAT = 0
    LONG = 1


@dataclass
class StrategyConfig:
    """Configuration for strategy parameters."""
    # Trend Following Strategy
    ema_fast: int = 20
    ema_slow: int = 50
    ema_long: int = 200
    adx_threshold: int = 25
    atr_period: int = 14
    atr_multiplier: float = 2.0
    
    # Mean Reversion Strategy
    rsi_period: int = 14
    rsi_entry: int = 30
    rsi_exit: int = 55
    bb_period: int = 20
    bb_std_dev: float = 2.0


@dataclass
class RiskConfig:
    """Configuration for risk management."""
    starting_capital: float = 25_000.0
    risk_per_trade: float = 0.01  # 1%
    max_position_size: float = 0.10  # 10%
    max_concurrent_trades: int = 5
    daily_loss_limit: float = 0.02  # 2%
    monthly_drawdown_limit: float = 0.10  # 10%
    transaction_cost: float = 0.001  # 0.1%
    slippage_bps: float = 1.0  # 1 basis point


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""
    #symbols: List[str] = field(default_factory=lambda: ["SPY", "QQQ", "TSLA", "MSFT","MU","NVDA ","AMD","INTC","AAPL","AMZN","GOOGL","META"])
    symbols: List[str] = field(default_factory=lambda: ["DUOL", "PINS", "TWTR", "SNAP","UBER","LYFT","ZM","SHOP","SQ","PYPL"])
    start_date: str = "2004-01-01"
    end_date: str = "2025-12-31"
    data_source: str = "yfinance"  # yfinance, csv, etc.
    initial_capital: float = 2500.0
    use_sentiment_filter: bool = False
    sentiment_threshold: float = -0.2


@dataclass
class ExecutionConfig:
    """Configuration for order execution."""
    # Interactive Brokers
    ib_host: str = "127.0.0.1"
    ib_port: int = 7497  # Paper trading
    ib_client_id: int = 1
    
    # Execution settings
    paper_trading: bool = True
    log_trades: bool = True
    trade_log_path: str = "logs/trades.csv"


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    log_dir: str = "logs/"
    log_file: str = "trading_fund.log"
    console_output: bool = True


@dataclass
class DashboardConfig:
    """Configuration for Streamlit dashboard."""
    port: int = 8501
    host: str = "127.0.0.1"
    refresh_interval: int = 5  # seconds
    theme: str = "dark"


@dataclass
class SystemConfig:
    """Master configuration object."""
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    
    @classmethod
    def from_defaults(cls) -> "SystemConfig":
        """Create config with all defaults."""
        return cls()


# Global config instance (to be initialized in main)
_config: SystemConfig | None = None


def get_config() -> SystemConfig:
    """Get current system configuration."""
    global _config
    if _config is None:
        _config = SystemConfig.from_defaults()
    return _config


def set_config(config: SystemConfig) -> None:
    """Set system configuration."""
    global _config
    _config = config
