import pandas as pd
import pytest

from src.clean_data import DataQualityError, clean_fundamentals, clean_prices


def price_frame():
    return pd.DataFrame({
        "date": ["2026-08-04"], "symbol": [" aapl "], "open": [1.0], "high": [2.0],
        "low": [0.5], "close": [1.5], "adjusted_close": [1.4],
        "volume": [10.0], "provider": ["TEST"],
    })


def test_price_cleaning_normalizes_schema():
    clean, report = clean_prices(price_frame())
    assert clean.iloc[0]["symbol"] == "AAPL"
    assert clean.iloc[0]["provider"] == "test"
    assert str(clean["volume"].dtype) == "int64"
    assert clean.iloc[0]["price_adjustment"] == "splits_and_dividends"
    assert not any(report["issues"].values())


def test_price_cleaning_rejects_impossible_bar():
    frame = price_frame()
    frame.loc[0, "high"] = 0.8
    with pytest.raises(DataQualityError, match="high_below_ohlc"):
        clean_prices(frame)


def test_fundamentals_derives_liabilities_with_same_period():
    frame = pd.DataFrame({
        "symbol": ["aapl"], "revenue": [10], "net_income": [2], "assets": [100],
        "liabilities": [None], "equity": [40], "eps_diluted": [1],
        "assets_period_end": ["2026-06-30"], "equity_period_end": ["2026-06-30"],
        "assets_filed": ["2026-07-31"], "equity_filed": ["2026-07-31"],
        "liabilities_period_end": [None], "liabilities_filed": [None],
        "liabilities_form": [None], "liabilities_tag": [None],
    })
    clean, report = clean_fundamentals(frame)
    assert clean.iloc[0]["liabilities"] == 60
    assert clean.iloc[0]["liabilities_form"] == "DERIVED"
    assert report["liabilities_derived"] == 1


def test_fundamentals_does_not_mix_reporting_periods():
    frame = pd.DataFrame({
        "symbol": ["AAPL"], "revenue": [10], "net_income": [2], "assets": [100],
        "liabilities": [None], "equity": [40], "eps_diluted": [1],
        "assets_period_end": ["2026-06-30"], "equity_period_end": ["2026-03-31"],
        "assets_filed": ["2026-07-31"], "equity_filed": ["2026-05-01"],
        "liabilities_period_end": [None], "liabilities_filed": [None],
        "liabilities_form": [None], "liabilities_tag": [None],
    })
    clean, report = clean_fundamentals(frame)
    assert pd.isna(clean.iloc[0]["liabilities"])
    assert report["liabilities_derived"] == 0
