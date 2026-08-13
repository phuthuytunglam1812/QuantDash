"""Create scoring-safe feature copies while preserving raw master values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


WINSOR_FEATURES = [
    "beta_252", "momentum_21d", "momentum_63d", "momentum_126d",
    "volatility_20d_annualized", "revenue_growth_yoy", "profit_margin", "pe_ratio",
]


def parse_number(value) -> float | None:
    if value in (None, "", "None", "-", "N/A"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def provider_valuation_table(raw_dir: str | Path, symbols: list[str]) -> pd.DataFrame:
    rows = []
    root = Path(raw_dir)
    for symbol in symbols:
        path = root / f"{symbol}_overview.json"
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        raw_pe = parse_number(payload.get("PERatio"))
        provider_eps = parse_number(payload.get("EPS"))
        meaningful = raw_pe is not None and raw_pe > 0 and provider_eps is not None and provider_eps > 0
        if not path.exists():
            reason = "provider overview missing"
        elif provider_eps is None:
            reason = "provider EPS missing"
        elif provider_eps <= 0:
            reason = "provider EPS nonpositive"
        elif raw_pe is None:
            reason = "provider P/E missing"
        elif raw_pe <= 0:
            reason = "provider P/E nonpositive"
        else:
            reason = ""
        rows.append({
            "symbol": symbol, "pe_ratio_raw": raw_pe, "provider_eps_ttm": provider_eps,
            "pe_ratio": raw_pe if meaningful else None, "pe_is_meaningful": meaningful,
            "pe_exclusion_reason": reason, "pe_source": "Alpha Vantage OVERVIEW.PERatio",
        })
    return pd.DataFrame(rows)


def transform_features(
    master: pd.DataFrame, valuation: pd.DataFrame,
    lower_quantile: float = 0.05, upper_quantile: float = 0.95,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 <= lower_quantile < upper_quantile <= 1:
        raise ValueError("winsor quantiles must satisfy 0 <= lower < upper <= 1")
    if master["symbol"].duplicated().any() or valuation["symbol"].duplicated().any():
        raise ValueError("transformation inputs require unique symbols")
    result = master.merge(valuation, on="symbol", how="left", validate="one_to_one")
    stock_mask = ~result["is_benchmark"]
    bounds = []
    for feature in WINSOR_FEATURES:
        values = pd.to_numeric(result.loc[stock_mask, feature], errors="coerce")
        available = values.dropna()
        lower = available.quantile(lower_quantile) if not available.empty else None
        upper = available.quantile(upper_quantile) if not available.empty else None
        transformed = pd.to_numeric(result[feature], errors="coerce")
        if lower is not None and upper is not None:
            result[f"{feature}_winsorized"] = transformed.clip(lower=lower, upper=upper)
            result[f"{feature}_outlier_flag"] = stock_mask & transformed.notna() & (
                transformed.lt(lower) | transformed.gt(upper)
            )
        else:
            result[f"{feature}_winsorized"] = transformed
            result[f"{feature}_outlier_flag"] = False
        result.loc[~stock_mask, [f"{feature}_winsorized", f"{feature}_outlier_flag"]] = [None, False]
        bounds.append({
            "feature": feature, "lower_quantile": lower_quantile, "upper_quantile": upper_quantile,
            "lower_bound": lower, "upper_bound": upper, "available_stock_values": len(available),
            "lower_capped_count": int((values < lower).sum()) if lower is not None else 0,
            "upper_capped_count": int((values > upper).sum()) if upper is not None else 0,
        })
    return result, pd.DataFrame(bounds)


def build_transformed_features(data_dir: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    root = Path(data_dir)
    processed = root / "processed"
    master = pd.read_parquet(processed / "master_features.parquet")
    stocks = master.loc[~master.is_benchmark, "symbol"].tolist()
    valuation = provider_valuation_table(root / "raw" / "alpha_vantage_overview", stocks)
    transformed, bounds = transform_features(master, valuation)
    transformed.to_parquet(processed / "master_features_transformed.parquet", index=False)
    transformed.to_csv(processed / "master_features_transformed.csv", index=False)
    bounds.to_csv(processed / "winsorization_bounds.csv", index=False)
    meaningful_mask = transformed.loc[~transformed.is_benchmark, "pe_is_meaningful"].eq(True)
    report = {
        "lower_quantile": 0.05, "upper_quantile": 0.95,
        "raw_columns_preserved": True, "stocks": len(stocks),
        "pe_meaningful": int(meaningful_mask.sum()),
        "pe_not_meaningful": int((~meaningful_mask).sum()),
        "winsorized_features": WINSOR_FEATURES,
        "missing_fill": "none", "ticker_removal": "none",
    }
    (processed / "transformation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return transformed, bounds, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    _, bounds, report = build_transformed_features(args.data_dir)
    print(json.dumps(report, indent=2))
    print(bounds.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
