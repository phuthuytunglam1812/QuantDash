# Benchmark comparison methodology (W2-18)

The ticker-versus-SPY view reuses the ticker and timeframe selected in W2-17.
It compares investment-return series on a consistent basis:

1. Select the stock and SPY daily `adjusted_close` observations inside the same
   calendar timeframe.
2. Inner join on the exact normalized trading date.
3. Drop a common-date pair if either adjusted close is missing. Do not
   forward-fill, backfill, interpolate, or replace missing data with zero.
4. Require at least two valid common dates.
5. Divide each series by its own adjusted close on the first common date and
   multiply by 100.

The two indexed series therefore start together at 100. The summary uses the
same first and last common observations as the chart:

- Stock return: `stock_last / stock_first - 1`.
- SPY return: `SPY_last / SPY_first - 1`.
- Excess return in percentage points: `(stock_return - SPY_return) * 100`.

The UI reports the common observation count and unmatched dates excluded from
each side. Both stock and SPY use provider `adjust=all`, covering splits and
cash dividends. Comparing one adjusted series with one raw-close series is not
permitted.
