"""Configuration objects for the Nasdaq-100 momentum backtest."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class BacktestConfig:
    """Runtime configuration for the backtest pipeline."""

    project_root: Path = Path(__file__).resolve().parents[1]
    start_date: str = "2016-01-01"
    end_date: str = "2026-05-12"
    benchmark: str = "QQQ"
    secondary_benchmark: str = "TQQQ"
    top_n: int = 3
    lookback_months: int = 6
    initial_capital: float = 100_000.0
    transaction_cost_bps: float = 0.0
    slippage_bps: float = 0.0
    min_price_history_months: int = 6
    score_method: str = "average_monthly_return"
    rebalance_frequency: str = "monthly"
    use_historical_membership: bool = False

    @property
    def data_dir(self) -> Path:
        """Return the top-level data directory."""
        return self.project_root / "data"

    @property
    def raw_prices_dir(self) -> Path:
        """Return the directory that stores cached raw price CSV files."""
        return self.data_dir / "raw_prices"

    @property
    def outputs_dir(self) -> Path:
        """Return the directory that stores generated results."""
        return self.project_root / "outputs"

    @property
    def charts_dir(self) -> Path:
        """Return the directory that stores generated charts."""
        return self.outputs_dir / "charts"

    @property
    def membership_path(self) -> Path:
        """Return the CSV path for Nasdaq-100 membership metadata."""
        return self.data_dir / "nasdaq100_membership.csv"

    @property
    def logs_dir(self) -> Path:
        """Return the log directory."""
        return self.project_root / "logs"
