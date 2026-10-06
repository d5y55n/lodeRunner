import hashlib
import sqlite3
import time
import pytest
from app.website import live, symbols
from app.website.config import STEPS, DAY
from test_live_dashboard import config, frame


def metadata(symbol='ETHUSDT', onboard=0, status='TRADING', contract='PERPETUAL'):
    return dict(symbol=symbol,baseAsset=symbol[:-4],quoteAsset='USDT',contractType=contract,status=status,
                onboardDate=onboard,pricePrecision=5,quantityPrecision=3,
                filters=[dict(filterType='PRICE_FILTER',tickSize='0.001')])


def test_public_universe_filtering():
    rows = symbols.discover(dict(symbols=[metadata(),metadata('BTCUSDT'),metadata('NEWUSDT',status='PENDING_TRADING'),metadata('OLDUSDT',contract='CURRENT_QUARTER')]))
    assert [r['symbol'] for r in rows] == ['BTCUSDT','ETHUSDT']
    assert rows[1]['tick_size'] == '0.001'
    assert rows[1]['history_readiness'] == 'UNCHECKED'


def test_feed_uses_own_symbol(monkeypatch):
    feed=live.PublicFeed('XRPUSDT');calls=[]
    def get(path,**params):
        calls.append((path,params))
        if path.endswith('/time'):return dict(serverTime=1000)
        if path.endswith('/price'):return dict(price='0.00000123',time=1000)
        return []
    monkeypatch.setattr(feed,'get',get)
    assert feed.ticker()['price']==.00000123
    feed.candles('1h',0,1000)
    assert calls[1][1]['symbol']==calls[2][1]['symbol']=='XRPUSDT'
    feed.close()


def test_legacy_migration_preserves_candles(tmp_path):
    with sqlite3.connect(tmp_path/'dashboard.sqlite3') as db:
        db.execute('CREATE TABLE candles(tf TEXT,open_time INTEGER,open REAL,high REAL,low REAL,close REAL,close_time INTEGER,PRIMARY KEY(tf,open_time))')
        db.execute("INSERT INTO candles VALUES('15m',0,100,101,99,100,899999)")
    s=live.Store(tmp_path)
    assert s.load('15m',0,900000).close.iloc[0]==100
    with s.connect() as db:
        assert db.execute('SELECT symbol FROM candles').fetchone()[0]=='BTCUSDT'
        assert db.execute("SELECT name FROM sqlite_master WHERE name='candles_symbol_time'").fetchone()
    with pytest.raises(live.CoverageError):live.Store(tmp_path,symbol='ETHUSDT')


def populated(root,symbol,multiplier):
    cfg=config();t=1702641600000;s=live.Store(root,symbol=symbol)
    for tf in STEPS:
        start,end=live.bounds(tf,t,cfg);f=frame(tf,start-30*DAY,end)
        # Different path shapes, not just price scaling, must produce independent distributions.
        f.loc[:,['open','high','low','close']]*=multiplier
        if multiplier>1:
            f.loc[:,['open','high','low','close']]+=f.index.to_numpy()[:,None]*.01
        s.insert(tf,f,end)
    return live.Dashboard(store=s,symbol=symbol,cfg=cfg),t


def test_analysis_distribution_replay_cache_and_history_isolation(tmp_path):
    a,t=populated(tmp_path/'btc','BTCUSDT',1)
    b,_=populated(tmp_path/'eth','ETHUSDT',3)
    try:
        sa=a.replay(t);sb=b.replay(t)
        assert sa['symbol']=='BTCUSDT' and sb['symbol']=='ETHUSDT'
        assert sa['price']!=sb['price']
        assert sa['scoring']!=sb['scoring']
        assert sa['converging']!=sb['converging']
        sb['price']=-1
        assert b.replay(t)['price']>0
        a.store.save(sa);b.store.save(b.replay(t))
        assert {s['symbol'] for s in a.store.history()}=={'BTCUSDT'}
        assert {s['symbol'] for s in b.store.history()}=={'ETHUSDT'}
        with pytest.raises(live.CoverageError):a.store.save(b.replay(t))
        with pytest.raises(live.CoverageError):b.replay(t-100*DAY)
    finally:a.stop();b.stop()


def test_on_demand_bootstrap_and_new_listing(tmp_path,monkeypatch):
    monkeypatch.setattr(live.time,'sleep',lambda _:None)
    cfg=config();decision=1702641600000;calls=[]
    class Feed:
        def candles(self,tf,start,end):
            calls.append((tf,start,end));return frame(tf,start,end)
        def close(self):pass
    d=live.Dashboard(store=live.Store(tmp_path/'eth',symbol='ETHUSDT'),symbol='ETHUSDT',cfg=cfg,feed_factory=Feed)
    newer=live.Dashboard(store=live.Store(tmp_path/'new',symbol='NEWUSDT'),symbol='NEWUSDT',onboard=decision-DAY,cfg=cfg,feed_factory=Feed)
    try:
        d.update(decision)
        assert d.analysis_status=='READY'
        assert len(calls)==4
        assert d.snapshot['symbol']=='ETHUSDT'
        d.update(decision)
        assert len(calls)==4
        newer.update(decision)
        assert newer.analysis_status=='HISTORY_INCOMPLETE'
        assert newer.snapshot is None
        assert len(calls)==4
    finally:d.stop();newer.stop()


