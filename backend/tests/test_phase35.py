import numpy as np
import pandas as pd
import pytest
from app.deepdive.percentiles import historical,frozen_percentiles,normalized_delta,block_labels
from app.deepdive.design import guard,design
from app.deepdive.analyze import percent_bucket,weights_for,match_indices,movement,summarize_matrix
from app.research.phase3_plan import utc


def test_exact_historical_midrank_and_same_time_exclusion():
    start=utc('2021-01-01')
    p,r,n,model=historical([0.,2.,1.,2.,3.],[start,start,start+1,start+1,start+2])
    assert np.isnan(p[:2]).all()
    np.testing.assert_allclose(p[2:],[.5,.75,1.])
    assert list(n)==[0,0,2,2,4]
    later=historical([0.,2.,1.,2.,3.,-999.],[start,start,start+1,start+1,start+2,start+3])[0]
    np.testing.assert_allclose(later[:5],p,equal_nan=True)


def test_event_balanced_ecdf_differs_from_duplicate_row_fit():
    start=utc('2021-01-01')
    p,r,n,model=historical([0.,0.,0.,2.,1.],[start,start,start,start+1,start+2])
    assert p[-1]==.5 and r[-1]==.75
    q,s=frozen_percentiles([1.,np.nan],model)
    assert q[0]==pytest.approx(.5)
    assert np.isnan(q[1])


def test_percentiles_against_brute_force_weighted_past():
    rng=np.random.default_rng(35)
    v=rng.integers(-4,5,90).astype(float)
    t=utc('2021-01-01')+np.repeat(np.arange(30),3)
    p,r,n,_=historical(v,t)
    for i in range(3,len(v)):
        past=t<t[i];weights=np.full(past.sum(),1/3)
        expected=np.sum(weights*((v[past]<v[i])+.5*(v[past]==v[i])))/weights.sum()
        assert p[i]==pytest.approx(expected)
        assert r[i]==pytest.approx(expected)
        assert n[i]==past.sum()


def test_movement_matches_expanded_rows_with_censoring():
    values=np.array([.3,.9,1.5,2.])
    weights=np.array([[1.,3.,2.,9.],[0.,0.,0.,1.]])
    complete=np.array([True,True,True,False])
    mean,median=movement(weights,values,complete)
    expanded=np.repeat(values[:3],weights[0,:3].astype(int))
    assert mean[0]==pytest.approx(expanded.mean())
    assert median[0]==pytest.approx(np.median(expanded))
    assert np.isnan(mean[1]) and np.isnan(median[1])


@pytest.mark.parametrize('day',['2020-12-31','2023-01-01','2024-01-01'])
def test_fit_rejects_non_development(day):
    with pytest.raises(ValueError,match='development'):historical([1.],[utc(day)])


def test_normalized_delta_and_zero_volume():
    result=normalized_delta([3.,0.,2.],[1.,0.,2.],[4.,0.,4.])
    np.testing.assert_allclose(result[[0,2]],[.5,0.])
    assert np.isnan(result[1])


def test_quarter_split_and_boundaries():
    assert list(block_labels([utc('2021-03-31'),utc('2021-04-01'),utc('2022-12-31')]))==['2021-Q1','2021-Q2','2022-Q4']
    assert list(percent_bucket([0.,.1,.99,1.,np.nan],10))==[1,2,10,10,0]


def test_no_2024_access():
    guard(utc('2023-01-01'),utc('2024-01-01'))
    with pytest.raises(ValueError,match='2024'):guard(utc('2023-01-01'),utc('2024-01-02'))
    assert design()['replication_label']=='previously inspected replication period'


def test_design_roundtrip_and_report_reproducibility():
    import json
    from app.deepdive.reports import markdown,svg_lines
    assert json.loads(json.dumps(design()))==design()
    frame=pd.DataFrame(dict(x=[1,2],y=[.1,np.nan]))
    assert markdown(frame)==markdown(frame.copy())
    args=('A & delta',[('support',[1,2],[.1,.2])],'decile')
    assert svg_lines(*args)==svg_lines(*args)
    assert 'A &amp; delta' in svg_lines(*args)


def test_matching_strictly_matured_and_context_separated():
    times=np.arange(6)*3600000
    cells=np.asarray(['LOW|NEGATIVE','LOW|NEGATIVE','HIGH|POSITIVE','LOW|NEGATIVE','CALIBRATION|CALIBRATION','LOW|NEGATIVE'])
    result=match_indices(times,cells,np.ones(6,dtype=bool),2)
    assert result.tolist()==[-1,-1,-1,1,-1,3]
    valid=result>=0
    assert (times[result[valid]]+2*3600000<=times[valid]).all()


def test_event_weights_and_exact_median():
    w=weights_for([0,0,1],[0,0,0],2,1)
    assert w.tolist()==[[2.,1.]]
    mean,median=movement(w,np.asarray([1.,5.]),np.asarray([True,True]))
    assert mean[0]==pytest.approx(7/3) and median[0]==1.
    large=weights_for([17000],np.array([20],dtype=np.int16),17519,21)
    assert large[20,17000]==1 and large.sum()==1


def test_summary_event_balance_and_reproducibility():
    meta=pd.DataFrame([dict(family='A_ALONE',facet='ALL',facet_value='ALL',bucket='ALL')])
    events=pd.DataFrame(dict(event_id=['a','b'],timestamp=[0,7200000],volatility_regime=['LOW']*2,return_regime=['POSITIVE']*2)).set_index('event_id')
    outcomes=pd.DataFrame(dict(event_id=['a','b'],direction=['LONG']*2,tp=[.003]*2,sl=[.003]*2,horizon=[1]*2,
        censored=[False]*2,label=['TP_FIRST','SL_FIRST'],mfe_pct=[1.,2.],mae_pct=[2.,1.]))
    args=(meta,np.array([[9.,1.]]),{('ALL','ALL'):0},events,outcomes)
    a,links=summarize_matrix(*args);b,_=summarize_matrix(*args)
    pd.testing.assert_frame_equal(a,b)
    assert a.iloc[0].tp_first_rate==.9
    assert a.iloc[0].event_balanced_tp_first_rate==.5
    assert a.iloc[0].unique_event_count==2
    outcomes.loc[1,['censored','label']]=[True,None]
    censored,_=summarize_matrix(meta,np.array([[9.,1.]]),{('ALL','ALL'):0},events,outcomes)
    assert censored.iloc[0].event_balanced_tp_first_rate==1.
    assert censored.iloc[0].event_balanced_censored_rate==.5


@pytest.mark.parametrize('kind',['SUPPORT','RESISTANCE'])
def test_support_resistance_and_visits_not_pooled(kind):
    from app.deepdive.analyze import memberships
    frame=pd.DataFrame(dict(event_id=['a','b','c'],kind=['SUPPORT','RESISTANCE','SUPPORT'],
        historical_delta_percentile=[.1,.2,.3],historical_row_percentile=[.1,.2,.3],percentile_history_rows=[100]*3,
        normalized_delta=[-.1,0.,.1],volume_delta=[-1.,0.,1.],legacy_delta_quartile=[1,2,3],
        visit_group=['1','2','4+'],quarter=['2021-Q1']*3,volatility_regime=['LOW']*3,return_regime=['POSITIVE']*3))
    meta,w,base=memberships(frame[frame.kind==kind],pd.Index(['a','b','c']))
    assert w[base[('ALL','ALL')]].sum()==(2 if kind=='SUPPORT' else 1)
    for facet,value in base:
        if facet=='visit_group':assert w[base[(facet,value)]].sum()==1
