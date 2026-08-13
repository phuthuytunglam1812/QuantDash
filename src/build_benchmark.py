"""Build the normalized SPY benchmark return series for Week 2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import BENCHMARK


BENCHMARK_COLUMNS = [
    "date", "symbol", "close", "simple_return", "log_return", "provider",
]


def build_benchmark(data_dir: str | Path = "data", symbol: str = BENCHMARK) -> tuple[pd.DataFrame, dict]:
    """Extract a unique, chronological benchmark series from clean features."""
    processed = Path(data_dir) / "processed"
    source = processed / "price_features.parquet"
    if not source.exists():
        raise FileNotFoundError(f"feature dataset not found: {source}")

    features = pd.read_parquet(source)
    missing = set(BENCHMARK_COLUMNS) - set(features.columns)
    if missing:
        raise ValueError(f"feature dataset is missing benchmark fields: {sorted(missing)}")

    benchmark = features.loc[
        features["symbol"].astype("string").str.upper().eq(symbol.upper()),
        BENCHMARK_COLUMNS,
    ].copy()
    if benchmark.empty:
        raise ValueError(f"benchmark symbol {symbol!r} is absent from the feature dataset")

    benchmark["date"] = pd.to_datetime(benchmark["date"], errors="raise").dt.normalize()
    benchmark["symbol"] = benchmark["symbol"].astype("string").str.upper()
    benchmark["provider"] = benchmark["provider"].astype("string").str.lower()
    for column in ["close", "simple_return", "log_return"]:
        benchmark[column] = pd.to_numeric(benchmark[column], errors="coerce")
    benchmark = benchmark.sort_values("date", kind="stable").reset_index(drop=True)

    duplicate_dates = int(benchmark["date"].duplicated().sum())
    if duplicate_dates:
        raise ValueError(f"benchmark contains {duplicate_dates} duplicate dates")
    if benchmark["close"].isna().any() or benchmark["close"].le(0).any():
        raise ValueError("benchmark close prices must be complete and positive")

    expected_simple = benchmark["close"].pct_change(fill_method=None)
    expected_log = np.log(benchmark["close"]).diff()
    if not np.allclose(benchmark["simple_return"], expected_simple, equal_nan=True):
        raise ValueError("stored SPY simple returns do not match close prices")
    if not np.allclose(benchmark["log_return"], expected_log, equal_nan=True):
        raise ValueError("stored SPY log returns do not match close prices")

    output = processed / "benchmark_spy.parquet"
    benchmark.to_parquet(output, index=False)
    report = {
        "symbol": symbol.upper(),
        "source": str(source),
        "output": str(output),
        "rows": len(benchmark),
        "return_rows": int(benchmark["simple_return"].notna().sum()),
        "first_date": benchmark["date"].min().strftime("%Y-%m-%d"),
        "last_date": benchmark["date"].max().strftime("%Y-%m-%d"),
        "duplicate_dates": duplicate_dates,
        "missing_close": int(benchmark["close"].isna().sum()),
        "expected_initial_return_nulls": int(benchmark["simple_return"].isna().sum()),
        "return_definition": "close-to-close; simple and logarithmic; raw provider close",
    }
    (processed / "benchmark_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return benchmark, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--symbol", default=BENCHMARK)
    args = parser.parse_args()
    _, report = build_benchmark(args.data_dir, args.symbol)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
