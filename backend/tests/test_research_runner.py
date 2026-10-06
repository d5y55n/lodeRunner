from dataclasses import replace
import math
import pytest
from app.research.config import Experiment, Periods
from app.research.models import Candle, canonical
from app.research.runner import run, run_grid
from app.research.volume import Trade
from app.research.data import from_market
from app.market.models import Candle as MarketCandle


def candles():
    result = []
    for i in range(60):
        o = 100+4*math.sin(i)
        close = 100+4*math.sin(i+1)
        result.append(Candle(str(i),i*1000,(i+1)*1000,o,max(o,close)+1+i*0.001,min(o,close)-1-i*0.001,close))
    return result


def config(**kwargs):
    default = dict(symbol="BTCUSDT",timeframe="1h",dataset_id="synthetic-v1",
                   periods=Periods(0,30000,45000,60000),detector="A",detector_parameters={},
                   width_model="fixed_percentage",width_parameter=0.002,horizons=(2,4),
                   tp_grid=(0.01,),sl_grid=(0.01,))
    return Experiment(**(default|kwargs))


def test_reproducibility_full_payload_and_identity():
    a = run(candles(),config())
    b = run(candles(),config())
    assert canonical(a) == canonical(b)
    assert a["candidates"] and a["interactions"] and a["measurements"]
    assert a["manifest"]["config"]["detector"] == "A"
    assert run(candles(),config(width_parameter=0.003))["experiment_id"] != a["experiment_id"]


def test_multiple_a_widths_and_independent_b_c_parameters():
    cfgs = [config(width_parameter=w) for w in (0.0005,0.002,0.005)]
    cfgs += [config(detector="B",detector_parameters={"width":w}) for w in (1,2)]
    cfgs += [config(detector="C",detector_parameters={"reversal_fraction":r}) for r in (0.01,0.03)]
    results = run_grid(candles(),cfgs)
    assert len({r["experiment_id"] for r in results}) == 7
    assert all(r["candidates"] for r in results)
    for r in results:
        known = {z["id"]:z["candidate"]["known_at"] for z in r["zones"]}
        assert all(v["start"] >= known[v["zone_id"]] for v in r["interactions"])
        assert len({(v["zone_id"],v["number"]) for v in r["interactions"]}) == len(r["interactions"])


def test_unseen_validation_and_test_cannot_change_research_results():
    cs = candles()
    original = run(cs,config())
    changed = cs[:30]+[replace(c,open=c.open*10,high=c.high*10,low=c.low*10,close=c.close*10) for c in cs[30:]]
    assert canonical(original) == canonical(run(changed,config()))
    assert all(row["outcome"]["measured_until"] <= 30000 for row in original["measurements"])


def test_validation_resets_and_final_test_locked():
    result = run(candles(),config(phase="validation"))
    assert all(c["source_timestamp"] >= 30000 for c in result["candidates"])
    assert all(r["outcome"]["measured_until"] <= 45000 for r in result["measurements"])
    with pytest.raises(ValueError,match="untouched"):
        config(phase="test")


def test_control_schedule_independent_of_detector_and_width():
    a = run(candles(),config())
    b = run(candles(),config(detector="B",detector_parameters={"width":2},width_parameter=0.005))
    controls = lambda r: [row for row in r["measurements"] if row["group"] == "control"]
    assert controls(a) == controls(b)
    assert a["comparison"]
    assert all(c["event"]["complete"]+c["event"]["censored"] == c["event"]["total"] for c in a["comparison"])


def test_missing_trade_features_explicit_and_d_requires_trades():
    a = run(candles(),config(volume_window_ms=1000))
    assert all(row["volume_features"]["status"] == "MISSING_TRADE_DATA"
               for row in a["measurements"] if row["group"] == "event")
    d = config(detector="D",detector_parameters={"bin_size":1,"window_ms":5000,"concentration_multiple":1.5})
    with pytest.raises(ValueError,match="trade-level"):
        run(candles(),d)


def test_d_runs_independently_on_real_trade_contract():
    ts = [Trade(str(i),i*1000+1,100 if i%2 else 102,10 if i%2 else 1,False) for i in range(30)]
    d = config(detector="D",detector_parameters={"bin_size":1,"window_ms":5000,"concentration_multiple":1.5})
    result = run(candles(),d,ts,(0,30000))
    assert result["candidates"]
    assert all(c["kind"] == "NEUTRAL" for c in result["candidates"])
    assert result["manifest"]["trade_sha256"]


def test_a_with_trade_volume_features():
    ts = [Trade(str(i),i*1000+1,100,1,False) for i in range(30)]
    result = run(candles(),config(volume_window_ms=1000),ts,(0,30000))
    statuses = {row["volume_features"]["status"] for row in result["measurements"] if row["group"] == "event"}
    assert "AVAILABLE" in statuses


def test_phase1_candle_adapter_exclusive_end_and_identity():
    c = MarketCandle(open_time=0,close_time=3599999,open=100,high=101,low=99,close=100,
                    volume=1,quote_volume=100,trade_count=1,taker_buy_volume=1,taker_buy_quote_volume=100)
    converted, = from_market([c],"BTCUSDT","1h")
    assert converted.end == 3600000 and converted.id == "BTCUSDT:1h:0"


@pytest.mark.parametrize("kwargs",[
    {"horizons":(0,)},{"tp_grid":(0,)},{"sl_grid":(float("nan"),)},
    {"width_parameter":float("inf")},{"control_stride":0},
    {"detector_parameters":{"invented":1}},
])
def test_invalid_experiment_rejected(kwargs):
    with pytest.raises(ValueError):
        config(**kwargs)
