import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  Brain,
  Crosshair,
  Gauge,
  Keyboard,
  LockKeyhole,
  Search,
  SlidersHorizontal,
  RotateCcw,
  Sparkles,
  Trophy,
  WalletCards,
} from "lucide-react";
import "./simulation.css";
import ArcadeGames from "./ArcadeGames";
import SimulationWorkbench from "./SimulationWorkbench";

const LESSONS = [
  {
    title: "Price is not performance",
    tag: "FOUNDATION",
    cards: [
      ["Raw Close", "The final traded price reported for a session."],
      [
        "Adjusted Close",
        "A historical price restated for splits and dividends so returns remain comparable.",
      ],
      ["Core habit", "Use the same price basis on both sides of a comparison."],
    ],
    quiz: [
      [
        "A stock splits 2-for-1. Which series avoids showing a fake 50% loss?",
        ["Raw Close", "Adjusted Close", "Volume", "P/E"],
        1,
      ],
      [
        "Adjusted Close mainly improves comparisons across…",
        ["Time", "Company names", "Screen sizes", "Currencies only"],
        0,
      ],
      [
        "Fill the gap: missing return data should remain ____.",
        ["zero", "100", "missing", "bullish"],
        2,
      ],
      [
        "For stock vs SPY, the safest basis is…",
        [
          "Stock raw / SPY adjusted",
          "Both adjusted",
          "Both volume",
          "Any two columns",
        ],
        1,
      ],
    ],
  },
  {
    title: "Read momentum without chasing",
    tag: "MOMENTUM",
    cards: [
      [
        "Return",
        "The percentage change relative to the starting adjusted price.",
      ],
      ["RSI 14", "A 0–100 comparison of smoothed recent gains and losses."],
      [
        "Core habit",
        "Above 70 or below 30 is context—not an automatic trade command.",
      ],
    ],
    quiz: [
      [
        "RSI compares average recent…",
        [
          "Revenue and cost",
          "Gains and losses",
          "Price and EPS",
          "Assets and debt",
        ],
        1,
      ],
      [
        "RSI above 70 always means sell.",
        ["True", "False", "Only for SPY", "Only Monday"],
        1,
      ],
      [
        "A 3-month momentum window uses roughly…",
        ["3 days", "21 trading days", "63 trading days", "365 trading days"],
        2,
      ],
      [
        "A positive return means ending adjusted price is…",
        ["Above its start", "Missing", "Always cheap", "Below zero"],
        0,
      ],
    ],
  },
  {
    title: "Separate quality from valuation",
    tag: "FUNDAMENTALS",
    cards: [
      ["Profit margin", "Profit retained per dollar of revenue."],
      [
        "P/E",
        "Price paid per dollar of earnings. Lower is not automatically better.",
      ],
      [
        "Core habit",
        "A strong company can still be expensive; a cheap stock can still be weak.",
      ],
    ],
    quiz: [
      [
        "Profit margin describes…",
        [
          "Price speed",
          "Profit per revenue dollar",
          "Share count",
          "Market sensitivity",
        ],
        1,
      ],
      [
        "A lower P/E guarantees a better investment.",
        ["True", "False", "Always after earnings", "Only for tech"],
        1,
      ],
      [
        "YoY growth compares with…",
        [
          "The prior day",
          "The same period one year earlier",
          "SPY only",
          "The next quarter",
        ],
        1,
      ],
      [
        "Missing P/E should be converted to zero.",
        ["True", "False", "Only in charts", "Only for filters"],
        1,
      ],
    ],
  },
  {
    title: "Measure risk, not fear",
    tag: "RISK",
    cards: [
      [
        "Volatility",
        "How widely recent returns varied, annualized for a common scale.",
      ],
      [
        "Drawdown",
        "The decline from an earlier peak inside the chosen window.",
      ],
      [
        "Beta",
        "Historical sensitivity to the market; context rather than attractiveness.",
      ],
    ],
    quiz: [
      [
        "Higher volatility means…",
        [
          "Guaranteed loss",
          "Wider recent outcomes",
          "Bad management",
          "Low P/E",
        ],
        1,
      ],
      [
        "Drawdown begins from a previous…",
        ["Peak", "Dividend", "Volume", "P/E"],
        0,
      ],
      [
        "Beta is included in QuantDash attractiveness score.",
        ["True", "False", "Only when high", "Only when low"],
        1,
      ],
      [
        "Risk metrics should be read as…",
        ["Trade commands", "Context", "Missing data", "Company names"],
        1,
      ],
    ],
  },
  {
    title: "Build an evidence-based view",
    tag: "DECISION",
    cards: [
      [
        "Sub-scores",
        "Momentum, fundamental quality, and valuation kept separate for interpretation.",
      ],
      [
        "Coverage",
        "The share of intended scoring information that was actually available.",
      ],
      [
        "Core habit",
        "Compare the score, its components, risk context, and the market benchmark.",
      ],
    ],
    quiz: [
      [
        "A composite score is best treated as…",
        [
          "A guarantee",
          "A research starting point",
          "A price target",
          "A trading order",
        ],
        1,
      ],
      [
        "Percentile rank preserves exact magnitude.",
        ["True", "False", "Only for RSI", "Only for P/E"],
        1,
      ],
      [
        "A 95th percentile in 20 stocks is very precise.",
        ["True", "False", "Always", "Only for SPY"],
        1,
      ],
      [
        "Before acting, inspect…",
        [
          "Only score",
          "Only price",
          "Components, coverage, and risk",
          "Ticker length",
        ],
        2,
      ],
    ],
  },
];

