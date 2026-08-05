# RSI formula note (W1-15)

QuantDash uses **Wilder's 14-period RSI**, implemented directly in
`src/features.py` without a technical-analysis library.

1. Compute daily change: `change_t = close_t - close_(t-1)`.
2. Split it into `gain_t = max(change_t, 0)` and
   `loss_t = max(-change_t, 0)`.
3. Seed average gain and loss with the arithmetic means of the first 14 changes.
4. Thereafter apply Wilder smoothing:

   `avg_t = ((13 * avg_(t-1)) + current_t) / 14`

5. Calculate `RS = average_gain / average_loss` and
   `RSI = 100 - 100 / (1 + RS)`.

The first 14 rows per symbol are null because 14 changes require 15 prices.
If average loss is zero RSI is 100; if average gain is zero RSI is 0; if both
are zero (a flat market), RSI is defined as neutral at 50.
