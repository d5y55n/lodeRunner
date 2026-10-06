from __future__ import annotations

import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class BinanceClientError(RuntimeError):
    """Raised when the Binance API cannot provide a valid response."""


class BinanceFuturesClient:
    BASE_URL = "https://fapi.binance.com"
    KLINES_PATH = "/fapi/v1/klines"

    def __init__(self, timeout: float = 30.0) -> None:
        self._client = httpx.Client(base_url=self.BASE_URL, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def get_klines(
        self,
        *,
        symbol: str,
        interval: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 1000,
    ) -> list[list[Any]]:
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

        try:
            response = self._client.get(self.KLINES_PATH, params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("binance_request_failed symbol=%s interval=%s error=%s", symbol, interval, exc)
            raise BinanceClientError(f"Binance request failed: {exc}") from exc

        payload = response.json()
        if not isinstance(payload, list):
            raise BinanceClientError("Unexpected Binance payload type")
        return payload

