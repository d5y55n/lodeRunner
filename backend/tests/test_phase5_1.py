from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest
from app.current_confluence.states import evaluate,classify
from app.current_confluence.contract import TFS,WIDTHS,Sources,PLAN
from app.current_confluence.analyze import fit,definitions,slope_from_sums
from app.current_confluence.reports import shape


def score(prices,kinds,p,width=.004,**kwargs):
    n=len(prices)
    return evaluate(np.array(prices,dtype=float),np.array(kinds),np.arange(n),np.arange(n),p,width,**kwargs)


def test_same_price_not_carried_native_score():
    prices=[100,102];kinds=['SUPPORT','RESISTANCE']
    assert score(prices,kinds,100)['state']=='S'
    current=score(prices,kinds,102)
    assert current['state']=='R' and current['evaluation_price']==102
    assert current['nearest_resistance_distance']==0


def test_far_historical_support_is_not_current_support():
    r=score([100,101],['SUPPORT','SUPPORT'],200)
    assert r['support_count']==0 and r['state']=='M' and r['full_map_support_count']==2


def test_neutral_requires_nonempty_valid_structure():
    assert score([100,100],['SUPPORT','RESISTANCE'],100)['state']=='N'
    assert score([],[],100)['state']=='M'
    assert classify(10,0,False)=='M'


@pytest.mark.parametrize('tf',TFS)
def test_current_price_original_reference_parity(tf):
    rng=np.random.default_rng(51);prices=rng.uniform(90,110,1000);kinds=rng.choice(['SUPPORT','RESISTANCE'],1000)
    w=WIDTHS[tf]
    for p in [100.,prices[0]*(1+w),prices[0]*(1-w),prices[0]*(1+1.5*w),prices[0]*(1-1.5*w)]:
        a=score(prices,kinds,p,w);b=score(prices,kinds,p,w,reference=True)
        assert a==b


def test_raw_direction_not_weighted_A1_direction():
    r=score([100.5,100.5,100],['SUPPORT','SUPPORT','RESISTANCE'],100)
    assert r['A1']==0 and r['raw_difference']==1 and r['state']=='S'


def test_nearest_current_price_ties_follow_native_order():
    r=evaluate(np.array([99.,101.]),np.array(['SUPPORT','SUPPORT']),np.array([20,10]),np.array([0,0]),100,.004)
    assert r['nearest_support']==101


def fake():
    patterns=['SSSS','RRRR','SSSR','SSSN','SSRR','RRSS','MMMM']*50
    f=pd.DataFrame(dict(pattern=patterns,joint_quantity=np.arange(len(patterns),dtype=float)+1,flow_status='AVAILABLE'))
    rng=np.random.default_rng(52)
    for i,tf in enumerate(TFS):
        f[tf+'__state']=[p[i] for p in patterns]
        f[tf+'__imbalance']=[{'S':1,'R':-1,'N':0,'M':np.nan}[p[i]] for p in patterns]*rng.uniform(.001,.99,len(f))
        for side in ['support','resistance']:
            f[tf+'__nearest_'+side+'_in_full_band']=rng.random(len(f))>.15
            f[tf+'__nearest_'+side+'_absolute_distance']=rng.uniform(0,.03,len(f))
    a=np.abs(f[[tf+'__imbalance' for tf in TFS]].to_numpy())
    for name,fn in [('minimum',np.min),('median',np.median),('maximum',np.max)]:f['strength_'+name]=fn(a,axis=1)
    return f


def test_exact_hierarchy_is_not_any_k_counts():
    f=fake();model=fit(f);m,meta,c=definitions(f,model)
    assert m['support/path/15m+1h'].sum()==200
    assert np.array_equal(m['support/path/15m+1h+4h+1d'],m['pattern/SSSS'])
    assert not np.any(m['support/hierarchy/3/added_not_aligned']&m['pattern/SSSS'])
    assert all('overlap' not in k for k in m)
    assert len({r[0] for r in c})==len(c)


def test_frozen_strength_quantity_cuts_not_refit():
    f=fake();model=fit(f);f.loc[0,'joint_quantity']=1e12;f.loc[7,'flow_status']='QUARANTINED'
    m,_,_=definitions(f,model)
    assert m['SSSS/quantity/high'][0] and m['SSSS/quantity/missing'][7]
    assert model==fit(fake())
    assert not any('A1' in k for k in model)


def test_continuous_slope_scale_and_constant_guard():
    x=np.arange(10)/10;y=2*x+3
    sums=np.array([len(x),x.sum(),(x*x).sum(),y.sum(),(x*y).sum()])
    assert np.isclose(slope_from_sums(sums),.2)
    assert np.isnan(slope_from_sums(np.array([10,10,10,20,20])))


def test_phase_gate_and_no_spatial_reads():
    with patch('app.current_confluence.contract.check_freeze',side_effect=ValueError('not frozen')):
        with pytest.raises(ValueError):Sources('replication')
    with pytest.raises(ValueError):Sources('development').frame('C:/data/phase5/development/overlaps/2022-01-05.parquet')
    with pytest.raises(ValueError):Sources('2024')
    assert PLAN['no_spatial'] and PLAN['no_detector_change']


def test_exact_hierarchy_shape_sparse_and_nonlinear():
    assert shape(np.array([.1,.2,.3,.4]),[True]*4)=='MONOTONIC_INCREASING'
    assert shape(np.array([.1,.3,.2,.4]),[True]*4)=='NONLINEAR'
    assert shape(np.array([.1,.2,.3,.4]),[True,True,True,False])=='SPARSE'
