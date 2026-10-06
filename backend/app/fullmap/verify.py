"""Inspect saved decision facts independently of future outcome calculation."""
import json
import platform
from pathlib import Path
from xml.etree import ElementTree
import duckdb
import numpy as np
import pandas as pd
import pyarrow
from app.market.aggregate_trades import sha256,write_json
from app.research.runner import code_digest
from .contract import ROOT,SOURCE,HOUR,LOOKBACK
from .core import contribution
from .run import preserve_inventory


def main():
    dest=ROOT/'sanity';results=json.loads((ROOT/'run-results.json').read_text())
    for name,digest in results['artifact_hashes'].items():
        if sha256(dest/name)!=digest:raise AssertionError(f'Changed export: {name}')
    before=json.loads((ROOT/'preserved-before.json').read_text())
    if before!=preserve_inventory():raise AssertionError('Previous artifacts changed')
    lineage=json.loads((SOURCE.parent/'phase35/source-lineage.json').read_text())
    if code_digest()!=lineage['phase3_code_digest']:raise AssertionError('Frozen Phase 3 code changed')
    for name,digest in lineage['artifact_hashes'].items():
        if sha256(SOURCE/name)!=digest:raise AssertionError('Original Phase 3 completion artifact changed')
    snapshots=[json.loads(line) for line in (dest/'snapshots.jsonl').open(encoding='utf-8')]
    candidates={r['candidate_id']:r for r in (json.loads(line) for line in (dest/'candidates.jsonl').open(encoding='utf-8'))}
    events=pd.read_parquet(dest/'events.parquet');outcomes=pd.read_parquet(dest/'future-outcomes.parquet')
    assert len(snapshots)==168 and len({s['snapshot_id'] for s in snapshots})==168
    assert len(events)==events.event_id.nunique()==24
    assert set(outcomes.event_id)==set(events.event_id) and len(outcomes)==576
    assert outcomes.outcome_id.nunique()==576 and not outcomes.censored.any()
    assert events.decision_timestamp.tolist()==list(range(1672358400000,1672444800000,HOUR))
    joined=outcomes.merge(events,on='event_id',validate='many_to_one')
    assert (joined.measured_until==joined.decision_timestamp+joined.horizon*HOUR).all()
    assert (joined.measured_until<1672531200000).all()
    hits=joined[joined.first_hit_at.notna()]
    assert ((hits.first_hit_at>=hits.decision_timestamp)&(hits.first_hit_at<=hits.measured_until)).all()
    assert pd.Series([s['event_id'] for s in snapshots]).value_counts().eq(7).all()
    for snap in snapshots:
        t=snap['decision_timestamp'];assert snap['lookback_start']==t-LOOKBACK and snap['lookback_end']==t
        assert snap['event_id'] in set(events.event_id)
        assert len(set(snap['known_candidate_ids']))==snap['known_candidate_count']
        if snap['detector']!='A':assert snap['native_score'] is None
        if snap['detector']=='D':
            assert not snap['volume']['eligible_complete_coverage_comparison']
            continue
        members=[candidates[c] for c in snap['known_candidate_ids']]
        assert all(c['known_at']<=t and c['source_timestamp']>=t-LOOKBACK and c['dependency_start']>=t-LOOKBACK for c in members)
        for kind in ['support','resistance']:
            raw=snap['raw'][kind]
            assert raw['above']+raw['below']+raw['near']==raw['total']==sum(c['kind']==kind.upper() for c in members)
            assert sum(raw['density'].values())==raw['total']
        v=snap['volume'];assert v['observation_start']==t-HOUR and v['observation_end']==t
        assert v['status']=='AVAILABLE'
        assert v['joint']['quantity']<=v['support']['quantity']+v['resistance']['quantity']+1e-7
        if snap['detector']=='A':
            expected=sum((1 if c['kind']=='SUPPORT' else -1)*contribution(c['price'],snap['decision_price'],.004) for c in members)
            assert expected==snap['native_score']['long_score']==-snap['native_score']['short_score']
    bins=pd.read_parquet(dest/'d-bins.parquet')
    assert bins.kind.eq('NEUTRAL').all() and (bins.quantity>0).all()
    np.testing.assert_allclose(bins.quantity,bins.buy+bins.sell,rtol=1e-9,atol=1e-7)
    np.testing.assert_allclose(bins.delta,bins.buy-bins.sell,rtol=1e-10,atol=1e-7)
    junit=ElementTree.parse(ROOT/'test-results.xml').getroot()[0].attrib
    assert junit['failures']==junit['errors']==junit['skipped']=='0'
    source=Path(__file__).parent
    verification=dict(status='PASS',tests=junit,all_snapshot_contracts_checked=168,A_recomputed_scores=24,
        source_dependency_memberships_checked=sum(s['known_candidate_count'] for s in snapshots if s['detector']!='D'),
        D_bin_rows_checked=len(bins),all_outcome_events_aligned=True,prior_artifacts_unchanged=len(before),
        phase3_frozen_digest_unchanged=True,phase3_original_completion_hashes_unchanged=True,
        artifact_hashes_verified=len(results['artifact_hashes']),source_code_sha256={p.name:sha256(p) for p in sorted(source.glob('*.py'))},
        runtime=dict(python=platform.python_version(),platform=platform.platform(),pandas=pd.__version__,numpy=np.__version__,
                     duckdb=duckdb.__version__,pyarrow=pyarrow.__version__),
        no_2024_market_data_access=True,no_strategy_or_threshold_selected=True)
    write_json(ROOT/'verification.json',verification)
    print(json.dumps({k:v for k,v in verification.items() if k not in ['source_code_sha256','runtime']},indent=2))


if __name__=='__main__':main()
