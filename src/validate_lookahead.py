"""Audit current QuantDash snapshots for obvious future-information leakage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def future_date_violations(
    frame: pd.DataFrame, as_of: object, date_columns: list[str]
) -> dict[str, int]:
    """Count populated source dates later than the decision timestamp."""
    cutoff = pd.Timestamp(as_of).normalize()
    violations: dict[str, int] = {}
    for column in date_columns:
        if column not in frame:
            continue
        dates = pd.to_datetime(frame[column], errors="coerce").dt.normalize()
        violations[column] = int(dates.gt(cutoff).sum())
    return violations


def build_lookahead_audit(data_dir: str | Path = "data") -> dict:
    """Audit the current latest-date snapshot and write reproducible evidence."""
    processed = Path(data_dir) / "processed"
    prices = pd.read_parquet(processed / "price_features.parquet")
    fundamentals = pd.read_parquet(processed / "fundamentals_clean.parquet")
    master = pd.read_parquet(processed / "master_features.parquet")

    as_of = pd.to_datetime(prices["date"], errors="raise").max().normalize()
    filed_columns = [name for name in fundamentals if name.endswith("_filed")]
    period_columns = [name for name in fundamentals if name.endswith("_period_end")]
    checks = {
        "technical_dates_after_as_of": future_date_violations(prices, as_of, ["date"]),
        "master_dates_after_as_of": future_date_violations(master, as_of, ["date"]),
        "fundamental_filing_dates_after_as_of": future_date_violations(
            fundamentals, as_of, filed_columns
        ),
        "fundamental_period_ends_after_as_of": future_date_violations(
            fundamentals, as_of, period_columns
        ),
    }
    passed = all(count == 0 for group in checks.values() for count in group.values())
    report = {
        "task": "W3-01 look-ahead bias validation",
        "as_of": as_of.strftime("%Y-%m-%d"),
        "passed": passed,
        "checks": checks,
        "technical_feature_policy": (
            "Returns, SMA, EMA, RSI, volatility, drawdown, momentum, and beta use "
            "the current or earlier trading observations only. Prefix-invariance is tested."
        ),
        "snapshot_scope": (
            "This validates the current latest-date screener snapshot. Historical point-in-time "
            "fundamental selection is handled by W3-02 before forward-return research."
        ),
    }
    output = processed / "lookahead_bias_audit.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not passed:
        raise ValueError(f"look-ahead audit failed; inspect {output}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    report = build_lookahead_audit(args.data_dir)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
