from dataclasses import asdict
import pytest
from app.research.models import Candidate
from app.research.zones import construct
from app.research.volume import Trade,TradeIndex,aggregate,zone_features,VolumeConcentration


def trades():
    return [Trade("1",1,100,2,False),Trade("2",9,100.09,3,True),
            Trade("3",10,100.10,7,False),Trade("4",19,100.11,1,True),
            Trade("5",20,100,1000000,True)]


def test_index_preserves_exact_binning_and_boundary_semantics():
    ts = trades()
    assert aggregate(ts,0.1,0,20,20) == aggregate(TradeIndex(ts),0.1,0,20,20)
    a,b = aggregate(TradeIndex(ts),0.1,0,20,20)
    assert (a.quantity,b.quantity) == (5,8)
    assert (a.volume_delta,b.volume_delta) == (-1,6)
    assert (b.aggressive_buy_quantity,b.aggressive_sell_quantity) == (7,1)


def test_index_and_plain_volume_features_past_only():
    z = construct(Candidate("A","SUPPORT",100,0,10,"1h",("0",)),"fixed_percentage",0.01)
    ts = trades()
    expected = zone_features(z,ts[:4],20,10,0,30)
    assert expected == zone_features(z,TradeIndex(ts),20,10,0,30)
    assert expected["quantity"] == 8 and expected["baseline_quantity"] == 5
    assert expected["relative_zone_volume"] == 1.6
    assert expected["volume_delta"] == 6


@pytest.mark.parametrize("detector",["A","B","C"])
def test_future_mutation_cannot_change_decision_features(detector):
    z = construct(Candidate(detector,"RESISTANCE",100,0,10,"1h",("0",)),"fixed_percentage",0.01)
    base = trades()
    mutated = base[:4]+[Trade("5",20,100,1e12,False),Trade("6",21,100,1e12,True)]
    assert zone_features(z,TradeIndex(base),20,10,0,30) == zone_features(z,TradeIndex(mutated),20,10,0,30)


def test_d_real_archive_contract_and_determinism():
    ts = TradeIndex(trades())
    a = VolumeConcentration(ts,0.1,10,1.0,0).detect([],"1h",20)
    b = VolumeConcentration(trades()[:4],0.1,10,1.0,0).detect([],"1h",20)
    assert a == b and len(a) == 2 and all(c.kind == "NEUTRAL" for c in a)
    assert all(c.known_at in (10,20) for c in a)


def test_index_rejects_duplicate_ids():
    with pytest.raises(ValueError):
        TradeIndex([trades()[0],trades()[0]])
