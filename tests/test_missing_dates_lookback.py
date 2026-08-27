import numpy as np
import pandas as pd
import pytest

from src.align_returns import align_returns
from src.calculate_beta import add_rolling_betas
from src.dashboard import prepare_benchmark_comparison, prepare_deep_dive
from src.features import (
    add_momentum,
    add_moving_averages,
    add_returns,
    add_risk_features,
    add_rsi,
)


def test_calendar_gap_uses_adjacent_available_trading_observations_only():
    prices = pd.DataFrame(
        {
            "symbol": ["A", "A", "A"],
            "date": ["2026-01-02", "2026-01-05", "2026-01-08"],
            "close": [100.0, 110.0, 121.0],
        }
    )
    result = add_returns(prices)
    assert result.date.tolist() == list(pd.to_datetime(prices.date))
    assert result.simple_return.iloc[1:].tolist() == pytest.approx([0.1, 0.1])


def test_missing_price_breaks_return_chain_without_zero_or_forward_fill():
    prices = pd.DataFrame(
        {
            "symbol": ["A"] * 4,
            "date": pd.bdate_range("2026-01-02", periods=4),
            "close": [100.0, np.nan, 110.0, 121.0],
        }
    )
    result = add_returns(prices)
    assert result.simple_return.iloc[:3].isna().all()
    assert result.simple_return.iloc[3] == pytest.approx(0.1)


def test_short_history_keeps_every_named_indicator_unavailable():
    prices = pd.DataFrame(
        {
            "symbol": ["A"] * 14,
            "date": pd.bdate_range("2026-01-02", periods=14),
            "close": np.linspace(100, 113, 14),
        }
    )
    result = add_returns(prices)
    result = add_moving_averages(result)
    result = add_rsi(result)
    result = add_risk_features(result)
    result = add_momentum(result)
    unavailable = [
        "sma_20",
        "sma_50",
        "ema_20",
        "rsi_14",
        "volatility_20d_annualized",
        "momentum_21d",
        "momentum_63d",
        "momentum_126d",
    ]
    assert result[unavailable].isna().all().all()


def test_beta_recovers_only_after_a_new_complete_window_after_missing_pair():
    n = 45
    market = np.sin(np.arange(n) / 5) / 100
    frame = pd.DataFrame(
        {
            "symbol": "A",
            "date": pd.bdate_range("2026-01-02", periods=n),
            "simple_return": market * 1.4,
            "benchmark_simple_return": market,
        }
    )
    frame.loc[20, "simple_return"] = np.nan
    result = add_rolling_betas(frame, windows=(20,))
    assert result.loc[20:39, "beta_20"].isna().all()
    assert result.loc[40, "beta_20"] == pytest.approx(1.4)


def test_alignment_drops_nonmatching_dates_and_never_creates_pairs():
    stocks = pd.DataFrame(
        {
            "date": ["2026-01-02", "2026-01-05", "2026-01-06"],
            "symbol": ["A"] * 3,
            "simple_return": [0.01, 0.02, 0.03],
            "log_return": [0.00995, 0.0198, 0.02956],
        }
    )
    benchmark = pd.DataFrame(
        {
            "date": ["2026-01-02", "2026-01-06"],
            "symbol": ["SPY"] * 2,
            "simple_return": [0.005, 0.007],
            "log_return": [0.00499, 0.00698],
        }
    )
    aligned, audit = align_returns(stocks, benchmark)
    assert aligned.date.tolist() == list(pd.to_datetime(["2026-01-02", "2026-01-06"]))
    assert audit.loc[0, "stock_dates_without_benchmark"] == 1


def test_benchmark_comparison_rejects_insufficient_common_history():
    history = pd.DataFrame(
        {
            "symbol": ["A", "A", "SPY", "SPY"],
            "date": ["2026-01-02", "2026-01-05", "2026-01-02", "2026-01-06"],
            "adjusted_close": [100.0, 101.0, 200.0, 202.0],
        }
    )
    with pytest.raises(ValueError, match="at least two common"):
        prepare_benchmark_comparison(history, "A", "3M")


def test_deep_dive_preserves_warmup_nulls_in_short_visible_window():
    dates = pd.bdate_range("2026-01-02", periods=10)
    history = pd.DataFrame(
        {
            "symbol": "A",
            "date": dates,
            "adjusted_close": np.linspace(100, 109, 10),
            "sma_20": np.nan,
            "sma_50": np.nan,
            "rsi_14": np.nan,
            "volatility_20d_annualized": np.nan,
        }
    )
    result = prepare_deep_dive(history, "A", "3M")
    assert len(result) == 10
    assert result[["sma_20", "sma_50", "rsi_14", "volatility_20d_annualized"]].isna().all().all()
