"""Download and inventory raw daily OHLCV for the configured universe."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from src.clients import MarketDataClient
from src.clients.base import DataProviderError
from src.config import BENCHMARK, TICKERS


@dataclass
class DownloadRecord:
    symbol: str
    success: bool
    rows: int = 0
    first_date: str = ""
    last_date: str = ""
    provider: str = ""
    path: str = ""
    note: str = ""


def _record(symbol: str, frame: pd.DataFrame, path: Path, note: str = "") -> DownloadRecord:
    dates = pd.to_datetime(frame["date"], errors="coerce").dropna()
    provider = str(frame["provider"].iloc[0]) if "provider" in frame and not frame.empty else ""
    return DownloadRecord(
        symbol=symbol, success=not frame.empty, rows=len(frame),
        first_date=dates.min().strftime("%Y-%m-%d") if not dates.empty else "",
        last_date=dates.max().strftime("%Y-%m-%d") if not dates.empty else "",
        provider=provider, path=str(path), note=note,
    )


def download_universe(
    output_dir: str | Path = "data/raw/prices", years: int = 2,
    end_date: date | None = None, symbols: list[str] | None = None,
    overwrite: bool = False, pause_seconds: float = 0.15,
    client: MarketDataClient | None = None,
) -> pd.DataFrame:
    """Fetch two-year raw files; existing non-empty files are resumable skips."""
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    end = end_date or date.today()
    start = end - timedelta(days=365 * years + 7)
    universe = symbols or [*TICKERS, BENCHMARK]
    market = client or MarketDataClient()
    records: list[DownloadRecord] = []
    for symbol in universe:
        path = target / f"{symbol.upper()}.csv"
        if path.exists() and path.stat().st_size > 0 and not overwrite:
            existing = pd.read_csv(path, parse_dates=["date"])
            records.append(_record(symbol, existing, path, "existing file; skipped"))
            continue
        try:
            frame = market.daily_twelve_data(
                symbol, outputsize=5000,
                start_date=start.isoformat(), end_date=end.isoformat(),
            )
            raw = frame.reset_index()
            raw.to_csv(path, index=False)
            records.append(_record(symbol, raw, path))
        except Exception as exc:
            note = str(exc) if isinstance(exc, DataProviderError) else f"{type(exc).__name__}: {exc}"
            records.append(DownloadRecord(symbol=symbol, success=False, note=note))
        time.sleep(max(0.0, pause_seconds))
    manifest = pd.DataFrame(asdict(item) for item in records)
    manifest.to_csv(target.parent / "download_manifest.csv", index=False)
    metadata = {"requested_start": start.isoformat(), "requested_end": end.isoformat(),
                "years": years, "symbols": universe}
    (target.parent / "download_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, default=2)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--symbol", action="append", dest="symbols")
    args = parser.parse_args()
    manifest = download_universe(years=args.years, symbols=args.symbols, overwrite=args.overwrite)
    print(manifest.to_string(index=False))
    return 0 if bool(manifest["success"].all()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
