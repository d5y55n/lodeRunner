"""Causal post-confirmation contact summaries with bounded candidate cache."""
import argparse
import time
from collections import OrderedDict
from types import SimpleNamespace
import numpy as np
import pandas as pd
from app.fullmap_scale.explanatory import Crossings
from app.fullmap_scale.storage import restore
from .contract import *
from .data import load
from .run import key


class History(Crossings):
    def __init__(self, engine, capacity=4096):
        super().__init__(engine)
        self.cache=OrderedDict();self.capacity=capacity

    def history(self,index,t):
        result=super().history(index,t)
        self.cache.move_to_end(index)
        if len(self.cache)>self.capacity:self.cache.popitem(last=False)
        return result


def features(history, members, t, current, width):
    e=history.engine;prices=e.prices[members]
    full=(current<prices*(1+width))&(current>prices*(1-width))
    half=((current>=prices*(1+width))&(current<prices*(1+1.5*width)))|((current<=prices*(1-width))&(current>prices*(1-1.5*width)))
    nearby=members[full|half]
    if np.any(e.known[nearby]>t):raise ValueError('Unconfirmed candidate')
    values=[history.history(int(i),t) for i in nearby]
    contacts=[v[2] for v in values if v[2] is not None]
    return dict(mean_prior_crossings=float(np.mean([v[0] for v in values])) if values else None,
                mean_prior_visits=float(np.mean([v[1] for v in values])) if values else None,
                mean_hours_since_last_contact=float(np.mean(contacts)) if contacts else None,
                nearby_candidates=len(nearby),as_of=t,crossings_status='AVAILABLE')


def execute(tf,phase):
    dest=ROOT/tf/phase;proof=read(dest/'price-complete.json')
    cs=load(tf,replication=phase=='replication')
    cat_path=dest/'candidate-catalog.parquet'
    if sha256(cat_path)!=proof['hashes']['candidate-catalog.parquet']:raise ValueError('Catalog changed')
    cat=pd.read_parquet(cat_path).set_index('candidate_index')
    cat=cat.reindex(range(int(cat.index.max())+1))
    e=SimpleNamespace(known=cat.known_at.to_numpy(),prices=cat.price.to_numpy(),
        reference=SimpleNamespace(ends=[c.end for c in cs]),close=[c.close for c in cs],
        high=[c.high for c in cs],low=[c.low for c in cs])
    history=History(e);out=dest/'crossings';out.mkdir(exist_ok=True)
    before=time.perf_counter();count=0;hashes={}
    for day_i,p in enumerate(sorted((dest/'normalized').glob('*.parquet'))):
        rows=[]
        for name,params in CONFIGS:
            folder=dest/key(name,params)
            sp=folder/(p.stem+'-states.parquet');mp=folder/(p.stem+'-membership.parquet')
            for path in [sp,mp]:
                if sha256(path)!=proof['hashes'][str(path.relative_to(dest))]:raise ValueError('State changed')
            states=pd.read_parquet(sp).to_dict('records');members=list(restore(pd.read_parquet(mp)))
            if len(states)!=len(members):raise ValueError('Membership cardinality')
            for state,(sid,idx) in zip(states,members):
                assert sid==state['snapshot_id']
                rows.append(dict(snapshot_id=sid,**features(history,idx,state['decision_timestamp'],state['decision_price'],WIDTHS[tf])))
        target=out/p.name;pd.DataFrame(rows).to_parquet(target,index=False,compression='zstd')
        hashes[str(target.relative_to(dest))]=sha256(target);count+=len(rows)
        if (day_i+1)%30==0:print('CROSSINGS',tf,phase,day_i+1,flush=True)
    write_json(dest/'crossings-complete.json',dict(status='COMPLETE',rows=count,hashes=hashes,
        elapsed_seconds=time.perf_counter()-before,code_sha256=sha256(__file__),cache_capacity=4096,
        definitions='Strict closed-close crossing after known_at; visits are contact-run starts after known_at; query end <= T'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('timeframe',choices=list(HORIZONS))
    p.add_argument('phase',choices=['development','replication']);a=p.parse_args();execute(a.timeframe,a.phase)
