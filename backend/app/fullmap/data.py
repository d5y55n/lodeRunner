"""Read verified, explicitly enumerated pre-2023 sources without changing them."""
import json
import time
import pandas as pd
from app.market.aggregate_trades import sha256,write_json
from app.market.models import Candle as MarketCandle
from app.research.data import from_market
from app.research.models import identity
from app.research.phase3_engine import load_coverage
from app.research.phase3_storage import connect,literal
from .contract import ROOT,SOURCE
from .acquire import WARM,MONTHS


def load_sources():
    warm=json.loads((WARM/'coverage.json').read_text())
    old=load_coverage(SOURCE)
    if not warm['ready']:raise ValueError('Warm-up coverage unresolved')
    months=MONTHS+list(pd.date_range('2021-01-01','2022-12-01',freq='MS').strftime('%Y-%m'))
    sources=[];candles=[];profiles=[]
    for month in months:
        root=WARM if month in MONTHS else SOURCE
        for kind in ['klines','aggTrades']:
            report_path=root/'integrity'/f'{month}-{kind}.json'
            report=json.loads(report_path.read_text())
            if not report['passed']:raise ValueError(f'Invalid source: {report_path}')
            path=root/('candles' if kind=='klines' else 'profiles')/f'{month}.parquet'
            expected=report['normalized_sha256' if kind=='klines' else 'profile_sha256']
            if sha256(path)!=expected:raise ValueError(f'Changed normalized source: {path}')
            if kind=='aggTrades':
                coverage=warm if root==WARM else old
                key='profile_hashes' if root==WARM else 'source_profile_hashes'
                if coverage[key][month]!=expected or coverage['source_hashes'][month]!=report['sha256']:
                    raise ValueError('Source differs from outcome-blind coverage decision')
                profiles.append(path)
            else:candles.append(pd.read_parquet(path))
            sources.append(dict(month=month,kind=kind,path=str(path),sha256=expected,
                integrity_report_sha256=sha256(report_path),raw_source_sha256=report['sha256']))
    market=pd.concat(candles,ignore_index=True)
    cs=from_market([MarketCandle(**r) for r in market.drop(columns='ignore').to_dict('records')],'BTCUSDT','1h')
    bad=sorted({tuple(x) for x in warm['quarantine_intervals']+old['quarantine_intervals'] if x[0]<1672531200000})
    lineage=dict(sources=sources,warmup_coverage_sha256=sha256(WARM/'coverage.json'),
        previous_coverage_id=old['coverage_id'],quarantine_intervals=bad,
        history_start=cs[0].start,history_end=cs[-1].end,candle_count=len(cs),
        warmup_aggregate_rows=warm['aggregate_rows'],no_2023_market_files_read=True,no_2024_access=True)
    write_json(ROOT/'source-lineage.json',lineage)
    return cs,profiles,bad,lineage


def hourly_bins(paths,width,lineage):
    dest=ROOT/'derived';dest.mkdir(exist_ok=True)
    path=dest/f'hourly-bins-{width}.parquet';manifest=dest/f'hourly-bins-{width}.json'
    key=identity([lineage['sources'],width,'floor half-open quantity buy sell; sorted serial sum v2'])
    before=time.perf_counter()
    if path.exists() and manifest.exists():
        old=json.loads(manifest.read_text())
        if old['input_id']==key and old['sha256']==sha256(path):
            return pd.read_parquet(path),dict(old,reused=True,load_seconds=time.perf_counter()-before)
    con=connect(dest)
    try:
        con.execute('SET threads=1')
        parts=[]
        for source_path in paths:
            part=dest/f'{source_path.stem}-bins-{width}.parquet'
            con.execute(f"COPY (SELECT hour,CAST(floor(price/{width}) AS BIGINT) AS bin,"
                f"sum(quantity) AS quantity,sum(buy) AS buy,sum(sell) AS sell "
                f"FROM (SELECT * FROM read_parquet({literal(source_path)}) ORDER BY hour,price) "
                f"GROUP BY hour,bin ORDER BY hour,bin) "
                f"TO {literal(part)} (FORMAT PARQUET,COMPRESSION ZSTD)")
            parts.append(part)
        source='['+','.join(literal(p) for p in parts)+']'
        con.execute(f"COPY (SELECT * FROM read_parquet({source}) ORDER BY hour,bin) TO {literal(path)} (FORMAT PARQUET,COMPRESSION ZSTD)")
    finally:con.close()
    info=dict(input_id=key,sha256=sha256(path),bin_width=width,interval='[floor(price/width)*width,(floor(price/width)+1)*width)',
        source='verified exact observed-price profiles; never candle volume',seconds=time.perf_counter()-before,bytes=path.stat().st_size,reused=False)
    write_json(manifest,info)
    return pd.read_parquet(path),info
