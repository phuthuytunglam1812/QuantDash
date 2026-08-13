import pandas as pd
import pytest

from src.transform_features import provider_valuation_table, transform_features


def test_winsorization_preserves_raw_and_caps_only_scoring_copy():
    master = pd.DataFrame({
        "symbol": [f"S{i}" for i in range(20)] + ["SPY"],
        "is_benchmark": [False] * 20 + [True],
        **{feature: list(range(20)) + [10] for feature in [
            "beta_252", "momentum_21d", "momentum_63d", "momentum_126d",
            "volatility_20d_annualized", "revenue_growth_yoy", "profit_margin",
        ]},
    })
    valuation = pd.DataFrame({
        "symbol": [f"S{i}" for i in range(20)], "pe_ratio": list(range(1, 21)),
        "pe_ratio_raw": list(range(1, 21)), "provider_eps_ttm": [1] * 20,
        "pe_is_meaningful": [True] * 20, "pe_exclusion_reason": [""] * 20,
        "pe_source": ["test"] * 20,
    })
    result, bounds = transform_features(master, valuation)
    assert result.loc[result.symbol.eq("S19"), "beta_252"].iloc[0] == 19
    assert result.loc[result.symbol.eq("S19"), "beta_252_winsorized"].iloc[0] == pytest.approx(18.05)
    assert result.loc[result.symbol.eq("S19"), "beta_252_outlier_flag"].iloc[0]
    assert pd.isna(result.loc[result.symbol.eq("SPY"), "beta_252_winsorized"].iloc[0])
    assert bounds.set_index("feature").loc["beta_252", "upper_capped_count"] == 1


def test_provider_pe_negative_or_missing_is_not_meaningful(tmp_path):
    (tmp_path / "A_overview.json").write_text('{"PERatio":"-4", "EPS":"-2"}')
    (tmp_path / "B_overview.json").write_text('{"PERatio":"20", "EPS":"4"}')
    result = provider_valuation_table(tmp_path, ["A", "B", "C"]).set_index("symbol")
    assert pd.isna(result.loc["A", "pe_ratio"])
    assert result.loc["A", "pe_ratio_raw"] == -4
    assert not result.loc["A", "pe_is_meaningful"]
    assert result.loc["B", "pe_ratio"] == 20
    assert result.loc["C", "pe_exclusion_reason"] == "provider overview missing"
