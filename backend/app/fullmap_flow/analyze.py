"""Transparent event-aligned conditional summaries; no fitted prediction model."""
import argparse
from itertools import product
import numpy as np
import pandas as pd
from .common import *

GRID=['direction','tp','sl','horizon']
GRIDS=list(product(['LONG','SHORT'],[.003,.005],[.003,.005],[4,8,24]))
INCREMENTAL=DELTA+['support_delta','resistance_delta','support_volume_share','joint_quantity']

def outcome_arrays(events,outcomes):
    if events.event_id.duplicated().any() or outcomes.duplicated(['event_id']+GRID).any():raise ValueError('Duplicate event/outcome join')
    if set(events.event_id)!=set(outcomes.event_id) or len(outcomes)!=len(events)*24:raise ValueError('Incomplete outcome join')
    index=pd.MultiIndex.from_tuples([(eid,*g) for eid in events.event_id for g in GRIDS],names=['event_id']+GRID)
    f=outcomes.set_index(['event_id']+GRID).reindex(index)
    if f.censored.isna().any():raise ValueError('Missing grid row')
    complete=(~f.censored).to_numpy().reshape(-1,24)
    arrays={'complete':complete.astype(float),'censored':1.-complete,'state_count':np.ones_like(complete,dtype=float)}
    for label in ['TP_FIRST','SL_FIRST','NEITHER','AMBIGUOUS']:
        arrays[label]=(f.label.eq(label).to_numpy().reshape(-1,24)&complete).astype(float)
    for col in ['mfe_pct','mae_pct','time_to_mfe_ms','time_to_mae_ms']:
        a=f[col].to_numpy(dtype=float).reshape(-1,24)
        arrays[col+'_sum']=np.where(complete&np.isfinite(a),a,0.)
        arrays[col+'_n']=(complete&np.isfinite(a)).astype(float)
    return arrays

def aggregate(groups,arrays):
    codes,unique=pd.factorize(pd.MultiIndex.from_frame(groups),sort=True)
    count=len(unique);indices=(codes[:,None]*24+np.arange(24)).ravel()
    out=unique.to_frame(index=False).iloc[np.repeat(np.arange(count),24)].reset_index(drop=True)
    out.columns=groups.columns
    for j,col in enumerate(GRID):out[col]=[g[j] for g in GRIDS]*count
    for name,values in arrays.items():out[name]=np.bincount(indices,weights=values.ravel(),minlength=count*24)
    out['tp_first_rate']=out.TP_FIRST/out.complete.replace(0,np.nan)
    out['gross_resolved_expectancy_pct']=100*(out.TP_FIRST*out.tp-out.SL_FIRST*out.sl)/(out.TP_FIRST+out.SL_FIRST).replace(0,np.nan)
    for col in ['mfe_pct','mae_pct','time_to_mfe_ms','time_to_mae_ms']:
        out[col]=out.pop(col+'_sum')/out.pop(col+'_n').replace(0,np.nan)
    return out

def cuts(values,n):
    a=np.asarray(values,dtype=float);a=a[np.isfinite(a)]
    return sorted(set(map(float,np.quantile(a,np.arange(1,n)/n)))) if len(a) else []

def flow_model(frame):
    result={}
    for field in FLOW:
        a=frame[field].where(frame.status.eq('AVAILABLE'))
        c20=cuts(a,20);b=buckets(a,c20)
        groups=pd.DataFrame({'b':b,'week':frame.week});groups=groups[groups.b>=0]
        counts=groups.groupby('b').size();weeks=groups.groupby('b').week.nunique()
        result[field]=dict(decile=cuts(a,10),quartile=cuts(a,4),ventile=c20,
            ventile_supported=bool(len(counts)==20 and counts.min()>=200 and weeks.min()>=5),
            positive_cut=float(a[a>.01].quantile(.9)) if (a>.01).any() else 1.)
    return result

def conditions(frame):
    result={name:frame[name+'_bucket'].to_numpy(dtype=int) for name in CONDITIONS if name+'_bucket' in frame}
    result['map_direction']=np.sign(frame.imbalance).to_numpy(dtype=int)+1
    # Joint geometry descriptor retains all observed cells, not just favorable extremes.
    result['cluster_concentration']=result['map_direction']*100+frame.clusters_bucket.to_numpy()*10+frame.candidates_per_cluster_bucket.to_numpy()
    result['age_band']=np.where(frame.mean_age.notna(),np.searchsorted([30*24,180*24,365*24],frame.mean_age,side='left'),-1)
    result['ALL']=np.zeros(len(frame),dtype=int)
    return result

