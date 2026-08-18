from pathlib import Path
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard import (
    build_research_summary, build_screener, filter_screener, prepare_benchmark_comparison,
    prepare_deep_dive, prepare_signal_map,
)


st.set_page_config(page_title="QuantDash", page_icon="📈", layout="wide")

st.markdown("""
<style>
    :root {--qd-cyan:#22d3ee; --qd-blue:#60a5fa; --qd-indigo:#6366f1; --qd-bg:#050a12; --qd-panel:#0b1322; --qd-line:rgba(56,189,248,.28);}
    html, body, [class*="css"] {font-family: Inter, ui-sans-serif, system-ui, sans-serif;}
    .stApp {
        color: #dbeafe;
        background:
            linear-gradient(rgba(34,211,238,.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(34,211,238,.025) 1px, transparent 1px),
            radial-gradient(circle at 82% 4%, rgba(37,99,235,.15), transparent 28%),
            radial-gradient(circle at 15% 40%, rgba(8,145,178,.08), transparent 25%),
            var(--qd-bg);
        background-size: 42px 42px, 42px 42px, auto, auto, auto;
    }
    [data-testid="stHeader"] {background: rgba(5,10,18,.72); backdrop-filter: blur(16px); border-bottom: 1px solid rgba(56,189,248,.10);}
    .block-container {max-width: 1440px; padding-top: 2.4rem; padding-bottom: 4rem;}
    .subtitle {color: #94a3b8; margin-top: -0.6rem; margin-bottom: 1.5rem; letter-spacing: .025em;}
    h1, h2, h3, h4, h5 {letter-spacing: -.025em; color: #f8fafc;}
    h1 {
        font-family: "IBM Plex Mono", "Cascadia Code", Consolas, monospace !important;
        background: linear-gradient(90deg, #f8fafc, #7dd3fc 58%, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 0 28px rgba(34,211,238,.12);
    }
    h2 {margin-top: 2.4rem !important; padding: 0 0 .65rem .85rem; border-left: 3px solid var(--qd-cyan); border-bottom: 1px solid rgba(56,189,248,.13);}
    h3, h4, h5 {font-family: "IBM Plex Mono", "Cascadia Code", Consolas, monospace !important;}
    p, li {color: #cbd5e1;}
    a {color: #67e8f9 !important; text-decoration-color: rgba(103,232,249,.4) !important;}
    .research-path {
        margin: 14px 0 24px; padding: 13px 16px; border: 1px solid rgba(34,211,238,.22); border-radius: 10px;
        background: linear-gradient(90deg, rgba(6,182,212,.08), rgba(99,102,241,.06));
        color: #bae6fd; font: 600 .88rem "IBM Plex Mono",Consolas,monospace; letter-spacing: .025em;
    }
    .research-path span {color:#475569; padding:0 .35rem;}
    .method-toc {
        margin:1.25rem 0 2.6rem; padding:1.2rem; border:1px solid rgba(56,189,248,.32); border-radius:14px;
        background:linear-gradient(135deg,rgba(10,20,36,.96),rgba(8,12,29,.94));
        box-shadow:inset 3px 0 0 rgba(34,211,238,.72),0 0 28px rgba(14,165,233,.08);
    }
    .method-toc__eyebrow {font:700 .72rem "IBM Plex Mono",Consolas,monospace; letter-spacing:.16em; color:#67e8f9;}
    .method-toc__title {margin:.25rem 0 1rem; font:700 1.15rem "IBM Plex Mono",Consolas,monospace; color:#f8fafc;}
    .method-toc__grid {display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.65rem;}
    .method-toc__grid a {
        display:grid; grid-template-columns:2rem 1fr; padding:.85rem; border:1px solid rgba(96,165,250,.24); border-radius:9px;
        background:rgba(7,15,29,.72); color:#dbeafe !important; font:650 .86rem "IBM Plex Mono",Consolas,monospace;
        text-decoration:none !important; transition:all .18s ease;
    }
    .method-toc__grid a span {grid-row:1 / 3; color:#67e8f9; font-size:.72rem; letter-spacing:.08em; padding-top:.12rem;}
    .method-toc__grid a small {margin-top:.22rem; color:#7c8ca3; font:500 .68rem "IBM Plex Mono",Consolas,monospace;}
    .method-toc__grid a:hover {transform:translateY(-2px); border-color:#22d3ee; background:rgba(14,116,144,.13); box-shadow:0 0 20px rgba(34,211,238,.10);}
    .method-anchor {scroll-margin-top:5.5rem; height:1px;}
    @media (max-width:900px) {.method-toc__grid {grid-template-columns:1fr 1fr;}}
    @media (max-width:560px) {.method-toc__grid {grid-template-columns:1fr;}}
    ::selection {background: rgba(34, 211, 238, .32); color: #f8fafc;}
    [data-testid="stSidebar"] {background: linear-gradient(180deg, rgba(8,15,28,.99), rgba(5,10,18,.99)); border-right: 1px solid var(--qd-line);}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {border-left: 0; border-bottom: 1px solid rgba(56,189,248,.18); padding-left: 0; text-transform: uppercase; font-size: .88rem; letter-spacing: .12em; color: #7dd3fc;}
    [data-testid="stWidgetLabel"] p, label p {font: 600 .78rem "IBM Plex Mono",Consolas,monospace; color:#bae6fd !important; letter-spacing:.035em;}
    [data-baseweb="input"] > div, [data-baseweb="base-input"], [data-baseweb="select"] > div,
    [data-baseweb="textarea"] > div, [data-baseweb="tag"] {
        background: rgba(8,15,28,.92) !important; color:#e0f2fe !important;
        border-color: rgba(56,189,248,.30) !important; border-radius: 9px !important;
    }
    [data-baseweb="select"] > div {
        box-shadow: inset 0 0 22px rgba(14,165,233,.055), 0 0 18px rgba(34,211,238,.075) !important;
    }
    [data-baseweb="tag"] {
        border:1px solid rgba(103,232,249,.40) !important;
        background:linear-gradient(135deg,rgba(8,145,178,.22),rgba(79,70,229,.20)) !important;
        box-shadow:0 0 12px rgba(34,211,238,.13) !important;
    }
    [data-baseweb="input"] input, [data-baseweb="base-input"] input, [data-baseweb="select"] input,
    [data-baseweb="select"] div {color:#e0f2fe !important; font-family:"IBM Plex Mono",Consolas,monospace !important;}
    [data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within {
        border-color:var(--qd-cyan) !important; box-shadow:0 0 0 1px var(--qd-cyan),0 0 18px rgba(34,211,238,.10) !important;
    }
    [role="listbox"], [data-baseweb="popover"] {background:#08111f !important; border-color:rgba(56,189,248,.35) !important;}
    [role="option"] {color:#dbeafe !important; font-family:"IBM Plex Mono",Consolas,monospace !important;}
    [role="option"]:hover {background:rgba(34,211,238,.12) !important;}
    [data-testid="stButton"] button, [data-testid="stDownloadButton"] button,
    [data-testid="stPopover"] button, [data-testid="stFormSubmitButton"] button {
        border:1px solid rgba(34,211,238,.34) !important; border-radius:8px !important;
        background:linear-gradient(135deg,rgba(14,116,144,.20),rgba(49,46,129,.18)) !important;
        color:#bae6fd !important; font:600 .78rem "IBM Plex Mono",Consolas,monospace !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.04); transition:all .18s ease;
    }
    [data-testid="stButton"] button:hover, [data-testid="stDownloadButton"] button:hover,
    [data-testid="stPopover"] button:hover, [data-testid="stFormSubmitButton"] button:hover {
        border-color:#22d3ee !important; color:#f8fafc !important; transform:translateY(-1px); box-shadow:0 0 20px rgba(34,211,238,.14);
    }
    [data-testid="stFormSubmitButton"] button {
        min-height:3rem; text-transform:uppercase; letter-spacing:.12em !important;
        background:linear-gradient(105deg,rgba(8,145,178,.38),rgba(79,70,229,.34)) !important;
        border-color:rgba(103,232,249,.72) !important; color:#ecfeff !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.08),0 0 22px rgba(34,211,238,.16) !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        background:linear-gradient(105deg,rgba(6,182,212,.50),rgba(99,102,241,.44)) !important;
        box-shadow:0 0 30px rgba(34,211,238,.27),inset 0 0 18px rgba(255,255,255,.035) !important;
    }
    [data-testid="stExpander"] {
        position:relative; border:1px solid rgba(56,189,248,.32) !important; border-radius:12px !important;
        background:linear-gradient(135deg,rgba(10,20,36,.94),rgba(6,12,24,.94)) !important;
        box-shadow:inset 3px 0 0 rgba(34,211,238,.65),inset 0 1px 0 rgba(255,255,255,.035),0 0 22px rgba(14,165,233,.065) !important;
        overflow:hidden;
    }
    [data-testid="stExpander"] summary {
        font:600 .84rem "IBM Plex Mono",Consolas,monospace; color:#bae6fd !important;
        letter-spacing:.025em; padding-top:.2rem; padding-bottom:.2rem;
    }
    [data-testid="stExpander"] summary:hover {color:#67e8f9 !important; background:rgba(34,211,238,.045);}
    [data-testid="stExpanderDetails"] {border-top:1px solid rgba(56,189,248,.13); background:rgba(3,10,20,.48); padding:1rem 1.15rem 1.15rem;}
    [data-testid="stPopoverBody"] {
        background:linear-gradient(145deg,#091525,#050b14) !important; color:#dbeafe !important;
        border:1px solid rgba(34,211,238,.40) !important; border-radius:12px !important;
        box-shadow:0 0 32px rgba(34,211,238,.13) !important;
        font-family:"IBM Plex Mono",Consolas,monospace !important;
    }
    [data-testid="stTabs"] [role="tablist"] {gap:8px; border-bottom:1px solid rgba(56,189,248,.20);}
    [data-testid="stTabs"] button[role="tab"] {font-family:"IBM Plex Mono",Consolas,monospace; color:#94a3b8; border-radius:7px 7px 0 0;}
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {color:#67e8f9; background:rgba(34,211,238,.08);}
    [data-testid="stDataFrame"] {border:1px solid rgba(56,189,248,.24); border-radius:12px; overflow:hidden; box-shadow:0 0 28px rgba(14,165,233,.055);}
    [data-testid="stAlert"] {background:rgba(8,20,36,.86) !important; border:1px solid rgba(56,189,248,.25) !important; border-radius:10px !important; color:#dbeafe !important;}
    [data-testid="stCaptionContainer"] p {font: .75rem/1.5 "IBM Plex Mono",Consolas,monospace; color:#7c8ca3 !important;}
    [data-testid="stCheckbox"] svg {color:#22d3ee !important;}
    [data-testid="stCheckbox"] label {padding:.22rem .1rem;}
    [data-testid="stCheckbox"] label:hover {background:rgba(34,211,238,.045); border-radius:7px;}
    [data-testid="stSlider"] [role="slider"] {background:#22d3ee !important; box-shadow:0 0 12px rgba(34,211,238,.45);}
    [data-testid="stRadio"] [role="radiogroup"] {display:flex; gap:8px; padding:6px; border:1px solid rgba(56,189,248,.25); border-radius:11px; background:rgba(5,12,23,.82); width:fit-content;}
    [data-testid="stRadio"] [role="radiogroup"] label {padding:8px 14px; border-radius:7px; font-family:"IBM Plex Mono",Consolas,monospace;}
    [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {background:linear-gradient(135deg,rgba(8,145,178,.25),rgba(79,70,229,.22)); box-shadow:0 0 16px rgba(34,211,238,.10);}
    hr {border-color:rgba(56,189,248,.16) !important;}
    ::-webkit-scrollbar {width:10px;height:10px;} ::-webkit-scrollbar-track{background:#050a12;} ::-webkit-scrollbar-thumb{background:#17314a;border:2px solid #050a12;border-radius:10px;} ::-webkit-scrollbar-thumb:hover{background:#155e75;}
    .tech-stat {
        position: relative; overflow: hidden; height: 188px; padding: 18px 20px; box-sizing:border-box;
        display:flex; flex-direction:column;
        border: 1px solid rgba(56, 189, 248, .42); border-radius: 14px;
        background: linear-gradient(145deg, rgba(15, 23, 42, .98), rgba(3, 12, 24, .98));
        box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 0 24px rgba(14,165,233,.09);
        color: #e6f7ff; font-family: "IBM Plex Mono", "Cascadia Code", Consolas, monospace;
    }
    .tech-stat::before {
        content: ""; position: absolute; inset: 0 auto 0 0; width: 3px;
        background: linear-gradient(#22d3ee, #6366f1); box-shadow: 0 0 16px #22d3ee;
    }
    .tech-stat::after {
        content: ""; position: absolute; width: 80px; height: 80px; right: -35px; top: -35px;
        border: 1px solid rgba(34,211,238,.22); transform: rotate(45deg);
    }
    .tech-label {font-size: .76rem; letter-spacing: .11em; text-transform: uppercase; color: #7dd3fc;}
    .tech-value {
        font-size: clamp(1.5rem, 2.45vw, 2.25rem); line-height: 1.08; margin-top: 14px;
        font-weight: 650; color: #f8fafc; white-space:nowrap; letter-spacing:-.035em;
    }
    .tech-delta {margin-top:auto; padding-top:10px; font-size:.72rem; line-height:1.45; color:#94a3b8; text-transform:uppercase; letter-spacing:.025em;}
    .context-board {
        display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px;
        padding: 16px; border: 1px solid rgba(99,102,241,.36); border-radius: 16px;
        background: radial-gradient(circle at top right, rgba(37,99,235,.12), transparent 36%), #080f1c;
        box-shadow: inset 0 0 36px rgba(14,165,233,.035);
    }
    .context-node {padding: 17px; border: 1px solid rgba(56,189,248,.22); border-radius: 10px; background: rgba(15,23,42,.84);}
    .context-key {font: 700 .72rem "IBM Plex Mono",Consolas,monospace; letter-spacing: .12em; color: #22d3ee; margin-bottom: 9px;}
    .context-reading {display:flex; align-items:center; gap:11px; flex-wrap:wrap; margin:.2rem 0 .85rem;}
    .context-number {font:700 1.85rem "IBM Plex Mono",Consolas,monospace; color:#f8fafc; letter-spacing:-.045em;}
    .context-status {padding:4px 8px; border:1px solid rgba(129,140,248,.45); border-radius:999px; background:rgba(79,70,229,.14); color:#c7d2fe; font:700 .69rem "IBM Plex Mono",Consolas,monospace; text-transform:uppercase; letter-spacing:.06em;}
    .context-headline {margin:.55rem 0 .45rem; color:#7dd3fc; font:700 .67rem "IBM Plex Mono",Consolas,monospace; letter-spacing:.10em; text-transform:uppercase;}
    .context-copy {font:.85rem/1.52 "IBM Plex Mono",Consolas,monospace; color:#dbeafe;}
    [data-testid="stLatex"] {padding:.9rem 1rem; border:1px solid rgba(56,189,248,.24); border-radius:9px; background:rgba(2,8,18,.72); overflow-x:auto;}
    [data-testid="stLatex"] .katex {color:#f8fafc; font-size:1.18em;}
    .plain-formula {
        margin:.45rem 0 .8rem; padding:14px 16px; border:1px solid rgba(34,211,238,.30); border-radius:9px;
        background:linear-gradient(135deg,rgba(8,145,178,.10),rgba(15,23,42,.78));
        color:#ecfeff; font:700 .92rem/1.65 "IBM Plex Mono",Consolas,monospace; letter-spacing:.01em;
        box-shadow:inset 3px 0 0 rgba(34,211,238,.65);
    }
    @media (max-width: 760px) {.context-board {grid-template-columns: 1fr;}}
</style>
""", unsafe_allow_html=True)


