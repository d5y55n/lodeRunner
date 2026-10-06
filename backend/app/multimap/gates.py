"""Real native parity before benchmarks; no old gate artifacts are rewritten."""
import argparse
import time
import pandas as pd
from app.fullmap_scale.gate import equivalent
from app.fullmap_scale.storage import Stream
from app.fullmap.run import peak_memory
from .contract import *
from .data import load
from .engine import Engine

def gate(tf):
    before=time.perf_counter();cs=load(tf);e=Engine(cs,tf);setup=time.perf_counter()-before
    start=cs[0].start+LOOKBACK;count=0
    # Include the first eligible window, intermediate history and the end of development.
    starts=[start,start+100*STEPS[tf],cs[-1].end-8*STEPS[tf]]
    for first in starts:
        for t in range(first,first+8*STEPS[tf],STEPS[tf]):
            for name,params in CONFIGS:
                s,m=e.snapshot(t,name,params);c,r,n=e.reference_snapshot(t,name,params)
                assert s['known_candidate_ids']==[x.id for x in c]
                equivalent(s['raw'],r);equivalent(s['native_score'],n)
                count+=1
    # A physically truncated input gives exactly the same candidate state at T.
    t=start+7*STEPS[tf];truncated=Engine([c for c in cs if c.end<=t],tf)
    for name,params in CONFIGS:
        a,_=e.snapshot(t,name,params);b,_=truncated.snapshot(t,name,params);equivalent(a,b)
    dest=ROOT/tf;dest.mkdir(exist_ok=True)
    code={p.name:sha256(p) for p in Path(__file__).parent.glob('*.py') if p.name in ['contract.py','engine.py','data.py']}
    write_json(dest/'parity.json',dict(status='PASS',snapshots=count,physical_truncations=5,initialization_seconds=setup,code=code))
    print('NATIVE_PARITY_PASS',tf,count,flush=True)
    if tf!='15m':return
    writers={identity(c):Stream(dest/'benchmark'/identity(c)[:12]) for c in CONFIGS}
    tick=time.perf_counter()
    for j in range(1000):
        for name,params in CONFIGS:
            s,m=e.snapshot(start+j*STEPS[tf],name,params);writers[identity((name,params))].add(s,m)
    for writer in writers.values():writer.flush()
    seconds=time.perf_counter()-tick;size=sum(p.stat().st_size for p in (dest/'benchmark').rglob('*') if p.is_file())
    states=(FINAL_START-start)//STEPS[tf]
    report=dict(status='PASS',timestamps=1000,map_snapshots=5000,initialization_seconds=setup,loop_seconds=seconds,
        peak_RAM_bytes=peak_memory(),output_bytes=size,projected_timestamps=states,
        projected_loop_seconds=seconds*states/1000,projected_membership_state_bytes=size*states/1000,
        scope='candidate/geometry/native score plus compact serialization; excludes labels, flow, crossing extras and statistical analysis',code=code)
    write_json(dest/'benchmark.json',report);print('NATIVE_BENCHMARK',report,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('timeframe',choices=list(HORIZONS));gate(p.parse_args().timeframe)
