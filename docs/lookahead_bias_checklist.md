# W3-01 — Look-ahead bias validation checklist

Decision time for the current screener is the latest normalized market date in
`price_features.parquet`. A value is eligible only if it was observable on or
before that date.

| Area | Validation rule | Evidence | Result |
|---|---|---|---|
| Returns | Uses the same row and the immediately preceding price within ticker | `pct_change(fill_method=None)` and prefix-invariance test | Pass |
| SMA / EMA | Rolling/expanding state ends at the current observation | Prefix-invariance test after changing all future prices | Pass |
| RSI | Wilder seed and recursion consume gains/losses through the current row only | Prefix-invariance test | Pass |
| Volatility | Trailing 20 log returns, full window required | Prefix-invariance test | Pass |
| Drawdown | Running peak and cumulative minimum through the current row | Prefix-invariance test | Pass |
| Momentum | Exact 21/63/126-observation backward lags; no nearest-date fill | Prefix-invariance and warm-up tests | Pass |
| Beta | Trailing aligned stock/SPY returns with full 60/126/252 windows | Beta prefix-invariance test | Pass |
| Current fundamental snapshot | Filing and period dates must not exceed the screener as-of date | `lookahead_bias_audit.json` | Pass for current snapshot |
| Historical fundamentals | A historical row may use only filings available by that row's date | Point-in-time rule scheduled for W3-02 | Open for W3-02 |
| Cross-sectional ranks/scores | Compare stocks from one common snapshot only | One-row-per-ticker latest snapshot | Pass for descriptive screener |
| Forward-return research | Features at time *t* must be frozen before returns after *t* are calculated | Required gate for W3-06/W3-07 | Not run yet |

## Important scope distinction

The current app is a **latest-date descriptive screener**, not a historical
backtest. Passing W3-01 means future price rows cannot alter earlier technical
features and the current snapshot contains no source dates beyond its as-of
date. It does not authorize historical use of today's latest fundamental value.
W3-02 will implement the filing-date-aware point-in-time selection needed before
the quintile and forward-return studies.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m src.validate_lookahead
.\.venv\Scripts\python.exe -m pytest tests/test_lookahead_bias.py -q
```

Machine-readable evidence is written to
`data/processed/lookahead_bias_audit.json`.
