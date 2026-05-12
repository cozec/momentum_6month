"""Price download and CSV caching."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import yfinance as yf


def _normalize_price_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a clean OHLCV frame with the required CSV schema."""
    if frame.empty:
        return frame
    if isinstance(frame.columns, pd.MultiIndex):
        frame = frame.copy()
        frame.columns = frame.columns.get_level_values(0)
    normalized = frame.reset_index().rename(columns={"index": "Date"})
    if "Date" not in normalized:
        normalized = normalized.rename(columns={normalized.columns[0]: "Date"})
    keep = ["Date", "Open", "High", "Low", "Close", "Volume"]
    normalized = normalized[[column for column in keep if column in normalized.columns]]
    normalized["Date"] = pd.to_datetime(normalized["Date"]).dt.tz_localize(None)
    return normalized


def download_price_data(
    tickers: list[str],
    start_date: str,
    end_date: str,
    raw_prices_dir: Path,
) -> dict[str, Path]:
    """Download adjusted OHLCV prices with per-ticker CSV caching."""
    raw_prices_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = raw_prices_dir.parent / "yfinance_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    if hasattr(yf, "set_tz_cache_location"):
        yf.set_tz_cache_location(str(cache_dir))
    cached_paths: dict[str, Path] = {}
    for ticker in sorted(set(tickers)):
        output_path = raw_prices_dir / f"{ticker}.csv"
        if output_path.exists():
            cached_paths[ticker] = output_path
            continue
        try:
            frame = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            frame = _normalize_price_frame(frame)
            if frame.empty:
                logging.warning("No prices downloaded for %s", ticker)
                continue
            frame.to_csv(output_path, index=False)
            cached_paths[ticker] = output_path
        except Exception as exc:  # noqa: BLE001
            logging.warning("Failed to download %s: %s", ticker, exc)
    return cached_paths
