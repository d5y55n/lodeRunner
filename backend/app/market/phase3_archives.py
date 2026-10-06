"""Monthly archive acquisition with bounded-memory validation and exact-price profiles."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import io
import json
from pathlib import Path
import zipfile
import httpx
import numpy as np
import pandas as pd
from .aggregate_trades import download_file,sha256,write_json
from app.research.phase3_plan import utc,permitted,manifest

ROOT = Path(__file__).resolve().parents[3]/"data/phase3"


class IntegrityError(ValueError):
    def __init__(self,stats,examples):
        self.stats,self.examples=stats,examples
        super().__init__("Trade sequence integrity failed: "+json.dumps(stats))


def months():
    return [f"{y}-{m:02d}" for y in range(2021,2024) for m in range(1,13)]


def month_bounds(month):
    y,m = map(int,month.split("-"))
    start = utc(month+"-01")
    end = utc(f"{y+1 if m==12 else y}-{1 if m==12 else m+1:02d}-01")
    permitted(start,end)
    return start,end


def capture(month,kind,root=ROOT):
    start,end = month_bounds(month)
    suffix = "aggTrades" if kind=="aggTrades" else "1h"
    filename = f"BTCUSDT-{suffix}-{month}.zip"
    part = f"aggTrades/BTCUSDT/{filename}" if kind=="aggTrades" else f"klines/BTCUSDT/1h/{filename}"
    url = "https://data.binance.vision/data/futures/um/monthly/"+part
    raw = root/"raw"/kind
    raw.mkdir(parents=True,exist_ok=True)
    archive,checksum = raw/filename,raw/(filename+".CHECKSUM")
    with httpx.Client(timeout=120,follow_redirects=True) as client:
        download_file(client,url,archive)
        download_file(client,url+".CHECKSUM",checksum)
    parts = checksum.read_text().split()
    digest = sha256(archive)
    if len(parts)!=2 or parts[0].lower()!=digest or parts[1].lstrip("*")!=filename:
        raise ValueError("Official checksum mismatch: "+filename)
    with zipfile.ZipFile(archive) as z:
        members = z.namelist()
        if len(members)!=1 or not members[0].endswith(".csv") or z.testzip() is not None:
            raise ValueError("Archive CRC/members invalid: "+filename)
    return archive,{"month":month,"kind":kind,"url":url,"sha256":digest,"bytes":archive.stat().st_size,
                    "start":start,"end":end,"checksum_verified":True,"zip_crc_verified":True}


def validate_trade_chunk(frame,start,end,previous=None,allow_id_gaps=False):
    names=["id","price","quantity","first","last","timestamp","maker"]
    frame.columns=names
    for name in names[:-1]:
        frame[name]=pd.to_numeric(frame[name],errors="raise")
    for name in ("id","first","last","timestamp"):
        if ((frame[name]%1)!=0).any() or (frame[name]<0).any():
            raise ValueError("Invalid integer field")
        frame[name]=frame[name].astype("int64")
    maker=frame.maker.astype(str).str.lower()
    if not maker.isin(["true","false"]).all():
        raise ValueError("Invalid maker boolean")
    frame["maker"]=maker.eq("true")
    if (not np.isfinite(frame.price).all() or not np.isfinite(frame.quantity).all()
            or (frame.price<=0).any() or (frame.quantity<=0).any()
            or (frame["first"]>frame["last"]).any()):
        raise ValueError("Invalid trade values")
    if not frame.timestamp.between(start,end-1).all():
        raise ValueError("Timestamp unit/range violation")
    ids=frame.id.to_numpy();times=frame.timestamp.to_numpy()
    did=np.diff(ids,prepend=previous[0] if previous else ids[0]-1)
    dtime=np.diff(times,prepend=previous[1] if previous else times[0])
    first=frame["first"].to_numpy();last=frame["last"].to_numpy()
    constituent=first-np.r_[previous[2] if previous else first[0]-1,last[:-1]]-1
    stats={"rows":len(frame),"duplicate_ids_in_chunk":int(frame.id.duplicated().sum()),
           "duplicate_records_in_chunk":int(frame.duplicated().sum()),
           "ordering_violations":int(((did<=0)|(dtime<0)).sum()),
           "aggregate_discontinuities":int((did!=1).sum()),
           "constituent_discontinuities":int((constituent!=0).sum())}
    failures=("duplicate_ids_in_chunk","duplicate_records_in_chunk","ordering_violations")
    if any(stats[k] for k in failures) or (stats["aggregate_discontinuities"] and not allow_id_gaps):
        examples=[]
        for i in np.flatnonzero((did!=1)|(dtime<0))[:20]:
            examples.append({"previous_id":int(ids[i-1]) if i else previous[0] if previous else None,
                             "id":int(ids[i]),"timestamp":int(times[i]),"id_step":int(did[i])})
        raise IntegrityError(stats,examples)
    return frame,stats,(int(ids[-1]),int(times[-1]),int(last[-1]))


def trade_chunks(archives):
    for archive in archives:
        with zipfile.ZipFile(archive) as z:
            member=z.namelist()[0]
            with z.open(member) as stream:first_line=stream.readline().decode("utf-8-sig")
            header=0 if first_line.startswith("agg_trade_id") else None
            dtypes={"id":"int64","price":"float64","quantity":"float64","first":"int64",
                    "last":"int64","timestamp":"int64","maker":"str"}
            with z.open(member) as stream:
                yield from pd.read_csv(stream,header=header,names=list(dtypes),chunksize=500000,dtype=dtypes)


def process_trades(archive,report,root=ROOT):
    destination=root/"profiles"/f"{report['month']}.parquet"
    destination.parent.mkdir(parents=True,exist_ok=True)
    pieces=[];previous=None;previous_record=None;totals={};days=set();gaps=[]
    for chunk in trade_chunks(archive if isinstance(archive,list) else [archive]):
                frame,stats,previous=validate_trade_chunk(chunk,report["start"],report["end"],previous,allow_id_gaps=True)
                ids=frame.id.to_numpy()
                steps=np.diff(ids,prepend=previous_record["id"] if previous_record else ids[0]-1)
                for i in np.flatnonzero(steps>1):
                    before=frame.iloc[int(i)-1].to_dict() if i else previous_record
                    gaps.append({"before":before,"after":frame.iloc[int(i)].to_dict(),"id_step":int(steps[i])})
                previous_record=frame.iloc[-1].to_dict()
                if "first_aggregate_id" not in report:
                    report["first_aggregate_id"]=int(frame.id.iloc[0])
                    report["first_timestamp"]=int(frame.timestamp.iloc[0])
                    report["first_record"]=frame.iloc[0].to_dict()
                for key,value in stats.items():totals[key]=totals.get(key,0)+value
                days.update((frame.timestamp//86400000).unique().tolist())
                frame["hour"]=frame.timestamp//3600000*3600000
                frame["buy"]=frame.quantity.where(~frame.maker,0.)
                frame["sell"]=frame.quantity.where(frame.maker,0.)
                # Price is an exact observed float64 price, not a coarse VAP bin.
                pieces.append(frame.groupby(["hour","price"],sort=True)[["quantity","buy","sell"]].sum().reset_index())
    expected=set(range(report["start"]//86400000,report["end"]//86400000))
    missing=sorted(expected-days)
    report.update(totals,gaps=gaps,last_record=previous_record,coverage_schema=1,
                  missing_dates=[pd.Timestamp(d*86400000,unit="ms",tz="UTC").date().isoformat() for d in missing],
                  last_aggregate_id=previous[0] if previous else None,last_timestamp=previous[1] if previous else None)
    if missing or previous is None:raise ValueError("Missing trade dates")
    profile=pd.concat(pieces).groupby(["hour","price"],sort=True)[["quantity","buy","sell"]].sum().reset_index()
    profile.to_parquet(destination,index=False)
    report.update(profile=str(destination.relative_to(root)),profile_sha256=sha256(destination),
                  passed=True,coverage_pending=bool(gaps),status="FORENSIC_PENDING" if gaps else "PASS_WITH_WARNINGS" if totals["constituent_discontinuities"] else "PASS")
    return report


def process_candles(archive,report,root=ROOT):
    with zipfile.ZipFile(archive) as z:
        with z.open(z.namelist()[0]) as stream:
            first=stream.readline().decode("utf-8-sig")
        with z.open(z.namelist()[0]) as stream:
            frame=pd.read_csv(stream,header=0 if first.startswith("open_time") else None)
    if len(frame.columns)!=12:raise ValueError("Unexpected candle schema")
    frame.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trade_count","taker_buy_volume","taker_buy_quote_volume","ignore"]
    expected=np.arange(report["start"],report["end"],3600000)
    if not np.array_equal(frame.open_time.to_numpy(),expected):raise ValueError("Missing/duplicate/reordered candles")
    from .models import Candle
    for record in frame.drop(columns="ignore").to_dict(orient="records"):Candle(**record)
    path=root/"candles"/f"{report['month']}.parquet";path.parent.mkdir(parents=True,exist_ok=True)
    frame.to_parquet(path,index=False)
    report.update(passed=True,rows=len(frame),normalized_sha256=sha256(path))
    return report


def task(month,kind,root):
    path=root/"integrity"/f"{month}-{kind}.json";path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        old=json.loads(path.read_text())
        if old.get("passed"):return old
    report={"month":month,"kind":kind}
    try:
        archive,report=capture(month,kind,root)
        report=process_trades(archive,report,root) if kind=="aggTrades" else process_candles(archive,report,root)
        write_json(path,report)
        print(f"VERIFIED {month} {kind} rows={report['rows']}",flush=True)
        return report
    except Exception as exc:
        report.update(passed=False,error=str(exc),missing_or_invalid=True)
        if isinstance(exc,IntegrityError):report.update(failed_chunk=exc.stats,discontinuity_examples=exc.examples)
        write_json(path,report)
        print(f"FAILED {month} {kind}: {exc}",flush=True)
        return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers",type=int,default=2)
    parser.add_argument("--month",choices=months())
    args=parser.parse_args()
    ROOT.mkdir(parents=True,exist_ok=True);write_json(ROOT/"plan.json",manifest())
    selected=[args.month] if args.month else months()
    jobs=[(m,k) for m in selected for k in ("klines","aggTrades")]
    results=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(task,m,k,ROOT) for m,k in jobs]
        for future in as_completed(futures):
            results.append(future.result())
            write_json(ROOT/"acquisition-status.json",{"expected":len(jobs),"finished":len(results),
                       "passed":sum(r["passed"] for r in results),"reports":sorted(results,key=lambda r:(r["month"],r["kind"]))})
    if not all(r["passed"] for r in results):raise SystemExit("Acquisition incomplete; inspect missing/invalid reports")


if __name__=="__main__":main()
