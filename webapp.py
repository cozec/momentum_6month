"""Local dashboard server for the Nasdaq-100 momentum project."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, send_from_directory

from src.backtest import (
    generate_next_rebalance_picks,
    generate_open_rebalance_picks,
    run_backtest,
)
from src.config import BacktestConfig
from src.metrics import (
    calculate_comparison_stats,
    calculate_summary_stats,
    format_comparison_markdown,
    update_summary_performance_table,
)
from src.plots import generate_all_charts, generate_last_year_pick_views
from src.utils import configure_logging, ensure_directories


PROJECT_ROOT = Path(__file__).resolve().parent
app = Flask(__name__)


def _records(path: Path) -> list[dict[str, object]]:
    """Read a CSV into JSON-ready records."""
    if not path.exists():
        return []
    frame = pd.read_csv(path)
    return frame.fillna("").to_dict(orient="records")


def _dashboard_payload(config: BacktestConfig) -> dict[str, object]:
    """Build the JSON document consumed by the frontend."""
    outputs = config.outputs_dir
    return {
        "generated_at": date.today().isoformat(),
        "config": {
            "start_date": config.start_date,
            "end_date": config.end_date,
            "top_n": config.top_n,
            "lookback_months": config.lookback_months,
            "benchmark": config.benchmark,
            "secondary_benchmark": config.secondary_benchmark,
        },
        "open_picks": _records(outputs / "open_rebalance_picks.csv"),
        "next_picks": _records(outputs / "next_rebalance_picks.csv"),
        "last_year": _records(outputs / "last_12_month_picks.csv"),
        "comparison": _records(outputs / "comparison_stats.csv"),
        "summary": _records(outputs / "summary_stats.csv"),
    }


def refresh_outputs() -> dict[str, object]:
    """Refresh market data to today and regenerate dashboard artifacts."""
    config = BacktestConfig(end_date=date.today().isoformat())
    ensure_directories([config.outputs_dir, config.charts_dir, config.logs_dir])
    configure_logging(config.logs_dir / "dashboard.log")

    selections, portfolio_returns = run_backtest(config, force_refresh_prices=True)
    open_picks = generate_open_rebalance_picks(config)
    next_picks = generate_next_rebalance_picks(config)

    summary = calculate_summary_stats(portfolio_returns)
    summary.to_csv(config.outputs_dir / "summary_stats.csv", index=False)
    comparison = calculate_comparison_stats(portfolio_returns)
    comparison.to_csv(config.outputs_dir / "comparison_stats.csv", index=False)
    update_summary_performance_table(
        str(config.project_root / "summary.md"),
        format_comparison_markdown(comparison),
    )
    generate_all_charts(portfolio_returns, selections, config.charts_dir)
    generate_last_year_pick_views(
        portfolio_returns,
        selections,
        config.outputs_dir,
        config.charts_dir,
        open_picks=open_picks,
    )
    next_picks.to_csv(config.outputs_dir / "next_rebalance_picks.csv", index=False)
    return _dashboard_payload(config)


@app.get("/")
def index() -> str:
    """Render the dashboard shell."""
    return render_template("dashboard.html")


@app.post("/api/refresh")
def refresh_dashboard() -> object:
    """Refresh all outputs and return updated dashboard data."""
    return jsonify(refresh_outputs())


@app.get("/api/dashboard")
def dashboard_snapshot() -> object:
    """Return the latest cached dashboard payload without forcing a refresh."""
    config = BacktestConfig(end_date=date.today().isoformat())
    return jsonify(_dashboard_payload(config))


@app.get("/outputs/<path:filename>")
def outputs_file(filename: str) -> object:
    """Serve generated charts and CSV artifacts."""
    return send_from_directory(PROJECT_ROOT / "outputs", filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
