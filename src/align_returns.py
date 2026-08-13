"""Strictly align stock and SPY returns on identical trading dates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.config import BENCHMARK


RETURN_COLUMNS = ["simple_return", "log_return"]


def normalize_trading_date(values: pd.Series) -> pd.Series:
    """Parse mixed date representations to timezone-naive UTC calendar dates."""
    parsed = pd.to_datetime(values, format="mixed", errors="coerce", utc=True)
    if parsed.isna().any():
        examples = values[parsed.isna()].astype(str).head(3).tolist()
        raise ValueError(f"unparseable trading dates: {examples}")
    return parsed.dt.normalize().dt.tz_localize(None)


def align_returns(
    stock_features: pd.DataFrame,
    benchmark: pd.DataFrame,
    benchmark_symbol: str = BENCHMARK,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Inner-join non-benchmark stocks to SPY; never fill or nearest-date match."""
    stock_required = {"date", "symbol", *RETURN_COLUMNS}
    benchmark_required = {"date", "symbol", *RETURN_COLUMNS}
    if missing := stock_required - set(stock_features.columns):
        raise ValueError(f"stock features missing columns: {sorted(missing)}")
    if missing := benchmark_required - set(benchmark.columns):
        raise ValueError(f"benchmark missing columns: {sorted(missing)}")

    stocks = stock_features[list(stock_required)].copy()
    market = benchmark[list(benchmark_required)].copy()
    stocks["date"] = normalize_trading_date(stocks["date"])
    market["date"] = normalize_trading_date(market["date"])
    stocks["symbol"] = stocks["symbol"].astype("string").str.strip().str.upper()
    market["symbol"] = market["symbol"].astype("string").str.strip().str.upper()
    stocks = stocks[~stocks["symbol"].eq(benchmark_symbol.upper())].copy()
    market = market[market["symbol"].eq(benchmark_symbol.upper())].copy()

    if market.empty:
        raise ValueError(f"benchmark {benchmark_symbol!r} is absent")
    if stocks.duplicated(["symbol", "date"]).any():
        raise ValueError("stock returns contain duplicate symbol/date keys")
    if market["date"].duplicated().any():
        raise ValueError("benchmark returns contain duplicate dates")

    for column in RETURN_COLUMNS:
        stocks[column] = pd.to_numeric(stocks[column], errors="coerce")
        market[column] = pd.to_numeric(market[column], errors="coerce")

    market = market.rename(columns={
        "simple_return": "benchmark_simple_return",
        "log_return": "benchmark_log_return",
    })[["date", "benchmark_simple_return", "benchmark_log_return"]]

    records = []
    aligned_groups = []
    for symbol, group in stocks.groupby("symbol", sort=True):
        stock_valid = group.dropna(subset=RETURN_COLUMNS).copy()
        benchmark_valid = market.dropna(subset=["benchmark_simple_return", "benchmark_log_return"])
        merged = stock_valid.merge(
            benchmark_valid,
            on="date",
            how="inner",
            validate="one_to_one",
            sort=True,
        )
        aligned_groups.append(merged)
        stock_dates = set(stock_valid["date"])
        benchmark_dates = set(benchmark_valid["date"])
        records.append({
            "symbol": symbol,
            "stock_rows_total": len(group),
            "stock_valid_return_rows": len(stock_valid),
            "benchmark_valid_return_rows": len(benchmark_valid),
            "aligned_rows": len(merged),
            "stock_dates_without_benchmark": len(stock_dates - benchmark_dates),
            "benchmark_dates_without_stock": len(benchmark_dates - stock_dates),
            "stock_null_return_rows_removed": len(group) - len(stock_valid),
            "fill_method": "none",
            "join_method": "exact-date inner join",
        })

    aligned = pd.concat(aligned_groups, ignore_index=True) if aligned_groups else pd.DataFrame()
    aligned = aligned[[
        "date", "symbol", "simple_return", "log_return",
        "benchmark_simple_return", "benchmark_log_return",
    ]].sort_values(["symbol", "date"], kind="stable").reset_index(drop=True)
    audit = pd.DataFrame(records)
    return aligned, audit


def build_aligned_returns(data_dir: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    processed = Path(data_dir) / "processed"
    features = pd.read_parquet(processed / "price_features.parquet")
    benchmark = pd.read_parquet(processed / "benchmark_spy.parquet")
    aligned, audit = align_returns(features, benchmark)
    aligned.to_parquet(processed / "aligned_stock_spy_returns.parquet", index=False)
    audit.to_csv(processed / "alignment_audit.csv", index=False)
    report = {
        "stock_symbols": int(aligned["symbol"].nunique()),
        "aligned_rows": len(aligned),
        "first_date": aligned["date"].min().strftime("%Y-%m-%d"),
        "last_date": aligned["date"].max().strftime("%Y-%m-%d"),
        "duplicate_symbol_dates": int(aligned.duplicated(["symbol", "date"]).sum()),
        "missing_return_cells": int(aligned.drop(columns=["date", "symbol"]).isna().sum().sum()),
        "join": "exact normalized UTC date, inner join",
        "fill": "none",
        "nearest_date_matching": False,
    }
    (processed / "alignment_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return aligned, audit, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    _, audit, report = build_aligned_returns(args.data_dir)
    print(json.dumps(report, indent=2))
    print(audit.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
