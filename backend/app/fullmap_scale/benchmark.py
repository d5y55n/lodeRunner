"""Performance/storage gate: 1,000 timestamps, five directional configurations."""
import json
import time
import pandas as pd
from app.fullmap.contract import HOUR,LOOKBACK
from app.fullmap.run import CONFIGS,peak_memory
from app.research.phase3_profiles import Profiles
from app.research.phase3_engine import load_coverage
from app.market.aggregate_trades import write_json,sha256
from .history import ROOT,SOURCE,load_prices
from .engine import Engine
from .storage import Stream,catalog
from .explanatory import Crossings


def assert_gate():
    gate=json.loads((ROOT/'parity-gate.json').read_text())
    if gate['status']!='PASS':raise ValueError('Parity gate failed')
    path=__import__('pathlib').Path(__file__).parent/'engine.py'
    if sha256(path)!=gate['source_sha256']['engine.py']:raise ValueError('Engine changed since parity gate')


def main():
    assert_gate();dest=ROOT/'benchmark';dest.mkdir(exist_ok=True)
    engine_digest=sha256(__import__('pathlib').Path(__file__).parent/'engine.py')
    before=time.perf_counter();cs=load_prices();engine=Engine(cs);crossings=Crossings(engine)
    bad=load_coverage(SOURCE)['quarantine_intervals'];profile=Profiles(SOURCE/'profiles',bad)
    start=cs[0].start+LOOKBACK;count=1000
    writers={str(i):Stream(dest/str(i)) for i in range(5)}
    init=time.perf_counter()-before;tick=time.perf_counter()
    for k in range(count):
        t=start+k*HOUR
        for i,(name,params) in enumerate(CONFIGS[:5]):
            snapshot,_,members=engine.snapshot(t,name,params,profile)
            extra=crossings.features(members,t,snapshot['decision_price']) if name=='A' else None
            writers[str(i)].add(snapshot,members,extra)
        if (k+1)%100==0:print('BENCHMARK',k+1,round(time.perf_counter()-tick,2),flush=True)
    for w in writers.values():w.flush()
    catalog(dest,engine)
    elapsed=time.perf_counter()-tick;size=sum(p.stat().st_size for p in dest.rglob('*.parquet'))
    n=(1704067200000-start)//HOUR
    result=dict(status='PASS',timestamps=count,directional_snapshots=count*5,initialization_seconds=init,
        seconds_per_1000_timestamps=elapsed,peak_RAM_bytes=peak_memory(),bytes_per_1000_timestamps=size,
        full_run_timestamps=n,projected_seconds=init+elapsed*n/count,projected_bytes=size*n/count,
        projection_scope='A/B/C states, catalog, membership and A crossing features; separate D/outcome/statistics work not included',
        engine_sha256=engine_digest,semantics_unchanged=True,no_strategy_outcomes_examined=True)
    write_json(ROOT/'benchmark-gate.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
