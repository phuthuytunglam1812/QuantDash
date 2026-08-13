# Transformation rules (W2-09)

## Preservation rule

Raw master features are never overwritten. Scoring-safe copies use the suffix
`_winsorized`, and every transformed feature has an `_outlier_flag`. No ticker
is deleted and missing values are not filled.

## Winsorization

The 20-stock cross-section supplies empirical P5 and P95 bounds. Values below
P5 are capped at P5 and values above P95 are capped at P95 only in scoring
copies. SPY is excluded from bound estimation. Exact bounds and cap counts are
stored in `winsorization_bounds.csv`.

Applied to beta 252, 21/63/126-day momentum, annualized volatility, YoY revenue
growth, quarterly profit margin, and P/E. RSI is already bounded; identifiers,
flags, counts, daily returns, and drawdowns are not winsorized.

## P/E

P/E comes from cached Alpha Vantage `OVERVIEW.PERatio`, which is a trailing
provider valuation. QuantDash does not divide price by a single quarterly EPS
and mislabel it as P/E. Provider P/E and EPS are preserved as raw provenance.

P/E is meaningful for scoring only when provider EPS and P/E are both present
and positive. Missing, zero, or negative values become null in `pe_ratio` with
an explicit exclusion reason. They are never converted to zero or absolute
values and are excluded from percentile estimation.
