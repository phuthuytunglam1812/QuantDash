# Signal-label rules (W2-14)

Component and overall labels use the same transparent 0–100 thresholds:

| Score | Label |
|---|---|
| 80–100 | Strong |
| 60–<80 | Positive |
| 40–<60 | Neutral |
| 20–<40 | Weak |
| 0–<20 | Very Weak |
| Missing | Unavailable |

QuantDash displays momentum, fundamentals, valuation, and overall labels
separately. A strong overall label does not imply that every component is
strong. This makes combinations such as Strong Momentum, Strong Fundamentals,
Weak Valuation, and Positive Overall visible to users.

If the composite was renormalized because a sub-score is unavailable, the
display label includes coverage, for example `Positive (Incomplete: 80%
coverage)`. Scores below the 80% minimum are not eligible for ranking.

Beta, volatility, RSI, and drawdown remain risk/state context and do not change
these labels. Labels are relative experimental screening summaries for this
20-stock universe, not buy/sell recommendations.
