from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.market.data_service import (
    DATA_ROOT,
    DataIntegrityError,
    HistoricalMarketDataService,
    deduplicate_and_sort_candles,
    detect_gaps,
    raw_kline_to_candle,
    save_dataset,
    validate_candle_sequence,
)
from app.market.models import BinanceKlinesQuery, Candle


def make_candle(open_time: int, *, open_: float = 100.0, high: float = 110.0, low: float = 90.0, close: float = 105.0) -> Candle:
    return Candle(
        open_time=open_time,
        close_time=open_time + 3_600_000 - 1,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=10.0,
        quote_volume=1000.0,
        trade_count=5,
        taker_buy_volume=4.0,
        taker_buy_quote_volume=400.0,
    )


def test_raw_kline_to_candle_maps_fields() -> None:
    candle = raw_kline_to_candle(
        [0, "1", "3", "0.5", "2", "10", 3_599_999, "20", 7, "4", "8", "ignore"]
    )

    assert candle.open == 1.0
    assert candle.high == 3.0
    assert candle.low == 0.5
    assert candle.close == 2.0
    assert candle.trade_count == 7


def test_ohlc_validation_rejects_invalid_high() -> None:
    with pytest.raises(ValueError):
        make_candle(0, high=100.0, close=105.0)


def test_duplicate_removal_is_deterministic() -> None:
    earlier = make_candle(0, close=101.0)
    later = make_candle(0, close=102.0)
    sorted_candles, duplicate_count = deduplicate_and_sort_candles([later, earlier])

    assert duplicate_count == 1
    assert len(sorted_candles) == 1
    assert sorted_candles[0].close == 101.0


def test_validate_candle_sequence_detects_gaps() -> None:
    candles = [make_candle(0), make_candle(7_200_000)]
    gaps = validate_candle_sequence(candles, "1h")

    assert len(gaps) == 1
    assert gaps[0].expected_open_time == 3_600_000
    assert gaps[0].missing_candle_count == 1


def test_validate_candle_sequence_rejects_bad_close_time() -> None:
    candle = Candle(
        open_time=0,
        close_time=1,
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

    with pytest.raises(DataIntegrityError):
        validate_candle_sequence([candle], "1h")


def test_download_raises_when_fail_on_gaps_enabled() -> None:
    class FakeClient:
        def get_klines(self, **kwargs: object) -> list[list[object]]:
            return [
                [0, "100", "110", "90", "105", "1", 3_599_999, "1", 1, "1", "1", "ignore"],
                [7_200_000, "100", "110", "90", "105", "1", 10_799_999, "1", 1, "1", "1", "ignore"],
            ]

    service = HistoricalMarketDataService(client=FakeClient())
    query = BinanceKlinesQuery(
        symbol="BTCUSDT",
        interval="1h",
        fail_on_gaps=True,
    )

    with pytest.raises(DataIntegrityError):
        service.download_klines(query)


def test_save_dataset_writes_csv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.market.data_service.DATA_ROOT", tmp_path)
    result = save_dataset(
        candles=[make_candle(0)],
        symbol="BTCUSDT",
        interval="1h",
        start_time=0,
        end_time=3_600_000,
        save_format="csv",
    )

    assert result.path.exists()
    frame = pd.read_csv(result.path)
    assert len(frame) == 1
    assert frame.iloc[0]["open_time"] == 0
