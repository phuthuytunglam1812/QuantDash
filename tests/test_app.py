from streamlit.testing.v1 import AppTest


def test_streamlit_app_renders_and_filters():
    app = AppTest.from_file("app.py").run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "QuantDash"
    assert any("Stocks shown" in item.value and "20 / 20" in item.value for item in app.markdown)
    assert len(app.get("latex")) >= 4
    assert any("N is the stock universe" in item.value for item in app.markdown)
    assert any("Adjusted close" in item.value for item in app.markdown)
    assert any("VALUATION // P/E" in item.value for item in app.markdown)
    assert len(app.dataframe) == 1
    assert len(app.get("plotly_chart")) == 3

    app.text_input[0].set_value("Apple")
    apply_button = next(button for button in app.button if button.label == "Apply filters")
    apply_button.click().run(timeout=30)
    assert not app.exception
    assert any("Stocks shown" in item.value and "1 / 20" in item.value for item in app.markdown)
    assert app.selectbox[0].value == "AAPL"
    assert len(app.get("plotly_chart")) == 3


def test_learn_methods_is_a_separate_navigation_page():
    app = AppTest.from_file("app.py").run(timeout=30)
    app.radio[0].set_value("Learn the Methods").run(timeout=30)
    assert not app.exception
    assert any(title.value == "Learn the Methods" for title in app.title)
    assert any("Adjusted Close = Raw Close" in item.value for item in app.markdown)
    contents = next(item.value for item in app.markdown if "TABLE OF CONTENTS" in item.value)
    for anchor in ["#adjusted-close", "#returns", "#trend", "#rsi", "#risk", "#notation"]:
        assert f'href="{anchor}"' in contents
    assert len(app.dataframe) == 0
