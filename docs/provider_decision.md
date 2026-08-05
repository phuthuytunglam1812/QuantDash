# Data-provider decision (W1-07)

Status: decided by data type after live probes.

## Decision

There is no single primary provider because prices and financial statements are
different datasets:

| Data needed | Primary | Fallback | Reason |
|---|---|---|---|
| Daily OHLCV | Alpha Vantage | Twelve Data | Documented market-data APIs; both passed the live probe |
| Company fundamentals | SEC EDGAR Company Facts | Alpha Vantage, if a normalized field is unavailable | SEC is the authoritative filing/XBRL source and requires no API key |
| Local development only | yfinance | — | Convenient for quick prototypes, but unofficial and lower priority |

SEC EDGAR does **not** replace a price provider: Company Facts and submissions
contain filing/XBRL data, not exchange OHLCV bars. Conversely, a price API is not
the source of record for reported financial statements.

## Live evidence

The OHLCV probes on 2026-08-05 (Asia/Saigon) returned:

| Provider | Success | Rows | Latest date |
|---|---:|---:|---|
| yfinance | Yes | 22 | 2026-08-04 |
| Alpha Vantage | Yes | 100 | 2026-08-04 |
| Twelve Data | Yes | 30 | 2026-08-04 |

The SEC Company Facts probe also succeeded, returning **503 US-GAAP concepts**
for Apple Inc.; the most recent filing date present was **2026-07-31**.

The different row counts reflect provider-specific sample sizes, not different
quality scores. Run `python -m src.api_comparison` to refresh the evidence and
include the SEC Company Facts probe.

## Trade-offs

- Alpha Vantage's compact daily response is sufficient for connectivity tests,
  but longer history and adjusted-price access depend on the chosen plan.
- SEC facts need CIK mapping, taxonomy normalization, unit selection, and careful
  handling of amended filings and repeated facts.
- yfinance remains useful for debugging, but the pipeline must not silently use
  it when an official/configured source fails.

## Revisit when

- the API plan cannot cover 21 symbols within its request budget;
- adjusted price history is required but unavailable on the selected plan;
- the project needs production uptime, licensing, or redistribution guarantees.
