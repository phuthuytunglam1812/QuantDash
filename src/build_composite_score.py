"""Build transparent sub-scores and an experimental composite attractiveness score."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


MOMENTUM_WEIGHTS = {
    "momentum_21d_score": 0.20,
    "momentum_63d_score": 0.40,
    "momentum_126d_score": 0.40,
}
QUALITY_WEIGHTS = {"growth_score": 0.50, "profitability_score": 0.50}
COMPOSITE_WEIGHTS = {"momentum_subscore": 0.40, "quality_subscore": 0.40, "valuation_subscore": 0.20}


def weighted_score(
    frame: pd.DataFrame, weights: dict[str, float], require_all: bool = True,
) -> tuple[pd.Series, pd.Series]:
    """Return weighted score and intended-weight coverage; never fill missing values."""
    if abs(sum(weights.values()) - 1.0) > 1e-12:
        raise ValueError("weights must sum to 1")
    missing_columns = set(weights) - set(frame.columns)
    if missing_columns:
        raise ValueError(f"score inputs missing columns: {sorted(missing_columns)}")
    values = frame[list(weights)].apply(pd.to_numeric, errors="coerce")
    weight_series = pd.Series(weights)
    available = values.notna()
    coverage = available.mul(weight_series, axis=1).sum(axis=1)
    numerator = values.mul(weight_series, axis=1).sum(axis=1, min_count=1)
    score = numerator / coverage.where(coverage.gt(0))
    if require_all:
        score = score.where(coverage.eq(1.0))
    return score, coverage


def build_scores_from_frame(percentiles: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    if percentiles["symbol"].duplicated().any() or context["symbol"].duplicated().any():
        raise ValueError("score inputs require one row per symbol")
    result = percentiles.copy()

    # A sub-score is produced only when all intended components are available.
    result["momentum_subscore"], result["momentum_subscore_coverage"] = weighted_score(
        result, MOMENTUM_WEIGHTS, require_all=True
    )
    result["quality_subscore"], result["quality_subscore_coverage"] = weighted_score(
        result, QUALITY_WEIGHTS, require_all=True
    )
    result["valuation_subscore"] = result["valuation_score"]
    result["valuation_subscore_coverage"] = result["valuation_subscore"].notna().astype(float)

    # At composite level, renormalize across available complete sub-scores.
    result["composite_score"], result["score_coverage"] = weighted_score(
        result, COMPOSITE_WEIGHTS, require_all=False
    )
    result["intended_components_available"] = result[list(COMPOSITE_WEIGHTS)].notna().sum(axis=1)
    result["incomplete_score_flag"] = result["score_coverage"].lt(1.0)
    result["score_eligible"] = result["score_coverage"].ge(0.80)
    result["score_rank"] = result["composite_score"].where(result["score_eligible"]).rank(
        method="min", ascending=False
    ).astype("Int64")

    context_columns = [
        "symbol", "beta_252", "volatility_20d_annualized", "rsi_14", "drawdown",
        "drawdown_resilience_score", "pe_exclusion_reason", "unusual_margin_flag",
    ]
    context_columns = [column for column in context_columns if column in context]
    result = result.merge(context[context_columns], on="symbol", how="left", validate="one_to_one")
    result["beta_role"] = "risk/sensitivity context; excluded from composite"
    result["score_interpretation"] = (
        "experimental relative attractiveness; inspect raw values, coverage, and risk context"
    )
    return result.sort_values(["score_rank", "symbol"], na_position="last").reset_index(drop=True)


def build_composite_score(data_dir: str | Path = "data") -> tuple[pd.DataFrame, dict]:
    processed = Path(data_dir) / "processed"
    percentiles = pd.read_parquet(processed / "percentile_features.parquet")
    context = pd.read_parquet(processed / "master_features_transformed.parquet")
    scores = build_scores_from_frame(percentiles, context)
    scores.to_parquet(processed / "composite_scores.parquet", index=False)
    scores.to_csv(processed / "composite_scores.csv", index=False)
    report = {
        "stocks": len(scores),
        "subscores": {
            "momentum": MOMENTUM_WEIGHTS,
            "quality": QUALITY_WEIGHTS,
            "valuation": {"valuation_score": 1.0},
        },
        "composite_weights": COMPOSITE_WEIGHTS,
        "beta_in_composite": False,
        "risk_context_outside_composite": ["beta_252", "volatility_20d_annualized", "rsi_14", "drawdown"],
        "missing_policy": "subscores require all components; composite renormalizes available complete subscores",
        "minimum_score_coverage": 0.80,
        "full_coverage_stocks": int(scores["score_coverage"].eq(1).sum()),
        "incomplete_stocks": int(scores["incomplete_score_flag"].sum()),
        "eligible_stocks": int(scores["score_eligible"].sum()),
        "warning": "Experimental cross-sectional score for a 20-stock universe; not an investment recommendation.",
    }
    (processed / "composite_score_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return scores, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    scores, report = build_composite_score(args.data_dir)
    print(json.dumps(report, indent=2))
    print(scores[[
        "score_rank", "symbol", "momentum_subscore", "quality_subscore",
        "valuation_subscore", "composite_score", "score_coverage",
        "incomplete_score_flag", "beta_252",
    ]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
