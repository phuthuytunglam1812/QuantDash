import numpy as np
import pandas as pd

from src.build_correlations import correlation_outputs


def test_correlation_uses_pairwise_complete_without_fill():
    frame = pd.DataFrame({
        "a": [1.0, 2.0, 3.0, 4.0],
        "b": [2.0, 4.0, 6.0, 8.0],
        "c": [1.0, np.nan, 3.0, 4.0],
    })
    correlation, counts, pairs = correlation_outputs(frame, {"A": "a", "B": "b", "C": "c"})
    assert correlation.loc["A", "B"] == 1.0
    assert counts.loc["A", "B"] == 4
    assert counts.loc["A", "C"] == 3
    row = pairs[(pairs.feature_1.eq("A")) & pairs.feature_2.eq("C")].iloc[0]
    assert row.pairwise_observations == 3


def test_correlation_pair_table_has_unique_upper_triangle_pairs():
    frame = pd.DataFrame({"a": range(5), "b": range(5), "c": range(5)})
    _, _, pairs = correlation_outputs(frame, {"A": "a", "B": "b", "C": "c"})
    assert len(pairs) == 3
    assert not pairs.duplicated(["feature_1", "feature_2"]).any()
