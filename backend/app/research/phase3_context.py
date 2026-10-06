"""Development-only quantiles and causal historical matching; no future labels."""
from dataclasses import dataclass
import bisect
import math
import numpy as np
from .models import identity,validate_candles


def contexts(candles, lookback=24):
    validate_candles(candles)
    if lookback < 2:
        raise ValueError("Context window needs at least two candles")
    records = []
    for i,c in enumerate(candles):
        if i < lookback:
            continue
        window = candles[i-lookback:i+1]
        returns = np.diff(np.log([x.close for x in window]))
        records.append({"timestamp":c.end,"volatility":float(np.std(returns,ddof=0)),
                        "recent_return":c.close/window[0].close-1,
                        "source_start":window[0].start,"source_end":c.end})
    return records


@dataclass(frozen=True)
class Quantiles:
    field: str
    cuts: tuple[float,...]
    development_end: int
    sample_count: int

    @classmethod
    def fit(cls,field,records,development_end,groups=4):
        if groups < 2:
            raise ValueError("At least two quantile groups")
        if any(r["timestamp"] >= development_end for r in records):
            raise ValueError("Bucket fitting received non-development observations")
        values = [r[field] for r in records if r.get(field) is not None and math.isfinite(r[field])]
        if not values:
            raise ValueError("No finite development observations for quantiles")
        cuts = tuple(float(x) for x in np.quantile(values,np.arange(1,groups)/groups))
        return cls(field,cuts,development_end,len(values))

    def bucket(self,value):
        if value is None or not math.isfinite(value):
            return "MISSING"
        return f"Q{bisect.bisect_right(self.cuts,value)+1}"


def matched_control(target, pool, volatility_buckets, return_buckets, horizon_ms):
    """Most recent earlier context match whose full outcome window is already past.

    Matching sees context only, never its outcome. Development bucket fits are
    descriptive in-sample; validation must use a previously frozen fit.
    """
    if max(volatility_buckets.development_end,return_buckets.development_end) > target["timestamp"]:
        raise ValueError("Matcher bucket thresholds were not available at target time")
    eligible = [r for r in pool if r["timestamp"]+horizon_ms <= target["timestamp"]
                and r["timestamp"] < target["timestamp"]
                and volatility_buckets.bucket(r["volatility"])==volatility_buckets.bucket(target["volatility"])
                and return_buckets.bucket(r["recent_return"])==return_buckets.bucket(target["recent_return"])]
    return max(eligible,key=lambda r:r["timestamp"]) if eligible else None


class ControlIndex:
    """Indexed equivalent of matched_control; only context records are indexed."""
    def __init__(self,pool,volatility_buckets,return_buckets):
        self.models=(volatility_buckets,return_buckets)
        self.cells={}
        for record in sorted(pool,key=lambda r:r["timestamp"]):
            self.cells.setdefault(self.key(record),[]).append(record)
        self.times={key:[r["timestamp"] for r in rows] for key,rows in self.cells.items()}

    def key(self,record):
        return tuple(m.bucket(record[m.field]) for m in self.models)

    def match(self,target,horizon_ms):
        if horizon_ms<=0:raise ValueError("Positive matching horizon required")
        if max(m.development_end for m in self.models)>target["timestamp"]:
            raise ValueError("Matcher bucket thresholds were not available at target time")
        key=self.key(target)
        index=bisect.bisect_right(self.times.get(key,[]),target["timestamp"]-horizon_ms)-1
        return self.cells[key][index] if index>=0 else None


def frozen_subset(configurations,bucket_models,development_end,selection_rule=None):
    from dataclasses import asdict
    payload = {"configurations":configurations,"bucket_models":[asdict(b) for b in bucket_models],
               "development_end":development_end,"selection_uses":"development_only"}
    if selection_rule is not None:payload["selection_rule"]=selection_rule
    return {**payload,"freeze_id":identity(payload)}


def verify_freeze(frozen):
    if frozen.get("freeze_id")!=identity({k:v for k,v in frozen.items() if k!="freeze_id"}):
        raise ValueError("Frozen validation configuration was modified")