const SIM_FIELDS = {
  composite_score: "Composite score",
  momentum_63d_raw_pct: "Momentum 3M %",
  profit_margin_raw_pct: "Profit margin %",
  pe_ratio_raw: "P/E",
  beta_252_raw: "Beta 252D",
  rsi_14: "RSI 14",
  volatility_pct: "Volatility %",
};
const seeded = (text) => {
  let value = 2166136261;
  for (const character of text)
    value = Math.imul(value ^ character.charCodeAt(0), 16777619);
  return ((value >>> 0) % 10000) / 10000;
};
const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
function buildSyntheticMarket(data) {
  const regimes = [-1.1, 0.65, -0.45, 1.2, -0.2];
  const days = [
    data.stocks.map((stock) => ({ ...stock, simulation_change_pct: 0 })),
  ];
  for (let day = 1; day <= 5; day += 1) {
    days.push(
      days[day - 1].map((stock) => {
        const qualityTilt = ((stock.composite_score ?? 50) - 50) / 50;
        const volatilityScale = clamp(
          (stock.volatility_pct ?? 35) / 35,
          0.55,
          2.4,
        );
        const noise =
          (seeded(`${stock.symbol}-day-${day}-quantdash`) - 0.5) *
          5.5 *
          volatilityScale;
        const change = clamp(
          regimes[day - 1] + qualityTilt * 1.15 + noise,
          -9,
          9,
        );
        return {
          ...stock,
          simulation_regime_pct: regimes[day - 1],
          simulation_quality_tilt_pct: qualityTilt * 1.15,
          simulation_noise_pct: noise,
          adjusted_close: (stock.adjusted_close ?? 100) * (1 + change / 100),
          daily_return_pct: change,
          simulation_change_pct: change,
          momentum_63d_raw_pct:
            (stock.momentum_63d_raw_pct ?? 0) + change * 0.75,
          rsi_14: clamp((stock.rsi_14 ?? 50) + change * 1.35, 5, 95),
          volatility_pct: clamp(
            (stock.volatility_pct ?? 35) * (0.96 + Math.abs(change) / 55),
            5,
            200,
          ),
          composite_score: clamp(
            (stock.composite_score ?? 50) + change * 0.28,
            0,
            100,
          ),
        };
      }),
    );
  }
  return days;
}
const rewardTitle = (worth) =>
  worth >= 9000
    ? ["QUANT ARCHITECT", "S"]
    : worth >= 8000
      ? ["MARKET STRATEGIST", "A"]
      : worth >= 7000
        ? ["SIGNAL SCOUT", "B"]
        : ["RESEARCH ROOKIE", "C"];

