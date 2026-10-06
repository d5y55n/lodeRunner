"""Read-only forensic scan of a reserved-safe official monthly archive."""
import argparse
import zipfile
import json
import httpx
import pandas as pd
import numpy as np
from .phase3_archives import ROOT,month_bounds
from .aggregate_trades import write_json,download_file,sha256


def audit(month,daily=False):
    month_bounds(month)
    path=ROOT/"raw/aggTrades"/f"BTCUSDT-aggTrades-{month}.zip"
    names=["id","price","quantity","first","last","timestamp","maker"]
    examples=[];previous=None;rows=0;count=0
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as stream:header=0 if stream.readline().startswith(b"agg_trade_id") else None
        with z.open(z.namelist()[0]) as stream:
            for frame in pd.read_csv(stream,header=header,names=names,usecols=["id","timestamp"],dtype="int64",chunksize=1000000):
                ids=frame.id.to_numpy();times=frame.timestamp.to_numpy()
                steps=np.diff(ids,prepend=previous if previous is not None else ids[0]-1)
                bad=np.flatnonzero(steps!=1);count+=len(bad);rows+=len(frame)
                for i in bad[:max(0,100-len(examples))]:
                    examples.append(dict(previous_id=int(ids[i-1]) if i else previous,id=int(ids[i]),
                                         timestamp=int(times[i]),step=int(steps[i]),
                                         utc=pd.Timestamp(times[i],unit="ms",tz="UTC").isoformat()))
                previous=int(ids[-1])
    result=dict(month=month,rows_scanned=rows,aggregate_discontinuities=count,examples=examples,
                repaired=False,eligible_for_research=count==0)
    write_json(ROOT/"integrity"/f"{month}-gap-audit.json",result)
    print(result,flush=True)
    if daily:compare_daily(result)


def compare_daily(result):
    names=["id","price","quantity","first","last","timestamp","maker"]
    comparisons=[]
    for day in sorted({r["utc"][:10] for r in result["examples"]}):
        month_bounds(day[:7])
        filename=f"BTCUSDT-aggTrades-{day}.zip"
        url="https://data.binance.vision/data/futures/um/daily/aggTrades/BTCUSDT/"+filename
        root=ROOT/"raw/daily-audit";root.mkdir(parents=True,exist_ok=True)
        archive=root/filename;checksum=root/(filename+".CHECKSUM")
        with httpx.Client(timeout=120,follow_redirects=True) as client:
            download_file(client,url,archive);download_file(client,url+".CHECKSUM",checksum)
        expected=checksum.read_text().split()
        digest=sha256(archive)
        if len(expected)!=2 or expected[0]!=digest or expected[1].lstrip("*")!=filename:
            raise ValueError("Daily audit checksum mismatch")
        targets=[r for r in result["examples"] if r["utc"].startswith(day)]
        counts={r["previous_id"]:0 for r in targets}
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:raise ValueError("Daily audit ZIP CRC failure")
            with z.open(z.namelist()[0]) as stream:header=0 if stream.readline().startswith(b"agg_trade_id") else None
            with z.open(z.namelist()[0]) as stream:
                for frame in pd.read_csv(stream,header=header,names=names,usecols=["id"],dtype="int64",chunksize=500000):
                    for target in targets:
                        counts[target["previous_id"]]+=int(((frame.id>target["previous_id"])&(frame.id<target["id"])).sum())
        comparisons.extend(dict(**t,daily_url=url,daily_sha256=digest,checksum_verified=True,zip_crc_verified=True,
                                missing_id_count=t["step"]-1,missing_ids_present_in_daily=counts[t["previous_id"]]) for t in targets)
    write_json(ROOT/"integrity"/f"{result['month']}-daily-comparison.json",dict(comparisons=comparisons,repaired=False))
    print(comparisons,flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--month",required=True)
    parser.add_argument("--daily",action="store_true");parser.add_argument("--reuse-audit",action="store_true")
    args=parser.parse_args();month_bounds(args.month)
    if args.reuse_audit:compare_daily(json.loads((ROOT/"integrity"/f"{args.month}-gap-audit.json").read_text()))
    else:audit(args.month,args.daily)
