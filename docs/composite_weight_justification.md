# Experimental composite score: weight justification (W2-13)

## Structure

QuantDash builds interpretable sub-scores before the overall score.

### Momentum sub-score

`0.20 × momentum_21d_score + 0.40 × momentum_63d_score + 0.40 × momentum_126d_score`

The one-month signal receives less weight because it is noisier and highly
correlated with RSI. Three- and six-month signals receive equal higher weights
to emphasize more persistent trends without allowing the extreme six-month
outliers to dominate; inputs are percentile scores from winsorized values.

### Quality sub-score

`0.50 × growth_score + 0.50 × profitability_score`

Growth and profitability represent complementary dimensions. Equal weighting
avoids claiming that one is universally more important in this small,
cross-sector universe. Raw values and unusual-margin flags remain visible.

### Valuation sub-score

`valuation_score = 100 - P/E raw percentile`

Lower positive trailing P/E receives a higher score. This is only one valuation
metric and is deliberately limited to 20% of the composite. Nonpositive or
missing provider P/E receives no valuation sub-score, not zero.

## Composite weights

`0.40 × momentum_subscore + 0.40 × quality_subscore + 0.20 × valuation_subscore`

Momentum and quality receive balanced primary roles. Valuation receives less
weight because one trailing P/E ratio is a narrow and sector-sensitive proxy.
These are transparent experimental assumptions, not optimized weights. They
must be stress-tested in later work rather than fitted to this 20-stock sample.

## Why beta is excluded

Beta is market sensitivity, not monotonic attractiveness. High or low beta can
be desirable depending on the investor and market regime. Including it would
embed an unstated risk preference. Beta remains a filter, label, and dashboard
context alongside volatility, RSI, and drawdown. Drawdown resilience is shown
as an optional score but is not in the default composite to avoid silently
adding a defensive preference.

## Missing-value policy

Missing inputs are never zero-filled. A sub-score requires all its intended
components. At composite level, weights are renormalized across available
complete sub-scores, and `score_coverage` reports the fraction of intended
weight actually represented. Scores with coverage below 80% are ineligible;
scores at exactly 80% remain eligible but are flagged incomplete.

For example, if valuation is missing, momentum and quality retain their 40:40
relative balance and are renormalized to 50:50. Coverage is 80%, so users can
see that the result omits the intended 20% valuation information. This avoids
punishing provider missingness as if it were bad performance while preventing
the omission from being hidden.

## Interpretation warnings

- The universe contains only 20 stocks, so percentile steps are coarse.
- Percentiles preserve order but lose economic magnitude.
- The score is relative to this universe and date, not an absolute valuation.
- The result is an educational screening aid, not an investment recommendation.
