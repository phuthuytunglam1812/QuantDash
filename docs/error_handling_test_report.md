# W3-05 — P/E, zero-variance, and API-failure handling

## Nonpositive or unavailable P/E

Raw provider values are retained for audit, but valuation scoring requires both
trailing EPS and provider P/E to be strictly positive.

| Condition | Scoring P/E | Behavior |
|---|---|---|
| P/E < 0 | `NaN` | Excluded with `provider P/E nonpositive` |
| P/E = 0 | `NaN` | Excluded with `provider P/E nonpositive` |
| EPS <= 0 | `NaN` | Excluded with `provider EPS nonpositive` |
| Missing/unparseable P/E | `NaN` | Excluded with `provider P/E missing` |

No invalid valuation is converted to zero, made artificially cheap, or allowed
to pass an active P/E filter.

## Zero variance

- A constant adjusted-price path legitimately produces `0` realized volatility.
- A benchmark return window with zero variance produces `NaN` beta because the
  beta denominator is zero.
- Infinite beta is prohibited.
- Constant cross-sectional features can be winsorized without division errors,
  invented outliers, or infinite values.

## Provider and API failures

- HTTP timeout, connection, status, and JSON parsing failures become
  `DataProviderError`.
- API keys are redacted from exception messages.
- A non-object JSON payload is rejected as an invalid provider response.
- The configured HTTP layer retries eligible GET failures and uses a timeout.
- A failed price download writes a failure row to the manifest but does not
  create a fake or empty ticker CSV.
- Missing provider data remains missing; it is not replaced with zero.

## Automated evidence

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_error_handling.py -q
```

The tests cover negative/zero P/E, nonpositive EPS, constant features, zero
price and benchmark variance, timeouts, secret redaction, malformed JSON, and
failed download persistence.
