"""Evidence-driven Phase 4 exports. No timeframe ranking or confluence evaluation."""
import json
import numpy as np
import pandas as pd
from .contract import *
from .freeze import check,verify_files
from .run import key


def markdown(frame):
    if frame.empty:return 'No supported rows.\n'
    rows=['| '+' | '.join(map(str,frame.columns))+' |','| '+' | '.join(['---']*len(frame.columns))+' |']
    for row in frame.itertuples(index=False,name=None):
        rows.append('| '+' | '.join('NA' if pd.isna(v) else f'{v:.5g}' if isinstance(v,float) else str(v) for v in row)+' |')
    return '\n'.join(rows)+'\n'


def differences(frame,metric,bounds=None):
    valid=frame[(frame.bucket>=0)&(frame.complete>0)]
    if valid.empty or valid.bucket.nunique()<2:return pd.DataFrame()
    low,high=bounds if bounds is not None else (valid.bucket.min(),valid.bucket.max())
    keys=['period','direction','tp','sl','horizon']
    a=valid[valid.bucket==low][keys+[metric,'complete']]
    b=valid[valid.bucket==high][keys+[metric,'complete']]
    result=a.merge(b,on=keys,suffixes=('_low','_high'),validate='one_to_one')
    result['difference']=result[metric+'_high']-result[metric+'_low']
    return result


def curve_shape(values):
    a=np.asarray(values,dtype=float)
    if len(a)<3 or not np.isfinite(a).all():return 'INSUFFICIENT_BUCKETS'
    delta=np.diff(a)
    if np.all(delta==0):return 'FLAT'
    if np.all(delta>=0):return 'INCREASING'
    if np.all(delta<=0):return 'DECREASING'
    return 'NONMONOTONIC'


def shape_table(tf):
    rows=[];keys=['period','direction','tp','sl','horizon']
    fields=['A1','A2','imbalance','candidates_per_cluster','nearby_age_mean_hours','mean_prior_crossings','mean_prior_visits']
    for phase in ['development','replication']:
        for name,params in CONFIGS:
            ck=key(name,params)
            for field in fields:
                f=pd.read_parquet(ROOT/tf/phase/'analysis'/f'{ck}-1-{field}.parquet')
                f=f[(f.bucket>=0)&(f.complete>0)].sort_values('bucket')
                for values,g in f.groupby(keys):
                    rows.append(dict(timeframe=tf,phase=phase,config=ck,feature=field,**dict(zip(keys,values)),
                        supported_buckets=len(g),minimum_complete_cell=int(g.complete.min()),
                        shape=curve_shape(g.tp_first_rate.to_numpy())))
    return pd.DataFrame(rows)


def stability(tf):
    root=ROOT/tf;model=read(root/'development/analysis/buckets.json');rows=[]
    keys=['direction','tp','sl','horizon']
    for token,cuts in model.items():
        ck,window,field=token.split('/');filename=f'{ck}-{window}-{field}.parquet'
        dev=pd.read_parquet(root/'development/analysis'/filename)
        rep=pd.read_parquet(root/'replication/analysis'/filename)
        for metric in ['tp_first_rate','ambiguous_rate','mfe_pct','mae_pct']:
            valid=dev[(dev.bucket>=0)&(dev.complete>0)]
            if valid.bucket.nunique()<2:continue
            endpoints=(valid.bucket.min(),valid.bucket.max())
            d=differences(dev,metric,endpoints);r=differences(rep,metric,endpoints)
            if d.empty or r.empty:continue
            pooled=d[d.period=='ALL'].merge(r[r.period=='ALL'],on=keys,suffixes=('_dev','_rep'))
            for record in pooled.to_dict('records'):
                q=d[d.period!='ALL']
                for k in keys:q=q[q[k]==record[k]]
                signs=np.sign(q.difference.to_numpy());devsign=np.sign(record['difference_dev'])
                rows.append(dict(timeframe=tf,config=ck,flow_candles=int(window),feature=field,metric=metric,
                    **{k:record[k] for k in keys},elapsed_hours=record['horizon']*STEPS[tf]/HOUR,
                    development_high_minus_low=record['difference_dev'],replication_high_minus_low=record['difference_rep'],
                    represented_development_quarters=len(q),all_four_quarters_same_sign=bool(len(q)==4 and devsign!=0 and np.all(signs==devsign)),
                    replication_same_pooled_sign=bool(devsign!=0 and devsign==np.sign(record['difference_rep']))))
    return pd.DataFrame(rows)


