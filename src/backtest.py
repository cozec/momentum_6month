"""Portfolio accounting and end-to-end backtest orchestration."""

from __future__ import annotations

import logging
from dataclasses import asdict

import pandas as pd

from .config import BacktestConfig
from .download_data import download_price_data
from .membership import get_eligible_universe, load_nasdaq100_membership
from .signals import (
    calculate_momentum_scores,
    calculate_monthly_returns,
    get_first_trading_days,
    select_top_n,
)
from .utils import ensure_directories, load_price_matrix, pct_cost_from_bps


def calculate_portfolio_return(
    selected_tickers: list[str],
    prices: pd.DataFrame,
    entry_date: pd.Timestamp,
    exit_date: pd.Timestamp,
) -> pd.DataFrame:
    """Calculate equal-weight stock returns between two rebalance dates."""
    rows: list[dict[str, object]] = []
    for ticker in selected_tickers:
        if ticker not in prices:
            continue
        entry_price = prices.at[entry_date, ticker] if entry_date in prices.index else pd.NA
        exit_price = prices.at[exit_date, ticker] if exit_date in prices.index else pd.NA
        if pd.isna(entry_price) or pd.isna(exit_price) or entry_price <= 0:
            continue
        stock_return = (float(exit_price) / float(entry_price)) - 1.0
        rows.append(
            {
                "ticker": ticker,
                "entry_price": float(entry_price),
                "exit_price": float(exit_price),
                "stock_return": stock_return,
            }
        )
    return pd.DataFrame(rows)


def _benchmark_return(
    prices: pd.DataFrame,
    benchmark: str,
    entry_date: pd.Timestamp,
    exit_date: pd.Timestamp,
) -> float:
    """Return benchmark performance across one holding period."""
    if benchmark not in prices:
        return float("nan")
    entry = prices.at[entry_date, benchmark]
    exit_ = prices.at[exit_date, benchmark]
    if pd.isna(entry) or pd.isna(exit_) or entry <= 0:
        return float("nan")
    return (float(exit_) / float(entry)) - 1.0


def run_backtest(config: BacktestConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the complete monthly momentum backtest and persist result CSVs."""
    ensure_directories([config.raw_prices_dir, config.outputs_dir, config.charts_dir])
    membership = load_nasdaq100_membership(str(config.membership_path))
    all_tickers = sorted(set(membership["ticker"]).union({config.benchmark}))
    download_price_data(all_tickers, config.start_date, config.end_date, config.raw_prices_dir)
    prices = load_price_matrix(config.raw_prices_dir, all_tickers)
    if prices.empty:
        raise RuntimeError("No cached prices are available for the backtest.")

    monthly_returns = calculate_monthly_returns(prices.drop(columns=[config.benchmark], errors="ignore"))
    rebalance_dates = get_first_trading_days(prices[[config.benchmark]].dropna(how="all"))
    rebalance_dates = rebalance_dates[
        (rebalance_dates >= pd.Timestamp(config.start_date))
        & (rebalance_dates <= pd.Timestamp(config.end_date))
    ]

    selection_rows: list[dict[str, object]] = []
    portfolio_rows: list[dict[str, object]] = []
    portfolio_value = config.initial_capital
    qqq_start_price: float | None = None
    prior_holdings: set[str] = set()
    transaction_rate = pct_cost_from_bps(config.transaction_cost_bps)
    slippage_rate = pct_cost_from_bps(config.slippage_bps)

    for entry_date, exit_date in zip(rebalance_dates[:-1], rebalance_dates[1:]):
        eligible = get_eligible_universe(membership, entry_date)
        eligible_with_prices = [ticker for ticker in eligible if ticker in monthly_returns.columns]
        scores = calculate_momentum_scores(
            monthly_returns[eligible_with_prices].copy() if eligible_with_prices else pd.DataFrame(),
            entry_date,
            lookback_months=config.lookback_months,
            score_method=config.score_method,
        )
        selection = select_top_n(scores, config.top_n)
        if selection.empty:
            logging.info("No eligible selection for %s", entry_date.date())
            continue
        trade_returns = calculate_portfolio_return(
            selection["ticker"].tolist(),
            prices,
            entry_date,
            exit_date,
        )
        if trade_returns.empty:
            logging.info("No realized stock returns for %s", entry_date.date())
            continue
        selection = selection.merge(trade_returns, on="ticker", how="inner")
        if selection.empty:
            continue
        selection["weight"] = 1.0 / len(selection)

        current_holdings = set(selection["ticker"])
        buys = current_holdings.difference(prior_holdings)
        sells = prior_holdings.difference(current_holdings)
        turnover = (len(buys) + len(sells)) / max(config.top_n, 1)
        transaction_cost = turnover * transaction_rate
        slippage_cost = turnover * slippage_rate
        gross_return = float((selection["weight"] * selection["stock_return"]).sum())
        net_return = gross_return - transaction_cost - slippage_cost
        qqq_return = _benchmark_return(prices, config.benchmark, entry_date, exit_date)
        excess_return = net_return - qqq_return if pd.notna(qqq_return) else float("nan")
        portfolio_value *= 1.0 + net_return
        if qqq_start_price is None and config.benchmark in prices:
            start_price = prices.at[entry_date, config.benchmark]
            if pd.notna(start_price) and start_price > 0:
                qqq_start_price = float(start_price)
        qqq_value = float("nan")
        if qqq_start_price is not None and config.benchmark in prices:
            exit_price = prices.at[exit_date, config.benchmark]
            if pd.notna(exit_price) and exit_price > 0:
                qqq_value = config.initial_capital * (float(exit_price) / qqq_start_price)

        for row in selection.to_dict(orient="records"):
            selection_rows.append(
                {
                    "rebalance_date": entry_date,
                    "ticker": row["ticker"],
                    "rank": int(row["rank"]),
                    "momentum_score": float(row["momentum_score"]),
                    "weight": float(row["weight"]),
                    "entry_price": float(row["entry_price"]),
                    "exit_date": exit_date,
                    "exit_price": float(row["exit_price"]),
                    "stock_return": float(row["stock_return"]),
                }
            )
        portfolio_rows.append(
            {
                "rebalance_date": entry_date,
                "next_rebalance_date": exit_date,
                "portfolio_return_gross": gross_return,
                "transaction_cost": transaction_cost,
                "slippage_cost": slippage_cost,
                "portfolio_return_net": net_return,
                "qqq_return": qqq_return,
                "excess_return": excess_return,
                "portfolio_value": portfolio_value,
                "qqq_value": qqq_value,
                "turnover": turnover,
            }
        )
        prior_holdings = current_holdings

    selections = pd.DataFrame(selection_rows)
    portfolio_returns = pd.DataFrame(portfolio_rows)
    selections.to_csv(config.outputs_dir / "monthly_selections.csv", index=False)
    portfolio_returns.to_csv(config.outputs_dir / "portfolio_returns.csv", index=False)
    logging.info("Backtest complete with config: %s", asdict(config))
    return selections, portfolio_returns
