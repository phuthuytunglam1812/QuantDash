"""Build latest 1/3/6-month trading-day momentum table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.features import add_momentum


PERIODS = (21, 63, 126)


def build_momentum(data_dir: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    processed = Path(data_dir) / "processed"
    prices = pd.read_parquet(processed / "prices_clean.parquet")
    history = add_momentum(prices, PERIODS)
    columns = ["symbol", "date", "close"]
    for period in PERIODS:
        columns.extend([f"momentum_{period}d", f"momentum_{period}d_n_obs"])
    momentum = history[columns]
    latest = (
        momentum.sort_values(["symbol", "date"], kind="stable")
        .groupby("symbol", sort=True).tail(1)
        .sort_values("symbol").reset_index(drop=True)
    )
    momentum.to_parquet(processed / "momentum_history.parquet", index=False)
    latest.to_csv(processed / "latest_momentum.csv", index=False)
    report = {
        "periods": {"1_month": 21, "3_months": 63, "6_months": 126},
        "unit": "trading observations, not calendar days",
        "formula": "close_t / close_(t-N) - 1",
        "fill": "none",
        "symbols": int(momentum["symbol"].nunique()),
        "rows": len(momentum),
        "latest_non_null": {
            f"momentum_{period}d": int(latest[f"momentum_{period}d"].notna().sum())
            for period in PERIODS
        },
        "warmup_nulls_per_symbol": {f"momentum_{period}d": period for period in PERIODS},
    }
    (processed / "momentum_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return momentum, latest, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    _, latest, report = build_momentum(args.data_dir)
    print(json.dumps(report, indent=2))
    print(latest.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
