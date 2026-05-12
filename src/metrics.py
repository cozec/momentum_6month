"""Performance summary statistics."""

from __future__ import annotations

import math

import pandas as pd


def _max_drawdown(values: pd.Series) -> float:
    """Return the minimum peak-to-trough drawdown."""
    if values.empty:
        return float("nan")
    drawdowns = values / values.cummax() - 1.0
    return float(drawdowns.min())


def calculate_summary_stats(portfolio_returns: pd.DataFrame) -> pd.DataFrame:
    """Calculate headline strategy statistics."""
    if portfolio_returns.empty:
        return pd.DataFrame()
    monthly = portfolio_returns["portfolio_return_net"].dropna()
    qqq = portfolio_returns["qqq_return"].dropna()
    periods = len(monthly)
    ending_value = float(portfolio_returns["portfolio_value"].iloc[-1])
    starting_value = ending_value / float((1.0 + monthly).prod())
    years = periods / 12.0
    total_return = ending_value / starting_value - 1.0
    cagr = (ending_value / starting_value) ** (1.0 / years) - 1.0 if years else float("nan")
    volatility = monthly.std(ddof=1) * math.sqrt(12) if periods > 1 else float("nan")
    sharpe = monthly.mean() / monthly.std(ddof=1) * math.sqrt(12) if periods > 1 and monthly.std(ddof=1) else float("nan")
    benchmark_aligned = portfolio_returns.dropna(subset=["portfolio_return_net", "qqq_return"])
    win_rate = float(
        (benchmark_aligned["portfolio_return_net"] > benchmark_aligned["qqq_return"]).mean()
    )
    stats = {
        "CAGR": cagr,
        "annualized_volatility": volatility,
        "Sharpe_ratio": sharpe,
        "max_drawdown": _max_drawdown(portfolio_returns["portfolio_value"]),
        "win_rate_vs_QQQ": win_rate,
        "average_monthly_return": float(monthly.mean()),
        "median_monthly_return": float(monthly.median()),
        "best_month": float(monthly.max()),
        "worst_month": float(monthly.min()),
        "total_return": total_return,
        "number_of_rebalances": int(periods),
        "average_turnover": float(portfolio_returns["turnover"].mean()),
    }
    return pd.DataFrame({"metric": list(stats.keys()), "value": list(stats.values())})
