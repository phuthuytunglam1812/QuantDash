"""Build stock-only feature correlation matrices and an annotated heatmap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FEATURE_MAP = {
    "Beta 252": "beta_252_winsorized",
    "Momentum 21D": "momentum_21d_winsorized",
    "Momentum 63D": "momentum_63d_winsorized",
    "Momentum 126D": "momentum_126d_winsorized",
    "Volatility 20D": "volatility_20d_annualized_winsorized",
    "RSI 14": "rsi_14",
    "Drawdown": "drawdown",
    "Revenue Growth YoY": "revenue_growth_yoy_winsorized",
    "Profit Margin": "profit_margin_winsorized",
    "P/E": "pe_ratio_winsorized",
}


def correlation_outputs(
    frame: pd.DataFrame, feature_map: dict[str, str] = FEATURE_MAP,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    missing = set(feature_map.values()) - set(frame.columns)
    if missing:
        raise ValueError(f"correlation input missing columns: {sorted(missing)}")
    numeric = frame[list(feature_map.values())].apply(pd.to_numeric, errors="coerce")
    numeric = numeric.rename(columns={source: label for label, source in feature_map.items()})
    correlation = numeric.corr(method="pearson", min_periods=3)
    available = numeric.notna().astype("int64")
    pair_counts = available.T.dot(available)

    pairs = []
    labels = correlation.columns.tolist()
    for i, left in enumerate(labels):
        for right in labels[i + 1:]:
            value = correlation.loc[left, right]
            pairs.append({
                "feature_1": left, "feature_2": right, "correlation": value,
                "absolute_correlation": abs(value) if pd.notna(value) else None,
                "pairwise_observations": int(pair_counts.loc[left, right]),
            })
    strongest = pd.DataFrame(pairs).sort_values(
        ["absolute_correlation", "feature_1", "feature_2"],
        ascending=[False, True, True], kind="stable",
    ).reset_index(drop=True)
    return correlation, pair_counts, strongest


def plot_heatmap(correlation: pd.DataFrame, pair_counts: pd.DataFrame, output: Path) -> None:
    size = len(correlation)
    fig, axis = plt.subplots(figsize=(13, 11))
    image = axis.imshow(correlation.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    axis.set_xticks(range(size), correlation.columns, rotation=45, ha="right")
    axis.set_yticks(range(size), correlation.index)
    for row in range(size):
        for column in range(size):
            value = correlation.iloc[row, column]
            count = int(pair_counts.iloc[row, column])
            if pd.notna(value):
                color = "white" if abs(value) >= .55 else "black"
                axis.text(column, row, f"{value:.2f}\n(n={count})", ha="center", va="center", fontsize=7.5, color=color)
    axis.set_title("Stock feature Pearson correlations\nP5/P95 scoring features; SPY excluded; pairwise complete observations")
    colorbar = fig.colorbar(image, ax=axis, shrink=.8)
    colorbar.set_label("Pearson correlation")
    fig.tight_layout()
    fig.savefig(output, dpi=170, bbox_inches="tight")
    plt.close(fig)


def build_correlations(data_dir: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    processed = Path(data_dir) / "processed"
    master = pd.read_parquet(processed / "master_features_transformed.parquet")
    stocks = master[~master["is_benchmark"]].copy()
    if len(stocks) != 20:
        raise ValueError(f"expected 20 stocks, found {len(stocks)}")
    correlation, counts, strongest = correlation_outputs(stocks)
    correlation.to_csv(processed / "feature_correlation_matrix.csv")
    counts.to_csv(processed / "feature_correlation_pair_counts.csv")
    strongest.to_csv(processed / "feature_correlation_pairs.csv", index=False)
    plot_heatmap(correlation, counts, processed / "feature_correlation_heatmap.png")
    report = {
        "method": "Pearson",
        "stock_rows": len(stocks),
        "benchmark_excluded": True,
        "missing_policy": "pairwise complete observations; no fill",
        "feature_columns": FEATURE_MAP,
        "pairs_absolute_correlation_ge_0_70": int(strongest.absolute_correlation.ge(.70).sum()),
        "strongest_pairs": strongest.head(10).to_dict(orient="records"),
        "caution": "Cross-sectional n=20; correlations are descriptive and unstable, not causal.",
    }
    (processed / "feature_correlation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return correlation, counts, strongest, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    _, _, strongest, report = build_correlations(args.data_dir)
    print(json.dumps(report, indent=2))
    print(strongest.head(15).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
