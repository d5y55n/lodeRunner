"""Development generation followed by a single, frozen validation evaluation."""
import argparse
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
import numpy as np
import pandas as pd
from app.market.aggregate_trades import write_json,sha256
from app.market.models import Candle as MarketCandle
from .models import identity,canonical
from .data import from_market
from .detectors import make_detector
from .zones import construct
from .outcomes import measure
from .phase3_plan import manifest,DEVELOPMENT_START,DEVELOPMENT_END,VALIDATION_END,utc,permitted
from .phase3_identity import event_id,interaction_id,measurement_id
from .phase3_context import contexts,Quantiles,frozen_subset,ControlIndex,verify_freeze
from .phase3_fast import CandleArrays
from .phase3_profiles import Profiles
from .phase3_statistics import summary
from .phase3_storage import Sink,INTERACTIONS,LIFECYCLES,FEATURES,connect,literal

ROOT=Path(__file__).resolve().parents[3]/"data/phase3"


def configurations(plan):
    result=[]
    detectors=[("A",{}),*[("B",{"width":w}) for w in plan["B_widths"]],
               *[("C",{"reversal_fraction":r}) for r in plan["C_reversals"]],
               *[("D",{"bin_size":b,"concentration_multiple":plan["D_concentration"]}) for b in plan["D_bin_widths"]]]
    for name,parameters in detectors:
        widths=[("fixed_percentage",w) for w in plan["fixed_half_widths"]]+[("original_timeframe",plan["original_half_width"])]
        for model,width in widths:
            cfg={"detector":name,"parameters":parameters,"width_model":model,"width_parameter":width,
                 "exit_rule":"boundary","timeframe":plan["timeframe"]}
            result.append({**cfg,"configuration_id":identity(cfg)})
    return result


def require_catalog(root,start,end):
    permitted(start,end)
    coverage=load_coverage(root)
    months=pd.date_range(pd.Timestamp(start,unit="ms",tz="UTC"),pd.Timestamp(end-1,unit="ms",tz="UTC"),freq="MS").strftime("%Y-%m")
    missing=[];catalog=[];previous=None
    for month in months:
        for kind in ("klines","aggTrades"):
            path=root/"integrity"/f"{month}-{kind}.json"
            if not path.exists():missing.append(str(path));continue
            report=json.loads(path.read_text())
            if not report.get("passed"):missing.append(str(path));continue
            if kind=="aggTrades":
                if previous and (report["first_aggregate_id"]<=previous["last_aggregate_id"] or report["first_timestamp"]<previous["last_timestamp"]):
                    raise ValueError("Cross-month aggregate-ID/time ordering violation")
                previous=report
                if coverage["source_hashes"].get(month)!=report["sha256"]:raise ValueError("Source differs from adjudicated coverage")
                if sha256(root/report["profile"])!=report["profile_sha256"]:raise ValueError("Profile checksum changed")
                if coverage["source_profile_hashes"].get(month)!=report["profile_sha256"]:raise ValueError("Profile differs from adjudicated coverage")
            else:
                if sha256(root/"candles"/f"{month}.parquet")!=report["normalized_sha256"]:raise ValueError("Candle checksum changed")
            catalog.append(report)
    if missing:
        write_json(root/"missing-files.json",{"missing_or_invalid":missing})
        raise ValueError(f"Research blocked by {len(missing)} missing/invalid source files")
    return months,catalog


def load_coverage(root):
    path=root/"coverage-manifest.json"
    if not path.exists():raise ValueError("Outcome-blind coverage adjudication is required before research")
    coverage=json.loads(path.read_text())
    if not coverage.get("ready") or coverage.get("coverage_id")!=identity({k:v for k,v in coverage.items() if k!="coverage_id"}):
        raise ValueError("Coverage manifest incomplete or modified")
    for name,digest in coverage["forensic_hashes"].items():
        if sha256(root/"coverage"/name)!=digest:raise ValueError("Forensic decision changed")
    for name,digest in coverage.get("publication_hashes",{}).items():
        if sha256(root/"coverage"/name)!=digest:raise ValueError("Publication audit changed")
    return coverage


