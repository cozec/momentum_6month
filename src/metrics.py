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


def calculate_comparison_stats(portfolio_returns: pd.DataFrame) -> pd.DataFrame:
    """Compare strategy, QQQ, and TQQQ over the realized backtest window."""
    if portfolio_returns.empty:
        return pd.DataFrame()

    strategy_returns = portfolio_returns["portfolio_return_net"].dropna()
    qqq_returns = portfolio_returns["qqq_return"].dropna()
    tqqq_returns = portfolio_returns["tqqq_return"].dropna()
    periods = min(len(strategy_returns), len(qqq_returns), len(tqqq_returns))
    years = periods / 12.0
    if periods == 0:
        return pd.DataFrame()

    strategy_ending = float(portfolio_returns["portfolio_value"].iloc[-1])
    qqq_ending = float(portfolio_returns["qqq_value"].iloc[-1])
    tqqq_ending = float(portfolio_returns["tqqq_value"].iloc[-1])
    initial_capital = strategy_ending / float((1.0 + strategy_returns).prod())

    def _cagr(ending_value: float) -> float:
        return (ending_value / initial_capital) ** (1.0 / years) - 1.0 if years else float("nan")

    def _volatility(returns: pd.Series) -> float:
        return returns.std(ddof=1) * math.sqrt(12) if len(returns) > 1 else float("nan")

    def _sharpe(returns: pd.Series) -> float:
        deviation = returns.std(ddof=1)
        return returns.mean() / deviation * math.sqrt(12) if len(returns) > 1 and deviation else float("nan")

    metrics = [
        ("Final equity", strategy_ending, qqq_ending, tqqq_ending),
        (
            "Total return",
            strategy_ending / initial_capital - 1.0,
            qqq_ending / initial_capital - 1.0,
            tqqq_ending / initial_capital - 1.0,
        ),
        ("CAGR", _cagr(strategy_ending), _cagr(qqq_ending), _cagr(tqqq_ending)),
        (
            "Annualized volatility",
            _volatility(strategy_returns),
            _volatility(qqq_returns),
            _volatility(tqqq_returns),
        ),
        (
            "Sharpe ratio",
            _sharpe(strategy_returns),
            _sharpe(qqq_returns),
            _sharpe(tqqq_returns),
        ),
        (
            "Max drawdown",
            _max_drawdown(portfolio_returns["portfolio_value"]),
            _max_drawdown(portfolio_returns["qqq_value"]),
            _max_drawdown(portfolio_returns["tqqq_value"]),
        ),
        (
            "Average monthly return",
            float(strategy_returns.mean()),
            float(qqq_returns.mean()),
            float(tqqq_returns.mean()),
        ),
        (
            "Median monthly return",
            float(strategy_returns.median()),
            float(qqq_returns.median()),
            float(tqqq_returns.median()),
        ),
        (
            "Best month",
            float(strategy_returns.max()),
            float(qqq_returns.max()),
            float(tqqq_returns.max()),
        ),
        (
            "Worst month",
            float(strategy_returns.min()),
            float(qqq_returns.min()),
            float(tqqq_returns.min()),
        ),
    ]
    return pd.DataFrame(
        metrics,
        columns=["metric", "strategy", "qqq_buy_hold", "tqqq_buy_hold"],
    )


def format_comparison_markdown(comparison: pd.DataFrame) -> str:
    """Render comparison statistics as a Markdown table."""
    if comparison.empty:
        return ""

    percent_metrics = {
        "Total return",
        "CAGR",
        "Annualized volatility",
        "Max drawdown",
        "Average monthly return",
        "Median monthly return",
        "Best month",
        "Worst month",
    }
    currency_metrics = {"Final equity"}

    lines = [
        "| Metric | Strategy | QQQ Buy & Hold | TQQQ Buy & Hold |",
        "|---|---:|---:|---:|",
    ]
    for row in comparison.itertuples(index=False):
        if row.metric in currency_metrics:
            strategy = f"${row.strategy:,.2f}"
            qqq = f"${row.qqq_buy_hold:,.2f}"
            tqqq = f"${row.tqqq_buy_hold:,.2f}"
        elif row.metric in percent_metrics:
            strategy = f"{row.strategy * 100:,.2f}%"
            qqq = f"{row.qqq_buy_hold * 100:,.2f}%"
            tqqq = f"{row.tqqq_buy_hold * 100:,.2f}%"
        else:
            strategy = f"{row.strategy:,.2f}"
            qqq = f"{row.qqq_buy_hold:,.2f}"
            tqqq = f"{row.tqqq_buy_hold:,.2f}"
        lines.append(f"| {row.metric} | {strategy} | {qqq} | {tqqq} |")
    return "\n".join(lines)


def update_summary_performance_table(summary_path: str, markdown_table: str) -> None:
    """Insert or replace the benchmark comparison table in ``summary.md``."""
    if not markdown_table:
        return
    path = pd.io.common.stringify_path(summary_path)
    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()

    start_marker = "<!-- PERFORMANCE_TABLE_START -->"
    end_marker = "<!-- PERFORMANCE_TABLE_END -->"
    section = (
        "## Strategy vs QQQ and TQQQ Buy & Hold\n\n"
        f"{start_marker}\n"
        f"{markdown_table}\n"
        f"{end_marker}"
    )

    if start_marker in content and end_marker in content:
        prefix, tail = content.split(start_marker, maxsplit=1)
        _, suffix = tail.split(end_marker, maxsplit=1)
        replacement = f"{start_marker}\n{markdown_table}\n{end_marker}"
        content = f"{prefix}{replacement}{suffix}"
    elif "## Trade Detail Rule" in content:
        content = content.replace("## Trade Detail Rule", f"{section}\n\n## Trade Detail Rule")
    else:
        content = f"{content.rstrip()}\n\n{section}\n"

    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
