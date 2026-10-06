import numpy as np
import pandas as pd
import pytest
from scripts.phase5_1_validation_amendment import shared_close_validation
from app.current_confluence.states import evaluate


def fixture():
    args=(np.array([100.,102.]),np.array(['SUPPORT','RESISTANCE']),np.array([0,0]),np.array([0,0]))
    own=evaluate(*args,100.,.004)
    old=pd.Series(dict(source_price=100.,nearby_support_count=1,nearby_resistance_count=0,coverage_complete=True,
                       A1=own['A1'],A2=own['A2'],snapshot_id='test'))
    return args,old


def test_different_native_close_preserves_current_P_and_warns():
    args,old=fixture();v=evaluate(*args,102.,.004)
    warning=shared_close_validation(3600000,'1h',102.,old,v,args)
    assert warning['current_15m_P']==102 and warning['native_source_P']==100
    assert warning['current_state']=='R' and warning['native_state']=='S'
    assert warning['retained'] and not warning['price_replaced']


def test_identical_close_still_requires_exact_native_parity():
    args,old=fixture();v=evaluate(*args,100.,.004)
    assert shared_close_validation(3600000,'1h',100.,old,v,args) is None
    v['A1']=99
    with pytest.raises(ValueError):shared_close_validation(3600000,'1h',100.,old,v,args)


def test_different_close_cannot_bypass_scalar_reference():
    args,old=fixture();v=evaluate(*args,102.,.004);v['support_count']=100
    with pytest.raises(ValueError):shared_close_validation(3600000,'1h',102.,old,v,args)


def test_native_source_price_is_not_repaired():
    args,old=fixture();v=evaluate(*args,102.,.004);before=old.copy()
    shared_close_validation(3600000,'1h',102.,old,v,args)
    pd.testing.assert_series_equal(before,old)
