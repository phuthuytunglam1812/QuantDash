# W3-08 — Explain This Signal

The ticker console includes an expandable **Explain This Signal** panel. It
shows the current rule result, exact threshold bands, component scores and
labels, score coverage, weighting rule, and risk-context exclusions.

Overall labels are deterministic:

- Strong: score >= 80
- Positive: 60–79.9
- Neutral: 40–59.9
- Weak: 20–39.9
- Very Weak: below 20
- Unavailable: score missing or below eligibility requirements

The explanation separates momentum, fundamentals, and valuation. It explicitly
states that beta, RSI, volatility, and drawdown do not change the attractiveness
label and that no label is a buy/sell recommendation.
