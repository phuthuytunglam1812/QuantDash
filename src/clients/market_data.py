"""Normalized daily OHLCV with Alpha Vantage primary and Twelve Data fallback."""

from __future__ import annotations

import os

import pandas as pd
from dotenv import load_dotenv

from .base import BaseHttpClient, DataProviderError, HttpConfig


OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


def _normalize(frame: pd.DataFrame, symbol: str, provider: str) -> pd.DataFrame:
    frame.index = pd.to_datetime(frame.index, errors="coerce")
    frame.index.name = "date"
    frame = frame.rename(columns=lambda value: str(value).split(". ")[-1].lower())
    missing = set(OHLCV_COLUMNS) - set(frame.columns)
    if missing:
        raise DataProviderError(f"{provider} response is missing fields: {sorted(missing)}")
    frame = frame[OHLCV_COLUMNS].apply(pd.to_numeric, errors="coerce")
    frame["symbol"] = symbol.upper()
    frame["provider"] = provider
    return frame.sort_index()


class MarketDataClient(BaseHttpClient):
    def __init__(self, config: HttpConfig | None = None, session=None):
        load_dotenv()
        super().__init__(config=config, session=session)

    def daily_alpha_vantage(self, symbol: str, outputsize: str = "compact") -> pd.DataFrame:
        key = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()
        if not key:
            raise DataProviderError("ALPHA_VANTAGE_API_KEY is missing")
        payload = self.get_json(
            "https://www.alphavantage.co/query",
            params={"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": outputsize, "apikey": key},
        )
        values = payload.get("Time Series (Daily)")
        if not values:
            message = payload.get("Note") or payload.get("Information") or payload.get("Error Message")
            raise DataProviderError(message or "unexpected Alpha Vantage response")
        return _normalize(pd.DataFrame.from_dict(values, orient="index"), symbol, "alpha_vantage")

    def daily_twelve_data(
        self, symbol: str, outputsize: int = 100,
        start_date: str | None = None, end_date: str | None = None,
    ) -> pd.DataFrame:
        key = os.getenv("TWELVE_DATA_API_KEY", "").strip()
        if not key:
            raise DataProviderError("TWELVE_DATA_API_KEY is missing")
        params = {"symbol": symbol, "interval": "1day", "outputsize": outputsize, "apikey": key}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        payload = self.get_json(
            "https://api.twelvedata.com/time_series",
            params=params,
        )
        values = payload.get("values")
        if payload.get("status") == "error" or not values:
            raise DataProviderError(payload.get("message", "unexpected Twelve Data response"))
        return _normalize(pd.DataFrame(values).set_index("datetime"), symbol, "twelve_data")

    def daily(self, symbol: str, allow_fallback: bool = True) -> pd.DataFrame:
        """Fetch from Alpha Vantage, falling back only when explicitly allowed."""
        try:
            return self.daily_alpha_vantage(symbol)
        except DataProviderError as primary_error:
            if not allow_fallback:
                raise
            try:
                return self.daily_twelve_data(symbol)
            except DataProviderError as fallback_error:
                raise DataProviderError(
                    f"all price providers failed; Alpha Vantage: {primary_error}; "
                    f"Twelve Data: {fallback_error}"
                ) from fallback_error
