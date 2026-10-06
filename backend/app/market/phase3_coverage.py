"""Outcome-blind coverage adjudication; raw trade volume is never repaired."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import zipfile
import httpx
import numpy as np
import pandas as pd
from .aggregate_trades import download_file,sha256,write_json
from .phase3_archives import ROOT,months,month_bounds
from app.research.models import identity
from app.research.phase3_plan import DEVELOPMENT_START,VALIDATION_END,permitted

MINUTE=60000
NAMES=["id","price","quantity","first","last","timestamp","maker"]
DTYPES=dict(id="int64",price="float64",quantity="float64",first="int64",last="int64",timestamp="int64",maker="str")
POLICY={"version":"coverage-v4","unit_ms":MINUTE,"padding_minutes":5,
        "absolute_quantity_tolerance":0.01,"relative_quantity_tolerance":0.01,
        "time_gap_warning_ms":5000,"price_jump_warning_fraction":0.01,
        "price_only_exclusion":False,"id_only_exclusion":False,
        "boundary_pair_max_gap_ms":5000,"boundary_pair_absolute_tolerance":0.01,
        "boundary_pair_relative_tolerance":0.01,"boundary_pair_volume_basis":"minimum_minute_kline_volume",
        "boundary_max_minutes":5,
        "repair":False,"research_propagation":"exclude_D_windows_mark_volume_missing_keep_verified_price_history"}


def freeze_policy(root):
    root.mkdir(parents=True,exist_ok=True)
    path=root/(POLICY["version"]+"-policy.json")
    payload={**POLICY,"policy_id":identity(POLICY)}
    if path.exists():
        saved=json.loads(path.read_text())
        if saved["policy"]!=payload:raise ValueError("Predeclared coverage policy changed")
        return saved
    saved={"declared_at":datetime.now(timezone.utc).isoformat(),"policy":payload,"outcomes_used":False}
    write_json(path,saved)
    return saved


def official_daily(day,kind,root):
    month_bounds(day[:7])
    suffix="aggTrades" if kind=="aggTrades" else "1m"
    filename=f"BTCUSDT-{suffix}-{day}.zip"
    route=f"aggTrades/BTCUSDT/{filename}" if kind=="aggTrades" else f"klines/BTCUSDT/1m/{filename}"
    url="https://data.binance.vision/data/futures/um/daily/"+route
    directory=root/"raw"/("daily-audit" if kind=="aggTrades" else "daily-kline-audit")
    directory.mkdir(parents=True,exist_ok=True)
    archive=directory/filename;checksum=directory/(filename+".CHECKSUM")
    with httpx.Client(timeout=120,follow_redirects=True) as client:
        download_file(client,url,archive);download_file(client,url+".CHECKSUM",checksum)
    parts=checksum.read_text().split();digest=sha256(archive)
    if len(parts)!=2 or parts[0].lower()!=digest or parts[1].lstrip("*")!=filename:
        raise ValueError("Official daily checksum mismatch")
    with zipfile.ZipFile(archive) as z:
        if len(z.namelist())!=1 or z.testzip() is not None:raise ValueError("Official daily CRC/members invalid")
    return archive,dict(url=url,sha256=digest,checksum_verified=True,crc_verified=True)


def window_bounds(gap):
    start=max(DEVELOPMENT_START,(int(gap["before"]["timestamp"])//MINUTE-5)*MINUTE)
    end=min(VALIDATION_END,(int(gap["after"]["timestamp"])//MINUTE+6)*MINUTE)
    permitted(start,end)
    return start,end


def read_windows(archive,windows):
    selected=[]
    with zipfile.ZipFile(archive) as z:
        member=z.namelist()[0]
        with z.open(member) as stream:header=0 if stream.readline().startswith(b"agg_trade_id") else None
        with z.open(member) as stream:
            for frame in pd.read_csv(stream,header=header,names=NAMES,dtype=DTYPES,chunksize=1000000):
                mask=np.zeros(len(frame),dtype=bool)
                for start,end in windows:mask|=(frame.timestamp.to_numpy()>=start)&(frame.timestamp.to_numpy()<end)
                if mask.any():selected.append(frame.loc[mask])
    return pd.concat(selected,ignore_index=True) if selected else pd.DataFrame(columns=NAMES).astype(DTYPES)


def minute_trades(frame):
    if frame.empty:return pd.DataFrame(columns=["minute","quantity","count","first_time","last_time","open","high","low","close","buy","sell"])
    frame=frame.assign(minute=frame.timestamp//MINUTE*MINUTE,
                       buy=frame.quantity.where(frame.maker.str.lower().eq("false"),0.),
                       sell=frame.quantity.where(frame.maker.str.lower().eq("true"),0.))
    return frame.groupby("minute",sort=True).agg(quantity=("quantity","sum"),count=("id","size"),
        first_time=("timestamp","first"),last_time=("timestamp","last"),open=("price","first"),
        high=("price","max"),low=("price","min"),close=("price","last"),buy=("buy","sum"),sell=("sell","sum")).reset_index()


def classify_minute(aggregate_quantity,kline_quantity,publications_agree,kline_valid=True):
    if not publications_agree or not kline_valid:return "UNRESOLVED"
    if not np.isfinite([aggregate_quantity,kline_quantity]).all() or min(aggregate_quantity,kline_quantity)<0:
        return "UNRESOLVED"
    tolerance=max(POLICY["absolute_quantity_tolerance"],POLICY["relative_quantity_tolerance"]*kline_quantity)
    if kline_quantity-aggregate_quantity>tolerance:return "QUARANTINE"
    if aggregate_quantity-kline_quantity>tolerance:return "UNRESOLVED"
    return "RETAIN_WARNING"


def merged_intervals(minutes):
    result=[]
    for start in sorted(set(int(m) for m in minutes)):
        if result and result[-1][1]==start:result[-1][1]=start+MINUTE
        else:result.append([start,start+MINUTE])
    return result


def resolve_boundaries(rows):
    """Shortest disjoint bounded conservation blocks; never moves trade quantities."""
    result=[dict(r,raw_decision=r["decision"]) for r in rows];i=0
    while i+1<len(result):
        consumed=0
        for size in range(2,min(POLICY["boundary_max_minutes"],len(result)-i)+1):
            block=result[i:i+size]
            if not all(r.get("source_agrees",True) for r in block):break
            values=[r.get(k) for r in block for k in ("quantity","kline_quantity","first_time","last_time")]
            if any(v is None or not np.isfinite(v) for v in values):break
            if not all(b["minute"]==a["minute"]+MINUTE and 0<=b["first_time"]-a["last_time"]<=POLICY["boundary_pair_max_gap_ms"] for a,b in zip(block,block[1:])):break
            deltas=[r["quantity"]-r["kline_quantity"] for r in block]
            tolerance=max(POLICY["boundary_pair_absolute_tolerance"],POLICY["boundary_pair_relative_tolerance"]*min(r["kline_quantity"] for r in block))
            if min(deltas)<0<max(deltas) and abs(sum(deltas))<=tolerance and any(r["decision"] in ("QUARANTINE","UNRESOLVED") for r in block):
                for r in block:r.update(decision="RETAIN_BOUNDARY_WARNING",boundary_pair_start=block[0]["minute"],
                    boundary_block_end=block[-1]["minute"]+MINUTE,boundary_pair_residual=sum(deltas))
                consumed=size;break
        i+=consumed or 1
    return result


def fingerprint(frame):
    normalized=frame[NAMES].copy();normalized["maker"]=normalized.maker.str.lower()
    return hashlib.sha256(pd.util.hash_pandas_object(normalized,index=False).to_numpy().tobytes()).hexdigest()


def reclassify_evidence(result):
    quarantines=[]
    for gap in result["decisions"]:
        rows=[r for r in result["minute_evidence"] if r["gap_id"]==gap["gap_id"]]
        flat=[]
        for row in rows:
            a=row["aggregate"];k=row["kline"]
            decision=classify_minute(a["quantity"],k.get("volume"),gap["daily_monthly_records_agree"],bool(k))
            flat.append(dict(minute=row["minute"],quantity=a["quantity"],kline_quantity=k.get("volume"),
                             first_time=a.get("first_time"),last_time=a.get("last_time"),decision=decision,
                             source_agrees=gap["daily_monthly_records_agree"]))
        for row,resolved in zip(rows,resolve_boundaries(flat)):
            row.update({k:v for k,v in resolved.items() if k in ("decision","raw_decision","boundary_pair_start","boundary_pair_residual")})
            if row["decision"]=="QUARANTINE":quarantines.append(row["minute"])
        labels=[r["decision"] for r in rows]
        gap["decision"]="UNRESOLVED" if "UNRESOLVED" in labels else "PARTIAL_MINUTE_QUARANTINE" if "QUARANTINE" in labels else "RETAIN_WARNING"
    result["quarantine_intervals"]=merged_intervals(quarantines)
    return result


def adjudicate(gaps,root,monthly_sources):
    windows=[window_bounds(g) for g in gaps]
    month_windows={};day_windows={}
    for start,end in windows:
        for t in range(start//86400000*86400000,end,86400000):
            day=pd.Timestamp(t,unit="ms",tz="UTC").strftime("%Y-%m-%d")
            day_windows.setdefault(day,[]).append((start,end))
            month_windows.setdefault(day[:7],[]).append((start,end))
    monthly=[];sources=[]
    for month,ranges in sorted(month_windows.items()):
        path=root/"raw/aggTrades"/f"BTCUSDT-aggTrades-{month}.zip"
        report=monthly_sources[month]
        digest=sha256(path)
        if digest!=report.get("monthly_sha256",report["sha256"]):raise ValueError("Monthly raw archive changed after verification")
        monthly.append(read_windows(path,ranges));sources.append({"month":month,"sha256":digest,"url":report["url"]})
    monthly=pd.concat(monthly,ignore_index=True)
    daily=[];klines=[]
    for day,ranges in sorted(day_windows.items()):
        archive,source=official_daily(day,"aggTrades",root);sources.append(source)
        daily.append(read_windows(archive,ranges))
        archive,source=official_daily(day,"klines",root);sources.append(source)
        with zipfile.ZipFile(archive) as z:
            with z.open(z.namelist()[0]) as stream:header=0 if stream.readline().startswith(b"open_time") else None
            with z.open(z.namelist()[0]) as stream:frame=pd.read_csv(stream,header=header)
        if len(frame.columns)!=12:raise ValueError("Unexpected official kline schema")
        frame.columns=["minute","open","high","low","close","volume","end","quote","count","buy","buy_quote","ignore"]
        klines.append(frame)
    daily=pd.concat(daily,ignore_index=True)
    klines=pd.concat(klines,ignore_index=True)
    decisions=[];evidence=[];quarantines=[]
    for gap,(start,end) in zip(gaps,windows):
        m=monthly[(monthly.timestamp>=start)&(monthly.timestamp<end)]
        d=daily[(daily.timestamp>=start)&(daily.timestamp<end)]
        same=fingerprint(m)==fingerprint(d) and len(m)==len(d)
        before=m[m.id==gap["before"]["id"]];after=m[m.id==gap["after"]["id"]]
        if len(before)!=1 or len(after)!=1:raise ValueError("Discontinuity boundary records unavailable")
        before=before.iloc[0].to_dict();after=after.iloc[0].to_dict()
        gid=identity([int(before["id"]),int(after["id"])])
        trades=minute_trades(m).set_index("minute");local=[];local_evidence=[];flat=[]
        for minute in range(start,end,MINUTE):
            k=klines[klines.minute==minute]
            valid=len(k)==1 and int(k.iloc[0]["end"])==minute+MINUTE-1
            krow=k.iloc[0].to_dict() if valid else {}
            a=trades.loc[minute].to_dict() if minute in trades.index else {"quantity":0.,"count":0.,"buy":0.,"sell":0.}
            volume=float(krow["volume"]) if valid else None
            decision=classify_minute(float(a["quantity"]),volume,same,valid)
            row={"gap_id":gid,"minute":minute,"aggregate":a,"kline":krow,"decision":decision,
                 "volume_deficit":volume-a["quantity"] if valid else None,
                 "relative_volume_deficit":(volume-a["quantity"])/volume if valid and volume else None,
                 "high_difference":a.get("high",0)-krow["high"] if valid and a["count"] else None,
                 "low_difference":a.get("low",0)-krow["low"] if valid and a["count"] else None}
            local_evidence.append(row)
            flat.append(dict(minute=minute,quantity=a["quantity"],kline_quantity=volume,
                             first_time=a.get("first_time"),last_time=a.get("last_time"),
                             source_agrees=same,decision=decision))
        for row,resolved in zip(local_evidence,resolve_boundaries(flat)):
            row.update({k:v for k,v in resolved.items() if k in ("decision","raw_decision","boundary_pair_start","boundary_pair_residual")})
            evidence.append(row);local.append(row["decision"])
            if row["decision"]=="QUARANTINE":quarantines.append(row["minute"])
        gap_ms=int(after["timestamp"])-int(before["timestamp"])
        jump=float(after["price"])/float(before["price"])-1
        decisions.append({"gap_id":gid,"before":before,"after":after,"id_step":int(after["id"])-int(before["id"]),
            "timestamp_gap_ms":gap_ms,"price_change_fraction":jump,"daily_monthly_records_agree":same,
            "time_gap_warning":gap_ms>POLICY["time_gap_warning_ms"],"price_warning":abs(jump)>POLICY["price_jump_warning_fraction"],
            "window_start":start,"window_end":end,"monthly_window_rows":len(m),"daily_window_rows":len(d),
            "monthly_window_fingerprint":fingerprint(m),"daily_window_fingerprint":fingerprint(d),
            "decision":"UNRESOLVED" if "UNRESOLVED" in local else "PARTIAL_MINUTE_QUARANTINE" if "QUARANTINE" in local else "RETAIN_WARNING"})
    return dict(decisions=decisions,minute_evidence=evidence,quarantine_intervals=merged_intervals(quarantines),sources=sources)


def run(root=ROOT,allow_incomplete=False):
    declaration=freeze_policy(root);reports={};missing=[];gaps=[];previous=None
    for month in months():
        path=root/"integrity"/f"{month}-aggTrades.json"
        if not path.exists():missing.append(month);previous=None;continue
        report=json.loads(path.read_text())
        if not report.get("passed"):missing.append(month);previous=None;continue
        if report.get("aggregate_discontinuities",0)!=len(report.get("gaps",[])):
            raise ValueError("Every discontinuity must have full boundary evidence")
        reports[month]=report;gaps.extend(report.get("gaps",[]))
        if previous:
            step=report["first_aggregate_id"]-previous["last_aggregate_id"]
            if step<=0 or report["first_timestamp"]<previous["last_timestamp"]:raise ValueError("Invalid month boundary ordering")
            if step>1:
                gaps.append({"before":{"id":previous["last_aggregate_id"],"timestamp":previous["last_timestamp"]},
                             "after":{"id":report["first_aggregate_id"],"timestamp":report["first_timestamp"]}})
        previous=report
    if missing and not allow_incomplete:raise ValueError("Incomplete acquisition: "+str(missing))
    forensic=root/"coverage";forensic.mkdir(exist_ok=True)
    # Cache separately by gap plus source hashes, so every decision is auditable.
    results=[]
    for gap in gaps:
        gid=identity([int(gap["before"]["id"]),int(gap["after"]["id"])])
        start,end=window_bounds(gap)
        needed=sorted({pd.Timestamp(t,unit="ms",tz="UTC").strftime("%Y-%m") for t in range(start,end,MINUTE)})
        if any(m not in reports for m in needed):raise ValueError("Adjacent monthly source not yet available")
        source_ids={m:reports[m]["sha256"] for m in needed}
        path=forensic/(gid+"-"+POLICY["version"]+".json")
        if path.exists():
            result=json.loads(path.read_text())
            if result["policy_id"]!=identity(POLICY) or result["monthly_source_hashes"]!=source_ids:
                raise ValueError("Forensic evidence changed; explicit revision required")
        else:
            previous_path=forensic/(gid+".json")
            if previous_path.exists():
                result=json.loads(previous_path.read_text())
                if result["monthly_source_hashes"]!=source_ids:raise ValueError("Cached forensic source changed")
                result=reclassify_evidence(result)
                result["supersedes_evidence_sha256"]=sha256(previous_path)
            else:result=adjudicate([gap],root,reports)
            result.update(policy_id=identity(POLICY),monthly_source_hashes=source_ids,
                          recorded_at=datetime.now(timezone.utc).isoformat(),outcomes_used=False)
            write_json(path,result)
        results.append(result)
        print("COVERAGE",result["decisions"][0]["decision"],gap["after"]["timestamp"],flush=True)
    publications=[]
    from .phase3_publication_audit import audit
    for month,report in reports.items():
        if report.get("source_kind")=="official_daily_collection":publications.append(audit(month))
    quarantines=merged_intervals([m for r in results+publications for a,b in r["quarantine_intervals"] for m in range(a,b,MINUTE)])
    unresolved=[d for r in results for d in r["decisions"] if d["decision"]=="UNRESOLVED"]
    payload=dict(policy=declaration,source_hashes={m:r["sha256"] for m,r in reports.items()},
        source_profile_hashes={m:r["profile_sha256"] for m,r in reports.items()},
        missing_months=missing,decisions=[d for r in results for d in r["decisions"]],
        quarantine_intervals=quarantines,publication_decisions=publications,outcomes_used=False,
        ready=not missing and not unresolved and not any(r["unresolved_minutes"] for r in publications),
        publication_hashes={str(p.relative_to(forensic)):sha256(p) for p in sorted((forensic/"publication").glob("*")) if p.is_file()},
        forensic_hashes={p.name:sha256(p) for p in sorted(forensic.glob("*.json"))})
    payload["coverage_id"]=identity(payload)
    write_json(root/"coverage-manifest.json",payload)
    print(json.dumps({k:payload[k] for k in ("coverage_id","ready","missing_months")}|{
        "quarantined_minutes":sum((b-a)//MINUTE for a,b in quarantines),"unresolved_gaps":len(unresolved)}),flush=True)
    return payload


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--allow-incomplete",action="store_true")
    run(allow_incomplete=parser.parse_args().allow_incomplete)
