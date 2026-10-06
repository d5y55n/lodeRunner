from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.api.market_routes import get_market_data_service
from app.market.data_service import HistoricalMarketDataService
from app.market.models import Candle, DatasetSaveResult, KlineDownloadResult


def make_result() -> KlineDownloadResult:
    candle = Candle(
        open_time=0,
        close_time=3_599_999,
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=10.0,
        quote_volume=1000.0,
        trade_count=5,
        taker_buy_volume=4.0,
        taker_buy_quote_volume=400.0,
    )
    return KlineDownloadResult(
        symbol="BTCUSDT",
        interval="1h",
        requested_start_time=0,
        requested_end_time=3_600_000,
        candle_count=1,
        candles=[candle],
        duplicate_count=0,
        gaps=[],
        saved=DatasetSaveResult(path="data/raw/binance/sample.parquet", format="parquet"),
    )


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_market_endpoint_returns_service_result() -> None:
    class FakeService(HistoricalMarketDataService):
        def __init__(self) -> None:
            pass

        def download_klines(self, query):  # type: ignore[override]
            return make_result()

    app.dependency_overrides[get_market_data_service] = FakeService

    client = TestClient(app)
    response = client.get("/market/binance/klines?symbol=BTCUSDT&interval=1h&start_time=0&end_time=3600000")

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "BTCUSDT"
    assert payload["candle_count"] == 1

    app.dependency_overrides.clear()
