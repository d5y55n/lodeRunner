import numpy as np
import pandas as pd
import pytest
from app.multimap.profiles import STEP, aggregate, combine, Profiles15m
from app.multimap.contract import FINAL_START, sha256, write_json


def trades():
    return pd.DataFrame(dict(timestamp=[0, STEP-1, STEP, 2*STEP-1, 2*STEP],
                             price=[100., 100., 101., 100., 100.],
                             quantity=[2., 3., 5., 7., 1000.],
                             maker=[False, True, False, True, False]))


def test_quarter_boundaries_direction_and_delta():
    f = aggregate(trades())
    first = f[f.start == 0].iloc[0]
    assert first.quantity == 5 and first.buy == 2 and first.sell == 3 and first.delta == -1
    assert f[f.start == STEP].quantity.sum() == 12
    assert f[f.start == 2*STEP].quantity.sum() == 1000


def test_chunking_and_input_order_invariance():
    f = trades()
    expected = aggregate(f)
    pd.testing.assert_frame_equal(expected, combine([aggregate(f[:1]), aggregate(f[1:3]), aggregate(f[3:])]))
    pd.testing.assert_frame_equal(expected, aggregate(f.sample(frac=1, random_state=40)))


def test_no_future_trade_changes_past_profile():
    f = trades()
    pd.testing.assert_frame_equal(aggregate(f[f.timestamp < 2*STEP]),
                                  aggregate(f).query('start < @STEP * 2').reset_index(drop=True))


def fixture_profile(root, quarantines=()):
    directory = root / '1970-01'
    directory.mkdir()
    path = directory / '1970-01-01.parquet'
    aggregate(trades()).to_parquet(path, index=False)
    write_json(directory / 'manifest.json', dict(quarantines=quarantines, partitions={path.name: sha256(path)}))
    return path


def test_reader_causal_windows_missing_is_not_zero(tmp_path):
    fixture_profile(tmp_path)
    p = Profiles15m(tmp_path)
    assert p.window(2*STEP, 1).quantity.sum() == 12
    assert p.interval(3*STEP, 4*STEP) is None
    with pytest.raises(ValueError):p.interval(STEP, STEP)
    with pytest.raises(ValueError):p.interval(1, 2*STEP)
    with pytest.raises(ValueError):p.interval(FINAL_START, FINAL_START+STEP)
    with pytest.raises(ValueError):p.window(2*STEP, 2)


def test_quarantine_retained_but_unavailable(tmp_path):
    fixture_profile(tmp_path, [(STEP+1, STEP+2)])
    p = Profiles15m(tmp_path)
    assert p.interval(STEP, 2*STEP) is None
    assert p.interval(0, STEP).quantity.sum() == 5


def test_incomplete_month_not_published_and_hash_checked(tmp_path):
    path = fixture_profile(tmp_path)
    path.write_bytes(b'corrupted')
    with pytest.raises(ValueError, match='checksum'):Profiles15m(tmp_path).interval(0, STEP)
    assert Profiles15m(tmp_path).interval(32*86400000, 32*86400000+STEP) is None


def test_zone_union_deduplication_and_causal_flow(tmp_path):
    from app.multimap.flow import spans, measure_flow
    fixture_profile(tmp_path)
    zones=spans(np.array([100.,100.,100.]),np.array(['SUPPORT','SUPPORT','RESISTANCE']),100.,.002)
    assert len(zones['support'])==len(zones['joint'])==1
    result=measure_flow(Profiles15m(tmp_path),'15m',2*STEP,1,zones,[])
    assert result['joint_quantity']==7 and result['joint_sell']==7 and result['joint_delta']==-7
    assert result['shared_quantity']==7
    assert result['observation_end']==2*STEP
    missing=measure_flow(Profiles15m(tmp_path),'15m',4*STEP,1,zones,[])
    assert missing['flow_status']=='MISSING_PROFILE' and np.isnan(missing['joint_quantity'])
    quarantined=measure_flow(Profiles15m(tmp_path),'15m',2*STEP,1,zones,[(STEP,2*STEP)])
    assert quarantined['flow_status']=='QUARANTINED' and np.isnan(quarantined['joint_quantity'])


def test_flow_native_width_not_hourly_width():
    from app.multimap.flow import spans
    p=np.array([100.]);k=np.array(['SUPPORT'])
    assert spans(p,k,100.5,.002)['support']==[]
    assert spans(p,k,100.5,.007)['support']


def test_cached_window_has_exact_original_values_and_causal_guards(tmp_path):
    from app.multimap.flow import CachedProfiles15m
    fixture_profile(tmp_path)
    old=Profiles15m(tmp_path);new=CachedProfiles15m(tmp_path)
    for t in [STEP,2*STEP,3*STEP,STEP]:
        pd.testing.assert_frame_equal(old.window(t,1),new.window(t,1))
    with pytest.raises(ValueError):new.window(FINAL_START,1)
    with pytest.raises(ValueError):new.window(2*STEP,2)
