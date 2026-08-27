from datetime import date
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest
import requests

from src.calculate_beta import add_rolling_betas
from src.clients.base import BaseHttpClient, DataProviderError, HttpConfig
from src.clients.market_data import MarketDataClient
from src.download_prices import download_universe
from src.features import add_returns, add_risk_features
from src.transform_features import provider_valuation_table, transform_features


@pytest.mark.parametrize(
    ("pe", "eps", "reason"),
    [
        ("-8", "2", "provider P/E nonpositive"),
        ("0", "2", "provider P/E nonpositive"),
        ("20", "0", "provider EPS nonpositive"),
        ("20", "-3", "provider EPS nonpositive"),
        ("N/A", "2", "provider P/E missing"),
    ],
)
def test_invalid_valuation_is_retained_as_raw_but_excluded_from_score(
    tmp_path, pe, eps, reason
):
    (tmp_path / "A_overview.json").write_text(
        f'{{"PERatio": "{pe}", "EPS": "{eps}"}}', encoding="utf-8"
    )
    row = provider_valuation_table(tmp_path, ["A"]).iloc[0]
    assert pd.isna(row.pe_ratio)
    assert not row.pe_is_meaningful
    assert row.pe_exclusion_reason == reason


def test_constant_features_winsorize_without_division_or_infinity():
    master = pd.DataFrame(
        {
            "symbol": ["A", "B", "SPY"],
            "is_benchmark": [False, False, True],
            "beta_252": [1.0, 1.0, 1.0],
            "momentum_21d": [0.0, 0.0, 0.0],
            "momentum_63d": [0.0, 0.0, 0.0],
            "momentum_126d": [0.0, 0.0, 0.0],
            "volatility_20d_annualized": [0.0, 0.0, 0.0],
            "revenue_growth_yoy": [0.0, 0.0, np.nan],
            "profit_margin": [0.1, 0.1, np.nan],
        }
    )
    valuation = pd.DataFrame(
        {
            "symbol": ["A", "B"],
            "pe_ratio": [20.0, 20.0],
            "pe_ratio_raw": [20.0, 20.0],
        }
    )
    result, bounds = transform_features(master, valuation)
    numeric = result.filter(regex="_winsorized$").select_dtypes(include="number")
    assert not np.isinf(numeric.to_numpy()).any()
    assert not result.filter(regex="_outlier_flag$").any().any()
    assert bounds.loc[bounds.feature.eq("beta_252"), "lower_bound"].iloc[0] == 1.0
    assert bounds.loc[bounds.feature.eq("beta_252"), "upper_bound"].iloc[0] == 1.0


def test_zero_price_variance_produces_zero_volatility_and_nan_beta():
    prices = pd.DataFrame(
        {
            "symbol": "A",
            "date": pd.bdate_range("2026-01-02", periods=25),
            "close": 100.0,
        }
    )
    risk = add_risk_features(add_returns(prices))
    assert risk.volatility_20d_annualized.dropna().eq(0).all()

    aligned = pd.DataFrame(
        {
            "symbol": "A",
            "date": pd.bdate_range("2026-01-02", periods=20),
            "simple_return": np.linspace(-0.01, 0.01, 20),
            "benchmark_simple_return": 0.0,
        }
    )
    beta = add_rolling_betas(aligned, windows=(20,))
    assert pd.isna(beta.beta_20.iloc[-1])
    assert not np.isinf(beta.beta_20).any()


@patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "secret-value"})
def test_timeout_is_wrapped_and_secret_is_redacted():
    session = Mock()
    session.get.side_effect = requests.Timeout(
        "https://provider.test?apikey=secret-value"
    )
    client = MarketDataClient(config=HttpConfig(retries=0), session=session)
    with pytest.raises(DataProviderError) as caught:
        client.daily_alpha_vantage("AAPL")
    assert "secret-value" not in str(caught.value)
    assert "REDACTED" in str(caught.value)


def test_non_object_and_invalid_json_responses_raise_provider_error():
    non_object = Mock()
    non_object.raise_for_status.return_value = None
    non_object.json.return_value = []
    session = Mock()
    session.get.return_value = non_object
    with pytest.raises(DataProviderError, match="non-object"):
        BaseHttpClient(config=HttpConfig(retries=0), session=session).get_json("https://x")

    invalid = Mock()
    invalid.raise_for_status.return_value = None
    invalid.json.side_effect = ValueError("invalid JSON")
    session.get.return_value = invalid
    with pytest.raises(DataProviderError, match="invalid JSON"):
        BaseHttpClient(config=HttpConfig(retries=0), session=session).get_json("https://x")


def test_failed_download_writes_manifest_but_not_fake_price_file(tmp_path):
    client = Mock()
    client.daily_twelve_data.side_effect = DataProviderError("rate limited")
    manifest = download_universe(
        output_dir=tmp_path / "prices",
        end_date=date(2026, 8, 21),
        symbols=["AAPL"],
        overwrite=True,
        pause_seconds=0,
        client=client,
    )
    assert not bool(manifest.loc[0, "success"])
    assert "rate limited" in manifest.loc[0, "note"]
    assert not (tmp_path / "prices" / "AAPL.csv").exists()
    assert (tmp_path / "download_manifest.csv").exists()
