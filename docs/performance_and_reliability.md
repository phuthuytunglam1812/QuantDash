# W3-10 / W3-11 — Performance, caching, fallback, and errors

## Runtime architecture

The React interface performs **zero market-provider API calls** during normal
use. Python prepares `frontend/public/data/dashboard.json`; the browser fetches
that static snapshot once when the app starts. React state handles subsequent
filter, sort, chart, lesson, and simulation interactions.

Benefits:

- changing filters does not trigger an API request;
- provider rate limits cannot crash an active research session;
- one immutable snapshot keeps all cards and charts internally consistent;
- the browser and hosting platform can cache the JSON and compiled assets.

## Pipeline caching and call reduction

- Raw SEC JSON is reused unless `--overwrite` is explicitly requested.
- Existing non-empty price CSVs are skipped on repeat downloads.
- Provider beta responses are stored and reused.
- HTTP GET uses configured timeout, retry, exponential backoff, and
  `Retry-After` behavior.
- Alpha Vantage/Twelve Data fallback is explicit in the reusable client.
- Streamlit's retained interface caches its dashboard build with
  `@st.cache_data`.

## User-facing failure behavior

If the React snapshot is missing, malformed, or returns a non-success HTTP
status, the app displays a readable **Data snapshot unavailable** panel with a
Retry button and local recovery command. It does not show a blank page, invent
zero values, or erase Market Quest progress.

Pipeline failures are written to manifests/reports per ticker. Exceptions redact
API keys. Existing raw files remain resumable and a failed call never creates a
fake successful dataset.

## Deployment fallback

The committed browser-safe snapshot is the production fallback. Refreshing live
provider data is an offline build operation; if it fails, the last validated
snapshot can remain deployed with its visible market date.
