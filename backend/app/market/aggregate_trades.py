"""Auditable USD-M Futures aggregate-trade acquisition; never repairs gaps."""
import argparse
import csv
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
import httpx
import pandas as pd
from app.research.volume import Trade

DAY_MS = 86_400_000
ARCHIVE_ROOT = "https://data.binance.vision/data/futures/um/daily/aggTrades"


def midnight(day):
    return int(datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc).timestamp()*1000)


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def parse_bool(value):
    if value is True or value == "true" or value == "True":
        return True
    if value is False or value == "false" or value == "False":
        return False
    raise ValueError("Invalid buyer-is-maker boolean")


def parse_integer(value):
    if isinstance(value, bool) or not re.fullmatch(r"\d+", str(value)):
        raise ValueError("Expected nonnegative integer")
    return int(value)


def parse_record(row):
    if isinstance(row, dict):
        values = [row["a"], row["p"], row["q"], row.get("f"), row.get("l"), row["T"], row["m"]]
    else:
        if len(row) != 7:
            raise ValueError("Expected 7 USD-M aggregate-trade fields")
        values = row
    aid,p,q,first,last,ts,maker = values
    first = None if first in (None, "") else parse_integer(first)
    last = None if last in (None, "") else parse_integer(last)
    if (first is None) != (last is None) or (first is not None and first > last):
        raise ValueError("Invalid constituent trade ID range")
    return Trade(str(parse_integer(aid)), parse_integer(ts), float(p), float(q),
                 parse_bool(maker), first, last)


def inspect_records(rows, start, end):
    """Retain ordering and duplicates in report; invalid datasets cannot feed research."""
    report = {"requested_start":start, "requested_end":end, "timestamp_unit":"UTC milliseconds",
              "raw_rows":0, "valid_rows":0, "invalid_rows":0, "timestamp_out_of_range":0,
              "duplicate_aggregate_ids":0, "duplicate_records":0, "out_of_order":0,
              "aggregate_id_discontinuities":0, "constituent_id_discontinuities":0,
              "max_intertrade_gap_ms":0, "examples":[], "first_timestamp":None, "last_timestamp":None}
    trades, seen_ids, seen_records = [], set(), set()
    previous = None
    def issue(kind, row_no, detail):
        if len(report["examples"]) < 100:
            report["examples"].append({"kind":kind, "row":row_no, "detail":detail})
    for row in rows:
        report["raw_rows"] += 1
        try:
            t = parse_record(row)
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            report["invalid_rows"] += 1
            issue("invalid",report["raw_rows"],str(exc))
            continue
        report["valid_rows"] += 1
        aid = int(t.id)
        signature = (t.id,t.timestamp,t.price,t.quantity,t.buyer_is_maker,t.first_trade_id,t.last_trade_id)
        if aid in seen_ids:
            report["duplicate_aggregate_ids"] += 1
            issue("duplicate_id",report["raw_rows"],aid)
        if signature in seen_records:
            report["duplicate_records"] += 1
        seen_ids.add(aid)
        seen_records.add(signature)
        if not start <= t.timestamp < end:
            report["timestamp_out_of_range"] += 1
            issue("timestamp_range_or_unit",report["raw_rows"],t.timestamp)
        if previous:
            gap = t.timestamp-previous.timestamp
            report["max_intertrade_gap_ms"] = max(report["max_intertrade_gap_ms"],gap)
            if gap < 0 or aid < int(previous.id):
                report["out_of_order"] += 1
            if aid != int(previous.id)+1:
                report["aggregate_id_discontinuities"] += 1
                issue("aggregate_id_discontinuity",report["raw_rows"],[previous.id,t.id])
            if previous.last_trade_id is not None and t.first_trade_id is not None and t.first_trade_id != previous.last_trade_id+1:
                report["constituent_id_discontinuities"] += 1
                issue("constituent_id_discontinuity",report["raw_rows"],[previous.last_trade_id,t.first_trade_id])
        previous = t
        trades.append(t)
    if trades:
        report.update(first_timestamp=trades[0].timestamp,last_timestamp=trades[-1].timestamp,
                      first_aggregate_id=trades[0].id,last_aggregate_id=trades[-1].id,
                      leading_boundary_distance_ms=trades[0].timestamp-start,
                      trailing_boundary_distance_ms=end-trades[-1].timestamp)
    blocking = ("invalid_rows","timestamp_out_of_range","duplicate_aggregate_ids","duplicate_records",
                "out_of_order","aggregate_id_discontinuities")
    report["passed"] = bool(trades) and not any(report[k] for k in blocking)
    report["status"] = ("FAIL" if not report["passed"] else
                        "PASS_WITH_WARNINGS" if report["constituent_id_discontinuities"] else "PASS")
    report["coverage_basis"] = "Requested archive interval plus checksum; observed edges reported separately"
    report["limitations"] = ["ID gaps are detectable discontinuities, not automatic proof of lost executions.",
                             "Constituent trade-ID discontinuities are reported separately, not repaired.",
                             "No event at an interval boundary does not by itself imply a missing trade."]
    return trades, report


