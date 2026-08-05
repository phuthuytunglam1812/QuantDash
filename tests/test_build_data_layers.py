import json

import pandas as pd

from src.build_data_layers import build_layers


def test_build_layers_creates_parquet_and_catalog(tmp_path):
    prices_dir = tmp_path / "raw" / "prices"
    prices_dir.mkdir(parents=True)
    pd.DataFrame({
        "date": ["2026-08-04"], "symbol": ["AAPL"], "open": [1], "high": [2],
        "low": [0.5], "close": [1.5], "volume": [10], "provider": ["test"],
    }).to_csv(prices_dir / "AAPL.csv", index=False)
    processed = tmp_path / "processed"
    processed.mkdir()
    pd.DataFrame({"symbol": ["AAPL"], "company_name": ["Apple"]}).to_csv(
        processed / "fundamentals.csv", index=False
    )
    catalog = build_layers(tmp_path)
    assert (processed / "prices.parquet").exists()
    assert (processed / "fundamentals.parquet").exists()
    assert catalog["datasets"]["prices"]["rows"] == 1
    saved = json.loads((processed / "data_catalog.json").read_text(encoding="utf-8"))
    assert len(saved["datasets"]["prices"]["sha256"]) == 64


def test_build_rejects_incomplete_raw_price_schema(tmp_path):
    prices_dir = tmp_path / "raw" / "prices"
    prices_dir.mkdir(parents=True)
    pd.DataFrame({"date": ["2026-08-04"]}).to_csv(prices_dir / "bad.csv", index=False)
    processed = tmp_path / "processed"
    processed.mkdir()
    pd.DataFrame({"symbol": ["AAPL"]}).to_csv(processed / "fundamentals.csv", index=False)
    try:
        build_layers(tmp_path)
    except ValueError as exc:
        assert "missing columns" in str(exc)
    else:
        raise AssertionError("incomplete schema should fail")
