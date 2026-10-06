import hashlib
import io
import json
import zipfile
import httpx
import pytest
from app.market.aggregate_trades import parse_record, inspect_records, acquire_day, fetch_rest


def row(i=1,t=100,p="100",q="2",maker="false"):
    return [str(i),p,q,str(i*2),str(i*2+1),str(t),maker]


def test_archive_parsing_preserves_constituent_ids():
    t = parse_record(row())
    assert (t.id,t.price,t.quantity,t.timestamp,t.buyer_is_maker,t.first_trade_id,t.last_trade_id) == ("1",100,2,100,False,2,3)


def test_rest_parsing_and_optional_ids():
    assert parse_record({"a":1,"p":"100","q":"2","T":100,"m":True}).first_trade_id is None


@pytest.mark.parametrize("index,value",[(0,"1.5"),(1,"0"),(1,"nan"),(1,"inf"),(2,"-1"),(2,"0"),(5,"-1"),(5,"100.2"),(6,"1")])
def test_invalid_trade_fields(index,value):
    r = row()
    r[index] = value
    with pytest.raises(ValueError):
        parse_record(r)


def test_duplicate_records_and_duplicate_ids_not_repaired():
    trades,r = inspect_records([row(),row(),row(p="101")],0,1000)
    assert len(trades) == 3
    assert r["duplicate_aggregate_ids"] == 2 and r["duplicate_records"] == 1 and not r["passed"]


def test_ordering_and_discontinuities_detected():
    _,r = inspect_records([row(1,100),row(3,200),row(2,150)],0,1000)
    assert not r["passed"] and r["out_of_order"] == 1 and r["aggregate_id_discontinuities"] == 2


def test_wrong_timestamp_unit_and_coverage_report():
    _,r = inspect_records([row(1,1704067200000000)],1704067200000,1704153600000)
    assert r["timestamp_out_of_range"] == 1 and not r["passed"]
    _,good = inspect_records([row(1,10),row(2,990)],0,1000)
    assert good["passed"] and good["leading_boundary_distance_ms"] == 10
    assert good["trailing_boundary_distance_ms"] == 10


def zipped(rows):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream,"w") as z:
        z.writestr("trades.csv","agg_trade_id,price,quantity,first_trade_id,last_trade_id,transact_time,is_buyer_maker\n"+
                   "\n".join(",".join(r) for r in rows))
    return stream.getvalue()


@pytest.mark.parametrize("bad_checksum",[False,True])
def test_official_checksum_and_archive_report(tmp_path,bad_checksum):
    body = zipped([row(1,1704067200001),row(2,1704067200002)])
    filename = "BTCUSDT-aggTrades-2024-01-01.zip"
    checksum = "0"*64 if bad_checksum else hashlib.sha256(body).hexdigest()
    def response(request):
        return httpx.Response(200,content=(f"{checksum}  {filename}\n".encode() if str(request.url).endswith(".CHECKSUM") else body))
    with httpx.Client(transport=httpx.MockTransport(response)) as client:
        if bad_checksum:
            with pytest.raises(ValueError,match="SHA256"):
                acquire_day("2024-01-01",tmp_path,client=client)
        else:
            trades,r = acquire_day("2024-01-01",tmp_path,client=client)
            assert len(trades) == 2 and r["checksum_match"] and r["passed"]
    report = json.loads((tmp_path/(filename+".integrity.json")).read_text())
    assert report["passed"] != bad_checksum
    assert (tmp_path/filename).read_bytes() == body


def test_archive_integrity_failure_preserves_raw_and_report(tmp_path):
    body = zipped([row(1,1704067200001),row(3,1704067200002)])
    filename = "BTCUSDT-aggTrades-2024-01-01.zip"
    def response(request):
        return httpx.Response(200,content=(f"{hashlib.sha256(body).hexdigest()}  {filename}".encode()
                                          if str(request.url).endswith(".CHECKSUM") else body))
    with httpx.Client(transport=httpx.MockTransport(response)) as client:
        with pytest.raises(ValueError,match="integrity"):
            acquire_day("2024-01-01",tmp_path,client=client)
    report = json.loads((tmp_path/(filename+".integrity.json")).read_text())
    assert report["aggregate_id_discontinuities"] == 1 and not report["passed"]


def test_rest_pagination_raw_pages_and_local_hash(tmp_path):
    def response(request):
        start = 3 if "fromId" in request.url.params else 1
        data = [{"a":i,"p":"100","q":"1","T":i*100,"m":False,"f":i,"l":i} for i in range(start,start+2)]
        return httpx.Response(200,json=data)
    with httpx.Client(transport=httpx.MockTransport(response)) as client:
        trades,r = fetch_rest(0,350,tmp_path,client,limit=2)
    assert [t.id for t in trades] == ["1","2","3"]
    assert len(r["raw_pages"]) == 2 and not r["official_checksum_available"]
    assert r["page_records_after_end_excluded"] == 1
    assert r["passed"]


def test_constituent_discontinuity_is_explicit_warning_not_silent_repair():
    b = row(2,200)
    b[3],b[4] = "5","6"
    trades,r = inspect_records([row(),b],0,1000)
    assert r["status"] == "PASS_WITH_WARNINGS" and r["constituent_id_discontinuities"] == 1
    assert trades[1].first_trade_id == 5


def test_rest_failure_writes_failed_integrity_report(tmp_path):
    with httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(500))) as client:
        with pytest.raises(httpx.HTTPStatusError):
            fetch_rest(0,1000,tmp_path,client)
    r = json.loads((tmp_path/"0-1000-integrity.json").read_text())
    assert not r["passed"] and r["status"] == "FAIL"
