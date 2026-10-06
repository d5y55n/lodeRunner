"""Independent native-timeframe descriptive tables; no parameter selection."""
import argparse
from itertools import product
import numpy as np
import pandas as pd
from .contract import *
from .run import key

GRID=['direction','tp','sl','horizon']
MAP_FIELDS=['A1','A2','imbalance','full_map_imbalance','nearby_count','cluster_count',
            'candidates_per_cluster','overlap_pair_count','nearby_age_mean_hours',
            'nearest_support_distance','nearest_resistance_distance',
            'mean_prior_crossings','mean_prior_visits','mean_hours_since_last_contact']
FLOW_FIELDS=['joint_quantity','support_quantity','resistance_quantity',
             'support_delta','resistance_delta','joint_delta','support_normalized_delta',
             'resistance_normalized_delta','normalized_delta_difference']


def quartiles(values):
    values=np.asarray(values,dtype=float);values=values[np.isfinite(values)]
    return sorted(set(map(float,np.quantile(values,[.25,.5,.75])))) if len(values) else []


def buckets(values,cuts):
    a=np.asarray(values,dtype=float)
    return np.where(np.isfinite(a),np.searchsorted(cuts,a,side='left'),-1)


def arrays(events,outcome,tf):
    grids=list(product(['LONG','SHORT'],[.003,.005],[.003,.005],HORIZONS[tf]))
    if events.event_id.duplicated().any() or outcome.duplicated(['event_id']+GRID).any():
        raise ValueError('Duplicate outcome/event identity')
    if set(events.event_id)!=set(outcome.event_id) or len(outcome)!=len(events)*24:
        raise ValueError('Incomplete event grid')
    index=pd.MultiIndex.from_tuples([(eid,*g) for eid in events.event_id for g in grids],names=['event_id']+GRID)
    f=outcome.set_index(['event_id']+GRID).reindex(index)
    if f.censored.isna().any():raise ValueError('Incomplete outcome grid')
    complete=(~f.censored).to_numpy().reshape(-1,24)
    result={'complete':complete.astype(float),'censored':1.-complete,'state_count':np.ones_like(complete,dtype=float)}
    for label in ['TP_FIRST','SL_FIRST','NEITHER','AMBIGUOUS']:
        result[label]=(f.label.eq(label).to_numpy().reshape(-1,24)&complete).astype(float)
    for field in ['mfe_pct','mae_pct']:
        result[field+'_sum']=np.where(complete,f[field].to_numpy().reshape(-1,24),0.)
    return grids,result


def summarize(groups,values,grids):
    codes,unique=pd.factorize(pd.MultiIndex.from_frame(groups),sort=True)
    n=len(unique);indices=(codes[:,None]*24+np.arange(24)).ravel()
    out=unique.to_frame(index=False).iloc[np.repeat(np.arange(n),24)].reset_index(drop=True)
    out.columns=groups.columns
    for j,field in enumerate(GRID):out[field]=[g[j] for g in grids]*n
    for field,a in values.items():out[field]=np.bincount(indices,weights=a.ravel(),minlength=n*24)
    for label in ['TP_FIRST','SL_FIRST','NEITHER','AMBIGUOUS']:
        out[label.lower()+'_rate']=out[label]/out.complete.replace(0,np.nan)
    for field in ['mfe_pct','mae_pct']:out[field]=out.pop(field+'_sum')/out.complete.replace(0,np.nan)
    out['gross_resolved_expectancy_pct']=100*(out.TP_FIRST*out.tp-out.SL_FIRST*out.sl)/(out.TP_FIRST+out.SL_FIRST).replace(0,np.nan)
    return out


