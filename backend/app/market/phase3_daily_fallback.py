"""Explicit selection of verified official daily sources for invalid monthly files."""
import argparse
import json
import pandas as pd
from datetime import datetime,timezone
from .phase3_archives import ROOT,month_bounds,process_trades
from .phase3_coverage import official_daily
from .aggregate_trades import write_json
from app.research.models import identity


def run(month):
    start,end=month_bounds(month)
    path=ROOT/"integrity"/f"{month}-aggTrades.json"
    prior=json.loads(path.read_text())
    if prior.get("passed"):return prior
    directory=ROOT/"integrity/rejected-monthly";directory.mkdir(exist_ok=True)
    write_json(directory/path.name,prior)
    archives=[];sources=[]
    for timestamp in range(start,end,86400000):
        day=pd.Timestamp(timestamp,unit="ms",tz="UTC").strftime("%Y-%m-%d")
        archive,source=official_daily(day,"aggTrades",ROOT)
        archives.append(archive);sources.append(source)
    report=dict(month=month,kind="aggTrades",start=start,end=end,
                source_kind="official_daily_collection",source_parts=sources,
                sha256=identity(sources),monthly_sha256=prior["sha256"],url="official_daily_collection",
                checksum_verified=True,zip_crc_verified=True,
                source_selection_rule="invalid_monthly_source_replaced_in_full_with_verified_daily_publications",
                monthly_failure=prior.get("error"),reconstructed_trades=0,interpolated_quantity=0)
    report["source_selected_at"]=datetime.now(timezone.utc).isoformat()
    report=process_trades(archives,report,ROOT)
    write_json(path,report)
    print("DAILY_SOURCE_VERIFIED",month,report["rows"],"gaps",len(report["gaps"]),flush=True)
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--month",required=True)
    run(parser.parse_args().month)