METRIC_GUIDE = {
    "Stocks shown": ("Number of equities remaining after all active W2-15 filters.", "count(rows after filters)", "Shows how restrictive the current screen is. Zero is a valid result."),
    "Bullish": ("Rule-based technical state, separate from the composite signal.", "close > SMA50 AND RSI14 ≥ 50", "Describes current trend/momentum; it is not a buy recommendation."),
    "Median RSI": ("Middle RSI value among currently displayed stocks.", "median(RSI14 of filtered stocks)", "Summarizes the shortlist without letting one extreme ticker dominate."),
    "Median volatility": ("Middle 20-trading-day annualized volatility of the filtered stocks.", "median[stdev(20 daily log returns) × √252]", "Higher values imply a wider range of recent price outcomes."),
    "Adjusted close": ("Closing price adjusted for stock splits and cash dividends.", "provider close with adjust=all", "Creates a consistent investment-return series across corporate actions; raw close can distort long comparisons."),
    "RSI 14": ("Wilder Relative Strength Index over 14 trading observations.", "100 − 100 / (1 + Wilder average gain / Wilder average loss)", "30 and 70 are reference zones, not automatic buy/sell rules."),
    "20D annualized volatility": ("Annualized dispersion of the latest 20 adjusted-close daily log returns.", "sample stdev(log returns, 20D) × √252", "A risk/context measure; high volatility is not automatically a bad company."),
    "Max drawdown": ("Largest peak-to-trough loss inside the selected timeframe.", "min(adjusted close / running peak − 1)", "Shows downside experienced in the visible period; changing timeframe changes the result."),
    "Stock return": ("Selected stock return across the first and last common stock/SPY dates.", "last adjusted close / first adjusted close − 1", "Measures total adjusted-price performance over the selected comparison window."),
    "SPY return": ("Market benchmark return over the exact same common dates.", "SPY last adjusted close / SPY first adjusted close − 1", "Provides market context for the stock result."),
    "Excess return": ("Stock return minus SPY return, expressed in percentage points.", "(stock return − SPY return) × 100", "Positive means outperformance over this period; it does not establish future alpha."),
    "Common dates": ("Trading dates for which both stock and SPY adjusted close are present.", "inner join(stock date, SPY date)", "No dates are forward-filled or invented before comparison."),
}

