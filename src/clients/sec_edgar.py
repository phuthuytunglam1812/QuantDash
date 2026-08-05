"""SEC EDGAR submissions and Company Facts client."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from .base import BaseHttpClient, DataProviderError, HttpConfig


class SecEdgarClient(BaseHttpClient):
    BASE_URL = "https://data.sec.gov"

    def __init__(self, config: HttpConfig | None = None, session=None):
        load_dotenv()
        super().__init__(config=config, session=session)
        user_agent = os.getenv("SEC_USER_AGENT", "").strip()
        if not user_agent:
            raise DataProviderError("SEC_USER_AGENT is missing; use 'Name email@example.com'")
        self.headers = {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}

    @staticmethod
    def format_cik(cik: str | int) -> str:
        digits = str(cik).strip().upper().removeprefix("CIK")
        if not digits.isdigit():
            raise ValueError("CIK must contain digits only")
        return digits.zfill(10)

    def company_facts(self, cik: str | int) -> dict:
        cik10 = self.format_cik(cik)
        return self.get_json(f"{self.BASE_URL}/api/xbrl/companyfacts/CIK{cik10}.json", headers=self.headers)

    def submissions(self, cik: str | int) -> dict:
        cik10 = self.format_cik(cik)
        return self.get_json(f"{self.BASE_URL}/submissions/CIK{cik10}.json", headers=self.headers)

    def company_tickers(self) -> dict:
        return self.get_json("https://www.sec.gov/files/company_tickers.json", headers=self.headers)
