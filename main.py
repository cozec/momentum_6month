"""CLI entry point for the Nasdaq-100 momentum backtest."""

from __future__ import annotations

import argparse

from src.backtest import run_backtest
from src.config import BacktestConfig
from src.metrics import (
    calculate_comparison_stats,
    calculate_summary_stats,
    format_comparison_markdown,
    update_summary_performance_table,
)
from src.plots import generate_all_charts, generate_last_year_pick_views
from src.utils import configure_logging, ensure_directories


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the Nasdaq-100 momentum backtest.")
    parser.add_argument("--start-date", default="2016-01-01")
    parser.add_argument("--end-date", default="2026-05-12")
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--lookback-months", type=int, default=6)
    parser.add_argument("--benchmark", default="QQQ")
    parser.add_argument("--secondary-benchmark", default="TQQQ")
    parser.add_argument(
        "--score-method",
        choices=["average_monthly_return", "compound_6m_return"],
        default="average_monthly_return",
    )
    return parser.parse_args()


def main() -> None:
    """Run the backtest, summary statistics, and chart generation."""
    args = parse_args()
    config = BacktestConfig(
        start_date=args.start_date,
        end_date=args.end_date,
        top_n=args.top_n,
        lookback_months=args.lookback_months,
        benchmark=args.benchmark.upper(),
        secondary_benchmark=args.secondary_benchmark.upper(),
        score_method=args.score_method,
    )
    ensure_directories([config.outputs_dir, config.charts_dir, config.logs_dir])
    configure_logging(config.logs_dir / "backtest.log")
    selections, portfolio_returns = run_backtest(config)
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
    )


if __name__ == "__main__":
    main()
