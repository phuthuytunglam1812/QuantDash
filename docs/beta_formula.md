# Beta formula and window rules (W2-03)

For each stock and lookback `N`:

`beta_N = Cov(stock simple return, SPY simple return) / Var(SPY simple return)`

QuantDash calculates `beta_60`, `beta_126`, and `beta_252` from the exact-date
aligned dataset. A beta is produced only when all `N` aligned return pairs are
present. The first `N-1` rows are therefore null. A 90-observation sample is
never labeled `beta_252`.

Missing returns are not filled. If any return inside a candidate window is
missing, the beta remains null until a complete window is available. If SPY
variance is zero, beta is undefined and remains null rather than becoming zero
or infinity. Each beta column has a corresponding `_n_obs` audit column.
