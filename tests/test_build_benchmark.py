import numpy as np
import pandas as pd
import pytest

from src.build_benchmark import build_benchmark


def write_features(root, duplicate=False):
    processed = root / "processed"
    processed.mkdir(parents=True)
    dates = pd.to_datetime(["2026-01-01", "2026-01-02"])
    spy = pd.DataFrame({
        "date": dates, "symbol": ["SPY", "SPY"], "close": [100.0, 102.0],
        "simple_return": [np.nan, 0.02], "log_return": [np.nan, np.log(1.02)],
        "provider": ["twelve_data", "twelve_data"],
    })
    other = spy.assign(symbol="AAPL")
    frame = pd.concat([spy, other], ignore_index=True)
    if duplicate:
        frame = pd.concat([frame, spy.iloc[[1]]], ignore_index=True)
    frame.to_parquet(processed / "price_features.parquet", index=False)


def test_build_benchmark_extracts_normalized_spy(tmp_path):
    write_features(tmp_path)
    benchmark, report = build_benchmark(tmp_path)
    assert benchmark.symbol.unique().tolist() == ["SPY"]
    assert benchmark.date.is_monotonic_increasing
    assert report["rows"] == 2
    assert report["return_rows"] == 1
    assert (tmp_path / "processed" / "benchmark_spy.parquet").exists()
    assert (tmp_path / "processed" / "benchmark_report.json").exists()


def test_build_benchmark_rejects_duplicate_dates(tmp_path):
    write_features(tmp_path, duplicate=True)
    with pytest.raises(ValueError, match="duplicate dates"):
        build_benchmark(tmp_path)


def test_build_benchmark_rejects_return_mismatch(tmp_path):
    write_features(tmp_path)
    path = tmp_path / "processed" / "price_features.parquet"
    frame = pd.read_parquet(path)
    frame.loc[frame.symbol.eq("SPY") & frame.date.eq(pd.Timestamp("2026-01-02")), "simple_return"] = 0.5
    frame.to_parquet(path, index=False)
    with pytest.raises(ValueError, match="simple returns"):
        build_benchmark(tmp_path)
