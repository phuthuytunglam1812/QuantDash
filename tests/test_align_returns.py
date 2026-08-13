import numpy as np
import pandas as pd
import pytest

from src.align_returns import align_returns, normalize_trading_date


def test_normalize_mixed_date_formats_to_same_key():
    values = pd.Series(["2026-08-03", "2026-08-03 00:00:00", "2026-08-03 20:00:00 UTC"])
    result = normalize_trading_date(values)
    assert result.nunique() == 1
    assert result.iloc[0] == pd.Timestamp("2026-08-03")
    assert result.dt.tz is None


def test_alignment_is_exact_inner_join_without_fill():
    stocks = pd.DataFrame({
        "date": ["2026-08-01", "2026-08-02", "2026-08-03"],
        "symbol": ["AAPL"] * 3,
        "simple_return": [0.01, 0.02, 0.03],
        "log_return": [0.00995, 0.0198, 0.02956],
    })
    benchmark = pd.DataFrame({
        "date": ["2026-08-01", "2026-08-03"], "symbol": ["SPY", "SPY"],
        "simple_return": [0.001, np.nan], "log_return": [0.0009995, np.nan],
    })
    aligned, audit = align_returns(stocks, benchmark)
    assert aligned.date.tolist() == [pd.Timestamp("2026-08-01")]
    assert aligned.benchmark_simple_return.tolist() == [0.001]
    assert audit.iloc[0]["aligned_rows"] == 1
    assert audit.iloc[0]["fill_method"] == "none"


def test_alignment_handles_timezone_representation_but_not_nearest_day():
    stocks = pd.DataFrame({
        "date": ["2026-08-03 00:00:00"], "symbol": ["AAPL"],
        "simple_return": [0.01], "log_return": [0.00995],
    })
    benchmark = pd.DataFrame({
        "date": ["2026-08-03 20:00:00 UTC"], "symbol": ["SPY"],
        "simple_return": [0.005], "log_return": [0.00498],
    })
    aligned, _ = align_returns(stocks, benchmark)
    assert len(aligned) == 1

    benchmark["date"] = "2026-08-04 00:00:00 UTC"
    aligned, _ = align_returns(stocks, benchmark)
    assert aligned.empty


def test_alignment_rejects_duplicate_keys():
    stocks = pd.DataFrame({
        "date": ["2026-08-03", "2026-08-03"], "symbol": ["AAPL", "AAPL"],
        "simple_return": [0.01, 0.01], "log_return": [0.00995, 0.00995],
    })
    benchmark = pd.DataFrame({
        "date": ["2026-08-03"], "symbol": ["SPY"],
        "simple_return": [0.005], "log_return": [0.00498],
    })
    with pytest.raises(ValueError, match="duplicate"):
        align_returns(stocks, benchmark)
