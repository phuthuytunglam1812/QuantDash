from streamlit.testing.v1 import AppTest


def test_streamlit_app_renders_and_filters():
    app = AppTest.from_file("app.py").run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "QuantDash"
    assert app.metric[0].label == "Stocks shown"
    assert app.metric[0].value == "20 of 20"
    assert len(app.dataframe) == 1
    assert len(app.get("plotly_chart")) == 3

    app.text_input[0].set_value("Apple").run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "1 of 20"
    assert app.selectbox[0].value == "AAPL"
    assert len(app.get("plotly_chart")) == 3
