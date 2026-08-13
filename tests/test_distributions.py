import pandas as pd

from src.analyze_distributions import distribution_statistics


def test_distribution_statistics_tracks_missing_and_skew():
    frame = pd.DataFrame({"feature": [1.0, 1.0, 1.0, 10.0, None]})
    stats = distribution_statistics(frame, ["feature"]).iloc[0]
    assert stats.eligible_rows == 5
    assert stats.available_count == 4
    assert stats.missing_count == 1
    assert stats.missing_rate == .2
    assert stats.strong_skew_flag


def test_distribution_statistics_does_not_fill_missing():
    frame = pd.DataFrame({"feature": [1.0, None, 3.0]})
    stats = distribution_statistics(frame, ["feature"]).iloc[0]
    assert stats["mean"] == 2.0
    assert stats["median"] == 2.0