def test_registry_ttl_listing_age_and_allowlist(monkeypatch):
    calls=[]
    class Feed:
        def get(self,path):
            calls.append(path)
            return dict(serverTime=1800000000000,symbols=[metadata(),metadata('NEWUSDT',1799999999000)])
        def close(self):pass
    monkeypatch.setattr(symbols,'PublicFeed',Feed)
    r=symbols.Registry()
    assert r.universe()[1]['history_readiness']=='HISTORY_INCOMPLETE'
    r.universe();assert len(calls)==1
    with pytest.raises(symbols.HTTPException) as exc:r.get('../secret')
    assert exc.value.status_code==404


def test_global_download_concurrency_limit(tmp_path):
    d=live.Dashboard(store=live.Store(tmp_path))
    live.Dashboard.download_slot.acquire()
    try:
        d.update(1702641600000)
        assert d.progress['queued']
        assert d.snapshot is None
    finally:live.Dashboard.download_slot.release();d.stop()


def test_worker_registry_is_bounded_and_on_demand(monkeypatch):
    made=[]
    class Worker:
        def __init__(self,**kw):
            made.append(kw['symbol']);self.future=None;self.last_active=time.monotonic();self.stopped=False
        def stop(self):self.stopped=True
    r=symbols.Registry()
    r.metadata={s:dict(onboard_date=0) for s in ['A','B','C','D']}
    monkeypatch.setattr(r,'universe',lambda:[])
    monkeypatch.setattr(symbols,'Dashboard',Worker)
    assert made==[]
    for s in ['A','B','C']:r.get(s)
    with pytest.raises(symbols.HTTPException) as exc:r.get('D')
    assert exc.value.status_code==429
    first=r.workers['A'];first.last_active-=60
    r.get('D')
    assert first.stopped and len(r.workers)==3
    r.close()


def test_generic_routes_keep_symbol_scoped(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    d,t=populated(tmp_path/'eth','ETHUSDT',3)
    s=d.replay(t);d.snapshot=s;d.store.save(s)
    monkeypatch.setattr(d,'start',lambda:None)
    monkeypatch.setattr(symbols.registry,'get',lambda symbol:d)
    client=TestClient(app)
    try:
        assert client.get('/market/ETHUSDT/status').json()['symbol']=='ETHUSDT'
        assert client.get('/analysis/ETHUSDT/history').json()['rows'][0]['symbol']=='ETHUSDT'
        assert client.get('/dashboard/ETHUSDT/replay?at=2023-12-15T12:00:00Z').json()['symbol']=='ETHUSDT'
        assert client.get('/dashboard/ETHUSDT/replay?at=2020-01-01T00:00:00Z').status_code==422
        assert client.get('/market/ETHUSDT/candles?tf=1h').json()['symbol']=='ETHUSDT'
    finally:d.stop()


def test_evicted_btc_can_restart(monkeypatch):
    from functools import lru_cache
    from app.website import live_api
    class Worker:
        def __init__(self,**kw):self.future=None;self.last_active=time.monotonic();self.stopped=False
        def stop(self):self.stopped=True
    factory=lru_cache(maxsize=1)(lambda:Worker())
    monkeypatch.setattr(live_api,'dashboard',factory)
    monkeypatch.setattr(symbols,'Dashboard',Worker)
    r=symbols.Registry();r.metadata={s:dict(onboard_date=0) for s in ['BTCUSDT','A','B','C']}
    monkeypatch.setattr(r,'universe',lambda:[])
    old=r.get('BTCUSDT');r.get('A');r.get('B');old.last_active-=60
    r.get('C')
    assert old.stopped and factory.cache_info().currsize==0
    r.workers['A'].last_active-=60
    fresh=r.get('BTCUSDT')
    assert fresh is not old and not fresh.stopped
    r.close();factory.cache_clear()


def test_formula_files_unchanged():
    from app.website.config import PROJECT
    # v4 adds optional immutable candidate-map injection; arithmetic is unchanged.
    expected={'scoring.py':'a57557d467141dc90679ab09a8b69f2493ae6195cc59dbcf7e01931655159ef1',
              'converging.py':'c24535b76d59b3ab2078237bf0b438d8f35485adef818c951269ed5e6268d209'}
    for name,digest in expected.items():
        assert hashlib.sha256((PROJECT/'backend/app/website'/name).read_bytes()).hexdigest()==digest
