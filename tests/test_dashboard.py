import pandas as pd
import pytest

from src.dashboard import (
    filter_screener, prepare_benchmark_comparison, prepare_deep_dive,
    prepare_signal_map, signal_label,
)


def row(**changes):
    values = {"close": 110, "sma_50": 100, "rsi_14": 60}
    values.update(changes)
    return pd.Series(values)


def test_signal_labels_cover_main_states():
    assert signal_label(row()) == "Bullish"
    assert signal_label(row(rsi_14=75)) == "Overbought"
    assert signal_label(row(rsi_14=25)) == "Oversold"
    assert signal_label(row(close=90, rsi_14=40)) == "Bearish"
    assert signal_label(row(close=90, rsi_14=60)) == "Neutral"


def test_screener_filters_search_risk_trend_and_benchmark():
    frame = pd.DataFrame({
        "symbol": ["AAPL", "SPY", "TSLA"],
        "company_name": ["Apple Inc.", "SPDR ETF", "Tesla Inc."],
        "rsi_14": [60, 50, 80], "volatility_pct": [20, 15, 90],
        "trend_above_sma50": [True, True, False],
    })
    result = filter_screener(frame, search="apple", rsi_range=(40, 70), max_volatility=50,
                             trend="Above SMA 50", include_benchmark=False)
    assert result.symbol.tolist() == ["AAPL"]


def test_combined_filters_use_and_and_missing_values_do_not_pass():
    frame = pd.DataFrame({
        "symbol": ["A", "B", "C"], "company_name": ["A", "B", "C"],
        "rsi_14": [50, 50, 50], "volatility_pct": [20, 20, 20],
        "trend_above_sma50": [True, True, True],
        "momentum_63d_raw_pct": [12, 15, 20], "pe_ratio_raw": [25, float("nan"), 45],
        "overall_label": ["Positive", "Positive", "Strong"], "composite_score": [70, 80, 90],
    })
    result = filter_screener(
        frame, numeric_filters={"momentum_63d_raw_pct": (">=", 10), "pe_ratio_raw": ("<=", 35)},
        signal_labels=["Strong", "Positive"], sort_by="composite_score",
    )
    assert result.symbol.tolist() == ["A"]


def test_empty_signal_selection_returns_no_matches():
    frame = pd.DataFrame({
        "symbol": ["A"], "company_name": ["A"], "rsi_14": [50],
        "volatility_pct": [20], "trend_above_sma50": [True], "overall_label": ["Positive"],
    })
    assert filter_screener(frame, signal_labels=[]).empty


def test_signal_map_uses_filtered_rows_and_excludes_missing_axes():
    filtered = pd.DataFrame({
        "symbol": ["A", "B", "C"], "company_name": ["A", "B", "C"],
        "rsi_14": [55, 60, float("nan")], "pe_ratio_raw": [20, float("nan"), 30],
        "composite_score": [70, 80, float("nan")],
        "overall_label": ["Positive", "Strong", None],
    })
    chart, excluded = prepare_signal_map(filtered)
    assert chart.symbol.tolist() == ["A"]
    assert excluded == 2
    assert chart.loc[0, "bubble_score"] == 70


def test_deep_dive_uses_calendar_timeframe_and_adjusted_close_drawdown():
    dates = pd.date_range("2024-01-01", "2026-01-01", freq="MS")
    history = pd.DataFrame({
        "symbol": "A", "date": dates, "adjusted_close": range(100, 100 + len(dates)),
        "sma_20": 100.0, "sma_50": 100.0, "rsi_14": 50.0,
        "volatility_20d_annualized": 0.2,
    })
    result = prepare_deep_dive(history, "A", "3M")
    assert result.date.min() >= result.date.max() - pd.DateOffset(months=3)
    assert result.iloc[0].timeframe_drawdown == 0
    assert result.iloc[-1].volatility_20d_annualized_pct == 20


def test_deep_dive_rejects_unknown_timeframe():
    with pytest.raises(ValueError, match="unsupported timeframe"):
        prepare_deep_dive(pd.DataFrame(), "A", "5Y")


def test_benchmark_comparison_inner_joins_dates_and_normalizes_adjusted_close():
    history = pd.DataFrame({
        "symbol": ["A", "A", "A", "SPY", "SPY", "SPY"],
        "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03",
                                "2026-01-01", "2026-01-03", "2026-01-04"]),
        "adjusted_close": [100.0, 999.0, 120.0, 200.0, 220.0, 999.0],
    })
    aligned, summary = prepare_benchmark_comparison(history, "A", "3M")
    assert aligned.date.dt.strftime("%Y-%m-%d").tolist() == ["2026-01-01", "2026-01-03"]
    assert aligned["A_indexed"].tolist() == [100.0, 120.0]
    assert aligned["SPY_indexed"].tolist() == pytest.approx([100.0, 110.0])
    assert summary["stock_return"] == pytest.approx(0.2)
    assert summary["benchmark_return"] == pytest.approx(0.1)
    assert summary["excess_return_pp"] == pytest.approx(10.0)
    assert summary["stock_dates_excluded"] == 1
    assert summary["benchmark_dates_excluded"] == 1


def test_benchmark_comparison_does_not_fill_missing_adjusted_close():
    history = pd.DataFrame({
        "symbol": ["A", "A", "A", "SPY", "SPY", "SPY"],
        "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"] * 2),
        "adjusted_close": [100.0, float("nan"), 110.0, 200.0, 210.0, 220.0],
    })
    aligned, summary = prepare_benchmark_comparison(history, "A", "3M")
    assert aligned.date.dt.strftime("%Y-%m-%d").tolist() == ["2026-01-01", "2026-01-03"]
    assert summary["common_observations"] == 2
