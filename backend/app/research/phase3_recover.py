"""Resume feature construction from complete development parquet artifacts only."""
from dataclasses import asdict
import pandas as pd
import pyarrow.parquet as pq
from app.market.aggregate_trades import write_json,sha256
from .phase3_engine import ROOT,require_catalog,load_coverage,configurations
from .phase3_plan import DEVELOPMENT_START,DEVELOPMENT_END,manifest
from .phase3_storage import connect,literal
from .phase3_feature_batch import build_features


def recover():
    root=ROOT;dest=root/"development";plan=manifest();configs=configurations(plan)
    if (root/"frozen-validation.json").exists():raise ValueError("Cannot recover generation after freeze")
    _,catalog=require_catalog(root,DEVELOPMENT_START,DEVELOPMENT_END);coverage=load_coverage(root)
    names=["events.parquet","future_outcomes.parquet","candidates.parquet","interactions.parquet","future_interaction_lifecycles.parquet"]
    initial={name:sha256(dest/name) for name in names}
    metadata={name:pq.ParquetFile(dest/name).metadata.num_rows for name in names}
    if metadata["interactions.parquet"]!=metadata["future_interaction_lifecycles.parquet"]:raise ValueError("Incomplete lifecycle records")
    con=connect(dest)
    con.execute("CREATE VIEW visits AS SELECT * FROM read_parquet("+literal(dest/"interactions.parquet")+")")
    found={r[0] for r in con.execute("SELECT DISTINCT configuration_id FROM visits").fetchall()}
    if found!={c["configuration_id"] for c in configs}:raise ValueError("Incomplete configuration generation")
    violations=con.execute("SELECT count(*) FROM visits WHERE observed_at>=? OR start<? OR known_at>start",[DEVELOPMENT_END,DEVELOPMENT_START]).fetchone()[0]
    if violations:raise ValueError("Invalid recovered interaction bounds")
    unique=con.execute("SELECT count(DISTINCT event_id) FROM visits").fetchone()[0]
    # Independent market candles remain the price-history source during volume quarantine.
    for a,b in coverage["quarantine_intervals"]:
        if a>=DEVELOPMENT_END:continue
        count=con.execute("SELECT count(*) FROM read_parquet("+literal(dest/"candidates.parquet")+") WHERE detector='D' AND source_timestamp<? AND known_at>?",[b,a]).fetchone()[0]
        if count:raise ValueError("Recovered D candidates intersect quarantine")
    con.close()
    write_json(dest/"generation-recovery.json",{"reason":"Feature-stage interruption; complete upstream parquet reused",
        "coverage_id":coverage["coverage_id"],"upstream_hashes":initial,"row_counts":metadata,"outcomes_used_for_selection":False})
    print("RECOVERY_VERIFIED",metadata,flush=True)
    count=build_features(dest,root,DEVELOPMENT_START,coverage["quarantine_intervals"])
    if count!=metadata["interactions.parquet"]:raise ValueError("Feature row-count mismatch")
    if any(sha256(dest/name)!=digest for name,digest in initial.items()):raise ValueError("Upstream artifacts changed during recovery")
    write_json(dest/"configuration-manifest.json",{"plan":plan,"coverage_id":coverage["coverage_id"],
        "actual_start":DEVELOPMENT_START,"actual_end":DEVELOPMENT_END,"configurations":configs,"source_catalog":catalog,
        "event_definition":"symbol_timeframe_decision_close","raw_candidate_count":metadata["candidates.parquet"],
        "interaction_rows":count,"unique_events":unique,"recovered_feature_stage":True,
        "artifact_hashes":{p.name:sha256(p) for p in sorted(dest.glob("*.parquet"))}})


if __name__=="__main__":recover()
