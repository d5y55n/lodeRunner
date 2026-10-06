import numpy as np
import pytest
from app.research.models import Candle
from app.fullmap.core import FullMapEngine
from app.fullmap.contract import HOUR
from app.fullmap_scale.engine import Engine
from app.fullmap_scale.gate import equivalent


@pytest.mark.parametrize('name,params',[('A',{}),('B',{'width':1}),('B',{'width':2}),('C',{'reversal_fraction':.003}),('C',{'reversal_fraction':.005})])
def test_optimized_randomized_rolling_reference_parity(name,params):
    rng=np.random.default_rng(314);cs=[]
    for i in range(70):
        op,cl=map(float,rng.integers(9900,10100,2)/100)
        cs.append(Candle(str(i),i*HOUR,(i+1)*HOUR,op,max(op,cl)+.2,min(op,cl)-.2,cl))
    engine=Engine(cs,lookback=24*HOUR);reference=FullMapEngine(cs,lookback=24*HOUR)
    for i in range(24,71):
        actual,contributions,members=engine.snapshot(i*HOUR,name,params)
        expected,old=reference.snapshot(i*HOUR,name,params)
        equivalent(actual,expected);equivalent(contributions,old)
        assert [engine.ids[j] for j in members]==expected['known_candidate_ids']


def test_numeric_gate_detects_changed_mean_or_membership():
    with pytest.raises(AssertionError):equivalent({'mean':1.001},{'mean':1.})
    with pytest.raises(AssertionError):equivalent(['a','b'],['b','a'])


def test_membership_delta_round_trip_and_daily_checkpoint(tmp_path):
    import pandas as pd
    from app.fullmap_scale.storage import Stream,restore
    writer=Stream(tmp_path)
    for i,members in enumerate([[4,1],[1,3,4],[3]]):
        writer.add(dict(snapshot_id=str(i),decision_timestamp=(23+i)*HOUR,raw={},known_candidate_ids=[],contributing_candidate_ids=[]),members)
    writer.flush();rows=[]
    for p in sorted(tmp_path.glob('*-membership.parquet')):rows.extend(restore(pd.read_parquet(p)))
    assert [(sid,m.tolist()) for sid,m in rows]==[('0',[1,4]),('1',[1,3,4]),('2',[3])]


def test_crossing_features_no_future_information():
    from app.fullmap_scale.explanatory import Crossings
    cs=[Candle(str(i),i*HOUR,(i+1)*HOUR,*r) for i,r in enumerate([
        (101.,102.,99.9,100.),(100.,102.,100.,101.),(101.,101.1,99.9,100.1),
        (100.1,100.2,99.9,100.),(100.,200.,1.,150.),(150.,200.,1.,99.)])]
    a=Engine(cs,lookback=4*HOUR);b=Engine(cs[:4],lookback=4*HOUR)
    sa,_,ma=a.snapshot(4*HOUR,'A',{});sb,_,mb=b.snapshot(4*HOUR,'A',{})
    extra=Crossings(a).features(ma,4*HOUR,sa['decision_price'])
    equivalent(extra,Crossings(b).features(mb,4*HOUR,sb['decision_price']))
    assert extra['recent_0_30d']['count']>0 and extra['mean_prior_visits']==1
    assert extra['mean_prior_crossings']==0 and extra['mean_hours_since_last_contact']==0


def test_c_no_synchronization_flat_trackers_still_match_reference():
    cs=[Candle(str(i),i*HOUR,(i+1)*HOUR,100.,100.,100.,100.) for i in range(60)]
    a=Engine(cs,lookback=20*HOUR);b=FullMapEngine(cs,lookback=20*HOUR)
    for t in range(20*HOUR,61*HOUR,HOUR):
        equivalent(a.snapshot(t,'C',{'reversal_fraction':.003})[0],b.snapshot(t,'C',{'reversal_fraction':.003})[0])


def test_fast_vap_matches_reference_arithmetic_and_coverage():
    import pandas as pd
    from app.fullmap.volume import RollingVAP
    from app.fullmap_scale.vap import FastVAP
    frame=pd.DataFrame([dict(hour=t*HOUR,bin=b,quantity=float(t+b),buy=float(t),sell=float(b)) for t in range(5) for b in [3,2]])
    a=FastVAP(frame,50,lookback=2*HOUR,quarantines=[(HOUR,HOUR+60000)])
    b=RollingVAP(frame,50,lookback=2*HOUR,quarantines=[(HOUR,HOUR+60000)])
    for t in range(2*HOUR,6*HOUR,HOUR):
        x,y=a.snapshot(t,150);u,v=b.snapshot(t,150);equivalent(x,u);equivalent(y,v)


def test_summary_preserves_ambiguity_neither_and_censoring():
    import pandas as pd
    from app.fullmap_scale.analyze import metric_table,GRID
    rows=[]
    for i,label in enumerate(['TP_FIRST','SL_FIRST','AMBIGUOUS','NEITHER','TP_FIRST']):
        rows.append(dict(event_id=str(i),direction='LONG',tp=.003,sl=.005,horizon=8,label=label,censored=i==4,
            mfe_pct=1.,mae_pct=2.,time_to_mfe_ms=HOUR,time_to_mae_ms=HOUR))
    r=metric_table(pd.DataFrame(rows),GRID).iloc[0]
    assert r.complete==4 and r.censored==1 and r.TP_FIRST==1 and r.AMBIGUOUS==1
    assert r.tp_first_rate==.25 and r.gross_resolved_expectancy_pct==pytest.approx(-.1)


def test_replication_price_loader_requires_development_freeze(tmp_path,monkeypatch):
    import app.fullmap_scale.history as history
    monkeypatch.setattr(history,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='frozen'):history.load_prices(replication=True)
