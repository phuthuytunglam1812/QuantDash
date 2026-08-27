import pandas as pd
import pytest

from src.build_features import prepare_adjusted_price_basis
from src.features import add_returns


def test_split_does_not_create_fake_loss_in_adjusted_returns():
    prices = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "date": ["2026-01-02", "2026-01-05"],
            "close": [100.0, 50.0],
            "adjusted_close": [50.0, 50.0],
            "provider": ["alpha_vantage", "alpha_vantage"],
        }
    )
    prepared = prepare_adjusted_price_basis(prices)
    result = add_returns(prepared)
    assert prepared["unadjusted_close"].tolist() == [100.0, 50.0]
    assert result.loc[1, "simple_return"] == pytest.approx(0.0)
    assert prices.close.pct_change(fill_method=None).iloc[1] == pytest.approx(-0.5)


def test_dividend_adjustment_avoids_treating_distribution_as_price_loss():
    prices = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "date": ["2026-01-02", "2026-01-05"],
            "close": [100.0, 99.0],
            "adjusted_close": [99.0, 99.0],
            "provider": ["alpha_vantage", "alpha_vantage"],
        }
    )
    result = add_returns(prepare_adjusted_price_basis(prices))
    assert result.loc[1, "simple_return"] == pytest.approx(0.0)


def test_twelve_data_adjust_all_is_not_mislabeled_as_unadjusted_close():
    prices = pd.DataFrame(
        {
            "symbol": ["A"],
            "date": ["2026-01-02"],
            "close": [75.0],
            "adjusted_close": [75.0],
            "provider": ["twelve_data"],
        }
    )
    result = prepare_adjusted_price_basis(prices)
    assert pd.isna(result.loc[0, "unadjusted_close"])
    assert result.loc[0, "close"] == 75.0


def test_invalid_adjusted_close_fails_instead_of_falling_back_to_raw_close():
    prices = pd.DataFrame(
        {
            "symbol": ["A"],
            "date": ["2026-01-02"],
            "close": [75.0],
            "adjusted_close": [None],
            "provider": ["twelve_data"],
        }
    )
    with pytest.raises(ValueError, match="populated and strictly positive"):
        prepare_adjusted_price_basis(prices)