function Lesson({ lesson, onPass }) {
  const [flipped, setFlipped] = useState([]),
    [answers, setAnswers] = useState({}),
    [pendingAnswer, setPendingAnswer] = useState(null),
    [questionIndex, setQuestionIndex] = useState(0),
    [submitted, setSubmitted] = useState(false);
  const score =
    (Object.entries(answers).filter(([i, a]) => lesson.quiz[+i][2] === a)
      .length /
      lesson.quiz.length) *
    100;
  return (
    <section className="campaign-stage">
      <div className="stage-kicker">
        <Brain /> LEARN
      </div>
      <h2>{lesson.title}</h2>
      <p>Flip each field card, then complete the knowledge check.</p>
      <div className="learn-cards">
        {lesson.cards.map((card, i) => (
          <button
            className={flipped.includes(i) ? "flipped" : ""}
            onClick={() =>
              setFlipped(
                flipped.includes(i)
                  ? flipped.filter((x) => x !== i)
                  : [...flipped, i],
              )
            }
            key={card[0]}
          >
            <span>{flipped.includes(i) ? card[1] : card[0]}</span>
            <small>
              {flipped.includes(i) ? "CLICK TO CLOSE" : "FLIP TO LEARN"}
            </small>
          </button>
        ))}
      </div>
      {!submitted ? (
        <div className="quiz-round">
          <div className="quiz-progress">
            <span>
              QUESTION {questionIndex + 1} / {lesson.quiz.length}
            </span>
            <b>{Math.round((questionIndex / lesson.quiz.length) * 100)}%</b>
            <i>
              <em
                style={{
                  width: `${(questionIndex / lesson.quiz.length) * 100}%`,
                }}
              />
            </i>
          </div>
          <article>
            <div className="quiz-number">
              {String(questionIndex + 1).padStart(2, "0")}
            </div>
            <h3>{lesson.quiz[questionIndex][0]}</h3>
            <div className="quiz-options">
              {lesson.quiz[questionIndex][1].map((answer, answerIndex) => {
                const selected =
                  pendingAnswer === answerIndex ||
                  answers[questionIndex] === answerIndex;
                const correct = lesson.quiz[questionIndex][2] === answerIndex;
                const answered = answers[questionIndex] !== undefined;
                return (
                  <button
                    disabled={answered}
                    className={
                      answered && correct
                        ? "correct"
                        : answered && selected
                          ? "wrong"
                          : selected
                            ? "chosen"
                            : ""
                    }
                    onClick={() => setPendingAnswer(answerIndex)}
                    key={answer}
                  >
                    <span>{String.fromCharCode(65 + answerIndex)}</span>
                    {answer}
                  </button>
                );
              })}
            </div>
            {answers[questionIndex] === undefined && (
              <button
                className="confirm-answer"
                disabled={pendingAnswer == null}
                onClick={() =>
                  setAnswers({ ...answers, [questionIndex]: pendingAnswer })
                }
              >
                CONFIRM ANSWER
              </button>
            )}
            {answers[questionIndex] !== undefined && (
              <div
                className={`quiz-feedback ${
                  answers[questionIndex] === lesson.quiz[questionIndex][2]
                    ? "correct"
                    : "wrong"
                }`}
              >
                <b>
                  {answers[questionIndex] === lesson.quiz[questionIndex][2]
                    ? "CORRECT"
                    : "NOT QUITE"}
                </b>
                <span>
                  The answer is{" "}
                  {lesson.quiz[questionIndex][1][lesson.quiz[questionIndex][2]]}
                  .
                </span>
              </div>
            )}
          </article>
          <button
            className="campaign-primary"
            disabled={answers[questionIndex] === undefined}
            onClick={() => {
              if (questionIndex === lesson.quiz.length - 1) setSubmitted(true);
              else {
                setQuestionIndex(questionIndex + 1);
                setPendingAnswer(null);
              }
            }}
          >
            {questionIndex === lesson.quiz.length - 1
              ? "VIEW RESULTS"
              : "NEXT QUESTION"}{" "}
            <ArrowRight />
          </button>
        </div>
      ) : (
        <div className="quiz-result">
          <strong>{score.toFixed(0)}%</strong>
          <div>
            <b>{score >= 70 ? "CHECKPOINT CLEARED" : "KEEP LEARNING"}</b>
            <span>
              {score >= 70
                ? "The arcade is now unlocked."
                : "You need at least 70%. Review the cards and retry."}
            </span>
          </div>
          {score >= 70 ? (
            <button onClick={onPass}>
              ENTER ARCADE <ArrowRight />
            </button>
          ) : (
            <button
              onClick={() => {
                setAnswers({});
                setQuestionIndex(0);
                setSubmitted(false);
              }}
            >
              TRY AGAIN
            </button>
          )}
        </div>
      )}
    </section>
  );
}