def download_file(client, url, path):
    # Reuse locally pinned source bytes. A failed partial download is never reused.
    if path.exists():
        return
    part = path.with_suffix(path.suffix+".partial")
    with client.stream("GET",url) as response:
        response.raise_for_status()
        with part.open("wb") as stream:
            for chunk in response.iter_bytes():
                stream.write(chunk)
    part.replace(path)


def read_archive(path):
    with zipfile.ZipFile(path) as archive:
        files = [n for n in archive.namelist() if n.endswith(".csv")]
        if len(files) != 1 or archive.testzip() is not None:
            raise ValueError("Invalid archive members or ZIP CRC")
        with archive.open(files[0]) as stream:
            reader = csv.reader(io.TextIOWrapper(stream,encoding="utf-8-sig"))
            for i,row in enumerate(reader):
                if i == 0 and row and row[0] in ("agg_trade_id","aggregate_trade_id"):
                    continue
                yield row


def acquire_day(day, raw_dir, symbol="BTCUSDT", client=None):
    if not re.fullmatch(r"[A-Z0-9]+",symbol):
        raise ValueError("Invalid symbol")
    day = date.fromisoformat(day) if isinstance(day,str) else day
    start,end = midnight(day),midnight(day)+DAY_MS
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True,exist_ok=True)
    filename = f"{symbol}-aggTrades-{day.isoformat()}.zip"
    path = raw_dir/filename
    url = f"{ARCHIVE_ROOT}/{symbol}/{filename}"
    owned = client is None
    client = client or httpx.Client(timeout=60,follow_redirects=True)
    report_path = raw_dir/(filename+".integrity.json")
    report = {"symbol":symbol,"source_url":url,"archive":filename,"requested_start":start,"requested_end":end}
    try:
        download_file(client,url,path)
        checksum_path = raw_dir/(filename+".CHECKSUM")
        download_file(client,url+".CHECKSUM",checksum_path)
        parts = checksum_path.read_text(encoding="utf-8").strip().split()
        expected = parts[0].lower()
        actual = sha256(path)
        report.update(sha256=actual,expected_sha256=expected,
                      checksum_match=(len(parts)==2 and parts[1].lstrip("*")==filename
                                      and re.fullmatch("[0-9a-f]{64}",expected) is not None and actual==expected))
        if not report["checksum_match"]:
            raise ValueError("Official archive SHA256 mismatch")
        trades,integrity = inspect_records(read_archive(path),start,end)
        report.update(integrity)
        write_json(report_path,report)
        if not report["passed"]:
            raise ValueError("Trade integrity failed; inspect report before use")
        return trades,report
    except Exception as exc:
        report.update(passed=False,status="FAIL",error=str(exc))
        write_json(report_path,report)
        raise
    finally:
        if owned:
            client.close()


