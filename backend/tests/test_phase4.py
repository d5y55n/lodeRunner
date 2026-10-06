import numpy as np
import pytest
from app.research.models import Candle
from app.multimap.contract import STEPS,WIDTHS,LOOKBACK,Clock,latest_closed,FINAL_START,CONFIGS
from app.multimap.engine import Engine
from app.fullmap_scale.gate import equivalent

def candles(tf,n=150):
    rng=np.random.default_rng(4001);step=STEPS[tf];price=100.;result=[]
    for i in range(n):
        close=price*(1+rng.normal(0,.008))
        result.append(Candle(str(i),i*step,(i+1)*step,price,max(price,close)*1.003,min(price,close)*.997,close));price=close
    return result

@pytest.mark.parametrize('tf,count,width',[('15m',81600,.002),('1h',20400,.004),('4h',5100,.007),('1d',850,.022)])
def test_exact_calendar_counts_and_widths(tf,count,width):
    assert LOOKBACK//STEPS[tf]==count and WIDTHS[tf]==width

@pytest.mark.parametrize('tf',['15m','1h','4h','1d'])
def test_native_rolling_parity_and_expiry(tf):
    cs=candles(tf);step=STEPS[tf];e=Engine(cs,tf,100*step)
    for index in [100,101,115,140,149]:
        for name,params in CONFIGS:
            s,m=e.snapshot(index*step,name,params);c,r,n=e.reference_snapshot(index*step,name,params)
            assert s['known_candidate_ids']==[x.id for x in c]
            equivalent(s['raw'],r);equivalent(s['native_score'],n)
            assert np.all(e.known[m]<=index*step) and np.all(e.dependencies[m]>=(index-100)*step)
            assert s['last_closed_candle_end']==index*step
    with pytest.raises(ValueError):e.snapshot(100*step+1,'A',{})
    with pytest.raises(ValueError):e.snapshot(99*step,'A',{})

def test_missing_candle_is_not_count_fallback():
    cs=candles('15m');cs.pop(5)
    with pytest.raises(ValueError):Clock(cs,'15m',100*STEPS['15m'])

def test_alignment_only_closed_states_no_scores_combined():
    rows=[dict(decision_timestamp=t,last_closed_candle_end=t,A1=t) for t in [4*3600000,8*3600000,12*3600000]]
    assert latest_closed(rows,13*3600000+15*60000)==rows[-1]
    assert latest_closed(rows,3*3600000) is None
    assert latest_closed(rows,8*3600000)==rows[1]
    with pytest.raises(ValueError):latest_closed(rows,FINAL_START)
    with pytest.raises(ValueError):latest_closed([dict(decision_timestamp=3,last_closed_candle_end=4)],5)

def test_independent_adapter_leaves_frozen_hourly_engine_identical():
    from app.fullmap_scale.engine import Engine as Frozen
    cs=candles('1h');old=Frozen(cs,100*STEPS['1h']);new=Engine(cs,'1h',100*STEPS['1h'])
    for name,params in CONFIGS:
        a,_,_=old.snapshot(120*STEPS['1h'],name,params);b,_=new.snapshot(120*STEPS['1h'],name,params)
        for key in ['event_id','snapshot_id','native_score','raw','known_candidate_ids']:equivalent(a[key],b[key])


def test_common_state_and_native_outcome_contract():
    from app.multimap.run import normalized, outcomes
    cs=candles('4h');e=Engine(cs,'4h',100*STEPS['4h']);t=120*STEPS['4h']
    s,_=e.snapshot(t,'A',{});row=normalized(s)
    assert row['A1']==s['native_score']['long_score']
    assert row['A2']==s['native_score']['full_weight_only_long']
    assert row['last_closed_candle_end']==row['decision_timestamp']==t
    assert row['quantity'] is None and row['delta'] is None
    assert row['flow_status']=='PENDING_SEPARATE_TRADE_ATTACHMENT'
    labels=outcomes(cs,t,'4h',s['event_id'],cs[-1].end)
    assert len(labels)==24
    assert {r['elapsed_horizon_hours'] for r in labels}=={4,8,24}
    assert {r['horizon'] for r in labels}=={1,2,6}
    b,_=e.snapshot(t,'B',{'width':1})
    assert normalized(b)['A1'] is None and normalized(b)['A2'] is None
    assert b['event_id']==s['event_id']


def test_daily_outcomes_do_not_invent_intraday_or_cross_period_end():
    from app.multimap.run import outcomes
    cs=candles('1d');t=120*STEPS['1d']
    result=outcomes(cs,t,'1d','test',t+STEPS['1d'])
    assert {r['elapsed_horizon_hours'] for r in result}=={24,48,72}
    assert all(r['observed_candles']==1 for r in result)
    assert all(r['censored']==(r['horizon']>1) for r in result)
