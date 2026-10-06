import pytest
from app.research.phase3_identity import event_id,interaction_id,measurement_id
from app.research.phase3_context import Quantiles,matched_control,frozen_subset


def records():
    return [{"timestamp":i,"volatility":float(i%3),"recent_return":float(i%2)} for i in range(1,20)]


def test_event_identity_shared_across_configurations():
    event = event_id("BTCUSDT","1h",100)
    interactions = [interaction_id("candidate",f"config-{i}",90,1) for i in range(10)]
    assert len(set(interactions))==10
    assert len({event_id("BTCUSDT","1h",100) for _ in interactions})==1
    assert measurement_id(event,interactions[0],"c","LONG",.01,.01,4) != measurement_id(event,interactions[0],"c","SHORT",.01,.01,4)


def test_buckets_reject_validation_and_ignore_missing():
    with pytest.raises(ValueError,match="non-development"):
        Quantiles.fit("volatility",records(),15)
    model = Quantiles.fit("volatility",records(),20)
    assert model.bucket(None)=="MISSING"
    assert model.bucket(0)==model.bucket(0)


def test_matching_never_uses_future_or_unmatured_control():
    pool = records()
    v = Quantiles.fit("volatility",pool,20)
    r = Quantiles.fit("recent_return",pool,20)
    target = {"timestamp":30,"volatility":1.,"recent_return":1.}
    selected = matched_control(target,pool+[dict(target,timestamp=31)],v,r,4)
    assert selected["timestamp"]+4 <= target["timestamp"]
    assert selected==matched_control(target,pool,v,r,4)


def test_freeze_identity_reproducible():
    models=[Quantiles.fit("volatility",records(),20)]
    assert frozen_subset([{"detector":"A"}],models,20)==frozen_subset([{"detector":"A"}],models,20)
