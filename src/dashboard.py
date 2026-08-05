"""Testable data preparation helpers for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def signal_label(row: pd.Series) -> str:
    if pd.isna(row.get("rsi_14")) or pd.isna(row.get("sma_50")):
        return "Insufficient history"
    if row["rsi_14"] >= 70:
        return "Overbought"
    if row["rsi_14"] <= 30:
        return "Oversold"
    if row["close"] > row["sma_50"] and row["rsi_14"] >= 50:
        return "Bullish"
    if row["close"] < row["sma_50"] and row["rsi_14"] < 50:
        return "Bearish"
    return "Neutral"


def build_screener(data_dir: str | Path = "data") -> tuple[pd.DataFrame, pd.DataFrame]:
    processed = Path(data_dir) / "processed"
    history = pd.read_parquet(processed / "price_features.parquet")
    fundamentals = pd.read_parquet(processed / "fundamentals_clean.parquet")
    history = history.sort_values(["symbol", "date"], kind="stable")
    latest = history.groupby("symbol", sort=False).tail(1).copy()
    identity = fundamentals[[
        "symbol", "company_name", "sic_description", "revenue", "net_income", "assets", "eps_diluted"
    ]]
    latest = latest.merge(identity, on="symbol", how="left", validate="one_to_one")
    latest.loc[latest.symbol.eq("SPY"), ["company_name", "sic_description"]] = [
        "SPDR S&P 500 ETF Trust", "Benchmark ETF"
    ]
    latest["signal"] = latest.apply(signal_label, axis=1)
    latest["trend_above_sma50"] = latest["close"] > latest["sma_50"]
    latest["daily_return_pct"] = latest["simple_return"] * 100
    latest["volatility_pct"] = latest["volatility_20d_annualized"] * 100
    latest["drawdown_pct"] = latest["drawdown"] * 100
    latest["max_drawdown_pct"] = latest["max_drawdown_to_date"] * 100
    for column in ["revenue", "net_income", "assets"]:
        latest[f"{column}_billions"] = latest[column] / 1_000_000_000
    return latest.sort_values("symbol").reset_index(drop=True), history


def filter_screener(
    frame: pd.DataFrame, search: str = "", rsi_range: tuple[float, float] = (0, 100),
    max_volatility: float = 200, trend: str = "All", include_benchmark: bool = True,
) -> pd.DataFrame:
    result = frame.copy()
    if not include_benchmark:
        result = result[~result.symbol.eq("SPY")]
    term = search.strip().casefold()
    if term:
        names = result["company_name"].fillna("").str.casefold()
        result = result[result.symbol.str.casefold().str.contains(term, regex=False) | names.str.contains(term, regex=False)]
    result = result[result.rsi_14.between(*rsi_range) & result.volatility_pct.le(max_volatility)]
    if trend == "Above SMA 50":
        result = result[result.trend_above_sma50]
    elif trend == "Below SMA 50":
        result = result[~result.trend_above_sma50]
    return result.reset_index(drop=True)