function Arcade({ onReward }) {
  const [game, setGame] = useState(),
    [active, setActive] = useState(false),
    [time, setTime] = useState(0),
    [count, setCount] = useState(0),
    [sequence, setSequence] = useState(""),
    [target, setTarget] = useState({ x: 50, y: 50 }),
    [reaction, setReaction] = useState("idle"),
    start = useRef(),
    timer = useRef(),
    countRef = useRef(0);
  useEffect(
    () => () => {
      clearInterval(timer.current);
      clearTimeout(timer.current);
    },
    [],
  );
  const finish = (reward, metric) => {
    clearInterval(timer.current);
    clearTimeout(timer.current);
    setActive(false);
    onReward(Math.round(reward), metric);
  };
  const begin67 = () => {
    setGame("67");
    setActive(true);
    setTime(20);
    setCount(0);
    countRef.current = 0;
    setSequence("");
    timer.current = setInterval(
      () =>
        setTime((t) => {
          if (t <= 1) {
            finish(
              500 + countRef.current * 35,
              `${countRef.current} valid 67s`,
            );
            return 0;
          }
          return t - 1;
        }),
      1000,
    );
  };
  const type67 = (e) => {
    const clean = e.target.value.replace(/[^67]/g, "");
    setSequence(clean);
    const hits = (clean.match(/67/g) || []).length;
    countRef.current = hits;
    setCount(hits);
  };
  const beginAim = () => {
    setGame("aim");
    setActive(true);
    setTime(30);
    setCount(0);
    countRef.current = 0;
    timer.current = setInterval(
      () =>
        setTime((t) => {
          if (t <= 1) {
            finish(500 + countRef.current * 70, `${countRef.current} targets`);
            return 0;
          }
          return t - 1;
        }),
      1000,
    );
  };
  const hit = () => {
    countRef.current += 1;
    setCount(countRef.current);
    setTarget({ x: 8 + Math.random() * 84, y: 12 + Math.random() * 76 });
  };
  const beginReaction = () => {
    setGame("reaction");
    setActive(true);
    setReaction("wait");
    timer.current = setTimeout(
      () => {
        start.current = performance.now();
        setReaction("go");
      },
      1600 + Math.random() * 2400,
    );
  };
  const react = () => {
    if (reaction === "wait") {
      clearTimeout(timer.current);
      setReaction("early");
      setTimeout(beginReaction, 900);
    } else if (reaction === "go") {
      const ms = Math.round(performance.now() - start.current);
      finish(Math.max(600, 4200 - ms * 5), `${ms} ms`);
    }
  };
  if (!game)
    return (
      <section className="campaign-stage">
        <div className="stage-kicker">
          <Sparkles /> EARN VIRTUAL CAPITAL
        </div>
        <h2>Choose one arcade trial</h2>
        <p>
          One game per market day. Skill affects your virtual investing budget.
        </p>
        <div className="game-choices">
          <button onClick={begin67}>
            <Keyboard />
            <b>67 Sprint</b>
            <span>Type “67” repeatedly for 20 seconds.</span>
          </button>
          <button onClick={beginAim}>
            <Crosshair />
            <b>Target Grid</b>
            <span>Hit as many moving targets as possible in 30 seconds.</span>
          </button>
          <button onClick={beginReaction}>
            <Gauge />
            <b>Reaction Gate</b>
            <span>Wait for green. Lower milliseconds earn more.</span>
          </button>
        </div>
      </section>
    );
  if (game === "67")
    return (
      <section className="game-stage">
        <div className="game-hud">
          <span>TIME {time}s</span>
          <b>{count} × 67</b>
        </div>
        <div className="type-game">
          <strong>67</strong>
          <input
            autoFocus
            value={sequence}
            onChange={type67}
            placeholder="676767…"
          />
        </div>
      </section>
    );
  if (game === "aim")
    return (
      <section className="game-stage">
        <div className="game-hud">
          <span>TIME {time}s</span>
          <b>{count} HITS</b>
        </div>
        <div className="aim-field">
          <button
            aria-label="target"
            onClick={hit}
            style={{ left: `${target.x}%`, top: `${target.y}%` }}
          >
            <i />
          </button>
        </div>
      </section>
    );
  return (
    <section className={`reaction-field ${reaction}`} onClick={react}>
      <Gauge />
      <strong>
        {reaction === "wait"
          ? "WAIT FOR GREEN"
          : reaction === "go"
            ? "CLICK NOW"
            : "TOO EARLY"}
      </strong>
      <span>
        {reaction === "wait"
          ? "Clicking early restarts the trial."
          : reaction === "go"
            ? "React!"
            : "Resetting…"}
      </span>
    </section>
  );
}

