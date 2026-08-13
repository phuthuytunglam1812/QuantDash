"""Build transparent raw percentiles and selectively direction-adjusted scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


FEATURE_POLICY = {
    "momentum_21d": {"source": "momentum_21d_winsorized", "direction": "higher", "score": "momentum_21d_score"},
    "momentum_63d": {"source": "momentum_63d_winsorized", "direction": "higher", "score": "momentum_63d_score"},
    "momentum_126d": {"source": "momentum_126d_winsorized", "direction": "higher", "score": "momentum_126d_score"},
    "revenue_growth_yoy": {"source": "revenue_growth_yoy_winsorized", "direction": "higher", "score": "growth_score"},
    "profit_margin": {"source": "profit_margin_winsorized", "direction": "higher", "score": "profitability_score"},
    "pe_ratio": {"source": "pe_ratio_winsorized", "direction": "lower", "score": "valuation_score"},
    "drawdown": {"source": "drawdown", "direction": "higher", "score": "drawdown_resilience_score"},
    "beta_252": {"source": "beta_252_winsorized", "direction": "descriptive", "score": None},
    "volatility_20d_annualized": {"source": "volatility_20d_annualized_winsorized", "direction": "descriptive", "score": None},
    "rsi_14": {"source": "rsi_14", "direction": "descriptive", "score": None},
}


def percentile_rank(values: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return 0-100 percentile, ascending rank position, and eligible count."""
    numeric = pd.to_numeric(values, errors="coerce")
    eligible_count = int(numeric.notna().sum())
    percentile = numeric.rank(method="average", pct=True) * 100
    rank_position = numeric.rank(method="average", ascending=True)
    count = pd.Series(pd.NA, index=values.index, dtype="Int64")
    count.loc[numeric.notna()] = eligible_count
    return percentile, rank_position, count


def build_percentiles_from_frame(
    master: pd.DataFrame, feature_policy: dict = FEATURE_POLICY,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    stocks = master[~master["is_benchmark"]].copy()
    if stocks["symbol"].duplicated().any():
        raise ValueError("percentile input contains duplicate stock symbols")
    result = stocks[["symbol", "date"]].copy()
    policy_rows = []
    for feature, policy in feature_policy.items():
        source = policy["source"]
        if feature not in stocks or source not in stocks:
            raise ValueError(f"percentile input missing raw/scoring columns for {feature}")
        percentile, position, count = percentile_rank(stocks[source])
        result[f"{feature}_raw"] = stocks[feature]
        result[f"{feature}_scoring_value"] = stocks[source]
        result[f"{feature}_percentile"] = percentile
        result[f"{feature}_rank_position"] = position
        result[f"{feature}_eligible_count"] = count
        score_name = policy["score"]
        if policy["direction"] == "higher":
            result[score_name] = percentile
        elif policy["direction"] == "lower":
            result[score_name] = 100 - percentile
        policy_rows.append({
            "feature": feature, "scoring_source": source, "direction": policy["direction"],
            "direction_adjusted_score": score_name or "none",
            "eligible_count": int(stocks[source].notna().sum()),
            "approximate_rank_step_points": 100 / int(stocks[source].notna().sum()),
            "magnitude_preserved_in_raw_column": True,
        })
    return result.sort_values("symbol").reset_index(drop=True), pd.DataFrame(policy_rows)


def build_percentiles(data_dir: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    processed = Path(data_dir) / "processed"
    master = pd.read_parquet(processed / "master_features_transformed.parquet")
    percentiles, policy = build_percentiles_from_frame(master)
    percentiles.to_parquet(processed / "percentile_features.parquet", index=False)
    percentiles.to_csv(processed / "percentile_features.csv", index=False)
    policy.to_csv(processed / "percentile_feature_policy.csv", index=False)
    report = {
        "stock_rows": len(percentiles), "benchmark_excluded": True,
        "percentile_scale": "0-100; average rank for ties",
        "direction_adjustment": "only for features with explicit preference; beta, volatility, RSI remain descriptive",
        "small_sample_warning": "With 20 stocks, one rank step is approximately 5 percentage points (19 for P/E).",
        "magnitude_warning": "Percentiles preserve order, not economic distance; raw and scoring values remain beside ranks.",
        "missing_policy": "rank available stocks only; no fill; missing percentile remains null",
    }
    (processed / "percentile_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return percentiles, policy, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    percentiles, policy, report = build_percentiles(args.data_dir)
    print(json.dumps(report, indent=2))
    print(policy.to_string(index=False))
    print(percentiles[[
        "symbol", "momentum_126d_raw", "momentum_126d_percentile",
        "pe_ratio_raw", "pe_ratio_percentile", "valuation_score",
        "beta_252_raw", "beta_252_percentile",
    ]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
