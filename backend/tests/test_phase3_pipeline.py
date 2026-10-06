import json
import zipfile
from dataclasses import asdict
import numpy as np
import pandas as pd
import pytest
from app.research.phase3_context import ControlIndex,Quantiles,matched_control,frozen_subset,verify_freeze
from app.research.phase3_profiles import Profiles
from app.research.volume import Trade,VolumeConcentration,zone_features
from app.research.models import Candidate,Zone
from app.research.phase3_plan import utc
from app.market.phase3_archives import process_trades
from app.research import phase3_engine as engine


def test_indexed_controls_equal_reference():
    pool=[dict(timestamp=i,volatility=i%5,recent_return=i%3) for i in range(100)]
    models=[Quantiles(f,(1.,2.,3.),10,10) for f in ("volatility","recent_return")]
    index=ControlIndex(pool,*models)
    for target in pool[10:]:
        for horizon in (1,4,24):
            assert index.match(target,horizon)==matched_control(target,pool,*models,horizon)


def test_freeze_rejects_modified_rule():
    frozen=frozen_subset([],[],100,"coverage only")
    verify_freeze(json.loads(json.dumps(frozen)))
    frozen["selection_rule"]="changed"
    with pytest.raises(ValueError,match="modified"):verify_freeze(frozen)


def test_missing_dates_are_not_filled(tmp_path):
    archive=tmp_path/"tiny.zip"
    start=utc("2021-01-01")
    with zipfile.ZipFile(archive,"w") as z:
        z.writestr("tiny.csv",f"1,100,1,1,1,{start},false\n")
    report=dict(month="2021-01",start=start,end=start+2*86400000)
    with pytest.raises(ValueError,match="Missing trade dates"):
        process_trades(archive,report,tmp_path)
    assert report["missing_dates"]==["2021-01-02"]
    assert not (tmp_path/"profiles/2021-01.parquet").exists()


def test_profiles_equal_real_trade_semantics_and_exclude_future(tmp_path):
    start=utc("2021-01-01");hour=3600000
    trades=[Trade(str(i),start+h*hour+1,p,q,m) for i,(h,p,q,m) in enumerate([
        (0,100.,2.,False),(0,150.,1.,True),(1,100.,6.,True),(1,149.9,2.,False),
        (2,100.,99999.,False)])]
    frame=pd.DataFrame([dict(hour=t.timestamp//hour*hour,price=t.price,quantity=t.quantity,
                            buy=0. if t.buyer_is_maker else t.quantity,
                            sell=t.quantity if t.buyer_is_maker else 0.) for t in trades])
    frame.to_parquet(tmp_path/"2021-01.parquet",index=False)
    profiles=Profiles(tmp_path)
    candidate=Candidate("A","SUPPORT",100.,start,start+hour,"1h",())
    zone=Zone(candidate,99.,150.,"fixed_percentage",.1)
    actual=profiles.features(zone,start+2*hour,start)
    expected=zone_features(zone,trades,start+2*hour,hour,start,start+3*hour)
    for key in ("quantity","aggressive_buy_quantity","aggressive_sell_quantity","volume_delta","relative_zone_volume"):
        assert actual[key]==pytest.approx(expected[key])
    assert actual["quantity"]==8.
    optimized=profiles.d_candidates(start,start+2*hour,50,1.5)
    reference=VolumeConcentration(trades,50,hour,1.5,start).detect([],"1h",start+2*hour)
    assert [(c.price,c.known_at) for c in optimized]==[(c.price,c.known_at) for c in reference]
    with pytest.raises(ValueError,match="aligned"):profiles.features(zone,start+2*hour+1,start)