FORMULA_LATEX = {
    "Stocks shown": r"N_{shown}=\sum_{i=1}^{N}\mathbf{1}(\text{stock}_i\text{ passes every active filter})",
    "Bullish": r"\text{Bullish}_i=\mathbf{1}(P_i>SMA_{50,i}\;\land\;RSI_{14,i}\ge 50)",
    "Median RSI": r"\widetilde{RSI}_{14}=\operatorname{median}(RSI_{14,1},\ldots,RSI_{14,n})",
    "Median volatility": r"\widetilde{\sigma}_{20,ann}=\operatorname{median}_i\left[s(r_{i,t-19:t})\sqrt{252}\right]",
    "Adjusted close": r"P_t^{adj}=P_t^{raw}\times A_t^{split}\times A_t^{dividend}",
    "RSI 14": r"RSI_{14}=100-\frac{100}{1+\frac{\overline{G}_{14}^{Wilder}}{\overline{L}_{14}^{Wilder}}}",
    "20D annualized volatility": r"\sigma_{20,ann}=s\!\left(\ln\frac{P_t^{adj}}{P_{t-1}^{adj}}\right)_{20}\sqrt{252}",
    "Max drawdown": r"MDD_T=\min_{t\in T}\left(\frac{P_t^{adj}}{\max_{u\le t,\,u\in T}P_u^{adj}}-1\right)",
    "Stock return": r"R_{stock}=\frac{P_{last}^{adj}}{P_{first}^{adj}}-1",
    "SPY return": r"R_{SPY}=\frac{P_{SPY,last}^{adj}}{P_{SPY,first}^{adj}}-1",
    "Excess return": r"R_{excess}^{pp}=100\left(R_{stock}-R_{SPY}\right)",
    "Common dates": r"D_{common}=D_{stock}\cap D_{SPY}\quad\text{with both adjusted closes observed}",
}

FORMULA_PLAIN = {
    "Stocks shown": "Stocks shown = add 1 for every stock that passes all selected filters",
    "Bullish": "Bullish = Adjusted Close is above SMA 50 AND RSI 14 is at least 50",
    "Median RSI": "Median RSI = sort all displayed RSI values, then take the middle value",
    "Median volatility": "Median volatility = sort displayed volatility values, then take the middle value",
    "Adjusted close": "Adjusted Close = Raw Close × Split Adjustment × Dividend Adjustment",
    "RSI 14": "RSI = 100 − [100 ÷ (1 + Average Gain ÷ Average Loss)]",
    "20D annualized volatility": "20D volatility = Daily-movement spread across the latest 20 returns × √252",
    "Max drawdown": "Drawdown each day = Current Adjusted Close ÷ Highest Adjusted Close so far − 1; Max Drawdown = most negative result",
    "Stock return": "Stock Return = Last Adjusted Close ÷ First Adjusted Close − 1",
    "SPY return": "SPY Return = Last SPY Adjusted Close ÷ First SPY Adjusted Close − 1",
    "Excess return": "Excess Return = Stock Return − SPY Return",
    "Common dates": "Common Dates = keep a date only when both the stock and SPY have an Adjusted Close",
}