def bootstrap(frame,values,grids,bucket):
    """Cell-minus-unconditional rates, shared UTC seven-day block bootstrap draws."""
    weeks=(frame.decision_timestamp.to_numpy()//(7*86400000)).astype(int)
    unique=np.unique(weeks);wi=np.searchsorted(unique,weeks)
    rng=np.random.default_rng(4101)
    weights=rng.multinomial(len(unique),np.full(len(unique),1/len(unique)),size=1000)
    rows=[]
    for b in np.unique(bucket[bucket>=0]):
        selected=bucket==b
        for gi,g in enumerate(grids):
            bn=np.bincount(wi,weights=values['complete'][:,gi],minlength=len(unique))
            cn=np.bincount(wi,weights=values['complete'][:,gi]*selected,minlength=len(unique))
            represented=int((cn>0).sum())
            for label in ['TP_FIRST','AMBIGUOUS']:
                bt=np.bincount(wi,weights=values[label][:,gi],minlength=len(unique))
                ct=np.bincount(wi,weights=values[label][:,gi]*selected,minlength=len(unique))
                low=high=np.nan
                if represented>=5:
                    with np.errstate(invalid='ignore',divide='ignore'):
                        samples=(weights@ct)/(weights@cn)-(weights@bt)/(weights@bn)
                    finite=samples[np.isfinite(samples)]
                    if len(finite)>=950:low,high=np.quantile(finite,[.025,.975])
                rows.append(dict(zip(GRID,g))|dict(bucket=int(b),metric=label,week_blocks=represented,
                    increment=ct.sum()/cn.sum()-bt.sum()/bn.sum() if cn.sum() and bn.sum() else np.nan,
                    ci_low=low,ci_high=high))
    return pd.DataFrame(rows)


def execute(tf,phase):
    dest=ROOT/tf/phase;price=read(dest/'price-complete.json');flow=read(dest/'flow-complete.json')
    if flow['status']!='COMPLETE':raise ValueError('Flow attachment required; no omission fallback')
    if phase=='replication' and not (ROOT/tf/'development-freeze.json').exists():
        raise ValueError('Frozen development analysis required')
    crossing=read(dest/'crossings-complete.json')
    if crossing['status']!='COMPLETE':raise ValueError('Causal crossing features required')
    for manifest in [price,flow,crossing]:
        for name,digest in manifest['hashes'].items():
            if sha256(dest/name)!=digest:raise ValueError('Research input modified')
    state=pd.concat([pd.read_parquet(p) for p in sorted((dest/'normalized-with-flow').glob('*.parquet'))],ignore_index=True)
    extra=pd.concat([pd.read_parquet(p) for p in sorted((dest/'crossings').glob('*.parquet'))],ignore_index=True)
    state=state.drop(columns='crossings_status').merge(extra,on='snapshot_id',how='left',validate='one_to_one')
    if not state.crossings_status.eq('AVAILABLE').all() or not state.as_of.eq(state.decision_timestamp).all():
        raise ValueError('Missing/noncausal crossings join')
    volume=pd.concat([pd.read_parquet(p) for p in sorted((dest/'flow').glob('*.parquet'))],ignore_index=True)
    outcome=pd.concat([pd.read_parquet(p) for p in sorted((dest/'future-outcomes').glob('*.parquet'))],ignore_index=True)
    folder=dest/'analysis';folder.mkdir(exist_ok=True)
    models={};table_count=0
    for name,params in CONFIGS:
        ck=key(name,params)
        config_states=pd.read_parquet(next((dest/ck).glob('*-states.parquet')))
        cfg=config_states.configuration_id.iloc[0]
        base=state[state.configuration_id==cfg].sort_values('decision_timestamp').reset_index(drop=True)
        grids,ys=arrays(base[['event_id']],outcome,tf)
        quarter=pd.to_datetime(base.decision_timestamp,unit='ms',utc=True).dt.strftime('%Y-Q')+pd.to_datetime(base.decision_timestamp,unit='ms',utc=True).dt.quarter.astype(str)
        doubled={k:np.concatenate([v,v]) for k,v in ys.items()}
        periods=np.concatenate([np.full(len(base),'ALL'),quarter.to_numpy()])
        baseline=summarize(pd.DataFrame(dict(period=periods)),doubled,grids)
        baseline['elapsed_horizon_hours']=baseline.horizon*STEPS[tf]/HOUR
        baseline.to_parquet(folder/(ck+'-baseline.parquet'),index=False)
        for window in FLOW_CANDLES[tf]:
            f=base.drop(columns=[c for c in volume.columns if c in base and c not in ['snapshot_id','event_id','decision_timestamp','timeframe']])
            v=volume[volume.native_flow_candles==window]
            f=f.merge(v,on=['snapshot_id','event_id','decision_timestamp','timeframe'],validate='one_to_one',how='left')
            if f.flow_status.isna().any():raise ValueError('Missing flow join')
            for field in MAP_FIELDS+FLOW_FIELDS:
                # Geometry is independent of flow-window variants and exported once.
                if field in MAP_FIELDS and window!=1:continue
                values=f[field].copy()
                if field in FLOW_FIELDS:values=values.where(f.flow_status.eq('AVAILABLE'))
                model_key=f'{ck}/{window}/{field}'
                if phase=='development':cuts=quartiles(values)
                else:cuts=read(ROOT/tf/'development/analysis/buckets.json')[model_key]
                models[model_key]=cuts;b=buckets(values,cuts)
                groups=pd.DataFrame(dict(period=periods,bucket=np.tile(b,2)))
                table=summarize(groups,doubled,grids)
                table['elapsed_horizon_hours']=table.horizon*STEPS[tf]/HOUR
                table['feature']=field;table['native_flow_candles']=window
                stem=f'{ck}-{window}-{field}'
                table.to_parquet(folder/(stem+'.parquet'),index=False,compression='zstd')
                ci=bootstrap(f,ys,grids,b)
                if not ci.empty:ci['elapsed_horizon_hours']=ci.horizon*STEPS[tf]/HOUR
                ci.to_parquet(folder/(stem+'-bootstrap.parquet'),index=False,compression='zstd')
                table_count+=2
                if field in FLOW_FIELDS:
                    valid=(b>=0)&f.flow_status.eq('AVAILABLE').to_numpy()
                    for condition in ['A1','imbalance','candidates_per_cluster']:
                        condition_key=f'{ck}/1/{condition}'
                        if phase=='development':condition_cuts=quartiles(f[condition])
                        else:condition_cuts=read(ROOT/tf/'development/analysis/buckets.json')[condition_key]
                        cb=buckets(f[condition],condition_cuts);selected=np.tile(valid&(cb>=0),2)
                        if not selected.any():continue
                        group=pd.DataFrame(dict(period=periods,map_bucket=np.tile(cb,2),flow_bucket=np.tile(b,2)))[selected].reset_index(drop=True)
                        chosen={k:v[selected] for k,v in doubled.items()}
                        result=summarize(group,chosen,grids)
                        control=summarize(group.drop(columns='flow_bucket'),chosen,grids)
                        keys=['period','map_bucket']+GRID
                        rates=['tp_first_rate','ambiguous_rate','mfe_pct','mae_pct']
                        result=result.merge(control[keys+rates],on=keys,suffixes=('','_map_baseline'),validate='many_to_one')
                        for metric in rates:result[metric+'_increment']=result[metric]-result[metric+'_map_baseline']
                        result['elapsed_horizon_hours']=result.horizon*STEPS[tf]/HOUR
                        result.to_parquet(folder/(stem+'-within-'+condition+'.parquet'),index=False,compression='zstd')
                        table_count+=1
            print('NATIVE_ANALYSIS',tf,phase,ck,window,flush=True)
    if phase=='development':write_json(folder/'buckets.json',models)
    hashes={p.name:sha256(p) for p in folder.iterdir() if p.is_file() and p.name!='complete.json'}
    write_json(folder/'complete.json',dict(status='DESCRIPTIVE_TABLES_COMPLETE_REVIEW_PENDING',tables=table_count,
        hashes=hashes,analysis_code_sha256=sha256(__file__),phase=phase,
        inference='exploratory overlapping horizons; unadjusted descriptive intervals, not edge evidence',no_2024=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('timeframe',choices=list(HORIZONS))
    p.add_argument('phase',choices=['development','replication']);a=p.parse_args();execute(a.timeframe,a.phase)
