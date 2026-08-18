import React, { useMemo, useState } from "react";
import { ArrowRight, Search, SlidersHorizontal } from "lucide-react";

const FIELDS = {
  composite_score: "Composite score",
  momentum_subscore: "Momentum sub-score",
  quality_subscore: "Fundamentals sub-score",
  valuation_subscore: "Valuation sub-score",
  score_coverage: "Score coverage (0–1)",
  momentum_63d_raw_pct: "Momentum 3M %",
  profit_margin_raw_pct: "Profit margin %",
  revenue_growth_yoy_raw_pct: "Revenue growth YoY %",
  pe_ratio_raw: "P/E",
  beta_252_raw: "Beta 252D",
  rsi_14: "RSI 14",
  volatility_pct: "20D volatility %",
  max_drawdown_pct: "Maximum drawdown %",
  daily_return_pct: "Latest daily return %",
  adjusted_close: "Adjusted close",
};

export default function SimulationWorkbench({ stocks, day, onContinue }) {
  const blank = { search: "", criteria: [], signals: [] };
  const [draft, setDraft] = useState(blank),
    [filters, setFilters] = useState(blank),
    [selected, setSelected] = useState("MSFT"),
    [sort, setSort] = useState("composite_score"),
    [ascending, setAscending] = useState(false);
  const rows = useMemo(
    () =>
      stocks
        .filter((s) => s.symbol !== "SPY")
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
          return (x - y) * (ascending ? 1 : -1);
        }),
    [stocks, filters, sort, ascending],
  );
  const current = stocks.find((s) => s.symbol === selected) || rows[0],
    median = (field) => {
      const values = rows
        .map((row) => row[field])
        .filter((v) => v != null)
        .sort((a, b) => a - b);
      return values.length ? values[Math.floor(values.length / 2)] : null;
    },
    update = (i, key, value) =>
      setDraft({
        ...draft,
        criteria: draft.criteria.map((c, n) =>
          n === i ? { ...c, [key]: value } : c,
        ),
      });
  return (
    <section className="simulation-workbench">
      <div className="workbench-banner">
        <div>
          <span>SIMULATION MARKET / DAY {day + 1}</span>
          <h2>Inspect before you invest.</h2>
          <p>
            Fictional seeded scenario · separate from the live Research page
          </p>
        </div>
        <button onClick={onContinue}>
          FINISH INSPECTION <ArrowRight />
        </button>
      </div>
      <div className="sim-metrics">
        <div>
          <span>STOCKS SHOWN</span>
          <b>{rows.length} / 20</b>
        </div>
        <div>
          <span>MEDIAN SCORE</span>
          <b>{median("composite_score")?.toFixed(1) ?? "N/A"}</b>
        </div>
        <div>
          <span>MEDIAN RSI</span>
          <b>{median("rsi_14")?.toFixed(1) ?? "N/A"}</b>
        </div>
        <div>
          <span>MEDIAN VOLATILITY</span>
          <b>{median("volatility_pct")?.toFixed(1) ?? "N/A"}%</b>
        </div>
      </div>
      <div className="sim-workspace">
        <aside>
          <div className="panel-title">
            <SlidersHorizontal /> FILTER LAB
          </div>
          <label>
            SEARCH
            <div className="input-wrap">
              <Search />
              <input
                value={draft.search}
                onChange={(e) => setDraft({ ...draft, search: e.target.value })}
                placeholder="Ticker or company"
              />
            </div>
          </label>
          <label>OVERALL SIGNAL</label>
          <div className="checks">
            {["Strong", "Positive", "Neutral", "Weak", "Very Weak"].map(
              (signal) => (
                <button
                  key={signal}
                  className={draft.signals.includes(signal) ? "on" : ""}
                  onClick={() =>
                    setDraft({
                      ...draft,
                      signals: draft.signals.includes(signal)
                        ? draft.signals.filter((x) => x !== signal)
                        : [...draft.signals, signal],
                    })
                  }
                >
                  {signal}
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
                {Object.entries(FIELDS).map(([field, label]) => (
                  <option value={field} key={field}>
                    {label}
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
                  ×
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
            + ADD CRITERION
          </button>
          <button
            className="apply"
            onClick={() => setFilters(structuredClone(draft))}
          >
            APPLY FILTERS
          </button>
          <button
            className="reset"
            onClick={() => {
              setDraft(blank);
              setFilters(blank);
            }}
          >
            RESET
          </button>
          <small className="missing-note">
            Active criteria combine with AND. Missing values cannot pass and are
            never filled.
          </small>
        </aside>
        <div className="sim-results">
          <div className="sim-sort">
            <span>SHOWING {rows.length} OF 20</span>
            <label>
              SORT BY{" "}
              <select value={sort} onChange={(e) => setSort(e.target.value)}>
                {Object.entries(FIELDS).map(([field, label]) => (
                  <option value={field} key={field}>
                    {label}
                  </option>
                ))}
              </select>
              <button
                className="sort-direction"
                onClick={() => setAscending(!ascending)}
                title="Reverse sorting direction"
              >
                {ascending ? "ASC ↑" : "DESC ↓"}
              </button>
            </label>
          </div>
          <div className="sim-table">
            <table>
              <thead>
                <tr>
                  <th>TICKER</th>
                  <th>COMPANY</th>
                  <th>PRICE</th>
                  <th>MOMENTUM</th>
                  <th>P/E</th>
                  <th>RSI</th>
                  <th>SCORE</th>
                  <th>SIGNAL</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((s) => (
                  <tr
                    className={s.symbol === selected ? "selected" : ""}
                    onClick={() => setSelected(s.symbol)}
                    key={s.symbol}
                  >
                    <td>
                      <b>{s.symbol}</b>
                    </td>
                    <td>{s.company_name}</td>
                    <td>${s.adjusted_close?.toFixed(2)}</td>
                    <td>{s.momentum_63d_raw_pct?.toFixed(1) ?? "N/A"}%</td>
                    <td>{s.pe_ratio_raw?.toFixed(1) ?? "N/A"}</td>
                    <td>{s.rsi_14?.toFixed(1) ?? "N/A"}</td>
                    <td>
                      <strong>{s.composite_score?.toFixed(1) ?? "N/A"}</strong>
                    </td>
                    <td>{s.overall_label}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {current && (
            <div className="sim-detail">
              <div>
                <span>SELECTED RESEARCH FILE</span>
                <h3>
                  {current.symbol} · {current.company_name}
                </h3>
                <p>{current.sic_description}</p>
              </div>
              <div>
                <span>MOMENTUM</span>
                <b>{current.momentum_subscore?.toFixed(1) ?? "N/A"}</b>
                <small>{current.momentum_label}</small>
              </div>
              <div>
                <span>FUNDAMENTALS</span>
                <b>{current.quality_subscore?.toFixed(1) ?? "N/A"}</b>
                <small>{current.fundamentals_label}</small>
              </div>
              <div>
                <span>VALUATION</span>
                <b>{current.valuation_subscore?.toFixed(1) ?? "N/A"}</b>
                <small>{current.valuation_label}</small>
              </div>
              <div>
                <span>RISK CONTEXT</span>
                <b>β {current.beta_252_raw?.toFixed(2) ?? "N/A"}</b>
                <small>
                  {current.volatility_pct?.toFixed(1) ?? "N/A"}% volatility
                </small>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
