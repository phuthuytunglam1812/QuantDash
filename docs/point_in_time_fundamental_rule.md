# W3-02 — Point-in-time fundamental data rule

## Rule

For a decision made on date **T**, a fundamental fact is eligible only when:

`SEC filing date <= T`

The fiscal period end does not determine when investors knew the value. For
example, a quarter ending June 30 but filed August 1 is unavailable to a July 31
screen and becomes eligible on August 1.

## Selection procedure

1. Retain supported SEC forms: 10-Q, 10-K, 20-F, and 40-F.
2. Require a parseable SEC `filed` date. Missing or invalid filing dates remain
   unavailable; they are never inferred from the period end.
3. Remove every fact whose filing date is later than the decision date.
4. Prefer a normalized standalone quarterly SEC frame when calculating growth
   or margin; do not substitute cumulative YTD values.
5. Within the eligible facts, select the most recent fiscal period and then the
   latest filing for that period. This allows an amendment only after its own
   filing date.
6. For YoY growth, both the current and prior-year quarter must be eligible at
   T. Profit margin requires revenue and net income for identical period bounds.
7. Missing eligible inputs produce `NaN`; there is no zero fill, forward fill,
   or nearest-period substitution.

## API

```python
from src.download_fundamentals import latest_fact
from src.build_fundamental_growth import calculate_company_growth

fact = latest_fact(payload, ["Assets"], "USD", as_of="2026-07-31")
growth = calculate_company_growth("AAPL", payload, as_of="2026-07-31")
```

Omitting `as_of` preserves the current latest-snapshot build. Any historical
research, including W3-06 and W3-07, must supply `as_of` explicitly.

## Validation evidence

Automated tests cover:

- a newer quarter excluded one day before filing;
- the same quarter becoming eligible on its filing date;
- future filings excluded even when their period has already ended;
- facts with missing filing dates excluded;
- same-quarter YoY and matched-period margin rules retained.
