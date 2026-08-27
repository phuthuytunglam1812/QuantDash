import numpy as np
import pandas as pd
import pandas.testing as pdt

from src.calculate_beta import add_rolling_betas
from src.features import (
    add_momentum,
    add_moving_averages,
    add_returns,
    add_risk_features,
    add_rsi,
)
from src.validate_lookahead import future_date_violations


def _technical_pipeline(frame: pd.DataFrame) -> pd.DataFrame:
    result = add_returns(frame)
    result = add_moving_averages(result)
    result = add_rsi(result)
    result = add_risk_features(result)
    return add_momentum(result)


def test_all_price_features_are_prefix_invariant_to_future_price_changes():
    dates = pd.bdate_range("2025-01-02", periods=150)
    base = pd.DataFrame(
        {
            "symbol": "A",
            "date": dates,
            "close": 100 + np.linspace(0, 30, len(dates)) + np.sin(np.arange(len(dates))),
        }
    )
    changed_future = base.copy()
    changed_future.loc[120:, "close"] *= 9

    original = _technical_pipeline(base).iloc[:120].reset_index(drop=True)
    changed = _technical_pipeline(changed_future).iloc[:120].reset_index(drop=True)
    feature_columns = [
        "simple_return",
        "log_return",
        "sma_20",
        "sma_50",
        "ema_20",
        "rsi_14",
        "volatility_20d_annualized",
        "drawdown",
        "max_drawdown_to_date",
        "momentum_21d",
        "momentum_63d",
        "momentum_126d",
    ]
    pdt.assert_frame_equal(original[feature_columns], changed[feature_columns])


def test_rolling_beta_is_prefix_invariant_to_future_return_changes():
    dates = pd.bdate_range("2025-01-02", periods=90)
    market = np.sin(np.arange(90) / 8) / 100
    aligned = pd.DataFrame(
        {
            "symbol": "A",
            "date": dates,
            "simple_return": market * 1.2 + 0.001,
            "benchmark_simple_return": market,
        }
    )
    changed_future = aligned.copy()
    changed_future.loc[70:, ["simple_return", "benchmark_simple_return"]] *= -12
    original = add_rolling_betas(aligned, windows=(20,)).iloc[:70]
    changed = add_rolling_betas(changed_future, windows=(20,)).iloc[:70]
    pdt.assert_series_equal(original["beta_20"], changed["beta_20"])


def test_future_date_audit_counts_filing_dates_after_decision_date():
    frame = pd.DataFrame(
        {
            "revenue_filed": ["2026-05-01", "2026-08-15", None],
            "assets_filed": ["2026-06-01", "2026-07-01", "2026-09-01"],
        }
    )
    assert future_date_violations(
        frame, "2026-08-01", ["revenue_filed", "assets_filed"]
    ) == {"revenue_filed": 1, "assets_filed": 1}
