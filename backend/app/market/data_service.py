from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

import pandas as pd

from app.market.binance_client import BinanceFuturesClient
from app.market.models import (
    BinanceKlinesQuery,
    Candle,
    CandleGap,
    DatasetSaveResult,
    KlineDownloadResult,
    SUPPORTED_INTERVALS,
)


logger = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_ROOT = ROOT_DIR / "data" / "raw" / "binance"


class DataIntegrityError(ValueError):
    """Raised when candle data fails integrity validation."""


def raw_kline_to_candle(raw: list[object]) -> Candle:
    if len(raw) < 11:
        raise DataIntegrityError("Binance kline payload is missing required fields")

    return Candle(
        open_time=int(raw[0]),
        open=float(raw[1]),
        high=float(raw[2]),
        low=float(raw[3]),
        close=float(raw[4]),
        volume=float(raw[5]),
        close_time=int(raw[6]),
        quote_volume=float(raw[7]),
        trade_count=int(raw[8]),
        taker_buy_volume=float(raw[9]),
        taker_buy_quote_volume=float(raw[10]),
    )


def deduplicate_and_sort_candles(candles: Iterable[Candle]) -> tuple[list[Candle], int]:
    ordered = sorted(candles, key=lambda candle: (candle.open_time, candle.close_time))
    deduped: dict[int, Candle] = {}
    duplicate_count = 0

    for candle in ordered:
        if candle.open_time in deduped:
            duplicate_count += 1
        deduped[candle.open_time] = candle

    return list(deduped.values()), duplicate_count


def detect_gaps(candles: list[Candle], interval: str) -> list[CandleGap]:
    if not candles:
        return []

    step = SUPPORTED_INTERVALS[interval]
    gaps: list[CandleGap] = []
    for previous, current in zip(candles, candles[1:]):
        delta = current.open_time - previous.open_time
        if delta < step:
            raise DataIntegrityError("candles are not strictly chronological after deduplication")
        if delta > step:
            gaps.append(
                CandleGap(
                    expected_open_time=previous.open_time + step,
                    actual_open_time=current.open_time,
                    missing_candle_count=(delta // step) - 1,
                )
            )
    return gaps


def validate_candle_sequence(candles: list[Candle], interval: str) -> list[CandleGap]:
    if not candles:
        raise DataIntegrityError("Binance returned an empty dataset")

    step = SUPPORTED_INTERVALS[interval]
    for candle in candles:
        expected_close_time = candle.open_time + step - 1
        if candle.close_time != expected_close_time:
            raise DataIntegrityError(
                f"close_time mismatch at {candle.open_time}: expected {expected_close_time}, got {candle.close_time}"
            )

    return detect_gaps(candles, interval)


def candles_to_dataframe(candles: list[Candle]) -> pd.DataFrame:
    return pd.DataFrame([candle.model_dump() for candle in candles])


def save_dataset(
    *,
    candles: list[Candle],
    symbol: str,
    interval: str,
    start_time: int | None,
    end_time: int | None,
    save_format: str,
) -> DatasetSaveResult:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    start_label = str(start_time) if start_time is not None else "start"
    end_label = str(end_time) if end_time is not None else "latest"
    filename = f"{symbol}_{interval}_{start_label}_{end_label}.{save_format}"
    path = DATA_ROOT / filename

    frame = candles_to_dataframe(candles)
    if save_format == "parquet":
        frame.to_parquet(path, index=False)
    else:
        frame.to_csv(path, index=False)

    return DatasetSaveResult(path=path, format=save_format)


class HistoricalMarketDataService:
    def __init__(self, client: BinanceFuturesClient | None = None) -> None:
        self.client = client or BinanceFuturesClient()

    def download_klines(self, query: BinanceKlinesQuery) -> KlineDownloadResult:
        logger.info(
            "download_start symbol=%s interval=%s start=%s end=%s limit=%s",
            query.symbol,
            query.interval,
            query.start_time,
            query.end_time,
            query.limit,
        )

        all_candles: list[Candle] = []
        next_start = query.start_time
        step = SUPPORTED_INTERVALS[query.interval]

        while True:
            batch = self.client.get_klines(
                symbol=query.symbol,
                interval=query.interval,
                start_time=next_start,
                end_time=query.end_time,
                limit=query.limit,
            )

            if not batch:
                break

            normalized_batch = [raw_kline_to_candle(item) for item in batch]
            all_candles.extend(normalized_batch)

            last_candle = normalized_batch[-1]
            if next_start is not None and last_candle.open_time < next_start:
                raise DataIntegrityError("pagination did not advance forward")

            next_start = last_candle.open_time + step

            if query.end_time is not None and next_start >= query.end_time:
                break

            if len(batch) < query.limit:
                break

        candles, duplicate_count = deduplicate_and_sort_candles(all_candles)
        gaps = validate_candle_sequence(candles, query.interval)
        if gaps and query.fail_on_gaps:
            raise DataIntegrityError(f"missing candles detected: {len(gaps)} gaps")

        saved = None
        if query.save:
            saved = save_dataset(
                candles=candles,
                symbol=query.symbol,
                interval=query.interval,
                start_time=query.start_time,
                end_time=query.end_time,
                save_format=query.save_format,
            )

        logger.info(
            "download_complete symbol=%s interval=%s candles=%s duplicates=%s gaps=%s saved=%s",
            query.symbol,
            query.interval,
            len(candles),
            duplicate_count,
            len(gaps),
            bool(saved),
        )

        return KlineDownloadResult(
            symbol=query.symbol,
            interval=query.interval,
            requested_start_time=query.start_time,
            requested_end_time=query.end_time,
            candle_count=len(candles),
            candles=candles,
            gaps=gaps,
            duplicate_count=duplicate_count,
            saved=saved,
        )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download Binance Futures klines")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--interval", required=True, choices=sorted(SUPPORTED_INTERVALS.keys()))
    parser.add_argument("--start-time", type=int, default=None)
    parser.add_argument("--end-time", type=int, default=None)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--save-format", choices=["parquet", "csv"], default="parquet")
    parser.add_argument("--fail-on-gaps", action="store_true")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = build_argument_parser()
    args = parser.parse_args()
    query = BinanceKlinesQuery(
        symbol=args.symbol,
        interval=args.interval,
        start_time=args.start_time,
        end_time=args.end_time,
        limit=args.limit,
        save=True,
        save_format=args.save_format,
        fail_on_gaps=args.fail_on_gaps,
    )
    service = HistoricalMarketDataService()
    result = service.download_klines(query)
    print(
        {
            "symbol": result.symbol,
            "interval": result.interval,
            "candle_count": result.candle_count,
            "duplicate_count": result.duplicate_count,
            "gap_count": len(result.gaps),
            "saved_path": str(result.saved.path) if result.saved else None,
        }
    )


if __name__ == "__main__":
    main()

