import json
import shutil
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from app.research.models import Candle,Candidate
from app.research.detectors import ReversalCandles
from app.research.outcomes import measure
from app.research.volume import Trade
from app.fullmap.contract import WIDTHS,CANDLE_COUNTS,HOUR,LOOKBACK,configuration,state_identity,permitted
from app.fullmap.core import FullMapEngine,contribution,score_candidates,nearby_volume,union_intervals
from app.fullmap.volume import RollingVAP,bin_trades


def candles(rows):
    return [Candle(str(i),i*HOUR,(i+1)*HOUR,*map(float,row)) for i,row in enumerate(rows)]


def test_original_constants_and_850_day_requirement():
    assert WIDTHS=={'1d':.022,'4h':.007,'1h':.004,'15m':.002}
    assert CANDLE_COUNTS=={'1d':850,'4h':5100,'1h':20400,'15m':81600}
    assert LOOKBACK==20400*HOUR
    with pytest.raises(ValueError,match='INSUFFICIENT'):FullMapEngine(candles([(100,102,99,101)])).window(HOUR)


@pytest.mark.parametrize('timeframe',WIDTHS)
def test_full_half_and_strict_outer_boundaries(timeframe):
    w=WIDTHS[timeframe]
    assert contribution(100,100,w)==1
    for sign in [-1,1]:
        assert contribution(100,100*(1+sign*w),w)==.5
        assert contribution(100,100*(1+sign*1.5*w),w)==0


def test_golden_original_js_actual_function():
    fixtures=Path(__file__).parent/'fixtures/phase3r'
    node=shutil.which('node')
    if not node:
        node=str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    if not Path(node).exists():pytest.fail('Node is required to verify original JS parity')
    rng=np.random.default_rng(3);rows=[]
    for _ in range(80):
        op,cl=rng.uniform(90,110,2);rows.append((op,max(op,cl)+rng.uniform(0,3),min(op,cl)-rng.uniform(0,3),cl))
    sets=[candles(rows),candles([(98,100,97,99),(99,102,97,98)]),
          candles([(102,103,100,101),(101,103,99,102)]),candles([(100,101,99,100),(100,101,99,100)])]
    cases=[];expected=[]
    for cs in sets:
        for tf,w in WIDTHS.items():
            found=ReversalCandles().detect(cs,tf,cs[-1].end)
            for price in [*np.linspace(85,115,31),100,100*(1+w),100*(1-w),100*(1+1.5*w),100*(1-1.5*w)]:
                scores,_=score_candidates(found,float(price),w)
                for direction in ['LONG','SHORT']:
                    cases.append(dict(candles=[[c.start,c.open,c.high,c.low,c.close] for c in cs],timeframe=tf,entry=float(price),direction=direction))
                    expected.append(scores[direction.lower()+'_score'])
    result=subprocess.run([node,str(fixtures/'original-oracle.cjs'),str(fixtures/'original-script.js')],
        input=json.dumps(cases),capture_output=True,text=True,check=True)
    assert json.loads(result.stdout)==expected
    assert len(cases)==1152


def test_accumulation_and_support_resistance_signs():
    cs=[Candidate('A',k,p,0,HOUR,'1h',()) for k,p in [('SUPPORT',100.),('SUPPORT',100.),('RESISTANCE',100.),('RESISTANCE',200.)]]
    score,contributors=score_candidates(cs,100.,.004)
    assert score['long_score']==1 and score['short_score']==-1
    assert score['support_contribution_count']==2 and score['resistance_contribution_count']==1
    assert len(contributors)==3


def test_left_boundary_requires_both_adjacent_candles():
    cs=candles([(100,105,97,104),(104,106,98,99),(99,106,97,105),(105,107,98,100)])
    engine=FullMapEngine(cs,lookback=2*HOUR)
    one,_=engine.snapshot(3*HOUR,'A',{});two,_=engine.snapshot(4*HOUR,'A',{})
    assert one['known_candidate_count']==two['known_candidate_count']==1
    assert one['known_candidate_ids']!=two['known_candidate_ids']
    assert all(engine.catalog[c]['dependency_start']>=two['lookback_start'] for c in two['known_candidate_ids'])


