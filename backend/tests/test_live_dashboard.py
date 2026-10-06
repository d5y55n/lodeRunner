import hashlib
import json
import time
import numpy as np
import pandas as pd
import pytest
from app.website import api, live, market
from app.website.config import settings, STEPS, DAY


def config():
    return settings().model_copy(update={'history_days':1,'converging_history_days':1,'min_distribution_samples':1})


def frame(tf,start,end):
    ts=np.arange(start,end,STEPS[tf]);x=np.arange(len(ts));p=100+np.sin(x*.7)*3
    return pd.DataFrame(dict(open_time=ts,open=p-.1,high=p+1,low=p-1,close=p,close_time=ts+STEPS[tf]-1))


@pytest.mark.parametrize('bad',['duplicate','unordered','gap','ohlc','nonfinite','open'])
def test_ingest_invalid_pages_are_atomic(tmp_path,bad):
    store=live.Store(tmp_path);f=frame('15m',0,10*STEPS['15m'])
    if bad=='duplicate':f=pd.concat([f,f.tail(1)])
    if bad=='unordered':f=f.iloc[::-1]
    if bad=='gap':f=f.drop(3)
    if bad=='ohlc':f.loc[1,'high']=1
    if bad=='nonfinite':f.loc[1,'low']=float('nan')
    end=9*STEPS['15m'] if bad=='open' else 10*STEPS['15m']
    with pytest.raises(ValueError):store.insert('15m',f,end)
    assert store.read('15m',0,20*STEPS['15m']).empty


def test_retry_idempotent_conflicting_candle_rejected(tmp_path):
    store=live.Store(tmp_path);f=frame('15m',0,10*STEPS['15m'])
    store.insert('15m',f,10*STEPS['15m']);store.insert('15m',f,10*STEPS['15m'])
    assert len(store.load('15m',0,10*STEPS['15m']))==10
    f.loc[1,'close']+=.2
    with pytest.raises(live.CoverageError):store.insert('15m',f,10*STEPS['15m'])
    assert live.Store(tmp_path).load('15m',0,10*STEPS['15m']).close.iloc[1]!=f.close.iloc[1]


def test_reconnect_resumes_last_valid_page_and_surfaces_gap(tmp_path,monkeypatch):
    monkeypatch.setattr(live.time,'sleep',lambda _:None)
    store=live.Store(tmp_path);step=STEPS['15m'];f=frame('15m',0,10*step)
    store.insert('15m',f.iloc[:5],10*step)
    class Feed:
        def candles(self,tf,start,end):
            assert start==5*step
            return f.iloc[5:]
    pd.testing.assert_frame_equal(store.ensure('15m',0,10*step,Feed()),market.validate(f,'15m'))
    class Broken:
        def candles(self,tf,start,end):return frame(tf,start+step,end)
    with pytest.raises(live.CoverageError):store.ensure('15m',0,12*step,Broken())
    assert len(store.read('15m',0,12*step))==10


def populated(tmp_path):
    cfg=config();t=1702641600000;store=live.Store(tmp_path)
    for tf in STEPS:
        start,end=live.bounds(tf,t,cfg)
        store.insert(tf,frame(tf,start-DAY,end+STEPS[tf]),end+STEPS[tf])
    return live.Dashboard(store=store,cfg=cfg),t,cfg


def test_v1_parity_replay_cache_and_future_exclusion(tmp_path,monkeypatch):
    d,t,cfg=populated(tmp_path)
    frames={tf:d.store.load(tf,*live.bounds(tf,t,cfg)) for tf in STEPS}
    def load(tf,decision,cfg,mode):return frames[tf],['test']
    monkeypatch.setattr(market,'load',load);api.analyze.cache_clear()
    expected=api.analyze('replay',t,cfg.model_dump_json());actual=d.replay(t)
    for key in ['scoring','converging','charts','config','config_hash','descriptions']:
        assert actual[key]==expected[key]
    actual['price']=-1
    assert d.replay(t)['price']==expected['price']
    for tf in STEPS:
        assert max(c['close_time'] for c in actual['charts'][tf])<t
        for scale in actual['converging'][tf].values():
            for side in ['high','low']:
                r=scale[side]
                if r.get('known_at'):assert r['known_at']<=r['observation_time']<=t
    api.analyze.cache_clear();d.stop()


def test_native_states_only_change_on_native_close(tmp_path):
    d,t,cfg=populated(tmp_path)
    a=d.replay(t);b=d.replay(t+STEPS['15m'])
    assert a['converging']['15m']!=b['converging']['15m']
    for tf in ['1h','4h','1d']:assert a['converging'][tf]==b['converging'][tf]
    for score in b['scoring']['timeframes'].values():assert score['evaluation_price']==b['price']
    d.stop()


def test_snapshot_dedup_restore_checksum_and_staleness(tmp_path):
    d,t,cfg=populated(tmp_path);s=d.replay(t);s['mode']='live';d.store.save(s);d.store.save(s)
    assert len(d.store.history())==1
    restored=live.Dashboard(store=d.store,cfg=cfg)
    assert restored.status()['snapshot']['freshness']=='STALE'
    restored.snapshot=s;restored.verified_decision=t;restored.connection='CONNECTED';restored.analysis_status='READY'
    restored.ticker=dict(price=99999,server_timestamp=t+1000,timestamp=t+1000);restored.received_mono=time.monotonic()
    assert restored.status()['snapshot']['freshness']=='FRESH'
    assert restored.status()['snapshot']['price']!=99999
    restored.connection='DISCONNECTED'
    assert restored.status()['snapshot']['freshness']=='STALE'
    assert restored.status()['snapshot']['scoring']==s['scoring']
    with d.store.connect() as db:db.execute("UPDATE snapshots SET sha256='invalid'")
    with pytest.raises(live.CoverageError):d.store.history()
    d.stop();restored.stop()


def test_incomplete_history_is_not_shortened(tmp_path):
    d,t,cfg=populated(tmp_path)
    with pytest.raises(live.CoverageError):d.replay(t-40*DAY)
    with pytest.raises(ValueError):market.no_2024(market.FORBIDDEN_START,market.FORBIDDEN_END)
    assert d.store.path.parent==tmp_path
    d.stop()


def test_api_operational_routes(tmp_path,monkeypatch):
    from app.main import app
    from app.website import live_api
    from fastapi.testclient import TestClient
    d,t,cfg=populated(tmp_path);s=d.replay(t);d.snapshot=s;d.store.save(s)
    monkeypatch.setattr(d,'start',lambda:None)
    monkeypatch.setattr(live_api,'dashboard',lambda:d)
    client=TestClient(app)
    assert client.get('/market/btcusdt/status').json()['snapshot']['freshness']=='STALE'
    assert len(client.get('/analysis/btcusdt/history').json()['rows'])==1
    assert client.get('/market/btcusdt/candles?tf=1h&count=20').status_code==200
    assert client.get('/dashboard/btcusdt/replay?at=bad').status_code==422
    d.stop()
