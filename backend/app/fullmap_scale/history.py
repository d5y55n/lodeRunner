"""Authoritative prehistory discovery and price acquisition, before research."""
import json
import zipfile
import xml.etree.ElementTree as ET
import httpx
import numpy as np
import pandas as pd
from app.fullmap.contract import ROOT as REFERENCE,SOURCE,HOUR,LOOKBACK,permitted
from app.market.aggregate_trades import download_file,sha256,write_json
from app.market.phase3_archives import process_candles
from app.market.models import Candle as MarketCandle
from app.research.data import from_market
from app.research.models import identity
from app.research.phase3_engine import load_coverage

ROOT=REFERENCE.parent/'phase3r1'
HISTORY=ROOT/'history'
MONTHS=list(pd.date_range('2020-01-01','2020-08-01',freq='MS').strftime('%Y-%m'))
COLS=['open_time','open','high','low','close','volume','close_time','quote_volume','trade_count','taker_buy_volume','taker_buy_quote_volume','ignore']


def archive(period,kind,frequency='monthly',interval='1h'):
    if period[:4] not in ['2019','2020']:raise ValueError('Prehistory acquisition only')
    start=int(pd.Timestamp(period+'-01' if frequency=='monthly' else period,tz='UTC').timestamp()*1000)
    end=int((pd.Timestamp(start,unit='ms',tz='UTC')+(pd.offsets.MonthBegin() if frequency=='monthly' else pd.Timedelta(days=1))).timestamp()*1000)
    permitted(start,end)
    suffix='aggTrades' if kind=='aggTrades' else interval
    name=f'BTCUSDT-{suffix}-{period}.zip'
    route=f'aggTrades/BTCUSDT/{name}' if kind=='aggTrades' else f'klines/BTCUSDT/{interval}/{name}'
    url=f'https://data.binance.vision/data/futures/um/{frequency}/{route}'
    folder=HISTORY/'raw'/frequency/kind;folder.mkdir(parents=True,exist_ok=True)
    path=folder/name;checksum=folder/(name+'.CHECKSUM')
    with httpx.Client(timeout=180,follow_redirects=True) as c:
        download_file(c,url,path);download_file(c,url+'.CHECKSUM',checksum)
    parts=checksum.read_text().split();digest=sha256(path)
    if len(parts)!=2 or parts[0].lower()!=digest or parts[1].lstrip('*')!=name:raise ValueError('Official checksum mismatch')
    with zipfile.ZipFile(path) as z:
        if len(z.namelist())!=1 or z.testzip() is not None:raise ValueError('ZIP integrity failure')
    return path,dict(month=period[:7],kind=kind,start=start,end=end,url=url,sha256=digest,
        checksum_verified=True,zip_crc_verified=True,warmup_only=True)


def discovery():
    folder=HISTORY/'discovery';folder.mkdir(parents=True,exist_ok=True)
    records=[];ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
    with httpx.Client(timeout=60) as c:
        for frequency in ['monthly','daily']:
            for kind in ['klines','aggTrades']:
                for year in [2018,2019,2020]:
                    prefix=f'data/futures/um/{frequency}/{kind}/BTCUSDT/'+('1h/' if kind=='klines' else '')+f'BTCUSDT-'+('1h' if kind=='klines' else 'aggTrades')+f'-{year}'
                    r=c.get('https://s3-ap-northeast-1.amazonaws.com/data.binance.vision',params={'prefix':prefix,'max-keys':1000});r.raise_for_status()
                    path=folder/f'{frequency}-{kind}-{year}.xml';path.write_bytes(r.content)
                    tree=ET.fromstring(r.content)
                    if tree.find('s:IsTruncated',ns).text!='false':raise ValueError('Discovery pagination required')
                    keys=[e.find('s:Key',ns).text for e in tree.findall('s:Contents',ns)]
                    records.append(dict(url=str(r.url),sha256=sha256(path),keys=keys))
        params=dict(symbol='BTCUSDT',interval='1h',startTime=1546300800000,endTime=1577836799999,limit=3)
        r=c.get('https://fapi.binance.com/fapi/v1/klines',params=params);r.raise_for_status()
        write_json(folder/'earliest-price-rest.json',dict(url=str(r.url),response=r.json()))
        earliest=int(r.json()[0][0])
        r=c.get('https://fapi.binance.com/fapi/v1/aggTrades',params=dict(symbol='BTCUSDT',startTime=earliest,endTime=earliest+HOUR-1,limit=1))
        write_json(folder/'old-aggregate-rest.json',dict(url=str(r.url),status=r.status_code,response=r.json()))
    write_json(folder/'archive-index.json',records)
    return earliest