def common(tf,phase):
    root=ROOT/tf/phase;out=root/'native-states';out.mkdir(exist_ok=True)
    frames=[];hashes={}
    for p in sorted((root/'normalized-with-flow').glob('*.parquet')):
        f=pd.read_parquet(p).drop(columns='crossings_status')
        c=pd.read_parquet(root/'crossings'/p.name)
        f=f.merge(c,on='snapshot_id',how='left',validate='one_to_one')
        if not f.as_of.eq(f.decision_timestamp).all() or not f.last_closed_candle_end.eq(f.decision_timestamp).all():
            raise ValueError('Common contract leakage')
        if f.decision_timestamp.max()>=FINAL_START:raise ValueError('2024 forbidden')
        path=out/p.name
        # Do not rewrite the frozen development export.
        if phase=='replication':f.to_parquet(path,index=False,compression='zstd')
        hashes[path.name]=sha256(path);frames.append(f)
    if phase=='replication':write_json(root/'native-states-complete.json',dict(status='COMPLETE',hashes=hashes,rows=sum(map(len,frames))))
    result=pd.concat(frames,ignore_index=True)
    first=read(ROOT/'candles'/tf/'development-coverage.json')['earliest_850_day_decision'] if phase=='development' else 1672531200000
    end=1672531200000 if phase=='development' else FINAL_START
    expected=list(range(first,end,STEPS[tf]))
    if result.configuration_id.nunique()!=5 or any(sorted(f.decision_timestamp.tolist())!=expected for _,f in result.groupby('configuration_id')):
        raise ValueError('Native output clock has holes or duplicates')
    if not (result.lookback_end-result.lookback_start).eq(LOOKBACK).all():raise ValueError('Changed lookback')
    return result


def alignment(native):
    old=PROJECT/'data/phase3r1';hourly=[]
    for phase in ['development','replication']:
        for directory in (old/phase).iterdir():
            paths=sorted(directory.glob('*-states.parquet')) if directory.is_dir() else []
            if paths and pd.read_parquet(paths[0]).detector.iloc[0]=='A':
                for p in paths:
                    f=pd.read_parquet(p,columns=['decision_timestamp','snapshot_id'])
                    f['last_closed_candle_end']=f.decision_timestamp;hourly.extend(f.to_dict('records'))
                break
    sources={tf:f[f.detector=='A'][['decision_timestamp','last_closed_candle_end','snapshot_id']].sort_values('decision_timestamp').to_dict('records') for tf,f in native.items()}
    sources['1h']=sorted(hourly,key=lambda r:r['decision_timestamp'])
    if not hourly:raise ValueError('Frozen 1h reference not located')
    low=sources['15m'];sample=np.unique(np.linspace(0,len(low)-1,64,dtype=int));rows=[]
    for i in sample:
        t=low[int(i)]['decision_timestamp']
        for tf,states in sources.items():
            s=latest_closed(states,t)
            if s is None:raise ValueError('Alignment history unavailable')
            if s['last_closed_candle_end']>t or t-s['last_closed_candle_end']>=STEPS[tf]:
                raise ValueError('Unfinished or stale native state')
            rows.append(dict(query_timestamp=t,timeframe=tf,source_timestamp=s['last_closed_candle_end'],snapshot_id=s['snapshot_id']))
    return pd.DataFrame(rows)


