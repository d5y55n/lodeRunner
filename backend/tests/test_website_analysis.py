import math
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from app.website.config import settings, STEPS, DAY
from app.website import scoring as s, converging as c, market


def candles(count=80, tf='15m'):
    x=np.arange(count);close=100+5*np.sin(x*.6)+.03*x
    return pd.DataFrame(dict(open_time=x*STEPS[tf],close_time=(x+1)*STEPS[tf]-1,
                             open=close-.3*np.cos(x),high=close+1,low=close-1,close=close))


def cfg():
    return settings().model_copy(update={'min_distribution_samples':1})


def test_pair_parity_and_doji():
    f=candles(4);f['open']=[99,102,100,102];f['close']=[101,100,100,103];f['high']=[104,103,102,105];f['low']=[98,99,98,101]
    r=s.candidates(f);assert len(r)==1 and r[0]['kind']=='resistance' and r[0]['price']==103
    assert r[0]['known_at']==2*STEPS['15m']
    f=f.iloc[:2].copy();f['open']=[102,99];f['close']=[100,101]
    assert s.candidates(f)[0]['price']==99


@pytest.mark.parametrize('price,expected',[(100,1),(100.2,1),(100.25,.5),(100.3,.5),(100.31,0)])
def test_proximity(price,expected):
    assert s.proximity(price,100,.002,1.5)==expected


def test_recency():
    a=[s.age_weight(x,cfg()) for x in [0,180,360,100000]]
    assert a==sorted(a,reverse=True);assert a[:3]==[1,.625,.4375];assert a[-1]>=.25
    with pytest.raises(ValueError):s.age_weight(-1,cfg())


def test_scores_normalize_and_combine():
    f=candles();t=int(f.close_time.iloc[-1])+1
    rows={tf:s.score(f,tf,100,t,cfg()) for tf in STEPS}
    for row in rows.values():
        den=row['weighted_support']+row['weighted_resistance'];assert row['normalized']==pytest.approx((row['weighted_support']-row['weighted_resistance'])/den if den else 0)
        assert row['weighted_contribution']==row['normalized']*row['weight']
    assert -1<=s.combine(rows,cfg())['combined_normalized']<=1
    r=s.score(f,'15m',10000,t,cfg());assert not r['available'] and r['normalized']==0


def test_score_future_exclusion():
    f=candles();t=30*STEPS['15m']
    assert s.score(f,'15m',100,t,cfg(),True)==s.score(f.iloc[:30],'15m',100,t,cfg(),True)


def test_swing_confirmation_and_prefix():
    f=candles();n=2
    for side in ['high','low']:
        sources=c.swing_sources(f,n,side)
        assert np.all(sources[:2*n]==-1)
        for j,src in enumerate(sources):
            assert src<0 or src+n<=j
            assert c.swing_sources(f.iloc[:j+1],n,side)[-1]==src


def test_slope_formula():
    f=candles();streams=c.observations(f,2)
    for side,stream in streams.items():
        for j,i in enumerate(stream['source']):
            if i>=0:assert stream['slope'][j]==pytest.approx(math.log(f.close.iloc[j]/f[side].iloc[i])/(j-i))


def test_distribution_direction_origin_and_future():
    f=candles(6);streams={'high':{'slope':np.array([1.,-2.,3.,-4.,5.,99.])},'low':{'slope':np.array([8.,-9.,10.,-11.,12.,99.])}}
    t=5*STEPS['15m']
    assert c.distribution(f,streams,t,1,cfg(),'high').tolist()==[1.,3.]
    assert c.distribution(f,streams,t,-1,cfg(),'high').tolist()==[2.,4.]
    assert c.distribution(f,streams,t,1,cfg(),'low').tolist()==[8.,10.]


def test_metrics_percentile_median_ratio_direction():
    a=np.array([1.,2.,3.,4.]);r=c.metrics(a,3.,cfg())
    assert r['historical_median']==2.5 and r['stretch_ratio']==1.2 and r['percentile']==62.5
    assert r['direction']=='UPWARD_STRETCH';assert c.metrics(a,-3.,cfg())['direction']=='DOWNWARD_STRETCH'


