from dataclasses import asdict, dataclass, field
import hashlib
import json
import math


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def identity(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Candle:
    id: str
    start: int
    end: int  # Exclusive end in UTC milliseconds; OHLC becomes known here.
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self):
        if self.start < 0 or self.end <= self.start or not all(math.isfinite(x) and x > 0 for x in
                                             (self.open, self.high, self.low, self.close)):
            raise ValueError("Invalid candle time or price")
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError("Invalid OHLC bounds")


def validate_candles(candles):
    if len({c.id for c in candles}) != len(candles):
        raise ValueError("Duplicate candle identifiers")
    if any(a.end != b.start for a, b in zip(candles, candles[1:])):
        raise ValueError("Candles must be chronological, contiguous and non-overlapping")


@dataclass(frozen=True)
class Candidate:
    detector: str
    kind: str
    price: float
    source_timestamp: int
    known_at: int
    timeframe: str
    source_ids: tuple[str, ...]
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.detector not in ("A", "B", "C", "D") or self.kind not in ("SUPPORT", "RESISTANCE", "NEUTRAL"):
            raise ValueError("Invalid detector or candidate kind")
        if not math.isfinite(self.price) or self.price <= 0 or not 0 <= self.source_timestamp < self.known_at:
            raise ValueError("Invalid price or candidate availability")

    @property
    def id(self):
        return identity(asdict(self))


@dataclass(frozen=True)
class Zone:
    candidate: Candidate
    lower: float
    upper: float
    width_model: str
    width_parameter: float

    def __post_init__(self):
        if not all(math.isfinite(x) for x in (self.lower, self.upper, self.width_parameter)):
            raise ValueError("Nonfinite zone bounds")
        if not 0 < self.lower < self.upper or not 0 < self.width_parameter < 1:
            raise ValueError("Invalid zone bounds/width")

    @property
    def id(self):
        return identity(asdict(self))
