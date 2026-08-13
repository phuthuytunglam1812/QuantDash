"""Compare strict self-calculated betas with Alpha Vantage provider beta."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.clients import MarketDataClient
from src.config import TICKERS


WINDOWS = (60, 126, 252)


def parse_provider_beta(payload: dict) -> float | None:
    raw = payload.get("Beta")
    if raw in (None, "", "None", "-"):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def collect_provider_betas(
    raw_dir: str | Path,
    symbols: list[str] | None = None,
    overwrite: bool = False,
    pause_seconds: float = 1.1,
    client: MarketDataClient | None = None,
) -> pd.DataFrame:
    """Fetch/cache provider overviews without inventing missing beta values."""
    target = Path(raw_dir)
    target.mkdir(parents=True, exist_ok=True)
    market = client or MarketDataClient()
    rows = []
    for symbol in symbols or TICKERS:
        path = target / f"{symbol}_overview.json"
        status = "cached"
        error = ""
        payload = {}
        try:
            if path.exists() and not overwrite:
                payload = json.loads(path.read_text(encoding="utf-8"))
            else:
                payload = market.alpha_vantage_overview(symbol)
                path.write_text(json.dumps(payload), encoding="utf-8")
                status = "downloaded"
                time.sleep(max(0.0, pause_seconds))
        except Exception as exc:
            status = "error"
            error = f"{type(exc).__name__}: {exc}"
        beta = parse_provider_beta(payload)
        rows.append({
            "symbol": symbol,
            "provider_beta": beta,
            "provider": "Alpha Vantage OVERVIEW",
            "provider_status": status,
            "provider_error": error,
            "provider_beta_available": beta is not None,
        })
    return pd.DataFrame(rows)


def compare_betas(calculated: pd.DataFrame, provider: pd.DataFrame) -> pd.DataFrame:
    required = {"symbol", "date", *(f"beta_{window}" for window in WINDOWS)}
    if missing := required - set(calculated.columns):
        raise ValueError(f"calculated beta table missing columns: {sorted(missing)}")
    if calculated["symbol"].duplicated().any() or provider["symbol"].duplicated().any():
        raise ValueError("beta comparison inputs require one row per symbol")
    comparison = calculated.merge(provider, on="symbol", how="left", validate="one_to_one")
    for window in WINDOWS:
        comparison[f"difference_beta_{window}"] = comparison[f"beta_{window}"] - comparison["provider_beta"]
        comparison[f"absolute_difference_beta_{window}"] = comparison[f"difference_beta_{window}"].abs()
    comparison["methodology_comparable"] = False
    comparison["comparison_note"] = (
        "Provider lookback/methodology is not guaranteed to match the explicit QuantDash window."
    )
    return comparison


def build_beta_comparison(
    data_dir: str | Path = "data", overwrite: bool = False,
    client: MarketDataClient | None = None,
) -> tuple[pd.DataFrame, dict]:
    root = Path(data_dir)
    processed = root / "processed"
    calculated = pd.read_csv(processed / "latest_beta.csv", parse_dates=["date"])
    provider = collect_provider_betas(
        root / "raw" / "alpha_vantage_overview",
        symbols=calculated["symbol"].tolist(), overwrite=overwrite, client=client,
    )
    comparison = compare_betas(calculated, provider)
    comparison.to_csv(processed / "beta_comparison.csv", index=False)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "symbols": len(comparison),
        "provider": "Alpha Vantage OVERVIEW Beta",
        "provider_beta_available": int(comparison["provider_beta"].notna().sum()),
        "provider_errors": int(comparison["provider_status"].eq("error").sum()),
        "calculated_windows": list(WINDOWS),
        "methodology_comparable": False,
        "warning": "Differences are descriptive only because provider lookback and methodology may differ.",
        "missing_provider_beta_policy": "retain NaN; never fill",
    }
    (processed / "beta_comparison_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return comparison, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    comparison, report = build_beta_comparison(args.data_dir, args.overwrite)
    print(json.dumps(report, indent=2))
    columns = ["symbol", "beta_60", "beta_126", "beta_252", "provider_beta", "provider_status"]
    print(comparison[columns].to_string(index=False))
    return 0 if report["provider_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