def test_source_reset_velocity_acceleration_and_truncated_parity():
    f=candles(100);n=2;streams=c.observations(f,n)
    reset=valid=0
    for side in ['high','low']:
        for j in range(10,len(f)):
            r=c.point(f,streams,n,side,j,cfg());short=f.iloc[:j+1];q=c.point(short,c.observations(short,n),n,side,j,cfg());assert r==q
            ids=streams[side]['source']
            if ids[j]!=ids[j-1]:
                assert r['velocity'] is None and r['acceleration'] is None;reset+=1
            if r['acceleration'] is not None:
                p=r['recent_percentiles'];assert r['velocity']==pytest.approx(p[2]-p[1]);assert r['acceleration']==pytest.approx(p[2]-2*p[1]+p[0]);valid+=1
    assert reset>0 and valid>0


def test_native_timeframes_separate():
    f=candles();a=c.calculate(f,cfg());g=candles();g['close']=g.close+1;b=c.calculate(g,cfg());assert a!=b;assert c.calculate(f,cfg())==a


@pytest.mark.parametrize('kind',['gap','duplicate','negative','nan'])
def test_invalid_data(kind):
    f=candles()
    if kind=='gap':f=f.drop(5)
    elif kind=='duplicate':f=pd.concat([f,f.iloc[-1:]])
    elif kind=='negative':f.loc[1,'low']=-1
    else:f.loc[1,'high']=np.nan
    with pytest.raises(ValueError):market.validate(f,'15m')


def test_reserved_year_guard():
    with pytest.raises(ValueError):market.no_2024(market.FORBIDDEN_START-1,market.FORBIDDEN_START+1)
    market.no_2024(market.FORBIDDEN_START-DAY,market.FORBIDDEN_START)


@pytest.mark.parametrize('tf',list(STEPS))
def test_fully_closed_higher_alignment(monkeypatch,tf):
    config=cfg().model_copy(update={'history_days':1,'converging_history_days':1})
    t=market.timestamp('2023-12-15T12:15:00Z')
    def replay(tf,start,end):
        ts=np.arange(start,end,STEPS[tf]);f=pd.DataFrame(dict(open_time=ts,close_time=ts+STEPS[tf]-1,open=100,high=101,low=99,close=100))
        return f,[]
    monkeypatch.setattr(market,'replay',replay)
    f,_=market.load(tf,t,config,'replay');assert (f.close_time<t).all()
    assert f.close_time.iloc[-1]+1==t//STEPS[tf]*STEPS[tf]


def test_sparse_flat_and_diagnostics_pending():
    assert c.metrics(np.array([]),.1,cfg())['percentile'] is None
    assert c.metrics(np.array([.1]),0.,cfg())['state']=='FLAT'
    config=cfg().model_copy(update={'percentile_bands':[.01,.02,.03]})
    result=c.diagnostics(candles(100),2,config,last=12)
    assert result['retrospective_only']
    assert any(h['status']=='PENDING' for r in result['events'] for h in r['future'])


def test_settings_reject_invalid():
    from app.website.config import Settings
    d=settings().model_dump();d['tf_weights']['1d']=-1
    with pytest.raises(ValueError):Settings(**d)


def test_api_and_static(monkeypatch):
    from app.main import app
    from app.website import api
    def load(tf,t,config,mode):
        f=candles(100,tf);return f,['synthetic-test']
    monkeypatch.setattr(market,'load',load);api.analyze.cache_clear()
    with TestClient(app) as client:
        assert client.get('/').status_code==200
        assert client.get('/assets/app.js').status_code==200
        r=client.get('/analysis/btcusdt').json();assert len(r['scoring']['timeframes'])==4
        assert r['converging']['15m']['medium']['high']['source_type']=='HIGH'
        assert 'combined_prediction' not in r
        assert client.get('/analysis/btcusdt?at=invalid').status_code==422
    api.analyze.cache_clear()