def generate():
    output=ROOT/'reports';output.mkdir(exist_ok=True);native={};stabilities=[];distributions=[];baselines=[];coverage=[];volumes=[]
    for tf in HORIZONS:
        check(tf)
        for phase in ['development','replication']:
            root=ROOT/tf/phase
            for file in ['price-complete.json','flow-complete.json','crossings-complete.json']:
                verify_files(root,read(root/file))
            verify_files(root/'analysis',read(root/'analysis/complete.json'))
            f=common(tf,phase);native.setdefault(tf,[]).append(f)
            for cfg,g in f.groupby('configuration_id'):
                detector=g.detector.iloc[0]
                for field in ['A1','A2','imbalance','nearby_count','cluster_count','candidates_per_cluster','nearby_age_mean_hours','mean_prior_crossings','mean_prior_visits','quantity','delta']:
                    v=g[field].dropna()
                    distributions.append(dict(timeframe=tf,phase=phase,detector=detector,configuration_id=cfg,feature=field,
                        count=len(v),missing=int(g[field].isna().sum()),median=float(v.median()) if len(v) else None,
                        q25=float(v.quantile(.25)) if len(v) else None,q75=float(v.quantile(.75)) if len(v) else None))
            for name,params in CONFIGS:
                b=pd.read_parquet(root/'analysis'/(key(name,params)+'-baseline.parquet'));b=b[b.period=='ALL'].copy()
                b['timeframe']=tf;b['phase']=phase;b['config']=key(name,params);baselines.append(b)
            for label,count in read(root/'flow-complete.json')['counts'].items():
                volumes.append(dict(timeframe=tf,phase=phase,variant_status=label,rows=count))
            c=read(ROOT/'candles'/tf/(phase+'-coverage.json'))
            coverage.append(dict(timeframe=tf,phase=phase,earliest_850_day_decision_UTC=c['first_eligible_utc'],
                                 decision_timestamps=f.decision_timestamp.nunique(),map_states=len(f),complete_contiguous=c['complete_contiguous']))
        native[tf]=pd.concat(native[tf],ignore_index=True)
        stabilities.append(stability(tf))
    stable=pd.concat(stabilities,ignore_index=True);dist=pd.DataFrame(distributions);base=pd.concat(baselines,ignore_index=True)
    shapes=pd.concat([shape_table(tf) for tf in HORIZONS],ignore_index=True)
    shapes.to_csv(output/'bucket-curve-shapes.csv',index=False)
    cov=pd.DataFrame(coverage);vol=pd.DataFrame(volumes);aligned=alignment(native)
    for name,frame in [('chronological-stability',stable),('distributions',dist),('outcome-composition',base),('coverage',cov),('volume-status',vol),('alignment-sample',aligned)]:
        frame.to_csv(output/(name+'.csv'),index=False);frame.to_parquet(output/(name+'.parquet'),index=False,compression='zstd')
    for tf,f in native.items():
        f.iloc[np.unique(np.linspace(0,len(f)-1,100,dtype=int))].to_csv(output/(tf+'-common-schema-sample.csv'),index=False)
    shared='\n2023 is the **previously inspected replication period**, not an untouched final test. No 2024 market data, confluence performance, score summation, parameter ranking, or trading rule is used. All findings are descriptive, with overlapping outcomes and unadjusted multiple comparisons; no edge claim.\n'
    def save(name,body):(PROJECT/name).write_text(body+shared,encoding='utf-8')
    empty_observations=[dict(phase=phase,**r) for phase in ['development','replication'] for r in read(ROOT/('profile-coverage-'+phase+'.json'))['evidence']]
    empty=pd.DataFrame(empty_observations);empty.to_csv(output/'empty-observations.csv',index=False)
    save('PHASE4_DATA_COVERAGE.md','# Phase 4 Data Coverage\n\n'+markdown(cov)+'\nNative exchange alignment determines the first eligible decision; no shortened 850-day fallback. Official candle SHA/CRC and complete-continuity evidence are in each coverage manifest. Exact aggregate-trade profiles retain existing quarantine decisions and source hashes. August 2022 uses the previously adjudicated official daily collection, not the rejected monthly publication.\n\n## Empty Observed Intervals\n'+markdown(empty)+'\nOfficial zero-activity candles are corroborating evidence only, not replacement trade volume. No price states are selectively excluded and no empty profile is zero-filled.\n')
    for tf,label in [('15m','15M'),('4h','4H'),('1d','1D')]:
        d=dist[(dist.timeframe==tf)&(dist.detector=='A')][['phase','feature','count','missing','median','q25','q75']]
        b=base[(base.timeframe==tf)&(base.config=='A')]
        ranges=b.groupby('phase')[['tp_first_rate','ambiguous_rate','mfe_pct','mae_pct']].agg(['min','max'])
        ranges.columns=['_'.join(c) for c in ranges.columns];ranges=ranges.reset_index()
        save(f'PHASE4_{label}_RESULTS.md',f'# {tf} Independent Full-Map Results\n\n'+markdown(d)+'\n## Outcome Grid Ranges\n'+markdown(ranges)+
            '\n## A1/A2 Curve Shapes\n'+markdown(shapes[(shapes.timeframe==tf)&(shapes.config=='A')&shapes.feature.isin(['A1','A2'])].groupby(['phase','feature','period','shape']).size().reset_index(name='grid_cells'))+
            '\nShape labels describe observed frozen-bucket TP-first rates, separately by direction and grid. At least three supported buckets are required; they are not significance tests or fitted monotonic predictions. Quarter-specific differences show regime sensitivity rather than a selected winning regime.\n'+
            '\nRanges cover every predeclared direction/TP/SL/horizon combination and are not a selected result. A1/A2 retain native units; B/C receive no A score transformation. Crossing/visit features use only closed candles after known_at and no later than T.\n'+
            ('\nDaily maps are structural/context layers. Native 24/48/72-hour outcomes cannot resolve 4-hour entry timing; ambiguity is retained rather than rescaled away.\n' if tf=='1d' else ''))
    grouped=stable.groupby(['timeframe','feature','metric']).agg(comparisons=('feature','size'),all_four_quarters_same_sign=('all_four_quarters_same_sign','sum'),replication_same_pooled_sign=('replication_same_pooled_sign','sum')).reset_index()
    grouped.to_csv(output/'stability-counts.csv',index=False)
    stable['stable_and_replicated']=stable.all_four_quarters_same_sign&stable.replication_same_pooled_sign
    evidence=stable.groupby(['timeframe','config','flow_candles','feature','metric','direction']).agg(
        comparisons=('feature','size'),stable_and_replicated=('stable_and_replicated','sum'),
        development_positive=('development_high_minus_low',lambda v:int((v>0).sum())),
        development_negative=('development_high_minus_low',lambda v:int((v<0).sum())),
        replication_positive=('replication_high_minus_low',lambda v:int((v>0).sum())),
        replication_negative=('replication_high_minus_low',lambda v:int((v<0).sum())),
        median_development_contrast=('development_high_minus_low','median'),
        median_replication_contrast=('replication_high_minus_low','median')).reset_index()
    evidence.to_csv(output/'feature-evidence.csv',index=False)
    def statement(feature,metric='tp_first_rate'):
        selected=evidence[(evidence.config=='A')&(evidence.flow_candles==1)&(evidence.feature==feature)&(evidence.metric==metric)]
        return '; '.join(f'{r.timeframe} {r.direction}: {r.stable_and_replicated}/{r.comparisons} cells have the same nonzero sign in all four development quarters and pooled replication' for r in selected.itertuples()) or 'No supported comparison cells.'
    common_shapes=[]
    for (feature,direction),g in evidence[(evidence.config=='A')&(evidence.flow_candles==1)&(evidence.metric=='tp_first_rate')].groupby(['feature','direction']):
        if len(g)!=3:continue
        positive=(g.development_positive==g.comparisons)&(g.replication_positive==g.comparisons)
        negative=(g.development_negative==g.comparisons)&(g.replication_negative==g.comparisons)
        if positive.all() or negative.all():common_shapes.append(feature+' ('+direction+')')
    common_answer=('Uniform pooled high-minus-low sign across every supported grid and all three new timeframes, evaluated separately by outcome direction: '+', '.join(common_shapes)) if common_shapes else 'No feature/direction pair has a uniform nonzero pooled high-minus-low TP-first sign across every supported grid and all three new timeframes.'
    save('PHASE4_CHRONOLOGICAL_STABILITY.md','# Chronological Stability\n\n'+markdown(grouped[grouped.metric=='tp_first_rate'])+
        '\nEach comparison is a detector/flow-window/outcome-grid cell. High-minus-low development quartile contrasts use frozen cuts in replication. Missing quarter/cell support is not a success. Same sign is not significance or predictive superiority. Full TP/SL, ambiguity, MFE and MAE contrasts are in reports/chronological-stability.csv; seven-day 1,000-draw bootstrap files remain next to each source table.\n')
    save('PHASE4_TIMEFRAME_COMPARISON.md','# Timeframe Comparison (No Winner)\n\n'+markdown(dist[(dist.detector=='A')&dist.feature.isin(['A1','imbalance','cluster_count','nearby_count','nearby_age_mean_hours'])][['timeframe','phase','feature','median','q25','q75']])+
        '\n'+common_answer+' This is a stringent shape diagnostic, not an edge test; daily horizons and native flow durations differ.\n'+
        '\nRaw scale differences reflect candle frequency, native widths and candidate density; scores are not normalized or added. Compare elapsed horizons, not equal candle counts. Frozen 1h results remain the reference in PHASE3R2_COMPLETION.md and are not regenerated.\n')
    save('PHASE4_BC_RESULTS.md','# B/C Full Maps\n\n'+markdown(dist[(dist.detector!='A')&dist.feature.isin(['imbalance','cluster_count','nearby_count','nearby_age_mean_hours'])][['timeframe','phase','configuration_id','feature','median']])+
        '\n## Raw Imbalance Chronology\n'+markdown(evidence[(evidence.feature=='imbalance')&(evidence.metric=='tp_first_rate')][['timeframe','config','direction','comparisons','stable_and_replicated']])+
        '\nB widths 1/2 and C reversals 0.003/0.005 remain unscaled. Configuration IDs preserve distinct variants. Differences in density or supported cell counts are not detector superiority; no winner is selected.\n')
    save('PHASE4_VOLUME_DELTA_STATUS.md','# Volume and Delta\n\n'+markdown(vol)+
        '\n15m uses newly streamed exact observed-price aggregate-trade profiles with 1/4/8-candle windows. 4h and daily windows contain whole verified hourly trade profiles (1/2/4 native candles). Aggressive buy/sell and raw Delta are preserved. Side unions avoid duplicated quantity; support/resistance overlap is separately retained. Missing/quarantined windows are not zero-filled.\n\n'+
        markdown(grouped[(grouped.feature=='joint_quantity')&(grouped.metric=='ambiguous_rate')])+
        '\nQuantity/ambiguity contrasts above are descriptive. Map-conditioned quantity and Delta tables are the *-within-*.parquet outputs. Delta directional stability must not be inferred from unconditional associations or overlapping support/resistance exposure. D remains observed-only; this phase does not claim a complete 850-day D map.\n')
    save('PHASE4_ALIGNMENT_READINESS.md','# Causal Alignment Readiness\n\n'+f'{len(aligned)} deterministic lookups across 64 development/replication timestamps verified the latest fully closed 15m/1h/4h/1d state. The 1h source is read-only frozen research.\n\n'+
        'Native states contain timestamp, last close, price, window, detector/config, A1/A2 where applicable, raw geometry, age, contact history, quantity/Delta and coverage status. Files are under data/phase4/<timeframe>/<phase>/native-states. Only lookup infrastructure is provided: no forward-filled research dataset or confluence performance.\n')
    test=read(ROOT/'final-tests.json');audit=read(ROOT/'preservation-audit.json')
    if test['returncode'] or audit['status']!='PASS':raise ValueError('Final verification failed')
    save('PHASE4_COMPLETION.md','# Phase 4 Completion\n\n'+markdown(cov)+
        f'\nFinal suite: {test["tests"]} tests, {test["failures"]} failures, {test["errors"]} errors. Frozen artifact preservation: {audit["files"]} files unchanged.\n\n'+
        '## Completion Questions\n\n1. Architecture: native parity gates and full one-candle coverage checks passed for all three timeframes.\n'+
        '2. Shared feature shapes: '+common_answer+' Native-scale distributions and full contrasts are provided separately.\n'+
        '3. Timeframe-specific effects: daily timing resolution and differing widths/densities are structural, not predictive superiority.\n'+
        '4. A versus B/C: raw-imbalance stable/replicated cell counts for every detector are in PHASE4_BC_RESULTS.md. This is a controlled descriptive comparison, not evidence of a winning detector.\n'+
        '5. Cluster concentration: '+statement('candidates_per_cluster')+'.\n'+
        '6. Candidate age: '+statement('nearby_age_mean_hours')+'. Contact metrics are also exported.\n'+
        '7. Quantity versus ambiguity: '+statement('joint_quantity','ambiguous_rate')+'. Conditional tables retain fixed map buckets.\n'+
        '8. Support normalized Delta: '+statement('support_normalized_delta')+'. No directional trading rule is established; other variants and missingness are retained.\n'+
        '9. Alignment: native outputs and frozen 1h passed causal lookup checks.\n'+
        '10. Remaining structural limitations: observed-only D history, daily OHLC ambiguity, quarantine-conditioned coverage, prior inspection of 2023 and multiple comparisons must carry into any later phase. No confluence evaluation was executed.\n\n'+
        'Detailed evidence: data/phase4/reports/*.csv and *.parquet; per-timeframe analysis directories retain full grids and bootstrap tables. STOP after this phase.\n')
    write_json(ROOT/'completion.json',dict(status='COMPLETE',no_2024=True,no_confluence=True,no_trading_rules=True,
        reports={p.name:sha256(p) for p in PROJECT.glob('PHASE4_*.md') if p.name!='PHASE4_PROGRESS.md'}))


if __name__=='__main__':generate()
