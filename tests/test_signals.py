"""Unit tests for signal generation."""

from __future__ import annotations

import pandas as pd

from src.signals import (
    calculate_momentum_scores,
    calculate_monthly_returns,
    filter_tickers_with_min_history,
    get_first_trading_days,
    select_top_n,
)


def test_monthly_returns_uses_month_end_prices() -> None:
    """Monthly returns should use the final available price in each month."""
    prices = pd.DataFrame(
        {"AAA": [100.0, 110.0, 121.0]},
        index=pd.to_datetime(["2026-01-02", "2026-01-30", "2026-02-27"]),
    )
    monthly = calculate_monthly_returns(prices)
    assert round(float(monthly.loc["2026-02-28", "AAA"]), 6) == 0.1


def test_momentum_score_excludes_current_partial_month() -> None:
    """Scores should only use returns from completed months."""
    index = pd.date_range("2025-11-30", periods=7, freq="ME")
    monthly = pd.DataFrame({"AAA": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 9.0]}, index=index)
    scores = calculate_momentum_scores(monthly, pd.Timestamp("2026-05-01"))
    assert round(float(scores["AAA"]), 6) == 0.035


def test_select_top_three() -> None:
    """Selection should rank the largest scores first."""
    scores = pd.Series({"AAA": 0.1, "BBB": 0.3, "CCC": 0.2, "DDD": 0.05})
    selected = select_top_n(scores, 3)
    assert selected["ticker"].tolist() == ["BBB", "CCC", "AAA"]
    assert selected["rank"].tolist() == [1, 2, 3]


def test_first_trading_days() -> None:
    """The first observed date in each month should define rebalance dates."""
    prices = pd.DataFrame(
        {"AAA": [1.0, 2.0, 3.0, 4.0]},
        index=pd.to_datetime(["2026-01-02", "2026-01-05", "2026-02-02", "2026-02-03"]),
    )
    first_days = get_first_trading_days(prices)
    assert first_days.tolist() == [pd.Timestamp("2026-01-02"), pd.Timestamp("2026-02-02")]


def test_minimum_history_filter_uses_completed_months_only() -> None:
    """Eligibility should honor the configured minimum completed-month count."""
    monthly = pd.DataFrame(
        {
            "AAA": [0.01, 0.02, 0.03, 0.04, 0.05, 0.06],
            "BBB": [0.01, 0.02, None, 0.04, 0.05, 0.06],
        },
        index=pd.date_range("2025-11-30", periods=6, freq="ME"),
    )
    tickers = filter_tickers_with_min_history(
        monthly,
        ["AAA", "BBB"],
        pd.Timestamp("2026-06-01"),
        min_months=6,
    )
    assert tickers == ["AAA"]
