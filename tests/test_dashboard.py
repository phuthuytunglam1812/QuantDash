import pandas as pd

from src.dashboard import filter_screener, signal_label


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
