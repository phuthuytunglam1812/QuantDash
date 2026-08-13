# Screener filter rules (W2-15)

## Combination rule

Every active criterion is combined with logical **AND**. A stock must pass all
enabled numeric filters, the selected signal labels, and the basic search,
RSI, volatility, and trend filters.

## Missing-value rule

Missing data is never converted to zero. If a filter is active for a feature,
a stock with a missing value for that feature does not pass that filter. If the
filter is inactive, the stock may remain visible and the table displays the
value as unavailable.

For example, a missing P/E does not pass `P/E <= 35`; it is not interpreted as
a zero P/E. This conservative behavior prevents absent provider data from
creating a false match.

## Units

Momentum, revenue growth, and profit margin controls use percentage points in
the UI: a stored value of `0.10` is shown and filtered as `10%`. P/E and beta
use their natural ratio units, while scores use the 0–100 scale.

## Signal and risk separation

The categorical Overall Signal filter uses W2-14 labels. Beta remains an
optional risk/sensitivity filter and is not part of the composite score or its
signal label.

## User feedback and controls

- The result count shows `x of 20 stocks`, including a valid zero-result state.
- Reset Filters restores all controls to their defaults.
- Columns to Show lets the user choose which available features appear.
- Results are sorted by composite score descending, with missing scores last.