def test_small_end_to_end_reproducible(tmp_path,monkeypatch):
    start=utc("2021-01-01");n=72;hour=3600000;end=start+n*hour
    monkeypatch.setattr(engine,"DEVELOPMENT_START",start)
    monkeypatch.setattr(engine,"DEVELOPMENT_END",end)
    monkeypatch.setattr(engine,"require_catalog",lambda *args:(["2021-01"],[]))
    monkeypatch.setattr(engine,"load_coverage",lambda *args:{"coverage_id":"synthetic-test","quarantine_intervals":[]})
    (tmp_path/"candles").mkdir();(tmp_path/"profiles").mkdir()
    rows=[];profiles=[]
    for i in range(n):
        op=100+np.sin(i)*2;close=100+np.sin(i+1)*2
        rows.append(dict(open_time=start+i*hour,close_time=start+(i+1)*hour-1,
            open=op,high=max(op,close)+1,low=min(op,close)-1,close=close,volume=10.,
            quote_volume=1000.,trade_count=10,taker_buy_volume=5.,taker_buy_quote_volume=500.,ignore=0))
        profiles.extend(dict(hour=start+i*hour,price=float(p),quantity=float(i+1),buy=float(i+1),sell=0.) for p in range(95,106))
    pd.DataFrame(rows).to_parquet(tmp_path/"candles/2021-01.parquet",index=False)
    pd.DataFrame(profiles).to_parquet(tmp_path/"profiles/2021-01.parquet",index=False)
    plan=engine.manifest();configs=engine.configurations(plan)[:2]
    dest=engine.generate(tmp_path,"development",configs,plan)
    first=pd.read_parquet(dest/"interactions.parquet")
    volume=[Quantiles(f,(1.,2.,3.),end,10) for f in
            ("quantity","relative_zone_volume","aggressive_buy_quantity","aggressive_sell_quantity","volume_delta")]
    context=[Quantiles(f,(-.01,.0,.01),start+24*hour,10) for f in ("volatility","recent_return")]
    table=engine.summarize(dest,volume,context)
    assert not table.empty and (dest/"matched_baseline.csv").exists()
    from app.research.phase3_disk_summary import summarize_disk
    optimized=summarize_disk(dest,volume,context)
    for name in ("measurement_count","unique_event_count","tp_first_rate","mfe_pct_median"):
        assert np.allclose(sorted(table[name]),sorted(optimized[name]),equal_nan=True)
    engine.generate(tmp_path,"development",configs,plan)
    pd.testing.assert_frame_equal(first,pd.read_parquet(dest/"interactions.parquet"))
    assert (pd.read_parquet(dest/"events.parquet").timestamp<end).all()


@pytest.mark.parametrize("quarantine", [False, True])
def test_batch_features_match_scalar_past_only(tmp_path, quarantine):
    from app.research.phase3_feature_batch import build_features
    start = utc("2021-01-01")
    hour = 3600000
    (tmp_path / "profiles").mkdir()
    dest = tmp_path / "development"
    dest.mkdir()
    pd.DataFrame([
        dict(hour=start+h*hour, price=p, quantity=q, buy=q*.25, sell=q*.75)
        for h, q in [(0, 2.), (1, 6.), (2, 999999.)]
        for p in [99., 100., 101.]
    ]).to_parquet(tmp_path / "profiles/2021-01.parquet", index=False)
    rows = [dict(interaction_id=str(i), event_id="event", observed_at=start+2*hour,
                 known_at=start, zone_lower=lo, zone_upper=hi)
            for i, (lo, hi) in enumerate([(99., 100.), (100., 101.), (99.5, 100.5), (102., 103.)])]
    pd.DataFrame(rows).to_parquet(dest / "interactions.parquet", index=False)
    intervals = [(start, start+60000)] if quarantine else []
    assert build_features(dest, tmp_path, start, intervals) == len(rows)
    actual = pd.read_parquet(dest / "decision_features.parquet").set_index("interaction_id")
    profiles = Profiles(tmp_path / "profiles", intervals)
    candidate = Candidate("A", "SUPPORT", 100., start, start+1, "1h", ())
    for row in rows:
        zone = Zone(candidate, row["zone_lower"], row["zone_upper"], "fixed_percentage", .01)
        expected = profiles.features(zone, start+2*hour, start)
        result = actual.loc[row["interaction_id"]]
        assert result.status == expected["status"]
        for key in ("quantity", "aggressive_buy_quantity", "aggressive_sell_quantity", "volume_delta", "relative_zone_volume"):
            if expected.get(key) is None:
                assert pd.isna(result[key])
            else:
                assert result[key] == pytest.approx(expected[key])
