"""Validate, clean, and document the processed QuantDash datasets."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


OHLC = ["open", "high", "low", "close"]
FUNDAMENTAL_METRICS = ["revenue", "net_income", "assets", "liabilities", "equity", "eps_diluted"]


class DataQualityError(ValueError):
    """Input violates a rule that must not be repaired silently."""


def clean_prices(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    required = {"date", "symbol", "open", "high", "low", "close", "adjusted_close", "volume", "provider"}
    missing_columns = required - set(frame.columns)
    if missing_columns:
        raise DataQualityError(f"prices missing columns: {sorted(missing_columns)}")
    clean = frame.copy()
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce").dt.normalize()
    clean["symbol"] = clean["symbol"].astype("string").str.strip().str.upper()
    clean["provider"] = clean["provider"].astype("string").str.strip().str.lower()
    for column in [*OHLC, "adjusted_close", "volume"]:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    issue_counts = {
        "missing_date": int(clean["date"].isna().sum()),
        "missing_symbol": int((clean["symbol"].isna() | clean["symbol"].eq("")).sum()),
        "duplicate_symbol_date": int(clean.duplicated(["symbol", "date"]).sum()),
        "missing_ohlcv_cells": int(clean[[*OHLC, "volume"]].isna().sum().sum()),
        "missing_adjusted_close": int(clean["adjusted_close"].isna().sum()),
        "nonpositive_adjusted_close_rows": int(clean["adjusted_close"].le(0).sum()),
        "nonpositive_price_rows": int(clean[OHLC].le(0).any(axis=1).sum()),
        "negative_volume_rows": int(clean["volume"].lt(0).sum()),
        "high_below_ohlc_rows": int(clean["high"].lt(clean[OHLC].max(axis=1)).sum()),
        "low_above_ohlc_rows": int(clean["low"].gt(clean[OHLC].min(axis=1)).sum()),
    }
    if any(issue_counts.values()):
        details = ", ".join(f"{key}={value}" for key, value in issue_counts.items() if value)
        raise DataQualityError(f"price validation failed: {details}")
    clean["volume"] = clean["volume"].round().astype("int64")
    clean["price_adjustment"] = "splits_and_dividends"
    clean = clean.sort_values(["symbol", "date"], kind="stable").reset_index(drop=True)
    report = {
        "rows": len(clean), "symbols": int(clean["symbol"].nunique()),
        "first_date": clean["date"].min().strftime("%Y-%m-%d"),
        "last_date": clean["date"].max().strftime("%Y-%m-%d"),
        "issues": issue_counts,
        "actions": ["normalized dates", "uppercased symbols", "coerced numeric fields", "sorted by symbol/date"],
    }
    return clean, report


def clean_fundamentals(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    required = {"symbol", "assets", "liabilities", "equity"}
    missing_columns = required - set(frame.columns)
    if missing_columns:
        raise DataQualityError(f"fundamentals missing columns: {sorted(missing_columns)}")
    clean = frame.copy()
    clean["symbol"] = clean["symbol"].astype("string").str.strip().str.upper()
    if clean["symbol"].duplicated().any():
        raise DataQualityError("fundamentals contain duplicate symbols")
    for metric in FUNDAMENTAL_METRICS:
        clean[metric] = pd.to_numeric(clean[metric], errors="coerce")
        for suffix in ("period_end", "filed"):
            column = f"{metric}_{suffix}"
            if column in clean:
                clean[column] = pd.to_datetime(clean[column], errors="coerce").dt.normalize()
    liabilities_missing_before = int(clean["liabilities"].isna().sum())
    same_period = clean["assets_period_end"].eq(clean["equity_period_end"])
    derivable = clean["liabilities"].isna() & clean["assets"].notna() & clean["equity"].notna() & same_period
    clean.loc[derivable, "liabilities"] = clean.loc[derivable, "assets"] - clean.loc[derivable, "equity"]
    clean.loc[derivable, "liabilities_period_end"] = clean.loc[derivable, "assets_period_end"]
    clean.loc[derivable, "liabilities_filed"] = clean.loc[derivable, ["assets_filed", "equity_filed"]].max(axis=1)
    clean.loc[derivable, "liabilities_form"] = "DERIVED"
    clean.loc[derivable, "liabilities_tag"] = "derived: Assets - StockholdersEquity"
    for metric in FUNDAMENTAL_METRICS:
        clean[f"{metric}_is_missing"] = clean[metric].isna()
    negative_balance_rows = int(clean[["assets", "liabilities", "equity"]].lt(0).any(axis=1).sum())
    clean = clean.sort_values("symbol", kind="stable").reset_index(drop=True)
    report = {
        "rows": len(clean), "symbols": int(clean["symbol"].nunique()),
        "liabilities_missing_before": liabilities_missing_before,
        "liabilities_derived": int(derivable.sum()),
        "negative_balance_rows": negative_balance_rows,
        "missing_after": {metric: int(clean[metric].isna().sum()) for metric in FUNDAMENTAL_METRICS},
        "actions": ["normalized symbols and dates", "coerced numeric metrics",
                    "derived liabilities only for matching assets/equity periods", "added missing-value flags"],
    }
    return clean, report


def clean_datasets(data_dir: str | Path = "data") -> dict:
    root = Path(data_dir) / "processed"
    prices, price_report = clean_prices(pd.read_parquet(root / "prices.parquet"))
    fundamentals, fundamental_report = clean_fundamentals(pd.read_parquet(root / "fundamentals.parquet"))
    prices.to_parquet(root / "prices_clean.parquet", index=False)
    fundamentals.to_parquet(root / "fundamentals_clean.parquet", index=False)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "prices": price_report, "fundamentals": fundamental_report,
        "policy": {
            "prices": "fail rather than silently drop or impute invalid OHLCV rows",
            "fundamentals": "retain unresolved nulls with flags; derived values carry provenance",
        },
    }
    (root / "data_quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    report = clean_datasets(args.data_dir)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
