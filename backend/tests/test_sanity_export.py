from copy import deepcopy
import json
import pytest
from app.research.models import Candle,canonical
from app.research.volume import Trade,TradeIndex
from app.research.sanity_export import build_exports,write_exports,select_sample


def inputs():
    cs = [Candle(str(i),i*1000,(i+1)*1000,100,103+i%2,97-i%2,101 if i%2==0 else 99) for i in range(12)]
    ts = TradeIndex([Trade(str(i),i*100+1,100+i%3,1+i%2,i%2==0,i,i) for i in range(120)])
    plan = {"start":0,"end":12000,"original_research_end":15000,"symbol":"BTCUSDT","timeframe":"1h",
            "volume_window_ms":1000,"bin_sizes":[1],"zone_half_width":0.01,
            "exit_rule":{"model":"boundary","separation_fraction":0},"tp_grid":[0.01],"sl_grid":[0.01],"horizons":[2],
            "detectors":[{"detector":"A","parameters":{}},{"detector":"B","parameters":{"width":1}},
                         {"detector":"C","parameters":{"reversal_fraction":0.01}},
                         {"detector":"D","parameters":{"bin_size":1,"window_ms":1000,"concentration_multiple":1}}]}
    return cs,ts,plan


def test_reproducible_export_bytes_and_no_outcomes_in_feature_files(tmp_path):
    bundle = build_exports(*inputs())
    assert canonical(bundle) == canonical(build_exports(*inputs()))
    first = write_exports(bundle,tmp_path)
    (tmp_path/"run-report.json").write_text('{"unrelated":"not in hash scope"}')
    assert first == write_exports(bundle,tmp_path)
    for d in bundle["decision_features"]:
        assert "outcome" not in d and "label" not in d and "end" not in d
        assert d["decision_time"] >= d["known_at"]
    assert all(o["future_only"] for o in bundle["outcomes_future"])
    html = (tmp_path/"sanity.html").read_text()
    embedded = json.loads(html.split("const DATA=",1)[1].split(";\nconst $",1)[0])
    assert "outcomes_future" not in embedded and "interactions_retrospective" not in embedded
    assert '<script src=' not in html and '__RESEARCH_DATA__' not in html


def test_reserved_period_refused():
    cs,ts,plan = inputs()
    plan["original_research_end"] = 11000
    with pytest.raises(ValueError,match="original research"):
        build_exports(cs,ts,plan)


def test_decision_features_invariant_to_future_price_and_trade_changes():
    cs,ts,plan = inputs()
    original = build_exports(cs,ts,plan)
    changed = [t for t in ts if t.timestamp < 6000]+[Trade(str(i),i*100+1,100,1e6,True) for i in range(60,120)]
    after = build_exports(cs,TradeIndex(changed),plan)
    # A/B/C candidates and decision records only use candles and trailing trades.
    past = lambda b:[d for d in b["decision_features"] if d["detector"] in ("A","B","C") and d["decision_time"] <= 6000]
    assert past(original) == past(after)


def test_sample_is_deterministic_and_not_outcome_based():
    bundle = build_exports(*inputs())
    assert select_sample(bundle["candidates"],bundle["interactions_retrospective"]) == bundle["sample"]
    assert bundle["sample"]["retrospective_selection"]
    assert all(z in {c["zone_id"] for c in bundle["candidates"]} for z in bundle["sample"]["zone_ids"])
