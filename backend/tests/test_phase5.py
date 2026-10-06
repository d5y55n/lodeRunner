import json
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest
from app.confluence.geometry import union, intersect, nearby, latest_indices, distance, sign
from app.confluence.contract import TFS, STEPS, WIDTHS, Sources, timestamp_guard, PLAN
from app.confluence.build import overlap_rows, alignment_audit
from app.confluence.analyze import cohorts, fit_buckets, contrast, block_arrays
from app.confluence.reports import shape, plot_svg


def test_native_hourly_missing_flow_preserved():
    from app.confluence.build import hourly_flow
    v=dict(status='QUARANTINED',observation_start=0,observation_end=3600000,
           support=None,resistance=None,joint=None)
    r=hourly_flow(v)
    assert r['joint_quantity'] is None and r['flow_status']=='QUARANTINED'
    v['status']='AVAILABLE'
    with pytest.raises(ValueError):hourly_flow(v)


def test_closed_touch_intersection():
    assert intersect([[1,2]],[[2,3]])==[[2.,2.]]
    assert intersect([[1,2]],[[3,4]])==[]


def test_union_no_double_count():
    assert union([[1,4],[2,3],[4,5],[8,9]])==[[1.,5.],[8.,9.]]


def test_multiway_not_pairwise_inference():
    a=[[0,2],[8,10]];b=[[1,3],[5,6]];c=[[5,6],[9,10]]
    assert intersect(a,b) and intersect(a,c) and intersect(b,c)
    assert intersect(intersect(a,b),c)==[]


@pytest.mark.parametrize('tf',TFS)
def test_native_boundary_and_truncation(tf):
    step=STEPS[tf];times=np.arange(0,10*step,step);queries=np.array([step-1,step,step+1,2*step])
    i,v=latest_indices(times,queries,step)
    assert v.all() and i.tolist()==[0,1,1,2]
    for q,idx in zip(queries,i):
        t=times[times<=q];j,ok=latest_indices(t,[q],step)
        assert ok[0] and t[j[0]]==times[idx]


def test_no_stale_or_future_state():
    idx,valid=latest_indices([10,20],[9,10,19,20,30],10)
    assert valid.tolist()==[False,True,True,True,False]
    with pytest.raises(ValueError):latest_indices([10,10],[10],10)
    with pytest.raises(ValueError):latest_indices([11,20],[20],10)


def test_sign_does_not_treat_empty_as_balanced():
    assert [sign(v) for v in [None,np.nan,0,1,-1]]==['M','M','N','S','R']


def test_native_nearby_strict_boundary():
    p=np.array([100.]);w=.004
    assert nearby(p,100,w)[0]
    assert nearby(p,100*(1+w),w)[0]
    assert not nearby(p,100*(1+1.5*w),w)[0]


def test_overlap_auditable_native_widths():
    states={}
    for tf in TFS:
        low,high=100*(1-WIDTHS[tf]),100*(1+WIDTHS[tf])
        states[tf]={side+'_union':json.dumps([[low,high]]) for side in ['support','resistance']}
        states[tf].update({side+'_intervals':json.dumps([[low,high,42]]) for side in ['support','resistance']})
    features,rows=overlap_rows(900000,101,states)
    assert features['support_overlap_count']==4
    r=next(r for r in rows if r['side']=='support' and r['timeframe_count']==4)
    assert r['lower']==99.8 and r['upper']==100.2 and r['candidate_interval_count']==4
    assert np.isclose(r['price_distance'],.8)
    assert rows==overlap_rows(900000,101,states)[1]


def test_period_restriction_before_read():
    with patch('app.confluence.contract.check_freeze',side_effect=ValueError('not frozen')):
        with pytest.raises(ValueError):Sources('replication')
    with pytest.raises(ValueError):Sources('2024')
    with pytest.raises(ValueError):timestamp_guard(np.array([1704067200000]),'replication')
    with pytest.raises(ValueError):Sources('development').frame('C:/forbidden/2023.parquet')


