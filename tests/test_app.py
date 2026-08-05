from streamlit.testing.v1 import AppTest


def test_streamlit_app_renders_and_filters():
    app = AppTest.from_file("app.py").run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "QuantDash"
    assert app.metric[0].label == "Matches"
    assert app.metric[0].value == "21"
    assert len(app.dataframe) == 1

    app.text_input[0].set_value("Apple").run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "1"
    assert app.selectbox[0].value == "AAPL"