def render_plain_formula(text: str) -> None:
    st.markdown(f'<div class="plain-formula">{escape(text)}</div>', unsafe_allow_html=True)

FORMULA_TERMS = {
    "Stocks shown": "N is the stock universe; 𝟙(·) equals 1 only when the condition is true.",
    "Bullish": "P is adjusted close; SMA₅₀ is its 50-observation mean; RSI₁₄ is Wilder RSI.",
    "Median RSI": "The tilde denotes the median across currently filtered stocks.",
    "Median volatility": "s is sample standard deviation; r is daily adjusted-close log return; 252 is trading days per year.",
    "Adjusted close": "Praw is the reported close; Asplit and Adividend are provider adjustment factors for corporate actions.",
    "RSI 14": "Ḡ is the Wilder-smoothed average of positive adjusted-close changes. L̄ is the Wilder-smoothed average magnitude of negative changes; it is stored as a positive number.",
    "20D annualized volatility": "Padj is adjusted close; s is sample standard deviation over the latest 20 log returns.",
    "Max drawdown": "T is the selected timeframe; the denominator is the running adjusted-close peak within T.",
    "Stock return": "First and last refer to the first and last valid dates common to the stock and SPY.",
    "SPY return": "The benchmark uses the exact same common-date window and adjusted price basis.",
    "Excess return": "pp means percentage points, not percent change relative to SPY return.",
    "Common dates": "∩ denotes intersection; missing pairs are excluded without forward-fill or imputation.",
}


def render_rsi_gain_loss_steps() -> None:
    st.markdown("#### How gains and losses are built")
    st.markdown(
        "RSI does **not** use the company’s accounting profit or loss. Here, a gain or loss means only the "
        "change in **Adjusted Close from one trading observation to the next**."
    )
    st.markdown("**Step 1 — Calculate the daily adjusted-price change**")
    render_plain_formula("Today’s change = Today’s Adjusted Close − Previous trading day’s Adjusted Close")
    st.latex(r"\Delta P_t=P_t^{adj}-P_{t-1}^{adj}")
    st.markdown("**Step 2 — Split that one change into two non-negative columns**")
    split_cols = st.columns(2)
    with split_cols[0]:
        st.markdown("**Gain column**")
        render_plain_formula("Gain = Today’s change when positive; otherwise 0")
        st.latex(r"G_t=\max(\Delta P_t,0)")
        st.caption("An up day records the price increase. A down or unchanged day records 0.")
    with split_cols[1]:
        st.markdown("**Loss column**")
        render_plain_formula("Loss = Absolute size of today’s decline when negative; otherwise 0")
        st.latex(r"L_t=\max(-\Delta P_t,0)")
        st.caption("A down day records the absolute size of the decline as a positive number. An up or unchanged day records 0.")
    st.markdown("**Example before averaging**")
    st.markdown("""
| Adjusted Close move | ΔP | Gain G | Loss L |
|---|---:|---:|---:|
| 100 USD → 103 USD | +3 USD | 3 | 0 |
| 103 USD → 101 USD | −2 USD | 0 | 2 |
| 101 USD → 101 USD | 0 USD | 0 | 0 |

The loss is entered as `2`, not `−2`, because RSI compares the **magnitudes** of upward and downward movement.
""")
    st.markdown("**Step 3 — Seed RSI with the first 14 changes**")
    render_plain_formula("First Average Gain = (Gain Day 1 + Gain Day 2 + … + Gain Day 14) ÷ 14")
    render_plain_formula("First Average Loss = (Loss Day 1 + Loss Day 2 + … + Loss Day 14) ÷ 14")
    st.latex(r"\overline{G}_{14,seed}=\frac{1}{14}\sum_{i=1}^{14}G_i\qquad \overline{L}_{14,seed}=\frac{1}{14}\sum_{i=1}^{14}L_i")
    st.markdown(
        "This first value needs 15 adjusted closes to create 14 price changes. The earlier RSI cells remain missing during this warm-up; they are not filled with zero."
    )
    st.markdown("**Step 4 — Update each later observation using Wilder smoothing**")
    render_plain_formula("New Average Gain = [(Previous Average Gain × 13) + Today’s Gain] ÷ 14")
    render_plain_formula("New Average Loss = [(Previous Average Loss × 13) + Today’s Loss] ÷ 14")
    st.latex(r"\overline{G}_t=\frac{13\overline{G}_{t-1}+G_t}{14}\qquad \overline{L}_t=\frac{13\overline{L}_{t-1}+L_t}{14}")
    st.markdown(
        "The previous average receives weight 13 and today’s gain or loss receives weight 1. This makes RSI smoother than repeatedly taking a brand-new 14-day simple average."
    )
    st.markdown("**Step 5 — Convert the two smoothed averages into RSI**")
    render_plain_formula("Relative Strength = Average Gain ÷ Average Loss")
    render_plain_formula(FORMULA_PLAIN["RSI 14"])
    st.latex(r"RS_t=\frac{\overline{G}_t}{\overline{L}_t}\qquad RSI_t=100-\frac{100}{1+RS_t}")
    st.markdown(
        "If average loss is zero and gains exist, RSI is 100. If average gain is zero and losses exist, RSI is 0. "
        "If both are zero because price has been flat, QuantDash reports RSI as 50."
    )

METRIC_EXAMPLES = {
    "Stocks shown": "If 6 of 20 stocks remain, fourteen failed at least one active condition. It does not mean the six are good investments—only that they match your screen.",
    "Bullish": "If adjusted close is above SMA 50 and RSI is 56, the technical state is Bullish. A company can still have weak fundamentals or an expensive valuation.",
    "Median RSI": "For RSI values 40, 52, and 75, the median is 52—the middle observation after sorting, not the arithmetic average.",
    "Median volatility": "If the middle stock has 32% annualized volatility, half the valid shortlist is below roughly 32% and half is above it.",
    "Adjusted close": "After a 2-for-1 split, a historical raw close of 100 USD may be restated near 50 USD so the chart does not show a fake 50% loss caused only by the split.",
    "RSI 14": "An RSI of 72 means recent upward moves have outweighed downward moves. It flags strong recent momentum, but price can remain above 70 for a long time.",
    "20D annualized volatility": "A value of 40% does not predict a 40% loss. It says recent daily movements, when scaled to a one-year convention, have been relatively wide.",
    "Max drawdown": "If price rises from 100 USD to 120 USD and later falls to 90 USD, drawdown from that peak is 90/120 − 1 = −25%.",
    "Stock return": "If adjusted close moves from 100 USD to 115 USD on the common comparison dates, stock return is +15%.",
    "SPY return": "If SPY moves from an indexed 100 to 108 over the same common dates, its benchmark return is +8%.",
    "Excess return": "A stock return of +15% versus SPY at +8% gives +7 percentage points of excess return—not 87.5% excess return.",
    "Common dates": "If the stock has Monday–Wednesday data but SPY lacks Tuesday, Tuesday is removed from both series before returns are calculated.",
}

