"""Export the tested Python dashboard model for the React client."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.dashboard import build_screener


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "frontend" / "public" / "data" / "dashboard.json"


def clean(value):
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def export_dashboard_data(output: Path = OUTPUT) -> Path:
    screener, history = build_screener(ROOT / "data")
    stock_columns = [
        "symbol", "company_name", "sic_description", "date", "adjusted_close", "daily_return_pct",
        "rsi_14", "volatility_pct", "max_drawdown_pct", "momentum_21d_raw_pct", "momentum_63d_raw_pct",
        "momentum_126d_raw_pct", "profit_margin_raw_pct",
        "revenue_growth_yoy_raw_pct", "pe_ratio_raw", "beta_252_raw", "momentum_subscore",
        "quality_subscore", "valuation_subscore", "composite_score", "score_coverage",
        "momentum_label", "fundamentals_label", "valuation_label", "overall_label",
        "overall_display_label", "signal", "trend_above_sma50",
    ]
    stock_columns = [column for column in stock_columns if column in screener]
    stocks = [
        {column: clean(value) for column, value in row.items()}
        for row in screener[stock_columns].to_dict(orient="records")
    ]

    history_columns = [
        "symbol", "date", "adjusted_close", "sma_20", "sma_50", "rsi_14",
        "volatility_20d_annualized", "drawdown",
    ]
    history_rows = history[history_columns].sort_values(["symbol", "date"])
    histories: dict[str, list[dict]] = {}
    for symbol, rows in history_rows.groupby("symbol", sort=True):
        histories[symbol] = [
            {column: clean(value) for column, value in row.items() if column != "symbol"}
            for row in rows.to_dict(orient="records")
        ]

    payload = {
        "meta": {
            "generated_from": "src.dashboard.build_screener",
            "latest_market_date": clean(pd.to_datetime(screener["date"]).max()),
            "price_basis": "adjusted_close",
            "benchmark": "SPY",
            "missing_policy": "No imputation; filtered metrics require a real value; comparisons use common dates.",
        },
        "stocks": stocks,
        "history": histories,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return output


if __name__ == "__main__":
    path = export_dashboard_data()
    print(f"Exported React data to {path.relative_to(ROOT)}")
