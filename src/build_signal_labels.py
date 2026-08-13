"""Create transparent component and overall signal labels from W2-13 scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


LABEL_RULES = [
    (80.0, "Strong"),
    (60.0, "Positive"),
    (40.0, "Neutral"),
    (20.0, "Weak"),
    (0.0, "Very Weak"),
]


def score_label(value) -> str:
    if pd.isna(value):
        return "Unavailable"
    numeric = float(value)
    if numeric < 0 or numeric > 100:
        raise ValueError(f"score outside 0-100: {numeric}")
    for threshold, label in LABEL_RULES:
        if numeric >= threshold:
            return label
    raise AssertionError("unreachable score label")


def build_labels_from_frame(scores: pd.DataFrame) -> pd.DataFrame:
    required = {
        "symbol", "momentum_subscore", "quality_subscore", "valuation_subscore",
        "composite_score", "score_coverage", "incomplete_score_flag", "score_eligible",
    }
    if missing := required - set(scores.columns):
        raise ValueError(f"signal input missing columns: {sorted(missing)}")
    if scores["symbol"].duplicated().any():
        raise ValueError("signal input contains duplicate symbols")
    result = scores.copy()
    result["momentum_label"] = result["momentum_subscore"].map(score_label)
    result["fundamentals_label"] = result["quality_subscore"].map(score_label)
    result["valuation_label"] = result["valuation_subscore"].map(score_label)
    result["overall_label"] = result["composite_score"].map(score_label)
    result["overall_display_label"] = result.apply(
        lambda row: (
            "Unavailable"
            if pd.isna(row["composite_score"])
            else (
                f"{row['overall_label']} (Incomplete: {row['score_coverage']:.0%} coverage)"
                if row["incomplete_score_flag"]
                else row["overall_label"]
            )
        ),
        axis=1,
    )
    result["signal_is_eligible"] = result["score_eligible"] & result["composite_score"].notna()
    result["signal_note"] = result.apply(
        lambda row: (
            "Below minimum score coverage; do not rank"
            if not row["signal_is_eligible"]
            else (
                "Composite renormalized because one or more sub-scores are unavailable"
                if row["incomplete_score_flag"]
                else "Full intended score coverage"
            )
        ),
        axis=1,
    )
    result["risk_context_note"] = "Beta, volatility, RSI, and drawdown are context; not label inputs"
    return result


def build_signal_labels(data_dir: str | Path = "data") -> tuple[pd.DataFrame, dict]:
    processed = Path(data_dir) / "processed"
    scores = pd.read_parquet(processed / "composite_scores.parquet")
    labeled = build_labels_from_frame(scores)
    labeled.to_parquet(processed / "signal_labels.parquet", index=False)
    labeled.to_csv(processed / "signal_labels.csv", index=False)
    report = {
        "label_rules": [
            {"minimum_inclusive": threshold, "label": label} for threshold, label in LABEL_RULES
        ],
        "missing_label": "Unavailable",
        "component_labels": ["momentum_label", "fundamentals_label", "valuation_label"],
        "overall_label": "overall_label",
        "coverage_warning_in_display": True,
        "risk_features_in_labels": False,
        "stocks": len(labeled),
        "overall_distribution": labeled["overall_label"].value_counts(dropna=False).to_dict(),
    }
    (processed / "signal_label_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return labeled, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    labeled, report = build_signal_labels(args.data_dir)
    print(json.dumps(report, indent=2))
    print(labeled[[
        "symbol", "momentum_subscore", "momentum_label", "quality_subscore",
        "fundamentals_label", "valuation_subscore", "valuation_label",
        "composite_score", "overall_display_label", "signal_note",
    ]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