METRIC_PREREQUISITES = {
    "Bullish": [
        ("Adjusted Close", "A historical closing price corrected for stock splits and cash dividends so corporate actions do not create fake jumps."),
        ("SMA 50", "The average of the latest 50 Adjusted Close observations; it is a slower reference line for price trend."),
        ("RSI 14", "A 0–100 indicator comparing recent upward and downward adjusted-price movement over 14 trading changes."),
    ],
    "Median RSI": [("RSI 14", "A 0–100 measure of recent upward versus downward adjusted-price movement.")],
    "Median volatility": [("Annualized volatility", "Recent daily movement spread scaled to a one-year convention; it is not a predicted annual loss.")],
    "Stock return": [("Adjusted Close", "A closing price restated for splits and dividends so performance across time is comparable.")],
    "SPY return": [("SPY", "A fund tracking the S&P 500, used here as broad US large-cap market context."), ("Adjusted Close", "A split-and-dividend-adjusted historical closing price.")],
    "Excess return": [("SPY", "The market benchmark used for the same common dates."), ("Percentage points", "The arithmetic difference between two percentage returns.")],
}

FRIENDLY_LATEX = {
    "RSI 14": r"RSI=100-\left[\frac{100}{1+\left(\frac{\text{Average Gain}}{\text{Average Loss}}\right)}\right]",
}

METRIC_MISTAKES = {
    "Stocks shown": "Do not keep tightening filters until only one stock remains. That can manufacture apparent precision and hide useful alternatives.",
    "Bullish": "Bullish describes a rule-based price condition. It does not mean undervalued, profitable, safe, or guaranteed to rise.",
    "Median RSI": "The median summarizes the current filtered set, so it changes when filters change. It is not a market-wide constant.",
    "Median volatility": "Annualized volatility is not the maximum possible loss and does not indicate price direction.",
    "Adjusted close": "Do not compare one adjusted series with another website’s raw close without checking its corporate-action policy.",
    "RSI 14": "Above 70 is not automatically 'sell,' and below 30 is not automatically 'buy.' RSI needs trend, fundamentals, valuation, and risk context.",
    "20D annualized volatility": "A stable company can have volatile shares, and a low-volatility share can still be overvalued or decline slowly.",
    "Max drawdown": "Drawdown depends on the chosen timeframe. A 3M drawdown and 2Y drawdown answer different questions.",
    "Stock return": "Past return is descriptive. It should not be treated as a forecast of the next period.",
    "SPY return": "SPY is broad US large-cap market context, not a perfect benchmark for every company, sector, or risk level.",
    "Excess return": "Positive past excess return does not prove manager skill or future alpha, especially over a short window.",
    "Common dates": "Never replace a missing benchmark return with zero; zero means a real unchanged price, while missing means unknown.",
}


def render_stat(target, label: str, value: str, guide_key: str, delta: str = "") -> None:
    definition, _, significance = METRIC_GUIDE[guide_key]
    with target:
        st.markdown(
            f'<div class="tech-stat"><div class="tech-label">{escape(label)}</div>'
            f'<div class="tech-value">{escape(value)}</div>'
            f'<div class="tech-delta">{escape(delta) if delta else "LIVE • CLICK BELOW TO INSPECT"}</div></div>',
            unsafe_allow_html=True,
        )
        with st.popover(f"ⓘ About {label}", use_container_width=True):
            st.markdown("### In plain English")
            st.markdown(definition)
            if guide_key in METRIC_PREREQUISITES:
                st.markdown("### Terms to know first")
                for term, explanation in METRIC_PREREQUISITES[guide_key]:
                    st.markdown(f"**{term}** — {explanation}")
            st.markdown("**Formula in normal terms**")
            if guide_key in FRIENDLY_LATEX:
                st.latex(FRIENDLY_LATEX[guide_key])
            else:
                render_plain_formula(FORMULA_PLAIN[guide_key])
            with st.expander("Show compact mathematical notation"):
                st.latex(FORMULA_LATEX[guide_key])
                st.markdown(f"**What the symbols mean**  \n{FORMULA_TERMS[guide_key]}")
            if guide_key == "RSI 14":
                render_rsi_gain_loss_steps()
            st.markdown(f"**Simple example**  \n{METRIC_EXAMPLES[guide_key]}")
            st.markdown(f"**How to use it**  \n{significance}")
            st.warning(f"Common beginner mistake: {METRIC_MISTAKES[guide_key]}")


def style_figure(chart):
    chart.update_layout(
        paper_bgcolor="#070d17", plot_bgcolor="#070d17",
        font=dict(color="#dbeafe", family="IBM Plex Mono, Cascadia Code, Consolas, monospace"),
        hoverlabel=dict(bgcolor="#07111f", bordercolor="#22d3ee", font=dict(color="#f8fafc", size=13, family="Cascadia Code, Consolas, monospace")),
        xaxis=dict(gridcolor="rgba(148,163,184,.20)", zerolinecolor="rgba(148,163,184,.28)"),
        yaxis=dict(gridcolor="rgba(148,163,184,.20)", zerolinecolor="rgba(148,163,184,.28)"),
    )
    return chart


