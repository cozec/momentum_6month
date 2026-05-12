"""Chart generation for backtest outputs."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
import pandas as pd


def _save(fig: plt.Figure, path: Path) -> None:
    """Persist a chart and release the matplotlib figure."""
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_equity_curve(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    output_path: Path,
) -> None:
    """Plot cumulative strategy and benchmark equity curves."""
    strategy_curve = (1.0 + strategy_returns.fillna(0.0)).cumprod()
    benchmark_curve = (1.0 + benchmark_returns.fillna(0.0)).cumprod()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(strategy_curve.index, strategy_curve.values, label="Strategy")
    ax.plot(benchmark_curve.index, benchmark_curve.values, label="QQQ")
    ax.set_title("Equity Curve")
    ax.legend()
    ax.grid(alpha=0.25)
    _save(fig, output_path)


def plot_drawdowns(portfolio_values: pd.Series, output_path: Path) -> None:
    """Plot portfolio drawdowns."""
    drawdowns = portfolio_values / portfolio_values.cummax() - 1.0
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(drawdowns.index, drawdowns.values, 0.0, alpha=0.35)
    ax.set_title("Drawdown Curve")
    ax.grid(alpha=0.25)
    _save(fig, output_path)


def generate_all_charts(
    portfolio_returns: pd.DataFrame,
    monthly_selections: pd.DataFrame,
    charts_dir: Path,
) -> None:
    """Generate every chart requested by the project specification."""
    if portfolio_returns.empty:
        return
    charts_dir.mkdir(parents=True, exist_ok=True)
    chart_data = portfolio_returns.copy()
    chart_data["rebalance_date"] = pd.to_datetime(chart_data["rebalance_date"])
    chart_data = chart_data.set_index("rebalance_date")

    plot_equity_curve(
        chart_data["portfolio_return_net"],
        chart_data["qqq_return"],
        charts_dir / "equity_curve.png",
    )
    plot_drawdowns(chart_data["portfolio_value"], charts_dir / "drawdown_curve.png")

    fig, ax = plt.subplots(figsize=(9, 4))
    chart_data["portfolio_return_net"].hist(ax=ax, bins=20)
    ax.set_title("Monthly Return Distribution")
    _save(fig, charts_dir / "monthly_return_distribution.png")

    for window in (6, 12):
        rolling = (1.0 + chart_data["portfolio_return_net"]).rolling(window).apply(
            lambda series: series.prod() - 1.0,
            raw=False,
        )
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(rolling.index, rolling.values)
        ax.set_title(f"Rolling {window}-Month Return")
        ax.grid(alpha=0.25)
        _save(fig, charts_dir / f"rolling_{window}m_return.png")

    if not monthly_selections.empty:
        counts = monthly_selections["ticker"].value_counts().head(20).sort_values()
        fig, ax = plt.subplots(figsize=(9, 6))
        counts.plot.barh(ax=ax)
        ax.set_title("Top Selected Stocks Frequency")
        _save(fig, charts_dir / "top_selected_frequency.png")

    fig, ax = plt.subplots(figsize=(10, 4))
    chart_data["excess_return"].plot(kind="bar", ax=ax)
    ax.set_title("Monthly Excess Return vs QQQ")
    ax.set_xticks([])
    _save(fig, charts_dir / "monthly_excess_return.png")


def generate_last_year_pick_views(
    portfolio_returns: pd.DataFrame,
    monthly_selections: pd.DataFrame,
    outputs_dir: Path,
    charts_dir: Path,
    months: int = 12,
) -> pd.DataFrame:
    """Create a compact last-year picks table and two supporting charts."""
    if portfolio_returns.empty or monthly_selections.empty:
        return pd.DataFrame()

    returns = portfolio_returns.copy()
    returns["rebalance_date"] = pd.to_datetime(returns["rebalance_date"])
    recent_dates = returns["rebalance_date"].sort_values().tail(months)

    selections = monthly_selections.copy()
    selections["rebalance_date"] = pd.to_datetime(selections["rebalance_date"])
    recent_selections = selections[selections["rebalance_date"].isin(recent_dates)].copy()
    recent_returns = returns[returns["rebalance_date"].isin(recent_dates)].copy()
    if recent_selections.empty:
        return pd.DataFrame()

    picks = (
        recent_selections.pivot(
            index="rebalance_date",
            columns="rank",
            values="ticker",
        )
        .rename(columns={1: "pick_1", 2: "pick_2", 3: "pick_3"})
        .reset_index()
    )
    score_means = (
        recent_selections.groupby("rebalance_date", as_index=False)["momentum_score"]
        .mean()
        .rename(columns={"momentum_score": "avg_momentum_score"})
    )
    table = picks.merge(score_means, on="rebalance_date", how="left").merge(
        recent_returns[
            ["rebalance_date", "portfolio_return_net", "qqq_return", "excess_return"]
        ],
        on="rebalance_date",
        how="left",
    )
    table = table.sort_values("rebalance_date")
    table.to_csv(outputs_dir / "last_12_month_picks.csv", index=False)

    timeline = recent_selections.copy().sort_values(["rebalance_date", "rank"])
    ordered_months = sorted(timeline["rebalance_date"].drop_duplicates().tolist())
    ordered_tickers = timeline["ticker"].drop_duplicates().tolist()
    cmap = plt.get_cmap("tab20")
    ticker_colors = {
        ticker: cmap(index % cmap.N)
        for index, ticker in enumerate(ordered_tickers)
    }

    fig, ax = plt.subplots(figsize=(13, 4.8))
    month_lookup = {month: position for position, month in enumerate(ordered_months)}
    for row in timeline.itertuples(index=False):
        x_pos = month_lookup[row.rebalance_date]
        y_pos = 3 - int(row.rank)
        rect = Rectangle(
            (x_pos, y_pos),
            1.0,
            1.0,
            facecolor=ticker_colors[row.ticker],
            edgecolor="white",
            linewidth=1.2,
        )
        ax.add_patch(rect)
        ax.text(
            x_pos + 0.5,
            y_pos + 0.5,
            row.ticker,
            ha="center",
            va="center",
            fontsize=9,
            color="black",
        )
    ax.set_xlim(0, len(ordered_months))
    ax.set_ylim(0, 3)
    ax.set_xticks([index + 0.5 for index in range(len(ordered_months))])
    ax.set_xticklabels([month.strftime("%Y-%m") for month in ordered_months], rotation=30, ha="right")
    ax.set_yticks([0.5, 1.5, 2.5])
    ax.set_yticklabels(["Rank 3", "Rank 2", "Rank 1"])
    ax.set_title("Last 12 Months: Pick Rotation Blocks")
    ax.set_xlabel("Rebalance Month")
    ax.set_ylabel("Selection Rank")
    ax.grid(False)
    ax.set_aspect("auto")
    legend_handles = [
        Patch(facecolor=color, edgecolor="none", label=ticker)
        for ticker, color in ticker_colors.items()
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.28),
        ncol=min(6, max(1, len(legend_handles))),
        frameon=False,
    )
    _save(fig, charts_dir / "last_12_month_pick_rotation.png")

    frequency = timeline["ticker"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(9, 5))
    frequency.plot.barh(ax=ax, color="#33658a")
    ax.set_title("Last 12 Months: Selection Frequency")
    ax.set_xlabel("Months Selected")
    ax.grid(axis="x", alpha=0.25)
    _save(fig, charts_dir / "last_12_month_selection_frequency.png")
    return table
