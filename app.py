from pathlib import Path

import pandas as pd
import streamlit as st

from src.dashboard import build_screener, filter_screener


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
    search = st.text_input("Ticker or company", placeholder="e.g. AAPL or Apple")
    rsi_range = st.slider("RSI 14 range", 0, 100, (0, 100))
    max_volatility = st.slider("Maximum annualized volatility", 10, 200, 200, format="%d%%")
    trend = st.selectbox("Trend", ["All", "Above SMA 50", "Below SMA 50"])
    include_benchmark = st.checkbox("Include SPY benchmark", value=True)
    st.caption("Latest market data: " + screener.date.max().strftime("%Y-%m-%d"))

filtered = filter_screener(screener, search, rsi_range, max_volatility, trend, include_benchmark)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Matches", len(filtered))
col2.metric("Bullish", int(filtered.signal.eq("Bullish").sum()))
col3.metric("Median RSI", f"{filtered.rsi_14.median():.1f}" if len(filtered) else "—")
col4.metric("Median volatility", f"{filtered.volatility_pct.median():.1f}%" if len(filtered) else "—")

st.subheader("Screener")
display_columns = {
    "symbol": "Ticker", "company_name": "Company", "close": "Close",
    "daily_return_pct": "1D return %", "rsi_14": "RSI 14", "signal": "Signal",
    "sma_20": "SMA 20", "sma_50": "SMA 50", "volatility_pct": "Volatility %",
    "drawdown_pct": "Drawdown %", "revenue_billions": "Revenue $B",
    "net_income_billions": "Net income $B", "eps_diluted": "Diluted EPS",
}
table = filtered[list(display_columns)].rename(columns=display_columns)
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
    },
)
st.download_button(
    "Download filtered CSV", table.to_csv(index=False).encode("utf-8"),
    file_name="quantdash_screener.csv", mime="text/csv",
)

st.subheader("Ticker detail")
available = filtered.symbol.tolist() or screener.symbol.tolist()
selected = st.selectbox("Select ticker", available)
detail = screener[screener.symbol.eq(selected)].iloc[0]
d1, d2, d3, d4 = st.columns(4)
d1.metric("Close", f"${detail.close:,.2f}", f"{detail.daily_return_pct:.2f}%")
d2.metric("RSI 14", f"{detail.rsi_14:.1f}")
d3.metric("20D volatility", f"{detail.volatility_pct:.1f}%")
d4.metric("Current drawdown", f"{detail.drawdown_pct:.1f}%")

ticker_history = history[history.symbol.eq(selected)].set_index("date")
st.line_chart(ticker_history[["close", "sma_20", "sma_50", "ema_20"]], height=360)
st.caption(
    "Educational prototype—not investment advice. Prices use provider close rather than adjusted close. "
    "SEC metrics may represent different fiscal periods; provenance remains in the processed dataset."
)
