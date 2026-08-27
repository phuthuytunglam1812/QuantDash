# QuantDash

An educational equity screener for 20 US stocks plus the SPY benchmark.

## What the product does

QuantDash combines a transparent stock screener, ticker/SPY research console,
plain-language formula library, and five-day educational Market Quest. It is a
research starting point for beginners—not a brokerage, forecast engine, or
personalized investment recommendation.

## Data sources and price basis

- Twelve Data `adjust=all` or Alpha Vantage Daily Adjusted for historical OHLCV
- SEC EDGAR Company Facts for reported fundamentals and filing provenance
- SPY as the market benchmark

All price-derived features and comparisons use split-and-dividend-adjusted
close. Stock/SPY pairs use exact common dates without forward/zero filling.

## Core formulas

- Return: `Adjusted Close today / previous Adjusted Close - 1`
- SMA 20: `(Day 1 + ... + Day 20) / 20`
- RSI 14: `100 - 100 / (1 + Wilder Average Gain / Wilder Average Loss)`
- Volatility: `sample std. dev. of 20 log returns * sqrt(252)`
- Drawdown: `Adjusted Close / running peak - 1`
- Momentum: `Adjusted Close today / Adjusted Close N observations ago - 1`
- Beta: `covariance(stock return, SPY return) / variance(SPY return)`

Exact conventions are linked throughout `docs/` and in the in-app method library.

## Limitations

- The 20-stock universe is small; percentile steps are coarse and may have
  survivorship/selection bias.
- Fundamental coverage varies by SEC tag and issuer; missing values remain missing.
- Scores are relative cross-sectional ranks and discard some magnitude information.
- Beta and historical volatility describe past behavior; they are not forecasts.
- Momentum research uses overlapping forward windows and omits costs, taxes,
  slippage, and capacity.
- Market Quest uses a seeded fictional market and virtual money.
- The product is educational and does not provide financial advice.

## Quick start (recommended)

### What you need

- Python 3.11 or newer
- Node.js 20 or newer (Node 22 LTS is recommended)
- Git

The React demo uses the prepared snapshot in `frontend/public/data/dashboard.json`,
so API keys are **not required** just to run and explore the website.

### Windows PowerShell

Run these commands from the repository root:

```powershell
# 1. Create and activate the Python environment.
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install the Python pipeline and test dependencies.
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Install the React dependencies.
cd frontend
npm install

# 4. Start the website.
npm run dev
```

Open <http://localhost:5173> in Chrome or Edge. Keep the terminal open while
using the website. Press `Ctrl+C` in that terminal to stop it.

### Optional AI guidance

Research-intent guidance and Market Quest coaching can use the OpenAI Responses
API without exposing the secret to React. Copy `.env.example` to `.env`, add a
newly rotated key, and run the private proxy in a second PowerShell window:

```powershell
cd "C:\Users\hoang\OneDrive\Documents\paul\code in general\QuantDash"
.\.venv\Scripts\python.exe -m uvicorn ai_server:app --host 127.0.0.1 --port 8000
```

Then run `npm run dev` from `frontend` as usual. Vite proxies `/api` to the
private server. If the key/server/network is unavailable, the interface labels
and uses its local safety fallback instead of crashing.

If PowerShell blocks environment activation, run this once in the same terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cd frontend
npm install
npm run dev
```

Then open <http://localhost:5173>.

## Run it again later

The dependencies only need to be installed once. On later runs:

```powershell
cd frontend
npm run dev
```

The camera-based 67 game needs browser camera permission. Camera access works
on `localhost`; approve the permission prompt when the game starts.

## Verify the installation

From the repository root:

```powershell
# Python regression suite
.\.venv\Scripts\python.exe -m pytest -q

