import math
from copy import deepcopy
import numpy as np
from .config import DAY


def candidates(frame):
    """Pair detector only; known_at is the second candle's close boundary."""
    o, h, l, c = (frame[k].to_numpy() for k in ["open", "high", "low", "close"])
    rows = []
    for i in range(1, len(frame)):
        kind = "resistance" if c[i-1] > o[i-1] and c[i] < o[i] else "support" if c[i-1] < o[i-1] and c[i] > o[i] else None
        if kind:
            rows.append(dict(kind=kind, price=float(min(h[i-1], h[i]) if kind == "resistance" else max(l[i-1], l[i])),
                             source_time=int(frame.open_time.iloc[i]), known_at=int(frame.close_time.iloc[i])+1,
                             dependency_start=int(frame.open_time.iloc[i-1])))
    return rows


def age_weight(age_days, cfg):
    if age_days < 0:
        raise ValueError("Future candidate")
    return cfg.recency_floor + (1-cfg.recency_floor)*0.5**(age_days/cfg.half_life_days)


def proximity(price, candidate, width, outer):
    d = abs(price/candidate-1)
    # Resolve binary floating-point rounding of an exact decimal boundary.
    if d <= width or math.isclose(d, width, rel_tol=0, abs_tol=1e-14):
        return 1.0
    return 0.5 if d <= width*outer or math.isclose(d, width*outer, rel_tol=0, abs_tol=1e-14) else 0.0


def state(value, cfg):
    return "SUPPORT" if value > cfg.balanced_band else "RESISTANCE" if value < -cfg.balanced_band else "BALANCED"


def score(frame, tf, price, timestamp, cfg, debug=False, candidate_map=None):
    start = timestamp-cfg.history_days*DAY
    frame = frame[(frame.close_time < timestamp) & (frame.open_time >= start)]
    cs = candidates(frame) if candidate_map is None else deepcopy(candidate_map)
    names = ["0-30d", "30-90d", "90-180d", "180-365d", "365d+"]
    buckets = [dict(age=name, support_count=0, resistance_count=0, weighted_support=0., weighted_resistance=0.) for name in names]
    total = {"support": 0., "resistance": 0.}
    raw = {"support": 0, "resistance": 0}
    legacy = 0.
    for c in cs:
        age = (timestamp-c["known_at"])/DAY
        p = proximity(price, c["price"], cfg.widths[tf], cfg.outer_multiplier)
        value = p*age_weight(age, cfg)
        c.update(age_days=age, proximity_weight=p, age_weight=age_weight(age, cfg), contribution=value)
        total[c["kind"]] += value
        raw[c["kind"]] += int(p > 0)
        legacy += p*(1 if c["kind"] == "support" else -1)
        b = buckets[int(np.searchsorted([30, 90, 180, 365], age, side="right"))]
        b[c["kind"]+"_count"] += 1
        b["weighted_"+c["kind"]] += value
    denom = sum(total.values())
    normalized = (total["support"]-total["resistance"])/denom if denom else 0.
    nearest = {}
    for side in total:
        group = [c for c in cs if c["kind"] == side]
        c = min(group, key=lambda x: (abs(x["price"]-price), x["known_at"], x["price"])) if group else None
        nearest[side] = dict(price=c["price"], distance_pct=100*(c["price"]/price-1), known_at=c["known_at"]) if c else None
    result = dict(tf=tf, normalized=normalized, state=state(normalized, cfg), available=bool(denom),
                  raw_support_count=raw["support"], raw_resistance_count=raw["resistance"],
                  map_support_count=sum(c["kind"] == "support" for c in cs), map_resistance_count=sum(c["kind"] == "resistance" for c in cs),
                  weighted_support=total["support"], weighted_resistance=total["resistance"], legacy_score=legacy,
                  weight=cfg.tf_weights[tf], weighted_contribution=normalized*cfg.tf_weights[tf],
                  nearest=nearest, age_buckets=buckets, evaluation_price=price,
                  source_close=int(frame.close_time.iloc[-1])+1 if len(frame) else None)
    if debug:
        result["candidates"] = cs
    return result


def combine(rows, cfg):
    value = sum(r["weighted_contribution"] for r in rows.values())
    normalized = value/sum(cfg.tf_weights.values())
    return dict(combined_score=value, combined_normalized=normalized, state=state(normalized, cfg),
                no_structure_timeframes=[tf for tf, r in rows.items() if not r["available"]])
