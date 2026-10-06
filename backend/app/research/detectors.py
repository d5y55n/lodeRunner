from typing import Protocol
from .models import Candidate, validate_candles


class Detector(Protocol):
    def detect(self, candles, timeframe: str, as_of: int) -> list[Candidate]: ...


def available(candles, as_of):
    validate_candles(candles)
    return [c for c in candles if c.end <= as_of]


class ReversalCandles:
    """Exact reference selection from original scoring.js, without any weights."""

    def detect(self, candles, timeframe, as_of):
        result = []
        cs = available(candles, as_of)
        for before, after in zip(cs, cs[1:]):
            if before.close > before.open and after.close < after.open:
                chosen = after if before.high > after.high else before
                kind, price = "RESISTANCE", chosen.high
            elif before.close < before.open and after.close > after.open:
                chosen = after if before.low < after.low else before
                kind, price = "SUPPORT", chosen.low
            else:
                continue
            result.append(Candidate("A", kind, price, chosen.start, after.end,
                                    timeframe, (before.id, after.id),
                                    {"reference_candle_id": chosen.id, "rule": "original_scoring_js"}))
        return result


class LocalExtrema:
    def __init__(self, width):
        if not isinstance(width, int) or width < 1:
            raise ValueError("width must be a positive integer")
        self.width = width

    def detect(self, candles, timeframe, as_of):
        cs = available(candles, as_of)
        result = []
        w = self.width
        for i in range(w, len(cs) - w):
            c = cs[i]
            window = cs[i-w:i+w+1]
            neighbors = [x for j, x in enumerate(window) if j != w]
            for kind, price, qualifies in (
                ("RESISTANCE", c.high, all(c.high > x.high for x in neighbors)),
                ("SUPPORT", c.low, all(c.low < x.low for x in neighbors)),
            ):
                if qualifies:
                    result.append(Candidate("B", kind, price, c.start, window[-1].end,
                                            timeframe, tuple(x.id for x in window),
                                            {"width": w, "ties": "strict_exclude"}))
        return result


class ConfirmedReversal:
    """Independent running high/low trackers; later candle close confirms reversal.

    A candle establishing a new extreme cannot confirm that same extreme.
    After confirmation each tracker resets to the confirming candle.
    """

    def __init__(self, reversal_fraction):
        if not 0 < reversal_fraction < 1:
            raise ValueError("reversal_fraction must be between 0 and 1")
        self.fraction = reversal_fraction

    def detect(self, candles, timeframe, as_of):
        cs = available(candles, as_of)
        if not cs:
            return []
        result = []
        high = low = cs[0]
        for c in cs[1:]:
            if c.high > high.high:
                high = c
            elif c.close <= high.high * (1 - self.fraction):
                result.append(self.event("RESISTANCE", high, high.high, c, timeframe))
                high = c
            if c.low < low.low:
                low = c
            elif c.close >= low.low * (1 + self.fraction):
                result.append(self.event("SUPPORT", low, low.low, c, timeframe))
                low = c
        return result

    def event(self, kind, extreme, price, confirmation, timeframe):
        return Candidate("C", kind, price, extreme.start, confirmation.end, timeframe,
                         (extreme.id, confirmation.id),
                         {"reversal_fraction": self.fraction, "confirmation": "later_close",
                          "reset": "confirmation_candle", "ties": "earliest_extreme"})


def make_detector(name, parameters):
    if name == "A" and not parameters:
        return ReversalCandles()
    if name == "B" and set(parameters) == {"width"}:
        return LocalExtrema(**parameters)
    if name == "C" and set(parameters) == {"reversal_fraction"}:
        return ConfirmedReversal(**parameters)
    raise ValueError("Unsupported detector or parameter set")
