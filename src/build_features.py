"""Build the feature dataset from clean daily prices."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.features import add_moving_averages, add_returns, add_risk_features, add_rsi


def build_features(data_dir: str | Path = "data") -> tuple[pd.DataFrame, dict]:
    processed = Path(data_dir) / "processed"
    prices = pd.read_parquet(processed / "prices_clean.parquet")
    features = add_risk_features(
        add_rsi(add_moving_averages(add_returns(prices)), period=14),
        volatility_window=20,
    )
    output = processed / "price_features.parquet"
    features.to_parquet(output, index=False)
    first_rows = features.groupby("symbol", sort=False).head(1)
    report = {
        "rows": len(features),
        "symbols": int(features["symbol"].nunique()),
        "simple_return_non_null": int(features["simple_return"].notna().sum()),
        "log_return_non_null": int(features["log_return"].notna().sum()),
        "first_row_nulls_expected": len(first_rows),
        "first_simple_return_all_null": bool(first_rows["simple_return"].isna().all()),
        "first_log_return_all_null": bool(first_rows["log_return"].isna().all()),
        "sma_20_non_null": int(features["sma_20"].notna().sum()),
        "sma_50_non_null": int(features["sma_50"].notna().sum()),
        "ema_20_non_null": int(features["ema_20"].notna().sum()),
        "warmup_nulls_per_symbol": {"sma_20": 19, "sma_50": 49, "ema_20": 19},
        "rsi_14_non_null": int(features["rsi_14"].notna().sum()),
        "rsi_14_warmup_nulls_per_symbol": 14,
        "volatility_20d_annualized_non_null": int(features["volatility_20d_annualized"].notna().sum()),
        "volatility_warmup_nulls_per_symbol": 20,
        "drawdown_non_null": int(features["drawdown"].notna().sum()),
        "max_drawdown_to_date_non_null": int(features["max_drawdown_to_date"].notna().sum()),
        "formula": {
            "simple_return": "close_t / close_(t-1) - 1",
            "log_return": "ln(close_t / close_(t-1))",
            "rsi_14": "100 - 100 / (1 + WilderAvgGain14 / WilderAvgLoss14)",
            "volatility_20d_annualized": "std_sample(last 20 log returns) * sqrt(252)",
            "drawdown": "close / cumulative_max(close) - 1",
            "max_drawdown_to_date": "cumulative_min(drawdown)",
        },
        "note": "Returns use provider close, not adjusted close; first row per symbol is undefined.",
    }
    (processed / "feature_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return features, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    _, report = build_features(args.data_dir)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
