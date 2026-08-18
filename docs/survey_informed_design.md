# Survey-informed product refinements

Source: `kết quả survey.pdf`, supplied by the project owner on 2026-08-14.
The survey is treated as directional product evidence, not as a statistically
representative market study or a set of implementation instructions.

## Evidence used

- 15 of 18 respondents were in grades 11–12, and 94.1% of respondents to the
  knowledge question did not identify as proficient investors.
- Confidence across the research-task cluster averaged about 1.97/5.
- 83.3% disagreed that they knew the basic steps for researching a stock, and
  83.3% disagreed that they knew how to move from a stock to a formed view.
- Step-by-step workflow had the highest proposed-feature mean (4.44/5), while
  inline explanations scored 4.11/5 and simple filters 4.06/5.
- 14 of 18 respondents preferred either a fixed workflow or proactive next-step
  guidance. Version B, with guidance, explanations, comparisons, and risk
  context, was selected by 13 of 17 respondents.
- Short onboarding was favored over either skipping onboarding or turning the
  product into a course.

## Changes made

1. Added a short optional onboarding guide and a visible four-stage research
   path: Screen → Compare → Understand → Form a view.
2. Reframed the screener as shortlist generation rather than a recommendation.
3. Added inline explanations for P/E, profit margin, RSI, and annualized
   volatility at the selected ticker.
4. Added a structured evidence summary separating supporting evidence,
   cautions, and missing information.
5. Added a research checklist that covers business model, fundamentals,
   valuation, price/risk, benchmark comparison, and data gaps.

## Guardrails

- “High” and “low” are explicitly relative to the current 20-stock universe;
  QuantDash does not claim company-history context without historical metric
  data.
- Missing values stay unavailable and become information gaps; they are not
  converted to zero or favorable evidence.
- Composite and component labels remain research aids, not buy/sell decisions.
- Simulated portfolio and AI assistant features were not added in this pass.
  Survey support for them was weaker than for guided workflow, and both would
  materially expand MVP scope.

## Survey limitations retained

The sample is small and concentrated in high-school respondents. One mutually
exclusive response was flagged as inconsistent, and two respondents showed an
unusual cross-question rating pattern. These observations support treating the
results as qualitative design guidance rather than precise population estimates.
