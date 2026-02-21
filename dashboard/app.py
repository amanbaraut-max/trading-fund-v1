"""
Streamlit Dashboard - real-time portfolio and strategy monitoring
"""

import logging
import sys
import os
from typing import List, Optional

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backtesting.engine import BacktestResult

logger = logging.getLogger(__name__)


class TradingDashboard:
    """Streamlit dashboard for trading system monitoring."""
    
    def __init__(self):
        """Initialize dashboard."""
        st.set_page_config(
            page_title="Trading Fund V1",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        
        self.results: List[BacktestResult] = []
    
    def add_result(self, result: BacktestResult) -> None:
        """Add backtest result to display."""
        self.results.append(result)
    
    def render(self) -> None:
        """Render dashboard."""
        st.title("📈 Trading Fund V1")
        st.markdown("Systematic Hybrid Trading Engine - Phase 1 POC")
        
        if not self.results:
            st.warning("No backtest results to display")
            return
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Overview", "Equity Curves", "Trade Analysis", "Metrics"]
        )
        
        with tab1:
            self._render_overview()
        
        with tab2:
            self._render_equity_curves()
        
        with tab3:
            self._render_trade_analysis()
        
        with tab4:
            self._render_metrics()
    
    def _render_overview(self) -> None:
        """Render overview tab."""
        st.header("Performance Overview")
        
        # Summary cards
        cols = st.columns(4)
        
        if self.results:
            avg_return = sum(r.total_return for r in self.results) / len(self.results)
            avg_sharpe = sum(r.sharpe_ratio for r in self.results) / len(self.results)
            avg_dd = sum(r.max_drawdown for r in self.results) / len(self.results)
            total_trades = sum(r.total_trades for r in self.results)
            
            with cols[0]:
                st.metric("Avg Return", f"{avg_return:.1%}")
            
            with cols[1]:
                st.metric("Avg Sharpe", f"{avg_sharpe:.2f}")
            
            with cols[2]:
                st.metric("Avg Max DD", f"{avg_dd:.1%}")
            
            with cols[3]:
                st.metric("Total Trades", f"{total_trades}")
        
        # Results table
        st.subheader("Strategy Results")
        
        results_data = []
        for result in self.results:
            results_data.append({
                "Strategy": result.strategy_name,
                "Symbol": result.symbol,
                "Return": f"{result.total_return:.1%}",
                "CAGR": f"{result.cagr:.1%}",
                "Sharpe": f"{result.sharpe_ratio:.2f}",
                "Max DD": f"{result.max_drawdown:.1%}",
                "Profit Factor": f"{result.profit_factor:.2f}",
                "Win Rate": f"{result.win_rate:.1%}",
                "Trades": result.total_trades,
            })
        
        df_results = pd.DataFrame(results_data)
        st.dataframe(df_results, use_container_width=True)
    
    def _render_equity_curves(self) -> None:
        """Render equity curves tab."""
        st.header("Equity Curves")
        
        if not self.results:
            st.warning("No results to display")
            return
        
        # Plot equity curves
        fig = go.Figure()
        
        for result in self.results:
            label = f"{result.strategy_name} ({result.symbol})"
            fig.add_trace(
                go.Scatter(
                    x=result.equity_curve.index,
                    y=result.equity_curve.values,
                    mode="lines",
                    name=label,
                    hovertemplate="%{x|%Y-%m-%d}<br>$%{y:,.0f}<extra></extra>",
                )
            )
        
        fig.update_layout(
            title="Portfolio Equity Curves",
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            hovermode="x unified",
            height=500,
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Drawdown chart
        st.subheader("Drawdown Analysis")
        
        fig2 = go.Figure()
        
        for result in self.results:
            equity = result.equity_curve
            cummax = equity.cummax()
            drawdown = ((equity - cummax) / cummax * 100)
            
            label = f"{result.strategy_name} ({result.symbol})"
            fig2.add_trace(
                go.Scatter(
                    x=equity.index,
                    y=drawdown.values,
                    fill="tozeroy",
                    name=label,
                    mode="lines",
                    hovertemplate="%{x|%Y-%m-%d}<br>%{y:.1f}%<extra></extra>",
                )
            )
        
        fig2.update_layout(
            title="Portfolio Drawdown",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode="x unified",
            height=400,
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    def _render_trade_analysis(self) -> None:
        """Render trade analysis tab."""
        st.header("Trade Analysis")
        
        if not self.results:
            st.warning("No results to display")
            return
        
        # Select strategy
        strategy_options = [f"{r.strategy_name} ({r.symbol})" for r in self.results]
        selected = st.selectbox("Select Strategy", strategy_options)
        
        # Find matching result
        result = None
        for r in self.results:
            if f"{r.strategy_name} ({r.symbol})" == selected:
                result = r
                break
        
        if not result:
            return
        
        # Trades table
        st.subheader("Trade List")
        
        trades_data = []
        for trade in result.trades:
            trades_data.append({
                "Entry Date": trade.entry_date.strftime("%Y-%m-%d"),
                "Entry Price": f"${trade.entry_price:.2f}",
                "Exit Date": trade.exit_date.strftime("%Y-%m-%d") if trade.exit_date else "Open",
                "Exit Price": f"${trade.exit_price:.2f}" if trade.exit_price else "-",
                "Shares": trade.shares,
                "P&L": f"${trade.pnl:.2f}",
                "P&L %": f"{trade.pnl_pct:.1%}",
            })
        
        df_trades = pd.DataFrame(trades_data)
        st.dataframe(df_trades, use_container_width=True)
        
        # Win/Loss distribution
        if result.trades:
            cols = st.columns(3)
            
            with cols[0]:
                st.metric("Winning Trades", result.winning_trades)
            
            with cols[1]:
                st.metric("Losing Trades", result.losing_trades)
            
            with cols[2]:
                st.metric("Win Rate", f"{result.win_rate:.1%}")
    
    def _render_metrics(self) -> None:
        """Render detailed metrics tab."""
        st.header("Performance Metrics")
        
        if not self.results:
            st.warning("No results to display")
            return
        
        # Create comparison table
        metrics_data = []
        
        for result in self.results:
            metrics_data.append({
                "Strategy": f"{result.strategy_name}",
                "Symbol": result.symbol,
                "Starting Capital": f"${result.starting_capital:,.0f}",
                "Final Value": f"${result.final_value:,.0f}",
                "Total Return": f"{result.total_return:.1%}",
                "CAGR": f"{result.cagr:.1%}",
                "Sharpe Ratio": f"{result.sharpe_ratio:.2f}",
                "Max Drawdown": f"{result.max_drawdown:.1%}",
                "Profit Factor": f"{result.profit_factor:.2f}",
                "Win Rate": f"{result.win_rate:.1%}",
                "Avg Win": f"${result.avg_win:.2f}",
                "Avg Loss": f"${result.avg_loss:.2f}",
                "Consecutive Wins": result.consecutive_wins,
                "Total Trades": result.total_trades,
            })
        
        df_metrics = pd.DataFrame(metrics_data)
        st.dataframe(df_metrics, use_container_width=True)


def run_dashboard(results: List[BacktestResult]) -> None:
    """Run Streamlit dashboard with results."""
    dashboard = TradingDashboard()
    
    for result in results:
        dashboard.add_result(result)
    
    dashboard.render()


def load_results() -> List[BacktestResult]:
    """Load backtest results from pickle file."""
    results_file = "backtest_results.pkl"
    
    try:
        if os.path.exists(results_file):
            with open(results_file, "rb") as f:
                return pickle.load(f)
    except Exception as e:
        st.error(f"Failed to load results: {e}")
    
    return []


if __name__ == "__main__":
    import pickle
    
    # Load results and display
    results = load_results()
    
    if results:
        run_dashboard(results)
    else:
        st.error("No backtest results found. Run 'python main.py' first to generate results.")
