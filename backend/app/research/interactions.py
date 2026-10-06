from dataclasses import dataclass, field
from .models import validate_candles


@dataclass(frozen=True)
class ExitRule:
    model: str = "boundary"
    separation_fraction: float = 0.0

    def __post_init__(self):
        if self.model not in ("boundary", "confirmed") or not 0 <= self.separation_fraction < 1:
            raise ValueError("Invalid exit rule")
        if self.model == "boundary" and self.separation_fraction != 0:
            raise ValueError("Boundary exit cannot have separation")


@dataclass
class Interaction:
    zone_id: str
    number: int
    start: int
    observed_at: int
    entry_price: float
    approach: str
    end: int | None = None
    state: str = "ENTERED"
    wick_touched: bool = False
    close_entered: bool = False
    max_penetration_price: float | None = 0.0
    max_penetration_zone_fraction: float | None = 0.0
    candles_spent: int = 0
    exit_direction: str | None = None
    crossed_through: bool | None = False
    transitions: list = field(default_factory=list)


def side(price, zone):
    return "ABOVE" if price > zone.upper else "BELOW" if price < zone.lower else "INSIDE"


def track(zone, candles, rule=ExitRule()):
    validate_candles(candles)
    result = []
    active = None
    previous = None
    for c in candles:
        if c.start < zone.candidate.known_at:
            previous = c
            continue
        overlap = c.high >= zone.lower and c.low <= zone.upper
        if active is None and overlap:
            approach = side(previous.close if previous else c.open, zone)
            active = Interaction(zone.id, len(result)+1, c.start, c.end, c.close, approach)
            active.transitions = [("OUTSIDE", c.start), ("ENTERED", c.end)]
            if approach == "INSIDE":
                active.max_penetration_price = active.max_penetration_zone_fraction = None
                active.crossed_through = None
            result.append(active)
        elif active is not None and active.state == "ENTERED":
            active.state = "INTERACTING"
            active.transitions.append(("INTERACTING", c.end))
        if active is not None:
            active.candles_spent += 1
            if overlap:
                # A wick is a price interval outside the real candle body.
                wick = ((c.low < min(c.open, c.close) and c.low <= zone.upper
                         and min(c.open, c.close) >= zone.lower) or
                        (c.high > max(c.open, c.close) and c.high >= zone.lower
                         and max(c.open, c.close) <= zone.upper))
                active.wick_touched |= wick
                active.close_entered |= zone.lower <= c.close <= zone.upper
                if active.approach != "INSIDE":
                    penetration = (zone.upper - c.low if active.approach == "ABOVE"
                                   else c.high - zone.lower)
                    active.max_penetration_price = max(active.max_penetration_price, penetration)
                    active.max_penetration_zone_fraction = active.max_penetration_price / (zone.upper-zone.lower)
            distance = zone.candidate.price * rule.separation_fraction
            direction = ("ABOVE" if c.close > zone.upper + distance else
                         "BELOW" if c.close < zone.lower - distance else None)
            opposite = "BELOW" if active.approach == "ABOVE" else "ABOVE"
            if active.approach != "INSIDE" and side(c.close, zone) == opposite:
                active.crossed_through = True
            if direction:
                active.end, active.exit_direction, active.state = c.end, direction, "EXITED"
                active.transitions.append(("EXITED", c.end))
                active = None
        previous = c
    return result
