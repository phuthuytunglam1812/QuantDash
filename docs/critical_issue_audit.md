# W3-13 — P0/P1 critical issue audit

## Resolved before release candidate

| Severity | Issue | Resolution | Verification |
|---|---|---|---|
| P0 | Market Quest returned from inspection to the same Day 1 lesson | Inspection now transitions to the investment basket; investment advances the day | React production build |
| P0 | Fundamental facts could be selected without an explicit historical decision date | Reusable filing-date-aware selector added | Point-in-time tests |
| P0 | Twelve Data adjusted close was mislabeled as unadjusted close | Raw close retained only when explicitly supplied | Adjusted-price tests |
| P1 | Snapshot load failure could leave a permanent blank/loading page | Readable error, Retry action, and recovery instruction | React build |
| P1 | Quiz displayed all questions at once | One-question flow with feedback and progress | React build |
| P1 | Simulation basket UI and single-ticker accounting disagreed | Dollar allocations across unlimited companies with fractional holdings | React build |
| P1 | Signal label lacked component-level rationale | Explain This Signal panel added | React build |
| P1 | Missing ticker on RSI/P-E map looked like an app error | Explicit plotted/missing count retained; missing P/E never fabricated | Dashboard tests |

## Release gate

- Python regression suite passes.
- React production bundle builds.
- No known local P0 defect remains.
- External usability findings from W3-12 must be appended here and triaged before
  claiming final product-testing completion.
