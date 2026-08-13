"""Calculate strict full-window rolling beta against SPY."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_WINDOWS = (60, 126, 252)


def add_rolling_betas(
    aligned: pd.DataFrame,
    windows: tuple[int, ...] = DEFAULT_WINDOWS,
    return_column: str = "simple_return",
    benchmark_column: str = "benchmark_simple_return",
) -> pd.DataFrame:
    """Add beta_N only when exactly N valid aligned observations are available."""
    required = {"date", "symbol", return_column, benchmark_column}
    if missing := required - set(aligned.columns):
        raise ValueError(f"aligned returns missing columns: {sorted(missing)}")
    if not windows or any(window < 2 for window in windows):
        raise ValueError("beta windows must contain integers >= 2")

    result = aligned.copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise").dt.normalize()
    result[return_column] = pd.to_numeric(result[return_column], errors="coerce")
    result[benchmark_column] = pd.to_numeric(result[benchmark_column], errors="coerce")
    if result.duplicated(["symbol", "date"]).any():
        raise ValueError("aligned returns contain duplicate symbol/date keys")
    result = result.sort_values(["symbol", "date"], kind="stable").reset_index(drop=True)

    for window in windows:
        beta_parts = []
        observation_parts = []
        variance_parts = []
        for _, group in result.groupby("symbol", sort=False):
            pair_valid = group[[return_column, benchmark_column]].notna().all(axis=1).astype("int64")
            observations = pair_valid.rolling(window, min_periods=1).sum()
            covariance = group[return_column].rolling(window, min_periods=window).cov(group[benchmark_column])
            market_variance = group[benchmark_column].rolling(window, min_periods=window).var(ddof=1)
            beta = covariance / market_variance
            beta = beta.where(observations.eq(window) & market_variance.gt(0))
            beta_parts.append(beta)
            observation_parts.append(observations.astype("int64"))
            variance_parts.append(market_variance)
        result[f"beta_{window}"] = pd.concat(beta_parts).sort_index()
        result[f"beta_{window}_n_obs"] = pd.concat(observation_parts).sort_index()
        result[f"benchmark_variance_{window}"] = pd.concat(variance_parts).sort_index()
    return result


def latest_beta_table(rolling: pd.DataFrame, windows: tuple[int, ...] = DEFAULT_WINDOWS) -> pd.DataFrame:
    columns = ["symbol", "date"]
    for window in windows:
        columns.extend([f"beta_{window}", f"beta_{window}_n_obs"])
    return (
        rolling.sort_values(["symbol", "date"], kind="stable")
        .groupby("symbol", sort=True)
        .tail(1)[columns]
        .sort_values("symbol")
        .reset_index(drop=True)
    )


def build_beta_features(
    data_dir: str | Path = "data", windows: tuple[int, ...] = DEFAULT_WINDOWS,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    processed = Path(data_dir) / "processed"
    aligned = pd.read_parquet(processed / "aligned_stock_spy_returns.parquet")
    rolling = add_rolling_betas(aligned, windows)
    latest = latest_beta_table(rolling, windows)
    rolling.to_parquet(processed / "rolling_beta.parquet", index=False)
    latest.to_csv(processed / "latest_beta.csv", index=False)

    report = {
        "windows": list(windows),
        "formula": "cov(stock simple return, SPY simple return) / var(SPY simple return)",
        "full_window_required": True,
        "partial_windows": False,
        "zero_benchmark_variance_result": "NaN",
        "rolling_rows": len(rolling),
        "symbols": int(rolling["symbol"].nunique()),
        "latest_non_null": {f"beta_{w}": int(latest[f"beta_{w}"].notna().sum()) for w in windows},
        "warmup_nulls_per_symbol": {f"beta_{w}": w - 1 for w in windows},
    }
    (processed / "beta_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return rolling, latest, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    _, latest, report = build_beta_features(args.data_dir)
    print(json.dumps(report, indent=2))
    print(latest.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
