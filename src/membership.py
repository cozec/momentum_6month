"""Nasdaq-100 membership loading and eligibility logic."""

from __future__ import annotations

import pandas as pd


def load_nasdaq100_membership(filepath: str) -> pd.DataFrame:
    """Load the membership CSV and normalize date columns."""
    membership = pd.read_csv(filepath)
    required = {"ticker", "start_date", "end_date"}
    missing = required.difference(membership.columns)
    if missing:
        raise ValueError(f"Membership file is missing columns: {sorted(missing)}")
    membership = membership.copy()
    membership["ticker"] = membership["ticker"].astype(str).str.upper()
    membership["start_date"] = pd.to_datetime(membership["start_date"], errors="coerce")
    membership["end_date"] = pd.to_datetime(membership["end_date"], errors="coerce")
    return membership


def get_eligible_universe(membership_df: pd.DataFrame, date: pd.Timestamp) -> list[str]:
    """Return tickers considered members on a given date."""
    active = membership_df[
        (membership_df["start_date"].isna() | (membership_df["start_date"] <= date))
        & (membership_df["end_date"].isna() | (membership_df["end_date"] >= date))
    ]
    return sorted(active["ticker"].dropna().unique().tolist())
