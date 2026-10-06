"""Independent saved-output membership, causality, freeze and preservation audit."""
from bisect import bisect_right
import heapq
import json
from pathlib import Path
from xml.etree import ElementTree
import numpy as np
import pandas as pd
from app.fullmap.contract import HOUR,LOOKBACK
from app.fullmap.core import FullMapEngine,contribution
from app.fullmap.run import CONFIGS
from app.research.models import identity
from app.research.phase3_profiles import Profiles
from app.research.phase3_engine import load_coverage
from app.research.runner import code_digest
from app.market.aggregate_trades import sha256,write_json
from .history import ROOT,HISTORY,REFERENCE,SOURCE,load_prices
from .storage import unpack
from .gate import equivalent


def main():
    seal=json.loads((ROOT/'development-freeze.json').read_text())
    for name,digest in seal['files'].items():
        if sha256(ROOT/name)!=digest:raise AssertionError('Frozen development table changed')
    for name,digest in seal['code'].items():
        if sha256(Path(__file__).parent/name)!=digest:raise AssertionError('Frozen research code changed')
    old=json.loads((REFERENCE/'run-results.json').read_text())
    for name,digest in old['artifact_hashes'].items():
        if sha256(REFERENCE/'sanity'/name)!=digest:raise AssertionError('Phase 3R reference export changed')
    original=json.loads((REFERENCE/'verification.json').read_text())
    for name,digest in original['source_code_sha256'].items():
        if sha256(Path(__file__).parent.parent/'fullmap'/name)!=digest:raise AssertionError('Phase 3R reference code changed')
    old_inventory=json.loads((REFERENCE/'preserved-before.json').read_text());project=ROOT.parent.parent
    for name,digest in old_inventory.items():
        if sha256(project/name)!=digest:raise AssertionError('Prior research artifact changed')
    if code_digest()!=old['old_research_code_digest']:raise AssertionError('Prior Phase 3 code changed')
    extra_coverage=json.loads((HISTORY/'trade-coverage.json').read_text())
    for name,digest in extra_coverage['forensic_hashes'].items():
        if sha256(HISTORY/'coverage'/name)!=digest:raise AssertionError('Additional trade forensic evidence changed')
    reference_lineage=json.loads((REFERENCE/'source-lineage.json').read_text())
    if sha256(REFERENCE/'warmup/coverage.json')!=reference_lineage['warmup_coverage_sha256']:raise AssertionError('Prior warm-up adjudication changed')
    cs=load_prices(True);reference=FullMapEngine(cs);profile=Profiles(SOURCE/'profiles',load_coverage(SOURCE)['quarantine_intervals'])
    sample_times={1641402000000,1648771200000,1656633600000,1664582400000,1672531200000,1680307200000,1688169600000,1696118400000,1704063600000}
    counters=dict(snapshot_rows=0,membership_updates=0,reference_reconstructions=0,outcome_rows=0,censored_rows=0)
    phases={}
    for phase in ['development','replication']:
        folder=ROOT/phase;event=pd.read_parquet(folder/'events.parquet');timestamps=dict(zip(event.event_id,event.timestamp))
        dmanifest=json.loads((folder/'D/complete.json').read_text())
        for item in dmanifest['source_profiles']:
            if item['month']>='2024-01':raise AssertionError('Forbidden source period')
            if sha256(Path(item['path']))!=item['sha256']:raise AssertionError('Normalized trade source changed')
        end=1672531200000 if phase=='development' else 1704067200000
        assert event.event_id.is_unique and event.timestamp.is_unique
        assert np.diff(event.timestamp).tolist()==[HOUR]*(len(event)-1)
        outcomes=pd.concat([pd.read_parquet(p) for p in sorted(folder.glob('*-outcomes.parquet'))],ignore_index=True)
        assert len(outcomes)==24*len(event) and outcomes.outcome_id.is_unique
        assert outcomes.groupby('event_id').size().eq(24).all()
        t=outcomes.event_id.map(timestamps);available=np.minimum(outcomes.horizon,(end-t)//HOUR)
        assert outcomes.observed_candles.eq(available).all()
        assert outcomes.censored.eq(available<outcomes.horizon).all()
        assert outcomes.measured_until.eq(t+available*HOUR).all() and outcomes.measured_until.le(end).all()
        counters['outcome_rows']+=len(outcomes);counters['censored_rows']+=int(outcomes.censored.sum())
        for name,params in CONFIGS[:5]:
            key=identity((name,params))[:12];stage='A' if name=='A' else 'BC'
            cat=pd.read_parquet(folder/('catalog-'+stage)/'candidate-catalog.parquet').set_index('candidate_index')
            cat=cat.reindex(range(int(cat.index.max())+1))
            dep=cat.dependency_start.fillna(-1).to_numpy(dtype=np.int64)
            known=cat.known_at.fillna(1704070800000).to_numpy(dtype=np.int64)
            kinds=cat.kind.fillna('UNUSED').to_numpy();prices=cat.price.to_numpy();ids=cat.candidate_id.to_numpy()
            seen=[]
            for path in sorted((folder/key).glob('*-states.parquet')):
                states=pd.read_parquet(path);members=pd.read_parquet(path.with_name(path.name.replace('-states','-membership')))
                assert states.snapshot_id.tolist()==members.snapshot_id.tolist()
                active=set();heap=[];supports=0
                for s,m in zip(states.to_dict('records'),members.itertuples()):
                    current=int(s['decision_timestamp']);adds=unpack(m.added).astype(np.int64);removes=unpack(m.removed).astype(np.int64)
                    if m.checkpoint:active=set();heap=[];supports=0
                    assert all(int(i) in active for i in removes)
                    active.difference_update(map(int,removes));supports-=int((kinds[removes]=='SUPPORT').sum())
                    assert not any(int(i) in active for i in adds)
                    assert np.all(known[adds]<=current) and np.all(dep[adds]>=current-LOOKBACK)
                    active.update(map(int,adds));supports+=int((kinds[adds]=='SUPPORT').sum())
                    for i in adds:heapq.heappush(heap,(int(dep[i]),int(i)))
                    while heap and heap[0][1] not in active:heapq.heappop(heap)
                    assert not heap or heap[0][0]>=current-LOOKBACK
                    assert len(active)==s['known_candidate_count'] and supports==s['support_count'] and len(active)-supports==s['resistance_count']
                    assert timestamps[s['event_id']]==current
                    seen.append(s['event_id']);counters['snapshot_rows']+=1;counters['membership_updates']+=len(adds)+len(removes)
                    if current in sample_times:
                        order=sorted(active,key=lambda i:(known[i],0 if kinds[i]=='RESISTANCE' else 1))
                        actual={k:v for k,v in s.items() if k!='extra'}
                        for k in ['detector_parameters','representations','native_score','raw','volume']:
                            actual[k]=json.loads(actual[k]) if isinstance(actual[k],str) else actual[k]
                        actual['known_candidate_ids']=[ids[i] for i in order]
                        contributing=[i for i in order if contribution(prices[i],s['decision_price'],.004)]
                        actual['contributing_candidate_ids']=[ids[i] for i in contributing] if name=='A' else []
                        actual['raw']['nearby_candidate_ids']=[ids[i] for kind in ['SUPPORT','RESISTANCE'] for i in contributing if kinds[i]==kind]
                        expected,_=reference.snapshot(current,name,params,profile);equivalent(actual,expected)
                        counters['reference_reconstructions']+=1
            assert seen==event.event_id.tolist()
        phases[phase]=dict(timestamps=len(event),start=int(event.timestamp.min()),end=int(event.timestamp.max()),outcomes=len(outcomes),censored=int(outcomes.censored.sum()))
        print('AUDITED',phase,flush=True)
    tests=ElementTree.parse(ROOT/'test-results.xml').getroot()[0].attrib
    assert tests['failures']==tests['errors']==tests['skipped']=='0'
    result=dict(status='PASS',counters=counters,phases=phases,tests=tests,old_artifacts_unchanged=len(old_inventory),
        old_Phase3R_export_hashes_unchanged=len(old['artifact_hashes']),development_freeze_unchanged=True,
        no_future_membership=True,no_2024_outcomes=True,replication_not_refit=True,
        source_sha256={p.name:sha256(p) for p in Path(__file__).parent.glob('*.py')})
    write_json(ROOT/'verification.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
