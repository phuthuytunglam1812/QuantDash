# W3-04 — Missing dates and insufficient-lookback test report

## Policies validated

### Calendar gaps

Weekends, holidays, and exchange closures are not missing rows that should be
invented. Return and momentum windows count actual ordered trading
observations—not calendar days. A Friday-to-Monday return is valid when both
prices exist.

### Missing observations

- A missing price is never converted to zero or carried forward.
- Returns touching a missing price remain `NaN`.
- Stock/SPY observations are paired only by an exact normalized date inner join.
- A missing stock or SPY return removes that pair from beta input.

### Insufficient history

| Feature | Minimum history |
|---|---:|
| RSI 14 | 15 prices / 14 changes |
| SMA 20 and EMA 20 | 20 prices |
| 20D annualized volatility | 20 valid returns / 21 prices |
| SMA 50 | 50 prices |
| Momentum 21/63/126 | N+1 prices for an N-observation lag |
| Beta 60/126/252 | Entire named window of valid aligned return pairs |

Before the required lookback exists, the named feature remains `NaN`. A shorter
window is never relabelled as a longer indicator.

### Recovery after a gap

Rolling beta remains unavailable while a missing pair is inside its window. It
becomes available only after that gap has rolled out and a complete new window
exists. Dashboard benchmark comparison fails clearly when fewer than two common
adjusted-close dates remain.

## Automated evidence

`tests/test_missing_dates_lookback.py` covers calendar gaps, missing prices,
short histories, rolling-beta recovery, exact-date alignment, insufficient
benchmark overlap, and preservation of indicator warm-up nulls in the UI data.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_missing_dates_lookback.py -q
```
