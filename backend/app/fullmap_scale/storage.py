"""Daily streaming tables and deterministic catalog-index membership deltas."""
import zlib
import numpy as np
import pandas as pd
from app.research.models import canonical


def pack(values):
    return zlib.compress(np.asarray(values,dtype='<u4').tobytes(),level=6)


def unpack(blob):
    return np.frombuffer(zlib.decompress(blob),dtype='<u4')


class Stream:
    def __init__(self,directory):
        self.directory=directory;directory.mkdir(parents=True,exist_ok=True)
        self.day=None;self.rows=[];self.memberships=[];self.prior=None;self.count=0

    def add(self,snapshot,members,extra=None):
        day=pd.Timestamp(snapshot['decision_timestamp'],unit='ms',tz='UTC').strftime('%Y-%m-%d')
        if self.day!=day:
            self.flush();self.day=day;self.prior=None
        current=np.sort(np.asarray(members,dtype=np.uint32))
        added=current if self.prior is None else np.setdiff1d(current,self.prior,assume_unique=True)
        removed=[] if self.prior is None else np.setdiff1d(self.prior,current,assume_unique=True)
        self.memberships.append(dict(snapshot_id=snapshot['snapshot_id'],timestamp=snapshot['decision_timestamp'],
            checkpoint=self.prior is None,added=pack(added),removed=pack(removed)))
        self.prior=current
        raw={k:v for k,v in snapshot['raw'].items() if k!='nearby_candidate_ids'}
        row={k:v for k,v in snapshot.items() if k not in ['known_candidate_ids','contributing_candidate_ids','raw']}
        row['raw']=raw;row['extra']=extra or {}
        self.rows.append({k:canonical(v) if isinstance(v,(dict,list)) else v for k,v in row.items()})
        self.count+=1

    def flush(self):
        if self.rows:
            pd.DataFrame(self.rows).to_parquet(self.directory/f'{self.day}-states.parquet',index=False,compression='zstd')
            pd.DataFrame(self.memberships).to_parquet(self.directory/f'{self.day}-membership.parquet',index=False,compression='zstd')
            self.rows=[];self.memberships=[]


def catalog(directory,engine):
    rows=[{k:canonical(v) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()} for r in engine.catalog]
    pd.DataFrame(rows).to_parquet(directory/'candidate-catalog.parquet',index=False,compression='zstd')


def restore(frame):
    members=set()
    for row in frame.itertuples():
        if row.checkpoint:members=set()
        members.difference_update(map(int,unpack(row.removed)));members.update(map(int,unpack(row.added)))
        yield row.snapshot_id,np.asarray(sorted(members),dtype=np.uint32)
