"""Testable data preparation helpers for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


TIMEFRAME_OFFSETS = {
    "3M": pd.DateOffset(months=3), "6M": pd.DateOffset(months=6),
    "1Y": pd.DateOffset(years=1), "2Y": pd.DateOffset(years=2),
}


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

    signals_path = processed / "signal_labels.parquet"
    if signals_path.exists():
        signals = pd.read_parquet(signals_path)
        signal_columns = [
            "symbol", "momentum_21d_raw", "momentum_63d_raw", "momentum_126d_raw",
            "revenue_growth_yoy_raw", "profit_margin_raw", "pe_ratio_raw", "beta_252_raw",
            "momentum_subscore", "quality_subscore", "valuation_subscore", "composite_score",
            "score_coverage", "momentum_label", "fundamentals_label", "valuation_label",
            "overall_label", "overall_display_label",
        ]
        signal_columns = [column for column in signal_columns if column in signals]
        latest = latest.merge(
            signals[signal_columns], on="symbol", how="left", validate="one_to_one"
        )
        for column in ["momentum_21d_raw", "momentum_63d_raw", "momentum_126d_raw",
                       "revenue_growth_yoy_raw", "profit_margin_raw"]:
            if column in latest:
                latest[f"{column}_pct"] = latest[column] * 100
    return latest.sort_values("symbol").reset_index(drop=True), history


def filter_screener(
    frame: pd.DataFrame, search: str = "", rsi_range: tuple[float, float] = (0, 100),
    max_volatility: float = 200, trend: str = "All", include_benchmark: bool = True,
    numeric_filters: dict[str, tuple[str, float]] | None = None,
    signal_labels: list[str] | None = None,
    sort_by: str | None = None,
    ascending: bool = False,
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
    if signal_labels is not None and "overall_label" in result:
        # An empty selection intentionally returns no matches. Missing labels never pass.
        result = result[result["overall_label"].notna() & result["overall_label"].isin(signal_labels)]
    for column, (operator, threshold) in (numeric_filters or {}).items():
        if column not in result:
            raise ValueError(f"unknown filter feature: {column}")
        values = pd.to_numeric(result[column], errors="coerce")
        if operator == ">=":
            keep = values.notna() & values.ge(threshold)
        elif operator == "<=":
            keep = values.notna() & values.le(threshold)
        else:
            raise ValueError(f"unsupported filter operator: {operator}")
        result = result[keep]
    if sort_by:
        if sort_by not in result:
            raise ValueError(f"unknown sort feature: {sort_by}")
        result = result.sort_values(sort_by, ascending=ascending, na_position="last", kind="stable")
    return result.reset_index(drop=True)


def prepare_signal_map(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Return W2-16 chart rows without inventing missing RSI or P/E values."""
    required = {"symbol", "rsi_14", "pe_ratio_raw", "composite_score", "overall_label"}
    if missing := required - set(frame.columns):
        raise ValueError(f"signal map input missing columns: {sorted(missing)}")
    chart = frame.copy()
    eligible = chart["rsi_14"].notna() & chart["pe_ratio_raw"].notna()
    excluded = int((~eligible).sum())
    chart = chart[eligible].copy()
    chart["bubble_score"] = pd.to_numeric(chart["composite_score"], errors="coerce").fillna(1).clip(lower=1)
    chart["overall_label"] = chart["overall_label"].fillna("Unavailable")
    return chart.reset_index(drop=True), excluded


