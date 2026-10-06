import pytest
from app.research.models import Candidate
from app.research.zones import construct
from app.research.volume import Trade, aggregate, VolumeConcentration, zone_features


def test_trade_bins_exact_decimal_boundaries_and_sides():
    trades = [Trade("1",1,100.0,2,False),Trade("2",2,100.09,3,True),Trade("3",3,100.1,4,False)]
    a,b = aggregate(trades,0.1,0,10,10)
    assert (a.lower,a.upper,a.quantity,a.aggressive_buy_quantity,a.aggressive_sell_quantity,a.volume_delta) == (100,100.1,5,2,3,-1)
    assert (b.lower,b.quantity,b.volume_delta) == (100.1,4,4)
    assert (a.observation_start,a.observation_end) == (0,10)


def test_unknown_side_is_not_silently_assigned():
    b, = aggregate([Trade("1",1,100,3,None)],1,0,2,2)
    assert b.unknown_side_quantity == 3 and b.volume_delta is None


def test_aggregate_trade_maker_mapping():
    t = Trade.from_binance_aggregate({"a":1,"T":1,"p":"100","q":"3","m":True})
    b, = aggregate([t],1,0,2,2)
    assert b.aggressive_sell_quantity == 3


def test_d_neutral_candidates_only_after_window_complete():
    ts = [Trade("1",1,100,10,False),Trade("2",2,102,1,True),Trade("3",12,200,1000,True)]
    d = VolumeConcentration(ts,1,10,1.5,0)
    assert d.detect([],"1h",9) == []
    event, = d.detect([],"1h",10)
    assert (event.kind,event.price,event.known_at) == ("NEUTRAL",100.5,10)
    assert event.metadata["bin"]["quantity"] == 10
    assert [e for e in d.detect([],"1h",20) if e.known_at <= 10] == [event]


def test_zone_volume_uses_past_equal_duration_baseline():
    z = construct(Candidate("A","SUPPORT",100,0,10,"1h",("0",)),"fixed_percentage",0.01)
    ts = [Trade("1",2,100,2,False),Trade("2",12,100,6,True),Trade("3",22,100,1000,True)]
    f = zone_features(z,ts,20,10,0,30)
    assert f["quantity"] == 6 and f["relative_zone_volume"] == 3 and f["volume_delta"] == -6
    assert f["baseline_definition"] == "same_zone_previous_equal_duration"
    assert zone_features(z,ts,20,10,5,30)["status"] == "MISSING_TRADE_COVERAGE"


def test_trade_duplicates_and_future_windows_rejected():
    t = Trade("1",1,100,1,True)
    with pytest.raises(ValueError):
        aggregate([t,t],1,0,2,2)
    with pytest.raises(ValueError):
        aggregate([t],1,0,3,2)


def test_zero_volume_baseline_ratio_missing_not_infinity():
    z = construct(Candidate("B","RESISTANCE",100,0,10,"1h",("0",)),"fixed_percentage",0.01)
    f = zone_features(z,[Trade("1",12,100,6,True)],20,10,0,20)
    assert f["baseline_quantity"] == 0 and f["relative_zone_volume"] is None


def test_future_trades_cannot_change_features_at_observation_time():
    z = construct(Candidate("C","SUPPORT",100,0,10,"1h",("0",)),"fixed_percentage",0.01)
    past = [Trade("1",2,100,1,True),Trade("2",12,100,2,False)]
    future = past+[Trade("3",22,100,10000,True)]
    assert zone_features(z,past,20,10,0,30) == zone_features(z,future,20,10,0,30)
