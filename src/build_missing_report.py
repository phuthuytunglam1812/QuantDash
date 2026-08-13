"""Build feature-level missingness reports with benchmark-aware denominators."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


NON_FEATURE_METADATA = {
    "symbol", "date", "is_benchmark", "quality_note",
    "revenue_growth_available", "profit_margin_available", "unusual_margin_flag",
    "has_fundamentals", "has_beta", "has_momentum", "has_growth",
}
STOCK_ONLY_FEATURES = {
    "company_name", "sic", "sic_description", "fiscal_year_end", "exchange",
    "revenue", "net_income", "assets", "liabilities", "equity", "eps_diluted",
    "beta_60", "beta_60_n_obs", "beta_126", "beta_126_n_obs", "beta_252", "beta_252_n_obs",
    "revenue_growth_yoy", "profit_margin", "latest_frame", "comparison_frame",
    "revenue_growth_available", "profit_margin_available", "unusual_margin_flag", "quality_note",
    "has_fundamentals", "has_beta", "has_growth",
}


def build_missing_report_from_frame(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    required = {"symbol", "is_benchmark"}
    if missing := required - set(master.columns):
        raise ValueError(f"master feature table missing columns: {sorted(missing)}")
    if master["symbol"].duplicated().any():
        raise ValueError("master feature table contains duplicate symbols")

    stocks = master[~master["is_benchmark"]]
    benchmark = master[master["is_benchmark"]]
    feature_rows = []
    ticker_rows = []
    for column in master.columns:
        if column in NON_FEATURE_METADATA:
            continue
        stock_only = column in STOCK_ONLY_FEATURES
        eligible = stocks if stock_only else master
        missing_mask = eligible[column].isna()
        missing_symbols = eligible.loc[missing_mask, "symbol"].tolist()
        missing_count = int(missing_mask.sum())
        eligible_count = len(eligible)
        feature_rows.append({
            "feature": column,
            "scope": "stocks_only" if stock_only else "stocks_and_benchmark",
            "eligible_rows": eligible_count,
            "missing_count": missing_count,
            "available_count": eligible_count - missing_count,
            "missing_rate": missing_count / eligible_count if eligible_count else None,
            "missing_symbols": ",".join(missing_symbols),
            "benchmark_not_applicable": bool(stock_only and not benchmark.empty),
        })
        for symbol in missing_symbols:
            ticker_rows.append({"symbol": symbol, "feature": column, "scope": "eligible_missing"})

    report = pd.DataFrame(feature_rows).sort_values(
        ["missing_rate", "feature"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)
    missing_by_ticker = pd.DataFrame(ticker_rows, columns=["symbol", "feature", "scope"])
    summary = {
        "master_rows": len(master),
        "stock_rows": len(stocks),
        "benchmark_rows": len(benchmark),
        "features_assessed": len(report),
        "features_with_stock_missing": int(
            report.loc[report.scope.eq("stocks_only"), "missing_count"].gt(0).sum()
        ),
        "features_with_any_eligible_missing": int(report["missing_count"].gt(0).sum()),
        "benchmark_structural_missing_excluded": True,
        "fill_policy": "none",
        "denominator_policy": "stock-only features use 20 stocks; shared market features use all 21 rows",
    }
    return report, missing_by_ticker, summary


def build_missing_report(data_dir: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    processed = Path(data_dir) / "processed"
    master = pd.read_parquet(processed / "master_features.parquet")
    report, missing_by_ticker, summary = build_missing_report_from_frame(master)
    report.to_csv(processed / "missing_feature_report.csv", index=False)
    missing_by_ticker.to_csv(processed / "missing_by_ticker.csv", index=False)
    (processed / "missing_report_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return report, missing_by_ticker, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    report, _, summary = build_missing_report(args.data_dir)
    print(json.dumps(summary, indent=2))
    print(report.loc[report.missing_count.gt(0)].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
