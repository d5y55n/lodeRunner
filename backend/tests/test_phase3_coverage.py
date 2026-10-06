import json
import pandas as pd
import pytest
from app.market.phase3_coverage import classify_minute,merged_intervals,freeze_policy,window_bounds,POLICY,resolve_boundaries
from app.market.phase3_archives import validate_trade_chunk
from app.research.phase3_profiles import Profiles
from app.research.phase3_engine import load_coverage
from app.research.phase3_plan import utc
from app.research.models import Candidate,Zone


@pytest.mark.parametrize("quantity,kline,agree,expected",[
    (100.,100.,True,"RETAIN_WARNING"),(99.1,100.,True,"RETAIN_WARNING"),
    (98.,100.,True,"QUARANTINE"),(0.,1.,True,"QUARANTINE"),
    (101.1,100.,True,"UNRESOLVED"),(100.,100.,False,"UNRESOLVED"),
    (0.,0.,True,"RETAIN_WARNING"),(float("nan"),1.,True,"UNRESOLVED")])
def test_uniform_quantity_rule(quantity,kline,agree,expected):
    assert classify_minute(quantity,kline,agree)==expected


def test_positive_id_gap_is_not_coverage_failure():
    frame=pd.DataFrame([[10,100,1,10,10,30,"false"]])
    _,stats,_=validate_trade_chunk(frame,0,100,(1,20,1),allow_id_gaps=True)
    assert stats["aggregate_discontinuities"]==1
    with pytest.raises(ValueError):
        validate_trade_chunk(pd.DataFrame([[1,100,1,1,1,30,"false"]]),0,100,(1,20,1),allow_id_gaps=True)


def test_quarantine_does_not_bridge_good_minutes():
    assert merged_intervals([0,60000,180000])==[[0,120000],[180000,240000]]


def test_policy_is_immutable(tmp_path):
    original=freeze_policy(tmp_path)
    assert freeze_policy(tmp_path)==original
    original["policy"]["relative_quantity_tolerance"]=.5
    (tmp_path/(POLICY["version"]+"-policy.json")).write_text(json.dumps(original))
    with pytest.raises(ValueError,match="changed"):freeze_policy(tmp_path)


def test_no_2024_forensic_window():
    ts=utc("2024-01-01")-1
    _,end=window_bounds({"before":{"timestamp":ts-100},"after":{"timestamp":ts}})
    assert end==utc("2024-01-01")


def test_quarantine_marks_features_unavailable_without_reading_trades(tmp_path):
    start=utc("2021-01-01");hour=3600000
    candidate=Candidate("A","SUPPORT",100,start,start+hour,"1h",())
    zone=Zone(candidate,99,101,"fixed_percentage",.01)
    profiles=Profiles(tmp_path,[(start+hour,start+hour+60000)])
    assert profiles.features(zone,start+2*hour,start)["status"]=="QUARANTINED_TRADE_COVERAGE"
    assert profiles.d_candidates(start+hour,start+2*hour,50)==[]
    assert not profiles.quarantined(start+hour+60000,start+2*hour)


def test_research_requires_adjudication(tmp_path):
    with pytest.raises(ValueError,match="adjudication"):load_coverage(tmp_path)


def boundary_rows():
    return [dict(minute=i*60000,quantity=q,kline_quantity=100.,first_time=i*60000+10,
                 last_time=(i+1)*60000-10,decision=classify_minute(q,100.,True))
            for i,q in enumerate([102.,98.,102.])]


def test_boundary_conservation_is_disjoint_and_never_moves_quantity():
    rows=boundary_rows();result=resolve_boundaries(rows)
    assert [r["decision"] for r in result]==["RETAIN_BOUNDARY_WARNING","RETAIN_BOUNDARY_WARNING","UNRESOLVED"]
    assert [r["quantity"] for r in result]==[102.,98.,102.]
    assert rows[0]["decision"]=="UNRESOLVED"


def test_boundary_pair_cannot_explain_actual_outage_or_missing_source():
    rows=boundary_rows()[:2];rows[1]["first_time"]+=5000
    assert resolve_boundaries(rows)[0]["decision"]=="UNRESOLVED"


def test_three_minute_conservation_and_material_net_loss():
    rows=boundary_rows()
    for row,q in zip(rows,[102.,102.,96.]):
        row["quantity"]=q;row["decision"]=classify_minute(q,100.,True)
    assert all(r["decision"]=="RETAIN_BOUNDARY_WARNING" for r in resolve_boundaries(rows))
    rows[-1]["quantity"]=90.;rows[-1]["decision"]="QUARANTINE"
    assert resolve_boundaries(rows)[-1]["decision"]=="QUARANTINE"
    rows=boundary_rows()[:2];rows[0]["source_agrees"]=False
    assert resolve_boundaries(rows)[0]["decision"]=="UNRESOLVED"