def prepare_deep_dive(history: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    """Slice adjusted-price history and calculate drawdown from the selected-period peak."""
    if timeframe not in TIMEFRAME_OFFSETS:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    required = {"symbol", "date", "adjusted_close", "sma_20", "sma_50", "rsi_14",
                "volatility_20d_annualized"}
    if missing := required - set(history.columns):
        raise ValueError(f"deep-dive input missing columns: {sorted(missing)}")
    ticker = history[history["symbol"].eq(symbol)].copy()
    if ticker.empty:
        raise ValueError(f"unknown ticker: {symbol}")
    ticker["date"] = pd.to_datetime(ticker["date"], errors="raise")
    ticker = ticker.sort_values("date", kind="stable")
    end = ticker["date"].max()
    ticker = ticker[ticker["date"].ge(end - TIMEFRAME_OFFSETS[timeframe])].copy()
    ticker["timeframe_drawdown"] = ticker["adjusted_close"] / ticker["adjusted_close"].cummax() - 1
    ticker["volatility_20d_annualized_pct"] = ticker["volatility_20d_annualized"] * 100
    ticker["timeframe_drawdown_pct"] = ticker["timeframe_drawdown"] * 100
    return ticker.reset_index(drop=True)


def prepare_benchmark_comparison(
    history: pd.DataFrame, symbol: str, timeframe: str, benchmark: str = "SPY",
) -> tuple[pd.DataFrame, dict]:
    """Align adjusted closes on identical dates, then index both series to 100."""
    if symbol == benchmark:
        raise ValueError("comparison ticker must differ from benchmark")
    if timeframe not in TIMEFRAME_OFFSETS:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    required = {"symbol", "date", "adjusted_close"}
    if missing := required - set(history.columns):
        raise ValueError(f"benchmark comparison input missing columns: {sorted(missing)}")
    prices = history[list(required)].copy()
    prices["date"] = pd.to_datetime(prices["date"], errors="raise")
    latest = prices.loc[prices["symbol"].isin([symbol, benchmark]), "date"].max()
    window = prices[
        prices["symbol"].isin([symbol, benchmark])
        & prices["date"].ge(latest - TIMEFRAME_OFFSETS[timeframe])
    ].copy()
    stock = window[window["symbol"].eq(symbol)][["date", "adjusted_close"]].rename(
        columns={"adjusted_close": "stock_adjusted_close"}
    )
    market = window[window["symbol"].eq(benchmark)][["date", "adjusted_close"]].rename(
        columns={"adjusted_close": "benchmark_adjusted_close"}
    )
    if stock["date"].duplicated().any() or market["date"].duplicated().any():
        raise ValueError("benchmark comparison contains duplicate dates")
    aligned = stock.merge(market, on="date", how="inner", validate="one_to_one").sort_values("date")
    aligned = aligned[
        aligned["stock_adjusted_close"].notna() & aligned["benchmark_adjusted_close"].notna()
    ].reset_index(drop=True)
    if len(aligned) < 2:
        raise ValueError("benchmark comparison requires at least two common adjusted-close dates")
    if aligned[["stock_adjusted_close", "benchmark_adjusted_close"]].le(0).any().any():
        raise ValueError("benchmark comparison requires positive adjusted closes")
    aligned[f"{symbol}_indexed"] = aligned["stock_adjusted_close"] / aligned["stock_adjusted_close"].iloc[0] * 100
    aligned[f"{benchmark}_indexed"] = aligned["benchmark_adjusted_close"] / aligned["benchmark_adjusted_close"].iloc[0] * 100
    stock_return = aligned["stock_adjusted_close"].iloc[-1] / aligned["stock_adjusted_close"].iloc[0] - 1
    benchmark_return = aligned["benchmark_adjusted_close"].iloc[-1] / aligned["benchmark_adjusted_close"].iloc[0] - 1
    summary = {
        "symbol": symbol, "benchmark": benchmark, "timeframe": timeframe,
        "stock_return": float(stock_return), "benchmark_return": float(benchmark_return),
        "excess_return_pp": float((stock_return - benchmark_return) * 100),
        "common_observations": len(aligned),
        "first_common_date": aligned["date"].iloc[0], "last_common_date": aligned["date"].iloc[-1],
        "stock_dates_excluded": int(len(stock) - len(aligned)),
        "benchmark_dates_excluded": int(len(market) - len(aligned)),
        "price_basis": "adjusted_close (splits and dividends) for both series",
        "missing_policy": "inner join common dates; no fill or imputation",
    }
    return aligned, summary


def build_research_summary(detail: pd.Series, universe: pd.DataFrame) -> dict:
    """Build beginner-friendly context without turning missing data into evidence."""
    stocks = universe[~universe["symbol"].eq("SPY")].copy()

    def relative_context(
        column: str, label: str, higher_means: str, display_suffix: str = "",
    ) -> tuple[str, dict]:
        value = pd.to_numeric(pd.Series([detail.get(column)]), errors="coerce").iloc[0]
        peers = pd.to_numeric(stocks.get(column, pd.Series(dtype=float)), errors="coerce").dropna()
        if pd.isna(value):
            detail_context = {
                "label": label, "value": "N/A", "status": "Unavailable",
                "peer_position": "Peer position cannot be calculated.",
                "meaning": "Missing data is not treated as zero or favorable evidence.",
            }
            return f"{label}: unavailable; do not infer a zero or a favorable result.", detail_context
        if peers.empty:
            detail_context = {
                "label": label, "value": f"{value:.1f}{display_suffix}", "status": "Context unavailable",
                "peer_position": "No valid peer observations are available.", "meaning": higher_means,
            }
            return f"{label}: {value:.1f}; peer context unavailable.", detail_context
        percentile = float(peers.le(value).mean() * 100)
        band = "high" if percentile >= 67 else "low" if percentile <= 33 else "middle-range"
        detail_context = {
            "label": label, "value": f"{value:.1f}{display_suffix}", "status": band.title(),
            "peer_position": f"Higher than approximately {percentile:.0f}% of valid stocks in this 20-stock universe.",
            "meaning": higher_means,
        }
        return f"{label}: {value:.1f} ({band}; higher than about {percentile:.0f}% of this 20-stock universe). {higher_means}", detail_context

    rsi = pd.to_numeric(pd.Series([detail.get("rsi_14")]), errors="coerce").iloc[0]
    if pd.isna(rsi):
        rsi_context = "RSI 14: unavailable because there is insufficient usable price history."
        rsi_detail = {"label": "RSI 14", "value": "N/A", "status": "Unavailable", "peer_position": "No RSI position is inferred.", "meaning": "Insufficient usable price history."}
    elif rsi >= 70:
        rsi_context = f"RSI 14: {rsi:.1f}, above 70. Recent gains are strong, but this can indicate an overextended move."
        rsi_detail = {"label": "RSI 14", "value": f"{rsi:.1f}", "status": "Above 70", "peer_position": "Above the conventional upper reference zone.", "meaning": "Recent gains are strong, but the move may be overextended; this is not an automatic sell signal."}
    elif rsi <= 30:
        rsi_context = f"RSI 14: {rsi:.1f}, below 30. Selling pressure is strong; this is not automatically a buy signal."
        rsi_detail = {"label": "RSI 14", "value": f"{rsi:.1f}", "status": "Below 30", "peer_position": "Below the conventional lower reference zone.", "meaning": "Selling pressure is strong; this is not automatically a buy signal."}
    else:
        rsi_context = f"RSI 14: {rsi:.1f}, between 30 and 70; neither reference extreme is active."
        rsi_detail = {"label": "RSI 14", "value": f"{rsi:.1f}", "status": "30–70 range", "peer_position": "Neither conventional RSI reference extreme is active.", "meaning": "Momentum is not currently in an extreme reference zone."}

    valuation_text, valuation_detail = relative_context(
        "pe_ratio_raw", "P/E", "A higher P/E means investors pay more per dollar of earnings and may increase downside risk if growth slows."
    )
    profitability_text, profitability_detail = relative_context(
        "profit_margin_raw_pct", "Profit margin %", "A higher margin indicates more profit retained per dollar of revenue, but durability still needs investigation.", "%"
    )
    risk_text, risk_detail = relative_context(
        "volatility_pct", "20D annualized volatility %", "Higher volatility means a wider range of recent price outcomes, not necessarily a worse company.", "%"
    )
    contexts = {
        "valuation": valuation_text,
        "profitability": profitability_text,
        "risk": risk_text,
        "momentum": rsi_context,
    }
    context_details = {
        "valuation": valuation_detail, "profitability": profitability_detail,
        "momentum": rsi_detail, "risk": risk_detail,
    }

    strengths, cautions, gaps = [], [], []
    label_map = {
        "Momentum": detail.get("momentum_label"),
        "Fundamentals": detail.get("fundamentals_label"),
        "Valuation": detail.get("valuation_label"),
    }
    for name, label in label_map.items():
        if label in {"Strong", "Positive"}:
            strengths.append(f"{name}: {label}")
        elif label in {"Weak", "Very Weak"}:
            cautions.append(f"{name}: {label}")
        elif pd.isna(label) or label == "Unavailable":
            gaps.append(f"{name} score unavailable")
    beta = pd.to_numeric(pd.Series([detail.get("beta_252_raw")]), errors="coerce").iloc[0]
    if pd.isna(beta):
        gaps.append("252-day beta unavailable")
    elif beta > 1.5:
        cautions.append(f"Beta {beta:.2f}: historically more market-sensitive than SPY")
    coverage = pd.to_numeric(pd.Series([detail.get("score_coverage")]), errors="coerce").iloc[0]
    if pd.isna(coverage):
        gaps.append("Composite-score coverage unavailable")
    elif coverage < 1:
        gaps.append(f"Composite score uses only {coverage:.0%} of intended component weight")
    return {
        "contexts": contexts,
        "context_details": context_details,
        "strengths": strengths,
        "cautions": cautions,
        "data_gaps": gaps,
        "overall": detail.get("overall_display_label", "Unavailable"),
        "conclusion_prompt": "Form a view only after checking business context, fundamentals, valuation, price/risk, and data gaps.",
    }
