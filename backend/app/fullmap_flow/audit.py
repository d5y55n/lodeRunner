"""Read-only checks of prior artifacts and final ablation output contracts."""
from xml.etree import ElementTree
import numpy as np
import pandas as pd
from .common import *
from .analyze import outcome_arrays
from app.research.phase3_engine import load_coverage

def main():
    freeze=check_freeze();old=read(ROOT/'preserved-before.json')
    for rel,digest in old.items():
        if sha256(PROJECT/rel)!=digest:raise ValueError(f'Prior artifact changed: {rel}')
    counts={};models=0;quarantines=load_coverage(SOURCE)['quarantine_intervals']
    for phase in ['development','replication']:
        start,end=bounds(phase);info=read(ROOT/phase/'features-complete.json')
        events=pd.read_parquet(BASE/phase/'events.parquet')
        outcomes=pd.concat([pd.read_parquet(p) for p in sorted((BASE/phase).glob('*-outcomes.parquet'))])
        outcome_arrays(events,outcomes)
        for month,digest in info['source_profile_sha256'].items():
            assert int(month[:4])<2024 and sha256(SOURCE/'profiles'/f'{month}.parquet')==digest
        for config in CONFIGS:
            ck=key(config)
            for hours in WINDOWS:
                folder=ROOT/phase/'analysis'/f'{ck}-{hours}h';f=pd.read_parquet(folder/'states.parquet')
                assert f.event_id.tolist()==events.event_id.tolist()
                assert f.timestamp.between(start,end-1).all()
                assert f.observation_end.eq(f.timestamp).all() and f.observation_start.eq(f.timestamp-hours*HOUR).all()
                expected=np.zeros(len(f),dtype=bool)
                for a,b in quarantines:expected|=(f.observation_start.to_numpy()<b)&(f.timestamp.to_numpy()>a)
                assert np.array_equal(f.status.eq('QUARANTINED').to_numpy(),expected)
                valid=f.status.eq('AVAILABLE')
                for side in ['support','resistance','joint']:
                    q,b,s=(f[side+'_'+x] for x in ['quantity','buy','sell'])
                    assert (q[valid]>=-1e-7).all() and np.allclose(q[valid],(b+s)[valid],rtol=1e-9,atol=1e-7)
                    assert np.allclose(f.loc[valid,side+'_delta'],(b-s)[valid])
                    assert q[~valid].isna().all()
                    positive=valid&q.gt(0)
                    assert np.allclose(f.loc[positive,side+'_normalized_delta'],((b-s)/q)[positive])
                    assert f.loc[valid&q.eq(0),side+'_normalized_delta'].isna().all()
                assert np.allclose(f.shared_quantity[valid],(f.support_quantity+f.resistance_quantity-f.joint_quantity)[valid])
                assert (f.shared_quantity[valid]>=-1e-7).all()
                assert (f.shared_quantity[valid]<=np.minimum(f.support_quantity,f.resistance_quantity)[valid]+1e-7).all()
                source=pd.read_parquet(BASE/phase/'analysis'/f'{ck}-state-features.parquet')
                for col in source.columns:
                    pd.testing.assert_series_equal(f[col],source[col],check_names=False)
                models+=1;counts[f'{phase}/{ck}/{hours}h']=dict(states=len(f),coverage_available=int(valid.sum()),
                    support_zero=int((valid&f.support_quantity.eq(0)).sum()),resistance_zero=int((valid&f.resistance_quantity.eq(0)).sum()))
        assert read(ROOT/phase/'analysis/complete.json')['status']=='COMPLETE'
    tests=ElementTree.parse(ROOT/'test-results.xml').getroot()[0].attrib
    assert tests['failures']==tests['errors']==tests['skipped']=='0'
    write_json(ROOT/'verification.json',dict(status='PASS',tests=tests,prior_artifacts_unchanged=len(old),
        flow_state_tables=models,counts=counts,freeze_id=freeze['freeze_id'],
        one_hour_parity_rows=sum(read(ROOT/p/'features-complete.json')['one_hour_parity_rows'] for p in ['development','replication']),
        outcome_join='same existing event/grid identity; source outcomes read-only',no_2024=True))
    print('AUDIT_PASS',len(old),'prior artifacts',models,'flow tables',flush=True)

if __name__=='__main__':main()
