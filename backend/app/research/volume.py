"""Exact trade-based volume aggregation. Candle volume is never accepted here."""
from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_FLOOR
import math
from bisect import bisect_left
from collections.abc import Sequence
from .models import Candidate


@dataclass(frozen=True)
class Trade:
    id: str
    timestamp: int
    price: float
    quantity: float
    buyer_is_maker: bool | None
    first_trade_id: int | None = None
    last_trade_id: int | None = None

    def __post_init__(self):
        if not all(math.isfinite(x) and x > 0 for x in (self.price, self.quantity)):
            raise ValueError("Invalid trade price/quantity")
        if self.timestamp < 0 or (self.buyer_is_maker is not None and type(self.buyer_is_maker) is not bool):
            raise ValueError("Invalid trade timestamp/maker flag")

    @classmethod
    def from_binance_aggregate(cls, row):
        return cls(str(row["a"]), int(row["T"]), float(row["p"]), float(row["q"]), row["m"],
                   int(row["f"]) if row.get("f") is not None else None,
                   int(row["l"]) if row.get("l") is not None else None)


def validate_trades(trades):
    if isinstance(trades, TradeIndex):
        return
    if len({t.id for t in trades}) != len(trades):
        raise ValueError("Duplicate trade IDs; deduplicate acquisition before research")
    if any(a.timestamp > b.timestamp for a, b in zip(trades, trades[1:])):
        raise ValueError("Trades must be ordered")


class TradeIndex(Sequence):
    """Immutable, validated timestamp index; preserves original aggregation semantics."""
    def __init__(self, trades):
        self._items = tuple(trades)
        validate_trades(self._items)
        self._times = tuple(t.timestamp for t in self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def window(self, start, end):
        return self._items[bisect_left(self._times, start):bisect_left(self._times, end)]


def trade_window(trades, start, end):
    if isinstance(trades, TradeIndex):
        return trades.window(start, end)
    return (t for t in trades if start <= t.timestamp < end)


def totals(trades):
    total = math.fsum(t.quantity for t in trades)
    unknown = math.fsum(t.quantity for t in trades if t.buyer_is_maker is None)
    buys = math.fsum(t.quantity for t in trades if t.buyer_is_maker is False)
    sells = math.fsum(t.quantity for t in trades if t.buyer_is_maker is True)
    return {"quantity": total, "aggressive_buy_quantity": buys,
            "aggressive_sell_quantity": sells, "unknown_side_quantity": unknown,
            "volume_delta": buys-sells if unknown == 0 else None}


@dataclass(frozen=True)
class VolumeBin:
    lower: float
    upper: float
    quantity: float
    aggressive_buy_quantity: float
    aggressive_sell_quantity: float
    unknown_side_quantity: float
    volume_delta: float | None
    observation_start: int
    observation_end: int
    trade_ids: tuple[str, ...]


def aggregate(trades, bin_size, start, end, as_of):
    validate_trades(trades)
    if not math.isfinite(bin_size) or bin_size <= 0 or not start < end <= as_of:
        raise ValueError("Invalid bin width or future observation window")
    width = Decimal(str(bin_size))
    bins = {}
    for t in trade_window(trades, start, end):
        if start <= t.timestamp < end:
            index = int((Decimal(str(t.price))/width).to_integral_value(rounding=ROUND_FLOOR))
            bins.setdefault(index, []).append(t)
    return [VolumeBin(float(i*width), float((i+1)*width), **totals(ts),
                      observation_start=start, observation_end=end,
                      trade_ids=tuple(t.id for t in ts)) for i, ts in sorted(bins.items())]


class VolumeConcentration:
    """D: occupied-bin quantity / mean occupied-bin quantity >= multiplier.

    Fixed, non-overlapping windows and neutral candidates; no directional claim.
    """
    def __init__(self, trades, bin_size, window_ms, concentration_multiple, start):
        validate_trades(trades)
        if (not math.isfinite(bin_size) or bin_size <= 0 or type(window_ms) is not int
                or window_ms < 1 or not math.isfinite(concentration_multiple)
                or concentration_multiple < 1 or start < 0):
            raise ValueError("Invalid volume detector parameters")
        self.trades = trades
        self.bin_size, self.window_ms = bin_size, window_ms
        self.multiple, self.start = concentration_multiple, start

    def detect(self, candles, timeframe, as_of):
        result = []
        for start in range(self.start, as_of-self.window_ms+1, self.window_ms):
            end = start + self.window_ms
            bins = aggregate(self.trades, self.bin_size, start, end, as_of)
            mean = math.fsum(b.quantity for b in bins)/len(bins) if bins else 0
            for b in bins:
                if mean and b.quantity >= mean*self.multiple:
                    result.append(Candidate("D", "NEUTRAL", (b.lower+b.upper)/2,
                                            start, end, timeframe, (),
                                            {"bin": asdict(b), "bin_size": self.bin_size,
                                             "window_ms": self.window_ms,
                                             "concentration_multiple": self.multiple,
                                             "baseline": "mean_occupied_bin_quantity",
                                             "observed_ratio": b.quantity/mean}))
        return result


def zone_features(zone, trades, as_of, window_ms, coverage_start, coverage_end):
    """Two equal trailing windows; ratio of in-zone quantity rates.

    Coverage endpoints assert acquisition completeness, not first/last trade times.
    """
    validate_trades(trades)
    start, baseline_start = as_of-window_ms, as_of-2*window_ms
    if window_ms <= 0 or as_of < zone.candidate.known_at:
        raise ValueError("Invalid or pre-confirmation feature time")
    if baseline_start < coverage_start or as_of > coverage_end:
        return {"status": "MISSING_TRADE_COVERAGE", "as_of": as_of}
    current = [t for t in trade_window(trades, start, as_of) if zone.lower <= t.price <= zone.upper]
    baseline = [t for t in trade_window(trades, baseline_start, start) if zone.lower <= t.price <= zone.upper]
    facts = totals(current)
    base = totals(baseline)["quantity"]
    return {"status": "AVAILABLE", "as_of": as_of, **facts,
            "window_start": start, "window_end": as_of,
            "baseline_start": baseline_start, "baseline_end": start,
            "baseline_quantity": base, "baseline_definition": "same_zone_previous_equal_duration",
            "relative_zone_volume": facts["quantity"]/base if base else None}
