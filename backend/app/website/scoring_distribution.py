"""Operational, symbol-local, prior-only Scoring observations; no formula changes."""
from copy import deepcopy
import hashlib
import json
import sqlite3
import threading
from pathlib import Path

import numpy as np

from . import scoring, converging
from .config import DAY, STEPS
from .market import validate

VERSION = 'scoring-distribution-v1-midrank-full-lookback'
_lock = threading.RLock()


def identity(symbol, cfg):
    raw = dict(symbol=symbol, config=cfg.model_dump(), version=VERSION,
               formula=hashlib.sha256(Path(scoring.__file__).read_bytes()).hexdigest(),
               lookback_days=cfg.history_days)
    return hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()


def summary(values, levels):
    values = np.asarray(values, dtype=float)
    result = dict(count=len(values))
    result.update({f'q{q:02}':float(np.quantile(values,q/100)) if len(values) else None for q in levels})
    return result


def describe(rows, timestamp, value, cfg, symbol, key):
    prior = [(int(t), float(v)) for t,v in rows if timestamp-cfg.history_days*DAY <= t < timestamp]
    values = np.array([v for _,v in prior], dtype=float)
    positive, negative = values[values>0], -values[values<0]
    signed = summary(values,[1,5,10,25,50,75,90,95,99])
    signed.update({name:float(fn(values)) if len(values) else None for name,fn in
                   [('min',np.min),('max',np.max),('mean',np.mean),('median',np.median)]})
    direction = 'SUPPORT' if value>0 else 'RESISTANCE' if value<0 else 'BALANCED'
    samples = positive if value>0 else negative if value<0 else np.array([])
    p = converging.percentile(samples,abs(value)) if value!=0 and len(samples)>=cfg.min_distribution_samples else None
    counts, edges = np.histogram(values,bins=np.linspace(-1,1,41))
    return dict(direction=direction, percentile=p, sample_count=len(samples),
                status='BALANCED' if value==0 else 'READY' if p is not None else 'INSUFFICIENT_HISTORY',
                label=['NORMAL','ELEVATED','STRONG','EXTREME'][int(np.searchsorted([75,90,95],p,side='right'))] if p is not None else None,
                distribution_version=VERSION, distribution_key=key, symbol=symbol,
                observation_score=value, decision_timestamp=timestamp,
                minimum_samples=cfg.min_distribution_samples, lookback_days=cfg.history_days,
                coverage_start=prior[0][0] if prior else None, coverage_end=prior[-1][0] if prior else None,
                coverage_basis='Available complete-lookback decisions only; no shortened scoring windows',
                statistics=dict(signed=signed,positive=summary(positive,[50,75,90,95,99]),
                                negative_magnitude=summary(negative,[50,75,90,95,99])),
                histogram=dict(edges=edges.tolist(),counts=counts.tolist()))


def historical_scores(frames, times, cfg):
    """Same pair candidates/proximity/recency and ordered sums as scoring.score.

    Vectorized weights omit debug/map rendering only. Each candidate requires both
    candles in the decision's rolling window and known_at <= that decision.
    """
    prepared = {}
    for tf,f in frames.items():
        cs = scoring.candidates(f)
        prepared[tf] = {k:np.array([c[k] for c in cs]) for k in ['price','known_at','dependency_start','kind']}
    clock = frames['15m'].close_time.to_numpy()+1
    prices = frames['15m'].close.to_numpy()
    for t in times:
        price = float(prices[np.searchsorted(clock,t,side='right')-1])
        total = 0.
        for tf in STEPS:
            c = prepared[tf]
            mask = (c['known_at']<=t)&(c['dependency_start']>=t-cfg.history_days*DAY)
            cp = c['price'][mask].astype(float)
            distance = np.abs(price/cp-1)
            width = cfg.widths[tf]
            near = (distance<=width)|(np.abs(distance-width)<=1e-14)
            outer = (distance<=width*cfg.outer_multiplier)|(np.abs(distance-width*cfg.outer_multiplier)<=1e-14)
            proximity = np.where(near,1.,np.where(outer,.5,0.))
            age = (t-c['known_at'][mask])/DAY
            weights = proximity*(cfg.recency_floor+(1-cfg.recency_floor)*np.power(.5,age/cfg.half_life_days))
            sides = c['kind'][mask]
            sums = []
            for side in ['support','resistance']:
                w = weights[sides==side]
                sums.append(float(np.cumsum(w)[-1]) if len(w) else 0.)
            denom = sum(sums)
            normalized = (sums[0]-sums[1])/denom if denom else 0.
            total += normalized*cfg.tf_weights[tf]
        yield int(t), total/sum(cfg.tf_weights.values())


