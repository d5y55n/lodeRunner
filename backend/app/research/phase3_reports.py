"""Descriptive development reports only: no edge, significance or trading claims."""
import json
import argparse
from pathlib import Path
import pandas as pd
from .phase3_engine import ROOT,load_coverage
from .phase3_storage import connect,literal
from app.market.aggregate_trades import write_json,sha256


def markdown(frame):
    def cell(v):
        if pd.isna(v):return "NA"
        if isinstance(v,float):return f"{v:.6g}"
        return str(v).replace("|","/")
    return "\n".join(["| "+" | ".join(frame.columns)+" |","| "+" | ".join(["---"]*len(frame.columns))+" |"]+
                     ["| "+" | ".join(cell(v) for v in row)+" |" for row in frame.itertuples(index=False,name=None)])


def reports(root=ROOT,phase="development"):
    if phase not in ("development","validation"):raise ValueError("Unknown phase")
    dest=root/phase
    if not (dest/"evaluation-complete.json").exists():
        raise ValueError("Research evaluation has not completed; partial reports are prohibited")
    coverage=load_coverage(root)
    frozen=json.loads((root/"frozen-validation.json").read_text())
    configuration=json.loads((dest/"configuration-manifest.json").read_text())
    table=pd.read_csv(dest/"research_summary.csv")
    con=connect(dest)
    candidates=con.execute("SELECT detector,count(*) candidates,count(DISTINCT candidate_id) unique_candidates FROM read_parquet("+literal(dest/"candidates.parquet")+") GROUP BY detector ORDER BY detector").df()
    counts=pd.read_csv(dest/"detector_counts.csv").merge(candidates,on="detector")
    d_counts=con.execute("SELECT json_extract_string(metadata,'$.bin_size') bin_width, count(*) candidates, avg(cast(json_extract_string(metadata,'$.observed_ratio') AS DOUBLE)) mean_concentration, median(cast(json_extract_string(metadata,'$.observed_ratio') AS DOUBLE)) median_concentration FROM read_parquet("+literal(dest/"candidates.parquet")+") WHERE detector='D' GROUP BY bin_width ORDER BY bin_width").df()
    con.close()
    docs=root.parents[1]/"docs/research";docs.mkdir(exist_ok=True)
    warning=f"{phase.title()}-only descriptive results. Overlapping zones/configurations/horizons are dependent. No edge, significance, optimal-parameter or live-trading claim. No 2024 data used."
    prefix="PHASE3" if phase=="development" else "PHASE3_VALIDATION"
    subset=table[(table.table=="sr_only")&(table.width_model=="original_timeframe")&(table.direction=="LONG")&(table.tp==.003)&(table.sl==.003)&(table.horizon==8)].copy()
    cfglabels={c["configuration_id"]:c["detector"]+" "+json.dumps(c["parameters"],sort_keys=True) for c in configuration["configurations"]}
    subset["configuration"]=subset.configuration_id.map(cfglabels)
    shown=["configuration","unique_event_count","measurement_count","tp_first_rate","sl_first_rate","ambiguous_rate","censored_rate","event_balanced_tp_first_rate","mfe_pct_median","mae_pct_median"]
    (docs/(prefix+"_DETECTOR_COMPARISON.md")).write_text(f"# {phase.title()} Detector Comparison\n\n"+warning+"\n\n"+markdown(counts)+
        "\n\n## Predeclared Display Slice\n\nOriginal 1h half-width 0.004, LONG, TP=SL=0.003, horizon=8 candles. This display slice is not a selected winner. All configured widths/directions/TP/SL/horizons remain in research_summary.csv.\n\n"+
        markdown(subset[shown])+"\n\n## Detector D\n\nBin width is independent of zone width; occupied-bin mean multiplier remains 1.5.\n\n"+markdown(d_counts)+"\n",encoding="utf-8")
    attachments=pd.read_csv(dest/"volume_attachment_counts.csv")
    volume=table[(table.detector=="A")&(table.width_model=="original_timeframe")&(table.direction=="LONG")&(table.tp==.003)&(table.sl==.003)&(table.horizon==8)&table.table.isin(["sr_only","relative_zone_volume_bucket","volume_delta_bucket"])].copy()
    volume["bucket"]=volume.relative_zone_volume_bucket.fillna(volume.volume_delta_bucket).fillna("ALL")
    (docs/(prefix+"_VOLUME_ABLATION.md")).write_text(f"# {phase.title()} Volume Ablation\n\n"+warning+"\n\n"+markdown(attachments)+
        "\n\nQuarantined overlapping current/baseline windows are MISSING, not zero. A/B/C price interactions remain in S/R-only tables. Full-development quantiles describe development retrospectively and are frozen for future validation. They are not online-available thresholds during their own fit period.\n\nA, original 1h width, LONG, TP=SL=0.003, horizon=8 display slice:\n\n"+
        markdown(volume[["table","bucket","unique_event_count","measurement_count","tp_first_rate","sl_first_rate","ambiguous_rate","event_balanced_tp_first_rate"]])+"\n",encoding="utf-8")
    schedule=pd.read_csv(dest/"schedule_baseline.csv");matched=pd.read_csv(dest/"matched_baseline.csv");targets=pd.read_csv(dest/"matched_targets.csv")
    def display(frame):return frame[(frame.direction=="LONG")&(frame.tp==.003)&(frame.sl==.003)&(frame.horizon==8)]
    matched=display(matched);matched["configuration"]=matched.configuration_id.map(cfglabels)
    targets=display(targets);targets["configuration"]=targets.configuration_id.map(cfglabels)
    keys=["configuration","unique_event_count","measurement_count","tp_first_rate","event_balanced_tp_first_rate"]
    (docs/(prefix+"_BASELINE_COMPARISON.md")).write_text(f"# {phase.title()} Baseline Comparison\n\n"+warning+
        "\n\nSchedule: every fourth closed candle. Matcher: January 2021 context quantiles, only earlier controls whose full horizon has elapsed at target time. No matching before February 2021. Matching never sees outcomes. Control reuse is not independence.\n\n## Schedule Display Slice\n\n"+
        markdown(display(schedule)[["unique_event_count","measurement_count","tp_first_rate","sl_first_rate","ambiguous_rate"]])+
        "\n\n## Matched Controls (Same Display Slice)\n\nUnique events below count reused CONTROL events; matched_target_count separately counts target events.\n\n"+
        markdown(matched[keys+["matched_target_count","eligible_target_count"]])+
        "\n\n## Matched Targets Only\n\nCompare controls with this matched target subset, not unmatched S/R rows.\n\n"+markdown(targets[keys])+"\n",encoding="utf-8")
    catalog=[json.loads(p.read_text()) for p in sorted((root/"integrity").glob("*-aggTrades.json"))]
    total=sum(r["rows"] for r in catalog);qminutes=sum((b-a)//60000 for a,b in coverage["quarantine_intervals"])
    gaps=pd.DataFrame([{"utc_after":pd.Timestamp(g["after"]["timestamp"],unit="ms",tz="UTC").isoformat(),
        "missing_ID_numbers":g["id_step"]-1,"timestamp_gap_seconds":g["timestamp_gap_ms"]/1000,
        "price_change_fraction":g["price_change_fraction"],"publications_agree":g["daily_monthly_records_agree"],
        "decision":g["decision"]} for g in coverage["decisions"]])
    quarantine=pd.DataFrame([{"start_utc":pd.Timestamp(a,unit="ms",tz="UTC").isoformat(),
        "end_utc_exclusive":pd.Timestamp(b,unit="ms",tz="UTC").isoformat(),"minutes":(b-a)//60000}
        for a,b in coverage["quarantine_intervals"]])
    quarantine.to_csv(root/"quarantine-intervals.csv",index=False)
    replacements=pd.DataFrame([{"month":r["month"],"monthly_rows":r["monthly_rows"],"selected_daily_rows":r["daily_rows"],
        "monthly_duplicate_rows":r["monthly_duplicate_adjacent_rows"],"unresolved_minutes":r["unresolved_minutes"]}
        for r in coverage["publication_decisions"]])
    (docs/"PHASE3_COVERAGE_REPORT.md").write_text("# Outcome-Blind Coverage Report\n\n"+
        f"Active policy: {coverage['policy']['policy']['version']}. Coverage ID: {coverage['coverage_id']}. All decisions precede research outcomes. No reconstructed trades.\n\n"+
        "## Selected-Source ID Discontinuities\n\n"+markdown(gaps)+"\n\n## Rejected Monthly Publications\n\n"+markdown(replacements)+
        "\n\n## Minute-Level Trade-Volume Quarantine\n\n"+markdown(quarantine)+
        "\n\nA/B/C verified candle history is retained. D formation windows intersecting these intervals are omitted; overlapping current/baseline zone-volume features are unavailable, not zero. Price/time jumps alone never trigger exclusion. Boundary conservation warnings do not shift timestamps or volume. Daily/monthly sources are not independent observations of execution. See the versioned policy and raw forensic evidence for assumptions and amendments.\n",encoding="utf-8")
    status=dict(phase=phase,phase_complete=True,validation_run=(root/"validation-started.json").exists(),final_test_used=False,
        aggregate_rows=total,months=len(catalog),coverage_id=coverage["coverage_id"],freeze_id=frozen["freeze_id"],
        quarantined_minutes=qminutes,configurations=len(configuration["configurations"]),frozen_configurations=len(frozen["configurations"]),
        interaction_rows=configuration["interaction_rows"],unique_events=configuration["unique_events"],
        measurement_rows=int(table.loc[table.table=="sr_only","measurement_count"].sum()))
    write_json(dest/(phase+"-completion.json"),status)
    (docs/("PHASE3_"+phase.upper()+"_COMPLETION.md")).write_text(f"# Phase 3 {phase.title()} Completion\n\n"+warning+
        "\n\nDevelopment [2021-01-01,2023-01-01) UTC. Reserved validation [2023-01-01,2024-01-01). All 2024 untouched.\n\n"+
        f"Verified acquisition: {len(catalog)} months, {total:,} aggregate trades in selected official publications. Quarantined trade-volume minutes: {qminutes}.\n\n"+
        f"{phase.title()} configurations: {len(configuration['configurations'])}; interactions: {configuration['interaction_rows']:,}; unique decision-close events: {configuration['unique_events']:,}.\n\n"+
        f"Frozen validation configurations: {len(frozen['configurations'])}. Selection is coverage-only (original 1h width and >=100 unique development events), never a win-rate ranking. Freeze ID: {frozen['freeze_id']}.\n\n"+
        "Measurements use a lossless normalized representation: interactions.parquet + future_outcomes.parquet and the measurements view in research.duckdb, with reproducible measurement IDs. research_summary.csv carries exact row multiplicities and unique-event counts. Future interaction durations/exits are separate from decision-time features.\n\n"+
        "Scope: this long-range run uses 1h candles. Fixed half-widths are 0.0005/0.001/0.002/0.003/0.005; original 1h width is 0.004. Other timeframe mappings are not evaluated here. B widths 1/2, C reversals 0.003/0.005, D bins 50/100; no parameter ranking.\n\n"+
        "Limitations: event identity conservatively combines same-timestamp zones; adjacent horizons remain dependent. Quantile cuts can repeat, creating empty descriptive buckets. Gross expectancy is conditional boundary return on unambiguous resolved full-horizon observations, excludes costs and is not strategy P&L. Source agreement is not proof of complete executions; the predeclared tolerance can miss small deficits.\n\n"+
        "See PHASE3_COVERAGE_POLICY.md, coverage-manifest.json, forensic evidence, detector comparison, volume ablation and baseline comparison. Validation status is recorded separately; development completion is not evidence of an edge.\n",encoding="utf-8")
    print(json.dumps(status,indent=2),flush=True)
    if phase=="validation":
        development=json.loads((root/"development/development-completion.json").read_text())
        (docs/"PHASE3_COMPLETION.md").write_text("# Phase 3 Completion\n\n"+warning+
            "\n\nCompleted the 1h historical research scope: development 2021-2022, one frozen validation evaluation in 2023. All 2024 remains untouched. No live signals or trading. Other timeframe mappings were not evaluated.\n\n"+
            markdown(pd.DataFrame([development,status])[["phase","configurations","interaction_rows","unique_events","measurement_rows"]])+"\n\n"+
            f"Coverage policy: {coverage['policy']['policy']['version']}; quarantined trade-volume minutes: {qminutes}; retained price history is unchanged. Source groups: 72/72, aggregate rows: {total:,}.\n\n"+
            f"Frozen configuration ID: {frozen['freeze_id']}. Selection used development coverage only, not win-rate ranking. Validation was not used to refit quantiles or choose settings.\n\n"+
            "See separate development and validation detector/volume/baseline reports and PHASE3_COVERAGE_POLICY.md for source-quality amendments made before outcomes. No final strategy or edge conclusion is made.\n",encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--phase",choices=["development","validation"],default="development")
    reports(phase=parser.parse_args().phase)
