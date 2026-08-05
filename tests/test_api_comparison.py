from unittest.mock import Mock, patch

import pandas as pd

from src.api_comparison import (
    ProbeResult,
    _safe_error,
    compare_providers,
    probe_alpha_vantage,
    probe_sec_edgar,
    probe_twelve_data,
)


def _response(payload):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


@patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test"})
@patch("src.api_comparison.requests.get")
def test_alpha_vantage_probe(mock_get):
    mock_get.return_value = _response({"Time Series (Daily)": {"2026-08-04": {"4. close": "100"}}})
    result = probe_alpha_vantage()
    assert result.success and result.rows == 1


@patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test"})
@patch("src.api_comparison.requests.get")
def test_twelve_data_probe(mock_get):
    mock_get.return_value = _response({"values": [{"datetime": "2026-08-04", "close": "100"}]})
    result = probe_twelve_data()
    assert result.success and result.rows == 1


@patch("src.api_comparison.probe_yfinance", side_effect=RuntimeError("offline"))
@patch("src.api_comparison.probe_alpha_vantage")
@patch("src.api_comparison.probe_twelve_data")
@patch("src.api_comparison.probe_sec_edgar")
def test_comparison_keeps_going_after_failure(sec, twelve, alpha, _yf):
    alpha.return_value = ProbeResult("Alpha Vantage", True, 1, "close", "2026-08-04", 0.1)
    twelve.return_value = ProbeResult("Twelve Data", True, 1, "close", "2026-08-04", 0.1)
    sec.return_value = ProbeResult("SEC EDGAR", True, 1, "facts", "2026-08-04", 0.1)
    result = compare_providers()
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 4
    assert not bool(result.iloc[0]["success"])


@patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "super-secret"})
def test_errors_redact_api_keys():
    note = _safe_error(RuntimeError("https://example.test/?apikey=super-secret"))
    assert "super-secret" not in note
    assert "[REDACTED]" in note


@patch.dict("os.environ", {"SEC_USER_AGENT": "Student student@example.com"})
@patch("src.api_comparison.requests.get")
def test_sec_companyfacts_probe(mock_get):
    mock_get.return_value = _response({
        "entityName": "Apple Inc.",
        "facts": {"us-gaap": {"Assets": {"units": {"USD": [{"filed": "2026-08-01"}]}}}},
    })
    result = probe_sec_edgar()
    assert result.success and result.rows == 1
    assert "not OHLCV" in result.columns
