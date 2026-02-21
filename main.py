"""
Trading Fund Main Entry Point
Production-structured systematic trading engine (Phase 1 POC)
"""

import logging
import os
import pickle
from datetime import datetime

from config.settings import SystemConfig, set_config, get_config
from data.data_handler import DataLoader
from backtesting.engine import BacktestEngine
from strategies.strategy1_momentum import TrendFollowingStrategy
from strategies.strategy2_mean_reversion import MeanReversionStrategy


# Configure logging
def setup_logging(config: SystemConfig) -> None:
    """Setup logging configuration."""
    log_config = config.logging
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_config.log_dir, exist_ok=True)
    
    log_path = os.path.join(log_config.log_dir, log_config.log_file)
    
    logging.basicConfig(
        level=getattr(logging, log_config.level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler() if log_config.console_output else logging.NullHandler(),
        ]
    )


def run_backtests() -> None:
    """Run backtesting for all strategies."""
    config = get_config()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("STARTING BACKTESTING")
    logger.info("=" * 70)
    
    # Load data
    data_loader = DataLoader(source_type=config.backtest.data_source)
    data_dict = data_loader.fetch_multiple(
        symbols=config.backtest.symbols,
        start_date=config.backtest.start_date,
        end_date=config.backtest.end_date,
    )
    
    if not data_dict:
        logger.error("No data loaded")
        return
    
    # Initialize backtesting engine
    backtest_engine = BacktestEngine(
        backtest_config=config.backtest,
        risk_config=config.risk,
    )
    
    # Test each strategy on each symbol
    results = []
    
    for symbol, data in data_dict.items():
        logger.info(f"\nTesting strategies on {symbol}")
        logger.info("-" * 70)
        
        # Trend Following Strategy
        trend_strategy = TrendFollowingStrategy(symbol=symbol, config=config.strategy)
        result_1 = backtest_engine.run(trend_strategy, data)
        results.append(result_1)
        
        logger.info(f"Trend Following:")
        logger.info(f"  Total Return: {result_1.total_return:.1%}")
        logger.info(f"  CAGR: {result_1.cagr:.1%}")
        logger.info(f"  Sharpe Ratio: {result_1.sharpe_ratio:.2f}")
        logger.info(f"  Max Drawdown: {result_1.max_drawdown:.1%}")
        logger.info(f"  Profit Factor: {result_1.profit_factor:.2f}")
        logger.info(f"  Win Rate: {result_1.win_rate:.1%}")
        logger.info(f"  Trades: {result_1.total_trades}")
        
        # Mean Reversion Strategy
        mr_strategy = MeanReversionStrategy(symbol=symbol, config=config.strategy)
        result_2 = backtest_engine.run(mr_strategy, data)
        results.append(result_2)
        
        logger.info(f"\nMean Reversion:")
        logger.info(f"  Total Return: {result_2.total_return:.1%}")
        logger.info(f"  CAGR: {result_2.cagr:.1%}")
        logger.info(f"  Sharpe Ratio: {result_2.sharpe_ratio:.2f}")
        logger.info(f"  Max Drawdown: {result_2.max_drawdown:.1%}")
        logger.info(f"  Profit Factor: {result_2.profit_factor:.2f}")
        logger.info(f"  Win Rate: {result_2.win_rate:.1%}")
        logger.info(f"  Trades: {result_2.total_trades}")
    
    logger.info("\n" + "=" * 70)
    logger.info("BACKTESTING COMPLETE")
    logger.info("=" * 70)
    
    # Summary statistics
    logger.info("\nSUMMARY")
    logger.info("-" * 70)
    
    avg_sharpe = sum(r.sharpe_ratio for r in results) / len(results)
    avg_return = sum(r.total_return for r in results) / len(results)
    avg_dd = sum(r.max_drawdown for r in results) / len(results)
    
    logger.info(f"Average Sharpe Ratio: {avg_sharpe:.2f}")
    logger.info(f"Average Return: {avg_return:.1%}")
    logger.info(f"Average Max Drawdown: {avg_dd:.1%}")
    
    # Save results to file for dashboard
    results_file = "backtest_results.pkl"
    try:
        with open(results_file, "wb") as f:
            pickle.dump(results, f)
        logger.info(f"\nResults saved to {results_file}")
    except Exception as e:
        logger.warning(f"Failed to save results: {e}")


def main() -> None:
    """Main entry point."""
    # Initialize configuration
    config = SystemConfig.from_defaults()
    set_config(config)
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("Trading Fund V1 - Systematic Trading Engine")
    logger.info(f"Started: {datetime.now()}")
    logger.info("=" * 70)
    
    # Run backtests
    try:
        run_backtests()
    except Exception as e:
        logger.error(f"Error running backtests: {e}", exc_info=True)
        return
    
    logger.info("\n✓ System completed successfully")


if __name__ == "__main__":
    main()

