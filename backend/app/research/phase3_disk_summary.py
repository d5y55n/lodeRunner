"""Exact multiplicity-weighted summaries without expanding shared outcomes."""
import json
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from app.market.aggregate_trades import write_json
from .phase3_storage import connect,literal
from .phase3_context import ControlIndex
from .phase3_statistics import summary


def weighted_quantile(values,weights,q):
    order=np.argsort(values,kind="stable");v=np.asarray(values)[order];w=np.asarray(weights,dtype=np.int64)[order]
    rank=q*(int(w.sum())-1);cumulative=np.cumsum(w)
    low=int(np.searchsorted(cumulative,int(np.floor(rank)),side="right"))
    high=int(np.searchsorted(cumulative,int(np.ceil(rank)),side="right"))
    return float(v[low]+(v[high]-v[low])*(rank-np.floor(rank)))


def weighted_metrics(frame):
    weights=frame.weight.to_numpy(dtype=np.int64)
    n=int(weights.sum());complete=frame.loc[~frame.censored];cw=complete.weight.to_numpy(dtype=np.int64)
    unique=frame.drop_duplicates("event_id");uc=unique.loc[~unique.censored]
    result=dict(measurement_count=n,unique_event_count=int(frame.event_id.nunique()),
                censored_rate=float(weights[frame.censored.to_numpy()].sum()/n),
                event_balanced_censored_rate=float(unique.censored.mean()),complete_measurement_count=int(cw.sum()))
    for label in ("TP_FIRST","SL_FIRST","NEITHER","AMBIGUOUS"):
        result[label.lower()+"_rate"]=float(cw[(complete.label==label).to_numpy()].sum()/cw.sum()) if len(cw) else None
        result["event_balanced_"+label.lower()+"_rate"]=float((uc.label==label).mean()) if len(uc) else None
    for field in ("mfe_pct","mae_pct","time_to_mfe_ms","time_to_mae_ms"):
        valid=complete[field].notna();v=complete.loc[valid,field].to_numpy();w=cw[valid.to_numpy()]
        result[field+"_mean"]=float(np.average(v,weights=w)) if len(v) else None
        for suffix,q in (("median",.5),("q10",.1),("q90",.9)):
            result[field+"_"+suffix]=weighted_quantile(v,w,q) if len(v) else None
    resolved=complete.loc[complete.label.isin(["TP_FIRST","SL_FIRST"])]
    result["resolved_measurement_count"]=int(resolved.weight.sum())
    result["gross_boundary_expectancy_conditional_pct"]=(float(np.average(np.where(resolved.label=="TP_FIRST",resolved.tp,-resolved.sl),weights=resolved.weight)*100) if len(resolved) else None)
    result["expectancy_definition"]="boundary_return_conditional_on_unambiguous_resolved_complete_horizon_no_costs"
    return result


def bucket_sql(model):
    cases=" ".join(f"WHEN {model.field} < {repr(cut)} THEN 'Q{i+1}'" for i,cut in enumerate(model.cuts))
    return f"CASE WHEN {model.field} IS NULL OR NOT isfinite({model.field}) THEN 'MISSING' {cases} ELSE 'Q{len(model.cuts)+1}' END AS {model.field}_bucket"


def measurement_expression():
    fields=["'\"outcome-v1\"'","to_json(i.event_id)::VARCHAR","to_json(i.interaction_id)::VARCHAR",
            "to_json(i.configuration_id)::VARCHAR","to_json(o.direction)::VARCHAR",
            "o.tp::VARCHAR","o.sl::VARCHAR","o.horizon::VARCHAR"]
    return "sha256('[' || "+" || ',' || ".join(fields)+" || ']')"


