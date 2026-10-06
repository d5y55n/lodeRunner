"""Official native candles with exact REST responses and SHA/CRC archive evidence."""
import argparse
import io
import time
import zipfile
import httpx
import numpy as np
import pandas as pd
from app.market.models import Candle as MarketCandle
from app.research.data import from_market
from .contract import *

COLS=['open_time','open','high','low','close','volume','close_time','quote_volume','trade_count','taker_buy_volume','taker_buy_quote_volume','ignore']

def fetch(client,url,path,params=None):
    if path.exists():return path.read_bytes()
    for attempt in range(4):
        try:
            r=client.get(url,params=params);r.raise_for_status();path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(r.content)
            return r.content
        except httpx.HTTPError:
            if attempt==3:raise
            time.sleep(2**attempt)

def validate(frame,tf,start=None,end=None):
    frame=frame.copy()
    for col in COLS:frame[col]=pd.to_numeric(frame[col],errors='raise')
    step=STEPS[tf]
    if frame.empty or frame.open_time.duplicated().any():raise ValueError('Missing/duplicate candles')
    if not np.array_equal(frame.open_time,np.arange(int(frame.open_time.iloc[0]),int(frame.open_time.iloc[-1])+step,step)):raise ValueError('Native chronological gap')
    if not frame.close_time.eq(frame.open_time+step-1).all() or (frame.open_time%step).any():raise ValueError('Candle boundaries differ from declared native clock')
    if start is not None and frame.open_time.iloc[0]!=start:raise ValueError('Coverage start gap')
    if end is not None and frame.close_time.iloc[-1]+1!=end:raise ValueError('Coverage end gap')
    permitted(int(frame.open_time.iloc[0]),int(frame.close_time.iloc[-1])+1)
    from_market([MarketCandle(**r) for r in frame.drop(columns='ignore').to_dict('records')],'BTCUSDT',tf)
    return frame

def archive(client,tf,period,frequency='monthly'):
    year=int(period[:4])
    if not 2019<=year<=2023:raise ValueError('Forbidden archive year')
    name=f'BTCUSDT-{tf}-{period}.zip';base=f'https://data.binance.vision/data/futures/um/{frequency}/klines/BTCUSDT/{tf}/'
    path=ROOT/'candles'/tf/'raw'/frequency/name
    raw=fetch(client,base+name,path);check=fetch(client,base+name+'.CHECKSUM',path.with_suffix('.zip.CHECKSUM')).decode().split()
    if len(check)!=2 or check[0].lower()!=sha256(path) or check[1].lstrip('*')!=name:raise ValueError('Official SHA mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.namelist())!=1:raise ValueError('CRC/member failure')
        content=z.read(z.namelist()[0]);header=0 if content.startswith(b'open_time') else None
        frame=pd.read_csv(io.BytesIO(content),header=header,names=COLS)
    return frame,dict(url=base+name,sha256=check[0],official_checksum=True,crc=True)

def acquire(tf,phase):
    initialize()
    if tf not in HORIZONS:raise ValueError('Existing 1h input is frozen')
    if phase=='replication' and not (ROOT/tf/'development-freeze.json').exists():raise ValueError('Freeze native development before 2023 acquisition')
    dest=ROOT/'candles'/tf;dest.mkdir(parents=True,exist_ok=True);sources=[]
    with httpx.Client(timeout=90,follow_redirects=True) as client:
        if phase=='development':
            probe=dict(symbol='BTCUSDT',interval=tf,startTime=1546300800000,endTime=1577836799999,limit=3)
            raw=fetch(client,'https://fapi.binance.com/fapi/v1/klines',dest/'raw/earliest.json',probe)
            earliest=int(json.loads(raw)[0][0]);cursor=earliest;parts=[];end=1577836800000
            while cursor<end:
                path=dest/'raw'/f'rest-{cursor}.json';params=dict(symbol='BTCUSDT',interval=tf,startTime=cursor,endTime=end-1,limit=1500)
                rows=json.loads(fetch(client,'https://fapi.binance.com/fapi/v1/klines',path,params))
                frame=validate(pd.DataFrame(rows,columns=COLS),tf,start=cursor)
                if frame.close_time.iloc[-1]>=end:raise ValueError('Out-of-range REST')
                sources.append(dict(path=str(path.relative_to(ROOT)),url='https://fapi.binance.com/fapi/v1/klines',params=params,sha256=sha256(path),official_checksum=False))
                parts.append(frame);cursor=int(frame.close_time.iloc[-1])+1
            pre=validate(pd.concat(parts,ignore_index=True),tf,start=earliest,end=end)
            overlap,proof=archive(client,tf,'2019-12-31','daily');overlap=validate(overlap,tf,start=1577750400000,end=end)
            np.testing.assert_allclose(pre[pre.open_time>=1577750400000][COLS[:-1]].to_numpy(),overlap[COLS[:-1]].to_numpy(),rtol=0,atol=0)
            pre.to_parquet(dest/'2019.parquet',index=False);sources.append(dict(rest_daily_overlap_exact=True,**proof))
            months=pd.date_range('2020-01-01','2022-12-01',freq='MS')
        else:months=pd.date_range('2023-01-01','2023-12-01',freq='MS')
        for date in months:
            month=date.strftime('%Y-%m');start=int(date.tz_localize('UTC').timestamp()*1000);end=int((date+pd.offsets.MonthBegin()).tz_localize('UTC').timestamp()*1000)
            frame,proof=archive(client,tf,month);frame=validate(frame,tf,start=start,end=end)
            path=dest/f'{month}.parquet';frame.to_parquet(path,index=False)
            sources.append(dict(month=month,normalized_sha256=sha256(path),rows=len(frame),**proof))
            print('NATIVE_CANDLES',tf,month,len(frame),flush=True)
    paths=sorted(dest.glob('*.parquet'));allowed=[p for p in paths if phase=='replication' or not p.name.startswith('2023')]
    frame=validate(pd.concat([pd.read_parquet(p) for p in allowed],ignore_index=True),tf)
    earliest=int(frame.open_time.iloc[0]);eligible=earliest+LOOKBACK
    report=dict(timeframe=tf,phase=phase,earliest_candle=earliest,earliest_850_day_decision=eligible,
        first_eligible_utc=pd.Timestamp(eligible,unit='ms',tz='UTC').isoformat(),source_count=len(sources),sources=sources,
        normalized={p.name:sha256(p) for p in allowed},rows=len(frame),coverage_end=int(frame.close_time.iloc[-1])+1,
        complete_contiguous=True,outcomes_examined=False,no_2024=True)
    write_json(dest/f'{phase}-coverage.json',report);print('COVERAGE_READY',tf,report['first_eligible_utc'],flush=True)

def load(tf,replication=False):
    report=read(ROOT/'candles'/tf/('replication-coverage.json' if replication else 'development-coverage.json'))
    frames=[]
    for name,digest in report['normalized'].items():
        path=ROOT/'candles'/tf/name
        if name.startswith('2024') or sha256(path)!=digest:raise ValueError('Forbidden or changed native candles')
        frames.append(pd.read_parquet(path))
    f=pd.concat(frames,ignore_index=True)
    return from_market([MarketCandle(**r) for r in f.drop(columns='ignore').to_dict('records')],'BTCUSDT',tf)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['development','replication']);p.add_argument('timeframe',choices=list(HORIZONS));a=p.parse_args();acquire(a.timeframe,a.phase)
