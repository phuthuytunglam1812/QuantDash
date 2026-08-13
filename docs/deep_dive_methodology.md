# Ticker deep-dive methodology (W2-17)

## Price basis

All price-derived calculations use daily **adjusted close**. Twelve Data is
requested with `adjust=all`, which applies both split and dividend adjustments.
The normalized schema retains `adjusted_close` and records
`price_adjustment=splits_and_dividends`. Alpha Vantage fallback requests its
Daily Adjusted endpoint and normalizes the adjusted-close field identically.

Raw close is retained for provenance, but it is not the basis for return,
moving-average, RSI, momentum, volatility, or drawdown features.

## Formulas

- Simple return: `adjusted_close[t] / adjusted_close[t-1] - 1`.
- Log return: `ln(adjusted_close[t] / adjusted_close[t-1])`.
- SMA(N): arithmetic mean of adjusted close over N trading observations.
- EMA(20): adjusted-close exponentially weighted mean with span 20 and
  `adjust=False`.
- RSI(14): Wilder-smoothed average gain and loss over 14 trading observations.
- 20D annualized volatility: sample standard deviation (`ddof=1`) of the latest
  20 adjusted-close daily log returns, multiplied by `sqrt(252)`.
- Selected-timeframe drawdown: `adjusted_close / cumulative_max(adjusted_close)
  - 1` inside the visible timeframe.
- Selected-timeframe maximum drawdown: minimum of that drawdown series.

## Timeframes

The UI supports 3M, 6M, 1Y, and 2Y as calendar lookbacks from the latest
available observation. Timeframe selection controls the visible data and resets
the drawdown peak to the beginning of that visible window. It does not
recalculate rolling SMA, RSI, or volatility without warm-up history: those
features are calculated on the full series first and then sliced.

This distinction is intentional. A 20-day volatility point shown at the start
of a 3M chart may use observations immediately before the chart boundary, while
the 3M drawdown begins with a fresh in-window peak.
