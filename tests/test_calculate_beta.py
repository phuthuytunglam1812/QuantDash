import numpy as np
import pandas as pd
import pytest

from src.calculate_beta import add_rolling_betas, latest_beta_table


def aligned_frame(n=300, multiplier=1.5, symbol="TEST"):
    market = np.linspace(-0.02, 0.025, n) + np.sin(np.arange(n)) * 0.002
    return pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=n),
        "symbol": symbol,
        "simple_return": multiplier * market,
        "benchmark_simple_return": market,
    })


def test_beta_requires_entire_named_window():
    result = add_rolling_betas(aligned_frame(130), windows=(60, 126, 252))
    assert result.beta_60.iloc[:59].isna().all()
    assert result.beta_60.iloc[59] == pytest.approx(1.5)
    assert result.beta_126.iloc[:125].isna().all()
    assert result.beta_126.iloc[125] == pytest.approx(1.5)
    assert result.beta_252.isna().all()
    assert result.beta_252_n_obs.iloc[-1] == 130


def test_beta_does_not_fill_missing_pair_inside_window():
    frame = aligned_frame(65)
    frame.loc[30, "simple_return"] = np.nan
    result = add_rolling_betas(frame, windows=(60,))
    assert result.beta_60.isna().all()
    assert result.beta_60_n_obs.iloc[-1] == 59


def test_zero_market_variance_produces_nan_not_zero_or_infinity():
    frame = aligned_frame(60)
    frame["benchmark_simple_return"] = 0.01
    result = add_rolling_betas(frame, windows=(60,))
    assert pd.isna(result.beta_60.iloc[-1])
    assert not np.isinf(result.beta_60).any()


def test_beta_resets_per_symbol_and_latest_table_is_one_row_each():
    frame = pd.concat([
        aligned_frame(70, 1.5, "A"),
        aligned_frame(70, 0.5, "B"),
    ], ignore_index=True)
    rolling = add_rolling_betas(frame, windows=(60,))
    latest = latest_beta_table(rolling, windows=(60,))
    assert latest.symbol.tolist() == ["A", "B"]
    assert latest.set_index("symbol").loc["A", "beta_60"] == pytest.approx(1.5)
    assert latest.set_index("symbol").loc["B", "beta_60"] == pytest.approx(0.5)
    assert rolling.groupby("symbol").head(59).beta_60.isna().all()
