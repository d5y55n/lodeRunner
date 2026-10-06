"""Outcome-blind comparison of rejected monthly publications and selected daily sources."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from .phase3_archives import ROOT,trade_chunks,month_bounds
from .phase3_coverage import official_daily,classify_minute,merged_intervals,resolve_boundaries,MINUTE,POLICY
from .aggregate_trades import sha256,write_json
from app.research.models import identity


def scan(archives,issue_path):
    parts=[];previous=None;gaps=[];duplicate_rows=0;reversals=0;positive_jumps=0
    schema=pa.schema([(k,pa.int64() if k.endswith(("id","timestamp")) or k=="id_step" else pa.float64())
                      for k in ["before_id","before_timestamp","before_price","before_quantity","after_id","after_timestamp","after_price","after_quantity","id_step"]])
    writer=pq.ParquetWriter(issue_path,schema,compression="zstd")
    for frame in trade_chunks(archives):
        ids=frame.id.to_numpy();steps=np.diff(ids,prepend=previous["id"] if previous else ids[0]-1)
        bad=steps!=1
        reversals+=int((steps<0).sum());positive_jumps+=int((steps>1).sum())
        if bad.any():
            issue={"id_step":steps[bad]}
            for field in ("id","timestamp","price","quantity"):
                values=frame[field].to_numpy()
                issue["before_"+field]=np.r_[previous[field] if previous else values[0],values[:-1]][bad]
                issue["after_"+field]=values[bad]
            writer.write_table(pa.Table.from_pandas(pd.DataFrame(issue),schema=schema,preserve_index=False))
        duplicate_rows+=int((steps==0).sum())
        previous=frame.iloc[-1].to_dict()
        frame["minute"]=frame.timestamp//MINUTE*MINUTE
        parts.append(frame.groupby("minute",sort=True).agg(quantity=("quantity","sum"),count=("id","size"),
            first_time=("timestamp","min"),last_time=("timestamp","max"),low=("price","min"),high=("price","max")).reset_index())
    writer.close()
    if not reversals:
        for row in pd.read_parquet(issue_path).to_dict(orient="records"):
            if row["id_step"]>1:gaps.append({"before":{k:row["before_"+k] for k in ("id","timestamp","price","quantity")},
                                             "after":{k:row["after_"+k] for k in ("id","timestamp","price","quantity")},"id_step":row["id_step"]})
    table=pd.concat(parts).groupby("minute",sort=True).agg(quantity=("quantity","sum"),count=("count","sum"),
        first_time=("first_time","min"),last_time=("last_time","max"),low=("low","min"),high=("high","max")).reset_index()
    return table,gaps,duplicate_rows,{"raw_positive_jumps":positive_jumps,"raw_reversals":reversals,
                                    "issue_rows_file":issue_path.name,"issue_rows_sha256":sha256(issue_path)}


def audit(month):
    start,end=month_bounds(month)
    chosen=json.loads((ROOT/"integrity"/f"{month}-aggTrades.json").read_text())
    if chosen.get("source_kind")!="official_daily_collection":raise ValueError("No daily source replacement")
    out=ROOT/"coverage/publication";out.mkdir(parents=True,exist_ok=True)
    result_path=out/f"{month}-{POLICY['version']}.json"
    if result_path.exists():return json.loads(result_path.read_text())
    monthly=ROOT/"raw/aggTrades"/f"BTCUSDT-aggTrades-{month}.zip"
    if sha256(monthly)!=chosen["monthly_sha256"]:raise ValueError("Rejected monthly source changed")
    prior_path=out/f"{month}.json"
    prior=json.loads(prior_path.read_text()) if prior_path.exists() else None
    reusable=prior and prior["monthly_sha256"]==chosen["monthly_sha256"] and prior["daily_source_id"]==chosen["sha256"]
    if reusable:
        for filename,digest in prior["evidence_hashes"].items():
            if "comparison" in filename:continue
            if sha256(out/filename)!=digest:raise ValueError("Cached publication evidence modified")
        m=pd.read_parquet(out/f"{month}-monthly-minutes.parquet")
        gaps=prior["monthly_gaps"];duplicates=prior["monthly_duplicate_adjacent_rows"]
        ordering=prior.get("monthly_ordering",{"raw_reversals":0,"raw_positive_jumps":len(gaps)})
    else:m,gaps,duplicates,ordering=scan([monthly],out/f"{month}-monthly-order-issues.parquet")
    daily=[]
    for source in chosen["source_parts"]:
        path=ROOT/"raw/daily-audit"/source["url"].rsplit("/",1)[-1]
        if sha256(path)!=source["sha256"]:raise ValueError("Selected daily source changed")
        daily.append(path)
    if reusable:
        d=pd.read_parquet(out/f"{month}-daily-minutes.parquet");remaining=chosen["gaps"]
        duplicate_daily=prior["daily_duplicate_adjacent_rows"];daily_ordering=prior.get("daily_ordering",{})
    else:d,remaining,duplicate_daily,daily_ordering=scan(daily,out/f"{month}-daily-order-issues.parquet")
    m.to_parquet(out/f"{month}-monthly-minutes.parquet",index=False)
    d.to_parquet(out/f"{month}-daily-minutes.parquet",index=False)
    comparison=pd.DataFrame({"minute":np.arange(start,end,MINUTE)}).merge(m,on="minute",how="left").merge(d,on="minute",how="left",suffixes=("_monthly","_daily")).fillna({"quantity_monthly":0.,"quantity_daily":0.,"count_monthly":0.,"count_daily":0.})
    affected=comparison[(comparison.quantity_monthly-comparison.quantity_daily).abs()>1e-7].minute.astype("int64").tolist()
    if ordering["raw_reversals"]:affected.extend(range(start,end,MINUTE))
    for gap in gaps:
        affected.extend(range(max(start,(int(gap["before"]["timestamp"])//MINUTE-5)*MINUTE),
                              min(end,(int(gap["after"]["timestamp"])//MINUTE+6)*MINUTE),MINUTE))
    affected=sorted(set(t+d for t in affected for d in (-MINUTE,0,MINUTE) if start<=t+d<end));klines=[];sources=[]
    for day in sorted({pd.Timestamp(t,unit="ms",tz="UTC").strftime("%Y-%m-%d") for t in affected}):
        archive,source=official_daily(day,"klines",ROOT);sources.append(source)
        import zipfile
        with zipfile.ZipFile(archive) as z:
            with z.open(z.namelist()[0]) as stream:header=0 if stream.readline().startswith(b"open_time") else None
            with z.open(z.namelist()[0]) as stream:frame=pd.read_csv(stream,header=header)
        frame.columns=["minute","open","high","low","close","volume","end","quote","count","buy","buy_quote","ignore"]
        klines.append(frame)
    k=pd.concat(klines).set_index("minute") if klines else pd.DataFrame()
    selected=comparison[comparison.minute.isin(affected)].copy()
    decisions=[]
    for row in selected.to_dict(orient="records"):
        minute=int(row["minute"]);valid=minute in k.index
        volume=float(k.loc[minute,"volume"]) if valid else None
        verdict=classify_minute(float(row["quantity_daily"]),volume,True,valid)
        row.update(kline_quantity=volume,decision=verdict)
        decisions.append(row)
    flat=[dict(minute=int(r["minute"]),quantity=r["quantity_daily"],kline_quantity=r["kline_quantity"],
               first_time=r.get("first_time_daily"),last_time=r.get("last_time_daily"),decision=r["decision"]) for r in decisions]
    for row,resolved in zip(decisions,resolve_boundaries(flat)):
        row.update({k:v for k,v in resolved.items() if k in ("decision","raw_decision","boundary_pair_start","boundary_pair_residual")})
    evidence=pd.DataFrame(decisions);evidence.to_parquet(out/f"{month}-comparison-{POLICY['version']}.parquet",index=False)
    quarantines=merged_intervals(evidence.loc[evidence.decision=="QUARANTINE","minute"])
    findings=[]
    for gap in gaps:
        before,after=gap["before"],gap["after"]
        findings.append({**gap,"timestamp_gap_ms":int(after["timestamp"])-int(before["timestamp"]),
                         "price_change_fraction":float(after["price"])/float(before["price"])-1,
                         "same_gap_in_selected_daily":any(x["before"]["id"]==before["id"] and x["after"]["id"]==after["id"] for x in remaining)})
    result=dict(audit_schema=3,policy_id=identity(POLICY),month=month,decision="SELECT_VERIFIED_OFFICIAL_DAILY_PUBLICATION",outcomes_used=False,
        monthly_sha256=chosen["monthly_sha256"],daily_source_id=chosen["sha256"],monthly_gaps=findings,
        monthly_duplicate_adjacent_rows=duplicates,daily_duplicate_adjacent_rows=duplicate_daily,
        monthly_ordering=ordering,daily_ordering=daily_ordering,
        affected_minutes=len(affected),quarantine_intervals=quarantines,
        unresolved_minutes=int((evidence.decision=="UNRESOLVED").sum()),kline_sources=sources,
        monthly_rows=int(m["count"].sum()),daily_rows=int(d["count"].sum()),
        evidence_hashes={p.name:sha256(p) for p in sorted(out.glob(f"{month}-*.parquet"))})
    write_json(result_path,result);print("PUBLICATION_AUDIT",month,"inspected_minutes",result["affected_minutes"],
        "quarantined_minutes",sum((b-a)//MINUTE for a,b in quarantines),"unresolved",result["unresolved_minutes"],flush=True)
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--month",required=True)
    audit(parser.parse_args().month)
