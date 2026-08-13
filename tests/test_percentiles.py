import pandas as pd
import pytest

from src.build_percentiles import build_percentiles_from_frame, percentile_rank


def test_percentile_rank_reports_position_and_eligible_count_without_fill():
    values = pd.Series([10.0, 20.0, None, 30.0])
    percentile, position, count = percentile_rank(values)
    assert percentile.dropna().tolist() == pytest.approx([100 / 3, 200 / 3, 100])
    assert position.dropna().tolist() == [1, 2, 3]
    assert count.dropna().tolist() == [3, 3, 3]
    assert pd.isna(percentile.iloc[2])


def test_direction_adjustment_is_separate_from_raw_percentile():
    rows = []
    for symbol, pe, momentum in [("A", 10, .1), ("B", 20, .2), ("C", 30, .3)]:
        rows.append({
            "symbol": symbol, "date": "2026-08-04", "is_benchmark": False,
            "pe_ratio": pe, "pe_ratio_winsorized": pe,
            "momentum": momentum, "momentum_winsorized": momentum,
            "beta": momentum, "beta_winsorized": momentum,
        })
    rows.append({"symbol": "SPY", "date": "2026-08-04", "is_benchmark": True})
    policy = {
        "pe_ratio": {"source": "pe_ratio_winsorized", "direction": "lower", "score": "valuation_score"},
        "momentum": {"source": "momentum_winsorized", "direction": "higher", "score": "momentum_score"},
        "beta": {"source": "beta_winsorized", "direction": "descriptive", "score": None},
    }
    result, policy_table = build_percentiles_from_frame(pd.DataFrame(rows), policy)
    indexed = result.set_index("symbol")
    assert indexed.loc["C", "pe_ratio_percentile"] == 100
    assert indexed.loc["C", "valuation_score"] == 0
    assert indexed.loc["C", "momentum_score"] == 100
    assert "beta_score" not in result
    assert policy_table.set_index("feature").loc["beta", "direction"] == "descriptive"


def test_ties_use_average_rank():
    percentile, position, _ = percentile_rank(pd.Series([1, 1, 3, 4]))
    assert position.iloc[0] == 1.5
    assert percentile.iloc[0] == pytest.approx(37.5)
