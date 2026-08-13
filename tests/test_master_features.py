import pandas as pd
import pytest

from src.build_master_features import build_master_from_frames


def frames():
    technical = pd.DataFrame({"symbol": ["AAPL", "SPY"], "date": ["2026-08-04"] * 2, "close": [100, 200]})
    fundamentals = pd.DataFrame({"symbol": ["AAPL"], "company_name": ["Apple"], "revenue": [10]})
    betas = pd.DataFrame({
        "symbol": ["AAPL"], "beta_60": [1], "beta_60_n_obs": [60],
        "beta_126": [1], "beta_126_n_obs": [126], "beta_252": [1], "beta_252_n_obs": [252],
    })
    momentum = pd.DataFrame({
        "symbol": ["AAPL", "SPY"], "momentum_21d": [.1, .05], "momentum_21d_n_obs": [21, 21],
        "momentum_63d": [.2, .1], "momentum_63d_n_obs": [63, 63],
        "momentum_126d": [.3, .15], "momentum_126d_n_obs": [126, 126],
    })
    growth = pd.DataFrame({
        "symbol": ["AAPL"], "revenue_growth_yoy": [.2], "profit_margin": [.25],
        "latest_frame": ["CY2026Q2"], "comparison_frame": ["CY2025Q2"],
        "revenue_growth_available": [True], "profit_margin_available": [True],
        "unusual_margin_flag": [False], "quality_note": [""],
    })
    return technical, fundamentals, betas, momentum, growth


def test_master_is_one_row_per_symbol_and_spy_fundamentals_stay_null():
    master, report = build_master_from_frames(*frames())
    assert master.symbol.tolist() == ["AAPL", "SPY"]
    assert not master.symbol.duplicated().any()
    spy = master[master.symbol.eq("SPY")].iloc[0]
    assert spy.is_benchmark
    assert pd.isna(spy.company_name)
    assert pd.isna(spy.beta_252)
    assert spy.momentum_126d == .15
    assert report["fill_policy"] == "none"


def test_master_rejects_duplicate_source_symbols():
    source = list(frames())
    source[2] = pd.concat([source[2], source[2]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate symbols"):
        build_master_from_frames(*source)


def test_dedicated_momentum_snapshot_wins_without_suffix_columns():
    source = list(frames())
    source[0]["momentum_126d"] = [999, 999]
    master, _ = build_master_from_frames(*source)
    assert master.loc[master.symbol.eq("AAPL"), "momentum_126d"].iloc[0] == .3
    assert not any(column.endswith(("_x", "_y")) for column in master.columns)
