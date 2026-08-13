"""Build reproducible processed Parquet layers from preserved raw downloads."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PRICE_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "adjusted_close", "volume", "provider"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_price_layer(raw_dir: Path, output: Path) -> pd.DataFrame:
    files = sorted(raw_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"no raw price CSV files found in {raw_dir}")
    frames = []
    for path in files:
        frame = pd.read_csv(path)
        missing = set(PRICE_COLUMNS) - set(frame.columns)
        if missing:
            raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")
        frames.append(frame[PRICE_COLUMNS])
    prices = pd.concat(frames, ignore_index=True)
    prices["date"] = pd.to_datetime(prices["date"], errors="raise")
    prices["symbol"] = prices["symbol"].astype("string")
    prices["provider"] = prices["provider"].astype("string")
    for column in ["open", "high", "low", "close", "adjusted_close", "volume"]:
        prices[column] = pd.to_numeric(prices[column], errors="raise")
    prices = prices.sort_values(["symbol", "date"], kind="stable").reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(output, index=False)
    return prices


def build_fundamental_layer(raw_csv: Path, output: Path) -> pd.DataFrame:
    if not raw_csv.exists():
        raise FileNotFoundError(f"fundamentals snapshot not found: {raw_csv}")
    fundamentals = pd.read_csv(raw_csv)
    for column in [name for name in fundamentals if name.endswith(("_period_end", "_filed"))]:
        fundamentals[column] = pd.to_datetime(fundamentals[column], errors="coerce")
    fundamentals = fundamentals.sort_values("symbol", kind="stable").reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    fundamentals.to_parquet(output, index=False)
    return fundamentals


def _dataset_entry(path: Path, frame: pd.DataFrame) -> dict:
    entry = {
        "path": str(path), "rows": len(frame), "columns": list(frame.columns),
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "sha256": sha256(path),
    }
    if "date" in frame:
        entry["first_date"] = frame["date"].min().strftime("%Y-%m-%d")
        entry["last_date"] = frame["date"].max().strftime("%Y-%m-%d")
    if "symbol" in frame:
        entry["symbols"] = sorted(frame["symbol"].dropna().unique().tolist())
    return entry


def build_layers(data_dir: str | Path = "data") -> dict:
    root = Path(data_dir)
    processed = root / "processed"
    prices_path = processed / "prices.parquet"
    fundamentals_path = processed / "fundamentals.parquet"
    prices = build_price_layer(root / "raw" / "prices", prices_path)
    fundamentals = build_fundamental_layer(processed / "fundamentals.csv", fundamentals_path)
    raw_files = sorted((root / "raw").rglob("*"))
    raw_inventory = [
        {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in raw_files if path.is_file()
    ]
    catalog = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_policy": "Provider-shaped source files; never modified by this build.",
        "processed_policy": "Typed, consolidated analysis inputs; cleaning follows in W1-12.",
        "raw_inventory": raw_inventory,
        "datasets": {
            "prices": _dataset_entry(prices_path, prices),
            "fundamentals": _dataset_entry(fundamentals_path, fundamentals),
        },
    }
    (processed / "data_catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    catalog = build_layers(args.data_dir)
    for name, dataset in catalog["datasets"].items():
        print(f"{name}: {dataset['rows']} rows -> {dataset['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
