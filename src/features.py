"""Quantitative feature calculations for clean price data."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Add close-to-close simple and log returns independently per symbol."""
    required = {"symbol", "date", "close"}
    missing = required - set(prices.columns)
    if missing:
        raise ValueError(f"prices missing return inputs: {sorted(missing)}")
    result = prices.copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise")
    result["close"] = pd.to_numeric(result["close"], errors="raise")
    if result["close"].le(0).any():
        raise ValueError("log returns require strictly positive close prices")
    result = result.sort_values(["symbol", "date"], kind="stable").reset_index(drop=True)
    grouped_close = result.groupby("symbol", sort=False)["close"]
    result["simple_return"] = grouped_close.pct_change(fill_method=None)
    result["log_return"] = grouped_close.transform(lambda values: np.log(values).diff())
    return result


def add_moving_averages(prices: pd.DataFrame) -> pd.DataFrame:
    """Add SMA(20), SMA(50), and EMA(20), with full warm-up periods."""
    required = {"symbol", "date", "close"}
    missing = required - set(prices.columns)
    if missing:
        raise ValueError(f"prices missing moving-average inputs: {sorted(missing)}")
    result = prices.copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise")
    result["close"] = pd.to_numeric(result["close"], errors="raise")
    result = result.sort_values(["symbol", "date"], kind="stable").reset_index(drop=True)
    grouped = result.groupby("symbol", sort=False)["close"]
    result["sma_20"] = grouped.transform(lambda values: values.rolling(20, min_periods=20).mean())
    result["sma_50"] = grouped.transform(lambda values: values.rolling(50, min_periods=50).mean())
    result["ema_20"] = grouped.transform(
        lambda values: values.ewm(span=20, adjust=False, min_periods=20).mean()
    )
    return result


def _wilder_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Wilder RSI explicitly, including its simple-average seed."""
    if period < 1:
        raise ValueError("RSI period must be positive")
    values = close.to_numpy(dtype=float)
    output = np.full(len(values), np.nan, dtype=float)
    if len(values) <= period:
        return pd.Series(output, index=close.index)
    changes = np.diff(values)
    gains = np.maximum(changes, 0.0)
    losses = np.maximum(-changes, 0.0)
    average_gain = gains[:period].mean()
    average_loss = losses[:period].mean()

    def value(gain: float, loss: float) -> float:
        if gain == 0 and loss == 0:
            return 50.0
        if loss == 0:
            return 100.0
        if gain == 0:
            return 0.0
        relative_strength = gain / loss
        return 100.0 - 100.0 / (1.0 + relative_strength)

    output[period] = value(average_gain, average_loss)
    for index in range(period + 1, len(values)):
        average_gain = ((period - 1) * average_gain + gains[index - 1]) / period
        average_loss = ((period - 1) * average_loss + losses[index - 1]) / period
        output[index] = value(average_gain, average_loss)
    return pd.Series(output, index=close.index)


def add_rsi(prices: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Add manually calculated Wilder RSI independently per symbol."""
    required = {"symbol", "date", "close"}
    missing = required - set(prices.columns)
    if missing:
        raise ValueError(f"prices missing RSI inputs: {sorted(missing)}")
    result = prices.copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise")
    result["close"] = pd.to_numeric(result["close"], errors="raise")
    result = result.sort_values(["symbol", "date"], kind="stable").reset_index(drop=True)
    result[f"rsi_{period}"] = result.groupby("symbol", sort=False, group_keys=False)["close"].apply(
        lambda values: _wilder_rsi(values, period)
    )
    return result


def add_risk_features(
    prices: pd.DataFrame, volatility_window: int = 20, trading_days: int = 252,
) -> pd.DataFrame:
    """Add annualized log-return volatility and running drawdown features."""
    required = {"symbol", "date", "close"}
    missing = required - set(prices.columns)
    if missing:
        raise ValueError(f"prices missing risk inputs: {sorted(missing)}")
    if volatility_window < 2 or trading_days < 1:
        raise ValueError("volatility_window must be >= 2 and trading_days must be positive")
    result = prices.copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise")
    result["close"] = pd.to_numeric(result["close"], errors="raise")
    if result["close"].le(0).any():
        raise ValueError("risk features require strictly positive close prices")
    result = result.sort_values(["symbol", "date"], kind="stable").reset_index(drop=True)
    grouped = result.groupby("symbol", sort=False)
    if "log_return" not in result:
        result["log_return"] = grouped["close"].transform(lambda values: np.log(values).diff())
    result[f"volatility_{volatility_window}d_annualized"] = grouped["log_return"].transform(
        lambda values: values.rolling(volatility_window, min_periods=volatility_window).std(ddof=1)
        * np.sqrt(trading_days)
    )
    running_peak = grouped["close"].cummax()
    result["drawdown"] = result["close"] / running_peak - 1.0
    result["max_drawdown_to_date"] = result.groupby("symbol", sort=False)["drawdown"].cummin()
    return result


def add_momentum(
    prices: pd.DataFrame, periods: tuple[int, ...] = (21, 63, 126),
) -> pd.DataFrame:
    """Add close-to-close momentum using exact trading-observation lags."""
    required = {"symbol", "date", "close"}
    if missing := required - set(prices.columns):
        raise ValueError(f"prices missing momentum inputs: {sorted(missing)}")
    if not periods or any(period < 1 for period in periods):
        raise ValueError("momentum periods must contain positive integers")
    result = prices.copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise")
    result["close"] = pd.to_numeric(result["close"], errors="raise")
    if result["close"].le(0).any():
        raise ValueError("momentum requires strictly positive close prices")
    if result.duplicated(["symbol", "date"]).any():
        raise ValueError("momentum input contains duplicate symbol/date keys")
    result = result.sort_values(["symbol", "date"], kind="stable").reset_index(drop=True)
    grouped = result.groupby("symbol", sort=False)["close"]
    for period in periods:
        result[f"momentum_{period}d"] = grouped.pct_change(periods=period, fill_method=None)
        result[f"momentum_{period}d_n_obs"] = result.groupby("symbol", sort=False).cumcount().clip(upper=period)
    return result
