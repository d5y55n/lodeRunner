"""Bounded first deliverable: 24 hourly full states, not a strategy search."""
from bisect import bisect_right
from collections import Counter
from dataclasses import asdict
from itertools import product
from pathlib import Path
import ctypes
import json
import os
import shutil
import subprocess
import time
import numpy as np
import pandas as pd
from app.market.aggregate_trades import write_json,sha256
from app.research.models import canonical,identity
from app.research.outcomes import measure
from app.research.phase3_profiles import Profiles
from app.research.phase3_plan import utc
from app.research.runner import code_digest
from .contract import ROOT,SOURCE,HOUR,LOOKBACK,configuration
from .core import FullMapEngine
from .volume import RollingVAP
from .data import load_sources,hourly_bins

CONFIGS=[('A',{}),('B',{'width':1}),('B',{'width':2}),
         ('C',{'reversal_fraction':.003}),('C',{'reversal_fraction':.005}),
         ('D',{'bin_size':50,'concentration_multiple':1.5}),('D',{'bin_size':100,'concentration_multiple':1.5})]
START=utc('2022-12-30');END=START+24*HOUR


def peak_memory():
    if os.name!='nt':
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    class Counters(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in
            ['peak','working','poolpeak','pool','nonpoolpeak','nonpool','pagefile','peakpagefile']]
    counters=Counters();counters.cb=ctypes.sizeof(counters)
    kernel=ctypes.WinDLL('kernel32');kernel.GetCurrentProcess.restype=ctypes.c_void_p
    psapi=ctypes.WinDLL('psapi');psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb):raise OSError('Memory measurement failed')
    return counters.peak


def preserve_inventory():
    project=ROOT.parent.parent
    paths=list((project/'backend/app/research').glob('*.py'))+list((project/'backend/app/deepdive').glob('*.py'))
    paths+=list((project/'data/phase35').rglob('*'))
    paths+=list(project.glob('PHASE*.md'))
    paths=[p for p in paths if p.is_file() and not p.name.startswith('PHASE3R_')]
    return {str(p.relative_to(project)):sha256(p) for p in sorted(paths)}


def write_rows(dest,name,rows):
    # Complex fields are canonical JSON in Parquet, and native JSON in JSONL.
    with (dest/(name+'.jsonl')).open('w',encoding='utf-8',newline='\n') as stream:
        for row in rows:stream.write(canonical(row)+'\n')
    flat=[{k:canonical(v) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()} for r in rows]
    pd.DataFrame(flat).to_parquet(dest/(name+'.parquet'),index=False)


def js_parity(engine,snapshots):
    fixtures=Path(__file__).resolve().parents[2]/'tests/fixtures/phase3r'
    node=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    cases=[];expected=[]
    for snap in snapshots:
        if snap['detector']!='A':continue
        cs=engine.window(snap['decision_timestamp'])
        for direction in ['LONG','SHORT']:
            cases.append(dict(candles=[[c.start,c.open,c.high,c.low,c.close] for c in cs],timeframe='1h',
                entry=snap['decision_price'],direction=direction))
            expected.append(snap['native_score'][direction.lower()+'_score'])
    run=subprocess.run([node,str(fixtures/'original-oracle.cjs'),str(fixtures/'original-script.js')],
        input=json.dumps(cases),capture_output=True,text=True,check=True)
    if json.loads(run.stdout)!=expected:raise AssertionError('Real candle JS parity failed')
    return dict(cases=len(cases),passed=True,original_sha256=sha256(fixtures/'original-script.js'))


