import pandas as pd
import pytest

from src.build_signal_labels import build_labels_from_frame, score_label


@pytest.mark.parametrize("value, expected", [
    (100, "Strong"), (80, "Strong"), (79.999, "Positive"),
    (60, "Positive"), (40, "Neutral"), (20, "Weak"),
    (0, "Very Weak"), (None, "Unavailable"),
])
def test_score_label_boundaries(value, expected):
    assert score_label(value) == expected


def test_component_labels_and_incomplete_overall_are_separate():
    frame = pd.DataFrame({
        "symbol": ["A"], "momentum_subscore": [92], "quality_subscore": [88],
        "valuation_subscore": [25], "composite_score": [76],
        "score_coverage": [.8], "incomplete_score_flag": [True], "score_eligible": [True],
    })
    result = build_labels_from_frame(frame).iloc[0]
    assert result.momentum_label == "Strong"
    assert result.fundamentals_label == "Strong"
    assert result.valuation_label == "Weak"
    assert result.overall_label == "Positive"
    assert result.overall_display_label == "Positive (Incomplete: 80% coverage)"
    assert "renormalized" in result.signal_note
    assert "not label inputs" in result.risk_context_note


def test_out_of_range_score_fails_loudly():
    with pytest.raises(ValueError, match="outside"):
        score_label(101)
