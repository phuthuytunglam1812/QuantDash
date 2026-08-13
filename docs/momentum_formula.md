# Momentum formula (W2-05)

QuantDash interprets months as approximate US trading-session counts:

| Label | Trading-day lag |
|---|---:|
| 1 month | 21 |
| 3 months | 63 |
| 6 months | 126 |

For lag `N`:

`momentum_Nd = close_t / close_(t-N trading observations) - 1`

These are observation lags, not calendar-day offsets. The calculation does not
search for a nearby date and does not fill a missing historical close. The first
`N` rows per symbol remain null because no price exists `N` observations earlier.
The current project uses raw provider close, so these are price momentum rather
than total-return momentum.