def analysis_tables(dest,snapshots,outcomes):
    rows=[]
    for s in snapshots:
        if s['detector']!='A':continue
        rows.append(dict(event_id=s['event_id'],timestamp=s['decision_timestamp'],price=s['decision_price'],
            **s['native_score'],nearby_support=s['raw']['support']['density']['inner']+s['raw']['support']['density']['outer'],
            nearby_resistance=s['raw']['resistance']['density']['inner']+s['raw']['resistance']['density']['outer'],
            nearest_support_distance=s['raw']['support']['nearest_absolute_distance_fraction'],
            nearest_resistance_distance=s['raw']['resistance']['nearest_absolute_distance_fraction']))
    frame=pd.DataFrame(rows);frame.to_csv(dest/'a-ablation-states.csv',index=False)
    labels=pd.DataFrame(outcomes);joined=labels.merge(frame,on='event_id',validate='many_to_one')
    joined.to_csv(dest/'a-ablation-outcomes.csv',index=False)
    tables=[]
    for direction,group in joined.groupby('direction'):
        for variant,score in [('A1',direction.lower()+'_score'),('A2','full_weight_only_'+direction.lower())]:
            for key,g in group.groupby([score,'tp','sl','horizon'],sort=True):
                complete=g[~g.censored];counts=Counter(complete.label)
                tables.append(dict(variant=variant,direction=direction,score=float(key[0]),tp=key[1],sl=key[2],horizon=int(key[3]),
                    events=len(g),censored=int(g.censored.sum()),**{k:counts[k] for k in ['TP_FIRST','SL_FIRST','NEITHER','AMBIGUOUS']},
                    mean_mfe_pct=float(g.mfe_pct.mean()),mean_mae_pct=float(g.mae_pct.mean()),
                    mean_time_to_mfe_ms=float(g.time_to_mfe_ms.mean()) if g.time_to_mfe_ms.notna().any() else None,
                    mean_time_to_mae_ms=float(g.time_to_mae_ms.mean()) if g.time_to_mae_ms.notna().any() else None))
    pd.DataFrame(tables).to_csv(dest/'a-exact-score-outcomes.csv',index=False)
    return dict(long_exact_distribution={str(k):v for k,v in sorted(Counter(frame.long_score).items())},
        short_exact_distribution={str(k):v for k,v in sorted(Counter(frame.short_score).items())},
        outer_band_changed_score_events=int((frame.long_score!=frame.full_weight_only_long).sum()),
        interpretation='24 serially dependent timestamps only; no monotonicity, threshold or edge inference')


