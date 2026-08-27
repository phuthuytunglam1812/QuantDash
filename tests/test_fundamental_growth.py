import pytest

from src.build_fundamental_growth import calculate_company_growth, quarterly_facts


def payload():
    return {"entityName": "Example Inc.", "facts": {"us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [
            {"val": 100, "start": "2025-04-01", "end": "2025-06-30", "filed": "2025-08-01", "form": "10-Q", "frame": "CY2025Q2"},
            {"val": 120, "start": "2026-04-01", "end": "2026-06-30", "filed": "2026-08-01", "form": "10-Q", "frame": "CY2026Q2"},
            {"val": 220, "start": "2026-01-01", "end": "2026-06-30", "filed": "2026-08-01", "form": "10-Q"},
        ]}},
        "NetIncomeLoss": {"units": {"USD": [
            {"val": 24, "start": "2026-04-01", "end": "2026-06-30", "filed": "2026-08-01", "form": "10-Q", "frame": "CY2026Q2"},
            {"val": 40, "start": "2026-01-01", "end": "2026-06-30", "filed": "2026-08-01", "form": "10-Q"},
        ]}},
    }}}


def test_growth_is_yoy_same_quarter_and_margin_is_same_period():
    result = calculate_company_growth("TEST", payload())
    assert result["latest_frame"] == "CY2026Q2"
    assert result["comparison_frame"] == "CY2025Q2"
    assert result["revenue_growth_yoy"] == pytest.approx(0.2)
    assert result["profit_margin"] == pytest.approx(0.2)
    assert result["latest_net_income"] == 24


def test_ytd_facts_without_quarter_frame_are_excluded():
    revenue = quarterly_facts(payload(), ["RevenueFromContractWithCustomerExcludingAssessedTax"])
    assert revenue.value.tolist() == [100, 120]


def test_missing_prior_year_remains_null_not_qoq_substitute():
    data = payload()
    values = data["facts"]["us-gaap"]["RevenueFromContractWithCustomerExcludingAssessedTax"]["units"]["USD"]
    values.pop(0)
    result = calculate_company_growth("TEST", data)
    assert result["revenue_growth_yoy"] is None
    assert not result["revenue_growth_available"]
    assert "prior-year" in result["quality_note"]


def test_unmatched_income_period_does_not_create_margin():
    data = payload()
    income = data["facts"]["us-gaap"]["NetIncomeLoss"]["units"]["USD"][0]
    income["start"] = "2026-01-01"
    result = calculate_company_growth("TEST", data)
    assert result["profit_margin"] is None
    assert not result["profit_margin_available"]


def test_bank_net_revenue_tag_is_supported():
    data = payload()
    revenue = data["facts"]["us-gaap"].pop("RevenueFromContractWithCustomerExcludingAssessedTax")
    data["facts"]["us-gaap"]["RevenuesNetOfInterestExpense"] = revenue
    result = calculate_company_growth("BANK", data)
    assert result["revenue_growth_yoy"] == pytest.approx(0.2)
    assert result["revenue_tag"] == "RevenuesNetOfInterestExpense"


def test_unusual_margin_is_flagged_not_capped():
    data = payload()
    data["facts"]["us-gaap"]["NetIncomeLoss"]["units"]["USD"][0]["val"] = 114
    result = calculate_company_growth("TEST", data)
    assert result["profit_margin"] == pytest.approx(0.95)
    assert result["unusual_margin_flag"]
    assert "exceeds 75%" in result["quality_note"]


def test_growth_snapshot_excludes_quarter_filed_after_as_of_date():
    before_filing = calculate_company_growth("TEST", payload(), as_of="2026-07-31")
    assert before_filing["latest_frame"] == "CY2025Q2"
    assert before_filing["revenue_growth_yoy"] is None

    on_filing_date = calculate_company_growth("TEST", payload(), as_of="2026-08-01")
    assert on_filing_date["latest_frame"] == "CY2026Q2"
    assert on_filing_date["revenue_growth_yoy"] == pytest.approx(0.2)


def test_growth_excludes_missing_filing_date_in_point_in_time_mode():
    data = payload()
    revenue = data["facts"]["us-gaap"]["RevenueFromContractWithCustomerExcludingAssessedTax"]["units"]["USD"]
    revenue[1]["filed"] = ""
    result = calculate_company_growth("TEST", data, as_of="2026-08-01")
    assert result["latest_frame"] == "CY2025Q2"
