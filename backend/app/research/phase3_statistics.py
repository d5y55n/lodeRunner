"""Counts and descriptive metrics with event identity retained, no naive inference."""
import numpy as np
import pandas as pd


def metrics(frame):
    if frame.empty:return {"measurement_count":0,"unique_event_count":0}
    n=len(frame)
    result={"measurement_count":n,"unique_event_count":int(frame.event_id.nunique()),
            "censored_rate":float(frame.censored.mean())}
    complete=frame.loc[~frame.censored]
    unique=frame.drop_duplicates(["event_id","direction","tp","sl","horizon"])
    unique_complete=unique.loc[~unique.censored]
    result["event_balanced_censored_rate"]=float(unique.censored.mean())
    result["complete_measurement_count"]=len(complete)
    for label in ("TP_FIRST","SL_FIRST","NEITHER","AMBIGUOUS"):
        result[label.lower()+"_rate"]=float((complete.label==label).mean()) if len(complete) else None
        result["event_balanced_"+label.lower()+"_rate"]=float((unique_complete.label==label).mean()) if len(unique_complete) else None
    for field in ("mfe_pct","mae_pct","time_to_mfe_ms","time_to_mae_ms"):
        values=complete[field].dropna()
        result[field+"_mean"]=float(values.mean()) if len(values) else None
        result[field+"_median"]=float(values.median()) if len(values) else None
        for q in (0.1,0.9):result[field+f"_q{int(q*100)}"]=float(values.quantile(q)) if len(values) else None
    resolved=complete.loc[complete.label.isin(["TP_FIRST","SL_FIRST"])]
    result["resolved_measurement_count"]=len(resolved)
    result["gross_boundary_expectancy_conditional_pct"]=(float(np.where(resolved.label=="TP_FIRST",resolved.tp,-resolved.sl).mean()*100) if len(resolved) else None)
    # This omits neither/ambiguous/censored and is NOT unconditional strategy profit.
    result["expectancy_definition"]="boundary_return_conditional_on_unambiguous_resolved_complete_horizon_no_costs"
    return result


def summary(frame,columns):
    records=[]
    for key,group in frame.groupby(columns,dropna=False,sort=True):
        if not isinstance(key,tuple):key=(key,)
        records.append({**dict(zip(columns,key)),**metrics(group)})
    return pd.DataFrame(records)