def main():
    ROOT.mkdir(exist_ok=True);dest=ROOT/'sanity';dest.mkdir(exist_ok=True)
    before=preserve_inventory();write_json(ROOT/'preserved-before.json',before)
    plan=dict(schema='phase3r-first-deliverable-v1',decision_start=START,decision_end_exclusive=END,
        decision_step=HOUR,lookback=LOOKBACK,sampling='first 24 consecutive hourly decisions with complete authorized 850-day price history',
        configs=[configuration(d,p) for d,p in CONFIGS],tp=[.003,.005],sl=[.003,.005],horizons=[4,8,24],
        warmup_only_2020=True,no_2024=True,no_other_timeframes=True,no_parameter_selection=True,
        outcome_unit='one underlying timestamp, shared across seven configurations',
        incomplete_D_policy='retain observed map with warning; never eligible for complete-coverage comparison')
    write_json(ROOT/'plan.json',plan)
    begin=time.perf_counter();cs,paths,bad,lineage=load_sources();engine=FullMapEngine(cs)
    if cs[0].start+LOOKBACK!=START:raise ValueError('Sampling start no longer matches first complete window')
    profiles=Profiles(SOURCE/'profiles',bad);rolling={};inputs={};preprocessing=[]
    for width in [50,100]:
        frame,info=hourly_bins(paths,width,lineage);preprocessing.append(info)
        inputs[width]=frame;rolling[width]=RollingVAP(frame,width,quarantines=bad)
        print('VAP_READY',width,len(frame),flush=True)
    setup=time.perf_counter()-begin;runstart=time.perf_counter()
    snapshots=[];contributions=[];bins=[];events=[];timings=[]
    for t in range(START,END,HOUR):
        price=engine.window(t)[-1].close
        for detector,params in CONFIGS:
            tick=time.perf_counter()
            if detector=='D':
                snap,rows=rolling[params['bin_size']].snapshot(t,price,params['concentration_multiple']);bins.extend(rows)
                if t in [START,END-HOUR]:
                    frame=inputs[params['bin_size']];direct=frame[(frame.hour>=t-LOOKBACK)&(frame.hour<t)].groupby('bin')[['quantity','buy','sell']].sum()
                    actual=np.asarray([[r['quantity'],r['buy'],r['sell']] for r in rows])
                    np.testing.assert_allclose(actual,direct.sort_index().to_numpy(),rtol=1e-10,atol=1e-7)
            else:
                snap,rows=engine.snapshot(t,detector,params,profiles);contributions.extend(rows)
            snapshots.append(snap);timings.append(dict(timestamp=t,detector=detector,parameters=params,
                seconds=time.perf_counter()-tick,candidate_count=snap['known_candidate_count']))
        events.append(dict(event_id=snap['event_id'],decision_timestamp=t,decision_price=price,phase='development_sanity'))
        print('FULL_MAP',pd.Timestamp(t,unit='ms',tz='UTC').isoformat(),[s['known_candidate_count'] for s in snapshots[-7:]],flush=True)
    measured=time.perf_counter()-runstart
    # Persist decision-only facts before opening future-outcome evaluation.
    write_rows(dest,'snapshots',snapshots);write_rows(dest,'candidates',list(engine.catalog.values()))
    write_rows(dest,'a-contributions',contributions);write_rows(dest,'d-bins',bins);write_rows(dest,'events',events)
    parity=js_parity(engine,snapshots)
    for t in [START,END-HOUR]:
        replay=FullMapEngine(cs[:bisect_right(engine.ends,t)])
        for detector,params in CONFIGS[:5]:
            snap,_=replay.snapshot(t,detector,params,profiles)
            original=next(s for s in snapshots if s['snapshot_id']==snap['snapshot_id'])
            if canonical(snap)!=canonical(original):raise AssertionError('Truncated-history replay differs')
    for width in [50,100]:
        frame=inputs[width];replay=RollingVAP(frame[frame.hour<START+HOUR],width,quarantines=bad)
        for t in [START,START+HOUR]:
            snap,rows=replay.snapshot(t,engine.window(t)[-1].close)
            if canonical(snap)!=canonical(next(s for s in snapshots if s['snapshot_id']==snap['snapshot_id'])):
                raise AssertionError('D truncated-trade replay differs')
    outcomes=[]
    for event in events:
        t=event['decision_timestamp'];i=bisect_right(engine.ends,t)
        for direction,tp,sl,h in product(['LONG','SHORT'],plan['tp'],plan['sl'],plan['horizons']):
            outcomes.append(dict(event_id=event['event_id'],outcome_id=identity([event['event_id'],direction,tp,sl,h]),
                **asdict(measure(event['decision_price'],t,cs[i:i+h],direction,tp,sl,h))))
    write_rows(dest,'future-outcomes',outcomes)
    analysis=analysis_tables(dest,snapshots,outcomes)
    # Re-serialization must produce the same bytes; run-dependent timings are excluded.
    expected=''.join(canonical(s)+'\n' for s in snapshots)
    if (dest/'snapshots.jsonl').read_text(encoding='utf-8')!=expected:raise AssertionError('Export round trip failed')
    after=preserve_inventory()
    if before!=after:raise AssertionError('Previous research artifacts changed')
    artifact_bytes=sum(p.stat().st_size for p in dest.iterdir() if p.is_file())
    results=dict(status='COMPLETE_FIRST_DELIVERABLE',snapshots=len(snapshots),unique_events=len(events),outcome_rows=len(outcomes),
        candidate_catalog_rows=len(engine.catalog),a_contribution_rows=len(contributions),d_bin_rows=len(bins),
        real_js_parity=parity,replay_checks=dict(ABC_truncated_history_snapshots=10,D_truncated_trade_snapshots=4,
            D_direct_bin_reconstruction_checks=4,deterministic_JSONL=True),analysis=analysis,
        timings=timings,setup_seconds=setup,rolling_run_seconds=measured,total_seconds=time.perf_counter()-begin,
        peak_working_set_bytes=peak_memory(),preprocessing=preprocessing,artifact_bytes=artifact_bytes,
        compute_projection_17520_steps_seconds=measured/24*17520,storage_projection_bytes=artifact_bytes/24*17520,
        projection_warning='Compute-only linear projection, not measured multi-year research; most 2021-22 windows lack authorized 850-day history',
        old_research_code_digest=code_digest(),preserved_artifacts=len(before),preserved_inventory_id=identity(before),
        D_complete_coverage_eligible_snapshots=sum(s['volume']['eligible_complete_coverage_comparison'] for s in snapshots if s['detector']=='D'),
        ABC_volume_available_snapshots=sum(s['volume']['status']=='AVAILABLE' for s in snapshots if s['detector']!='D'),
        quarantined_minutes=sum((b-a)//60000 for a,b in bad),no_2024_access=True,
        artifact_hashes={p.name:sha256(p) for p in dest.iterdir() if p.is_file()})
    write_json(ROOT/'run-results.json',results)
    print('PHASE3R_SANITY_COMPLETE',results['snapshots'],results['unique_events'],results['outcome_rows'],flush=True)


if __name__=='__main__':main()
