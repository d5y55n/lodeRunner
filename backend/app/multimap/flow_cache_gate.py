"""Real-data parity against the already-written uncached development flow."""
import numpy as np
import pandas as pd
from .contract import *
from .flow import CachedProfiles15m,spans,measure_flow,SOURCE,load_coverage,restore


def run():
    root=ROOT/'15m/development'
    path=sorted((root/'flow').glob('*.parquet'))[0];expected=pd.read_parquet(path).set_index(['snapshot_id','native_flow_candles'])
    cat=pd.read_parquet(root/'candidate-catalog.parquet').set_index('candidate_index')
    prices=cat.price.to_numpy();kinds=cat.kind.to_numpy()
    coverage=load_coverage(SOURCE);profile=CachedProfiles15m();count=0
    for folder in sorted(root.iterdir()):
        state=folder/(path.stem+'-states.parquet')
        if not state.exists():continue
        rows=pd.read_parquet(state).to_dict('records')
        members=list(restore(pd.read_parquet(folder/(path.stem+'-membership.parquet'))))
        for s,(sid,idx) in zip(rows,members):
            intervals=spans(prices[idx],kinds[idx],s['decision_price'],WIDTHS['15m'])
            for w in FLOW_CANDLES['15m']:
                result=measure_flow(profile,'15m',s['decision_timestamp'],w,intervals,coverage['quarantine_intervals'])
                old=expected.loc[(sid,w)]
                for key,value in result.items():
                    if key=='native_flow_candles':continue
                    if isinstance(value,(int,float)):np.testing.assert_allclose(value,old[key],rtol=1e-12,atol=1e-8,equal_nan=True)
                    else:assert value==old[key]
                count+=1
    if not count:raise ValueError('Empty real-data gate')
    write_json(ROOT/'15m/flow-cache-parity.json',dict(status='PASS',rows=count,day=path.stem,
        uncached_file_sha256=sha256(path),new_code_sha256=sha256(Path(__file__).parent/'flow.py')))
    print('FLOW_CACHE_REAL_PARITY_PASS',count,flush=True)


if __name__=='__main__':run()
