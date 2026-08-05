import numpy as np
import pandas as pd

from src.features import add_moving_averages, add_returns, add_risk_features, add_rsi


def make_prices(symbol: str, close) -> pd.DataFrame:
    values = list(close)
    return pd.DataFrame({
        "symbol": symbol,
        "date": pd.date_range("2026-01-01", periods=len(values)),
        "close": values,
    })


def full_feature_chain(prices: pd.DataFrame) -> pd.DataFrame:
    return add_risk_features(add_rsi(add_moving_averages(add_returns(prices))))


def test_constant_price_indicator_invariants():
    result = full_feature_chain(make_prices("FLAT", [100.0] * 60))
    assert result.simple_return.dropna().eq(0).all()
    assert result.log_return.dropna().eq(0).all()
    assert result.sma_20.dropna().eq(100).all()
    assert result.sma_50.dropna().eq(100).all()
    assert result.ema_20.dropna().eq(100).all()
    assert result.rsi_14.dropna().eq(50).all()
    assert result.volatility_20d_annualized.dropna().eq(0).all()
    assert result.drawdown.eq(0).all()
    assert result.max_drawdown_to_date.eq(0).all()


def test_indicator_pipeline_does_not_mutate_input():
    source = make_prices("A", np.linspace(100, 120, 60))
    original = source.copy(deep=True)
    full_feature_chain(source)
    pd.testing.assert_frame_equal(source, original)


def test_changing_one_symbol_cannot_change_another_symbols_features():
    a = make_prices("A", np.linspace(100, 120, 60))
    b = make_prices("B", np.linspace(50, 80, 60))
    baseline = full_feature_chain(pd.concat([a, b], ignore_index=True))
    altered_b = b.copy()
    altered_b["close"] *= 10
    changed = full_feature_chain(pd.concat([a, altered_b], ignore_index=True))
    columns = ["simple_return", "log_return", "sma_20", "sma_50", "ema_20", "rsi_14",
               "volatility_20d_annualized", "drawdown", "max_drawdown_to_date"]
    pd.testing.assert_frame_equal(
        baseline.loc[baseline.symbol.eq("A"), columns].reset_index(drop=True),
        changed.loc[changed.symbol.eq("A"), columns].reset_index(drop=True),
    )


def test_feature_bounds_and_warmups_for_multiple_symbols():
    prices = pd.concat([
        make_prices("A", 100 + np.sin(np.arange(60)) * 5),
        make_prices("B", 80 + np.cos(np.arange(60)) * 4),
    ], ignore_index=True)
    result = full_feature_chain(prices)
    assert result.rsi_14.dropna().between(0, 100).all()
    assert result.volatility_20d_annualized.dropna().ge(0).all()
    assert result.drawdown.between(-1, 0).all()
    assert result.max_drawdown_to_date.between(-1, 0).all()
    nulls = result.groupby("symbol").agg({
        "simple_return": lambda s: int(s.isna().sum()),
        "sma_20": lambda s: int(s.isna().sum()),
        "sma_50": lambda s: int(s.isna().sum()),
        "ema_20": lambda s: int(s.isna().sum()),
        "rsi_14": lambda s: int(s.isna().sum()),
        "volatility_20d_annualized": lambda s: int(s.isna().sum()),
    })
    assert nulls.eq({
        "simple_return": 1, "sma_20": 19, "sma_50": 49,
        "ema_20": 19, "rsi_14": 14, "volatility_20d_annualized": 20,
    }).all().all()


def test_drawdown_recovers_at_new_high_but_max_drawdown_is_retained():
    result = add_risk_features(add_returns(make_prices("A", [100, 120, 90, 80, 121])))
    assert result.drawdown.iloc[-1] == 0
    assert result.max_drawdown_to_date.iloc[-1] == 80 / 120 - 1
    assert result.max_drawdown_to_date.diff().dropna().le(0).all()
