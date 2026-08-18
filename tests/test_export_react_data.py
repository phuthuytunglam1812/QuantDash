import json

from src.export_react_data import export_dashboard_data


def test_export_react_data_preserves_missing_values_and_history(tmp_path):
    output = export_dashboard_data(tmp_path / "dashboard.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["meta"]["price_basis"] == "adjusted_close"
    assert payload["meta"]["benchmark"] == "SPY"
    assert len(payload["stocks"]) == 21
    assert "SPY" in payload["history"]
    assert payload["history"]["SPY"][0]["date"]
    assert all("adjusted_close" in row for row in payload["history"]["SPY"])
