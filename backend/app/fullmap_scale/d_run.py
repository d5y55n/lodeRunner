"""Observed D history and compact summaries; incomplete windows never rank."""
import argparse
import json
import time
import numpy as np
import pandas as pd
from app.fullmap.contract import HOUR,LOOKBACK
from app.market.aggregate_trades import write_json,sha256
from app.research.models import identity
from app.research.phase3_storage import connect,literal
from app.research.phase3_engine import load_coverage
from .history import ROOT,HISTORY,REFERENCE,SOURCE,MONTHS,load_prices
from .vap import FastVAP


def inputs(replication=False):
    if replication and not (ROOT/'development-freeze.json').exists():raise ValueError('Freeze development first')
    coverage=json.loads((HISTORY/'trade-coverage.json').read_text());warm=json.loads((REFERENCE/'warmup/coverage.json').read_text());old=load_coverage(SOURCE)
    if not coverage['ready'] or not warm['ready']:raise ValueError('Unresolved trade coverage')
    items=[(HISTORY,'2019-12',coverage)]+[(HISTORY,m,coverage) for m in MONTHS]
    items +=[(REFERENCE/'warmup',f'2020-{m:02d}',warm) for m in range(9,13)]
    items +=[(SOURCE,f'{y}-{m:02d}',old) for y in range(2021,2024 if replication else 2023) for m in range(1,13)]
    paths=[];sources=[]
    for root,month,cov in items:
        report=json.loads((root/'integrity'/f'{month}-aggTrades.json').read_text());path=root/'profiles'/f'{month}.parquet'
        key='source_profile_hashes' if root==SOURCE else 'profile_hashes'
        if not report['passed'] or sha256(path)!=report['profile_sha256'] or cov[key][month]!=report['profile_sha256'] or cov['source_hashes'][month]!=report['sha256']:
            raise ValueError('Profile differs from adjudicated source')
        paths.append(path);sources.append(dict(month=month,path=str(path),sha256=report['profile_sha256']))
    bad=coverage['quarantine_intervals']+warm['quarantine_intervals']+old['quarantine_intervals']
    return paths,sources,sorted(bad)


def bins(paths,sources,width,phase):
    dest=ROOT/'derived';dest.mkdir(exist_ok=True);parts=[]
    con=connect(dest);con.execute('SET threads=1')
    try:
        for path,source in zip(paths,sources):
            part=dest/f'{path.stem}-bins-{width}.parquet';meta=dest/f'{path.stem}-bins-{width}.json'
            key=identity([source,width,'sorted serial sum v2'])
            ready=False
            if meta.exists() and part.exists():
                m=json.loads(meta.read_text());ready=m['input_id']==key and m['sha256']==sha256(part)
            if not ready:
                con.execute(f"COPY (SELECT hour,CAST(floor(price/{width}) AS BIGINT) AS bin,sum(quantity) AS quantity,sum(buy) AS buy,sum(sell) AS sell "
                    f"FROM (SELECT * FROM read_parquet({literal(path)}) ORDER BY hour,price) GROUP BY hour,bin ORDER BY hour,bin) TO {literal(part)} (FORMAT PARQUET,COMPRESSION ZSTD)")
                write_json(meta,dict(input_id=key,sha256=sha256(part),source=source,bin_width=width))
            parts.append(part)
        return con.execute('SELECT * FROM read_parquet(['+','.join(literal(p) for p in parts)+']) ORDER BY hour,bin').fetchdf()
    finally:con.close()


def main(phase):
    before=time.perf_counter();paths,sources,bad=inputs(phase=='replication');cs=load_prices(phase=='replication')
    start=cs[0].start+LOOKBACK if phase=='development' else 1672531200000
    end=1672531200000 if phase=='development' else 1704067200000
    prices={c.end:c.close for c in cs};dest=ROOT/phase/'D';dest.mkdir(parents=True,exist_ok=True)
    temporal_start=1577750400000+LOOKBACK;summary=[]
    for width in [50,100]:
        frame=bins(paths,sources,width,phase);engine=FastVAP(frame,width,quarantines=bad)
        rows=[];day=None;count=0;eligible=0;missing=0
        for t in range(start,end,HOUR):
            current=pd.Timestamp(t,unit='ms',tz='UTC').strftime('%Y-%m-%d')
            if day is not None and current!=day:
                pd.DataFrame(rows).to_parquet(dest/f'{width}-{day}.parquet',index=False,compression='zstd');rows=[]
            day=current
            if t<temporal_start:
                rows.append(dict(timestamp=t,price=prices[t],bin_width=width,status='INSUFFICIENT_850_DAY_TRADE_HISTORY',eligible=False));missing+=1;continue
            snap,_=engine.snapshot(t,prices[t]);v=snap['volume'];eligible+=int(v['eligible_complete_coverage_comparison']);count+=1
            rows.append(dict(timestamp=t,price=prices[t],bin_width=width,snapshot_id=snap['snapshot_id'],
                lookback_start=t-LOOKBACK,lookback_end=t,status=v['coverage_status'],eligible=v['eligible_complete_coverage_comparison'],
                occupied_bins=snap['known_candidate_count'],concentration_bins=snap['raw']['concentration_region_count'],
                **{k:v[k] for k in ['total_quantity','buy','sell','delta','above_quantity','below_quantity','straddling_quantity','concentrated_above_quantity','concentrated_below_quantity']}))
            if count%2000==0:print('D_OBSERVED',phase,width,count,flush=True)
        if rows:pd.DataFrame(rows).to_parquet(dest/f'{width}-{day}.parquet',index=False,compression='zstd')
        summary.append(dict(bin_width=width,observed_maps=count,insufficient_history=missing,eligible_complete_coverage=eligible))
    write_json(dest/'complete.json',dict(status='COMPLETE_OBSERVED_ONLY',phase=phase,summary=summary,source_profiles=sources,
        quarantine_intervals=bad,earliest_temporally_complete_window=temporal_start,
        reconstruction='All verified per-hour bin inputs are retained under derived/. Seed FastVAP with exactly [T-850d,T) for an inspectable complete observed map; numeric tolerance as parity gate. No missing history is filled.',
        seconds=time.perf_counter()-before,no_D_predictive_comparison=True))
    print('D_COMPLETE',phase,summary,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['development','replication']);main(p.parse_args().phase)
