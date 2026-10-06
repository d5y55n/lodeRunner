import pandas as pd
import pytest
from app.market.phase3_archives import month_bounds,validate_trade_chunk
from app.research.phase3_plan import permitted,utc,manifest
from app.research.phase3_context import Quantiles,matched_control


def test_all_2024_reserved():
    with pytest.raises(ValueError):month_bounds("2024-01")
    with pytest.raises(ValueError):permitted(utc("2023-12-01"),utc("2024-01-02"))
    assert manifest()["final_test_start"]==utc("2024-01-01")


def test_chunk_boundary_gaps_and_duplicates_not_repaired():
    frame=pd.DataFrame([["3","100","1","3","3","30","false"]])
    with pytest.raises(ValueError,match="sequence"):
        validate_trade_chunk(frame,0,100,(1,20,1))


def test_valid_chunk_preserves_constituent_warning():
    frame=pd.DataFrame([["2","100","1","4","4","30","false"]])
    _,stats,last=validate_trade_chunk(frame,0,100,(1,20,1))
    assert stats["constituent_discontinuities"]==1 and last==(2,30,4)


def test_matcher_rejects_future_fitted_thresholds():
    model=Quantiles("volatility",(.1,.2,.3),100,20)
    with pytest.raises(ValueError,match="not available"):
        matched_control({"timestamp":50},[],model,model,10)
