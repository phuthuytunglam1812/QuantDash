import json
from unittest.mock import Mock

import pandas as pd
import pytest

from src.compare_beta import collect_provider_betas, compare_betas, parse_provider_beta


def test_parse_provider_beta_preserves_missing_as_none():
    assert parse_provider_beta({"Beta": "1.23"}) == 1.23
    assert parse_provider_beta({"Beta": "None"}) is None
    assert parse_provider_beta({}) is None


def test_provider_collection_caches_raw_response(tmp_path):
    client = Mock()
    client.alpha_vantage_overview.return_value = {"Symbol": "AAPL", "Beta": "1.2"}
    first = collect_provider_betas(tmp_path, ["AAPL"], pause_seconds=0, client=client)
    assert first.iloc[0]["provider_beta"] == 1.2
    assert first.iloc[0]["provider_status"] == "downloaded"
    assert json.loads((tmp_path / "AAPL_overview.json").read_text())["Beta"] == "1.2"
    second = collect_provider_betas(tmp_path, ["AAPL"], pause_seconds=0, client=client)
    assert second.iloc[0]["provider_status"] == "cached"
    assert client.alpha_vantage_overview.call_count == 1


def test_comparison_keeps_methodology_warning_and_differences():
    calculated = pd.DataFrame({
        "symbol": ["AAPL"], "date": ["2026-08-04"],
        "beta_60": [1.0], "beta_126": [1.1], "beta_252": [1.2],
    })
    provider = pd.DataFrame({
        "symbol": ["AAPL"], "provider_beta": [1.3], "provider": ["Alpha Vantage OVERVIEW"],
        "provider_status": ["downloaded"], "provider_error": [""],
        "provider_beta_available": [True],
    })
    result = compare_betas(calculated, provider)
    assert result.iloc[0]["difference_beta_252"] == pytest.approx(-0.1)
    assert not bool(result.iloc[0]["methodology_comparable"])
    assert "not guaranteed" in result.iloc[0]["comparison_note"]
