"""Small, safe probes used to compare candidate market-data providers."""

from __future__ import annotations

import os
import re
import time
from dataclasses import asdict, dataclass
from typing import Callable

import pandas as pd
import requests
import yfinance as yf
from dotenv import load_dotenv


@dataclass
class ProbeResult:
    provider: str
    success: bool
    rows: int = 0
    columns: str = ""
    latest_date: str = ""
    elapsed_seconds: float = 0.0
    note: str = ""


def _safe_error(exc: Exception) -> str:
    """Return useful diagnostics without leaking credentials embedded in URLs."""
    message = str(exc)
    for variable in ("ALPHA_VANTAGE_API_KEY", "TWELVE_DATA_API_KEY"):
        secret = os.getenv(variable, "").strip()
        if secret:
            message = message.replace(secret, "[REDACTED]")
    message = re.sub(r"(?i)(apikey=)[^&\s\"']+", r"\1[REDACTED]", message)
    return f"{type(exc).__name__}: {message}"


def _summarize(provider: str, started: float, frame: pd.DataFrame) -> ProbeResult:
    if frame.empty:
        raise ValueError("provider returned no price rows")
    latest = pd.to_datetime(frame.index).max()
    return ProbeResult(
        provider=provider,
        success=True,
        rows=len(frame),
        columns=", ".join(map(str, frame.columns)),
        latest_date=latest.strftime("%Y-%m-%d"),
        elapsed_seconds=round(time.perf_counter() - started, 3),
    )


def probe_yfinance(symbol: str = "AAPL") -> ProbeResult:
    started = time.perf_counter()
    frame = yf.download(symbol, period="1mo", interval="1d", progress=False, auto_adjust=False)
    return _summarize("yfinance", started, frame)


def probe_alpha_vantage(symbol: str = "AAPL") -> ProbeResult:
    started = time.perf_counter()
    key = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("ALPHA_VANTAGE_API_KEY is missing")
    response = requests.get(
        "https://www.alphavantage.co/query",
        params={"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "compact", "apikey": key},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    values = payload.get("Time Series (Daily)")
    if not values:
        message = payload.get("Note") or payload.get("Information") or payload.get("Error Message")
        raise RuntimeError(message or "unexpected Alpha Vantage response")
    frame = pd.DataFrame.from_dict(values, orient="index")
    return _summarize("Alpha Vantage", started, frame)


def probe_twelve_data(symbol: str = "AAPL") -> ProbeResult:
    started = time.perf_counter()
    key = os.getenv("TWELVE_DATA_API_KEY", "").strip()
    if not key:
        raise RuntimeError("TWELVE_DATA_API_KEY is missing")
    response = requests.get(
        "https://api.twelvedata.com/time_series",
        params={"symbol": symbol, "interval": "1day", "outputsize": 30, "apikey": key},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") == "error" or "values" not in payload:
        raise RuntimeError(payload.get("message", "unexpected Twelve Data response"))
    frame = pd.DataFrame(payload["values"]).set_index("datetime")
    return _summarize("Twelve Data", started, frame)


def probe_sec_edgar(symbol: str = "AAPL") -> ProbeResult:
    """Probe SEC Company Facts; this is fundamentals evidence, not OHLCV."""
    started = time.perf_counter()
    user_agent = os.getenv("SEC_USER_AGENT", "").strip()
    if not user_agent:
        raise RuntimeError("SEC_USER_AGENT is missing")
    # W1 universe mapping can be generalized in the production fundamentals client.
    sample_ciks = {"AAPL": "0000320193", "MSFT": "0000789019"}
    cik = sample_ciks.get(symbol.upper())
    if not cik:
        raise ValueError(f"no sample CIK configured for {symbol}")
    response = requests.get(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    concepts = payload.get("facts", {}).get("us-gaap", {})
    if not concepts:
        raise RuntimeError("SEC response contained no us-gaap company facts")
    filed_dates = [
        item.get("filed")
        for concept in concepts.values()
        for unit_items in concept.get("units", {}).values()
        for item in unit_items
        if item.get("filed")
    ]
    return ProbeResult(
        provider="SEC EDGAR",
        success=True,
        rows=len(concepts),
        columns="XBRL us-gaap concepts (fundamentals; not OHLCV)",
        latest_date=max(filed_dates) if filed_dates else "",
        elapsed_seconds=round(time.perf_counter() - started, 3),
        note=payload.get("entityName", ""),
    )


def compare_providers(symbol: str = "AAPL") -> pd.DataFrame:
    """Probe all providers independently so one failure does not stop the comparison."""
    load_dotenv()
    probes: list[tuple[str, Callable[[str], ProbeResult]]] = [
        ("yfinance", probe_yfinance),
        ("Alpha Vantage", probe_alpha_vantage),
        ("Twelve Data", probe_twelve_data),
        ("SEC EDGAR", probe_sec_edgar),
    ]
    results: list[dict] = []
    for name, probe in probes:
        started = time.perf_counter()
        try:
            result = probe(symbol)
        except Exception as exc:  # comparison should record provider failures
            result = ProbeResult(
                provider=name,
                success=False,
                elapsed_seconds=round(time.perf_counter() - started, 3),
                note=_safe_error(exc),
            )
        results.append(asdict(result))
    return pd.DataFrame(results)


if __name__ == "__main__":
    print(compare_providers().to_string(index=False))
