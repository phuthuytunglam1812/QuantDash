# W3-03 — Split and dividend price handling

## Decision

Every return, moving average, RSI, volatility, drawdown, momentum value, chart,
and stock-versus-SPY comparison uses **adjusted close** for both sides.

Adjusted close restates historical prices for corporate actions:

- A stock split changes the number of shares and quoted price but does not by
  itself destroy investor value.
- A cash dividend transfers value from the company to the shareholder. A raw
  ex-dividend price drop is therefore not the complete investment return.

Using raw close would make these events look like ordinary losses and would
distort all downstream indicators.

## Provider provenance

| Provider response | `adjusted_close` | `unadjusted_close` |
|---|---|---|
| Alpha Vantage Daily Adjusted | Explicit adjusted-close field | Explicit raw `close` retained |
| Twelve Data with `adjust=all` | Returned `close` is adjusted for splits and dividends | Unavailable, therefore `NaN` |

An adjusted Twelve Data close must not be copied into a column named
`unadjusted_close`. W3-03 corrects that previous provenance label.

## Pipeline safeguards

1. `adjusted_close` is required, numeric, populated, and strictly positive.
2. The pipeline fails instead of silently falling back to raw close.
3. A provider value is retained as `unadjusted_close` only when it is explicitly
   supplied as raw close.
4. The internal feature input `close` is then replaced with `adjusted_close`.
5. Stock and SPY comparisons use the same adjusted basis and exact common dates.

## Controlled examples

### 2-for-1 split

Raw close moves from `$100` to `$50`, apparently `-50%`. If adjusted history is
`$50 → $50`, the economic return is `0%`. QuantDash produces `0%`.

### $1 cash dividend

Raw close moves from `$100` to `$99`, apparently `-1%`. When the adjusted series
is `$99 → $99`, the total-return comparison is `0%`. QuantDash produces `0%`.

These are simplified validation fixtures; the provider calculates the exact
historical adjustment factors.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_adjusted_prices.py -q
.\.venv\Scripts\python.exe -m src.build_features
```
