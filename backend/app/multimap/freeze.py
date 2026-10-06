"""Fail-closed development review and immutable per-timeframe replication contract."""
import argparse
import numpy as np
import pandas as pd
from .contract import *
from .analyze import MAP_FIELDS, FLOW_FIELDS
from .run import key


def verify_files(root,manifest):
    for name,digest in manifest['hashes'].items():
        if sha256(root/name)!=digest:raise ValueError('Changed research artifact: '+str(root/name))


def review(tf):
    root=ROOT/tf/'development';analysis=root/'analysis'
    summaries={};manifest_hashes={}
    for filename in ['price-complete.json','flow-complete.json','crossings-complete.json']:
        record=read(root/filename);verify_files(root,record);manifest_hashes[filename]=sha256(root/filename)
    report=read(analysis/'complete.json');verify_files(analysis,report)
    if report['analysis_code_sha256']!=sha256(Path(__file__).parent/'analyze.py'):
        raise ValueError('Development analysis must use current code')
    model=read(analysis/'buckets.json')
    for name,params in CONFIGS:
        ck=key(name,params)
        for window in FLOW_CANDLES[tf]:
            fields=MAP_FIELDS+FLOW_FIELDS if window==1 else FLOW_FIELDS
            for field in fields:
                if f'{ck}/{window}/{field}' not in model:raise ValueError('Incomplete frozen features')
                p=analysis/f'{ck}-{window}-{field}.parquet'
                frame=pd.read_parquet(p)
                if not np.allclose(frame.complete+frame.censored,frame.state_count):raise ValueError('Censoring composition')
                if not np.allclose(frame[['TP_FIRST','SL_FIRST','NEITHER','AMBIGUOUS']].sum(axis=1),frame.complete):
                    raise ValueError('Outcome composition')
                if set(frame.horizon)!=set(HORIZONS[tf]):raise ValueError('Wrong native horizon grid')
                if field in FLOW_FIELDS:
                    for condition in ['imbalance','candidates_per_cluster']:
                        if not (analysis/f'{ck}-{window}-{field}-within-{condition}.parquet').exists():
                            raise ValueError('Missing map-conditioned flow analysis')
        baseline=pd.read_parquet(analysis/f'{ck}-baseline.parquet')
        pooled=baseline[baseline.period=='ALL']
        summaries[ck]=dict(complete_range=[int(pooled.complete.min()),int(pooled.complete.max())],
            ambiguous_rate_range=[float(pooled.ambiguous_rate.min()),float(pooled.ambiguous_rate.max())],
            tp_first_rate_range=[float(pooled.tp_first_rate.min()),float(pooled.tp_first_rate.max())],
            interpretation='All 24 grids retained; native daily ambiguity is not resolved artificially.')
    normalized=sorted((root/'normalized-with-flow').glob('*.parquet'))
    common=root/'native-states';common.mkdir(exist_ok=True);hashes={};times={}
    for path in normalized:
        f=pd.read_parquet(path).drop(columns='crossings_status')
        c=pd.read_parquet(root/'crossings'/path.name)
        f=f.merge(c,on='snapshot_id',validate='one_to_one',how='left')
        if not f.as_of.eq(f.decision_timestamp).all():raise ValueError('Causal contact join failed')
        if f.decision_timestamp.max()>=1672531200000:raise ValueError('Replication appeared in development')
        for cfg,rows in f.groupby('configuration_id'):times.setdefault(cfg,[]).extend(rows.decision_timestamp.tolist())
        target=common/path.name;f.to_parquet(target,index=False,compression='zstd');hashes[target.name]=sha256(target)
    first=read(ROOT/'candles'/tf/'development-coverage.json')['earliest_850_day_decision']
    expected=list(range(first,1672531200000,STEPS[tf]))
    if len(times)!=5 or any(sorted(t)!=expected for t in times.values()):raise ValueError('Native walk-forward holes')
    write_json(root/'native-states-complete.json',dict(hashes=hashes,status='COMPLETE',rows=len(expected)*5))
    result=dict(status='REVIEWED_NO_SELECTION',timeframe=tf,development_only=True,decision_count=len(expected),
        configuration_summaries=summaries,manifests=manifest_hashes,analysis_manifest_sha256=sha256(analysis/'complete.json'),
        no_parameter_selection=True,no_edge_claim=True,replication_label='previously inspected replication period',
        caveats=['Exploratory unadjusted multiple comparisons','Native daily outcomes are structural/context only',
                 'D is observed-only, not a complete 850-day trade map','Flow cells exclude unavailable/quarantined observations'])
    write_json(root/'development-review.json',result)
    return result


def freeze_all():
    # All development reviews finish before any replication gate is published.
    from .profile_coverage import audit
    audit('development')
    for tf in HORIZONS:review(tf)
    code={p.name:sha256(p) for p in Path(__file__).parent.glob('*.py')}
    for tf in HORIZONS:
        root=ROOT/tf
        contract=dict(plan=PLAN,timeframe=tf,code=code,
            bucket_sha256=sha256(root/'development/analysis/buckets.json'),
            review_sha256=sha256(root/'development/development-review.json'),
            analysis_manifest_sha256=sha256(root/'development/analysis/complete.json'))
        contract['freeze_id']=identity(contract)
        path=root/'development-freeze.json'
        if path.exists() and read(path)!=contract:raise ValueError('Cannot overwrite a frozen contract')
        write_json(path,contract)
        print('NATIVE_DEVELOPMENT_FROZEN',tf,contract['freeze_id'],flush=True)


def check(tf):
    r=read(ROOT/tf/'development-freeze.json')
    if identity({k:v for k,v in r.items() if k!='freeze_id'})!=r['freeze_id']:raise ValueError('Freeze tampered')
    for name,digest in r['code'].items():
        if sha256(Path(__file__).parent/name)!=digest:raise ValueError('Code changed after freeze')
    for name,field in [('analysis/buckets.json','bucket_sha256'),('development-review.json','review_sha256'),('analysis/complete.json','analysis_manifest_sha256')]:
        if sha256(ROOT/tf/'development'/name)!=r[field]:raise ValueError('Development definition changed')
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['review','freeze']);p.add_argument('--timeframe',choices=list(HORIZONS))
    a=p.parse_args()
    if a.action=='freeze':freeze_all()
    elif a.timeframe:review(a.timeframe)
    else:p.error('review requires --timeframe')
