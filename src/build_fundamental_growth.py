"""Build strict quarterly YoY revenue growth and matched-period profit margin."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

from src.config import TICKERS
from src.download_fundamentals import FACTS


QUARTER_FRAME = re.compile(r"^CY(?P<year>\d{4})Q(?P<quarter>[1-4])I?$")
REVENUE_TAGS = [*FACTS["revenue"][0], "RevenuesNetOfInterestExpense"]


def quarterly_facts(
    payload: dict,
    tags: list[str],
    unit: str = "USD",
    as_of: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Extract SEC-framed standalone quarters, deduplicated by period and tag priority."""
    concepts = payload.get("facts", {}).get("us-gaap", {})
    rows = []
    for priority, tag in enumerate(tags):
        for item in concepts.get(tag, {}).get("units", {}).get(unit, []):
            match = QUARTER_FRAME.fullmatch(str(item.get("frame", "")))
            if not match or item.get("form") not in {"10-Q", "10-K", "20-F", "40-F"}:
                continue
            rows.append({
                "frame": item["frame"], "year": int(match.group("year")),
                "quarter": int(match.group("quarter")), "value": item.get("val"),
                "start": item.get("start", ""), "end": item.get("end", ""),
                "filed": item.get("filed", ""), "form": item.get("form", ""),
                "tag": tag, "tag_priority": priority,
            })
    if not rows:
        return pd.DataFrame(columns=[
            "frame", "year", "quarter", "value", "start", "end", "filed", "form", "tag", "tag_priority"
        ])
    frame = pd.DataFrame(rows)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame["filed_date"] = pd.to_datetime(frame["filed"], errors="coerce")
    frame = frame.dropna(subset=["value", "filed_date"])
    if as_of is not None:
        frame = frame[frame["filed_date"].dt.normalize().le(pd.Timestamp(as_of).normalize())]
    # Prefer the configured canonical tag, then the most recently filed version.
    frame = frame.sort_values(
        ["year", "quarter", "tag_priority", "filed"],
        ascending=[True, True, True, False], kind="stable",
    ).drop_duplicates(["year", "quarter"], keep="first")
    return frame.sort_values(["year", "quarter"]).reset_index(drop=True)


def calculate_company_growth(
    symbol: str, payload: dict, as_of: str | pd.Timestamp | None = None
) -> dict:
    revenue = quarterly_facts(payload, REVENUE_TAGS, as_of=as_of)
    income = quarterly_facts(payload, FACTS["net_income"][0], as_of=as_of)
    base = {
        "symbol": symbol,
        "company_name": payload.get("entityName", ""),
        "revenue_growth_yoy": None,
        "profit_margin": None,
        "latest_revenue": None,
        "prior_year_revenue": None,
        "latest_net_income": None,
        "latest_frame": "",
        "comparison_frame": "",
        "revenue_tag": "",
        "net_income_tag": "",
        "period_start": "",
        "period_end": "",
        "revenue_growth_available": False,
        "profit_margin_available": False,
        "quality_note": "",
        "unusual_margin_flag": False,
    }
    if revenue.empty:
        base["quality_note"] = "no SEC-framed standalone quarterly revenue"
        return base

    latest = revenue.iloc[-1]
    prior = revenue[(revenue.year.eq(latest.year - 1)) & revenue.quarter.eq(latest.quarter)]
    base.update({
        "latest_revenue": latest.value,
        "latest_frame": latest.frame,
        "comparison_frame": f"CY{latest.year - 1}Q{latest.quarter}",
        "revenue_tag": latest.tag,
        "period_start": latest.start,
        "period_end": latest.end,
        "latest_revenue_filed": latest.filed,
    })
    notes = []
    if not prior.empty and prior.iloc[-1].value > 0:
        prior_row = prior.iloc[-1]
        base["prior_year_revenue"] = prior_row.value
        base["prior_year_revenue_tag"] = prior_row.tag
        base["prior_year_revenue_filed"] = prior_row.filed
        base["revenue_growth_yoy"] = latest.value / prior_row.value - 1
        base["revenue_growth_available"] = True
    else:
        notes.append("same-quarter prior-year revenue unavailable or nonpositive")

    matched_income = income[
        income["start"].eq(latest.start) & income["end"].eq(latest.end)
    ]
    if not matched_income.empty and latest.value != 0:
        income_row = matched_income.iloc[-1]
        base["latest_net_income"] = income_row.value
        base["net_income_tag"] = income_row.tag
        base["net_income_filed"] = income_row.filed
        base["profit_margin"] = income_row.value / latest.value
        base["profit_margin_available"] = True
        base["unusual_margin_flag"] = abs(base["profit_margin"]) > 0.75
        if base["unusual_margin_flag"]:
            notes.append("absolute quarterly profit margin exceeds 75%; review source fact")
    else:
        notes.append("same-period quarterly net income unavailable or revenue zero")
    base["quality_note"] = "; ".join(notes)
    return base


def build_fundamental_growth(data_dir: str | Path = "data") -> tuple[pd.DataFrame, dict]:
    root = Path(data_dir)
    raw = root / "raw" / "sec"
    rows = []
    for symbol in TICKERS:
        path = raw / f"{symbol}_companyfacts.json"
        if not path.exists():
            rows.append({"symbol": symbol, "quality_note": "raw Company Facts file missing"})
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.append(calculate_company_growth(symbol, payload))
    frame = pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)
    output = root / "processed" / "fundamental_growth.csv"
    frame.to_csv(output, index=False)
    report = {
        "symbols": len(frame),
        "revenue_growth_definition": "latest SEC-framed standalone quarter vs same quarter prior year",
        "profit_margin_definition": "same-period quarterly net income / quarterly revenue",
        "revenue_growth_yoy_available": int(frame["revenue_growth_available"].fillna(False).sum()),
        "profit_margin_available": int(frame["profit_margin_available"].fillna(False).sum()),
        "unusual_margin_flags": int(frame["unusual_margin_flag"].fillna(False).sum()),
        "missing_policy": "retain null; never substitute QoQ, YTD, nearest period, or zero",
        "source": "SEC EDGAR Company Facts",
    }
    (root / "processed" / "fundamental_growth_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return frame, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    frame, report = build_fundamental_growth(args.data_dir)
    print(json.dumps(report, indent=2))
    print(frame[[
        "symbol", "latest_frame", "comparison_frame", "revenue_growth_yoy",
        "profit_margin", "quality_note",
    ]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