def test_no_future_candle_or_candidate_and_stable_identity():
    cs=candles([(100,105,97,104),(104,106,98,99),(99,106,97,105),(105,1000,1,100)])
    a=FullMapEngine(cs[:3],lookback=3*HOUR).snapshot(3*HOUR,'A',{})[0]
    b=FullMapEngine(cs,lookback=3*HOUR).snapshot(3*HOUR,'A',{})[0]
    assert a==b
    cfg=configuration('A',{})
    assert state_identity(cfg,3*HOUR,105)==state_identity(cfg,3*HOUR,105)
    with pytest.raises(ValueError):FullMapEngine(cs,lookback=3*HOUR).snapshot(3*HOUR+1,'A',{})


def test_b_full_map_and_c_confirmation():
    cs=candles([(100,102,99,101),(101,110,98,105),(105,106,100,101),(101,103,100,102)])
    engine=FullMapEngine(cs,lookback=3*HOUR)
    b,_=engine.snapshot(3*HOUR,'B',{'width':1})
    assert b['known_candidate_count']==2 and b['native_score'] is None
    c,_=engine.snapshot(3*HOUR,'C',{'reversal_fraction':.03})
    assert c['native_score'] is None
    assert all(engine.catalog[x]['known_at']<=3*HOUR for x in c['known_candidate_ids'])
    assert any(engine.catalog[x]['known_at']==3*HOUR for x in c['known_candidate_ids'])


def test_d_trade_boundaries_and_rolling_expiration():
    ts=[Trade(str(i),t,p,q,m) for i,(t,p,q,m) in enumerate([(0,100.,1.,False),(HOUR,150.,2.,True),(2*HOUR,100.,999.,False)])]
    bins=bin_trades(ts,0,2*HOUR,50)
    assert bins[2].tolist()==[1,1,0] and bins[3].tolist()==[2,0,2]
    hourly=pd.DataFrame([dict(hour=i*HOUR,bin=2,quantity=float(i+1),buy=float(i+1),sell=0.) for i in range(4)])
    engine=RollingVAP(hourly,50,lookback=2*HOUR,quarantines=[(0,60000)])
    a,arows=engine.snapshot(2*HOUR,110);b,brows=engine.snapshot(3*HOUR,110)
    assert a['volume']['total_quantity']==3 and b['volume']['total_quantity']==5
    assert a['volume']['coverage_status']=='INCOMPLETE_OBSERVABLE_COVERAGE'
    assert b['volume']['eligible_complete_coverage_comparison']
    assert a['support_count'] is None and arows[0]['kind']=='NEUTRAL'
    with pytest.raises(ValueError,match='exactly one'):engine.snapshot(5*HOUR,110)


def test_outcome_starts_after_decision_not_in_current_candle():
    cs=candles([(100,150,50,100),(100,101,99.9,100.5)])
    o=measure(100,HOUR,cs,'LONG',.005,.005,1)
    assert o.label=='TP_FIRST' and o.observed_candles==1


def test_union_volume_not_double_counted():
    class Profile:
        def quarantined(self,a,b):return False
        def quantity(self,t,low,high):
            q=3. if low<=100<=high else 0.
            return dict(quantity=q,aggressive_buy_quantity=q,aggressive_sell_quantity=0.)
    cs=[Candidate('A',k,100.,0,HOUR,'1h',()) for k in ['SUPPORT','SUPPORT','RESISTANCE']]
    volume=nearby_volume(cs,100,.004,2*HOUR,Profile())
    assert volume['support']['quantity']==3 and volume['joint']['quantity']==3
    assert volume['shared_support_resistance_quantity']==3
    assert union_intervals([(0,2),(1,3),(4,5)])==[[0,3],[4,5]]


def test_no_2024_and_no_other_timeframe_execution():
    with pytest.raises(ValueError,match='2024'):permitted(1704067200000,1704070800000)
    with pytest.raises(ValueError,match='1h only'):FullMapEngine(candles([(100,102,99,101)]),timeframe='15m')


def test_b_requires_right_confirmation_and_left_dependency():
    cs=candles([(100,102,99,101),(101,110,98,105),(105,106,100,101),(101,103,100,102)])
    engine=FullMapEngine(cs,lookback=3*HOUR)
    before,_=FullMapEngine(cs[:2],lookback=2*HOUR).snapshot(2*HOUR,'B',{'width':1})
    first,_=engine.snapshot(3*HOUR,'B',{'width':1})
    later,_=engine.snapshot(4*HOUR,'B',{'width':1})
    assert before['known_candidate_count']==0
    assert first['known_candidate_count']==2
    assert set(first['known_candidate_ids']).isdisjoint(later['known_candidate_ids'])


