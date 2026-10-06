from dataclasses import dataclass
import math
from .models import validate_candles


@dataclass(frozen=True)
class Outcome:
    direction: str
    tp: float
    sl: float
    horizon: int
    label: str | None
    first_hit_at: int | None
    mfe_pct: float
    mae_pct: float
    time_to_mfe_ms: int | None
    time_to_mae_ms: int | None
    observed_candles: int
    censored: bool
    measured_until: int


def measure(entry_price, observed_at, candles, direction, tp, sl, horizon):
    validate_candles(candles)
    if (not math.isfinite(entry_price) or entry_price <= 0 or observed_at < 0
            or direction not in ("LONG", "SHORT") or not 0 < tp < 1 or not 0 < sl < 1
            or type(horizon) is not int or horizon < 1):
        raise ValueError("Invalid outcome configuration")
    future = [c for c in candles if c.start >= observed_at][:horizon]
    target = entry_price * (1+tp if direction == "LONG" else 1-tp)
    stop = entry_price * (1-sl if direction == "LONG" else 1+sl)
    label = hit_at = None
    mfe = mae = 0.0
    tmfe = tmae = None
    for c in future:
        favorable = (c.high/entry_price-1 if direction == "LONG" else 1-c.low/entry_price)*100
        adverse = (1-c.low/entry_price if direction == "LONG" else c.high/entry_price-1)*100
        if favorable > mfe:
            mfe, tmfe = favorable, c.end-observed_at
        if adverse > mae:
            mae, tmae = adverse, c.end-observed_at
        if label is not None:
            continue
        # The open is known to precede the candle's extremes, including gap cases.
        open_tp = c.open >= target if direction == "LONG" else c.open <= target
        open_sl = c.open <= stop if direction == "LONG" else c.open >= stop
        touch_tp = c.high >= target if direction == "LONG" else c.low <= target
        touch_sl = c.low <= stop if direction == "LONG" else c.high >= stop
        if open_tp or open_sl:
            label, hit_at = ("TP_FIRST" if open_tp else "SL_FIRST"), c.start
        elif touch_tp or touch_sl:
            label = "AMBIGUOUS" if touch_tp and touch_sl else "TP_FIRST" if touch_tp else "SL_FIRST"
            hit_at = c.end
    censored = len(future) < horizon
    if label is None and not censored:
        label = "NEITHER"
    return Outcome(direction, tp, sl, horizon, label, hit_at, mfe, mae, tmfe, tmae,
                   len(future), censored, future[-1].end if future else observed_at)
