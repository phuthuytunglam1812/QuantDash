# Percentile interpretation (W2-12)

## Position is not preference

A raw percentile only reports relative position. A P/E percentile of 80 means
P/E is higher than most peers; it does not mean the stock is 80% favorable.
Direction-adjusted scores are separate columns. Lower P/E receives a higher
valuation score, while higher momentum, revenue growth, profit margin, and
drawdown resilience receive higher scores. Beta, volatility, and RSI remain
descriptive because “higher is better” is not a defensible universal rule.

## Small-universe precision

There are 20 stocks, so one rank position is roughly five percentage points.
P/E has only 19 eligible stocks, so its step is roughly 5.26 points. A label
such as “95th percentile” should be interpreted as an approximate rank near the
top of this small universe, not population-level statistical precision.

## Percentiles lose magnitude

Ranks preserve ordering but discard economic distance. Growth of 20% versus
200% may be only one rank step apart, just like 10% versus 11%. QuantDash keeps
raw values and winsorized scoring values next to each percentile and rank
position so users can inspect magnitude. Percentiles are a robust starting
point for screening, not a complete investment conclusion.

Missing values are not filled and receive no percentile or adjusted score.
