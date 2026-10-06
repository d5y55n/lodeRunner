import numpy as np
import pandas as pd
import pytest
from app.fullmap_flow.common import HOUR,buckets,shape,guard,PLAN
from app.fullmap_flow.features import flow,intervals
from app.fullmap_flow.analyze import outcome_arrays,aggregate,GRIDS,summary

class Profile:
    def __init__(self,trades=(),bad=(),missing=()):self.trades=trades;self.bad=bad;self.missing=missing;self.calls=[]
    def quarantined(self,a,b):return any(a<y and b>x for x,y in self.bad)
    def hour(self,h):
        self.calls.append(h)
        return None if h in self.missing else True
    def quantity(self,h,lo,hi):
        selected=[x for x in self.trades if h<=x[0]<h+HOUR and lo<=x[1]<=hi]
        buy=sum(q for _,_,q,m in selected if not m);sell=sum(q for _,_,q,m in selected if m)
        return dict(quantity=buy+sell,aggressive_buy_quantity=buy,aggressive_sell_quantity=sell)

@pytest.mark.parametrize('window',[1,4,8])
def test_observation_boundaries_and_future_exclusion(window):
    t=100*HOUR;start=t-window*HOUR
    trades=[(start-1,100,100,False),(start,100,3,False),(t-1,100,1,True),(t,100,999,True),(t+1,100,999,False)]
    p=Profile(trades);spans={'support':[[99,101]],'resistance':[],'joint':[[99,101]]}
    r=flow(p,t,window,spans)
    assert r['support_quantity']==4 and r['support_buy']==3 and r['support_sell']==1
    assert r['support_delta']==2 and r['support_normalized_delta']==.5
    assert min(p.calls)==start and max(p.calls)<t
    truncated=flow(Profile(trades[:3]),t,window,spans)
    for k in r:
        if isinstance(r[k],float):assert np.isclose(r[k],truncated[k],equal_nan=True)
        else:assert r[k]==truncated[k]

def test_support_resistance_union_shared_no_double_count():
    spans=intervals(np.array([100.,100.,100.]),np.array(['SUPPORT','SUPPORT','RESISTANCE']),100)
    assert spans['support']==[[99.6,100.4]] and spans['support']==spans['resistance']==spans['joint']
    r=flow(Profile([(99*HOUR,100,4,False),(99*HOUR,100,1,True)]),100*HOUR,1,spans)
    assert r['support_quantity']==r['resistance_quantity']==r['joint_quantity']==r['shared_quantity']==5
    assert r['normalized_delta_difference']==r['raw_delta_difference']==0
    assert r['support_volume_share']==.5

def test_zero_volume_not_missing_and_normalized_undefined():
    r=flow(Profile(),100*HOUR,1,dict(support=[],resistance=[],joint=[]))
    assert r['status']=='AVAILABLE' and r['joint_quantity']==0
    assert np.isnan(r['support_normalized_delta']) and np.isnan(r['support_volume_share'])

@pytest.mark.parametrize('window',[1,4,8])
def test_quarantine_any_intersection_invalidates_whole_window(window):
    t=100*HOUR;spans=dict(support=[],resistance=[],joint=[])
    r=flow(Profile(bad=[(t-window*HOUR,t-window*HOUR+1)]),t,window,spans)
    assert r['status']=='QUARANTINED' and np.isnan(r['joint_quantity'])
    r=flow(Profile(bad=[(t,t+1)]),t,window,spans)
    assert r['status']=='AVAILABLE'

def test_missing_profile_is_not_silently_empty_union():
    r=flow(Profile(missing=[99*HOUR]),100*HOUR,1,dict(support=[],resistance=[],joint=[]))
    assert r['status']=='MISSING_PROFILE' and np.isnan(r['support_quantity'])

def test_frozen_development_cuts_not_refit():
    assert buckets([-100,0,.5,100,np.nan],[0,.5]).tolist()==[0,1,2,2,-1]
    assert shape([-.5,-.01,0,.01,.2,.8,.9,np.nan],.8).tolist()==[0,1,1,1,2,2,3,-1]
    assert PLAN['windows']==[1,4,8]

@pytest.mark.parametrize('t,w',[(1704067200000,1),(1704067200000+HOUR,8),(100*HOUR+1,1),(100*HOUR,2)])
def test_forbidden_time_and_window(t,w):
    with pytest.raises(ValueError):guard(t,w)

def labels():
    rows=[]
    for eid,label in [('a','TP_FIRST'),('b','AMBIGUOUS')]:
        for direction,tp,sl,h in GRIDS:
            rows.append(dict(event_id=eid,direction=direction,tp=tp,sl=sl,horizon=h,label=label,censored=False,
                mfe_pct=.8,mae_pct=.5,time_to_mfe_ms=HOUR,time_to_mae_ms=2*HOUR))
    return pd.DataFrame(rows)

def test_identical_outcome_join_and_ambiguity_denominator():
    e=pd.DataFrame({'event_id':['a','b']});f=labels()
    a=outcome_arrays(e,f.iloc[::-1]);r=aggregate(pd.DataFrame({'group':[0,0]}),a)
    assert len(r)==24 and r.tp_first_rate.eq(.5).all() and r.AMBIGUOUS.eq(1).all()
    assert r.complete.eq(2).all()
    with pytest.raises(ValueError):outcome_arrays(e,f.iloc[:-1])
    with pytest.raises(ValueError):outcome_arrays(e,pd.concat([f,f.iloc[:1]]))

def test_map_baseline_uses_same_finite_flow_cohort():
    e=pd.DataFrame({'event_id':['a','b']});a=outcome_arrays(e,labels())
    frame=pd.DataFrame({'quarter':['2022Q1']*2,'status':['AVAILABLE']*2})
    allbase=aggregate(pd.DataFrame({'period':['ALL']*2}),a)
    quarter=aggregate(pd.DataFrame({'period':['2022Q1']*2}),a)
    r=summary(frame,a,np.array([0,0]),np.array([2,-1]),pd.concat([allbase,quarter]))
    assert r.tp_first_rate.eq(1).all() and r.tp_first_rate_map_only.eq(1).all()
    assert r.tp_first_rate_unconditioned.eq(.5).all()

def test_fully_censored_cell_is_not_a_replication_comparison():
    from app.fullmap_flow.reports import pair_contrasts
    common=dict(period='ALL',map_bucket=0,direction='LONG',tp=.003,sl=.003,horizon=8,
        SL_FIRST=0,AMBIGUOUS=0,NEITHER=0,tp_first_rate_map_only=.5)
    f=pd.DataFrame([dict(**common,flow_bucket=2,complete=20,tp_first_rate=.5),
        dict(**common,flow_bucket=3,complete=0,tp_first_rate=np.nan)])
    assert not pair_contrasts(f,2,3).comparable.any()
