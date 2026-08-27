from unittest.mock import Mock

from src.download_fundamentals import build_snapshot, download_fundamentals, latest_fact


def facts_payload():
    return {"entityName": "Example Inc.", "facts": {"us-gaap": {
        "Assets": {"units": {"USD": [
            {"val": 10, "end": "2025-12-31", "filed": "2026-02-01", "form": "10-K"},
            {"val": 12, "end": "2026-03-31", "filed": "2026-05-01", "form": "10-Q"},
        ]}},
        "NetIncomeLoss": {"units": {"USD": [
            {"val": 2, "end": "2026-03-31", "filed": "2026-05-01", "form": "10-Q", "frame": "CY2026Q1"},
            {"val": 99, "end": "2026-03-31", "filed": "2026-05-01", "form": "10-Q"},
            {"val": 100, "end": "2026-03-31", "filed": "2026-05-01", "form": "10-Q", "frame": "CY2026"}
        ]}},
    }}}


def test_latest_fact_uses_latest_filing():
    fact = latest_fact(facts_payload(), ["Assets"], "USD")
    assert fact.value == 12
    assert fact.form == "10-Q"


def test_latest_fact_prefers_standalone_sec_frame_over_ytd_value():
    fact = latest_fact(facts_payload(), ["NetIncomeLoss"], "USD")
    assert fact.value == 2


def test_latest_fact_respects_filing_date_as_of_rule():
    assert latest_fact(facts_payload(), ["Assets"], "USD", as_of="2026-04-30").value == 10
    assert latest_fact(facts_payload(), ["Assets"], "USD", as_of="2026-05-01").value == 12


def test_latest_fact_does_not_use_undated_or_future_filing():
    data = facts_payload()
    items = data["facts"]["us-gaap"]["Assets"]["units"]["USD"]
    items.extend([
        {"val": 999, "end": "2026-06-30", "filed": "", "form": "10-Q"},
        {"val": 888, "end": "2026-06-30", "filed": "2026-08-01", "form": "10-Q"},
    ])
    assert latest_fact(data, ["Assets"], "USD", as_of="2026-07-31").value == 12


def test_snapshot_keeps_provenance():
    row = build_snapshot("TEST", "0000000001", {"name": "Example Inc.", "exchanges": ["NYSE"]}, facts_payload())
    assert row["assets"] == 12
    assert row["assets_tag"] == "Assets"
    assert row["source"] == "SEC EDGAR Company Facts"


def test_downloader_writes_raw_and_processed(tmp_path):
    client = Mock()
    client.company_tickers.return_value = {"0": {"ticker": "TEST", "cik_str": 1}}
    client.company_facts.return_value = facts_payload()
    client.submissions.return_value = {"name": "Example Inc.", "exchanges": ["NYSE"]}
    frame = download_fundamentals(tmp_path / "raw", tmp_path / "processed.csv", ["TEST"],
                                  pause_seconds=0, client=client)
    assert len(frame) == 1
    assert (tmp_path / "raw" / "TEST_companyfacts.json").exists()
    assert (tmp_path / "processed.csv").exists()