# React production build
cd frontend
npm run build
```

## Dependency files

- `requirements.txt` — Python pipeline, Streamlit, and automated tests
- `requirements-notebook.txt` — optional notebook-only additions
- `frontend/package.json` and `frontend/package-lock.json` — React website,
  Vite, icons, formatting, and MediaPipe camera tracking

Do not commit `.env`. Copy `.env.example` to `.env` only when refreshing data
from providers, then add your own API keys:

```powershell
Copy-Item .env.example .env
```

## Common problems

- **`npm` is not recognized:** install Node.js, reopen PowerShell, and retry.
- **Port 5173 is occupied:** run `npm run dev -- --port 5174`, then open
  <http://localhost:5174>.
- **The page shows old campaign progress:** use **Reset campaign** in Market Quest.
- **Camera does not start:** allow camera access in the browser site settings and
  reload the page.
- **Prepared market data is missing:** from the repository root, run
  `.\.venv\Scripts\python.exe -m src.export_react_data`.

## React interface prototype

The new React/Vite interface lives in `frontend/`. The tested Python pipeline remains the
source of truth: it exports a browser-safe snapshot rather than duplicating financial
calculations in JavaScript.

```powershell
# From the repository root, refresh the frontend data after rebuilding the pipeline.
.\.venv\Scripts\python.exe -m src.export_react_data

# Start the React development server.
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Build the deployable static bundle with `npm run build`.
The existing Streamlit interface remains available during the migration.

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

## SPY benchmark series (W2-01)

```powershell
python -m src.build_benchmark
```

The command extracts and validates a dedicated chronological SPY series in
`data/processed/benchmark_spy.parquet`, with simple/log returns and a JSON
coverage report. It fails if dates are duplicated or stored returns disagree
with the underlying closes.

## Exact stock/SPY alignment (W2-02)

```powershell
python -m src.align_returns
```

Dates are parsed in UTC and normalized to timezone-naive calendar days before
an exact inner join. No forward fill, backward fill, zero fill, nearest-date
matching, or `merge_asof` is used. Per-ticker dropped-date counts are written to
`data/processed/alignment_audit.csv`.

## Rolling beta (W2-03)

```powershell
python -m src.calculate_beta
```

The build creates strict full-window `beta_60`, `beta_126`, and `beta_252`
series plus observation-count columns. It never relabels a partial sample as a
longer beta. See `docs/beta_formula.md` for the formula and null rules.

## Provider beta comparison (W2-04)

```powershell
python -m src.compare_beta
```

The comparison uses Alpha Vantage `OVERVIEW.Beta` and caches raw responses.
Provider beta is never treated as methodologically identical to explicit
60/126/252-day betas; missing provider values remain null and are never filled.

## Trading-day momentum (W2-05)

```powershell
python -m src.build_momentum
```

Momentum uses exact 21/63/126 trading-observation lags for approximately
1/3/6 months. It does not use calendar offsets, nearest dates, or missing-value
fills. See `docs/momentum_formula.md`.

## Fundamental growth (W2-06)

```powershell
python -m src.build_fundamental_growth
```

Revenue growth is YoY for the latest SEC-framed standalone quarter versus the
same quarter one year earlier. Profit margin uses revenue and net income with
identical period boundaries. YTD, QoQ, nearest-period, and filled substitutes
are prohibited. See `docs/fundamental_growth_formula.md`.

## Master feature table (W2-07)

```powershell
python -m src.build_master_features
```

The master table uses validated one-to-one joins to create one row per ticker.
SPY is retained for benchmark/technical features; company fundamental, growth,
and beta fields remain null rather than being filled with zero.

## Missing-data report (W2-08)

```powershell
python -m src.build_missing_report
```

The report calculates feature-level missing rates using eligible denominators.
SPY's structurally inapplicable company fundamentals are excluded from stock
missing rates rather than counted as data defects. No values are filled.

## Outlier and P/E transformations (W2-09)

```powershell
python -m src.transform_features
```

Raw values remain unchanged. Scoring copies are winsorized at stock-only P5/P95
with explicit flags and recorded bounds. Nonpositive/missing provider P/E is
excluded as not meaningful rather than changed to zero. See
`docs/transformation_rules.md`.

## Feature distributions (W2-10)

```powershell
python -m src.analyze_distributions
```

The analysis excludes SPY, writes descriptive statistics for 20 stocks, and
creates histogram and raw-vs-winsorized boxplot PNGs. It does not alter data or
transformation rules.

