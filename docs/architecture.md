# W3-15 — QuantDash architecture

```mermaid
flowchart LR
    AV[Alpha Vantage] --> DL[Provider clients\ntimeout/retry/redaction]
    TD[Twelve Data adjust=all] --> DL
    SEC[SEC EDGAR Company Facts] --> DL
    DL --> RAW[(data/raw\nimmutable provider responses)]
    RAW --> CLEAN[Schema/date/numeric validation\nno silent fills]
    CLEAN --> PROC[(data/processed\nParquet + audit reports)]
    PROC --> TECH[Returns / SMA / EMA / RSI\nvolatility / drawdown / momentum]
    PROC --> PIT[Point-in-time SEC selector\nfiled date <= decision date]
    TECH --> ALIGN[Exact-date stock/SPY alignment]
    ALIGN --> BETA[60/126/252D beta]
    TECH --> MASTER[One-row-per-ticker master]
    PIT --> MASTER
    BETA --> MASTER
    MASTER --> SCORE[Winsorized scoring copies\npercentiles / sub-scores / labels]
    SCORE --> EXPORT[Browser-safe dashboard.json]
    TECH --> EXPORT
    EXPORT --> REACT[React Research UI\nfilter / compare / explain]
    EXPORT --> QUEST[Market Quest\nseeded fictional simulation]
    MASTER --> STREAMLIT[Legacy Streamlit interface]
    TECH --> RESEARCH[Momentum quintile\nand forward-return notebook]
```

## Boundaries

- Provider access and secret keys remain in Python; the browser receives no keys.
- Live UI interactions read one validated static snapshot and make no provider
  calls.
- Missing values remain explicit throughout the pipeline.
- The Market Quest scenario is fictional, deterministic, and separate from the
  real research snapshot.
