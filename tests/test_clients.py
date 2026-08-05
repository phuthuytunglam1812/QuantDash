from unittest.mock import Mock, patch

import pytest
import requests

from src.clients.base import DataProviderError, HttpConfig
from src.clients.market_data import MarketDataClient
from src.clients.sec_edgar import SecEdgarClient


def response(payload):
    result = Mock()
    result.json.return_value = payload
    result.raise_for_status.return_value = None
    return result


@patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test"})
def test_alpha_vantage_is_normalized():
    session = Mock()
    session.get.return_value = response({"Time Series (Daily)": {"2026-08-04": {
        "1. open": "1", "2. high": "2", "3. low": "0.5", "4. close": "1.5", "5. volume": "10"
    }}})
    frame = MarketDataClient(session=session).daily_alpha_vantage("aapl")
    assert frame.iloc[0]["symbol"] == "AAPL"
    assert frame.iloc[0]["close"] == 1.5


@patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "a", "TWELVE_DATA_API_KEY": "t"})
def test_price_client_falls_back_to_twelve_data():
    client = MarketDataClient(session=Mock())
    client.daily_alpha_vantage = Mock(side_effect=DataProviderError("limited"))
    client.daily_twelve_data = Mock(return_value="fallback")
    assert client.daily("AAPL") == "fallback"


@patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "secret"})
def test_http_error_redacts_secret():
    session = Mock()
    session.get.side_effect = requests.ConnectionError("url?apikey=secret")
    client = MarketDataClient(config=HttpConfig(retries=0), session=session)
    with pytest.raises(DataProviderError, match="REDACTED") as caught:
        client.daily_alpha_vantage("AAPL")
    assert "secret" not in str(caught.value)


@patch.dict("os.environ", {"SEC_USER_AGENT": "Student student@example.com"})
def test_sec_cik_and_headers():
    session = Mock()
    session.get.return_value = response({"facts": {}})
    client = SecEdgarClient(session=session)
    client.company_facts(320193)
    args, kwargs = session.get.call_args
    assert args[0].endswith("CIK0000320193.json")
    assert kwargs["headers"]["User-Agent"].startswith("Student")
