# W3-18 — Final presentation (7-slide speaking notes)

## Slide 1 — The beginner research problem

New investors see many unexplained ratios and signals, while typical screeners
encourage ranking before understanding. QuantDash asks users to Screen → Compare
→ Understand → Form a view.

## Slide 2 — Product experience

Show the futuristic React interface, combined Filter Lab, configurable columns,
Signal Map, ticker console, method library, and SPY comparison. Emphasize Apply
Filters, remaining-stock count, and explicit missing values.

## Slide 3 — Trustworthy data pipeline

Use `docs/architecture.md`. Twelve Data/Alpha Vantage provide adjusted prices;
SEC EDGAR provides filing-proven fundamentals. Raw responses are preserved,
processed layers are typed, dates are normalized, and stock/SPY returns use
exact inner joins.

## Slide 4 — Transparent quantitative methods

Explain trading-observation windows, full warm-ups, RSI, annualized volatility,
drawdown, momentum, and beta. Scores separate momentum, quality, and valuation;
beta remains risk context. Missing components renormalize weights with coverage.

## Slide 5 — Validation and small research result

Mention look-ahead prefix tests, point-in-time filing rules, adjusted/unadjusted
tests, edge cases, provider failures, and the full regression suite. The
63-observation momentum study contains 8,440 observations across 422 formation
dates. Historical Q5−Q1 21-day spread averaged about 1.90 percentage points and
was positive about 55.5% of formation dates, before costs and with overlapping
windows.

## Slide 6 — Learning through simulation

Show the five-day path: learn → pass 70% → arcade reward → inspect fictional
market → allocate across companies → receive next-day P&L. The deterministic
seed makes demonstrations reproducible; outcomes remain separate from live data.

## Slide 7 — Limits and next steps

State small-universe granularity, survivorship bias, provider coverage,
historical—not predictive—risk metrics, omitted costs, and no financial advice.
Close with external usability testing, public deployment, accessibility,
non-overlapping backtests, and larger point-in-time universes.
