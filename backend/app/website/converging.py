"""Causal native-clock observations, kept separate by TF, scale and sign."""
import numpy as np
from .config import DAY


def swing_sources(frame, n, side):
    values = frame["high" if side == "high" else "low"].to_numpy()
    sources = np.full(len(frame), -1, dtype=int)
    active = -1
    for j in range(len(frame)):
        i = j-n
        if i >= n:
            others = np.concatenate((values[i-n:i], values[i+1:i+n+1]))
            extreme = (values[i] > others).all() if side == "high" else (values[i] < others).all()
            if extreme:
                active = i
        sources[j] = active
    return sources


def observations(frame, n):
    close = frame.close.to_numpy()
    index = np.arange(len(frame))
    streams = {}
    for side in ["high", "low"]:
        src = swing_sources(frame, n, side)
        valid = src >= 0
        slopes = np.full(len(frame), np.nan)
        e = frame[side].to_numpy()[src[valid]]
        slopes[valid] = np.log(close[valid]/e)/(index[valid]-src[valid])
        streams[side] = dict(source=src, slope=slopes)
    return streams


def distribution(frame, streams, timestamp, direction, cfg, side):
    times = frame.close_time.to_numpy()+1
    mask = (times < timestamp) & (times >= timestamp-cfg.converging_history_days*DAY)
    slope = streams[side]["slope"]
    return np.abs(slope[mask & np.isfinite(slope) & (slope*direction > 0)])


def percentile(samples, magnitude):
    # Empirical CDF with midrank ties, exposed as part of the formula version.
    return float(100*((samples < magnitude).sum()+0.5*(samples == magnitude).sum())/len(samples)) if len(samples) else None


def metrics(samples, slope, cfg):
    result = dict(sample_count=len(samples), signed_slope=float(slope), slope_magnitude=abs(float(slope)),
                  direction="UPWARD_STRETCH" if slope > 0 else "DOWNWARD_STRETCH" if slope < 0 else "FLAT",
                  historical_median=None, quantiles=None, stretch_ratio=None, percentile=None, state="INSUFFICIENT_HISTORY")
    if slope == 0:
        result["state"] = "FLAT"
        return result
    if len(samples) < cfg.min_distribution_samples:
        return result
    q = np.quantile(samples, [.25, .5, .75, .9, .95, .99])
    p = percentile(samples, abs(slope))
    result.update(historical_median=float(q[1]), quantiles=dict(zip(["p25", "p50", "p75", "p90", "p95", "p99"], map(float, q))),
                  stretch_ratio=abs(float(slope))/q[1] if q[1] > 0 else None, percentile=p,
                  state=["NORMAL", "ELEVATED", "STRETCHED", "EXTREME"][int(np.searchsorted(cfg.percentile_bands, p, side="right"))])
    return result


def point(frame, streams, n, side, j, cfg):
    src = int(streams[side]["source"][j])
    if src < 0:
        return dict(source_side=side, state="NO_CONFIRMED_SWING", percentile=None, velocity=None, acceleration=None)
    price = float(frame[side].iloc[src])
    known = int(frame.close_time.iloc[src+n])+1
    history = []
    for k in range(j-2, j+1):
        if k < src+n or streams[side]["source"][k] != src:
            history.append(None)
            continue
        slope = float(np.log(frame.close.iloc[k]/price)/(k-src))
        t = int(frame.close_time.iloc[k])+1
        samples = distribution(frame, streams, t, int(np.sign(slope)), cfg, side)
        m = metrics(samples, slope, cfg)
        history.append(m)
    now = history[-1]
    comparable = lambda a, b: a is not None and b is not None and a["percentile"] is not None and b["percentile"] is not None and a["direction"] == b["direction"]
    velocity = now["percentile"]-history[1]["percentile"] if comparable(now, history[1]) else None
    prior = history[1]["percentile"]-history[0]["percentile"] if comparable(history[1], history[0]) else None
    now.update(source_side=side, source_type=side.upper(), source_id=f'{side}:{n}:{int(frame.open_time.iloc[src])}',
               swing_n=n, actual_direction="UP" if now["signed_slope"] > 0 else "DOWN" if now["signed_slope"] < 0 else "FLAT",
               source_price=price, source_time=int(frame.open_time.iloc[src]), known_at=known,
               elapsed_candles=j-src, observation_time=int(frame.close_time.iloc[j])+1, timestamp=int(frame.close_time.iloc[j])+1,
               velocity=velocity, acceleration=velocity-prior if velocity is not None and prior is not None else None,
               recent_percentiles=[m["percentile"] if m else None for m in history],
               derivative_basis="same extreme; each past point uses its own past-only CDF; null before confirmation or sign change")
    return now


def calculate(frame, cfg):
    result = {}
    for scale, n in cfg.swing_ns.items():
        streams = observations(frame, n)
        result[scale] = dict(n=n, high=point(frame, streams, n, "high", len(frame)-1, cfg),
                             low=point(frame, streams, n, "low", len(frame)-1, cfg))
    return result


def diagnostics(frame, n, cfg, last=64):
    """Retrospective only: fixed entry source and entry CDF, not decision features."""
    streams = observations(frame, n)
    rows = []
    for side in ["high", "low"]:
        prev_extreme = False
        prior_source = None
        # Include the preceding observation to distinguish entries from occupancy.
        for j in range(max(0, len(frame)-last-1), len(frame)):
            p = point(frame, streams, n, side, j, cfg)
            if p.get('source_id') != prior_source:
                prev_extreme = False
            extreme = p.get("percentile") is not None and p["percentile"] >= cfg.percentile_bands[-1]
            if extreme and not prev_extreme and j >= len(frame)-last:
                direction = 1 if p["signed_slope"] > 0 else -1
                samples = distribution(frame, streams, p["observation_time"], direction, cfg, side)
                future = []
                for h in cfg.diagnostic_horizons:
                    if j+h >= len(frame):
                        future.append(dict(horizon=h, status="PENDING", percentile=None))
                        continue
                    slope = float(np.log(frame.close.iloc[j+h]/p["source_price"])/(p["elapsed_candles"]+h))
                    future.append(dict(horizon=h, status="OBSERVED" if slope*direction > 0 else "DIRECTION_CHANGED",
                                       signed_slope=slope, percentile=percentile(samples, abs(slope)) if slope*direction > 0 else None,
                                       observed_at=int(frame.close_time.iloc[j+h])+1))
                rows.append(dict(entry=p, future=future))
            prev_extreme = extreme
            prior_source = p.get('source_id')
    return dict(retrospective_only=True, baseline="frozen entry CDF; same source; sign changes explicit", events=rows)
