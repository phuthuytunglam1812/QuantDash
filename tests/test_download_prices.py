from datetime import date
from unittest.mock import Mock

import pandas as pd

from src.download_prices import download_universe


def sample_frame(symbol="AAPL"):
    return pd.DataFrame(
        {"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5], "volume": [10],
         "symbol": [symbol], "provider": ["twelve_data"]},
        index=pd.DatetimeIndex(["2026-08-04"], name="date"),
    )


def test_downloader_writes_raw_file_and_manifest(tmp_path):
    client = Mock()
    client.daily_twelve_data.return_value = sample_frame()
    result = download_universe(tmp_path / "prices", end_date=date(2026, 8, 5), symbols=["AAPL"],
                               pause_seconds=0, client=client)
    assert result.iloc[0]["success"]
    assert (tmp_path / "prices" / "AAPL.csv").exists()
    assert (tmp_path / "download_manifest.csv").exists()
    _, kwargs = client.daily_twelve_data.call_args
    assert kwargs["start_date"] == "2024-07-29"


def test_downloader_resumes_existing_file(tmp_path):
    prices = tmp_path / "prices"
    prices.mkdir()
    sample_frame().reset_index().to_csv(prices / "AAPL.csv", index=False)
    client = Mock()
    result = download_universe(prices, symbols=["AAPL"], pause_seconds=0, client=client)
    client.daily_twelve_data.assert_not_called()
    assert "skipped" in result.iloc[0]["note"]