def render_methodology_page() -> None:
    st.title("Learn the Methods")
    st.markdown(
        '<p class="subtitle">A beginner-first reference for every price and risk calculation used by QuantDash.</p>',
        unsafe_allow_html=True,
    )
    st.info(
        "Recommended order: begin with Adjusted Close, then Returns, Trend, RSI, and Risk. "
        "Each later idea uses concepts introduced earlier."
    )
    st.markdown(
        """
<nav class="method-toc" aria-label="Methodology table of contents">
  <div class="method-toc__eyebrow">TABLE OF CONTENTS</div>
  <div class="method-toc__title">Choose a topic</div>
  <div class="method-toc__grid">
    <a href="#adjusted-close"><span>01</span>Adjusted Close<small>Start here</small></a>
    <a href="#returns"><span>02</span>Returns<small>Measure change</small></a>
    <a href="#trend"><span>03</span>SMA 20 / 50<small>Read trend</small></a>
    <a href="#rsi"><span>04</span>RSI 14<small>Read momentum</small></a>
    <a href="#risk"><span>05</span>Risk<small>Volatility & drawdown</small></a>
    <a href="#notation"><span>06</span>Notation<small>Formula reference</small></a>
  </div>
</nav>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div id="adjusted-close" class="method-anchor"></div>', unsafe_allow_html=True)
    st.markdown("## ① Price basis: Adjusted Close")
    st.markdown(
        "A normal closing price is the final quoted price for one trading day. Historical comparisons become misleading when a company "
        "splits its shares or pays a cash dividend. Adjusted Close restates older prices so those corporate actions do not look like sudden investment losses."
    )
    render_plain_formula(FORMULA_PLAIN["Adjusted close"])
    st.markdown(f"**Example:** {METRIC_EXAMPLES['Adjusted close']}")
    st.warning(METRIC_MISTAKES["Adjusted close"])

    st.markdown('<div id="returns" class="method-anchor"></div>', unsafe_allow_html=True)
    st.markdown("## ② Returns: turn prices into comparable changes")
    st.markdown("Return answers: ‘How much did the investment value change relative to where it started?’")
    render_plain_formula("Simple Return = Today’s Adjusted Close ÷ Previous Day’s Adjusted Close − 1")
    render_plain_formula("Log Return = natural log of (Today’s Adjusted Close ÷ Previous Day’s Adjusted Close)")
    st.markdown("A move from 100 USD to 103 USD gives a simple return of 3%. QuantDash uses log returns inside volatility calculations.")
    st.warning("The first observation has no previous price, so its return is missing—not zero.")

    st.markdown('<div id="trend" class="method-anchor"></div>', unsafe_allow_html=True)
    st.markdown("## ③ Trend: SMA 20 and SMA 50")
    render_plain_formula("SMA 20 = (Adjusted Close Day 1 + Day 2 + Day 3 + … + Day 20) ÷ 20")
    render_plain_formula("SMA 50 = (Adjusted Close Day 1 + Day 2 + Day 3 + … + Day 50) ÷ 50")
    st.markdown("SMA 20 reacts faster to recent prices. SMA 50 changes more slowly. Both summarize past adjusted prices and therefore lag the market.")

    st.markdown('<div id="rsi" class="method-anchor"></div>', unsafe_allow_html=True)
    st.markdown("## ④ Momentum: Wilder RSI 14")
    st.latex(FRIENDLY_LATEX["RSI 14"])
    render_rsi_gain_loss_steps()
    st.warning(METRIC_MISTAKES["RSI 14"])

    st.markdown('<div id="risk" class="method-anchor"></div>', unsafe_allow_html=True)
    st.markdown("## ⑤ Risk: volatility and drawdown")
    st.markdown("### 20D annualized volatility")
    render_plain_formula("1) Calculate 20 daily log returns → 2) measure how spread out they are → 3) multiply by √252")
    render_plain_formula("Daily spread = √{[(Day 1 Return − Average)² + … + (Day 20 Return − Average)²] ÷ 19}")
    st.markdown(f"**Example:** {METRIC_EXAMPLES['20D annualized volatility']}")
    st.warning(METRIC_MISTAKES["20D annualized volatility"])
    st.markdown("### Maximum drawdown")
    render_plain_formula(FORMULA_PLAIN["Max drawdown"])
    st.markdown(f"**Example:** {METRIC_EXAMPLES['Max drawdown']}")
    st.warning(METRIC_MISTAKES["Max drawdown"])

    st.markdown('<div id="notation" class="method-anchor"></div>', unsafe_allow_html=True)
    with st.expander("Compact mathematical notation reference"):
        for key in ["Adjusted close", "RSI 14", "20D annualized volatility", "Max drawdown"]:
            st.markdown(f"**{key}**")
            st.latex(FORMULA_LATEX[key])
            st.caption(FORMULA_TERMS[key])


@st.cache_data
def load_data():
    return build_screener(Path(__file__).parent / "data")


try:
    screener, history = load_data()
except FileNotFoundError:
    st.error("Processed data is missing. Run the data and feature build commands in README.md first.")
    st.stop()

st.title("QuantDash")
st.markdown('<p class="subtitle">A guided, evidence-based stock research workflow for beginners.</p>', unsafe_allow_html=True)

navigation = st.radio(
    "Main navigation", ["Research Dashboard", "Learn the Methods"],
    horizontal=True, label_visibility="collapsed", key="main_navigation",
)
if navigation == "Learn the Methods":
    render_methodology_page()
    st.stop()

with st.expander("New here? Start with this 60-second guide"):
    st.markdown("""
1. **Screen:** narrow the 20-stock universe using a few criteria you understand.
2. **Compare:** inspect the signal map; relative position is context, not a recommendation.
3. **Research:** choose one ticker and review business, fundamentals, valuation, price, and risk.
4. **Form a view:** use the evidence summary to record strengths, cautions, and missing information.

Start broad, add one filter at a time, and never treat a missing value as zero. QuantDash is an educational research tool—not investment advice.
""")

st.markdown(
    '<div class="research-path">RESEARCH PATH <span>//</span> ① SCREEN <span>→</span> '
    '② COMPARE <span>→</span> ③ UNDERSTAND <span>→</span> ④ FORM A VIEW</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Filters")
    def reset_filters():
        for key in list(st.session_state):
            if key.startswith("filter_") or key in {"search", "rsi_range", "max_volatility", "trend", "include_benchmark"}:
                del st.session_state[key]

    st.button("Reset filters", on_click=reset_filters, width="stretch")
    st.caption("Edit freely—results update only when you press Apply filters.")
    with st.form("screener_filter_form", border=False):
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
            value = st.number_input(label, low, high, default, key=f"filter_value_{column}")
            if enabled:
                numeric_filters[column] = (operator, value)

        label_options = ["Strong", "Positive", "Neutral", "Weak", "Very Weak"]
        st.markdown("**Overall signal**")
        with st.container(border=True):
            signal_columns = st.columns(2)
            selected_labels = [
                label for index, label in enumerate(label_options)
                if signal_columns[index % 2].checkbox(label, value=True, key=f"filter_signal_{label.lower().replace(' ', '_')}")
            ]
            st.caption(f"{len(selected_labels)} of {len(label_options)} signal groups selected")
        apply_filters = st.form_submit_button("Apply filters", type="primary", use_container_width=True)
    if apply_filters:
        st.success("Filters applied to the screener, signal map, and ticker shortlist.")
    st.caption("Latest market data: " + screener.date.max().strftime("%Y-%m-%d"))

filtered = filter_screener(
    screener, search, rsi_range, max_volatility, trend, include_benchmark,
    numeric_filters=numeric_filters,
    signal_labels=None if selected_labels == label_options else selected_labels,
    sort_by="composite_score", ascending=False,
)

col1, col2, col3, col4 = st.columns(4)
render_stat(col1, "Stocks shown", f"{len(filtered)} / {int((~screener.symbol.eq('SPY')).sum())}", "Stocks shown")
render_stat(col2, "Bullish", str(int(filtered.signal.eq("Bullish").sum())), "Bullish")
render_stat(col3, "Median RSI", f"{filtered.rsi_14.median():.1f}" if len(filtered) else "—", "Median RSI")
render_stat(col4, "Median volatility", f"{filtered.volatility_pct.median():.1f}%" if len(filtered) else "—", "Median volatility")

st.subheader("① Screen: find candidates")
st.caption("Use filters to create a research shortlist. A high score is a starting point, not a conclusion.")
with st.expander("What should I filter first?"):
    st.markdown("""
- **Momentum 3M:** recent adjusted-price performance over 63 trading observations.
- **Profit margin:** profit retained per dollar of revenue; compare alongside growth quality.
- **P/E:** price paid per dollar of earnings; lower is not automatically better.
- **Beta:** historical sensitivity to SPY; it describes risk and is excluded from attractiveness score.
- **Composite score:** relative ranking across this small 20-stock universe; inspect its coverage and component labels.
""")
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

st.subheader("② Compare: RSI vs P/E signal map")
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
    figure.update_traces(
        hovertemplate=("<b>%{hovertext}</b><br>P/E %{x:.1f}<br>RSI %{y:.1f}"
                       "<br>Composite %{marker.size:.1f}<extra></extra>")
    )
    style_figure(figure)
    st.plotly_chart(figure, width="stretch")
    st.caption(
        "Bubble size represents composite score. RSI and P/E are descriptive axes; "
        "the map is a relative comparison of the W2-15 subset, not a buy/sell recommendation."
    )

st.subheader("③ Understand: guided ticker research")
available = filtered.symbol.tolist() or screener.symbol.tolist()
detail_controls = st.columns([2, 1])
selected = detail_controls[0].selectbox("Select ticker", available)
timeframe = detail_controls[1].selectbox("Timeframe", ["3M", "6M", "1Y", "2Y"], index=2)
detail = screener[screener.symbol.eq(selected)].iloc[0]
research_summary = build_research_summary(detail, screener)
context_details = research_summary.get("context_details")
if context_details is None:
    # Streamlit can hot-reload app.py while retaining an older imported helper
    # module. Keep the page usable until the server completes a clean restart.
    def legacy_context(label, value, text, suffix=""):
        numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        return {
            "label": label,
            "value": "N/A" if pd.isna(numeric) else f"{numeric:.1f}{suffix}",
            "status": "Context",
            "peer_position": text,
            "meaning": "Refresh after the application update to load the structured interpretation.",
        }

    context_details = {
        "valuation": legacy_context("P/E", detail.get("pe_ratio_raw"), research_summary["contexts"]["valuation"]),
        "profitability": legacy_context("Profit margin %", detail.get("profit_margin_raw_pct"), research_summary["contexts"]["profitability"], "%"),
        "momentum": legacy_context("RSI 14", detail.get("rsi_14"), research_summary["contexts"]["momentum"]),
        "risk": legacy_context("20D annualized volatility %", detail.get("volatility_pct"), research_summary["contexts"]["risk"], "%"),
    }
deep_dive = prepare_deep_dive(history, selected, timeframe)
latest_deep_dive = deep_dive.iloc[-1]
d1, d2, d3, d4 = st.columns(4)
render_stat(d1, "Adjusted close", f"${latest_deep_dive.adjusted_close:,.2f}", "Adjusted close", f"1D Δ {detail.daily_return_pct:+.2f}%")
render_stat(d2, "RSI 14", f"{detail.rsi_14:.1f}", "RSI 14")
render_stat(d3, "20D annualized volatility", f"{latest_deep_dive.volatility_20d_annualized_pct:.1f}%", "20D annualized volatility")
render_stat(d4, f"{timeframe} max drawdown", f"{deep_dive.timeframe_drawdown_pct.min():.1f}%", "Max drawdown")

st.markdown("##### How to interpret the current snapshot")
context_items = [
    ("VALUATION // P/E", context_details["valuation"]),
    ("QUALITY // MARGIN", context_details["profitability"]),
    ("MOMENTUM // RSI", context_details["momentum"]),
    ("RISK // VOLATILITY", context_details["risk"]),
]
context_html = "".join(
    f'<div class="context-node"><div class="context-key">{escape(key)}</div>'
    f'<div class="context-reading"><span class="context-number">{escape(item["value"])}</span>'
    f'<span class="context-status">{escape(item["status"])}</span></div>'
    f'<div class="context-headline">Peer position</div><div class="context-copy">{escape(item["peer_position"])}</div>'
    f'<div class="context-headline">What it means</div><div class="context-copy">{escape(item["meaning"])}</div></div>'
    for key, item in context_items
)
st.markdown(f'<div class="context-board">{context_html}</div>', unsafe_allow_html=True)
st.caption("High/low descriptions are cross-sectional comparisons with the current 20-stock universe, not the company’s historical range.")

price_chart_data = deep_dive.rename(columns={
    "adjusted_close": "Adjusted Close", "sma_20": "SMA 20", "sma_50": "SMA 50",
})
price_figure = px.line(
    price_chart_data, x="date", y=["Adjusted Close", "SMA 20", "SMA 50"],
    labels={"value": "Adjusted price ($)", "variable": "Series", "date": "Date"},
)
price_figure.update_layout(height=390, margin=dict(l=20, r=20, t=20, b=20))
style_figure(price_figure)
st.plotly_chart(price_figure, width="stretch")
with st.expander("ⓘ Understand the price chart and its series"):
    st.markdown("**Adjusted Close**")
    render_plain_formula(FORMULA_PLAIN["Adjusted close"])
    st.markdown(
        "The provider restates historical close prices for stock splits and cash dividends. "
        "This makes returns across time more comparable than raw close. It is the price basis for all three lines."
    )
    series_cols = st.columns(2)
    with series_cols[0]:
        st.markdown("**SMA 20**")
        render_plain_formula("SMA 20 = (Adjusted Close Day 1 + Day 2 + Day 3 + … + Day 20) ÷ 20")
        st.caption("Shorter trend: the arithmetic mean of 20 adjusted closes.")
    with series_cols[1]:
        st.markdown("**SMA 50**")
        render_plain_formula("SMA 50 = (Adjusted Close Day 1 + Day 2 + Day 3 + … + Day 50) ÷ 50")
        st.caption("Slower trend: the arithmetic mean of 50 adjusted closes.")
    st.markdown("**Compact mathematical notation (optional)**")
    st.latex(r"P_t^{adj}=P_t^{raw}\times A_t^{split}\times A_t^{dividend}")
    st.latex(r"SMA_{N,t}=\frac{1}{N}\sum_{i=0}^{N-1}P_{t-i}^{adj}")
    st.warning(
        "Adjusted Close is a historical analytical series. It may differ from the raw closing quote shown by another website, "
        "especially around dividends or stock splits."
    )

if selected != "SPY":
    comparison, comparison_summary = prepare_benchmark_comparison(history, selected, timeframe)
    st.markdown(f"#### {selected} vs SPY · {timeframe}")
    market_cols = st.columns(4)
    render_stat(market_cols[0], f"{selected} return", f"{comparison_summary['stock_return']:+.1%}", "Stock return")
    render_stat(market_cols[1], "SPY return", f"{comparison_summary['benchmark_return']:+.1%}", "SPY return")
    render_stat(market_cols[2], "Excess return", f"{comparison_summary['excess_return_pp']:+.1f} pp", "Excess return")
    render_stat(market_cols[3], "Common dates", str(comparison_summary["common_observations"]), "Common dates")
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
    style_figure(comparison_figure)
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

if False:  # Methodology moved to the dedicated Learn the Methods navigation page.
    st.markdown("### Start here: what is being calculated?")
    st.markdown(
        "Every price-derived measure begins with **Adjusted Close**. The provider modifies historical prices for "
        "stock splits and cash dividends so corporate actions do not appear as artificial investment gains or losses. "
        "Indicators are calculated separately for each ticker and in chronological trading-date order."
    )
    method_tabs = st.tabs(["Price basis", "Returns", "Trend", "RSI", "Risk"])
    with method_tabs[0]:
        st.markdown("#### Adjusted Close")
        render_plain_formula(FORMULA_PLAIN["Adjusted close"])
        st.markdown("**Compact mathematical notation (optional)**")
        st.latex(FORMULA_LATEX["Adjusted close"])
        st.markdown(f"**Symbols:** {FORMULA_TERMS['Adjusted close']}")
        st.markdown(f"**Example:** {METRIC_EXAMPLES['Adjusted close']}")
        st.warning(METRIC_MISTAKES["Adjusted close"])
    with method_tabs[1]:
        st.markdown("#### Daily returns")
        st.markdown("A return expresses the price change relative to the previous trading observation, making different dollar-priced stocks comparable.")
        render_plain_formula("Simple Return = Today’s Adjusted Close ÷ Previous Day’s Adjusted Close − 1")
        render_plain_formula("Log Return = natural log of (Today’s Adjusted Close ÷ Previous Day’s Adjusted Close)")
        st.markdown("**Compact mathematical notation (optional)**")
        st.latex(r"R_t^{simple}=\frac{P_t^{adj}}{P_{t-1}^{adj}}-1")
        st.latex(r"r_t^{log}=\ln\left(\frac{P_t^{adj}}{P_{t-1}^{adj}}\right)")
        st.markdown("**Simple return** is intuitive for one-period performance. **Log return** is used for volatility because consecutive log returns add cleanly through time.")
        st.markdown("**Example:** a move from 100 USD to 103 USD produces a simple return of 103 ÷ 100 − 1 = 3%.")
        st.warning("The first observation has no previous price, so its return is correctly missing—not zero.")
    with method_tabs[2]:
        st.markdown("#### Moving averages: SMA 20 and SMA 50")
        render_plain_formula("SMA 20 = (Adjusted Close Day 1 + Day 2 + Day 3 + … + Day 20) ÷ 20")
        render_plain_formula("SMA 50 = (Adjusted Close Day 1 + Day 2 + Day 3 + … + Day 50) ÷ 50")
        st.markdown("**Compact mathematical notation (optional)**")
        st.latex(r"SMA_{N,t}=\frac{1}{N}\sum_{i=0}^{N-1}P_{t-i}^{adj}")
        st.markdown("`N` is the number of trading observations. SMA 20 reacts faster; SMA 50 is smoother and describes a slower trend.")
        st.markdown("**Example:** if the latest 20 adjusted closes average 120 USD, SMA 20 is 120 USD regardless of today’s raw closing quote.")
        st.warning("A moving average follows price with a delay. A crossover confirms past movement; it does not guarantee the next move.")
    with method_tabs[3]:
        st.markdown("#### Wilder RSI 14")
        render_plain_formula(FORMULA_PLAIN["RSI 14"])
        st.markdown("**Compact mathematical notation (optional)**")
        st.latex(FORMULA_LATEX["RSI 14"])
        st.markdown(f"**Symbols:** {FORMULA_TERMS['RSI 14']}")
        render_rsi_gain_loss_steps()
        st.markdown(f"**Example:** {METRIC_EXAMPLES['RSI 14']}")
        st.warning(METRIC_MISTAKES["RSI 14"])
    with method_tabs[4]:
        st.markdown("#### 20D annualized volatility")
        render_plain_formula("1) Calculate 20 daily log returns → 2) measure how spread out those 20 returns are → 3) multiply by √252")
        st.markdown("In expanded terms, the daily spread uses each return’s distance from the 20-day average:")
        render_plain_formula("Daily spread = √{[(Return Day 1 − Average Return)² + … + (Return Day 20 − Average Return)²] ÷ 19}")
        render_plain_formula("20D Annualized Volatility = Daily spread × √252")
        st.markdown("**Compact mathematical notation (optional)**")
        st.latex(FORMULA_LATEX["20D annualized volatility"])
        st.markdown(f"**Symbols:** {FORMULA_TERMS['20D annualized volatility']}")
        st.markdown(f"**Example:** {METRIC_EXAMPLES['20D annualized volatility']}")
        st.warning(METRIC_MISTAKES["20D annualized volatility"])
        st.markdown("#### Timeframe maximum drawdown")
        render_plain_formula(FORMULA_PLAIN["Max drawdown"])
        st.markdown("**Compact mathematical notation (optional)**")
        st.latex(FORMULA_LATEX["Max drawdown"])
        st.markdown(f"**Symbols:** {FORMULA_TERMS['Max drawdown']}")
        st.markdown(f"**Example:** {METRIC_EXAMPLES['Max drawdown']}")
        st.warning(METRIC_MISTAKES["Max drawdown"])
    st.info(
        "Warm-up policy: rolling indicators are calculated on the full available history before the selected 3M/6M/1Y/2Y chart window is applied. "
        "This prevents the first visible points from losing valid earlier observations. Timeframe drawdown is the exception: its peak intentionally resets at the start of the selected window."
    )

st.subheader("④ Form a view: evidence summary")
st.markdown(f"**Overall signal:** {research_summary['overall']}")
evidence_cols = st.columns(3)
with evidence_cols[0]:
    st.markdown("**Supporting evidence**")
    if research_summary["strengths"]:
        for item in research_summary["strengths"]:
            st.markdown(f"- {item}")
    else:
        st.caption("No component is currently labeled Strong or Positive.")
with evidence_cols[1]:
    st.markdown("**Cautions**")
    if research_summary["cautions"]:
        for item in research_summary["cautions"]:
            st.markdown(f"- {item}")
    else:
        st.caption("No rule-based caution was triggered; qualitative risks still require research.")
with evidence_cols[2]:
    st.markdown("**Information gaps**")
    if research_summary["data_gaps"]:
        for item in research_summary["data_gaps"]:
            st.markdown(f"- {item}")
    else:
        st.caption("All intended quantitative components are available.")

st.info(research_summary["conclusion_prompt"])
with st.expander("Research checklist before forming an opinion"):
    checklist_cols = st.columns(2)
    checklist_cols[0].checkbox("I understand how the company makes money", key=f"guided_business_{selected}")
    checklist_cols[0].checkbox("I reviewed growth and profitability", key=f"guided_fundamentals_{selected}")
    checklist_cols[1].checkbox("I reviewed valuation and its trade-offs", key=f"guided_valuation_{selected}")
    checklist_cols[1].checkbox("I reviewed price, risk, SPY comparison, and data gaps", key=f"guided_risk_{selected}")
    st.caption("The checklist structures research; checking a box does not validate the investment thesis.")
st.caption(
    "Educational prototype—not investment advice. Price-derived metrics use split-and-dividend-adjusted close. "
    "SEC metrics may represent different fiscal periods; provenance remains in the processed dataset."
)