def price_history():
    (HISTORY/'integrity').mkdir(parents=True,exist_ok=True)
    (HISTORY/'candles').mkdir(exist_ok=True)
    earliest=discovery();rows=[];cursor=earliest;end=1577836800000;sources=[]
    # REST has no publisher checksum; save exact responses and local hashes,
    # independently verify the overlapping official December 31 daily archive.
    with httpx.Client(timeout=60) as client:
        while cursor<end:
            params=dict(symbol='BTCUSDT',interval='1h',startTime=cursor,endTime=end-1,limit=1500)
            response=client.get('https://fapi.binance.com/fapi/v1/klines',params=params);response.raise_for_status()
            path=HISTORY/'raw'/f'rest-1h-{cursor}.json';path.parent.mkdir(exist_ok=True)
            path.write_bytes(response.content);part=response.json()
            if not part or part[0][0]!=cursor:raise ValueError('REST candle gap')
            if any(r[0]>=end for r in part):raise ValueError('REST out-of-range data')
            sources.append(dict(url=str(response.url),sha256=sha256(path),official_checksum_available=False))
            rows.extend(part);cursor=int(part[-1][6])+1
    frame=pd.DataFrame(rows,columns=COLS)
    for col in COLS:frame[col]=pd.to_numeric(frame[col])
    from_market([MarketCandle(**r) for r in frame.drop(columns='ignore').to_dict('records')],'BTCUSDT','1h')
    if not np.array_equal(frame.open_time,np.arange(earliest,end,HOUR)):raise ValueError('REST chronology/coverage failure')
    daily,report=archive('2019-12-31','klines','daily')
    with zipfile.ZipFile(daily) as z:
        with z.open(z.namelist()[0]) as stream:other=pd.read_csv(stream,header=None,names=COLS)
    overlap=frame[frame.open_time>=report['start']].reset_index(drop=True)
    np.testing.assert_allclose(overlap[COLS[:-1]].to_numpy(),other[COLS[:-1]].to_numpy(),rtol=0,atol=0)
    path=HISTORY/'candles/2019-rest.parquet';frame.to_parquet(path,index=False)
    write_json(HISTORY/'integrity/2019-rest.json',dict(passed=True,start=earliest,end=end,rows=len(frame),
        normalized_sha256=sha256(path),sources=sources,official_daily_overlap=report,overlap_identical=True))
    for month in MONTHS:
        path=HISTORY/'integrity'/f'{month}-klines.json'
        if path.exists():
            report=json.loads(path.read_text())
            if report.get('passed') and sha256(HISTORY/'candles'/f'{month}.parquet')==report['normalized_sha256']:continue
        source,report=archive(month,'klines');process_candles(source,report,HISTORY);write_json(path,report)
        print('HISTORY_PRICE',month,report['rows'],flush=True)
    # Inspect the earliest officially archived aggregate records, not a launch-date assumption.
    source,report=archive('2019-12-31','aggTrades','daily')
    with zipfile.ZipFile(source) as z:
        with z.open(z.namelist()[0]) as stream:first=stream.readline().decode().strip().split(',')
    report['first_raw_record']=first;write_json(HISTORY/'integrity/earliest-aggregate-archive.json',report)
    old=load_coverage(SOURCE)
    write_json(ROOT/'availability.json',dict(status='PRICE_PREHISTORY_VERIFIED_TRADE_EXTENSION_PENDING',
        earliest_authoritative_price=earliest,earliest_850_day_price=earliest+LOOKBACK,
        earliest_archived_trade_day=report['start'],earliest_archived_trade_timestamp=int(first[5]),
        earliest_potential_850_day_archived_trade_window=report['start']+LOOKBACK,
        trade_window_completeness_not_yet_verified=True,existing_quarantines=old['quarantine_intervals'],
        pre_2024_D_complete_window_exists=False,
        D_reason='Every candidate window after trade archive availability and before 2024 intersects already established development/replication quarantines',
        no_2024_access=True,outcomes_used=False))
    print('HISTORY_PRICE_READY',pd.Timestamp(earliest+LOOKBACK,unit='ms',tz='UTC').isoformat(),flush=True)


def load_prices(replication=False):
    if replication and not (ROOT/'development-freeze.json').exists():raise ValueError('Development analysis must be frozen first')
    paths=[HISTORY/'candles/2019-rest.parquet']+[HISTORY/'candles'/f'{m}.parquet' for m in MONTHS]
    paths += [REFERENCE/'warmup/candles'/f'2020-{m:02d}.parquet' for m in range(9,13)]
    paths += [SOURCE/'candles'/f'{y}-{m:02d}.parquet' for y in range(2021,2024 if replication else 2023) for m in range(1,13)]
    for path in paths:
        root=path.parent.parent;month=path.stem
        report=root/'integrity'/('2019-rest.json' if month=='2019-rest' else f'{month}-klines.json')
        record=json.loads(report.read_text())
        if not record['passed'] or sha256(path)!=record['normalized_sha256']:raise ValueError(f'Changed price source {path}')
    frame=pd.concat([pd.read_parquet(p) for p in paths],ignore_index=True)
    cs=from_market([MarketCandle(**r) for r in frame.drop(columns='ignore').to_dict('records')],'BTCUSDT','1h')
    permitted(cs[0].start,cs[-1].end)
    return cs


if __name__=='__main__':price_history()