## Feature correlations (W2-11)

```powershell
python -m src.build_correlations
```

The Pearson matrix uses 20 stock rows and scoring-safe features. SPY is
excluded. Missing P/E uses pairwise complete observations; no zero/median fill
is applied. The output includes pair counts, ranked pairs, and an annotated
heatmap.

## Percentile features (W2-12)

```powershell
python -m src.build_percentiles
```

Raw cross-sectional percentiles are separated from direction-adjusted scores.
Beta, volatility, and RSI remain descriptive. Output retains raw magnitude,
winsorized scoring values, rank position, and eligible count. Small-universe
precision and magnitude-loss warnings are documented in
`docs/percentile_interpretation.md`.

## Experimental composite score (W2-13)

```powershell
python -m src.build_composite_score
```

The build creates momentum, quality, and valuation sub-scores before a
40%/40%/20% composite. Beta is excluded and retained as risk context. Missing
sub-scores trigger weight renormalization plus explicit coverage and incomplete
flags. Full weight rationale is in `docs/composite_weight_justification.md`.

## Signal labels (W2-14)

```powershell
python -m src.build_signal_labels
```

## Interactive filters and sorting (W2-15)

The Streamlit screener supports simultaneous AND filters for momentum, profit
margin, P/E, beta, composite score, and W2-14 Overall Signal labels. Missing
values never pass an active feature filter and are never filled with zero. The
UI reports `x of 20 stocks`, provides a Reset Filters button, and lets the user
choose displayed columns. See `docs/screener_filter_rules.md` for exact rules.

## RSI vs P/E Signal Map (W2-16)

The Plotly bubble chart consumes the live W2-15 filtered subset. It maps raw P/E
against RSI 14, sizes bubbles by composite score, colors them by W2-14 Overall
Signal, and explicitly reports rows excluded because either axis is missing.
See `docs/signal_map_rules.md` for interpretation and missing-data rules.

## Ticker deep dive (W2-17)

The detail view uses split-and-dividend-adjusted close and supports 3M, 6M, 1Y,
and 2Y calendar lookbacks. It shows adjusted price with SMA 20/50, Wilder RSI
14, explicitly labeled 20-trading-day annualized volatility, and drawdown
recomputed from the selected-period peak. Exact formulas and warm-up behavior
are documented in `docs/deep_dive_methodology.md`.

## Benchmark comparison (W2-18)

The selected ticker is compared with SPY over the same W2-17 timeframe. Both
use split-and-dividend-adjusted close, are inner-joined on identical trading
dates without filling missing values, and are indexed to 100 on their first
common date. Summary cards show ticker return, SPY return, excess return in
percentage points, and the common-date count. See
`docs/benchmark_comparison_methodology.md` for exact rules.

## Survey-informed guided workflow

The app now presents a short optional onboarding guide and a four-stage flow:
Screen → Compare → Understand → Form a view. Selected-ticker context explains
P/E, margin, RSI, and volatility relative to the available data, while the
evidence summary separates strengths, cautions, and missing information. The
design rationale and survey limitations are recorded in
`docs/survey_informed_design.md`.

Momentum, fundamentals, valuation, and overall labels are displayed separately.
Incomplete composites include an explicit coverage warning. Beta and other risk
context do not affect labels. See `docs/signal_label_rules.md`.

## Week 3 validation and research

```powershell
python -m src.validate_lookahead
python -m src.momentum_research
pytest -q
```

- `docs/lookahead_bias_checklist.md` — future-information audit
- `docs/point_in_time_fundamental_rule.md` — SEC filing-date availability
- `docs/split_dividend_handling.md` — adjusted-price conventions
- `docs/missing_dates_lookback_test_report.md` — edge cases and warm-up rules
- `docs/error_handling_test_report.md` — P/E, variance, and provider failures
- `notebook/02_momentum_quintile_research.ipynb` — top/bottom quintile study
- `docs/architecture.md` — end-to-end data flow
- `docs/deployment.md` — Streamlit and React deployment runbooks
