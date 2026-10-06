from dataclasses import asdict
import math
import pytest
from app.research.models import Candle,Candidate
from app.research.zones import construct
from app.research.interactions import track,ExitRule
from app.research.phase3_fast import CandleArrays


@pytest.mark.parametrize("width",[.0005,.002,.01,.05])
@pytest.mark.parametrize("rule",[ExitRule(),ExitRule("confirmed",.01)])
@pytest.mark.parametrize("known",[1000,8000])
def test_fast_visits_match_reference(width,rule,known):
    cs=[]
    for i in range(100):
        op=100+3*math.sin(i*.7);close=100+3*math.sin((i+1)*.7)
        cs.append(Candle(str(i),i*1000,(i+1)*1000,op,max(op,close)+.7,min(op,close)-.9,close))
    z=construct(Candidate("A","SUPPORT",100,0,known,"1h",("0",)),"fixed_percentage",width)
    assert [asdict(v) for v in CandleArrays(cs).visits(z,rule)]==[asdict(v) for v in track(z,cs,rule)]
