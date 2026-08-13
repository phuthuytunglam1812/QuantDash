import numpy as np
import pandas as pd
import pytest

from src.features import _wilder_rsi, add_momentum, add_moving_averages, add_returns, add_risk_features, add_rsi


def test_returns_match_formulas_and_reset_per_symbol():
    prices = pd.DataFrame({
        "symbol": ["B", "A", "A", "B"],
        "date": ["2026-01-02", "2026-01-02", "2026-01-03", "2026-01-03"],
        "close": [20.0, 10.0, 11.0, 18.0],
    })
    result = add_returns(prices)
    first = result.groupby("symbol").head(1)
    assert first["simple_return"].isna().all()
    assert first["log_return"].isna().all()
    a_second = result[result.symbol.eq("A")].iloc[1]
    b_second = result[result.symbol.eq("B")].iloc[1]
    assert a_second.simple_return == pytest.approx(0.1)
    assert a_second.log_return == pytest.approx(np.log(1.1))
    assert b_second.simple_return == pytest.approx(-0.1)


def test_log_returns_reject_nonpositive_close():
    prices = pd.DataFrame({"symbol": ["A"], "date": ["2026-01-02"], "close": [0]})
    with pytest.raises(ValueError, match="strictly positive"):
        add_returns(prices)


def test_moving_averages_use_full_windows_and_reset_per_symbol():
    dates = pd.date_range("2026-01-01", periods=55)
    prices = pd.concat([
        pd.DataFrame({"symbol": symbol, "date": dates, "close": np.arange(1, 56, dtype=float) + offset})
        for symbol, offset in [("A", 0), ("B", 100)]
    ], ignore_index=True)
    result = add_moving_averages(prices)
    for symbol, offset in [("A", 0), ("B", 100)]:
        group = result[result.symbol.eq(symbol)].reset_index(drop=True)
        assert group.loc[:18, "sma_20"].isna().all()
        assert group.loc[:18, "ema_20"].isna().all()
        assert group.loc[:48, "sma_50"].isna().all()
        assert group.loc[19, "sma_20"] == pytest.approx(10.5 + offset)
        assert group.loc[49, "sma_50"] == pytest.approx(25.5 + offset)
        expected_ema = group.loc[:19, "close"].ewm(span=20, adjust=False).mean().iloc[-1]
        assert group.loc[19, "ema_20"] == pytest.approx(expected_ema)


def test_wilder_rsi_matches_reference_sequence():
    # Direct seed: average of the 10 positive and 4 negative changes below.
    close = pd.Series([
        54.8, 56.8, 57.85, 59.85, 60.57, 61.1, 62.17, 60.6,
        62.35, 62.15, 62.35, 61.45, 62.8, 61.37, 62.5,
    ])
    result = _wilder_rsi(close, 14)
    assert result.iloc[:14].isna().all()
    changes = close.diff().dropna()
    expected_gain = changes.clip(lower=0).mean()
    expected_loss = -changes.clip(upper=0).mean()
    expected = 100 - 100 / (1 + expected_gain / expected_loss)
    assert result.iloc[14] == pytest.approx(expected)
    assert result.iloc[14] == pytest.approx(74.21383647798743)


@pytest.mark.parametrize("values, expected", [
    (range(1, 17), 100.0),
    (range(17, 1, -1), 0.0),
    ([5.0] * 16, 50.0),
])
def test_rsi_handles_zero_loss_gain_and_flat_windows(values, expected):
    result = _wilder_rsi(pd.Series(values), 14)
    assert result.iloc[-1] == expected


def test_rsi_resets_at_symbol_boundary():
    dates = pd.date_range("2026-01-01", periods=16)
    prices = pd.concat([
        pd.DataFrame({"symbol": "UP", "date": dates, "close": range(1, 17)}),
        pd.DataFrame({"symbol": "DOWN", "date": dates, "close": range(17, 1, -1)}),
    ])
    result = add_rsi(prices)
    assert result.groupby("symbol").head(14)["rsi_14"].isna().all()
    assert result[result.symbol.eq("UP")].iloc[-1].rsi_14 == 100
    assert result[result.symbol.eq("DOWN")].iloc[-1].rsi_14 == 0


def test_risk_features_match_formulas_and_reset_per_symbol():
    dates = pd.date_range("2026-01-01", periods=25)
    a_close = pd.Series(100 * np.exp(np.arange(25) * 0.01))
    b_close = pd.Series([100, 110, 90, 80, 120] + list(np.linspace(121, 140, 20)))
    prices = pd.concat([
        pd.DataFrame({"symbol": "A", "date": dates, "close": a_close}),
        pd.DataFrame({"symbol": "B", "date": dates, "close": b_close}),
    ], ignore_index=True)
    result = add_risk_features(add_returns(prices))
    for symbol in ["A", "B"]:
        group = result[result.symbol.eq(symbol)].reset_index(drop=True)
        assert group.loc[:19, "volatility_20d_annualized"].isna().all()
        expected = group.log_return.iloc[1:21].std(ddof=1) * np.sqrt(252)
        assert group.loc[20, "volatility_20d_annualized"] == pytest.approx(expected)
        assert group.loc[0, "drawdown"] == 0
    b = result[result.symbol.eq("B")].reset_index(drop=True)
    assert b.loc[3, "drawdown"] == pytest.approx(80 / 110 - 1)
    assert b.loc[3, "max_drawdown_to_date"] == pytest.approx(80 / 110 - 1)
    assert b.loc[4, "drawdown"] == 0
    assert b.loc[4, "max_drawdown_to_date"] == pytest.approx(80 / 110 - 1)


def test_risk_features_reject_nonpositive_close():
    prices = pd.DataFrame({"symbol": ["A"], "date": ["2026-01-01"], "close": [0]})
    with pytest.raises(ValueError, match="strictly positive"):
        add_risk_features(prices)


def test_momentum_uses_exact_trading_observation_lags_and_full_warmup():
    dates = pd.bdate_range("2026-01-01", periods=130)
    prices = pd.concat([
        pd.DataFrame({"symbol": "A", "date": dates, "close": np.arange(1, 131, dtype=float)}),
        pd.DataFrame({"symbol": "B", "date": dates, "close": np.arange(101, 231, dtype=float)}),
    ], ignore_index=True)
    result = add_momentum(prices)
    for symbol, first_close in [("A", 1.0), ("B", 101.0)]:
        group = result[result.symbol.eq(symbol)].reset_index(drop=True)
        assert group.loc[:20, "momentum_21d"].isna().all()
        assert group.loc[:62, "momentum_63d"].isna().all()
        assert group.loc[:125, "momentum_126d"].isna().all()
        assert group.loc[21, "momentum_21d"] == pytest.approx(group.loc[21, "close"] / first_close - 1)
        assert group.loc[126, "momentum_126d"] == pytest.approx(group.loc[126, "close"] / first_close - 1)


def test_momentum_does_not_fill_missing_lag_price():
    prices = pd.DataFrame({
        "symbol": ["A"] * 23,
        "date": pd.bdate_range("2026-01-01", periods=23),
        "close": [100.0] + [np.nan] + list(np.linspace(102, 123, 21)),
    })
    result = add_momentum(prices, periods=(21,))
    assert pd.isna(result.loc[22, "momentum_21d"])
