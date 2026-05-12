"""Shared utilities for filesystem, prices, and logging."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd


def ensure_directories(paths: list[Path]) -> None:
    """Create directories if they do not already exist."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def configure_logging(log_path: Path) -> None:
    """Configure file and console logging for the application."""
    ensure_directories([log_path.parent])
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
    )


def load_price_matrix(raw_prices_dir: Path, tickers: list[str]) -> pd.DataFrame:
    """Load cached close prices into a wide date-by-ticker matrix."""
    close_series: list[pd.Series] = []
    for ticker in tickers:
        path = raw_prices_dir / f"{ticker}.csv"
        if not path.exists():
            logging.warning("Missing cached prices for %s", ticker)
            continue
        frame = pd.read_csv(path)
        if frame.empty or "Close" not in frame:
            logging.warning("Invalid cached prices for %s", ticker)
            continue
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
        frame["Close"] = pd.to_numeric(frame["Close"], errors="coerce")
        frame = frame.dropna(subset=["Date", "Close"])
        series = frame.set_index("Date")["Close"].rename(ticker).sort_index()
        close_series.append(series)
    if not close_series:
        return pd.DataFrame()
    prices = pd.concat(close_series, axis=1).sort_index()
    prices.index.name = "Date"
    return prices


def pct_cost_from_bps(bps: float) -> float:
    """Convert basis points into a decimal cost."""
    return bps / 10_000.0
