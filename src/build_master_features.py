"""Build one audited master-feature row per stock plus the SPY benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.config import BENCHMARK


def _require_unique(frame: pd.DataFrame, name: str) -> None:
    if "symbol" not in frame:
        raise ValueError(f"{name} is missing symbol")
    duplicates = frame.loc[frame["symbol"].duplicated(keep=False), "symbol"].tolist()
    if duplicates:
        raise ValueError(f"{name} has duplicate symbols: {sorted(set(duplicates))}")


def build_master_from_frames(
    latest_technical: pd.DataFrame,
    fundamentals: pd.DataFrame,
    betas: pd.DataFrame,
    momentum: pd.DataFrame,
    growth: pd.DataFrame,
    benchmark_symbol: str = BENCHMARK,
) -> tuple[pd.DataFrame, dict]:
    sources = {
        "technical": latest_technical.copy(), "fundamentals": fundamentals.copy(),
        "beta": betas.copy(), "momentum": momentum.copy(), "growth": growth.copy(),
    }
    for name, frame in sources.items():
        frame["symbol"] = frame["symbol"].astype("string").str.strip().str.upper()
        _require_unique(frame, name)

    technical = sources["technical"]
    technical["is_benchmark"] = technical["symbol"].eq(benchmark_symbol.upper())

    fundamental_columns = [
        "symbol", "company_name", "sic", "sic_description", "fiscal_year_end", "exchange",
        "revenue", "net_income", "assets", "liabilities", "equity", "eps_diluted",
    ]
    fundamental_columns = [column for column in fundamental_columns if column in sources["fundamentals"]]
    beta_columns = [
        "symbol", "beta_60", "beta_60_n_obs", "beta_126", "beta_126_n_obs",
        "beta_252", "beta_252_n_obs",
    ]
    momentum_columns = [
        "symbol", "momentum_21d", "momentum_21d_n_obs", "momentum_63d",
        "momentum_63d_n_obs", "momentum_126d", "momentum_126d_n_obs",
    ]
    growth_columns = [
        "symbol", "revenue_growth_yoy", "profit_margin", "latest_frame",
        "comparison_frame", "revenue_growth_available", "profit_margin_available",
        "unusual_margin_flag", "quality_note",
    ]

    # Dedicated snapshot tables are authoritative for these features. Remove
    # overlapping technical copies so pandas never creates ambiguous _x/_y columns.
    authoritative_columns = set(beta_columns[1:] + momentum_columns[1:] + growth_columns[1:])
    technical = technical.drop(columns=[column for column in authoritative_columns if column in technical.columns])

    master = technical.merge(
        sources["fundamentals"][fundamental_columns], on="symbol", how="left", validate="one_to_one"
    )
    master = master.merge(sources["beta"][beta_columns], on="symbol", how="left", validate="one_to_one")
    master = master.merge(
        sources["momentum"][momentum_columns], on="symbol", how="left", validate="one_to_one"
    )
    master = master.merge(sources["growth"][growth_columns], on="symbol", how="left", validate="one_to_one")

    master["has_fundamentals"] = master["company_name"].notna()
    master["has_beta"] = master["beta_252"].notna()
    master["has_momentum"] = master["momentum_126d"].notna()
    master["has_growth"] = master["revenue_growth_yoy"].notna()
    master = master.sort_values(["is_benchmark", "symbol"], kind="stable").reset_index(drop=True)

    stocks = master[~master["is_benchmark"]]
    report = {
        "rows": len(master),
        "stock_rows": len(stocks),
        "benchmark_rows": int(master["is_benchmark"].sum()),
        "duplicate_symbols": int(master["symbol"].duplicated().sum()),
        "stock_coverage": {
            "fundamentals": int(stocks["has_fundamentals"].sum()),
            "beta": int(stocks["has_beta"].sum()),
            "momentum": int(stocks["has_momentum"].sum()),
            "growth": int(stocks["has_growth"].sum()),
        },
        "benchmark_policy": "retain SPY technical/momentum row; company fundamentals, growth, and beta remain null",
        "fill_policy": "none",
        "join_validation": "one_to_one",
    }
    return master, report


def build_master_features(data_dir: str | Path = "data") -> tuple[pd.DataFrame, dict]:
    processed = Path(data_dir) / "processed"
    features = pd.read_parquet(processed / "price_features.parquet")
    latest_technical = (
        features.sort_values(["symbol", "date"], kind="stable")
        .groupby("symbol", sort=True).tail(1).reset_index(drop=True)
    )
    fundamentals = pd.read_parquet(processed / "fundamentals_clean.parquet")
    betas = pd.read_csv(processed / "latest_beta.csv", parse_dates=["date"]).drop(columns=["date"])
    momentum = pd.read_csv(processed / "latest_momentum.csv", parse_dates=["date"]).drop(columns=["date", "close"])
    growth = pd.read_csv(processed / "fundamental_growth.csv")
    master, report = build_master_from_frames(latest_technical, fundamentals, betas, momentum, growth)
    master.to_parquet(processed / "master_features.parquet", index=False)
    master.to_csv(processed / "master_features.csv", index=False)
    report["columns"] = list(master.columns)
    (processed / "master_features_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return master, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    master, report = build_master_features(args.data_dir)
    print(json.dumps(report, indent=2))
    print(master[[
        "symbol", "is_benchmark", "close", "rsi_14", "beta_252",
        "momentum_126d", "revenue_growth_yoy", "profit_margin",
    ]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
