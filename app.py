from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard import (
    build_screener, filter_screener, prepare_benchmark_comparison,
    prepare_deep_dive, prepare_signal_map,
)


st.set_page_config(page_title="QuantDash", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {background: #f7f9fc; border: 1px solid #e3e8ef; padding: 12px; border-radius: 10px;}
    .subtitle {color: #596579; margin-top: -0.6rem; margin-bottom: 1.5rem;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    return build_screener(Path(__file__).parent / "data")


try:
    screener, history = load_data()
except FileNotFoundError:
    st.error("Processed data is missing. Run the data and feature build commands in README.md first.")
    st.stop()

st.title("QuantDash")
st.markdown('<p class="subtitle">A reproducible US equity screener built from market prices and SEC filings.</p>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Filters")
    def reset_filters():
        for key in list(st.session_state):
            if key.startswith("filter_") or key in {"search", "rsi_range", "max_volatility", "trend", "include_benchmark"}:
                del st.session_state[key]

    st.button("Reset filters", on_click=reset_filters, width="stretch")
    search = st.text_input("Ticker or company", placeholder="e.g. AAPL or Apple", key="search")
    rsi_range = st.slider("RSI 14 range", 0, 100, (0, 100), key="rsi_range")
    max_volatility = st.slider("Maximum annualized volatility", 10, 200, 200, format="%d%%", key="max_volatility")
    trend = st.selectbox("Trend", ["All", "Above SMA 50", "Below SMA 50"], key="trend")
    include_benchmark = st.checkbox("Include SPY benchmark", value=False, key="include_benchmark")

    st.subheader("Combine criteria")
    numeric_filters = {}
    filter_specs = [
        ("Momentum 3M at least", "momentum_63d_raw_pct", ">=", -100.0, 300.0, 10.0),
        ("Profit margin at least", "profit_margin_raw_pct", ">=", -100.0, 100.0, 20.0),
        ("P/E at most", "pe_ratio_raw", "<=", 0.0, 500.0, 35.0, "x"),
        ("Beta 252D at most", "beta_252_raw", "<=", -5.0, 5.0, 1.5, ""),
        ("Composite score at least", "composite_score", ">=", 0.0, 100.0, 65.0, ""),
    ]
    for spec in filter_specs:
        label, column, operator, low, high, default, *suffix = spec
        enabled = st.checkbox(f"Use {label.lower()}", key=f"filter_enable_{column}")
        value = st.number_input(label, low, high, default, key=f"filter_value_{column}", disabled=not enabled)
        if enabled:
            numeric_filters[column] = (operator, value)

    label_options = ["Strong", "Positive", "Neutral", "Weak", "Very Weak"]
    selected_labels = st.multiselect("Overall signal", label_options, default=label_options, key="filter_signals")
    st.caption("Latest market data: " + screener.date.max().strftime("%Y-%m-%d"))

filtered = filter_screener(
    screener, search, rsi_range, max_volatility, trend, include_benchmark,
    numeric_filters=numeric_filters,
    signal_labels=None if selected_labels == label_options else selected_labels,
    sort_by="composite_score", ascending=False,
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Stocks shown", f"{len(filtered)} of {int((~screener.symbol.eq('SPY')).sum())}")
col2.metric("Bullish", int(filtered.signal.eq("Bullish").sum()))
col3.metric("Median RSI", f"{filtered.rsi_14.median():.1f}" if len(filtered) else "—")
col4.metric("Median volatility", f"{filtered.volatility_pct.median():.1f}%" if len(filtered) else "—")

st.subheader("Screener")
all_display_columns = {
    "symbol": "Ticker", "company_name": "Company", "close": "Close",
    "daily_return_pct": "1D return %", "rsi_14": "RSI 14", "signal": "Signal",
    "sma_20": "SMA 20", "sma_50": "SMA 50", "volatility_pct": "Volatility %",
    "drawdown_pct": "Drawdown %", "revenue_billions": "Revenue $B",
    "net_income_billions": "Net income $B", "eps_diluted": "Diluted EPS",
    "momentum_63d_raw_pct": "Momentum 3M %", "profit_margin_raw_pct": "Profit margin %",
    "revenue_growth_yoy_raw_pct": "Revenue growth YoY %", "pe_ratio_raw": "P/E",
    "beta_252_raw": "Beta 252D", "momentum_subscore": "Momentum score",
    "quality_subscore": "Fundamentals score", "valuation_subscore": "Valuation score",
    "composite_score": "Composite score", "score_coverage": "Score coverage",
    "momentum_label": "Momentum signal", "fundamentals_label": "Fundamentals signal",
    "valuation_label": "Valuation signal", "overall_display_label": "Overall signal",
}
available_display = {column: label for column, label in all_display_columns.items() if column in filtered}
default_columns = [
    label for column, label in available_display.items()
    if column in {"symbol", "company_name", "momentum_63d_raw_pct", "profit_margin_raw_pct", "pe_ratio_raw",
                  "beta_252_raw", "composite_score", "overall_display_label"}
]
chosen_labels = st.multiselect("Columns to show", list(available_display.values()), default=default_columns, key="filter_columns")
chosen_columns = [column for column, label in available_display.items() if label in chosen_labels]
table = filtered[chosen_columns].rename(columns=available_display)
st.caption(f"Showing {len(filtered)} of {int((~screener.symbol.eq('SPY')).sum())} stocks. Missing values never pass an active filter.")
st.dataframe(
    table,
    width="stretch",
    hide_index=True,
    column_config={
        "Close": st.column_config.NumberColumn(format="$%.2f"),
        "1D return %": st.column_config.NumberColumn(format="%.2f%%"),
        "RSI 14": st.column_config.NumberColumn(format="%.1f"),
        "SMA 20": st.column_config.NumberColumn(format="$%.2f"),
        "SMA 50": st.column_config.NumberColumn(format="$%.2f"),
        "Volatility %": st.column_config.NumberColumn(format="%.1f%%"),
        "Drawdown %": st.column_config.NumberColumn(format="%.1f%%"),
        "Revenue $B": st.column_config.NumberColumn(format="$%.1f"),
        "Net income $B": st.column_config.NumberColumn(format="$%.1f"),
        "Diluted EPS": st.column_config.NumberColumn(format="%.2f"),
        "Momentum 3M %": st.column_config.NumberColumn(format="%.1f%%"),
        "Profit margin %": st.column_config.NumberColumn(format="%.1f%%"),
        "Revenue growth YoY %": st.column_config.NumberColumn(format="%.1f%%"),
        "P/E": st.column_config.NumberColumn(format="%.1f"),
        "Beta 252D": st.column_config.NumberColumn(format="%.2f"),
        "Composite score": st.column_config.NumberColumn(format="%.1f"),
        "Score coverage": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.0%%"),
    },
)
st.download_button(
    "Download filtered CSV", table.to_csv(index=False).encode("utf-8"),
    file_name="quantdash_screener.csv", mime="text/csv",
)

st.subheader("Signal Map: RSI vs P/E")
signal_map, excluded_from_map = prepare_signal_map(filtered)
st.caption(
    f"Plotting {len(signal_map)} of {len(filtered)} currently filtered stocks. "
    f"{excluded_from_map} excluded from this chart because RSI or P/E is unavailable."
)
if signal_map.empty:
    st.info("No currently filtered stocks have both RSI and P/E available.")
else:
    signal_colors = {
        "Strong": "#15803d", "Positive": "#65a30d", "Neutral": "#64748b",
        "Weak": "#ea580c", "Very Weak": "#b91c1c", "Unavailable": "#a1a1aa",
    }
    figure = px.scatter(
        signal_map, x="pe_ratio_raw", y="rsi_14", size="bubble_score",
        color="overall_label", text="symbol", hover_name="symbol",
        hover_data={
            "company_name": True, "composite_score": ":.1f", "bubble_score": False,
            "pe_ratio_raw": ":.1f", "rsi_14": ":.1f",
        },
        category_orders={"overall_label": ["Strong", "Positive", "Neutral", "Weak", "Very Weak", "Unavailable"]},
        color_discrete_map=signal_colors,
        labels={
            "pe_ratio_raw": "P/E ratio (lower is cheaper, not automatically better)",
            "rsi_14": "RSI 14", "overall_label": "Overall signal",
            "composite_score": "Composite score",
        },
        size_max=34,
    )
    figure.add_hline(y=70, line_dash="dot", line_color="#dc2626", annotation_text="Overbought 70")
    figure.add_hline(y=30, line_dash="dot", line_color="#2563eb", annotation_text="Oversold 30")
    figure.update_traces(textposition="top center")
    figure.update_layout(height=560, margin=dict(l=20, r=20, t=30, b=20), legend_title_text="Overall signal")
    st.plotly_chart(figure, width="stretch")
    st.caption(
        "Bubble size represents composite score. RSI and P/E are descriptive axes; "
        "the map is a relative comparison of the W2-15 subset, not a buy/sell recommendation."
    )

st.subheader("Ticker detail")
available = filtered.symbol.tolist() or screener.symbol.tolist()
detail_controls = st.columns([2, 1])
selected = detail_controls[0].selectbox("Select ticker", available)
timeframe = detail_controls[1].selectbox("Timeframe", ["3M", "6M", "1Y", "2Y"], index=2)
detail = screener[screener.symbol.eq(selected)].iloc[0]
deep_dive = prepare_deep_dive(history, selected, timeframe)
latest_deep_dive = deep_dive.iloc[-1]
d1, d2, d3, d4 = st.columns(4)
d1.metric("Adjusted close", f"${latest_deep_dive.adjusted_close:,.2f}", f"{detail.daily_return_pct:.2f}%")
d2.metric("RSI 14", f"{detail.rsi_14:.1f}")
d3.metric("20D annualized volatility", f"{latest_deep_dive.volatility_20d_annualized_pct:.1f}%")
d4.metric(f"{timeframe} max drawdown", f"{deep_dive.timeframe_drawdown_pct.min():.1f}%")

price_figure = px.line(
    deep_dive, x="date", y=["adjusted_close", "sma_20", "sma_50"],
    labels={"value": "Adjusted price ($)", "variable": "Series", "date": "Date"},
)
price_figure.update_layout(height=390, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(price_figure, width="stretch")

if selected != "SPY":
    comparison, comparison_summary = prepare_benchmark_comparison(history, selected, timeframe)
    st.markdown(f"#### {selected} vs SPY · {timeframe}")
    market_cols = st.columns(4)
    market_cols[0].metric(f"{selected} return", f"{comparison_summary['stock_return']:+.1%}")
    market_cols[1].metric("SPY return", f"{comparison_summary['benchmark_return']:+.1%}")
    market_cols[2].metric("Excess return", f"{comparison_summary['excess_return_pp']:+.1f} pp")
    market_cols[3].metric("Common dates", comparison_summary["common_observations"])
    comparison_long = comparison.melt(
        id_vars="date", value_vars=[f"{selected}_indexed", "SPY_indexed"],
        var_name="Series", value_name="Indexed adjusted value",
    )
    comparison_long["Series"] = comparison_long["Series"].str.replace("_indexed", "", regex=False)
    comparison_figure = px.line(
        comparison_long, x="date", y="Indexed adjusted value", color="Series",
        labels={"date": "Common trading date"},
    )
    comparison_figure.add_hline(y=100, line_dash="dot", line_color="#64748b")
    comparison_figure.update_layout(height=390, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(comparison_figure, width="stretch")
    st.caption(
        f"Both series start at 100 on {comparison_summary['first_common_date']:%Y-%m-%d} and use "
        f"split-and-dividend-adjusted close on {comparison_summary['common_observations']} identical dates. "
        f"Excluded unmatched dates — {selected}: {comparison_summary['stock_dates_excluded']}, "
        f"SPY: {comparison_summary['benchmark_dates_excluded']}. No missing values were filled."
    )

indicator_tabs = st.tabs(["RSI 14", "20D annualized volatility", f"{timeframe} drawdown"])
with indicator_tabs[0]:
    st.line_chart(deep_dive.set_index("date")["rsi_14"], height=260)
    st.caption("Wilder RSI(14); 14 trading-observation warm-up. Reference levels: 30 and 70.")
with indicator_tabs[1]:
    st.line_chart(deep_dive.set_index("date")["volatility_20d_annualized_pct"], height=260)
    st.caption("Sample standard deviation of the latest 20 daily adjusted-close log returns × √252.")
with indicator_tabs[2]:
    st.line_chart(deep_dive.set_index("date")["timeframe_drawdown_pct"], height=260)
    st.caption(f"Adjusted close / running peak within the selected {timeframe} window − 1.")

with st.expander("Calculation methodology"):
    st.markdown("""
- **Price basis:** adjusted close with provider `adjust=all` (stock splits and cash dividends).
- **Return:** `ln(adjusted_close_t / adjusted_close_(t-1))` for volatility.
- **SMA 20/50:** arithmetic mean of adjusted close over 20/50 trading observations.
- **RSI 14:** Wilder average gains and losses over 14 trading observations.
- **20D annualized volatility:** sample standard deviation of 20 daily log returns multiplied by `sqrt(252)`.
- **Timeframe drawdown:** adjusted close divided by the running adjusted-close peak inside the selected window, minus one.

The timeframe controls the visible window and timeframe drawdown. Rolling indicators retain earlier warm-up observations before the chart is sliced.
""")
st.caption(
    "Educational prototype—not investment advice. Price-derived metrics use split-and-dividend-adjusted close. "
    "SEC metrics may represent different fiscal periods; provenance remains in the processed dataset."
)