def test_c_unconfirmed_extreme_never_exposed():
    cs=candles([(100,101,99,100),(100,110,99,109),(109,109,101,103)])
    engine=FullMapEngine(cs,lookback=2*HOUR)
    first,_=engine.snapshot(2*HOUR,'C',{'reversal_fraction':.05})
    second,_=engine.snapshot(3*HOUR,'C',{'reversal_fraction':.05})
    assert not any(engine.catalog[c]['kind']=='RESISTANCE' for c in first['known_candidate_ids'])
    assert any(engine.catalog[c]['kind']=='RESISTANCE' and engine.catalog[c]['known_at']==3*HOUR for c in second['known_candidate_ids'])


def test_d_invalid_configuration_and_quantity_conservation():
    frame=pd.DataFrame([dict(hour=0,bin=2,quantity=2.,buy=1.,sell=0.)])
    with pytest.raises(ValueError,match='conserve'):RollingVAP(frame,50,lookback=HOUR)
    frame['quantity']=1.
    with pytest.raises(ValueError):RollingVAP(frame,float('nan'),lookback=HOUR)
    for multiple in [0,-1,float('nan')]:
        with pytest.raises(ValueError,match='multiplier'):RollingVAP(frame,50,lookback=HOUR).snapshot(HOUR,100,multiple)


def test_d_missing_hour_is_not_zero_filled():
    frame=pd.DataFrame([dict(hour=0,bin=2,quantity=1.,buy=1.,sell=0.)])
    with pytest.raises(ValueError,match='Missing complete'):
        RollingVAP(frame,50,lookback=2*HOUR).snapshot(2*HOUR,100)


def test_warmup_acquisition_whitelist_before_network():
    from app.fullmap.acquire import capture
    for date in ['2024-01','2023-12','2019-12']:
        with pytest.raises(ValueError):capture(date,'aggTrades')


def test_partitioned_vap_reproducible_and_cache_checksum(tmp_path,monkeypatch):
    import app.fullmap.data as data
    from app.market.aggregate_trades import sha256
    monkeypatch.setattr(data,'ROOT',tmp_path)
    paths=[]
    for month,hour in [('2020-09',0),('2020-10',HOUR)]:
        path=tmp_path/(month+'.parquet')
        pd.DataFrame([dict(hour=hour,price=150.,quantity=2.,buy=0.,sell=2.),
                      dict(hour=hour,price=149.99,quantity=1.,buy=1.,sell=0.)]).to_parquet(path,index=False)
        paths.append(path)
    first,info=data.hourly_bins(paths,50,{'sources':['fixed-test-input']})
    second,again=data.hourly_bins(paths,50,{'sources':['fixed-test-input']})
    pd.testing.assert_frame_equal(first,second);assert again['reused']
    assert first['bin'].tolist()==[2,3,2,3] and first.quantity.tolist()==[1.,2.,1.,2.]
    # Corrupt only derived output. Rebuild must not trust a stale manifest.
    (tmp_path/'derived/hourly-bins-50.parquet').write_bytes(b'corrupt derived cache')
    rebuilt,rebuilt_info=data.hourly_bins(paths,50,{'sources':['fixed-test-input']})
    pd.testing.assert_frame_equal(first,rebuilt)
    assert rebuilt_info['sha256']==info['sha256']==sha256(tmp_path/'derived/hourly-bins-50.parquet')


def test_full_snapshot_export_reproducibility(tmp_path):
    from app.fullmap.run import write_rows
    from app.market.aggregate_trades import sha256
    cs=candles([(100,105,97,104),(104,106,98,99),(99,106,97,105)])
    s,_=FullMapEngine(cs,lookback=3*HOUR).snapshot(3*HOUR,'A',{})
    write_rows(tmp_path,'one',[s]);write_rows(tmp_path,'two',[s])
    assert sha256(tmp_path/'one.jsonl')==sha256(tmp_path/'two.jsonl')
    assert sha256(tmp_path/'one.parquet')==sha256(tmp_path/'two.parquet')
    assert json.loads((tmp_path/'one.jsonl').read_text())==s
