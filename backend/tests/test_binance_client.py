from __future__ import annotations

import httpx
import pytest

from app.market.binance_client import BinanceClientError, BinanceFuturesClient
from app.market.data_service import HistoricalMarketDataService
from app.market.models import BinanceKlinesQuery


def make_raw_kline(open_time: int, close: str = "101.0") -> list[object]:
    return [
        open_time,
        "100.0",
        "110.0",
        "90.0",
        close,
        "12.0",
        open_time + 3_600_000 - 1,
        "1200.0",
        100,
        "6.0",
        "600.0",
        "ignore",
    ]


def test_binance_client_passes_query_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(self: httpx.Client, path: str, params: dict[str, object]) -> httpx.Response:
        captured["path"] = path
        captured["params"] = params
        request = httpx.Request("GET", "https://fapi.binance.com/fapi/v1/klines")
        return httpx.Response(200, json=[], request=request)

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    client = BinanceFuturesClient()

    try:
        client.get_klines(
            symbol="BTCUSDT",
            interval="1h",
            start_time=1000,
            end_time=2000,
            limit=500,
        )
    finally:
        client.close()

    assert captured["path"] == "/fapi/v1/klines"
    assert captured["params"] == {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "startTime": 1000,
        "endTime": 2000,
        "limit": 500,
    }


def test_binance_client_raises_on_http_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(self: httpx.Client, path: str, params: dict[str, object]) -> httpx.Response:
        request = httpx.Request("GET", "https://fapi.binance.com/fapi/v1/klines")
        return httpx.Response(503, json={"msg": "unavailable"}, request=request)

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    client = BinanceFuturesClient()

    with pytest.raises(BinanceClientError):
        client.get_klines(symbol="BTCUSDT", interval="1h")

    client.close()


def test_pagination_collects_multiple_batches() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def get_klines(self, **kwargs: object) -> list[list[object]]:
            self.calls.append(kwargs)
            start_time = kwargs["start_time"]
            if start_time is None:
                return [make_raw_kline(0), make_raw_kline(3_600_000)]
            if start_time == 7_200_000:
                return [make_raw_kline(7_200_000)]
            return []

    service = HistoricalMarketDataService(client=FakeClient())
    result = service.download_klines(
        BinanceKlinesQuery(symbol="BTCUSDT", interval="1h", limit=2)
    )

    assert result.candle_count == 3
    assert [candle.open_time for candle in result.candles] == [0, 3_600_000, 7_200_000]

