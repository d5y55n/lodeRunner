import numpy as np
import pandas as pd
import pytest
from app.multimap.analyze import arrays, summarize, quartiles, buckets, bootstrap
from app.multimap.run import outcomes
from app.multimap.contract import STEPS
from app.research.models import Candle


@pytest.mark.parametrize('tf,expected',[('15m',{16,32,96}),('4h',{1,2,6}),('1d',{1,2,3})])
def test_native_grid_and_censored_composition(tf,expected):
    step=STEPS[tf]
    cs=[Candle(str(i),i*step,(i+1)*step,100,101,99,100) for i in range(110)]
    events=pd.DataFrame({'event_id':['a','b']})
    labels=pd.DataFrame(outcomes(cs,step,tf,'a',110*step)+outcomes(cs,109*step,tf,'b',110*step))
    grids,ys=arrays(events,labels,tf)
    assert {g[3] for g in grids}==expected
    summary=summarize(pd.DataFrame({'period':['ALL','ALL']}),ys,grids)
    assert (summary.complete+summary.censored==summary.state_count).all()
    assert (summary.TP_FIRST+summary.SL_FIRST+summary.NEITHER+summary.AMBIGUOUS==summary.complete).all()
    assert summary.AMBIGUOUS.sum()>0


def test_frozen_quantiles_missing_and_outside_development_range():
    cuts=quartiles([1,2,3,4,np.nan])
    assert cuts==[1.75,2.5,3.25]
    assert list(buckets([-100,2,3,100,np.nan],cuts))==[0,1,2,3,-1]
    assert quartiles([np.nan])==[]


def test_bootstrap_deterministic_and_sparse_blocks_unestimated():
    f=pd.DataFrame({'decision_timestamp':np.arange(8)*7*86400000})
    grids=[('LONG',.003,.005,1)]*24
    values={'complete':np.ones((8,24)),'TP_FIRST':np.tile(np.arange(8)[:,None]%2,(1,24)),
            'AMBIGUOUS':np.zeros((8,24))}
    groups=np.array([0,0,0,1,1,1,1,1])
    a=bootstrap(f,values,grids,groups);b=bootstrap(f,values,grids,groups)
    pd.testing.assert_frame_equal(a,b)
    assert a[a.bucket==0].ci_low.isna().all()
    assert a[a.bucket==1].ci_low.notna().all()
