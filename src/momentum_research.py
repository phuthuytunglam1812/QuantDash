"""Point-in-time momentum quintiles and forward-return research outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def build_momentum_research(
    prices: pd.DataFrame,
    momentum_window: int = 63,
    forward_window: int = 21,
    minimum_universe: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    required = {"symbol", "date", "adjusted_close"}
    if missing := required - set(prices):
        raise ValueError(f"momentum research missing columns: {sorted(missing)}")
    frame = prices[list(required)].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    frame["adjusted_close"] = pd.to_numeric(frame["adjusted_close"], errors="coerce")
    frame = frame[frame.symbol.ne("SPY")].sort_values(["symbol", "date"])
    if frame.duplicated(["symbol", "date"]).any():
        raise ValueError("momentum research requires unique symbol/date rows")
    grouped = frame.groupby("symbol", sort=False)["adjusted_close"]
    frame["momentum_63d"] = grouped.pct_change(momentum_window, fill_method=None)
    frame["forward_return_21d"] = grouped.shift(-forward_window) / frame["adjusted_close"] - 1
    frame = frame.dropna(subset=["momentum_63d", "forward_return_21d"])

    eligible_dates = frame.groupby("date").symbol.transform("count").ge(minimum_universe)
    frame = frame[eligible_dates].copy()
    frame["quintile"] = frame.groupby("date")["momentum_63d"].transform(
        lambda values: pd.qcut(
            values.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
        ).astype(int)
    )
    frame["forward_hit"] = frame["forward_return_21d"].gt(0)

    summary = (
        frame.groupby("quintile", observed=True)
        .agg(
            observations=("symbol", "size"),
            dates=("date", "nunique"),
            mean_forward_return=("forward_return_21d", "mean"),
            median_forward_return=("forward_return_21d", "median"),
            hit_rate=("forward_hit", "mean"),
        )
        .reset_index()
    )
    by_date = (
        frame.groupby(["date", "quintile"], observed=True).forward_return_21d.mean()
        .unstack("quintile")
        .rename(columns=lambda value: f"q{value}")
        .reset_index()
    )
    by_date["top_minus_bottom"] = by_date["q5"] - by_date["q1"]
    spread = by_date[["date", "q1", "q5", "top_minus_bottom"]]
    spread_values = spread.top_minus_bottom.dropna()
    report = {
        "momentum_window_trading_observations": momentum_window,
        "forward_window_trading_observations": forward_window,
        "minimum_cross_section": minimum_universe,
        "price_basis": "adjusted_close",
        "formation_and_forward_separation": True,
        "missing_policy": "complete signal and forward-return rows only; no fill",
        "observations": len(frame),
        "formation_dates": int(frame.date.nunique()),
        "symbols": int(frame.symbol.nunique()),
        "mean_top_minus_bottom": float(spread_values.mean()),
        "median_top_minus_bottom": float(spread_values.median()),
        "positive_spread_hit_rate": float(spread_values.gt(0).mean()),
        "limitations": [
            "Current fixed 20-stock universe may introduce survivorship bias.",
            "Overlapping 21-day forward returns are descriptive and not independent bets.",
            "No transaction costs, taxes, slippage, or capacity constraints are modeled.",
            "This is educational historical research, not an investment recommendation.",
        ],
    }
    return frame.reset_index(drop=True), summary, spread, report


def run(data_dir: str | Path = "data") -> dict:
    processed = Path(data_dir) / "processed"
    prices = pd.read_parquet(processed / "price_features.parquet")
    observations, summary, spread, report = build_momentum_research(prices)
    observations.to_parquet(processed / "momentum_quintile_observations.parquet", index=False)
    summary.to_csv(processed / "momentum_quintile_summary.csv", index=False)
    spread.to_csv(processed / "momentum_quintile_spread_by_date.csv", index=False)
    (processed / "momentum_research_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    print(json.dumps(run(args.data_dir), indent=2))


if __name__ == "__main__":
    main()
