"""Mandatory complete 24-state reference parity gate before scale execution."""
from bisect import bisect_right
from dataclasses import asdict
import json
import time
import numpy as np
import pandas as pd
from app.fullmap.contract import HOUR
from app.fullmap.run import CONFIGS,START,END,peak_memory
from .vap import FastVAP
from app.research.outcomes import measure
from app.research.phase3_profiles import Profiles
from app.research.phase3_engine import load_coverage
from app.market.aggregate_trades import write_json,sha256
from .history import ROOT,REFERENCE,SOURCE,load_prices
from .engine import Engine


def equivalent(actual,expected,path='root'):
    if isinstance(expected,dict):
        if set(actual)!=set(expected):raise AssertionError(f'{path}: different keys')
        for k in expected:equivalent(actual[k],expected[k],path+'.'+k)
    elif isinstance(expected,list):
        if len(actual)!=len(expected):raise AssertionError(f'{path}: length')
        for i,(a,b) in enumerate(zip(actual,expected)):equivalent(a,b,path+f'[{i}]')
    elif isinstance(expected,float):
        if not np.isclose(actual,expected,rtol=1e-12,atol=1e-12):raise AssertionError(f'{path}: {actual} != {expected}')
    elif actual!=expected:raise AssertionError(f'{path}: {actual} != {expected}')


def main():
    ROOT.mkdir(exist_ok=True);begin=time.perf_counter();cs=load_prices();engine=Engine(cs)
    bad=load_coverage(SOURCE)['quarantine_intervals'];profile=Profiles(SOURCE/'profiles',bad)
    rolling={w:FastVAP(pd.read_parquet(REFERENCE/'derived'/f'hourly-bins-{w}.parquet'),w,quarantines=bad) for w in [50,100]}
    initialization=time.perf_counter()-begin;states=[];tick=time.perf_counter()
    expected_bins=pd.read_parquet(REFERENCE/'sanity/d-bins.parquet')
    with (REFERENCE/'sanity/snapshots.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            expected=json.loads(line);t=expected['decision_timestamp'];params=expected['detector_parameters'];name=expected['detector']
            if name=='D':
                actual,bins=rolling[params['bin_size']].snapshot(t,expected['decision_price'])
                old=expected_bins[expected_bins.snapshot_id==actual['snapshot_id']].to_dict('records')
                equivalent(bins,old,'D bins')
            else:actual,_,_=engine.snapshot(t,name,params,profile)
            equivalent(actual,expected);states.append(actual)
    elapsed=time.perf_counter()-tick
    outcomes=0
    for line in (REFERENCE/'sanity/future-outcomes.jsonl').open(encoding='utf-8'):
        expected=json.loads(line);event=next(s for s in states if s['event_id']==expected['event_id'])
        t=event['decision_timestamp'];i=bisect_right(engine.reference.ends,t)
        actual=asdict(measure(event['decision_price'],t,cs[i:i+expected['horizon']],expected['direction'],expected['tp'],expected['sl'],expected['horizon']))
        equivalent(actual,{k:v for k,v in expected.items() if k not in ['event_id','outcome_id']});outcomes+=1
    # Full-data preparation must not change a state when future inputs disappear.
    truncated=Engine(cs[:bisect_right(engine.reference.ends,START)])
    for name,params in CONFIGS[:5]:
        a=truncated.snapshot(START,name,params,profile)[0]
        equivalent(a,next(s for s in states if s['snapshot_id']==a['snapshot_id']))
    result=dict(status='PASS',snapshots=168,underlying_timestamps=24,outcomes=outcomes,
        all_reference_fields_compared=True,exact_ID_membership_counts_scores=True,
        float_tolerance=dict(rtol=1e-12,atol=1e-12),future_truncated_checks=5,
        initialization_seconds=initialization,parity_loop_seconds=elapsed,
        peak_RAM_bytes=peak_memory(),source_sha256={p.name:sha256(p) for p in sorted(__import__('pathlib').Path(__file__).parent.glob('*.py'))},
        full_scale_permitted_only_after_benchmark=True)
    write_json(ROOT/'parity-gate.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