def generate(root,phase,configs,plan,output_name=None):
    if phase not in ("development","validation"):raise ValueError("Unknown research phase")
    start,end=(DEVELOPMENT_START,DEVELOPMENT_END) if phase=="development" else (DEVELOPMENT_END,VALIDATION_END)
    months,catalog=require_catalog(root,start,end)
    dest=root/(output_name or phase);dest.mkdir(parents=True,exist_ok=True)
    market=pd.concat([pd.read_parquet(root/"candles"/f"{m}.parquet") for m in months],ignore_index=True)
    market=market[(market.open_time>=start)&(market.close_time<end)]
    cs=from_market([MarketCandle(**r) for r in market.drop(columns="ignore").to_dict(orient="records")],"BTCUSDT","1h")
    coverage=load_coverage(root)
    arrays=CandleArrays(cs);profiles=Profiles(root/"profiles",coverage["quarantine_intervals"])
    context=contexts(cs,plan["context_lookback"])
    context_by_time={c["timestamp"]:c for c in context}
    events=[];labels=[]
    event_ids=[event_id("BTCUSDT","1h",c.end) for c in cs]
    for i,c in enumerate(cs):
        if c.end>=end:continue
        eid=event_ids[i]
        events.append({"event_id":eid,"timestamp":c.end,"reference_close":c.close,"phase":phase,
                       "schedule":i%plan["schedule_stride"]==0,**{k:v for k,v in context_by_time.get(c.end,{}).items() if k!="timestamp"}})
        for direction,tp,sl,h in product(("LONG","SHORT"),plan["tp"],plan["sl"],plan["horizons"]):
            outcome=asdict(measure(c.close,c.end,cs[i+1:i+1+h],direction,tp,sl,h))
            labels.append({"event_id":eid,"outcome_id":identity([eid,direction,tp,sl,h]),**outcome})
    pd.DataFrame(events).to_parquet(dest/"events.parquet",index=False)
    pd.DataFrame(labels).to_parquet(dest/"future_outcomes.parquet",index=False)
    del labels,events,market
    candidate_cache={};candidates=[];unique_events=set()
    interactions=Sink(dest/"interactions.parquet",INTERACTIONS)
    lifecycles=Sink(dest/"future_interaction_lifecycles.parquet",LIFECYCLES)
    for cfg in configs:
        before_count=interactions.count
        key=canonical([cfg["detector"],cfg["parameters"]])
        if key not in candidate_cache:
            params=cfg["parameters"]
            found=(profiles.d_candidates(start,end,params["bin_size"],params["concentration_multiple"]) if cfg["detector"]=="D"
                   else make_detector(cfg["detector"],params).detect(cs,"1h",end))
            candidate_cache[key]=found
            candidates.extend({"candidate_id":c.id,**asdict(c),"metadata":canonical(c.metadata),"source_ids":canonical(c.source_ids)} for c in found)
        print(f"GENERATE {phase} {cfg['detector']} {cfg['width_model']} {cfg['width_parameter']}",flush=True)
        for candidate in candidate_cache[key]:
            z=construct(candidate,cfg["width_model"],cfg["width_parameter"])
            cid=candidate.id;zid=z.id
            for number,(i,j,ended) in enumerate(arrays.visit_indices(z),1):
                observed_at=int(arrays.end[i]);visit_start=int(arrays.start[i]);visit_end=int(arrays.end[j]) if ended else None
                if observed_at>=end:continue
                iid=interaction_id(cid,cfg["configuration_id"],visit_start,number)
                eid=event_ids[i];unique_events.add(eid)
                lifecycles.add({"interaction_id":iid,"end":visit_end,"candles_spent":j-i+1,
                                   "available_at":visit_end,"censored":not ended})
                interactions.add({"interaction_id":iid,"event_id":eid,
                   "candidate_id":cid,"configuration_id":cfg["configuration_id"],"zone_id":zid,
                   "detector":candidate.detector,"kind":candidate.kind,"width_model":cfg["width_model"],"width_parameter":cfg["width_parameter"],
                   "start":visit_start,"observed_at":observed_at,"visit_number":number,
                   "visit_group":str(number) if number<4 else "4+","reference_close":float(arrays.close[i]),
                   "known_at":candidate.known_at,"zone_lower":z.lower,"zone_upper":z.upper,
                   "concentration":candidate.metadata.get("observed_ratio")})
        print("INTERACTIONS",cfg["configuration_id"][:10],interactions.count-before_count,flush=True)
    pd.DataFrame(candidates).to_parquet(dest/"candidates.parquet",index=False)
    interactions.close();lifecycles.close()
    del profiles,candidate_cache
    from .phase3_feature_batch import build_features
    if build_features(dest,root,start,coverage["quarantine_intervals"])!=interactions.count:
        raise ValueError("Feature row count differs from interactions")
    write_json(dest/"configuration-manifest.json",{"plan":plan,"coverage_id":coverage["coverage_id"],"actual_start":start,"actual_end":end,"configurations":configs,"source_catalog":catalog,
               "event_definition":"symbol_timeframe_decision_close","raw_candidate_count":len(candidates),
               "interaction_rows":interactions.count,"unique_events":len(unique_events),
               "artifact_hashes":{p.name:sha256(p) for p in sorted(dest.glob("*.parquet"))}})
    return dest


