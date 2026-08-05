# QuantDash

An educational equity screener for 20 US stocks plus the SPY benchmark.

## Current milestone

W1-06 compares three OHLCV sources plus SEC EDGAR Company Facts. W1-07 assigns
providers by data type: Alpha Vantage/Twelve Data for prices, SEC for reported
fundamentals, and yfinance only for local prototyping. Secrets remain in `.env`.

```powershell
.\.venv\Scripts\Activate.ps1
python -m src.api_comparison
pytest -q
```

See `docs/provider_decision.md` for the W1-07 provider decision and recorded
live comparison evidence.

## Reusable clients (W1-08)

```python
from src.clients import MarketDataClient, SecEdgarClient

prices = MarketDataClient().daily("AAPL")  # Alpha Vantage, then Twelve Data
facts = SecEdgarClient().company_facts(320193)
filings = SecEdgarClient().submissions(320193)
```

The price client returns a date-indexed frame with `open`, `high`, `low`,
`close`, `volume`, `symbol`, and `provider`. HTTP calls use timeouts and retries;
errors redact API keys. Fallback can be disabled with
`daily("AAPL", allow_fallback=False)`.

## Two-year price download (W1-09)

```powershell
python -m src.download_prices
```

This downloads the configured 20 stocks plus SPY to `data/raw/prices/` and
writes `data/raw/download_manifest.csv`. Re-running skips existing files; use
`--overwrite` only when a fresh download is intended. The two-year backfill uses
Twelve Data because the Alpha Vantage free compact response is limited to the
latest 100 daily observations.

## SEC profiles and fundamentals (W1-10)

```powershell
python -m src.download_fundamentals
```

Raw Company Facts and submissions JSON are saved under `data/raw/sec/`.
`data/processed/fundamentals.csv` contains normalized company identity plus the
latest filed revenue, net income, assets, liabilities, equity, and diluted EPS.
Every metric retains its period end, filing date, form, and XBRL tag.

## Raw and processed layers (W1-11)

```powershell
python -m src.build_data_layers
```

Provider responses remain under `data/raw/`. Consolidated typed Parquet files
and `data_catalog.json` are written under `data/processed/`. The catalog records
schemas, coverage, row counts, symbols, and SHA-256 checksums for reproducibility.

## Cleaning and validation (W1-12)

```powershell
python -m src.clean_data
```

The command writes `prices_clean.parquet`, `fundamentals_clean.parquet`, and
`data_quality_report.json`. Invalid price rows cause a hard failure rather than
silent deletion. Fundamental nulls are retained with flags; liabilities are
derived only when assets and equity refer to the same reporting date.

## Returns (W1-13)

```powershell
python -m src.build_features
```

`price_features.parquet` contains close-to-close `simple_return` and
`log_return`, calculated separately per symbol. The first return for every
symbol is intentionally null because no prior observation exists.

## Moving averages (W1-14)

The same feature build adds `sma_20`, `sma_50`, and `ema_20`. Indicators use
full warm-up windows and reset at every symbol boundary. EMA uses
`span=20, adjust=False`.

## RSI (W1-15)

The feature build also adds manually coded Wilder `rsi_14`. See
`docs/rsi_formula.md` for the seed, recursive smoothing, warm-up, and edge-case
definitions.

## Risk features (W1-16)

The feature build adds 20-day annualized log-return volatility, current
drawdown, and maximum drawdown-to-date. Definitions and conventions are in
`docs/risk_formula.md`.

## Indicator tests (W1-17)

```powershell
pytest
```

The suite checks formulas, warm-up periods, symbol isolation, input
immutability, constant-price behavior, indicator bounds, and drawdown paths.

## Validation notebook (W1-18)

`notebook/01_data_and_indicator_validation.ipynb` independently recomputes all
nine indicators for AAPL and SPY, asserts numerical agreement, summarizes data
quality, and charts moving averages and RSI.

To execute notebooks in a fresh environment, install the additional packages
with `pip install -r requirements-notebook.txt`.

## Streamlit screener (W1-19)

```powershell
streamlit run app.py
```

The dashboard joins each ticker's latest technical features with SEC
fundamentals and provides search, RSI/volatility/trend filters, a sortable
table, CSV export, signal labels, and ticker-level price/average history.