def intervals(frame,arrays,condition,flow_bucket):
    # The same bootstrap draws are used for the cell and its map-only cohort.
    weeks=np.sort(frame.week.unique());wi=np.searchsorted(weeks,frame.week)
    rng=np.random.default_rng(3202);weights=rng.multinomial(len(weeks),np.full(len(weeks),1/len(weeks)),1000)
    rows=[];valid=(flow_bucket>=0)&(condition>=0)&frame.status.eq('AVAILABLE').to_numpy()
    for cb in np.unique(condition[valid]):
        baseline=valid&(condition==cb)
        for fb in np.unique(flow_bucket[baseline]):
            cell=baseline&(flow_bucket==fb)
            for gi,g in enumerate(GRIDS):
                def totals(mask,name):return np.bincount(wi,weights=np.where(mask,arrays[name][:,gi],0.),minlength=len(weeks))
                bn=totals(baseline,'complete');bt=totals(baseline,'TP_FIRST')
                cn=totals(cell,'complete');ct=totals(cell,'TP_FIRST')
                represented=int((cn>0).sum());low=high=np.nan
                if represented>=5:
                    with np.errstate(divide='ignore',invalid='ignore'):
                        samples=(weights@ct)/(weights@cn)-(weights@bt)/(weights@bn)
                    finite=samples[np.isfinite(samples)]
                    if len(finite)>=950:low,high=np.quantile(finite,[.025,.975])
                rows.append(dict(zip(GRID,g))|dict(map_bucket=int(cb),flow_bucket=int(fb),
                    complete=int(cn.sum()),week_blocks=represented,increment=ct.sum()/cn.sum()-bt.sum()/bn.sum() if cn.sum() and bn.sum() else np.nan,
                    ci_low=low,ci_high=high))
    return pd.DataFrame(rows)

def summary(frame,arrays,cond,fb,unconditioned):
    valid=(fb>=0)&frame.status.eq('AVAILABLE').to_numpy()
    periods=np.concatenate([np.full(len(frame),'ALL'),frame.quarter.to_numpy()])
    select=np.tile(valid,2)
    g=pd.DataFrame(dict(period=periods,map_bucket=np.tile(cond,2),flow_bucket=np.tile(fb,2)))[select].reset_index(drop=True)
    a={k:np.concatenate([v,v])[select] for k,v in arrays.items()}
    if g.empty:return pd.DataFrame()
    full=aggregate(g,a);base=aggregate(g.drop(columns='flow_bucket'),a)
    cohort=aggregate(g[['period']],a)
    keys=['period','map_bucket']+GRID
    full=full.merge(base[keys+['tp_first_rate','complete']],on=keys,suffixes=('','_map_only'),validate='many_to_one')
    full=full.merge(cohort[['period']+GRID+['tp_first_rate']],on=['period']+GRID,suffixes=('','_cohort'),validate='many_to_one')
    full=full.merge(unconditioned[['period']+GRID+['tp_first_rate']],on=['period']+GRID,suffixes=('','_unconditioned'),validate='many_to_one')
    full['increment_vs_map']=full.tp_first_rate-full.tp_first_rate_map_only
    return full