def fit_buckets(dest):
    con=connect(dest)
    con.execute("CREATE VIEW features AS SELECT * FROM read_parquet("+literal(dest/"decision_features.parquet")+")")
    if con.execute("SELECT count(*) FROM features WHERE timestamp>=?",[DEVELOPMENT_END]).fetchone()[0]:
        raise ValueError("Bucket fitting received non-development observations")
    volume=[]
    for field in ("quantity","relative_zone_volume","aggressive_buy_quantity","aggressive_sell_quantity","volume_delta"):
        cuts,count=con.execute(f"SELECT quantile_cont({field},[0.25,0.5,0.75]),count({field}) FROM features WHERE isfinite({field})").fetchone()
        if not count:raise ValueError("No finite development values for "+field)
        volume.append(Quantiles(field,tuple(cuts),DEVELOPMENT_END,count))
    con.close()
    events=pd.read_parquet(dest/"events.parquet")
    calibration_end=utc("2021-02-01")
    early=events[(events.timestamp<calibration_end)&events.volatility.notna()].to_dict(orient="records")
    context=[Quantiles.fit(field,early,calibration_end) for field in ("volatility","recent_return")]
    return volume,context


def summarize(dest,volume_models,context_models):
    visits=pd.read_parquet(dest/"interactions.parquet")
    features=pd.read_parquet(dest/"decision_features.parquet")
    events=pd.read_parquet(dest/"events.parquet")
    outcomes=pd.read_parquet(dest/"future_outcomes.parquet")
    for model in volume_models:features[model.field+"_bucket"]=features[model.field].map(model.bucket)
    feature_columns=["interaction_id"]+[m.field+"_bucket" for m in volume_models]
    base=visits.merge(features[feature_columns],on="interaction_id",validate="one_to_one")
    tables=[]
    outdir=dest/"measurements";outdir.mkdir(exist_ok=True)
    for cfg,group in base.groupby("configuration_id",sort=True):
        measured=group.merge(outcomes,on="event_id",validate="many_to_many")
        measured["measurement_id"]=[measurement_id(e,i,cfg,d,tp,sl,h) for e,i,d,tp,sl,h in zip(measured.event_id,measured.interaction_id,measured.direction,measured.tp,measured.sl,measured.horizon)]
        measured.to_parquet(outdir/f"{cfg}.parquet",index=False)
        standard=["configuration_id","detector","width_model","width_parameter","direction","tp","sl","horizon"]
        for dimension in ([],["visit_group"],*[[m.field+"_bucket"] for m in volume_models]):
            table=summary(measured,standard+dimension);table["table"]=dimension[0] if dimension else "sr_only"
            tables.append(table)
    table=pd.concat(tables,ignore_index=True);table.to_csv(dest/"research_summary.csv",index=False)
    scheduled=events[events.schedule].merge(outcomes,on="event_id")
    summary(scheduled,["direction","tp","sl","horizon"]).to_csv(dest/"schedule_baseline.csv",index=False)
    # Match on past context only; no labels are available to this function.
    pool=events.loc[events.volatility.notna()].to_dict(orient="records")
    control_index=ControlIndex(pool,*context_models)
    matches=[]
    for target in pool:
        if target["timestamp"]<max(m.development_end for m in context_models):continue
        for h in sorted(outcomes.horizon.unique()):
            control=control_index.match(target,int(h)*3600000)
            if control:matches.append({"target_event_id":target["event_id"],"control_event_id":control["event_id"],"horizon":h})
    matching=pd.DataFrame(matches,columns=["target_event_id","control_event_id","horizon"])
    matching.to_parquet(dest/"matched_control_links.parquet",index=False)
    controls=matching.merge(outcomes,left_on=["control_event_id","horizon"],right_on=["event_id","horizon"])
    comparisons=[];paired_targets=[]
    for cfg,group in base.groupby("configuration_id",sort=True):
        targets=group[["event_id"]].drop_duplicates()
        paired=targets.merge(controls,left_on="event_id",right_on="target_event_id",suffixes=("_target",""))
        result=summary(paired,["direction","tp","sl","horizon"])
        result["configuration_id"]=cfg
        # Unique control counts use control IDs, not replicated target/zone rows.
        counts=paired.groupby(["direction","tp","sl","horizon"]).target_event_id.nunique().rename("matched_target_count").reset_index()
        result=result.merge(counts,on=["direction","tp","sl","horizon"])
        result["eligible_target_count"]=len(targets)
        comparisons.append(result)
        target_links=targets.merge(matching,left_on="event_id",right_on="target_event_id")
        target_outcomes=target_links.merge(outcomes,on=["event_id","horizon"])
        target_table=summary(target_outcomes,["direction","tp","sl","horizon"])
        target_table["configuration_id"]=cfg
        paired_targets.append(target_table)
    pd.concat(comparisons,ignore_index=True).to_csv(dest/"matched_baseline.csv",index=False)
    pd.concat(paired_targets,ignore_index=True).to_csv(dest/"matched_targets.csv",index=False)
    return table


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase",choices=["development","validation"],required=True)
    parser.add_argument("--resume-generated",action="store_true",help="Resume deterministic development summarization only")
    args=parser.parse_args();plan=manifest()
    freeze_path=ROOT/"frozen-validation.json"
    if args.phase=="development":
        if freeze_path.exists():raise ValueError("Development cannot be rerun after validation subset is frozen")
        cfgs=configurations(plan)
        if args.resume_generated:
            dest=ROOT/"development";saved=json.loads((dest/"configuration-manifest.json").read_text())
            if saved["plan"]!=plan or saved["configurations"]!=cfgs or saved["coverage_id"]!=load_coverage(ROOT)["coverage_id"]:
                raise ValueError("Generated development artifacts belong to a different run")
            for name,digest in saved["artifact_hashes"].items():
                if sha256(dest/name)!=digest:raise ValueError("Generated development artifact changed")
        else:dest=generate(ROOT,args.phase,cfgs,plan)
        from .phase3_disk_summary import summarize_disk
        volume,context=fit_buckets(dest);table=summarize_disk(dest,volume,context)
        # Coverage-based inclusion, never a win-rate ranking. Retain methods with enough unique events.
        eligible=set(table[(table.table=="sr_only")&(table.unique_event_count>=100)].configuration_id)
        selected=[c for c in cfgs if c["configuration_id"] in eligible and c["width_model"]=="original_timeframe"]
        if not selected:raise ValueError("No configuration meets predeclared coverage criterion")
        frozen=frozen_subset(selected,volume+context,DEVELOPMENT_END,
            "original timeframe width; >=100 unique development events; all eligible detector settings retained")
        frozen.pop("freeze_id")
        frozen["plan"]=plan
        frozen["coverage_id"]=load_coverage(ROOT)["coverage_id"]
        from .runner import code_digest
        frozen["research_code_digest"]=code_digest()
        frozen["development_artifact_hashes"]={p.name:sha256(p) for p in sorted(dest.glob("*.parquet"))}
        frozen["freeze_id"]=identity(frozen)
        write_json(freeze_path,frozen)
        write_json(dest/"evaluation-complete.json",{"phase":"development","freeze_id":frozen["freeze_id"]})
    else:
        if args.resume_generated:raise ValueError("Automatic validation reruns are prohibited")
        frozen=json.loads(freeze_path.read_text())
        verify_freeze(frozen)
        if frozen.get("plan")!=plan:raise ValueError("Research plan differs from frozen development plan")
        if frozen.get("coverage_id")!=load_coverage(ROOT)["coverage_id"]:raise ValueError("Coverage changed after development freeze")
        from .runner import code_digest
        if frozen.get("research_code_digest")!=code_digest():raise ValueError("Research code changed after development freeze")
        marker=ROOT/"validation-started.json"
        if marker.exists():raise ValueError("Single validation evaluation already started; inspect prior artifacts")
        models=[Quantiles(**{**m,"cuts":tuple(m["cuts"])}) for m in frozen["bucket_models"]]
        require_catalog(ROOT,DEVELOPMENT_END,VALIDATION_END)
        write_json(marker,{"freeze_id":frozen["freeze_id"]})
        dest=generate(ROOT,args.phase,frozen["configurations"],plan)
        from .phase3_disk_summary import summarize_disk
        summarize_disk(dest,models[:5],models[5:])
        write_json(dest/"evaluation-complete.json",{"phase":"validation","freeze_id":frozen["freeze_id"]})


if __name__=="__main__":main()
