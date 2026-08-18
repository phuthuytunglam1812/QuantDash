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
  momentum_63d_raw_pct: ["Momentum 3M %", -100, 200, 1],
  profit_margin_raw_pct: ["Profit margin %", -100, 100, 1],
  revenue_growth_yoy_raw_pct: ["Revenue growth YoY %", -100, 200, 1],
  pe_ratio_raw: ["P/E", -100, 400, 1],
  beta_252_raw: ["Beta 252D", -2, 5, 0.1],
  rsi_14: ["RSI 14", 0, 100, 1],
  volatility_pct: ["20D volatility %", 0, 200, 1],
};
const cols = {
  symbol: "Ticker",
  company_name: "Company",
  momentum_63d_raw_pct: "Momentum 3M",
  profit_margin_raw_pct: "Margin",
  pe_ratio_raw: "P/E",
  beta_252_raw: "Beta",
  composite_score: "Score",
  score_coverage: "Coverage",
  overall_label: "Signal",
};
const baseCols = [
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
      (s) => s.rsi_14 != null && s.pe_ratio_raw != null,
    ),
    unplotted = stocks.filter(
      (s) => s.rsi_14 == null || s.pe_ratio_raw == null,
    ),
    max = Math.max(...valid.map((s) => s.composite_score || 1), 1);
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
      <svg viewBox="0 0 1000 430">
        <g className="grid">
          <line x1="60" y1="210" x2="970" y2="210" />
          <line x1="515" y1="25" x2="515" y2="390" />
        </g>
        {valid.map((s) => {
          const x = 60 + (Math.max(0, Math.min(100, s.rsi_14)) / 100) * 910,
            pe = Math.max(-20, Math.min(200, s.pe_ratio_raw)),
            y = 390 - ((pe + 20) / 220) * 365,
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
        <text className="axis-label" x="470" y="425">
          RSI 14 →
        </text>
        <text className="axis-label" x="8" y="20">
          P/E ↑
        </text>
      </svg>
      <p className="chart-note">
        P/E is descriptive—not automatically better when lower. Bubble size
        represents composite score; beta is risk context only.
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
                stock.pe_ratio_raw == null ? "P/E N/A" : null,
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
      ...rows.map((r) =>
        visible
          .map((c) => `"${String(r[c] ?? "").replaceAll('"', '""')}"`)
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
    [page, setPage] = useState("research"),
    [draft, setDraft] = useState(blank),
    [filters, setFilters] = useState(blank),
    [selected, setSelected] = useState("MSFT"),
    [tf, setTf] = useState("1Y"),
    [visible, setVisible] = useState(baseCols),
    [sort, setSort] = useState("composite_score"),
    [asc, setAsc] = useState(false),
    [help, setHelp] = useState();
  useEffect(() => {
    fetch("/data/dashboard.json")
      .then((r) => r.json())
      .then(setData);
  }, []);
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
  const current = universe.find((s) => s.symbol === selected) || universe[0],
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
        <Simulation data={data} />
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
          <section className="workspace">
            <aside className="filters">
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
                    {Object.entries(cols).map(([k, v]) => (
                      <option value={k} key={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                  <button onClick={() => setAsc(!asc)}>
                    {asc ? "ASC" : "DESC"}
                  </button>
                  <button onClick={() => csv(filtered, visible)}>
                    <Download /> CSV
                  </button>
                </div>
              </div>
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
                    {filtered.map((s) => (
                      <tr
                        key={s.symbol}
                        className={selected === s.symbol ? "selected" : ""}
                        onClick={() => setSelected(s.symbol)}
                      >
                        {visible.map((c) => (
                          <td key={c}>
                            {c === "symbol" ? (
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
                            {num(bench.excess)} pp
                          </b>
                          <small>EXCESS RETURN</small>
                        </div>
                        <div>
                          <b>{bench.count}</b>
                          <small>COMMON DATES</small>
                        </div>
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