def analyze(phase):
    initialize()
    if phase=='replication':check_freeze()
    if read(ROOT/phase/'features-complete.json')['status']!='COMPLETE':raise ValueError('Missing features')
    dest=ROOT/phase/'analysis';dest.mkdir(exist_ok=True)
    events=pd.read_parquet(BASE/phase/'events.parquet')
    outcomes=pd.concat([pd.read_parquet(p) for p in sorted((BASE/phase).glob('*-outcomes.parquet'))],ignore_index=True)
    arrays=outcome_arrays(events,outcomes)
    total_files=0
    for config in CONFIGS:
        ck=key(config);states=pd.read_parquet(BASE/phase/'analysis'/f'{ck}-state-features.parquet')
        if states.event_id.tolist()!=events.event_id.tolist():raise ValueError('Changed event ordering')
        volume=pd.concat([pd.read_parquet(p) for p in sorted((ROOT/phase/'features').glob(f'{ck}-*.parquet'))],ignore_index=True)
        for window in WINDOWS:
            frame=states.merge(volume[volume.window_hours.eq(window)],on=['event_id','timestamp'],validate='one_to_one',how='left')
            if frame.status.isna().any() or len(frame)!=len(events):raise ValueError('Missing flow event')
            folder=dest/f'{ck}-{window}h';folder.mkdir(exist_ok=True)
            frame.to_parquet(folder/'states.parquet',index=False,compression='zstd')
            model_path=ROOT/'development/analysis'/folder.name/'model.json'
            if phase=='development':write_json(model_path,flow_model(frame))
            model=read(model_path);conds=conditions(frame)
            groups=pd.DataFrame({'period':np.concatenate([np.full(len(frame),'ALL'),frame.quarter.to_numpy()])})
            base=aggregate(groups,{k:np.concatenate([v,v]) for k,v in arrays.items()});base.to_csv(folder/'unconditioned.csv',index=False)
            describe=[];correlations=[]
            for period,f in [('ALL',frame),*list(frame.groupby('quarter',sort=True))]:
                for field in FLOW:
                    values=f[field].where(f.status.eq('AVAILABLE'))
                    d=values.describe(percentiles=[.05,.1,.25,.5,.75,.9,.95]).to_dict()
                    describe.append(dict(period=period,feature=field,states=len(f),unavailable=int(f.status.ne('AVAILABLE').sum()),
                        missing=int(values.isna().sum()),zero=int(values.eq(0).sum()),**d))
                    for geom in ['A1','A2','imbalance','clusters','candidates_per_cluster','nearest_support','nearest_resistance','distance_difference','volatility','recent_return']:
                        if geom in f:
                            paired=pd.DataFrame({'flow':values,'geometry':f[geom]}).dropna()
                            corr=paired.flow.rank().corr(paired.geometry.rank()) if paired.flow.nunique()>1 and paired.geometry.nunique()>1 else np.nan
                            correlations.append(dict(period=period,flow=field,geometry=geom,spearman=corr,pairs=int((values.notna()&f[geom].notna()).sum())))
            pd.DataFrame(describe).to_csv(folder/'distributions.csv',index=False);pd.DataFrame(correlations).to_csv(folder/'correlations.csv',index=False)
            for field in FLOW:
                values=frame[field].where(frame.status.eq('AVAILABLE'));m=model[field]
                schemes={'decile':buckets(values,m['decile'])}
                if m['ventile_supported']:schemes['ventile']=buckets(values,m['ventile'])
                if field in DELTA:schemes.update(sign=sign(values),shape=shape(values,m['positive_cut']))
                for scheme,fb in schemes.items():
                    tab=summary(frame,arrays,conds['ALL'],fb,base)
                    observed=pd.DataFrame({'flow_bucket':fb,'value':values}).query('flow_bucket >= 0').groupby('flow_bucket').value.agg(['min','median','max']).reset_index()
                    tab=tab.merge(observed.rename(columns={'min':'observed_flow_min','median':'observed_flow_median','max':'observed_flow_max'}),on='flow_bucket',validate='many_to_one')
                    tab.to_parquet(folder/f'curve-{field}-{scheme}.parquet',index=False,compression='zstd');total_files+=1
                if field not in INCREMENTAL:continue
                scheme='shape' if field in DELTA else 'quartile'
                fb=shape(values,m['positive_cut']) if field in DELTA else buckets(values,m['quartile'])
                for name,cond in conds.items():
                    if name=='ALL':continue
                    tab=summary(frame,arrays,cond,fb,base)
                    tab.to_parquet(folder/f'within-{name}-{field}.parquet',index=False,compression='zstd');total_files+=1
                    if config[0]=='A' and field in DELTA and name in ['A1','imbalance','clusters']:
                        intervals(frame,arrays,cond,fb).to_csv(folder/f'ci-{name}-{field}.csv',index=False)
            print('FLOW_ANALYSIS',phase,config,window,'hours',flush=True)
    write_json(dest/'complete.json',dict(status='COMPLETE',summary_partitions=total_files,event_count=len(events),outcome_rows=len(outcomes),plan_id=identity(PLAN)))

def freeze():
    if read(ROOT/'development/analysis/complete.json')['status']!='COMPLETE':raise ValueError('Finalize development first')
    files={str(p.relative_to(ROOT)):sha256(p) for p in sorted((ROOT/'development').rglob('*')) if p.is_file()}
    code={p.name:sha256(p) for p in sorted(CODE.glob('*.py')) if p.name not in ['reports.py','audit.py']}
    result=dict(plan=PLAN,files=files,code=code)
    write_json(ROOT/'development-freeze.json',dict(**result,freeze_id=identity(result)))
    print('FROZEN',identity(result),flush=True)

def refresh_correlations(phase):
    """Reproduce marginal correlations from saved, outcome-free state tables."""
    if phase=='replication':check_freeze()
    for folder in sorted((ROOT/phase/'analysis').iterdir()):
        if not folder.is_dir():continue
        frame=pd.read_parquet(folder/'states.parquet');rows=[]
        for period,f in [('ALL',frame),*list(frame.groupby('quarter',sort=True))]:
            for field in FLOW:
                for geom in ['A1','A2','imbalance','clusters','candidates_per_cluster','nearest_support','nearest_resistance','distance_difference','volatility','recent_return']:
                    if geom not in f:continue
                    paired=pd.DataFrame({'flow':f[field].where(f.status.eq('AVAILABLE')),'geometry':f[geom]}).dropna()
                    corr=paired.flow.rank().corr(paired.geometry.rank()) if paired.flow.nunique()>1 and paired.geometry.nunique()>1 else np.nan
                    rows.append(dict(period=period,flow=field,geometry=geom,spearman=corr,pairs=len(paired)))
        pd.DataFrame(rows).to_csv(folder/'correlations.csv',index=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['development','replication','freeze']);args=p.parse_args()
    freeze() if args.phase=='freeze' else analyze(args.phase)
