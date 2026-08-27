import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  BookOpen,
  ChevronRight,
  CircleHelp,
  Download,
  Eye,
  Filter,
  Info,
  Minimize2,
  Plus,
  RotateCcw,
  Search,
  SlidersHorizontal,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import "./styles.css";
import Simulation from "./Simulation";
const pct = (v, d = 1) =>
    v == null ? "N/A" : `${v >= 0 ? "+" : ""}${Number(v).toFixed(d)}%`,
  num = (v, d = 1) => (v == null ? "N/A" : Number(v).toFixed(d)),
  tone = (v = "") => v.toLowerCase().replaceAll(" ", "-"),
  clamp = (value, low, high) => Math.max(low, Math.min(high, value));
const tfDays = { "3M": 92, "6M": 183, "1Y": 366, "2Y": 732 };
const fields = {
  composite_score: ["Composite score", 0, 100, 1],
  momentum_21d_raw_pct: ["Momentum 1M %", -100, 200, 1],
  momentum_63d_raw_pct: ["Momentum 3M %", -100, 200, 1],
  momentum_126d_raw_pct: ["Momentum 6M %", -100, 400, 1],
  profit_margin_raw_pct: ["Profit margin %", -100, 100, 1],
  revenue_growth_yoy_raw_pct: ["Revenue growth YoY %", -100, 200, 1],
  pe_ratio_raw: ["P/E", -100, 400, 1],
  beta_252_raw: ["Beta 252D", -2, 5, 0.1],
  rsi_14: ["RSI 14", 0, 100, 1],
  volatility_pct: ["20D volatility %", 0, 200, 1],
  max_drawdown_pct: ["Maximum drawdown %", -100, 0, 1],
  momentum_subscore: ["Momentum sub-score", 0, 100, 1],
  quality_subscore: ["Fundamentals sub-score", 0, 100, 1],
  valuation_subscore: ["Valuation sub-score", 0, 100, 1],
  score_coverage: ["Score coverage", 0, 1, 0.05],
};
const cols = {
  rank: "Rank",
  symbol: "Ticker",
  company_name: "Company",
  adjusted_close: "Adjusted close",
  daily_return_pct: "Daily return",
  momentum_21d_raw_pct: "Momentum 1M",
  momentum_63d_raw_pct: "Momentum 3M",
  momentum_126d_raw_pct: "Momentum 6M",
  profit_margin_raw_pct: "Margin",
  revenue_growth_yoy_raw_pct: "Revenue growth YoY",
  pe_ratio_raw: "P/E",
  beta_252_raw: "Beta",
  rsi_14: "RSI 14",
  volatility_pct: "Volatility 20D",
  max_drawdown_pct: "Max drawdown",
  momentum_subscore: "Momentum score",
  quality_subscore: "Fundamentals score",
  valuation_subscore: "Valuation score",
  composite_score: "Score",
  score_coverage: "Coverage",
  overall_label: "Signal",
};
const baseCols = [
  "rank",
  "symbol",
  "company_name",
  "momentum_63d_raw_pct",
  "profit_margin_raw_pct",
  "pe_ratio_raw",
  "composite_score",
  "overall_label",
];
const METHODS = [
  {
    id: "adjusted",
    n: "01",
    title: "Adjusted Close",
    tag: "Price basis",
    text: "Historical close corrected for splits and cash dividends. It prevents corporate actions from looking like investment gains or losses.",
    formula:
      "Adjusted Close = Raw Close × Split Adjustment × Dividend Adjustment",
  },
  {
    id: "returns",
    n: "02",
    title: "Returns",
    tag: "Comparable change",
    text: "Return measures change relative to a starting value. Missing prior prices remain missing—not zero.",
    formula: "Return = Today’s Adjusted Close ÷ Previous Adjusted Close − 1",
  },
  {
    id: "trend",
    n: "03",
    title: "SMA 20 / 50",
    tag: "Trend",
    text: "A simple moving average smooths noise by averaging recent adjusted closes. It describes past prices and lags the market.",
    formula: "SMA 20 = (Day 1 + Day 2 + … + Day 20) ÷ 20",
  },
  {
    id: "rsi",
    n: "04",
    title: "RSI 14",
    tag: "Momentum",
    text: "RSI compares Wilder-smoothed gains and losses over 14 trading observations. The 30 and 70 zones are context, not commands.",
    formula: "RSI = 100 − [100 ÷ (1 + Average Gain ÷ Average Loss)]",
  },
  {
    id: "risk",
    n: "05",
    title: "Volatility",
    tag: "Range of outcomes",
    text: "Annualized volatility estimates dispersion in recent daily returns. Higher means wider variation, not necessarily a worse company.",
    formula: "20D Volatility = standard deviation of 20 log returns × √252",
  },
  {
    id: "drawdown",
    n: "06",
    title: "Drawdown",
    tag: "Peak-to-trough",
    text: "Drawdown compares adjusted close to the earlier peak inside the chosen window.",
    formula: "Drawdown = Current Adjusted Close ÷ Previous Peak − 1",
  },
  {
    id: "scores",
    n: "07",
    title: "Scores & coverage",
    tag: "Relative evidence",
    text: "Sub-scores are percentile comparisons inside this small universe. Coverage reports how much intended information was available.",
    formula: "Composite = weighted available sub-scores ÷ available weight",
  },
  {
    id: "momentum",
    n: "08",
    title: "3-month momentum",
    tag: "Recent performance",
    text: "Compares today's adjusted close with the adjusted close 63 trading observations earlier. Positive momentum means price rose over that window; it does not guarantee another rise.",
    formula: "Momentum 3M = Today ÷ Adjusted Close 63 observations ago − 1",
  },
  {
    id: "valuation",
    n: "09",
    title: "P/E and valuation score",
    tag: "Price paid for earnings",
    text: "P/E estimates how many dollars investors pay for one dollar of trailing earnings. Nonpositive earnings make the ratio unsuitable for this comparison. Lower P/E receives a higher relative valuation score, but cheap is not automatically good.",
    formula: "P/E = Share Price ÷ Earnings per Share",
  },
  {
    id: "quality",
    n: "10",
    title: "Growth and profit margin",
    tag: "Fundamental quality",
    text: "YoY growth compares revenue with the same quarter one year earlier. Profit margin estimates how much profit remains from each dollar of revenue. Both use SEC facts available by the decision date.",
    formula: "Profit Margin = Same-period Net Income ÷ Revenue",
  },
  {
    id: "beta",
    n: "11",
    title: "Beta 252D",
    tag: "Market sensitivity",
    text: "Beta describes how a stock historically moved with SPY across 252 aligned trading returns. It is risk context, not a component of attractiveness score, and high or low is not automatically better.",
    formula:
      "Beta = Covariance(Stock Return, SPY Return) ÷ Variance(SPY Return)",
  },
];
function Metric({ label, value, meta, t = "cyan", help }) {
  return (
    <article className={`metric-card ${t}`}>
      <div className="metric-scan" />
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{meta}</small>
      {help && (
        <button className="card-help" onClick={help}>
          <CircleHelp />
        </button>
      )}
    </article>
  );
}

