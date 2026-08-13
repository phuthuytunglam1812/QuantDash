"""Create stock-only feature distribution statistics and plots."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


FEATURES = [
    "beta_252", "momentum_21d", "momentum_63d", "momentum_126d",
    "volatility_20d_annualized", "rsi_14", "drawdown",
    "revenue_growth_yoy", "profit_margin", "pe_ratio",
]


def distribution_statistics(frame: pd.DataFrame, features: list[str] = FEATURES) -> pd.DataFrame:
    rows = []
    for feature in features:
        values = pd.to_numeric(frame[feature], errors="coerce").dropna()
        rows.append({
            "feature": feature, "eligible_rows": len(frame), "available_count": len(values),
            "missing_count": len(frame) - len(values),
            "missing_rate": (len(frame) - len(values)) / len(frame) if len(frame) else None,
            "mean": values.mean(), "median": values.median(), "std": values.std(ddof=1),
            "min": values.min(), "p05": values.quantile(.05), "p25": values.quantile(.25),
            "p75": values.quantile(.75), "p95": values.quantile(.95), "max": values.max(),
            "skewness": values.skew(), "strong_skew_flag": abs(values.skew()) > 1 if len(values) >= 3 else None,
        })
    return pd.DataFrame(rows)


def plot_histograms(frame: pd.DataFrame, output: Path, features: list[str] = FEATURES) -> None:
    columns = 2
    rows = math.ceil(len(features) / columns)
    fig, axes = plt.subplots(rows, columns, figsize=(14, rows * 3.4))
    axes = axes.ravel()
    for axis, feature in zip(axes, features):
        values = pd.to_numeric(frame[feature], errors="coerce").dropna()
        bins = min(10, max(5, len(values) // 2))
        axis.hist(values, bins=bins, color="#4472C4", alpha=.82, edgecolor="white")
        if not values.empty:
            axis.axvline(values.median(), color="#ED7D31", linestyle="--", label="Median")
            axis.axvline(values.mean(), color="#70AD47", linestyle=":", label="Mean")
        axis.set_title(feature.replace("_", " ").title())
        axis.set_ylabel("Stocks")
        axis.grid(axis="y", alpha=.2)
        axis.legend(fontsize=8)
    for axis in axes[len(features):]:
        axis.set_visible(False)
    fig.suptitle("QuantDash stock feature distributions (n=20; SPY excluded)", fontsize=15, y=.995)
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_raw_vs_winsorized(frame: pd.DataFrame, output: Path) -> None:
    comparable = [feature for feature in FEATURES if f"{feature}_winsorized" in frame.columns]
    fig, axes = plt.subplots(math.ceil(len(comparable) / 2), 2, figsize=(14, math.ceil(len(comparable) / 2) * 3.2))
    axes = axes.ravel()
    for axis, feature in zip(axes, comparable):
        raw = pd.to_numeric(frame[feature], errors="coerce").dropna()
        winsor = pd.to_numeric(frame[f"{feature}_winsorized"], errors="coerce").dropna()
        axis.boxplot([raw, winsor], tick_labels=["Raw", "P5/P95 scoring"], vert=True)
        axis.set_title(feature.replace("_", " ").title())
        axis.grid(axis="y", alpha=.2)
    for axis in axes[len(comparable):]:
        axis.set_visible(False)
    fig.suptitle("Raw vs winsorized stock features", fontsize=15, y=.995)
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def build_distribution_analysis(data_dir: str | Path = "data") -> tuple[pd.DataFrame, dict]:
    processed = Path(data_dir) / "processed"
    frame = pd.read_parquet(processed / "master_features_transformed.parquet")
    stocks = frame[~frame["is_benchmark"]].copy()
    if len(stocks) != 20:
        raise ValueError(f"expected 20 stock rows, found {len(stocks)}")
    stats = distribution_statistics(stocks)
    stats.to_csv(processed / "feature_distribution_statistics.csv", index=False)
    plot_histograms(stocks, processed / "feature_distributions.png")
    plot_raw_vs_winsorized(stocks, processed / "feature_raw_vs_winsorized.png")
    report = {
        "stock_rows": len(stocks), "benchmark_excluded": True,
        "features_analyzed": FEATURES,
        "strongly_skewed_features": stats.loc[stats.strong_skew_flag.eq(True), "feature"].tolist(),
        "features_with_missing": stats.loc[stats.missing_count.gt(0), "feature"].tolist(),
        "interpretation": "descriptive only; no transformation rules changed",
    }
    (processed / "feature_distribution_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return stats, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    stats, report = build_distribution_analysis(args.data_dir)
    print(json.dumps(report, indent=2))
    print(stats.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