def samples(store, cfg, timestamp):
    """Incrementally append closed-market observations. Cache contains no manual P."""
    key = identity(store.symbol,cfg)
    with _lock, sqlite3.connect(store.root/'scoring-distribution.sqlite3',timeout=120) as db:
        db.execute('CREATE TABLE IF NOT EXISTS observations(scope TEXT,timestamp INTEGER,value REAL,PRIMARY KEY(scope,timestamp))')
        db.execute('CREATE TABLE IF NOT EXISTS completed(scope TEXT,timestamp INTEGER,source_start TEXT,PRIMARY KEY(scope,timestamp))')
        with store.connect() as source:
            starts = json.dumps(source.execute('SELECT tf,MIN(open_time) FROM candles GROUP BY tf ORDER BY tf').fetchall())
        old = db.execute('SELECT source_start FROM completed WHERE scope=? AND timestamp=?',(key,timestamp)).fetchone()
        if not old or old[0]!=starts:
            from .live import bounds
            frames = {tf:store.read(tf,0,timestamp) for tf in STEPS}
            if all(len(f) for f in frames.values()):
                frames = {tf:validate(f,tf) for tf,f in frames.items()}
                clocks = frames['15m'].close_time.to_numpy()+1
                times = clocks[(clocks<timestamp)&(clocks>=timestamp-cfg.history_days*DAY)]
                existing = {r[0] for r in db.execute('SELECT timestamp FROM observations WHERE scope=? AND timestamp>=? AND timestamp<?',
                                                    (key,timestamp-cfg.history_days*DAY,timestamp))}
                times = [t for t in times if int(t) not in existing]
                # Missing full history is not replaced by partial-window scores.
                times = [int(t) for t in times if all(bounds(tf,int(t),cfg)[0]>=int(f.open_time.iloc[0]) and
                         int(f.close_time.iloc[-1])+1>=bounds(tf,int(t),cfg)[1] for tf,f in frames.items())]
                if times:
                    db.executemany('INSERT OR IGNORE INTO observations VALUES(?,?,?)',
                                   ((key,t,v) for t,v in historical_scores(frames,times,cfg)))
                if all(int(f.close_time.iloc[-1])+1>=bounds(tf,timestamp,cfg)[1] for tf,f in frames.items()):
                    db.execute('INSERT OR REPLACE INTO completed VALUES(?,?,?)',(key,timestamp,starts))
        rows = db.execute('SELECT timestamp,value FROM observations WHERE scope=? AND timestamp>=? AND timestamp<? ORDER BY timestamp',
                          (key,timestamp-cfg.history_days*DAY,timestamp)).fetchall()
    return rows,key


def attach(snapshot, store, cfg, build=True):
    if snapshot is None:
        return None
    result = deepcopy(snapshot)
    # Never apply the active config's distribution to an old differently configured snapshot.
    from .config import Settings
    config = Settings.model_validate(result['config']) if 'config' in result else cfg
    t = result['timestamp']
    rows,key = samples(store,config,t) if build else ([],identity(store.symbol,config))
    result['scoring_percentile'] = describe(rows,t,result['scoring']['overall']['combined_normalized'],config,store.symbol,key)
    return result
