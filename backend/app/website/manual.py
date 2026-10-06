"""Reprice immutable S/R candidates without hypothetical Converging."""
from copy import deepcopy
import math
import json
import re
import threading
from fastapi import APIRouter, HTTPException
from . import scoring
from .config import STEPS, DAY
from .live import bounds
from .market import timestamp
from .symbols import registry

router = APIRouter(tags=['manual-price'])


def valid_price(raw):
    if not re.fullmatch(r'[+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',str(raw).strip()):
        raise ValueError('Price must be a decimal number')
    try:
        value = float(raw)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('Price must be finite and positive') from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError('Price must be finite and positive')
    return value


_prepare_lock = threading.Lock()


def evaluate(d, price=None, decision=None):
    p = valid_price(price) if price is not None else None
    status = d.status()
    snapshot = status['snapshot']
    if decision is not None and (not snapshot or snapshot['timestamp'] != decision):
        snapshot = d.replay(decision)
    if not snapshot:
        raise ValueError('HISTORY_INCOMPLETE: analysis snapshot unavailable')
    result = deepcopy(snapshot)
    result.update(price_mode='manual' if p is not None else 'current',
                  analysis_price=p if p is not None else snapshot['price'],
                  market_price=(status['ticker'] or {}).get('price'),
                  market_close=snapshot['price'],converging_price_mode='actual_closed_market')
    if p is None:
        return result
    key = (snapshot['timestamp'],snapshot['config_hash'])
    # A worker belongs to exactly one symbol; its bounded maps never cross symbols.
    with _prepare_lock:
        cache = getattr(d,'manual_maps',{})
        if key not in cache:
            prepared = {}
            for tf in STEPS:
                frame = d.store.load(tf,*bounds(tf,snapshot['timestamp'],d.cfg))
                frame = frame[(frame.close_time < snapshot['timestamp']) & (frame.open_time >= snapshot['timestamp']-d.cfg.history_days*DAY)]
                prepared[tf] = (frame,scoring.candidates(frame))
            if len(cache) >= 2:
                cache.pop(next(iter(cache)))
            cache[key] = prepared
            d.manual_maps = cache
        prepared = cache[key]
    rows = {tf:scoring.score(f,tf,p,snapshot['timestamp'],d.cfg,candidate_map=cs) for tf,(f,cs) in prepared.items()}
    result['scoring'] = dict(overall=scoring.combine(rows,d.cfg),timeframes=rows)
    result['descriptions'] = {tf:{scale:{side:result['scoring']['overall']['state']+' + '+row['state']+' '+row.get('actual_direction','') for side,row in sides.items() if side in ('high','low')} for scale,sides in scales.items()} for tf,scales in result['converging'].items()}
    json.dumps(result,allow_nan=False)
    from .scoring_distribution import attach
    return attach(result,d.store,d.cfg)


@router.get('/dashboard/{symbol}/price')
def manual_price(symbol: str, price: str | None = None, at: str | None = None):
    try:
        if price is not None:
            valid_price(price)
        d = registry.get(symbol)
        decision = timestamp(at)//STEPS['15m']*STEPS['15m'] if at else None
        return evaluate(d,price,decision)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