function Invest({ stocks: marketStocks, day, cash, holdings, onAdvance }) {
  const stocks = marketStocks.filter((s) => s.symbol !== "SPY"),
    [allocations, setAllocations] = useState({}),
    prices = useMemo(
      () => Object.fromEntries(stocks.map((s) => [s.symbol, s.adjusted_close])),
      [stocks],
    );
  const ownedValue = Object.entries(holdings).reduce(
      (n, [s, q]) => n + q * (prices[s] || 0),
      0,
    ),
    total = cash + ownedValue,
    allocated = Object.values(allocations).reduce(
      (sum, amount) => sum + Math.max(0, Number(amount) || 0),
      0,
    ),
    remaining = cash - allocated,
    setAmount = (symbol, value) => {
      const amount = Math.max(0, Number(value) || 0);
      setAllocations((current) =>
        amount
          ? { ...current, [symbol]: amount }
          : Object.fromEntries(
              Object.entries(current).filter(([ticker]) => ticker !== symbol),
            ),
      );
    },
    submit = () => {
      if (allocated > 0 && allocated <= cash) onAdvance(allocations, prices);
    };
  return (
    <section className="campaign-stage">
      <div className="stage-kicker">
        <WalletCards /> INVEST / DAY {day + 1}
      </div>
      <h2>Allocate virtual capital</h2>
      <p>
        Build a basket with as many companies as you want. Amounts purchase
        fractional shares; existing holdings and unused cash carry forward.
      </p>
      <div className="wallet-row">
        <div>
          <span>CASH</span>
          <b>${cash.toFixed(0)}</b>
        </div>
        <div>
          <span>HOLDINGS</span>
          <b>${ownedValue.toFixed(0)}</b>
        </div>
        <div>
          <span>NET WORTH</span>
          <b>${total.toFixed(0)}</b>
        </div>
      </div>
      <div className="basket-summary">
        <span>{Object.keys(allocations).length} COMPANIES SELECTED</span>
        <b>${allocated.toFixed(0)} allocated</b>
        <strong className={remaining < 0 ? "over" : ""}>
          ${remaining.toFixed(0)} cash remaining
        </strong>
      </div>
      <div className="basket-grid">
        {stocks.map((stock) => {
          const position = (holdings[stock.symbol] || 0) * prices[stock.symbol];
          return (
            <label
              className={allocations[stock.symbol] ? "selected" : ""}
              key={stock.symbol}
            >
              <div>
                <b>{stock.symbol}</b>
                <span>${prices[stock.symbol]?.toFixed(2) || "N/A"}</span>
              </div>
              <small>
                {position > 0
                  ? `Currently held: $${position.toFixed(0)}`
                  : "No current position"}
              </small>
              <input
                aria-label={`Amount to invest in ${stock.symbol}`}
                type="number"
                min="0"
                max={cash}
                step="10"
                placeholder="$0"
                value={allocations[stock.symbol] || ""}
                onChange={(event) =>
                  setAmount(stock.symbol, event.target.value)
                }
              />
            </label>
          );
        })}
      </div>
      <button
        className="basket-submit"
        disabled={allocated <= 0 || remaining < 0}
        onClick={submit}
      >
        INVEST IN {Object.keys(allocations).length} COMPANIES & ADVANCE{" "}
        <ArrowRight />
      </button>
      <small className="simulation-note">
        Educational simulation only. No real orders or money are involved.
      </small>
    </section>
  );
}