def fake_states():
    patterns=['SSSS','SSSR','SSSN','SSRR','RRSS','RRRR','NNNN','MMMM']*30
    f=pd.DataFrame({'decision_timestamp':1640995200000+np.arange(len(patterns))*86400000,'flow_status':'AVAILABLE',
                    'joint_quantity':np.arange(len(patterns))+1.,'joint_delta':0.,'support_normalized_delta':0.,'resistance_normalized_delta':0.})
    from app.confluence.contract import SUBSETS
    for descriptor in ['imbalance','A1','A2']:f[descriptor+'_pattern']=patterns
    for side in ['support','resistance']:
        f[side+'_overlap_count']=2
        for s in SUBSETS:f[side+'_overlap_'+'+'.join(s)]=len(s)<=2
    for i,tf in enumerate(TFS):f[tf+'__imbalance']=[dict(S=.2,R=-.1,N=0,M=np.nan)[p[i]] for p in patterns]
    return f


def test_cohort_nested_and_conflict_preservation():
    f=fake_states();m,meta,c=cohorts(f,fit_buckets(f))
    all4=m['imbalance/support/aligned/15m+1h+4h+1d'];three=m['imbalance/support/aligned/15m+1h+4h']
    assert np.all(~all4|three)
    a=m['incremental/support/15m+1h+4h/add_1d/agrees'];b=m['incremental/support/15m+1h+4h/add_1d/not_agrees']
    assert not np.any(a&b) and np.array_equal(a|b,three)
    assert m['conflict/SS/RR'].sum()==30
    assert m['imbalance/support/count/0'].sum()==60
    assert m['imbalance/pattern/MMMM'].sum()==30
    assert len(set(name for name,*_ in c))==len(c)


def test_quantity_missing_not_zero_and_no_refit():
    f=fake_states();model=fit_buckets(f)
    f.loc[0,'flow_status']='QUARANTINED';f.loc[1,'joint_quantity']=1e12
    masks,_,_=cohorts(f,model)
    assert masks['quantity/support/count4/Q-1'][0]
    assert masks['quantity/support/count3/Q3'][1]
    assert model['joint_quantity']==fit_buckets(fake_states())['joint_quantity']


def test_paired_bootstrap_reproducibility_and_identity():
    f=fake_states();n=len(f);one=np.ones((n,24));zero=np.zeros_like(one)
    values={'complete':one,'TP_FIRST':one,'SL_FIRST':zero,'NEITHER':zero,'AMBIGUOUS':zero,'mfe_pct_sum':one,'mae_pct_sum':one}
    wi,_,w,metrics=block_arrays(f,values)
    from itertools import product
    grids=list(product(['LONG','SHORT'],[.003,.005],[.003,.005],[16,32,96]))
    mask=np.ones(n,bool)
    a=list(contrast(mask,mask,values,wi,w,metrics,grids))
    b=list(contrast(mask,mask,values,wi,w,metrics,grids))
    assert a==b and all(r['effect']==0 and r['ci_low']==0 and r['ci_high']==0 for r in a)


def test_sparse_shape_not_promoted():
    f=pd.DataFrame(dict(count=[1,2,3,4],TP_FIRST=[.1,.2,.3,.4],supported=[True]*4))
    assert shape(f)=='MONOTONIC_INCREASING'
    f.loc[3,'supported']=False
    assert shape(f)=='SPARSE'
    f.loc[3,'supported']=True;f.loc[2,'TP_FIRST']=.1
    assert shape(f)=='NONLINEAR'


def test_svg_missing_not_zero():
    svg=plot_svg('A & B',[('series',[.1,np.nan,.3])],['1','2','3'])
    assert 'A &amp; B' in svg and svg.count('<circle')==2


def test_plan_has_no_cross_timeframe_score_sum():
    assert PLAN['no_2024'] and PLAN['no_live_rules'] and PLAN['no_BC']
    assert WIDTHS=={'15m':.002,'1h':.004,'4h':.007,'1d':.022}
