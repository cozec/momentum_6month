"""Signal generation for monthly momentum rotation."""

from __future__ import annotations

import pandas as pd


def get_first_trading_days(price_df: pd.DataFrame) -> pd.DatetimeIndex:
    """Return the first available trading day in each calendar month."""
    if price_df.empty:
        return pd.DatetimeIndex([])
    valid_dates = price_df.dropna(how="all").index.to_series()
    first_days = valid_dates.groupby(valid_dates.dt.to_period("M")).min()
    return pd.DatetimeIndex(first_days.tolist())


def get_next_month_start_after_last_price(price_df: pd.DataFrame) -> pd.Timestamp:
    """Return the next month-start signal date after the latest cached price."""
    if price_df.empty:
        raise ValueError("Cannot infer the next rebalance date from empty prices.")
    latest_date = price_df.dropna(how="all").index.max()
    if pd.isna(latest_date):
        raise ValueError("Cannot infer the next rebalance date without valid prices.")
    return (pd.Timestamp(latest_date).to_period("M") + 1).to_timestamp()


def calculate_monthly_returns(price_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate month-end returns from daily adjusted close prices."""
    month_end_prices = price_df.sort_index().resample("ME").last()
    return month_end_prices.pct_change()


def calculate_momentum_scores(
    monthly_returns: pd.DataFrame,
    rebalance_date: pd.Timestamp,
    lookback_months: int = 6,
    score_method: str = "average_monthly_return",
) -> pd.Series:
    """Compute momentum scores from prior completed monthly returns only."""
    completed_month_end = rebalance_date.to_period("M").to_timestamp("M") - pd.offsets.MonthEnd(1)
    history = monthly_returns.loc[:completed_month_end].tail(lookback_months)
    if len(history) < lookback_months:
        return pd.Series(dtype=float)
    valid = history.dropna(axis=1, how="any")
    if valid.empty:
        return pd.Series(dtype=float)
    if score_method == "compound_6m_return":
        return (1.0 + valid).prod() - 1.0
    if score_method != "average_monthly_return":
        raise ValueError(f"Unsupported score method: {score_method}")
    return valid.mean()


def filter_tickers_with_min_history(
    monthly_returns: pd.DataFrame,
    tickers: list[str],
    rebalance_date: pd.Timestamp,
    min_months: int,
) -> list[str]:
    """Keep tickers with enough completed, non-null monthly returns."""
    if monthly_returns.empty or min_months <= 0:
        return [ticker for ticker in tickers if ticker in monthly_returns.columns]
    completed_month_end = rebalance_date.to_period("M").to_timestamp("M") - pd.offsets.MonthEnd(1)
    history = monthly_returns.loc[:completed_month_end]
    valid_tickers: list[str] = []
    for ticker in tickers:
        if ticker not in history.columns:
            continue
        if int(history[ticker].dropna().shape[0]) >= min_months:
            valid_tickers.append(ticker)
    return valid_tickers


def select_top_n(momentum_scores: pd.Series, n: int = 3) -> pd.DataFrame:
    """Rank and return the top-scoring tickers."""
    ranked = momentum_scores.dropna().sort_values(ascending=False).head(n)
    selection = ranked.rename("momentum_score").reset_index()
    selection.columns = ["ticker", "momentum_score"]
    selection["rank"] = range(1, len(selection) + 1)
    selection["weight"] = 1.0 / len(selection) if len(selection) else 0.0
    return selection
