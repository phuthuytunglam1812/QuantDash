import pandas as pd
import pytest

from src.build_composite_score import build_scores_from_frame, weighted_score


def test_weighted_score_renormalizes_missing_without_zero_fill():
    frame = pd.DataFrame({"a": [80.0], "b": [None], "c": [60.0]})
    score, coverage = weighted_score(frame, {"a": .4, "b": .4, "c": .2}, require_all=False)
    assert coverage.iloc[0] == pytest.approx(.6)
    assert score.iloc[0] == pytest.approx((80 * .4 + 60 * .2) / .6)
    strict, _ = weighted_score(frame, {"a": .4, "b": .4, "c": .2}, require_all=True)
    assert pd.isna(strict.iloc[0])


def test_subscores_and_beta_exclusion_are_explicit():
    percentile = pd.DataFrame({
        "symbol": ["A", "B"], "date": ["2026-08-04"] * 2,
        "momentum_21d_score": [90, 30], "momentum_63d_score": [80, 40],
        "momentum_126d_score": [70, 50], "growth_score": [60, 50],
        "profitability_score": [80, 60], "valuation_score": [50, None],
        "drawdown_resilience_score": [70, 40],
    })
    context = pd.DataFrame({
        "symbol": ["A", "B"], "beta_252": [3.0, .2],
        "volatility_20d_annualized": [.5, .2], "rsi_14": [60, 40], "drawdown": [-.1, -.2],
        "unusual_margin_flag": [False, False],
    })
    result = build_scores_from_frame(percentile, context).set_index("symbol")
    assert result.loc["A", "momentum_subscore"] == pytest.approx(78)
    assert result.loc["A", "quality_subscore"] == pytest.approx(70)
    assert result.loc["A", "composite_score"] == pytest.approx(69.2)
    assert result.loc["B", "score_coverage"] == pytest.approx(.8)
    assert result.loc["B", "incomplete_score_flag"]
    assert "excluded" in result.loc["A", "beta_role"]


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError, match="sum to 1"):
        weighted_score(pd.DataFrame({"a": [1]}), {"a": .5})