def acquire_days(start_day,end_day,raw_dir,normalized_dir):
    """End date exclusive. Each day has its own official source and integrity report."""
    first,last = date.fromisoformat(start_day),date.fromisoformat(end_day)
    if first >= last:
        raise ValueError("Empty date range")
    normalized_dir = Path(normalized_dir)
    normalized_dir.mkdir(parents=True,exist_ok=True)
    reports,files,boundary_warnings = [],[],[]
    prior = None
    for offset in range((last-first).days):
        day = first+timedelta(days=offset)
        trades,report = acquire_day(day,raw_dir)
        if prior and (int(trades[0].id) != int(prior.id)+1 or trades[0].timestamp < prior.timestamp):
            write_json(normalized_dir/"range-integrity.json",{"passed":False,"boundary":[asdict(prior),asdict(trades[0])]})
            raise ValueError("Cross-archive discontinuity; no repair applied")
        if prior and prior.last_trade_id is not None and trades[0].first_trade_id != prior.last_trade_id+1:
            boundary_warnings.append({"previous_last_trade_id":prior.last_trade_id,
                                      "next_first_trade_id":trades[0].first_trade_id,"date":str(day)})
        prior = trades[-1]
        path = normalized_dir/f"BTCUSDT-aggTrades-{day}.parquet"
        pd.DataFrame([asdict(t) for t in trades]).to_parquet(path,index=False)
        reports.append(report)
        files.append({"file":path.name,"sha256":sha256(path)})
    manifest = {"schema":"aggregate-trades-v1","symbol":"BTCUSDT","start":midnight(first),"end":midnight(last),
                "parser_code_sha256":sha256(Path(__file__)),
                "passed":True,"status":"PASS_WITH_WARNINGS" if boundary_warnings or any(r["status"]=="PASS_WITH_WARNINGS" for r in reports) else "PASS",
                "boundary_warnings":boundary_warnings,
                "trade_count":sum(r["valid_rows"] for r in reports),"days":reports,"normalized":files}
    write_json(normalized_dir/"range-integrity.json",manifest)
    return manifest


def _fetch_rest(start,end,raw_dir,client,limit=1000):
    """Bounded supplementary REST capture, raw pages preserved with local hashes.

    REST has no official archive checksum. Do not describe local hashes as one.
    """
    if not start < end or end-start > 3_600_000 or not 1 <= limit <= 1000:
        raise ValueError("REST request must span at most one hour")
    root = Path(raw_dir)
    root.mkdir(parents=True,exist_ok=True)
    rows,files = [],[]
    outside_after_end = 0
    cursor = None
    for page in range(10000):
        params = {"symbol":"BTCUSDT","limit":limit}
        params.update({"startTime":start,"endTime":end-1} if cursor is None else {"fromId":cursor})
        response = client.get("https://fapi.binance.com/fapi/v1/aggTrades",params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload,list):
            raise ValueError("Unexpected REST payload")
        path = root/f"{start}-{end}-page-{page:05d}.json"
        path.write_bytes(response.content)
        files.append({"file":path.name,"sha256":sha256(path)})
        if not payload:
            break
        for raw in payload:
            parsed = parse_record(raw)
            if parsed.timestamp < start:
                raise ValueError("REST returned trades preceding requested start")
            if parsed.timestamp >= end:
                outside_after_end += 1
            else:
                rows.append(raw)
        next_cursor = int(payload[-1]["a"])+1
        if cursor is not None and next_cursor <= cursor:
            raise ValueError("REST pagination did not advance")
        if int(payload[-1]["T"]) >= end or len(payload) < limit:
            break
        cursor = next_cursor
    else:
        raise ValueError("REST page bound reached; coverage incomplete")
    trades,report = inspect_records(rows,start,end)
    report.update(method="REST",raw_pages=files,official_checksum_available=False,
                  page_records_after_end_excluded=outside_after_end,
                  coverage_basis="Successful bounded REST pagination; observed edges and ID continuity only")
    write_json(root/f"{start}-{end}-integrity.json",report)
    if not report["passed"]:
        raise ValueError("REST trade integrity failed")
    return trades,report


def fetch_rest(start,end,raw_dir,client,limit=1000):
    try:
        return _fetch_rest(start,end,raw_dir,client,limit)
    except Exception as exc:
        root = Path(raw_dir)
        root.mkdir(parents=True,exist_ok=True)
        path = root/f"{start}-{end}-integrity.json"
        existing = json.loads(path.read_text()) if path.exists() else {}
        write_json(path,{**existing,"passed":False,"status":"FAIL","error":str(exc),
                         "requested_start":start,"requested_end":end,"method":"REST"})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start",required=True,help="UTC date, inclusive")
    parser.add_argument("--end",required=True,help="UTC date, exclusive")
    parser.add_argument("--raw-dir",type=Path,default=Path("../data/raw/binance/aggTrades"))
    parser.add_argument("--normalized-dir",type=Path,default=Path("../data/processed/aggTrades"))
    args = parser.parse_args()
    manifest = acquire_days(args.start,args.end,args.raw_dir,args.normalized_dir)
    print(json.dumps({k:manifest[k] for k in ("start","end","trade_count","passed")},indent=2))


if __name__ == "__main__":
    main()
