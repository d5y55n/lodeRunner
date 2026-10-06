"""Remove unused precomputed catalog rows, without changing any member index."""
import json
import pandas as pd
from app.fullmap.run import CONFIGS
from app.research.models import identity
from app.market.aggregate_trades import sha256,write_json
from .history import ROOT
from .storage import unpack


def main():
    records=[]
    for phase in ['development','replication']:
        folder=ROOT/phase;seen_ids=set()
        for stage,configs in [('A',CONFIGS[:1]),('BC',CONFIGS[1:5])]:
            if not (folder/(stage+'-complete.json')).exists():raise ValueError('Generation incomplete')
            used=set()
            for config in configs:
                for path in sorted((folder/identity(config)[:12]).glob('*-membership.parquet')):
                    for blob in pd.read_parquet(path,columns=['added']).added:used.update(map(int,unpack(blob)))
            path=folder/('catalog-'+stage)/'candidate-catalog.parquet';frame=pd.read_parquet(path)
            if not used.issubset(set(frame.candidate_index)):raise ValueError('Missing candidate catalog rows')
            chosen=frame[frame.candidate_index.isin(used)].sort_values('candidate_index')
            if not chosen.candidate_id.is_unique or seen_ids.intersection(chosen.candidate_id):raise ValueError('Duplicate phase catalog identity')
            seen_ids.update(chosen.candidate_id)
            old_sha=sha256(path);tmp=path.with_suffix('.tmp.parquet');chosen.to_parquet(tmp,index=False,compression='zstd');tmp.replace(path)
            records.append(dict(phase=phase,stage=stage,before_rows=len(frame),used_rows=len(chosen),
                before_sha256=old_sha,after_sha256=sha256(path),index_mapping_unchanged=True))
    write_json(ROOT/'catalog-compaction.json',dict(status='PASS',catalogs=records,
        semantics='One row per used candidate within each phase; disjoint A and BC catalogs. Cross-phase catalogs are self-contained and retain original shared SHA identities. Membership indices are never renumbered.'))
    print('CATALOG_COMPACTION',json.dumps(records),flush=True)


if __name__=='__main__':main()
