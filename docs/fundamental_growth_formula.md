# Fundamental growth formulas (W2-06)

## Revenue growth

QuantDash uses year-over-year quarterly growth:

`revenue_growth_yoy = latest standalone-quarter revenue / same-quarter prior-year revenue - 1`

Only SEC facts carrying a standalone calendar-quarter frame such as `CY2026Q2`
are candidates. A YTD fact is not substituted, and the nearest available quarter
is not used when the exact prior-year comparison is missing.

For banks, `RevenuesNetOfInterestExpense` is accepted as the comparable top-line
tag. The selected XBRL tag remains in the output.

## Profit margin

`profit_margin = standalone-quarter net income / standalone-quarter revenue`

The revenue and net-income facts must have identical period start and end dates.
This prevents quarterly revenue from being mixed with six- or nine-month net
income. Missing comparisons remain null and are accompanied by quality flags.
An absolute quarterly margin above 75% is retained but flagged for source review;
it is not clipped, winsorized, or silently removed.
