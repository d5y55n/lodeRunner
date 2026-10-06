import duckdb
import numpy as np
import pandas as pd
import pytest
from app.research.phase3_disk_summary import weighted_metrics,weighted_quantile,measurement_expression
from app.research.phase3_statistics import metrics
from app.research.phase3_identity import measurement_id
from app.research.phase3_fast import CandleArrays
from app.research.models import Candle,Candidate,Zone


def test_weighted_metrics_exact_expanded_equivalence():
    rows=[]
    for i,label in enumerate(["TP_FIRST","SL_FIRST","NEITHER","AMBIGUOUS",None]):
        rows.append(dict(event_id=str(i),direction="LONG",horizon=4,tp=.003,sl=.005,label=label,
                         censored=label is None,mfe_pct=i/10,mae_pct=i/20,
                         time_to_mfe_ms=i*100 if i else None,time_to_mae_ms=i*200,weight=i+1))
    frame=pd.DataFrame(rows)
    expanded=frame.loc[frame.index.repeat(frame.weight)]
    expected=metrics(expanded);actual=weighted_metrics(frame)
    for field,value in expected.items():
        if isinstance(value,(int,float)):assert actual[field]==pytest.approx(value)
        else:assert actual[field]==value


@pytest.mark.parametrize("q",[.1,.5,.9])
def test_weighted_quantiles_equal_expanded(q):
    values=np.array([3.,1.,9.,2.]);weights=np.array([7,1,3,5])
    assert weighted_quantile(values,weights,q)==pytest.approx(np.quantile(np.repeat(values,weights),q))


def test_sql_measurement_id_matches_reference():
    con=duckdb.connect()
    con.execute("CREATE TABLE i(event_id VARCHAR,interaction_id VARCHAR,configuration_id VARCHAR)")
    con.execute("INSERT INTO i VALUES ('event','visit','config')")
    con.execute("CREATE TABLE o(direction VARCHAR,tp DOUBLE,sl DOUBLE,horizon BIGINT)")
    con.execute("INSERT INTO o VALUES ('LONG',0.003,0.005,24)")
    result=con.execute("SELECT "+measurement_expression()+" FROM i CROSS JOIN o").fetchone()[0]
    assert result==measurement_id("event","visit","config","LONG",.003,.005,24)
    con.close()


@pytest.mark.parametrize("seed",range(16))
def test_vectorized_visits_preserve_reference(seed):
    rng=np.random.default_rng(seed);cs=[]
    for i in range(100):
        op,close=rng.uniform(95,105,2)
        cs.append(Candle(str(i),i*100,(i+1)*100,op,max(op,close)+1,min(op,close)-1,close))
    candidate=Candidate("A","SUPPORT",100,0,700,"1h",())
    zone=Zone(candidate,99,101,"fixed_percentage",.01)
    arrays=CandleArrays(cs)
    reference=arrays.visits(zone)
    fast=list(arrays.visit_indices(zone))
    assert [(cs[i].start,cs[j].end if ended else None,j-i+1) for i,j,ended in fast]==[(v.start,v.end,v.candles_spent) for v in reference]
