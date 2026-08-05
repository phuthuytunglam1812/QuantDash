# Risk-feature formulas (W1-16)

All calculations reset at each symbol boundary and use provider closing prices.

## Annualized volatility

`volatility_20d_annualized = sample_std(last 20 daily log returns) * sqrt(252)`

The sample standard deviation uses `ddof=1`. Twenty valid returns require 21
prices, so the first 20 rows per symbol are null.

## Drawdown

`drawdown_t = close_t / max(close_0 ... close_t) - 1`

Drawdown is zero at a running high and negative below it.

## Maximum drawdown to date

`max_drawdown_to_date_t = min(drawdown_0 ... drawdown_t)`

This is the worst peak-to-current loss observed from the start of the dataset
through date `t`; it never increases toward zero.
