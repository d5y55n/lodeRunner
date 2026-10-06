"""Streaming stage runner; replication requires the development-analysis seal."""
import argparse
from bisect import bisect_right
from dataclasses import asdict
from itertools import product
import json
import time
import pandas as pd
from app.fullmap.contract import HOUR,LOOKBACK
from app.fullmap.run import CONFIGS,peak_memory
from app.research.models import identity
from app.research.outcomes import measure
from app.research.phase3_profiles import Profiles
from app.research.phase3_engine import load_coverage
from app.market.aggregate_trades import sha256,write_json
from .history import ROOT,SOURCE,load_prices
from .engine import Engine
from .storage import Stream,catalog
from .explanatory import Crossings
from .benchmark import assert_gate


def run(phase,stage):
    assert_gate()
    benchmark=json.loads((ROOT/'benchmark-gate.json').read_text())
    if benchmark['status']!='PASS':raise ValueError('Benchmark gate required')
    if benchmark.get('engine_sha256')!=sha256(__import__('pathlib').Path(__file__).parent/'engine.py'):raise ValueError('Engine needs a matching benchmark')
    if phase not in ['development','replication'] or stage not in ['A','BC']:raise ValueError('Invalid stage')
    directory=ROOT/phase;directory.mkdir(exist_ok=True)
    if stage=='BC' and not (directory/'analysis/A-complete.json').exists():raise ValueError('Produce A analysis before B/C evaluation')
    if phase=='replication':
        freeze=json.loads((ROOT/'development-freeze.json').read_text())
        for name,digest in freeze['files'].items():
            if sha256(ROOT/name)!=digest:raise ValueError('Frozen development analysis changed')
        for name,digest in freeze['code'].items():
            if sha256(__import__('pathlib').Path(__file__).parent/name)!=digest:raise ValueError('Frozen research code changed')
    before=time.perf_counter();cs=load_prices(phase=='replication');engine=Engine(cs)
    bad=load_coverage(SOURCE)['quarantine_intervals'];profile=Profiles(SOURCE/'profiles',bad)
    cross=Crossings(engine);start=cs[0].start+LOOKBACK if phase=='development' else 1672531200000
    end=1672531200000 if phase=='development' else 1704067200000
    configs=CONFIGS[:1] if stage=='A' else CONFIGS[1:5]
    writers={identity([name,p]):Stream(directory/identity([name,p])[:12]) for name,p in configs}
    setup=time.perf_counter()-before;tick=time.perf_counter();labels=[];labelday=None;events=[]
    for step,t in enumerate(range(start,end,HOUR)):
        for name,params in configs:
            snap,_,members=engine.snapshot(t,name,params,profile)
            extra=cross.features(members,t,snap['decision_price']) if name=='A' else None
            writers[identity([name,params])].add(snap,members,extra)
        if stage=='A':
            day=pd.Timestamp(t,unit='ms',tz='UTC').strftime('%Y-%m-%d')
            if labelday is not None and day!=labelday:
                pd.DataFrame(labels).to_parquet(directory/f'{labelday}-outcomes.parquet',index=False,compression='zstd');labels=[]
            labelday=day;i=bisect_right(engine.reference.ends,t)
            events.append(dict(event_id=snap['event_id'],timestamp=t,price=snap['decision_price']))
            for direction,tp,sl,h in product(['LONG','SHORT'],[.003,.005],[.003,.005],[4,8,24]):
                labels.append(dict(event_id=snap['event_id'],outcome_id=identity([snap['event_id'],direction,tp,sl,h]),
                    **asdict(measure(snap['decision_price'],t,cs[i:i+h],direction,tp,sl,h))))
        if (step+1)%500==0:
            state=dict(phase=phase,stage=stage,completed=step+1,total=(end-start)//HOUR,elapsed_seconds=time.perf_counter()-tick)
            write_json(ROOT/'progress.json',state);print('SCALE',phase,stage,step+1,round(state['elapsed_seconds'],1),flush=True)
    for writer in writers.values():writer.flush()
    cat=directory/('catalog-'+stage);cat.mkdir(exist_ok=True);catalog(cat,engine)
    if labels:pd.DataFrame(labels).to_parquet(directory/f'{labelday}-outcomes.parquet',index=False,compression='zstd')
    if events:pd.DataFrame(events).to_parquet(directory/'events.parquet',index=False)
    result=dict(status='COMPLETE',phase=phase,stage=stage,timestamps=(end-start)//HOUR,
        start=start,end_exclusive=end,configs=configs,initialization_seconds=setup,loop_seconds=time.perf_counter()-tick,
        peak_RAM_bytes=peak_memory(),candidate_catalog_rows=len(engine.catalog),
        phase_label='primary development' if phase=='development' else 'previously inspected replication period',
        no_2024_access=True)
    write_json(directory/(stage+'-complete.json'),result);print('STAGE_COMPLETE',json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['development','replication']);parser.add_argument('stage',choices=['A','BC'])
    args=parser.parse_args();run(args.phase,args.stage)
