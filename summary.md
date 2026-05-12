# Project Summary

## Implemented

- Modular monthly momentum backtest engine
- Cached adjusted OHLCV CSV downloads through `yfinance`
- Membership loader with current-constituent and dated-membership support
- Prior-six-completed-month momentum scoring with optional compound return scoring
- Monthly rebalance accounting, turnover, transaction cost, slippage, and benchmark comparison
- Summary statistics and requested charts
- CLI entry point and unit tests

## Test Results

- `.venv/bin/python -m pytest -q`
- Result: `5 passed`
- One environment warning remains from `urllib3` about the local Python 3.9 LibreSSL build.

## Backtest Run

- Command:
  `.venv/bin/python main.py --start-date 2016-01-01 --end-date 2026-05-12 --top-n 3 --lookback-months 6 --benchmark QQQ`
- Generated:
  - `outputs/monthly_selections.csv`
  - `outputs/portfolio_returns.csv`
  - `outputs/summary_stats.csv`
  - `outputs/last_12_month_picks.csv`
  - `outputs/charts/*.png`
- Added recent-picks visuals:
  - `outputs/charts/last_12_month_pick_rotation.png`
  - `outputs/charts/last_12_month_selection_frequency.png`
- Completed monthly portfolio rows: `117`
- Completed selection rows: `351`

Headline stats from the generated run:

- CAGR: `49.65%`
- Annualized volatility: `39.52%`
- Sharpe ratio: `1.22`
- Max drawdown: `-35.80%`
- Win rate vs QQQ: `55.56%`
- Total return: `4,992.32%`

These figures are intentionally not presented as clean institutional-grade research because the supplied membership file is a current-constituent template and therefore survivorship-biased.

## Trade Detail Rule

The completed run produced more than 30 trade rows, so no trade-by-trade appendix was added here.
