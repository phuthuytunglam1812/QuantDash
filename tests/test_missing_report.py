import pandas as pd
import pytest

from src.build_missing_report import build_missing_report_from_frame


def test_missing_report_excludes_spy_structural_fundamental_nulls():
    master = pd.DataFrame({
        "symbol": ["A", "B", "SPY"], "is_benchmark": [False, False, True],
        "close": [10.0, None, 20.0], "revenue": [100.0, None, None],
        "eps_diluted": [1.0, None, None],
    })
    report, missing_by_ticker, summary = build_missing_report_from_frame(master)
    indexed = report.set_index("feature")
    assert indexed.loc["revenue", "eligible_rows"] == 2
    assert indexed.loc["revenue", "missing_count"] == 1
    assert indexed.loc["revenue", "missing_rate"] == pytest.approx(0.5)
    assert indexed.loc["close", "eligible_rows"] == 3
    assert indexed.loc["close", "missing_count"] == 1
    assert "SPY" not in missing_by_ticker.symbol.tolist()
    assert summary["benchmark_structural_missing_excluded"]


def test_missing_report_rejects_duplicate_tickers():
    master = pd.DataFrame({
        "symbol": ["A", "A"], "is_benchmark": [False, False], "close": [1, 2],
    })
    with pytest.raises(ValueError, match="duplicate"):
        build_missing_report_from_frame(master)


def test_empty_quality_note_is_not_treated_as_missing_feature():
    master = pd.DataFrame({
        "symbol": ["A", "SPY"], "is_benchmark": [False, True],
        "close": [1.0, 2.0], "quality_note": [None, None],
    })
    report, _, _ = build_missing_report_from_frame(master)
    assert "quality_note" not in report.feature.tolist()
