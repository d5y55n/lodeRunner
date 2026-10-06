import pytest
from app.research.models import Candidate, Candle
from app.research.zones import construct, ORIGINAL_WIDTHS, FIXED_WIDTHS
from app.research.interactions import track, ExitRule


def zone(kind="SUPPORT",known=1000,timeframe="1h"):
    return construct(Candidate("A",kind,100,0,known,timeframe,("0",)),"fixed_percentage",0.01)


def c(i,o,h,l,close):
    return Candle(str(i),i*1000,(i+1)*1000,o,h,l,close)


@pytest.mark.parametrize("fraction",FIXED_WIDTHS)
def test_fixed_zone_width(fraction):
    z = construct(zone().candidate,"fixed_percentage",fraction)
    assert z.lower == 100*(1-fraction)
    assert z.upper == 100*(1+fraction)
    assert z.width_parameter == fraction


@pytest.mark.parametrize("tf,fraction",ORIGINAL_WIDTHS.items())
def test_original_timeframe_configuration(tf,fraction):
    z = construct(zone(timeframe=tf).candidate,"original_timeframe")
    assert z.width_parameter == fraction
    assert z.lower == 100*(1-fraction)


def test_adaptive_only_receives_past():
    class TestWidth:
        name = "test_only"
        def fraction(self,candidate,history):
            assert all(c.end <= candidate.known_at for c in history)
            assert len(history) == 1
            return 0.01
    cs = [c(0,103,105,102,104),c(1,104,105,100,102)]
    assert construct(zone().candidate,"adaptive",adaptive=TestWidth(),candles=cs).width_model == "adaptive:test_only"


def test_no_interaction_before_known_at_even_confirmation_candle():
    cs = [c(i,100,102,98,100) for i in range(3)]
    visits = track(zone(known=2000),cs)
    assert len(visits) == 1 and visits[0].start == 2000


def test_wick_only_entry_and_exit():
    cs = [c(0,104,105,103,104),c(1,104,105,100,103)]
    v, = track(zone(),cs)
    assert v.wick_touched and not v.close_entered
    assert v.approach == "ABOVE" and v.exit_direction == "ABOVE"
    assert (v.start,v.observed_at,v.end) == (1000,2000,2000)
    assert v.max_penetration_price == 1


def test_continuous_close_inside_visit_not_double_counted_and_reentry():
    cs = [c(0,104,105,103,104),c(1,104,105,100,100),c(2,100,101,99,100),
          c(3,100,104,100,103),c(4,103,104,100,100)]
    a,b = track(zone(),cs)
    assert a.close_entered and a.candles_spent == 3
    assert a.transitions == [("OUTSIDE",1000),("ENTERED",2000),("INTERACTING",3000),("EXITED",4000)]
    assert a.number == 1 and b.number == 2
    assert b.state == "ENTERED" and b.end is None


@pytest.mark.parametrize("kind,cs,approach,exit_side",[
    ("SUPPORT",[c(0,104,105,103,104),c(1,104,104,97,98)],"ABOVE","BELOW"),
    ("RESISTANCE",[c(0,96,98,95,97),c(1,97,104,97,103)],"BELOW","ABOVE"),
])
def test_cross_through_direction(kind,cs,approach,exit_side):
    v, = track(zone(kind),cs)
    assert (v.approach,v.exit_direction,v.crossed_through) == (approach,exit_side,True)
    assert v.max_penetration_zone_fraction > 1


def test_confirmed_exit_delays_exit_until_separation():
    cs = [c(0,104,105,103,104),c(1,104,105,100,100),c(2,100,102,100,102),
          c(3,102,104,101,104)]
    assert track(zone(),cs)[0].end == 3000
    v, = track(zone(),cs,ExitRule("confirmed",0.02))
    assert v.end == 4000 and v.candles_spent == 3


def test_inside_approach_does_not_invent_direction():
    v, = track(zone(known=1000),[c(1,100,101,99,100)])
    assert v.approach == "INSIDE"
    assert v.crossed_through is None and v.max_penetration_price is None