function MarketMove({ move, onContinue, researchGoal }) {
  const pnl = move.afterWorth - move.beforeWorth;
  const [aiFeedback, setAiFeedback] = useState(null);
  const [aiBusy, setAiBusy] = useState(true);
  const held = move.moves.filter((item) => item.held);
  const best = [...held].sort(
    (a, b) => (b.contribution || 0) - (a.contribution || 0),
  )[0];
  const worst = [...held].sort(
    (a, b) => (a.contribution || 0) - (b.contribution || 0),
  )[0];
  const diversified = (move.positionCount || held.length) >= 3;
  const regime = move.marketRegime || 0;
  const goalNote = /safe|stable|risk|an toan|rủi ro/i.test(researchGoal || "")
    ? "Because your stated goal emphasizes stability, compare concentration and volatility before adding another position."
    : /growth|long|tăng trưởng|dài hạn/i.test(researchGoal || "")
      ? "Because your stated goal emphasizes growth, check whether business evidence supports the price momentum instead of judging one session."
      : "Use the next research round to test the reason you bought, not to invent a new reason after seeing the result.";
  useEffect(() => {
    let active = true;
    fetch("/api/market-feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        research_goal: researchGoal,
        day: move.day,
        before_worth: move.beforeWorth,
        after_worth: move.afterWorth,
        market_regime_pct: regime,
        positions: held.map((item) => ({
          symbol: item.symbol,
          change_pct: item.change,
          contribution: item.contribution || 0,
        })),
      }),
    })
      .then((response) => {
        if (!response.ok) throw new Error("AI service unavailable");
        return response.json();
      })
      .then((result) => active && setAiFeedback(result))
      .catch(() => active && setAiFeedback(null))
      .finally(() => active && setAiBusy(false));
    return () => {
      active = false;
    };
  }, [move.day]);
  return (
    <section className="market-reveal">
      <div className="stage-kicker">
        <Sparkles /> MARKET CLOSE / DAY {move.day}
      </div>
      <h2>The market moved.</h2>
      <p>
        Your order used the prior adjusted close. This is what changed when the
        next simulated session closed.
      </p>
      <div className="market-pnl">
        <div>
          <span>BEFORE</span>
          <b>${move.beforeWorth.toFixed(0)}</b>
        </div>
        <div>
          <span>AFTER</span>
          <b>${move.afterWorth.toFixed(0)}</b>
        </div>
        <div className={pnl >= 0 ? "gain" : "loss"}>
          <span>ONE-DAY P&L</span>
          <b>
            {pnl >= 0 ? "+" : ""}${pnl.toFixed(0)}
          </b>
          <small>
            {move.beforeWorth
              ? `${pnl >= 0 ? "+" : ""}${((pnl / move.beforeWorth) * 100).toFixed(2)}%`
              : "0.00%"}
          </small>
        </div>
      </div>
      <div className="market-tape">
        {move.moves.map((item) => (
          <article key={item.symbol}>
            <b>{item.symbol}</b>
            <div>
              <i
                style={{
                  width: `${Math.min(Math.abs(item.change) * 12, 100)}%`,
                }}
                className={item.change >= 0 ? "up" : "down"}
              />
            </div>
            <span className={item.change >= 0 ? "up-text" : "down-text"}>
              {item.change >= 0 ? "+" : ""}
              {item.change.toFixed(2)}%
            </span>
            {item.held && <small>IN PORTFOLIO</small>}
          </article>
        ))}
      </div>
      <div className="market-lesson">
        <b>WHY DID THIS RESULT HAPPEN?</b>
        <p>
          A good decision can lose money on one day, and a weak decision can
          gain. Review the evidence and position size—not only the latest
          outcome.
        </p>
      </div>
      {aiBusy ? (
        <div className="ai-advice-loader">
          <i />
          <b>REVIEWING YOUR DECISION</b>
          <span>
            Connecting the portfolio result, market move and your research
            goal...
          </span>
        </div>
      ) : (
        <div className="decision-feedback">
          <article className="feedback-good">
            <b>WHAT YOU DID WELL</b>
            <p>
              {aiFeedback?.did_well ||
                (diversified
                  ? `You spread risk across ${move.positionCount || held.length} companies, so one result had less control over the portfolio.`
                  : move.positionCount || held.length
                    ? "You made a deliberate selection and can trace exactly what drove the result."
                    : "You kept cash instead of forcing a trade without conviction.")}
            </p>
            {best && best.contribution > 0 ? (
              <small>
                Largest positive contribution: {best.symbol}{" "}
                {(best.contribution || 0) >= 0 ? "+" : ""}$
                {(best.contribution || 0).toFixed(0)}.
              </small>
            ) : (
              <small>Largest positive contribution: N/A.</small>
            )}
          </article>
          <article className="feedback-review">
            <b>WHAT TO REVIEW NEXT</b>
            <p>
              {aiFeedback?.review_next ||
                (!diversified && (move.positionCount || held.length)
                  ? "Your portfolio is concentrated. Check whether that risk was intentional and supported by evidence."
                  : "Diversification helps, but correlated companies can still fall together. Review each position's role.")}
            </p>
            {worst && worst.contribution < 0 ? (
              <small>
                Largest negative contribution: {worst.symbol}{" "}
                {(worst.contribution || 0) >= 0 ? "+" : ""}$
                {(worst.contribution || 0).toFixed(0)}.
              </small>
            ) : (
              <small>Largest negative contribution: N/A.</small>
            )}
          </article>
          <article className="feedback-bias">
            <b>DON'T LET ONE DAY FOOL YOU</b>
            <p>
              {aiFeedback?.bias_check || (
                <>
                  A profit does not automatically make the analysis good, and a
                  loss does not automatically make it bad. The move combines a
                  market regime ({regime >= 0 ? "+" : ""}
                  {regime.toFixed(2)}%), a score tilt and a seeded
                  volatility-scaled shock. It is fictional and reproducible, not
                  a forecast.
                </>
              )}
            </p>
            <small>{aiFeedback?.next_action || goalNote}</small>
          </article>
        </div>
      )}
      <small className="ai-feedback-status">
        {aiBusy
          ? "AI COACH IS REVIEWING THIS DECISION..."
          : aiFeedback
            ? "PERSONALIZED BY OPENAI"
            : "AI UNAVAILABLE — SHOWING LOCAL SAFETY FALLBACK"}
      </small>
      <button
        className="campaign-primary"
        disabled={aiBusy}
        onClick={onContinue}
      >
        {move.done ? "VIEW FINAL RANK" : `CONTINUE TO DAY ${move.day + 1}`}{" "}
        <ArrowRight />
      </button>
    </section>
  );
}

