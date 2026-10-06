from functools import lru_cache
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from .live import Dashboard
from .config import STEPS
from .market import timestamp, FORBIDDEN_START
from . import api

router = APIRouter(tags=['live-dashboard'])


@lru_cache(maxsize=1)
def dashboard():
    return Dashboard()


@router.get('/market/btcusdt/status')
def status():
    d = dashboard()
    d.start()
    return d.status()


@router.get('/dashboard/btcusdt/replay')
def replay(at: str):
    try:
        t = timestamp(at)//STEPS['15m']*STEPS['15m']
        if t <= FORBIDDEN_START:
            result = dict(api.analysis('replay',at))
            from .live import now_ms
            result.update(source_timestamp=result['timestamp'], calculated_timestamp=now_ms(), freshness='REPLAY')
            return result
        return dashboard().replay(t)
    except ValueError as exc:
        raise HTTPException(422, 'HISTORY_INCOMPLETE: '+str(exc)) from exc


@router.get('/analysis/btcusdt/history')
def history(limit: int = Query(30, ge=1, le=100)):
    d = dashboard()
    rows = d.store.history(limit)
    from .scoring_distribution import attach
    return dict(rows=[{k:r.get(k) for k in ['timestamp','price','scoring','scoring_percentile','converging','config_hash','source_timestamp','calculated_timestamp','live_price_at_calculation']} for r in [attach(row,d.store,d.cfg) for row in rows]])


@router.get('/market/btcusdt/candles')
def candles(tf: Literal['15m','1h','4h','1d']='15m', count: int = Query(240, ge=20, le=2000)):
    d = dashboard()
    s = d.status()
    if not s['snapshot']:
        return dict(status='HISTORY_INCOMPLETE', candles=[], timestamp=None)
    end = s['snapshot']['timestamp']//STEPS[tf]*STEPS[tf]
    return dict(status=s['snapshot']['freshness'], timestamp=end,
                candles=d.store.load(tf,end-count*STEPS[tf],end).to_dict('records'))
