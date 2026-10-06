import pytest
from app.research.models import Candle
from app.research.outcomes import measure


def c(i,h,l,close=100,open_=100):
    return Candle(str(i),i*1000,(i+1)*1000,open_,h,l,close)


@pytest.mark.parametrize("direction,high,low,label",[
    ("LONG",102,99.5,"TP_FIRST"),("LONG",100.5,98,"SL_FIRST"),
    ("LONG",100.5,99.5,"NEITHER"),("LONG",102,98,"AMBIGUOUS"),
    ("SHORT",100.5,98,"TP_FIRST"),("SHORT",102,99.5,"SL_FIRST"),
    ("SHORT",100.5,99.5,"NEITHER"),("SHORT",102,98,"AMBIGUOUS"),
])
def test_first_touch_labels(direction,high,low,label):
    result = measure(100,1000,[c(1,high,low)],direction,0.01,0.01,1)
    assert result.label == label and not result.censored


def test_first_hit_is_not_replaced_by_later_hit():
    assert measure(100,1000,[c(1,102,99.5),c(2,102,98)],"LONG",0.01,0.01,2).label == "TP_FIRST"


def test_entry_candle_excluded_and_short_tail_censored():
    r = measure(100,1000,[c(0,110,90),c(1,100.5,99.5)],"LONG",0.01,0.01,2)
    assert r.label is None and r.censored and r.observed_candles == 1


@pytest.mark.parametrize("direction,mfe,mae,tmfe,tmae",[
    ("LONG",5,4,2000,1000),("SHORT",4,5,1000,2000)])
def test_mfe_mae_full_horizon_and_times(direction,mfe,mae,tmfe,tmae):
    r = measure(100,1000,[c(1,102,96),c(2,105,98)],direction,0.01,0.01,2)
    assert r.mfe_pct == pytest.approx(mfe)
    assert r.mae_pct == pytest.approx(mae)
    assert (r.time_to_mfe_ms,r.time_to_mae_ms) == (tmfe,tmae)


def test_gap_open_resolves_order_when_open_already_beyond_stop():
    r = measure(100,1000,[c(1,103,95,100,96)],"LONG",0.01,0.01,1)
    assert r.label == "SL_FIRST" and r.first_hit_at == 1000


def test_horizon_is_only_observation_window():
    cs = [c(1,100.5,99.5),c(2,102,99.5)]
    assert measure(100,1000,cs,"LONG",0.01,0.01,1).label == "NEITHER"
    assert measure(100,1000,cs,"LONG",0.01,0.01,2).label == "TP_FIRST"


def test_unsorted_or_missing_outcome_candles_rejected():
    with pytest.raises(ValueError):
        measure(100,1000,[c(2,102,98),c(1,102,98)],"LONG",0.01,0.01,2)
    with pytest.raises(ValueError):
        measure(100,1000,[c(1,102,98),c(3,102,98)],"LONG",0.01,0.01,2)
