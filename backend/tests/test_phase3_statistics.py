import pandas as pd
from app.research.phase3_statistics import metrics


def test_duplicate_rows_increase_measurements_not_unique_events():
    base=dict(event_id="same",direction="LONG",horizon=4,censored=False,label="TP_FIRST",tp=.01,sl=.01,mfe_pct=1.,mae_pct=.1,time_to_mfe_ms=10,time_to_mae_ms=5)
    result=metrics(pd.DataFrame([base,base]))
    assert result["measurement_count"]==2 and result["unique_event_count"]==1
    assert result["gross_boundary_expectancy_conditional_pct"]==1.


def test_censored_neither_not_assumed_losses_or_wins():
    base=dict(event_id="one",direction="LONG",horizon=4,censored=False,label="NEITHER",tp=.01,sl=.01,mfe_pct=.5,mae_pct=.1,time_to_mfe_ms=10,time_to_mae_ms=5)
    result=metrics(pd.DataFrame([base,dict(base,event_id="two",censored=True,label=None)]))
    assert result["censored_rate"]==.5 and result["neither_rate"]==1.
    assert result["gross_boundary_expectancy_conditional_pct"] is None