export default function Simulation({ data, researchGoal = "" }) {
  const scenario = useMemo(() => buildSyntheticMarket(data), [data]);
  const [state, setState] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem("qd-campaign"));
      return saved?.version === 4
        ? saved
        : {
            version: 4,
            day: 0,
            phase: "path",
            cash: 0,
            holdings: {},
            history: [],
          };
    } catch {
      return {
        version: 4,
        day: 0,
        phase: "path",
        cash: 0,
        holdings: {},
        history: [],
      };
    }
  });
  useEffect(
    () => localStorage.setItem("qd-campaign", JSON.stringify(state)),
    [state],
  );
  const lesson = LESSONS[state.day],
    reset = () => {
      localStorage.removeItem("qd-campaign");
      setState({
        version: 4,
        day: 0,
        phase: "path",
        cash: 0,
        holdings: {},
        history: [],
      });
    };
  const reward = (money, metric) =>
    setState({
      ...state,
      phase: state.marketMove ? "market" : "inspect",
      cash: state.cash + money,
      history: [
        ...state.history,
        { day: state.day + 1, event: "arcade", value: money, metric },
      ],
    });
  const advance = (allocations, prices) => {
    const invested = Object.values(allocations).reduce(
        (sum, amount) => sum + Math.max(0, Number(amount) || 0),
        0,
      ),
      holdings = { ...state.holdings };
    Object.entries(allocations).forEach(([symbol, amount]) => {
      const price = prices[symbol];
      if (price > 0 && Number(amount) > 0) {
        holdings[symbol] = (holdings[symbol] || 0) + Number(amount) / price;
      }
    });
    const cash = state.cash - invested,
      nextPrices = Object.fromEntries(
        scenario[Math.min(state.day + 1, 5)].map((stock) => [
          stock.symbol,
          stock.adjusted_close,
        ]),
      ),
      worth =
        cash +
        Object.entries(holdings).reduce(
          (n, [s, q]) => n + q * (nextPrices[s] || prices[s] || 0),
          0,
        ),
      beforeWorth =
        cash +
        Object.entries(holdings).reduce(
          (n, [s, q]) => n + q * (prices[s] || 0),
          0,
        ),
      moves = scenario[Math.min(state.day + 1, 5)]
        .filter((stock) => stock.symbol !== "SPY")
        .map((stock) => {
          const change =
            prices[stock.symbol] && nextPrices[stock.symbol]
              ? (nextPrices[stock.symbol] / prices[stock.symbol] - 1) * 100
              : 0;
          return {
            symbol: stock.symbol,
            change,
            held: Boolean(holdings[stock.symbol]),
            contribution:
              (holdings[stock.symbol] || 0) *
              ((nextPrices[stock.symbol] || 0) - (prices[stock.symbol] || 0)),
          };
        })
        .sort((a, b) => Math.abs(b.change) - Math.abs(a.change)),
      done = state.day === LESSONS.length - 1;
    setState({
      ...state,
      day: done ? state.day : state.day + 1,
      phase: done ? "market" : "learn",
      cash,
      holdings,
      marketMove: {
        day: state.day + 1,
        beforeWorth,
        afterWorth: worth,
        moves,
        marketRegime:
          scenario[Math.min(state.day + 1, 5)][0]?.simulation_regime_pct || 0,
        positionCount: Object.values(holdings).filter(
          (quantity) => quantity > 0,
        ).length,
        done,
      },
      history: [
        ...state.history,
        {
          day: state.day + 1,
          event: "investment",
          value: invested,
          tickers: Object.keys(allocations),
        },
        { day: state.day + 1, event: "market", value: worth },
      ],
    });
  };
  const continueAfterMarket = () =>
    setState({
      ...state,
      phase: state.marketMove.done ? "final" : "inspect",
      marketMove: null,
    });
  const latest =
      state.history.filter((x) => x.event === "market").at(-1)?.value ||
      state.cash,
    [title, rank] = rewardTitle(latest);
  return (
    <main className="campaign">
      <section className="campaign-hero">
        <div className="eyebrow">
          <Trophy /> FIVE-DAY MARKET QUEST
        </div>
        <h1>
          Learn. Earn.
          <br />
          <em>Invest.</em>
        </h1>
        <p>
          Clear a checkpoint, win virtual capital, and respond as the simulated
          market advances.
        </p>
        <button className="campaign-reset" onClick={reset}>
          <RotateCcw /> Reset campaign
        </button>
      </section>
      <div className="day-path">
        {LESSONS.map((l, i) => (
          <div
            className={
              i < state.day ? "done" : i === state.day ? "current" : "locked"
            }
            onClick={() => {
              if (i === state.day && state.phase === "path")
                setState({ ...state, phase: "learn" });
            }}
            role={
              i === state.day && state.phase === "path" ? "button" : undefined
            }
            tabIndex={i === state.day && state.phase === "path" ? 0 : undefined}
            key={l.title}
          >
            <span>
              <em>{["◆", "↗", "★", "◇", "♛"][i]}</em>
              <sup>{i < state.day ? "✓" : i + 1}</sup>
            </span>
            <b>DAY {i + 1}</b>
            <small>{l.tag}</small>
            {i < 4 && <i />}
          </div>
        ))}
      </div>
      {state.phase === "path" && (
        <p className="path-prompt">
          Select the glowing Day {state.day + 1} checkpoint to begin.
        </p>
      )}
      {state.phase === "inspect" && (
        <SimulationWorkbench
          stocks={scenario[state.day]}
          day={state.day}
          onContinue={() => setState({ ...state, phase: "invest" })}
        />
      )}{" "}
      {state.phase === "learn" && (
        <Lesson
          lesson={lesson}
          onPass={() => setState({ ...state, phase: "arcade" })}
        />
      )}{" "}
      {state.phase === "arcade" && <ArcadeGames onReward={reward} />}{" "}
      {state.phase === "invest" && (
        <Invest
          stocks={scenario[state.day]}
          day={state.day}
          cash={state.cash}
          holdings={state.holdings}
          onAdvance={advance}
        />
      )}{" "}
      {state.phase === "market" && state.marketMove && (
        <MarketMove
          move={state.marketMove}
          onContinue={continueAfterMarket}
          researchGoal={researchGoal}
        />
      )}{" "}
      {state.phase === "final" && (
        <section className="final-rank">
          <Trophy />
          <span>CAMPAIGN COMPLETE</span>
          <strong>{rank}</strong>
          <h2>{title}</h2>
          <p>Final simulated net worth</p>
          <b>${latest.toFixed(0)}</b>
          <button onClick={reset}>PLAY AGAIN</button>
        </section>
      )}
      {state.phase !== "path" && (
        <aside className="campaign-ledger">
          <b>RUN STATUS</b>
          <span>Day {state.day + 1} / 5</span>
          <span>Virtual cash ${state.cash.toFixed(0)}</span>
          <span>{Object.keys(state.holdings).length} positions</span>
          <small>
            <LockKeyhole /> Progress saved on this device
          </small>
        </aside>
      )}
    </main>
  );
}
