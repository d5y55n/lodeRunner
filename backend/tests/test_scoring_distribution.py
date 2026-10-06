from copy import deepcopy
import hashlib
from pathlib import Path

import numpy as np
import pytest

from app.website import scoring, scoring_distribution as dist, manual
from app.website.config import settings, STEPS, DAY
from test_live_dashboard import config, frame
from app.website.live import Store, Dashboard, bounds


def populated(root,symbol,multiplier):
    cfg=config();t=1702641600000;store=Store(root,symbol=symbol)
    for tf in STEPS:
        start,end=bounds(tf,t,cfg)
        f=frame(tf,start-30*DAY,end)
        f.loc[:,['open','high','low','close']]*=multiplier
        f['open']=f.close+np.where(np.arange(len(f))%int(multiplier+2)<2,.4,-.4)*multiplier
        store.insert(tf,f,end)
    return Dashboard(store=store,symbol=symbol,cfg=cfg),t


def describe(value, rows=None, minimum=1, t=100):
    cfg=settings().model_copy(update={'min_distribution_samples':minimum})
    return dist.describe(rows or [(1,.1),(2,.2),(3,-.1),(4,-.2)],t,value,cfg,'BTCUSDT','key')


def test_formula_unchanged():
    assert hashlib.sha256(Path(scoring.__file__).read_bytes()).hexdigest()=='a57557d467141dc90679ab09a8b69f2493ae6195cc59dbcf7e01931655159ef1'


@pytest.mark.parametrize('value,direction,p',[ (.15,'SUPPORT',50),(-.15,'RESISTANCE',50),(0,'BALANCED',None),(.1,'SUPPORT',25),(-.2,'RESISTANCE',75),(1e-12,'SUPPORT',0),(-1e-12,'RESISTANCE',0),(.9,'SUPPORT',100)])
def test_direction_zero_ties_bounds(value,direction,p):
    r=describe(value)
    assert (r['direction'],r['percentile'])==(direction,p)
    assert p is None or 0<=p<=100


def test_prior_only_and_insufficient():
    a=describe(.15,t=3)
    b=describe(.15,[(1,.1),(2,.2),(3,999),(500,999)],t=3)
    assert a==b
    assert describe(.15,minimum=3)['percentile'] is None
    assert a['statistics']['signed']['count']==2


def test_historical_parity_causality_cache_manual_and_legacy(tmp_path,monkeypatch):
    d,t=populated(tmp_path,'ETHUSDT',3)
    try:
        frames={tf:d.store.read(tf,0,t) for tf in STEPS}
        times=[t-2*DAY,t-DAY,t-STEPS['15m']]
        rows=list(dist.historical_scores(frames,times,d.cfg))
        assert any(v!=0 for _,v in rows)
        for ts,value in rows:
            price=float(frames['15m'].loc[frames['15m'].close_time<ts,'close'].iloc[-1])
            expected=scoring.combine({tf:scoring.score(f,tf,price,ts,d.cfg) for tf,f in frames.items()},d.cfg)
            assert value==pytest.approx(expected['combined_normalized'],abs=1e-14)
        changed=deepcopy(frames)
        for tf,f in changed.items():
            f.loc[f.close_time>=times[0],['open','high','low','close']]*=10
        assert list(dist.historical_scores(changed,[times[0]],d.cfg))==[rows[0]]
        base=d.replay(t);d.snapshot=base
        baseline=deepcopy(base['scoring_percentile'])
        monkeypatch.setattr(dist,'historical_scores',lambda *a:pytest.fail('Cached baseline must be reused'))
        current=manual.evaluate(d)
        result=manual.evaluate(d,str(base['price']*1.5))
        assert current['scoring']==base['scoring']
        assert result['converging']==base['converging']
        assert result['scoring_percentile']['statistics']==baseline['statistics']
        assert result['scoring_percentile']['distribution_key']==baseline['distribution_key']
        old=deepcopy(base);old.pop('scoring_percentile')
        assert dist.attach(old,d.store,d.cfg)['scoring_percentile']==baseline
        assert 'scoring_percentile' not in old
    finally:d.stop()


def test_config_symbol_version_isolation(monkeypatch):
    cfg=settings();a=dist.identity('BTCUSDT',cfg)
    assert a!=dist.identity('ETHUSDT',cfg)
    assert a!=dist.identity('BTCUSDT',cfg.model_copy(update={'half_life_days':90}))
    assert a!=dist.identity('BTCUSDT',cfg.model_copy(update={'history_days':500}))
    monkeypatch.setattr(dist,'VERSION','new-version')
    assert a!=dist.identity('BTCUSDT',cfg)


def test_window_expiry():
    cfg=settings().model_copy(update={'history_days':1,'min_distribution_samples':1})
    r=dist.describe([(0,.9),(DAY,.1),(2*DAY,.9)],2*DAY,.2,cfg,'X','K')
    assert r['sample_count']==1 and r['percentile']==100
    assert r['coverage_start']==DAY


def test_replay_builds_missing_earlier_baseline_and_isolates_cache(tmp_path):
    d,t=populated(tmp_path/'eth','ETHUSDT',3)
    other,_=populated(tmp_path/'sol','SOLUSDT',7)
    try:
        now,key=dist.samples(d.store,d.cfg,t)
        past,_=dist.samples(d.store,d.cfg,t-2*DAY)
        assert len(past)==len(now)==96
        assert max(x[0] for x in past)<t-2*DAY
        different,otherkey=dist.samples(other.store,other.cfg,t)
        assert otherkey!=key and different!=now
        changed=d.cfg.model_copy(update={'recency_floor':.9})
        configured,configkey=dist.samples(d.store,changed,t)
        assert configkey!=key and configured!=now
        assert dist.samples(d.store,d.cfg,t)[0]==now
    finally:
        d.stop();other.stop()
