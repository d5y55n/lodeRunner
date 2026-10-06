import pytest
from app.research.models import Candle
from app.research.detectors import ReversalCandles, LocalExtrema, ConfirmedReversal


def c(i, o=100, h=103, l=97, close=101):
    return Candle(str(i), i*1000, (i+1)*1000, o, h, l, close)


@pytest.mark.parametrize("h1,h2,expected,source", [(110,108,108,"1"),(108,110,108,"0"),(110,110,110,"0")])
def test_a_bull_bear_reference_is_lower_high(h1,h2,expected,source):
    cs = [c(0,100,h1,95,105), c(1,105,h2,95,100)]
    event, = ReversalCandles().detect(cs,"1h",2000)
    assert (event.kind,event.price,event.known_at) == ("RESISTANCE",expected,2000)
    assert event.metadata["reference_candle_id"] == source
    assert event.source_ids == ("0","1")


@pytest.mark.parametrize("l1,l2,expected,source", [(90,92,92,"1"),(92,90,92,"0"),(90,90,90,"0")])
def test_a_bear_bull_reference_is_higher_low(l1,l2,expected,source):
    cs = [c(0,105,110,l1,100), c(1,100,110,l2,105)]
    event, = ReversalCandles().detect(cs,"1h",2000)
    assert (event.kind,event.price) == ("SUPPORT",expected)
    assert event.metadata["reference_candle_id"] == source


def test_a_doji_is_not_a_reversal():
    assert ReversalCandles().detect([c(0,close=100), c(1,105,110,95,100)],"1h",2000) == []


@pytest.mark.parametrize("kind,h,l", [("RESISTANCE",110,98),("SUPPORT",102,90)])
def test_b_extrema_and_confirmation(kind,h,l):
    cs = [c(0), c(1,100,h,l,101), c(2)]
    d = LocalExtrema(1)
    assert d.detect(cs,"1h",2999) == []
    event, = d.detect(cs,"1h",3000)
    assert event.kind == kind
    assert event.source_timestamp == 1000
    assert event.known_at == 3000
    assert event.source_ids == ("0","1","2")


def test_b_widths_independent_and_ties_excluded():
    cs = [c(0),c(1,100,110,97,101),c(2)]
    assert LocalExtrema(2).detect(cs,"1h",3000) == []
    assert LocalExtrema(1).detect([c(i) for i in range(5)],"1h",5000) == []


@pytest.mark.parametrize("kind,cs,price", [
    ("RESISTANCE",[c(0,100,110,99,108),c(1,108,109,100,105)],110),
    ("SUPPORT",[c(0,100,101,90,91),c(1,91,100,91,96)],90),
])
def test_c_later_close_confirmation(kind,cs,price):
    d = ConfirmedReversal(0.04)
    assert d.detect(cs,"1h",1999) == []
    events = d.detect(cs,"1h",2000)
    event, = [e for e in events if e.kind == kind]
    assert (event.price,event.source_timestamp,event.known_at) == (price,0,2000)


def test_c_new_extreme_cannot_confirm_on_same_candle():
    cs = [c(0),c(1,101,120,96,100)]
    assert ConfirmedReversal(0.05).detect(cs,"1h",2000) == []


@pytest.mark.parametrize("detector", [ReversalCandles(),LocalExtrema(1),LocalExtrema(2),ConfirmedReversal(0.04)])
def test_no_future_leakage_every_prefix(detector):
    cs = [c(0),c(1,101,110,99,108),c(2,108,109,95,96),c(3,96,104,94,103),
          c(4,103,105,92,95),c(5,95,109,93,108),c(6)]
    complete = detector.detect(cs,"1h",7000)
    for i in range(1,len(cs)+1):
        now = cs[i-1].end
        expected = [e for e in complete if e.known_at <= now]
        assert detector.detect(cs[:i],"1h",now) == expected
        assert detector.detect(cs,"1h",now) == expected


@pytest.mark.parametrize("detector", [ReversalCandles(),LocalExtrema(1),ConfirmedReversal(0.05)])
def test_detectors_reject_gaps(detector):
    with pytest.raises(ValueError):
        detector.detect([c(0),c(2)],"1h",3000)
