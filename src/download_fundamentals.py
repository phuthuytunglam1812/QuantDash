"""Download raw SEC filings data and build a normalized fundamentals snapshot."""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.clients import SecEdgarClient
from src.config import TICKERS


FACTS = {
    "revenue": (["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"], "USD"),
    "net_income": (["NetIncomeLoss", "ProfitLoss"], "USD"),
    "assets": (["Assets"], "USD"),
    "liabilities": (["Liabilities"], "USD"),
    "equity": (["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"], "USD"),
    "eps_diluted": (["EarningsPerShareDiluted"], "USD/shares"),
}


@dataclass
class FactValue:
    value: float | None = None
    period_end: str = ""
    filed: str = ""
    form: str = ""
    tag: str = ""
    unit: str = ""


def ticker_to_cik(payload: dict) -> dict[str, str]:
    return {
        str(item["ticker"]).upper(): str(item["cik_str"]).zfill(10)
        for item in payload.values()
    }


def latest_fact(
    company_facts: dict, tags: list[str], unit: str, as_of: str | pd.Timestamp | None = None
) -> FactValue:
    """Select the latest eligible fact known by ``as_of``.

    SEC facts without a valid filing date are never assumed to be available.
    The filing date, rather than the fiscal period end, controls availability.
    """
    concepts = company_facts.get("facts", {}).get("us-gaap", {})
    candidates: list[tuple[dict, str]] = []
    for tag in tags:
        for item in concepts.get(tag, {}).get("units", {}).get(unit, []):
            if item.get("form") in {"10-K", "10-Q", "20-F", "40-F"} and item.get("filed"):
                candidates.append((item, tag))
    if as_of is not None:
        cutoff = pd.Timestamp(as_of).normalize()
        candidates = [
            pair
            for pair in candidates
            if pd.notna(filed := pd.to_datetime(pair[0].get("filed"), errors="coerce"))
            and filed.normalize() <= cutoff
        ]
    if not candidates:
        return FactValue(unit=unit)
    # A filing can repeat quarterly, YTD, and comparative values with the same
    # filing date. SEC `frame` identifies a normalized standalone fiscal period;
    # prefer it to avoid accidentally selecting a cumulative YTD duration.
    framed_quarters = [
        pair for pair in candidates
        if re.fullmatch(r"CY\d{4}Q[1-4]I?", str(pair[0].get("frame", "")))
    ]
    framed = [pair for pair in candidates if pair[0].get("frame")]
    pool = framed_quarters or framed or candidates
    item, tag = max(pool, key=lambda pair: (pair[0].get("end", ""), pair[0].get("filed", "")))
    return FactValue(
        value=item.get("val"), period_end=item.get("end", ""), filed=item.get("filed", ""),
        form=item.get("form", ""), tag=tag, unit=unit,
    )


def build_snapshot(
    symbol: str,
    cik: str,
    submissions: dict,
    facts: dict,
    as_of: str | pd.Timestamp | None = None,
) -> dict:
    row = {
        "symbol": symbol,
        "cik": cik,
        "company_name": submissions.get("name") or facts.get("entityName", ""),
        "sic": submissions.get("sic", ""),
        "sic_description": submissions.get("sicDescription", ""),
        "fiscal_year_end": submissions.get("fiscalYearEnd", ""),
        "exchange": (submissions.get("exchanges") or [""])[0],
        "source": "SEC EDGAR Company Facts",
    }
    for field, (tags, unit) in FACTS.items():
        fact = latest_fact(facts, tags, unit, as_of=as_of)
        row[field] = fact.value
        row[f"{field}_period_end"] = fact.period_end
        row[f"{field}_filed"] = fact.filed
        row[f"{field}_form"] = fact.form
        row[f"{field}_tag"] = fact.tag
    return row


def download_fundamentals(
    output_dir: str | Path = "data/raw/sec", processed_path: str | Path = "data/processed/fundamentals.csv",
    symbols: list[str] | None = None, overwrite: bool = False, pause_seconds: float = 0.12,
    client: SecEdgarClient | None = None,
) -> pd.DataFrame:
    sec = client or SecEdgarClient()
    raw_dir = Path(output_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    target_symbols = symbols or TICKERS
    cik_map: dict[str, str] | None = None
    rows: list[dict] = []
    errors: list[dict] = []
    for symbol in target_symbols:
        facts_path = raw_dir / f"{symbol}_companyfacts.json"
        submissions_path = raw_dir / f"{symbol}_submissions.json"
        try:
            if facts_path.exists() and submissions_path.exists() and not overwrite:
                facts = json.loads(facts_path.read_text(encoding="utf-8"))
                submissions = json.loads(submissions_path.read_text(encoding="utf-8"))
                cik = str(facts.get("cik") or submissions.get("cik") or "").zfill(10)
            else:
                if cik_map is None:
                    cik_map = ticker_to_cik(sec.company_tickers())
                cik = cik_map.get(symbol.upper(), "")
                if not cik:
                    raise ValueError("ticker missing from SEC mapping")
                facts = sec.company_facts(cik)
                time.sleep(max(0.0, pause_seconds))
                submissions = sec.submissions(cik)
                facts_path.write_text(json.dumps(facts), encoding="utf-8")
                submissions_path.write_text(json.dumps(submissions), encoding="utf-8")
                time.sleep(max(0.0, pause_seconds))
            rows.append(build_snapshot(symbol, cik, submissions, facts))
        except Exception as exc:
            errors.append({"symbol": symbol, "error": f"{type(exc).__name__}: {exc}"})
    frame = pd.DataFrame(rows).sort_values("symbol") if rows else pd.DataFrame()
    processed = Path(processed_path)
    processed.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(processed, index=False)
    pd.DataFrame(errors, columns=["symbol", "error"]).to_csv(raw_dir / "download_errors.csv", index=False)
    return frame


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--symbol", action="append", dest="symbols")
    args = parser.parse_args()
    frame = download_fundamentals(symbols=args.symbols, overwrite=args.overwrite)
    print(frame[["symbol", "company_name", "revenue", "net_income", "assets", "eps_diluted"]].to_string(index=False))
    return 0 if len(frame) == len(args.symbols or TICKERS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
