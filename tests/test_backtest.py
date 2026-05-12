"""Unit tests for portfolio accounting."""

from __future__ import annotations

import pandas as pd

from src.backtest import calculate_portfolio_return


def test_portfolio_return_calculation() -> None:
    """Stock returns should use entry and exit prices for each selected ticker."""
    prices = pd.DataFrame(
        {"AAA": [100.0, 110.0], "BBB": [50.0, 45.0]},
        index=pd.to_datetime(["2026-01-02", "2026-02-02"]),
    )
    result = calculate_portfolio_return(
        ["AAA", "BBB"],
        prices,
        pd.Timestamp("2026-01-02"),
        pd.Timestamp("2026-02-02"),
    )
    observed = dict(zip(result["ticker"], result["stock_return"]))
    assert round(float(observed["AAA"]), 6) == 0.1
    assert round(float(observed["BBB"]), 6) == -0.1
