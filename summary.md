# Project Summary

## Implemented

- Modular monthly momentum backtest engine
- Cached adjusted OHLCV CSV downloads through `yfinance`
- Membership loader with current-constituent and dated-membership support
- Prior-six-completed-month momentum scoring with optional compound return scoring
- Monthly rebalance accounting, turnover, transaction cost, slippage, and benchmark comparison
- Summary statistics and requested charts
- Local Flask dashboard for current picks, recent pick history, and live refreshes
- CLI entry point and unit tests

## Test Results

- `.venv/bin/python -m pytest -q`
- Result: `7 passed`
- One environment warning remains from `urllib3` about the local Python 3.9 LibreSSL build.

## Backtest Run

- Command:
  `.venv/bin/python main.py --start-date 2016-01-01 --end-date 2026-05-12 --top-n 3 --lookback-months 6 --benchmark QQQ --secondary-benchmark TQQQ`
- Generated:
  - `outputs/monthly_selections.csv`
  - `outputs/portfolio_returns.csv`
  - `outputs/summary_stats.csv`
  - `outputs/comparison_stats.csv`
  - `outputs/last_12_month_picks.csv`
  - `outputs/charts/*.png`
- Added recent-picks visuals:
  - `outputs/charts/last_12_month_pick_rotation.png`
  - `outputs/charts/last_12_month_selection_frequency.png`
- Completed monthly portfolio rows: `117`
- Completed selection rows: `351`

Headline stats from the generated run:

- CAGR: `83.42%`
- Annualized volatility: `51.65%`
- Sharpe ratio: `1.43`
- Max drawdown: `-36.48%`
- Win rate vs QQQ: `59.83%`
- Total return: `36,926.79%`

These figures are intentionally not presented as clean institutional-grade research because the supplied membership file is a current-constituent template and therefore survivorship-biased.

## Strategy vs QQQ and TQQQ Buy & Hold

<!-- PERFORMANCE_TABLE_START -->
| Metric | Strategy | QQQ Buy & Hold | TQQQ Buy & Hold |
|---|---:|---:|---:|
| Final equity | $37,026,781.04 | $622,982.40 | $2,743,567.20 |
| Total return | 36,926.78% | 522.98% | 2,643.57% |
| CAGR | 83.42% | 20.64% | 40.45% |
| Annualized volatility | 51.65% | 20.11% | 62.87% |
| Sharpe ratio | 1.43 | 1.04 | 0.86 |
| Max drawdown | -36.48% | -33.67% | -80.13% |
| Average monthly return | 6.15% | 1.74% | 4.52% |
| Median monthly return | 3.60% | 2.08% | 5.10% |
| Best month | 60.73% | 16.69% | 52.19% |
| Worst month | -23.40% | -15.58% | -52.31% |
<!-- PERFORMANCE_TABLE_END -->

## Trade Detail Rule

The completed run produced more than 30 trade rows, so no trade-by-trade appendix was added here.
