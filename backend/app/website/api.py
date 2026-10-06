from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from .config import STEPS, Settings, settings
from . import market, scoring, converging

router = APIRouter(tags=['analysis-website'])


def parameters(mode, at):
    cfg = settings()
    t = market.timestamp(at or cfg.replay_default) if mode == 'replay' else int(datetime.now(timezone.utc).timestamp()*1000)
    if mode == 'live' and at is not None:
        raise ValueError("Live mode does not accept a historical timestamp")
    return cfg, t//STEPS['15m']*STEPS['15m']


@lru_cache(maxsize=6)
def analyze(mode, t, config_json):
    cfg = Settings.model_validate_json(config_json)
    frames, sources = {}, {}
    for tf in STEPS:
        frames[tf], sources[tf] = market.load(tf, t, cfg, mode)
    return evaluate_frames(mode, t, config_json, frames, sources)


def evaluate_frames(mode, t, config_json, frames, sources, symbol='BTCUSDT'):
    """Shared v1 engine. Providers are responsible for complete, closed native frames."""
    cfg = Settings.model_validate_json(config_json)
    price = float(frames['15m'].close.iloc[-1])
    scores = {tf: scoring.score(f, tf, price, t, cfg) for tf, f in frames.items()}
    overall = scoring.combine(scores, cfg)
    slopes = {tf: converging.calculate(f, cfg) for tf, f in frames.items()}
    descriptions = {}
    for tf, scales in slopes.items():
        descriptions[tf] = {}
        for scale, sides in scales.items():
            descriptions[tf][scale] = {}
            for side in ['high', 'low']:
                r = sides[side]
                r['timeframe'] = tf
                if r.get('source_id'):
                    r['source_id'] = tf+':'+r['source_id']
                    if symbol != 'BTCUSDT':
                        r['source_id'] = symbol+':'+r['source_id']
                descriptions[tf][scale][side] = overall['state']+' + '+r['state']+' '+r.get('actual_direction', '')
    return dict(symbol=symbol, mode=mode, timestamp=t, price=price, price_basis='Latest fully closed 15m close; not a live ticker quote',
                data_status='REPLAY' if mode == 'replay' else 'CLOSED_CANDLE_LIVE',
                scoring=dict(overall=overall, timeframes=scores), converging=slopes, descriptions=descriptions,
                charts={tf: f.tail(cfg.chart_candles).to_dict('records') for tf, f in frames.items()},
                config=cfg.model_dump(), config_hash=hashlib.sha256(config_json.encode()).hexdigest(), sources=sources,
                warnings=['Descriptive analysis, not probability or a trading rule.', 'Empirical slope normalization is not proof of mean reversion.',
                          'Repeated observations from one source are serially dependent.', 'Scoring uses common 15m P; Converging uses each native closed price.',
                          'Inclusive proximity endpoints intentionally differ from strict legacy research endpoints.',
                          'Swing bootstrap: 2*max(N)+3 earlier candles. Until the first confirmed source, observations are absent, never backfilled.'])


@router.get('/analysis/btcusdt')
def analysis(mode: Literal['replay', 'live'] = 'replay', at: str | None = None):
    try:
        cfg, t = parameters(mode, at)
        return analyze(mode, t, cfg.model_dump_json())
    except (ValueError, OSError) as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, 'Market data unavailable; no synthetic fallback: '+str(exc)) from exc


@router.get('/analysis/config')
def config():
    return settings().model_dump()


@router.get('/analysis/btcusdt/debug')
def debug(tf: Literal['15m', '1h', '4h', '1d'] = '15m', at: str | None = None):
    try:
        cfg, t = parameters('replay', at)
        f, _ = market.load(tf, t, cfg, 'replay')
        current, _ = market.load('15m', t, cfg, 'replay')
        return scoring.score(f, tf, float(current.close.iloc[-1]), t, cfg, debug=True)
    except (ValueError, OSError) as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get('/analysis/btcusdt/observations')
def observations(tf: Literal['15m', '1h', '4h', '1d'] = '15m', scale: Literal['short', 'medium', 'long'] = 'medium',
                 at: str | None = None, count: int = Query(12, ge=1, le=64)):
    try:
        cfg, t = parameters('replay', at)
        f, _ = market.load(tf, t, cfg, 'replay')
        n = cfg.swing_ns[scale]
        streams = converging.observations(f, n)
        rows = []
        for j in range(max(0, len(f)-count), len(f)):
            for side in ['high', 'low']:
                row = converging.point(f, streams, n, side, j, cfg)
                row.update(timeframe=tf, swing_n=n, timestamp=int(f.close_time.iloc[j])+1)
                if row.get('source_id'):
                    row['source_id'] = tf+':'+row['source_id']
                rows.append(row)
        return dict(observations=rows, distribution_key=['timeframe', 'swing_n', 'source_type', 'actual_direction'])
    except (ValueError, OSError) as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get('/analysis/btcusdt/diagnostics')
def diagnostics(tf: Literal['15m', '1h', '4h', '1d'] = '15m', scale: Literal['short', 'medium', 'long'] = 'medium', at: str | None = None):
    try:
        cfg, t = parameters('replay', at)
        f, _ = market.load(tf, t, cfg, 'replay')
        return converging.diagnostics(f, cfg.swing_ns[scale], cfg)
    except (ValueError, OSError) as exc:
        raise HTTPException(422, str(exc)) from exc
