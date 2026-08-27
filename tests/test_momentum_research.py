import numpy as np
import pandas as pd

from src.momentum_research import build_momentum_research


def sample_prices(symbols=20, periods=110):
    dates = pd.bdate_range("2025-01-02", periods=periods)
    rows = []
    for index in range(symbols):
        growth = 0.0003 + index * 0.00008
        values = 100 * np.exp(np.arange(periods) * growth)
        rows.append(
            pd.DataFrame(
                {"symbol": f"S{index:02}", "date": dates, "adjusted_close": values}
            )
        )
    return pd.concat(rows, ignore_index=True)


def test_quintiles_use_same_date_signal_and_future_prices_only_for_outcome():
    observations, summary, spread, report = build_momentum_research(sample_prices())
    assert set(observations.quintile.unique()) == {1, 2, 3, 4, 5}
    assert observations.groupby(["date", "quintile"]).size().eq(4).all()
    assert summary.set_index("quintile").loc[5, "mean_forward_return"] > summary.set_index("quintile").loc[1, "mean_forward_return"]
    assert spread.top_minus_bottom.gt(0).all()
    assert report["formation_and_forward_separation"]


def test_last_forward_window_is_excluded_not_filled():
    observations, _, _, _ = build_momentum_research(sample_prices())
    source_last = sample_prices().date.max()
    assert observations.date.max() < source_last
    assert observations.forward_return_21d.notna().all()


def test_missing_signal_or_outcome_is_excluded():
    prices = sample_prices()
    prices.loc[(prices.symbol == "S00") & (prices.groupby("symbol").cumcount() == 70), "adjusted_close"] = np.nan
    observations, _, _, _ = build_momentum_research(prices)
    assert observations[["momentum_63d", "forward_return_21d"]].notna().all().all()