function RsiFormula() {
  return (
    <div
      className="math-card"
      role="img"
      aria-label="RSI equals 100 minus 100 divided by 1 plus Average Gain divided by Average Loss"
    >
      <span className="math-name">RSI</span>
      <span className="math-op">=</span>
      <span>100</span>
      <span className="math-op">−</span>
      <span className="fraction fraction-outer">
        <span className="numerator">100</span>
        <span className="denominator">
          <span>1</span>
          <span className="math-op">+</span>
          <span className="fraction fraction-inner">
            <span className="numerator">Average Gain</span>
            <span className="denominator">Average Loss</span>
          </span>
        </span>
      </span>
    </div>
  );
}

function FormulaDisplay({ method }) {
  return method.id === "rsi" ? (
    <RsiFormula />
  ) : (
    <div className="formula">{method.formula}</div>
  );
}
function SvgLines({ series, hoverIndex, labels = [], unit = "", h = 320 }) {
  const all = series.flatMap((s) => s.v.filter((x) => x != null));
  if (!all.length)
    return <div className="empty">Insufficient observations.</div>;
  const rawMin = Math.min(...all),
    rawMax = Math.max(...all),
    padding = Math.max((rawMax - rawMin) * 0.08, Math.abs(rawMax || 1) * 0.01),
    min = rawMin - padding,
    max = rawMax + padding,
    span = max - min || 1,
    left = 90,
    right = 980,
    top = 16,
    bottom = h - 42,
    y = (value) => bottom - ((value - min) / span) * (bottom - top),
    x = (index, length) =>
      left + (index / Math.max(length - 1, 1)) * (right - left),
    p = (v) =>
      v
        .map((x, i) =>
          x == null
            ? null
            : `${left + (i / Math.max(v.length - 1, 1)) * (right - left)},${y(x)}`,
        )
        .filter(Boolean)
        .join(" "),
    ticks = Array.from({ length: 5 }, (_, index) => min + (span * index) / 4),
    longest = Math.max(...series.map((item) => item.v.length)),
    hoverX = hoverIndex == null ? null : x(hoverIndex, longest),
    allMonthTicks = labels
      .map((label, index) => {
        const date = new Date(`${label}T00:00:00`);
        const previous = index
          ? new Date(`${labels[index - 1]}T00:00:00`)
          : null;
        return !Number.isNaN(date.valueOf()) &&
          (!previous ||
            date.getMonth() !== previous.getMonth() ||
            date.getFullYear() !== previous.getFullYear())
          ? {
              index,
              text: date.toLocaleDateString("en-US", {
                month: "short",
                year: "2-digit",
              }),
            }
          : null;
      })
      .filter(Boolean),
    monthStep = Math.max(1, Math.ceil(allMonthTicks.length / 8)),
    monthTicks = allMonthTicks.filter((_, index) => index % monthStep === 0);
  return (
    <svg viewBox={`0 0 1000 ${h}`} preserveAspectRatio="xMidYMid meet">
      <g className="grid">
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={left} y1={y(tick)} x2={right} y2={y(tick)} />
            <text
              className="chart-axis-value"
              x={left - 10}
              y={y(tick) + 4}
              textAnchor="end"
            >
              {unit === "$" ? "$" : ""}
              {Math.abs(tick) >= 1000
                ? tick.toLocaleString(undefined, { maximumFractionDigits: 0 })
                : tick.toFixed(Math.abs(span) < 10 ? 1 : 0)}
              {unit === "$" ? "" : unit}
            </text>
          </g>
        ))}
      </g>
      {series.map((s, i) => (
        <polyline
          key={s.n}
          points={p(s.v)}
          fill="none"
          stroke={s.c || ["#7ddcff", "#537fff", "#ffaaa7"][i]}
          strokeWidth="2.4"
          vectorEffect="non-scaling-stroke"
        />
      ))}
      <g className="chart-month-axis">
        {monthTicks.map((tick) => (
          <g key={`${tick.index}-${tick.text}`}>
            <line
              x1={x(tick.index, longest)}
              y1={bottom}
              x2={x(tick.index, longest)}
              y2={bottom + 5}
            />
            <text
              x={x(tick.index, longest)}
              y={bottom + 22}
              textAnchor="middle"
            >
              {tick.text}
            </text>
          </g>
        ))}
      </g>
      {hoverX != null && (
        <g className="chart-hover-marks">
          <line x1={hoverX} y1={top} x2={hoverX} y2={bottom} />
          {series.map((item, index) => {
            const value = item.v[hoverIndex];
            return value == null ? null : (
              <circle
                key={item.n}
                cx={x(hoverIndex, item.v.length)}
                cy={y(value)}
                r="5"
                fill={item.c || ["#7ddcff", "#537fff", "#ffaaa7"][index]}
              />
            );
          })}
        </g>
      )}
    </svg>
  );
}
function Chart({ title, kicker, series, labels = [], unit = "" }) {
  const [hoverIndex, setHoverIndex] = useState(null);
  const length = Math.max(...series.map((item) => item.v.length));
  const inspect = (event) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const ratio = clamp(
      (event.clientX - bounds.left) / bounds.width,
      0.07,
      0.98,
    );
    setHoverIndex(
      Math.round(((ratio - 0.07) / 0.91) * Math.max(length - 1, 0)),
    );
  };
  const display = (value) =>
    value == null
      ? "N/A"
      : `${unit === "$" ? "$" : ""}${Number(value).toFixed(unit === "$" ? 2 : 1)}${unit === "$" ? "" : unit}`;
  return (
    <div className="chart-shell">
      <div className="chart-head">
        <div>
          <span>{kicker}</span>
          <h3>{title}</h3>
        </div>
        <div className="legend">
          {series.map((s) => (
            <span key={s.n}>
              <i style={{ background: s.c }} />
              {s.n}
            </span>
          ))}
        </div>
      </div>
      <div
        className="interactive-plot"
        onMouseMove={inspect}
        onMouseLeave={() => setHoverIndex(null)}
      >
        <SvgLines
          series={series}
          hoverIndex={hoverIndex}
          labels={labels}
          unit={unit}
        />
        {hoverIndex != null && (
          <div
            className="chart-tooltip"
            style={{
              left: `${7 + (hoverIndex / Math.max(length - 1, 1)) * 91}%`,
            }}
          >
            <b>{labels[hoverIndex] || `Observation ${hoverIndex + 1}`}</b>
            {series.map((item) => (
              <span key={item.n}>
                <i style={{ background: item.c }} />
                {item.n}
                <strong>{display(item.v[hoverIndex])}</strong>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
function SignalMap({ stocks, onPick }) {
  const valid = stocks.filter(
      (s) => s.rsi_14 != null && s.pe_ratio_raw != null && s.pe_ratio_raw > 0,
    ),
    unplotted = stocks.filter(
      (s) => s.rsi_14 == null || s.pe_ratio_raw == null || s.pe_ratio_raw <= 0,
    ),
    max = Math.max(...valid.map((s) => s.composite_score || 1), 1),
    sortedPe = valid.map((s) => s.pe_ratio_raw).sort((a, b) => a - b),
    medianPe = sortedPe.length ? sortedPe[Math.floor(sortedPe.length / 2)] : 25,
    peCap = Math.max(50, Math.min(200, Math.max(...sortedPe, 50))),
    dividerY = 390 - (Math.min(medianPe, peCap) / peCap) * 350;
  return (
    <div className="chart-shell signal-map">
      <div className="chart-head">
        <div>
          <span>02 / COMPARE</span>
          <h3>Signal map · RSI vs P/E</h3>
        </div>
        <small>
          {valid.length} plotted · {stocks.length - valid.length} missing
        </small>
      </div>
      <div className="quadrant-layout">
        <svg viewBox="0 0 1000 470">
          <g className="quadrant-zones">
            <rect
              x="60"
              y="40"
              width="455"
              height={dividerY - 40}
              className="q-caution"
            />
            <rect
              x="515"
              y="40"
              width="455"
              height={dividerY - 40}
              className="q-watch"
            />
            <rect
              x="60"
              y={dividerY}
              width="455"
              height={390 - dividerY}
              className="q-defensive"
            />
            <rect
              x="515"
              y={dividerY}
              width="455"
              height={390 - dividerY}
              className="q-balance"
            />
          </g>
          <g className="grid">
            <line x1="60" y1={dividerY} x2="970" y2={dividerY} />
            <line x1="515" y1="40" x2="515" y2="390" />
          </g>
          <text className="quadrant-title" x="80" y="68">
            HIGHER P/E · COOLER RSI
          </text>
          <text className="quadrant-title" x="535" y="68">
            HIGHER P/E · STRONGER RSI
          </text>
          <text className="quadrant-title" x="80" y="374">
            LOWER P/E · COOLER RSI
          </text>
          <text className="quadrant-title" x="535" y="374">
            LOWER P/E · STRONGER RSI
          </text>
          {valid.map((s) => {
            const x = 60 + (Math.max(0, Math.min(100, s.rsi_14)) / 100) * 910,
              pe = Math.max(0, Math.min(peCap, s.pe_ratio_raw)),
              y = 390 - (pe / peCap) * 350,
              r = 7 + ((s.composite_score || 0) / max) * 14;
            return (
              <g
                key={s.symbol}
                onClick={() => onPick(s.symbol)}
                className="bubble"
              >
                <circle
                  cx={x}
                  cy={y}
                  r={r}
                  fill={
                    ["Strong", "Positive"].includes(s.overall_label)
                      ? "#46e7bc"
                      : "#6b7fff"
                  }
                />
                <text x={x + r + 5} y={y + 4}>
                  {s.symbol}
                </text>
                <title>{`${s.symbol} · RSI ${num(s.rsi_14)} · P/E ${num(s.pe_ratio_raw)}`}</title>
              </g>
            );
          })}
          <text className="axis-label" x="445" y="440">
            RSI 14 · recent momentum →
          </text>
          <text className="axis-label" x="8" y="25">
            P/E · price paid for earnings ↑
          </text>
          <text className="axis-tick" x="60" y="418">
            0
          </text>
          <text className="axis-tick" x="505" y="418">
            50
          </text>
          <text className="axis-tick" x="950" y="418">
            100
          </text>
          <text className="axis-tick" x="65" y={dividerY - 8}>
            Median P/E {num(medianPe)}
          </text>
        </svg>
        <aside className="quadrant-guide">
          <article className="balance">
            <b>LOWER P/E + STRONGER RSI</b>
            <p>
              Cheaper relative valuation with stronger recent price momentum.
              Investigate quality and sustainability.
            </p>
          </article>
          <article className="watch">
            <b>HIGHER P/E + STRONGER RSI</b>
            <p>
              Strong momentum but investors pay more per dollar of earnings.
              Check whether growth supports it.
            </p>
          </article>
          <article className="defensive">
            <b>LOWER P/E + COOLER RSI</b>
            <p>
              Lower valuation with weak momentum. It may be overlooked—or facing
              genuine problems.
            </p>
          </article>
          <article className="caution">
            <b>HIGHER P/E + COOLER RSI</b>
            <p>
              Higher valuation without strong recent momentum. Review downside
              risk and the growth thesis carefully.
            </p>
          </article>
        </aside>
      </div>
      <p className="chart-note">
        RSI compares recent gains and losses on a 0–100 scale; 50 is the neutral
        divider here. P/E is price per dollar of earnings; the horizontal
        divider is this plotted subset’s median. Quadrants organize
        questions—not buy/sell signals. Bubble size represents composite score.
      </p>
      {unplotted.length > 0 && (
        <div className="unplotted-panel">
          <div>
            <span>UNPLOTTED — STILL IN THE SCREENER</span>
            <small>
              A bubble needs both RSI and P/E. No coordinate is invented for a
              missing value.
            </small>
          </div>
          <div className="unplotted-list">
            {unplotted.map((stock) => {
              const missing = [
                stock.rsi_14 == null ? "RSI N/A" : null,
                stock.pe_ratio_raw == null || stock.pe_ratio_raw <= 0
                  ? "P/E not meaningful"
                  : null,
              ].filter(Boolean);
              return (
                <button key={stock.symbol} onClick={() => onPick(stock.symbol)}>
                  <b>{stock.symbol}</b>
                  <span>{missing.join(" · ")}</span>
                  <ChevronRight />
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
function compare(history, symbol, tf) {
  const rows = history[symbol] || [],
    last = Math.max(...rows.map((r) => +new Date(r.date))),
    cut = last - tfDays[tf] * 864e5,
    a = new Map(
      rows
        .filter((r) => +new Date(r.date) >= cut && r.adjusted_close != null)
        .map((r) => [r.date, r.adjusted_close]),
    ),
    b = new Map(
      (history.SPY || [])
        .filter((r) => +new Date(r.date) >= cut && r.adjusted_close != null)
        .map((r) => [r.date, r.adjusted_close]),
    ),
    dates = [...a.keys()].filter((d) => b.has(d)).sort();
  if (dates.length < 2) return null;
  const av = a.get(dates[0]),
    bv = b.get(dates[0]),
    out = dates.map((d) => ({
      date: d,
      stock: (a.get(d) / av) * 100,
      spy: (b.get(d) / bv) * 100,
    }));
  return {
    rows: out,
    stock: out.at(-1).stock - 100,
    spy: out.at(-1).spy - 100,
    excess: out.at(-1).stock - out.at(-1).spy,
    count: out.length,
  };
}
function csv(rows, visible) {
  const body = [
      visible.map((c) => cols[c]).join(","),
      ...rows.map((r, rowIndex) =>
        visible
          .map(
            (c) =>
              `"${String(c === "rank" ? rowIndex + 1 : (r[c] ?? "")).replaceAll('"', '""')}"`,
          )
          .join(","),
      ),
    ].join("\n"),
    a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([body], { type: "text/csv" }));
  a.download = "quantdash-screen.csv";
  a.click();
  URL.revokeObjectURL(a.href);
}
function App() {
  const blank = { search: "", criteria: [], signals: [] };
  const [data, setData] = useState(),
    [loadError, setLoadError] = useState(""),
    [page, setPage] = useState("research"),
    [draft, setDraft] = useState(blank),
    [filters, setFilters] = useState(blank),
    [selected, setSelected] = useState("MSFT"),
    [tf, setTf] = useState("1Y"),
    [visible, setVisible] = useState(baseCols),
    [sort, setSort] = useState("composite_score"),
    [asc, setAsc] = useState(false),
    [goal, setGoal] = useState(""),
    [goalDraft, setGoalDraft] = useState(""),
    [goalAdvice, setGoalAdvice] = useState(""),
    [goalBusy, setGoalBusy] = useState(false),
    [filterOpen, setFilterOpen] = useState(true),
    [help, setHelp] = useState();
  const loadData = () => {
    setLoadError("");
    fetch("/data/dashboard.json", { cache: "default" })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then(setData)
      .catch(() =>
        setLoadError(
          "The prepared market snapshot could not be loaded. Your filters and campaign progress were not changed.",
        ),
      );
  };
  useEffect(loadData, []);
  const universe = data?.stocks?.filter((s) => s.symbol !== "SPY") || [];
  const filtered = useMemo(
    () =>
      universe
        .filter((s) => {
          const q = filters.search.toLowerCase();
          if (
            q &&
            !s.symbol.toLowerCase().includes(q) &&
            !(s.company_name || "").toLowerCase().includes(q)
          )
            return false;
          if (
            filters.signals.length &&
            !filters.signals.includes(s.overall_label)
          )
            return false;
          return filters.criteria.every(
            (c) =>
              s[c.field] != null &&
              (c.op === ">=" ? s[c.field] >= c.value : s[c.field] <= c.value),
          );
        })
        .sort((a, b) => {
          const x = a[sort],
            y = b[sort];
          if (x == null) return 1;
          if (y == null) return -1;
          return (
            (typeof x === "string" ? x.localeCompare(y) : x - y) *
            (asc ? 1 : -1)
          );
        }),
    [universe, filters, sort, asc],
  );
  const spyHistory = data?.history?.SPY || [],
    spyFromHistory = (() => {
      const rows = spyHistory.filter((row) => row.adjusted_close != null);
      if (rows.length < 2) return null;
      const currentPrice = rows.at(-1).adjusted_close;
      const prior = rows[Math.max(0, rows.length - 64)]?.adjusted_close;
      const previous = rows.at(-2)?.adjusted_close;
      return {
        momentum_63d_raw_pct:
          prior > 0 ? (currentPrice / prior - 1) * 100 : null,
        daily_return_pct:
          previous > 0 ? (currentPrice / previous - 1) * 100 : null,
      };
    })(),
    spy = data?.stocks?.find((s) => s.symbol === "SPY") || spyFromHistory,
    positiveMomentum = universe.filter(
      (s) => s.momentum_63d_raw_pct != null && s.momentum_63d_raw_pct > 0,
    ),
    favorable = universe.filter((s) =>
      ["Strong", "Positive"].includes(s.overall_label),
    ),
    outperformingSpy = universe.filter(
      (s) =>
        s.momentum_63d_raw_pct != null &&
        spy?.momentum_63d_raw_pct != null &&
        s.momentum_63d_raw_pct > spy.momentum_63d_raw_pct,
    ),
    marketTrend =
      (spy?.momentum_63d_raw_pct || 0) > 0 && (spy?.daily_return_pct || 0) > 0
        ? "UPTREND"
        : (spy?.momentum_63d_raw_pct || 0) < 0 &&
            (spy?.daily_return_pct || 0) < 0
          ? "DOWNTREND"
          : "MIXED",
    goalText = goal.toLowerCase(),
    goalGuide = !goal.trim()
      ? "Describe your goal and QuantDash will suggest which evidence to inspect first."
      : /income|dividend|cổ tức|thu nhập/.test(goalText)
        ? "Income focus: inspect profit margin, earnings quality, drawdown and valuation. Dividend history is not yet in this dataset, so do not infer income from the score."
        : /safe|stable|ổn định|an toàn|risk|rủi ro/.test(goalText)
          ? "Stability focus: begin with volatility, drawdown and beta, then check fundamentals. A high composite score does not guarantee low risk."
          : /growth|tăng trưởng|long.?term|dài hạn/.test(goalText)
            ? "Growth focus: begin with YoY revenue growth and profit margin, then compare valuation and momentum. High growth does not justify every P/E."
            : /cheap|value|định giá|p\/e/.test(goalText)
              ? "Value focus: inspect positive P/E and valuation score together with growth quality. A low P/E can reflect genuine business risk."
              : "Balanced starting point: compare momentum, fundamentals, valuation and risk separately; use the composite only as a shortlist, not a conclusion.",
    submitGoal = async () => {
      const intent = goalDraft.trim();
      if (!intent) return;
      setGoalBusy(true);
      setGoal(intent);
      try {
        const response = await fetch("/api/intent-advice", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ intent }),
        });
        if (!response.ok) throw new Error("AI service unavailable");
        const result = await response.json();
        setGoalAdvice(result.guidance || "");
      } catch {
        setGoalAdvice("");
      } finally {
        setGoalBusy(false);
      }
    },
    current = universe.find((s) => s.symbol === selected) || universe[0],
    hist = data?.history?.[current?.symbol] || [],
    last = hist.length ? +new Date(hist.at(-1).date) : 0,
    windowRows = hist.filter(
      (r) => +new Date(r.date) >= last - tfDays[tf] * 864e5,
    ),
    periodDrawdown = (() => {
      let peak = -Infinity;
      let worst = 0;
      windowRows.forEach((row) => {
        if (row.adjusted_close != null) {
          peak = Math.max(peak, row.adjusted_close);
          worst = Math.min(worst, row.adjusted_close / peak - 1);
        }
      });
      return worst * 100;
    })(),
    bench = data && current ? compare(data.history, current.symbol, tf) : null,
    median = (k) => {
      const v = filtered
        .map((x) => x[k])
        .filter((x) => x != null)
        .sort((a, b) => a - b);
      return v.length ? v[Math.floor(v.length / 2)] : null;
    },
    update = (i, k, v) =>
      setDraft({
        ...draft,
        criteria: draft.criteria.map((c, n) =>
          n === i ? { ...c, [k]: v } : c,
        ),
      });
  if (loadError)
    return (
      <div className="loading load-failure">
        <Activity />
        <strong>DATA SNAPSHOT UNAVAILABLE</strong>
        <p>{loadError}</p>
        <button onClick={loadData}>RETRY</button>
        <small>
          If this continues locally, run python -m src.export_react_data and
          refresh.
        </small>
      </div>
    );
  if (!data)
    return (
      <div className="loading">
        <Activity />
        <span>INITIALIZING QUANTDASH</span>
      </div>
    );
  return (
    <div className="app-shell">
      <header>
        <button className="brand" onClick={() => setPage("research")}>
          <span>Q</span>
          <div>
            QUANT<span>DASH</span>
            <small>RESEARCH SYSTEM</small>
          </div>
        </button>
        <nav>
          <button
            className={page === "research" ? "active" : ""}
            onClick={() => setPage("research")}
          >
            Research
          </button>
          <button
            className={page === "methods" ? "active" : ""}
            onClick={() => setPage("methods")}
          >
            Learn the methods
          </button>
          <button
            className={page === "simulation" ? "active" : ""}
            onClick={() => setPage("simulation")}
          >
            Market quest
          </button>
        </nav>
        <div className="market-date">
          <i /> DATA / {data.meta.latest_market_date}
        </div>
      </header>
      {page === "methods" ? (
        <main className="methods-page">
          <section className="hero compact">
            <div>
              <div className="eyebrow">
                <BookOpen /> KNOWLEDGE BASE
              </div>
              <h1>
                Understand the <em>system.</em>
              </h1>
              <p>
                Every formula includes its purpose and plain-language meaning.
              </p>
            </div>
          </section>
          <aside className="toc">
            <span>TABLE OF CONTENTS</span>
            {METHODS.map((m) => (
              <a href={`#${m.id}`} key={m.id}>
                <b>{m.n}</b>
                {m.title}
                <ChevronRight />
              </a>
            ))}
          </aside>
          <section className="method-stack">
            {METHODS.map((m) => (
              <article id={m.id} key={m.id}>
                <div className="method-number">{m.n}</div>
                <div>
                  <span>{m.tag}</span>
                  <h2>{m.title}</h2>
                  <p>{m.text}</p>
                  <FormulaDisplay method={m} />
                </div>
              </article>
            ))}
          </section>
        </main>
      ) : page === "simulation" ? (
        <Simulation data={data} researchGoal={goal} />
      ) : (
        <main>
          <section className="hero">
            <div>
              <div className="eyebrow">
                <Sparkles /> DECISION SUPPORT / NOT ADVICE
              </div>
              <h1>
                See the signal.
                <br />
                <em>Understand the evidence.</em>
              </h1>
              <p>
                Screen, compare with the market, and inspect every score without
                hiding missing data.
              </p>
            </div>
            <div className="orb">
              <span>20</span>
              <small>STOCK UNIVERSE</small>
            </div>
          </section>
          <section className="workflow">
            <span>01 SCREEN</span>
            <i />
            <span>02 COMPARE</span>
            <i />
            <span>03 UNDERSTAND</span>
            <i />
            <span>04 FORM A VIEW</span>
          </section>
          <section className="goal-console">
            <div>
              <span>YOUR RESEARCH INTENT</span>
              <h2>What are you trying to achieve?</h2>
              <p>
                Examples: long-term growth, lower volatility, income, value, or
                simply learning. This changes the guidance—not the underlying
                data or score.
              </p>
            </div>
            <div>
              <textarea
                value={goalDraft}
                onChange={(event) => setGoalDraft(event.target.value)}
                placeholder="e.g. I want long-term growth but I do not want extremely high risk"
              />
              <button
                className="intent-apply"
                disabled={!goalDraft.trim() || goalBusy}
                onClick={submitGoal}
              >
                <Sparkles /> {goalBusy ? "ANALYZING..." : "ANALYZE MY INTENT"}
              </button>
              {goalBusy ? (
                <div className="intent-loader">
                  <i />
                  <span>Building a research checklist for your goal...</span>
                </div>
              ) : (
                <small>{goalAdvice || goalGuide}</small>
              )}
            </div>
          </section>
          <section className="metrics">
            <Metric
              label="STOCKS SHOWN"
              value={`${filtered.length} / ${universe.length}`}
              meta="AFTER APPLIED FILTERS"
              help={() => setHelp("scores")}
            />
            <Metric
              label="MEDIAN SCORE"
              value={num(median("composite_score"))}
              meta="RELATIVE / 0–100"
              t="violet"
              help={() => setHelp("scores")}
            />
            <Metric
              label="MEDIAN RSI"
              value={num(median("rsi_14"))}
              meta="MOMENTUM / 14D"
              help={() => setHelp("rsi")}
            />
            <Metric
              label="MEDIAN VOLATILITY"
              value={pct(median("volatility_pct"))}
              meta="ANNUALIZED / 20D"
              t="violet"
              help={() => setHelp("risk")}
            />
          </section>
          <section className="market-pulse">
            <div className="pulse-heading">
              <span>MARKET CONTEXT / SPY BENCHMARK</span>
              <h2>{marketTrend}</h2>
              <p>
                SPY represents the broad US equity market reference. It is not
                automatically a “good signal”; it tells you whether a stock is
                keeping up with the market opportunity cost.
              </p>
            </div>
            <div
              className={
                spy?.momentum_63d_raw_pct >= 0 ? "pulse-good" : "pulse-bad"
              }
            >
              <b>{pct(spy?.momentum_63d_raw_pct)}</b>
              <span>SPY 3M MOMENTUM</span>
              <small>
                {spy?.momentum_63d_raw_pct >= 0
                  ? "Market rose over 3M"
                  : "Market fell over 3M"}
              </small>
            </div>
            <div>
              <b>
                {positiveMomentum.length} / {universe.length}
              </b>
              <span>STOCKS ABOVE 0% MOMENTUM</span>
              <small>
                {pct(
                  (positiveMomentum.length / Math.max(universe.length, 1)) *
                    100,
                  0,
                )}{" "}
                market breadth
              </small>
            </div>
            <div>
              <b>
                {outperformingSpy.length} / {universe.length}
              </b>
              <span>OUTPERFORMING SPY</span>
              <small>
                {pct(
                  (outperformingSpy.length / Math.max(universe.length, 1)) *
                    100,
                  0,
                )}{" "}
                beat SPY on the same 3M window
              </small>
            </div>
            <div>
              <b>
                {favorable.length} / {universe.length}
              </b>
              <span>RESEARCH-ELIGIBLE SIGNALS</span>
              <small>
                {pct(
                  (favorable.length / Math.max(universe.length, 1)) * 100,
                  0,
                )}{" "}
                Strong or Positive—not automatic investments
              </small>
            </div>
          </section>
          <div className="benchmark-key">
            <span>
              <i className="good" /> POSITIVE: above 0%
            </span>
            <span>
              <i className="beat" /> OUTPERFORMING: stock return &gt; SPY return
            </span>
            <span>
              <i className="bad" /> NEGATIVE: below 0%
            </span>
            <small>
              Magnitude matters: +20% is a larger rise than +2%; -20% is a
              larger fall than -2%. Always compare identical time windows.
            </small>
          </div>
          {current && spy?.momentum_63d_raw_pct != null && (
            <section className="direct-benchmark">
              <div>
                <span>MARKET NUMBER</span>
                <b>{pct(spy.momentum_63d_raw_pct)}</b>
                <small>SPY · 3M RETURN</small>
              </div>
              <i>VS</i>
              <div>
                <span>COMPANY NUMBER</span>
                <b>{pct(current.momentum_63d_raw_pct)}</b>
                <small>{current.symbol} · 3M RETURN</small>
              </div>
              <div
                className={
                  (current.momentum_63d_raw_pct || 0) >=
                  spy.momentum_63d_raw_pct
                    ? "ahead"
                    : "behind"
                }
              >
                <span>DIFFERENCE FROM MARKET</span>
                <b>
                  {pct(
                    (current.momentum_63d_raw_pct || 0) -
                      spy.momentum_63d_raw_pct,
                  )}
                </b>
                <small>
                  {(current.momentum_63d_raw_pct || 0) >=
                  spy.momentum_63d_raw_pct
                    ? `${current.symbol} outperformed SPY`
                    : `${current.symbol} lagged SPY`}
                </small>
              </div>
              <p>
                Higher means stronger price performance over this same
                period—not automatically a better company or a reason to buy.
                Check valuation, fundamentals and risk next.
              </p>
            </section>
          )}
          <section
            className={`workspace ${filterOpen ? "" : "filters-closed"}`}
          >
            <button
              className="filter-dock-toggle"
              onClick={() => setFilterOpen(!filterOpen)}
              title={filterOpen ? "Retract Filter Lab" : "Open Filter Lab"}
              aria-label={filterOpen ? "Retract Filter Lab" : "Open Filter Lab"}
            >
              {filterOpen ? <Minimize2 /> : <SlidersHorizontal />}
              <span>{filterOpen ? "RETRACT FILTERS" : "OPEN FILTERS"}</span>
            </button>
            <aside className={`filters ${filterOpen ? "" : "collapsed"}`}>
              <div className="panel-title">
                <SlidersHorizontal /> FILTER LAB
              </div>
              <label>
                SEARCH
                <div className="input-wrap">
                  <Search />
                  <input
                    value={draft.search}
                    onChange={(e) =>
                      setDraft({ ...draft, search: e.target.value })
                    }
                    placeholder="Ticker or company"
                  />
                </div>
              </label>
              <label>OVERALL SIGNAL</label>
              <div className="checks">
                {["Strong", "Positive", "Neutral", "Weak", "Very Weak"].map(
                  (s) => (
                    <button
                      className={draft.signals.includes(s) ? "on" : ""}
                      onClick={() =>
                        setDraft({
                          ...draft,
                          signals: draft.signals.includes(s)
                            ? draft.signals.filter((x) => x !== s)
                            : [...draft.signals, s],
                        })
                      }
                      key={s}
                    >
                      {s}
                    </button>
                  ),
                )}
              </div>
              <label>COMBINE CRITERIA</label>
              {draft.criteria.map((c, i) => (
                <div className="criterion" key={i}>
                  <select
                    value={c.field}
                    onChange={(e) => update(i, "field", e.target.value)}
                  >
                    {Object.entries(fields).map(([k, v]) => (
                      <option value={k} key={k}>
                        {v[0]}
                      </option>
                    ))}
                  </select>
                  <div>
                    <select
                      value={c.op}
                      onChange={(e) => update(i, "op", e.target.value)}
                    >
                      <option>&gt;=</option>
                      <option>&lt;=</option>
                    </select>
                    <input
                      type="number"
                      value={c.value}
                      step={fields[c.field][3]}
                      onChange={(e) => update(i, "value", +e.target.value)}
                    />
                    <button
                      onClick={() =>
                        setDraft({
                          ...draft,
                          criteria: draft.criteria.filter((_, n) => n !== i),
                        })
                      }
                    >
                      <Trash2 />
                    </button>
                  </div>
                </div>
              ))}
              <button
                className="add-filter"
                onClick={() =>
                  setDraft({
                    ...draft,
                    criteria: [
                      ...draft.criteria,
                      { field: "composite_score", op: ">=", value: 60 },
                    ],
                  })
                }
              >
                <Plus /> Add criterion
              </button>
              <button
                className="apply"
                onClick={() => setFilters(structuredClone(draft))}
              >
                <Filter /> APPLY FILTERS
              </button>
              <button
                className="reset"
                onClick={() => {
                  setDraft(blank);
                  setFilters(blank);
                }}
              >
                <RotateCcw /> Reset
              </button>
              <small className="missing-note">
                Criteria combine with AND. Missing values cannot pass active
                criteria and are never filled with zero.
              </small>
            </aside>
            <div className="results">
              <div className="section-title">
                <div>
                  <span>01 / SCREEN</span>
                  <h2>Find candidates</h2>
                </div>
                <div className="table-actions">
                  <select
                    value={sort}
                    onChange={(e) => setSort(e.target.value)}
                  >
                    {Object.entries(cols)
                      .filter(([k]) => k !== "rank")
                      .map(([k, v]) => (
                        <option value={k} key={k}>
                          {v}
                        </option>
                      ))}
                  </select>
                  <button onClick={() => setAsc(!asc)}>
                    {asc ? "ASC \u2191" : "DESC \u2193"}
                  </button>
                  <button onClick={() => csv(filtered, visible)}>
                    <Download /> CSV
                  </button>
                </div>
              </div>
              <p className="sort-note">
                Current order: <b>{cols[sort]}</b>,{" "}
                {asc
                  ? "ascending (smallest first)"
                  : "descending (largest first)"}
                . Rank 1 is the first row in this order.
              </p>
              <details className="score-guide">
                <summary>
                  <Info /> How is the score calculated and ranked?
                </summary>
                <div className="plain-formulas">
                  <h3>THE SCORE IN NORMAL TERMS</h3>
                  <p>
                    <b>1. Momentum</b>
                    <span>
                      (1M rank × 20%) + (3M rank × 40%) + (6M rank × 40%)
                    </span>
                  </p>
                  <p>
                    <b>2. Fundamentals</b>
                    <span>
                      (YoY revenue-growth rank + profit-margin rank) ÷ 2
                    </span>
                  </p>
                  <p>
                    <b>3. Valuation</b>
                    <span>100 − positive P/E percentile</span>
                  </p>
                  <p>
                    <b>4. Composite</b>
                    <span>
                      (Momentum × 40%) + (Fundamentals × 40%) + (Valuation ×
                      20%)
                    </span>
                  </p>
                  <small>
                    “Rank” means position versus the other stocks in this
                    20-stock universe, converted to a 0–100 score. It is not the
                    raw percentage.
                  </small>
                </div>
                <div className="score-guide-grid">
                  <article>
                    <b>MOMENTUM / 40%</b>
                    <p>
                      20% of the 1-month rank + 40% of the 3-month rank + 40% of
                      the 6-month rank.
                    </p>
                  </article>
                  <article>
                    <b>FUNDAMENTALS / 40%</b>
                    <p>
                      Half YoY revenue-growth rank and half profit-margin rank.
                      YoY compares the latest period with the same period one
                      year earlier.
                    </p>
                  </article>
                  <article>
                    <b>VALUATION / 20%</b>
                    <p>
                      100 minus the positive P/E percentile. Lower P/E scores
                      higher here, but it is not automatically a better company.
                    </p>
                  </article>
                  <article>
                    <b>COMPOSITE / 100%</b>
                    <p>
                      40% momentum + 40% fundamentals + 20% valuation. Beta, RSI
                      and volatility are context only and do not raise this
                      score.
                    </p>
                  </article>
                </div>
                <p className="score-caveat">
                  Every input is a relative percentile within this 20-stock
                  universe. If an input is missing, available weights are
                  renormalized and coverage is reported; missing data is never
                  changed to zero. Use ASC/DESC above to rank the current
                  filtered results.
                </p>
              </details>
              <details className="column-picker">
                <summary>
                  <Eye /> Choose table columns
                </summary>
                <div>
                  {Object.entries(cols).map(([k, v]) => (
                    <label key={k}>
                      <input
                        type="checkbox"
                        checked={visible.includes(k)}
                        disabled={k === "symbol"}
                        onChange={() =>
                          setVisible(
                            visible.includes(k)
                              ? visible.filter((x) => x !== k)
                              : [...visible, k],
                          )
                        }
                      />
                      {v}
                    </label>
                  ))}
                </div>
              </details>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      {visible.map((c) => (
                        <th key={c}>{cols[c]}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((s, rowIndex) => (
                      <tr
                        key={s.symbol}
                        className={selected === s.symbol ? "selected" : ""}
                        onClick={() => setSelected(s.symbol)}
                      >
                        {visible.map((c) => (
                          <td key={c}>
                            {c === "rank" ? (
                              <b>#{rowIndex + 1}</b>
                            ) : c === "symbol" ? (
                              <b>{s[c]}</b>
                            ) : c === "overall_label" ? (
                              <span className={`signal ${tone(s[c])}`}>
                                {s[c] || "N/A"}
                              </span>
                            ) : c === "score_coverage" ? (
                              pct((s[c] || 0) * 100, 0)
                            ) : c.includes("pct") ? (
                              pct(s[c])
                            ) : c === "company_name" ? (
                              s[c]
                            ) : (
                              num(s[c])
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!filtered.length && (
                  <div className="empty">
                    0 of {universe.length} stocks match. Try relaxing a
                    criterion.
                  </div>
                )}
              </div>
              <SignalMap stocks={filtered} onPick={setSelected} />
              {current && (
                <section className="deep-dive">
                  <div className="section-title">
                    <div>
                      <span>03 / UNDERSTAND</span>
                      <h2>{current.symbol} research console</h2>
                    </div>
                    <div className="selectors">
                      <select
                        value={selected}
                        onChange={(e) => setSelected(e.target.value)}
                      >
                        {universe.map((s) => (
                          <option key={s.symbol}>{s.symbol}</option>
                        ))}
                      </select>
                      <select
                        value={tf}
                        onChange={(e) => setTf(e.target.value)}
                      >
                        {Object.keys(tfDays).map((x) => (
                          <option key={x}>{x}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <section className="score-strip">
                    {[
                      [
                        "MOMENTUM",
                        current.momentum_subscore,
                        current.momentum_label,
                      ],
                      [
                        "FUNDAMENTALS",
                        current.quality_subscore,
                        current.fundamentals_label,
                      ],
                      [
                        "VALUATION",
                        current.valuation_subscore,
                        current.valuation_label,
                      ],
                      [
                        "OVERALL",
                        current.composite_score,
                        `${current.overall_label} · ${pct((current.score_coverage || 0) * 100, 0)} covered`,
                      ],
                    ].map((x) => (
                      <div key={x[0]}>
                        <span>{x[0]}</span>
                        <b>{num(x[1])}</b>
                        <small>{x[2]}</small>
                      </div>
                    ))}
                  </section>
                  <details className="signal-explainer">
                    <summary>
                      <Sparkles /> EXPLAIN THIS SIGNAL
                    </summary>
                    <div>
                      <header>
                        <span>RULE-BASED RESULT</span>
                        <b>{current.overall_label || "Unavailable"}</b>
                      </header>
                      <p>
                        The overall label comes from the composite score of{" "}
                        {num(current.composite_score)}. Scores of 80+, 60–79.9,
                        40–59.9, 20–39.9, and below 20 map to Strong, Positive,
                        Neutral, Weak, and Very Weak.
                      </p>
                      <div className="signal-scale">
                        {[
                          ["80–100", "Strong"],
                          ["60–79.9", "Positive"],
                          ["40–59.9", "Neutral"],
                          ["20–39.9", "Weak"],
                          ["0–19.9", "Very Weak"],
                        ].map(([range, label]) => (
                          <div className={tone(label)} key={label}>
                            <b>{range}</b>
                            <span>{label}</span>
                          </div>
                        ))}
                      </div>
                      <ul>
                        <li>
                          Momentum: {num(current.momentum_subscore)} →{" "}
                          {current.momentum_label || "Unavailable"}
                        </li>
                        <li>
                          Fundamentals: {num(current.quality_subscore)} →{" "}
                          {current.fundamentals_label || "Unavailable"}
                        </li>
                        <li>
                          Valuation: {num(current.valuation_subscore)} →{" "}
                          {current.valuation_label || "Unavailable"}
                        </li>
                        <li>
                          Coverage:{" "}
                          {pct((current.score_coverage || 0) * 100, 0)} of
                          intended inputs
                        </li>
                      </ul>
                      <small>
                        Composite weights are 40% momentum, 40% fundamentals,
                        and 20% valuation, renormalized across available
                        sub-scores. Beta, RSI, volatility, and drawdown are risk
                        context and do not change this label. This is not a
                        buy/sell recommendation.
                      </small>
                    </div>
                  </details>
                  <div className="detail-grid">
                    <Metric
                      label="ADJUSTED CLOSE"
                      value={`$${num(current.adjusted_close, 2)}`}
                      meta="SPLIT & DIVIDEND ADJUSTED"
                      help={() => setHelp("adjusted")}
                    />
                    <Metric
                      label="RSI 14"
                      value={num(current.rsi_14)}
                      meta="MOMENTUM CONTEXT"
                      t="violet"
                      help={() => setHelp("rsi")}
                    />
                    <Metric
                      label="20D VOLATILITY"
                      value={pct(current.volatility_pct)}
                      meta="ANNUALIZED"
                      help={() => setHelp("risk")}
                    />
                    <Metric
                      label={`${tf} MAX DRAWDOWN`}
                      value={pct(periodDrawdown)}
                      meta="PEAK TO TROUGH"
                      t="violet"
                      help={() => setHelp("drawdown")}
                    />
                  </div>
                  <Chart
                    title={`${current.symbol} adjusted price & moving averages · ${tf}`}
                    kicker="PRICE / TREND"
                    labels={windowRows.map((row) => row.date)}
                    unit="$"
                    series={[
                      {
                        n: "Adjusted close",
                        c: "#9bd2ff",
                        v: windowRows.map((r) => r.adjusted_close),
                      },
                      {
                        n: "SMA 20",
                        c: "#4d7dff",
                        v: windowRows.map((r) => r.sma_20),
                      },
                      {
                        n: "SMA 50",
                        c: "#ffa7a7",
                        v: windowRows.map((r) => r.sma_50),
                      },
                    ]}
                  />
                  <div className="chart-pair">
                    <Chart
                      title="RSI 14"
                      kicker="MOMENTUM"
                      labels={windowRows.map((row) => row.date)}
                      series={[
                        {
                          n: "RSI",
                          c: "#72e3ff",
                          v: windowRows.map((r) => r.rsi_14),
                        },
                      ]}
                    />
                    <Chart
                      title="Annualized volatility"
                      kicker="RISK"
                      labels={windowRows.map((row) => row.date)}
                      unit="%"
                      series={[
                        {
                          n: "Volatility %",
                          c: "#8c78ff",
                          v: windowRows.map((r) =>
                            r.volatility_20d_annualized == null
                              ? null
                              : r.volatility_20d_annualized * 100,
                          ),
                        },
                      ]}
                    />
                  </div>
                  {bench && (
                    <>
                      <div className="benchmark-summary">
                        <span>
                          {current.symbol} VS SPY · {tf}
                        </span>
                        <div>
                          <b>{pct(bench.stock)}</b>
                          <small>{current.symbol} RETURN</small>
                        </div>
                        <div>
                          <b>{pct(bench.spy)}</b>
                          <small>SPY RETURN</small>
                        </div>
                        <div>
                          <b>
                            {bench.excess >= 0 ? "+" : ""}
                            {num(bench.excess)}%
                          </b>
                          <small>EXCESS RETURN</small>
                        </div>
                        <div>
                          <b>{bench.count}</b>
                          <small>COMMON DATES</small>
                        </div>
                      </div>
                      <div
                        className={`benchmark-meaning ${bench.excess >= 0 ? "ahead" : "behind"}`}
                      >
                        <b>
                          {current.symbol} is{" "}
                          {bench.excess >= 0 ? "ahead of" : "behind"} SPY by{" "}
                          {Math.abs(bench.excess).toFixed(1)} percentage points
                          over {tf}.
                        </b>
                        <p>
                          SPY represents a broad basket of large U.S. companies.
                          Comparing with it asks whether owning this stock added
                          value versus a simple market benchmark. This is
                          context, not proof that the stock will keep
                          outperforming or underperforming.
                        </p>
                      </div>
                      <Chart
                        title={`${current.symbol} vs SPY · normalized to 100`}
                        kicker="MARKET COMPARISON / COMMON DATES ONLY"
                        labels={bench.rows.map((row) => row.date)}
                        series={[
                          {
                            n: current.symbol,
                            c: "#8dd4ff",
                            v: bench.rows.map((r) => r.stock),
                          },
                          {
                            n: "SPY",
                            c: "#537fff",
                            v: bench.rows.map((r) => r.spy),
                          },
                        ]}
                      />
                      <p className="chart-note">
                        Both series use Adjusted Close. Dates missing from
                        either side are excluded; nothing is filled.
                      </p>
                    </>
                  )}
                </section>
              )}
            </div>
          </section>
        </main>
      )}
      {help && (
        <div className="modal-backdrop" onClick={() => setHelp()}>
          <section className="modal" onClick={(e) => e.stopPropagation()}>
            <button onClick={() => setHelp()}>
              <X />
            </button>
            <span>BEGINNER GUIDE</span>
            <h2>
              {METHODS.find((m) => m.id === help)?.title || "Metric context"}
            </h2>
            <p>{METHODS.find((m) => m.id === help)?.text}</p>
            {METHODS.find((m) => m.id === help) && (
              <FormulaDisplay method={METHODS.find((m) => m.id === help)} />
            )}
            <button
              className="apply"
              onClick={() => {
                setHelp();
                setPage("methods");
              }}
            >
              OPEN METHOD LIBRARY <ChevronRight />
            </button>
          </section>
        </div>
      )}
      <footer>
        <span>QUANTDASH / REACT</span>
        <span>Educational research interface · not investment advice</span>
      </footer>
    </div>
  );
}
createRoot(document.getElementById("root")).render(<App />);