def summarize_disk(dest,volume_models,context_models):
    con=connect(dest)
    for name,file in (("interactions","interactions.parquet"),("features","decision_features.parquet")):
        con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet({literal(dest/file)})")
    buckets=",".join(bucket_sql(m) for m in volume_models)
    enriched=dest/"enriched-partitions"
    con.execute(f"COPY (SELECT i.configuration_id,i.event_id,i.visit_group,{buckets} FROM interactions i JOIN features f USING(interaction_id)) TO {literal(enriched)} (FORMAT PARQUET,PARTITION_BY(configuration_id),OVERWRITE_OR_IGNORE true,COMPRESSION ZSTD)")
    con.execute(f"CREATE VIEW base AS SELECT * FROM read_parquet({literal(enriched/'**/*.parquet')},hive_partitioning=true)")
    outcomes=pd.read_parquet(dest/"future_outcomes.parquet");events=pd.read_parquet(dest/"events.parquet")
    configurations=json.loads((dest/"configuration-manifest.json").read_text())["configurations"]
    tables=[];dimensions=[None,"visit_group"]+[m.field+"_bucket" for m in volume_models]
    for cfg in configurations:
        print("SUMMARIZE",cfg["detector"],cfg["width_parameter"],cfg["configuration_id"][:10],flush=True)
        for dimension in dimensions:
            extra=", "+dimension if dimension else ""
            weights=con.execute(f"SELECT event_id {extra}, count(*)::BIGINT weight FROM base WHERE configuration_id=? GROUP BY event_id {extra}",[cfg["configuration_id"]]).df()
            if weights.empty:continue
            for outcome_key,labels in outcomes.groupby(["direction","tp","sl","horizon"],sort=True):
                merged=weights.merge(labels,on="event_id",validate="many_to_one")
                groups=merged.groupby(dimension,sort=True) if dimension else [(None,merged)]
                for bucket,group in groups:
                    record={"configuration_id":cfg["configuration_id"],"detector":cfg["detector"],
                            "width_model":cfg["width_model"],"width_parameter":cfg["width_parameter"],
                            **dict(zip(["direction","tp","sl","horizon"],outcome_key)),
                            "table":dimension or "sr_only",**weighted_metrics(group)}
                    if dimension:record[dimension]=bucket
                    tables.append(record)
        pd.DataFrame(tables).to_csv(dest/"research_summary.csv",index=False)
    table=pd.DataFrame(tables)
    scheduled=events[events.schedule].merge(outcomes,on="event_id")
    summary(scheduled,["direction","tp","sl","horizon"]).to_csv(dest/"schedule_baseline.csv",index=False)
    pool=events.loc[events.volatility.notna()].to_dict(orient="records");index=ControlIndex(pool,*context_models)
    matches=[]
    for target in pool:
        if target["timestamp"]<max(m.development_end for m in context_models):continue
        for h in sorted(outcomes.horizon.unique()):
            control=index.match(target,int(h)*3600000)
            if control:matches.append({"target_event_id":target["event_id"],"control_event_id":control["event_id"],"horizon":int(h)})
    matching=pd.DataFrame(matches,columns=["target_event_id","control_event_id","horizon"])
    matching.to_parquet(dest/"matched_control_links.parquet",index=False)
    controls=matching.merge(outcomes,left_on=["control_event_id","horizon"],right_on=["event_id","horizon"])
    comparisons=[];paired_targets=[]
    for cfg in configurations:
        targets=con.execute("SELECT DISTINCT event_id FROM interactions WHERE configuration_id=?",[cfg["configuration_id"]]).df()
        paired=targets.merge(controls,left_on="event_id",right_on="target_event_id",suffixes=("_target",""))
        if paired.empty:continue
        result=summary(paired,["direction","tp","sl","horizon"]);result["configuration_id"]=cfg["configuration_id"]
        counts=paired.groupby(["direction","tp","sl","horizon"]).target_event_id.nunique().rename("matched_target_count").reset_index()
        result=result.merge(counts,on=["direction","tp","sl","horizon"]);result["eligible_target_count"]=len(targets)
        comparisons.append(result)
        links=targets.merge(matching,left_on="event_id",right_on="target_event_id")
        target_table=summary(links.merge(outcomes,on=["event_id","horizon"]),["direction","tp","sl","horizon"])
        target_table["configuration_id"]=cfg["configuration_id"];paired_targets.append(target_table)
    pd.concat(comparisons,ignore_index=True).to_csv(dest/"matched_baseline.csv",index=False)
    pd.concat(paired_targets,ignore_index=True).to_csv(dest/"matched_targets.csv",index=False)
    con.execute("SELECT detector, count(*) interaction_count, count(DISTINCT event_id) unique_events FROM interactions GROUP BY detector").df().to_csv(dest/"detector_counts.csv",index=False)
    con.execute("SELECT detector,status,count(*) interactions FROM interactions JOIN features USING(interaction_id) GROUP BY detector,status").df().to_csv(dest/"volume_attachment_counts.csv",index=False)
    con.close()
    database=duckdb.connect(str(dest/"research.duckdb"))
    for name,file in (("interactions","interactions.parquet"),("outcomes","future_outcomes.parquet"),("features","decision_features.parquet")):
        database.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_parquet({literal((dest/file).resolve())})")
    database.execute(f"CREATE OR REPLACE VIEW measurements AS SELECT {measurement_expression()} AS measurement_id,i.*,o.* EXCLUDE(event_id) FROM interactions i JOIN outcomes o USING(event_id)")
    database.close()
    write_json(dest/"measurement-contract.json",{"storage":"lossless_normalized_parquet_with_DuckDB_measurements_view",
        "measurement_identity":"sha256 canonical JSON [outcome-v1,event_id,interaction_id,configuration_id,direction,tp,sl,horizon]",
        "reason":"Avoid physically duplicating the same market outcome for every overlapping zone; multiplicities remain exact",
        "rows":int(table.loc[table.table=="sr_only","measurement_count"].sum()),"independent_samples":False})
    return table
