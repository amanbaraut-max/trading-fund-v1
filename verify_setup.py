#!/usr/bin/env python3
"""
Verification script to validate that all modules import correctly
and the system is ready to run backtests.
"""

import sys

def verify_imports():
    """Verify all core modules can be imported"""
    print("=" * 70)
    print("VERIFYING TRADING FUND SYSTEM SETUP")
    print("=" * 70)
    print()
    
    modules_to_test = [
        ("config.settings", ["get_config", "SystemConfig"]),
        ("data.data_handler", ["DataLoader"]),
        ("strategies.base_strategy", ["BaseStrategy", "SignalOutput"]),
        ("strategies.strategy1_momentum", ["TrendFollowingStrategy"]),
        ("strategies.strategy2_mean_reversion", ["MeanReversionStrategy"]),
        ("risk.position_sizing", ["PositionSizer"]),
        ("risk.portfolio", ["PortfolioRiskManager", "Position"]),
        ("backtesting.engine", ["BacktestEngine", "BacktestResult"]),
        ("ai.sentiment_overlay", ["SentimentOverlay"]),
        ("execution.execution_engine", ["ExecutionEngine", "IBKRClient"]),
    ]
    
    failed = []
    for module_name, classes in modules_to_test:
        try:
            module = __import__(module_name, fromlist=classes)
            for cls in classes:
                if not hasattr(module, cls):
                    failed.append(f"{module_name}.{cls}")
                    print(f"  ✗ {module_name}.{cls} (NOT FOUND)")
                else:
                    print(f"  ✓ {module_name}.{cls}")
        except Exception as e:
            failed.append(module_name)
            print(f"  ✗ {module_name} (ERROR: {str(e)[:60]})")
    
    print()
    print("=" * 70)
    
    if failed:
        print(f"FAILED: {len(failed)} imports failed")
        for item in failed:
            print(f"  - {item}")
        return False
    else:
        print("SUCCESS: All imports verified ✓")
        return True


def verify_config():
    """Verify configuration loads correctly"""
    print()
    print("=" * 70)
    print("VERIFYING CONFIGURATION")
    print("=" * 70)
    print()
    
    try:
        from config.settings import get_config
        
        config = get_config()
        
        print(f"  ✓ Configuration loaded")
        print(f"    - Starting capital: ${config.risk.starting_capital:,.0f}")
        print(f"    - Risk per trade: {config.risk.risk_per_trade:.1%}")
        print(f"    - Max position: {config.risk.max_position_size:.1%}")
        print(f"    - Symbols: {', '.join(config.backtest.symbols)}")
        print(f"    - Backtest period: {config.backtest.start_date} to {config.backtest.end_date}")
        print(f"    - Strategy params:")
        print(f"      - EMA periods: {config.strategy.ema_fast}/{config.strategy.ema_slow}/{config.strategy.ema_long}")
        print(f"      - ADX threshold: {config.strategy.adx_threshold}")
        print(f"      - RSI entry: {config.strategy.rsi_entry}")
        
        print()
        print("SUCCESS: Configuration verified ✓")
        return True
        
    except Exception as e:
        print(f"FAILED: {str(e)}")
        return False


def verify_data_loading():
    """Verify data can be loaded (small test)"""
    print()
    print("=" * 70)
    print("VERIFYING DATA LOADING (downloading 1 day test data)")
    print("=" * 70)
    print()
    
    try:
        from data.data_handler import DataLoader
        
        loader = DataLoader()
        data = loader.fetch("SPY", "2023-12-29", "2024-01-02")
        
        if data is not None and len(data) > 0:
            print(f"  ✓ Downloaded {len(data)} rows of data")
            print(f"    - Columns: {', '.join(data.columns.tolist())}")
            print(f"    - Date range: {data.index[0].date()} to {data.index[-1].date()}")
            print()
            print("SUCCESS: Data loading verified ✓")
            return True
        else:
            print("FAILED: No data returned")
            return False
            
    except Exception as e:
        print(f"FAILED: {str(e)}")
        return False


def main():
    """Run all verifications"""
    
    results = []
    
    # Test imports
    results.append(("Module Imports", verify_imports()))
    
    # Test config
    results.append(("Configuration", verify_config()))
    
    # Test data loading
    results.append(("Data Loading", verify_data_loading()))
    
    # Summary
    print()
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print()
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print()
    print("=" * 70)
    
    if all_passed:
        print("ALL VERIFICATIONS PASSED ✓")
        print()
        print("Your trading fund system is ready to use!")
        print()
        print("Next steps:")
        print("  1. Configure parameters in config/settings.py")
        print("  2. Run backtests: python main.py")
        print("  3. View dashboard: streamlit run dashboard/app.py")
        print()
        return 0
    else:
        print("SOME VERIFICATIONS FAILED ✗")
        print()
        print("Please fix the issues above and try again.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
