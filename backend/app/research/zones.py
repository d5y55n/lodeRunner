from typing import Protocol
from .models import Zone

FIXED_WIDTHS = (0.0005, 0.001, 0.002, 0.003, 0.005)
ORIGINAL_WIDTHS = {"15m": 0.002, "1h": 0.004, "4h": 0.007, "1d": 0.022}


class AdaptiveWidth(Protocol):
    """Implementations receive ONLY candles closed by candidate.known_at."""
    name: str
    def fraction(self, candidate, history) -> float: ...


def construct(candidate, model, parameter=None, adaptive=None, candles=()):
    if model == "original_timeframe":
        fraction = ORIGINAL_WIDTHS[candidate.timeframe]
        if parameter is not None and parameter != fraction:
            raise ValueError("Parameter does not match original timeframe mapping")
    elif model == "fixed_percentage":
        fraction = parameter
    elif model == "adaptive" and adaptive is not None:
        history = tuple(c for c in candles if c.end <= candidate.known_at)
        fraction = adaptive.fraction(candidate, history)
        model = "adaptive:" + adaptive.name
    else:
        raise ValueError("Unknown zone-width model")
    if fraction is None or not 0 < fraction < 1:
        raise ValueError("Zone half-width must be between 0 and 1")
    return Zone(candidate, candidate.price * (1-fraction), candidate.price * (1+fraction),
                model, fraction)
