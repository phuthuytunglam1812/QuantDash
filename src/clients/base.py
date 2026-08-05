"""Shared HTTP behavior: retries, timeouts, and credential-safe errors."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DataProviderError(RuntimeError):
    """A provider request failed or returned an invalid payload."""


def redact_secrets(message: str) -> str:
    for variable in ("ALPHA_VANTAGE_API_KEY", "TWELVE_DATA_API_KEY"):
        secret = os.getenv(variable, "").strip()
        if secret:
            message = message.replace(secret, "[REDACTED]")
    return re.sub(r"(?i)(apikey=)[^&\s\"']+", r"\1[REDACTED]", message)


@dataclass(frozen=True)
class HttpConfig:
    timeout_seconds: float = 20.0
    retries: int = 3
    backoff_factor: float = 0.5


class BaseHttpClient:
    def __init__(self, config: HttpConfig | None = None, session: requests.Session | None = None):
        self.config = config or HttpConfig()
        self.session = session or requests.Session()
        retry = Retry(
            total=self.config.retries,
            connect=self.config.retries,
            read=self.config.retries,
            status=self.config.retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def get_json(self, url: str, **kwargs) -> dict:
        try:
            response = self.session.get(url, timeout=self.config.timeout_seconds, **kwargs)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise DataProviderError(redact_secrets(str(exc))) from exc
        if not isinstance(payload, dict):
            raise DataProviderError("provider returned a non-object JSON response")
        return payload
