from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SUPPORTED_INTERVALS = {
    "15m": 15 * 60 * 1000,
    "1h": 60 * 60 * 1000,
    "4h": 4 * 60 * 60 * 1000,
    "1d": 24 * 60 * 60 * 1000,
}


class Candle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    open_time: int
    close_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    trade_count: int
    taker_buy_volume: float
    taker_buy_quote_volume: float

    @field_validator("open_time", "close_time", "trade_count")
    @classmethod
    def validate_non_negative_ints(cls, value: int) -> int:
        if value < 0:
            raise ValueError("value must be non-negative")
        return value

    @field_validator(
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "taker_buy_volume",
        "taker_buy_quote_volume",
    )
    @classmethod
    def validate_finite_numbers(cls, value: float) -> float:
        if value != value:
            raise ValueError("value must not be NaN")
        return float(value)

    @model_validator(mode="after")
    def validate_ohlc(self) -> "Candle":
        if self.close_time <= self.open_time:
            raise ValueError("close_time must be greater than open_time")
        if self.high < max(self.open, self.close):
            raise ValueError("high must be >= max(open, close)")
        if self.low > min(self.open, self.close):
            raise ValueError("low must be <= min(open, close)")
        if self.high < self.low:
            raise ValueError("high must be >= low")
        if self.volume < 0 or self.quote_volume < 0:
            raise ValueError("volume must be non-negative")
        if self.taker_buy_volume < 0 or self.taker_buy_quote_volume < 0:
            raise ValueError("taker buy volume must be non-negative")
        return self


class CandleGap(BaseModel):
    expected_open_time: int
    actual_open_time: int
    missing_candle_count: int


class DatasetSaveResult(BaseModel):
    path: Path
    format: Literal["parquet", "csv"]


class KlineDownloadResult(BaseModel):
    symbol: str
    interval: str
    requested_start_time: int | None = None
    requested_end_time: int | None = None
    candle_count: int
    candles: list[Candle]
    gaps: list[CandleGap] = Field(default_factory=list)
    duplicate_count: int = 0
    saved: DatasetSaveResult | None = None


class BinanceKlinesQuery(BaseModel):
    symbol: str = Field(min_length=1)
    interval: str
    start_time: int | None = Field(default=None, ge=0)
    end_time: int | None = Field(default=None, ge=0)
    limit: int = Field(default=1000, ge=1, le=1500)
    save: bool = False
    save_format: Literal["parquet", "csv"] = "parquet"
    fail_on_gaps: bool = False

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.upper()

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, value: str) -> str:
        if value not in SUPPORTED_INTERVALS:
            raise ValueError(
                f"unsupported interval '{value}'. Supported: {', '.join(SUPPORTED_INTERVALS)}"
            )
        return value

    @model_validator(mode="after")
    def validate_time_range(self) -> "BinanceKlinesQuery":
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be greater than start_time")
        return self

