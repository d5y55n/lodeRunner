"""Narrow H1-H4 comparisons; exact hierarchy, not any-k agreement search."""
from itertools import product
import numpy as np
import pandas as pd
from app.multimap.analyze import arrays,quartiles,buckets
from app.confluence.analyze import block_arrays,contrast,METRICS,GRID
from .contract import *


def fit(frame):
    model={tf:quartiles(frame[tf+'__imbalance'].abs()) for tf in TFS}
    model['quantity']=quartiles(frame.joint_quantity.where(frame.flow_status.eq('AVAILABLE')))
    for pattern,side in [('SSSS','support'),('RRRR','resistance')]:
        selected=frame.pattern.eq(pattern)
        for field in ['strength_minimum','strength_median','strength_maximum']:
            model[pattern+'/'+field]=quartiles(frame.loc[selected,field])
        d=frame[[tf+'__nearest_'+side+'_absolute_distance' for tf in TFS]].max(axis=1,skipna=False)
        model[pattern+'/distance_max']=quartiles(d[selected])
    return model


def definitions(frame,model):
    masks={};meta={};comparisons=[]
    def add(name,mask,family,priority,direction='BOTH'):
        masks[name]=np.asarray(mask,dtype=bool);meta[name]=dict(family=family,priority=priority,interpretation=direction)
        return name
    def cmp(name,a,b,family,priority,direction):comparisons.append((name,a,b,family,priority,direction))
    add('all',np.ones(len(frame),bool),'baseline','primary')
    for pattern in map(''.join,product('SRNM',repeat=4)):
        add('pattern/'+pattern,frame.pattern.eq(pattern),'exact_pattern','primary' if pattern in ['SSSS','RRRR'] else 'secondary')
    for pattern,side,char,direction in [('SSSS','support','S','LONG'),('RRRR','resistance','R','SHORT')]:
        condition=frame.pattern.eq(pattern).to_numpy();anchor='pattern/'+pattern
        for subset in PATHS:
            selected=np.all(np.array([frame[tf+'__state'].eq(char).to_numpy() for tf in subset]),axis=0)
            name=add(side+'/path/'+'+'.join(subset),selected,'hierarchy','primary' if subset in HIERARCHY else 'secondary',direction)
            if subset not in HIERARCHY:cmp(name+'/vs_all',name,'all','secondary_paths','secondary',direction)
        for i,base in enumerate(['all']+[side+'/path/'+'+'.join(s) for s in HIERARCHY[:-1]]):
            cmp(pattern+'/vs_baseline_'+str(i),anchor,base,'all_four_baselines','primary',direction)
        for order in range(1,4):
            lower=side+'/path/'+'+'.join(HIERARCHY[order-1]);higher=side+'/path/'+'+'.join(HIERARCHY[order])
            cmp(side+f'/hierarchy/{order}_to_{order+1}',higher,lower,'hierarchy_increment','primary',direction)
            other=add(side+f'/hierarchy/{order}/added_not_aligned',masks[lower]&~masks[higher]&frame[HIERARCHY[order][-1]+'__state'].ne('M').to_numpy(),
                      'conditional_hierarchy','primary',direction)
            cmp(side+f'/hierarchy/{order}/added_agrees_vs_not',higher,other,'conditional_hierarchy','primary',direction)
        native=[]
        for tf in TFS:
            b=buckets(frame[tf+'__imbalance'].abs(),model[tf]);native.append(b)
            for k in range(-1,len(model[tf])+1):
                add(f'{pattern}/native/{tf}/Q{k}',condition&(b==k),'native_strength','primary',direction)
            cmp(f'{pattern}/native/{tf}/high_minus_low',f'{pattern}/native/{tf}/Q{len(model[tf])}',f'{pattern}/native/{tf}/Q0','native_strength','primary',direction)
        native=np.array(native).T;upper=np.array([len(model[tf]) for tf in TFS])
        missing=np.any(native<0,axis=1);strong_count=np.sum(native==upper,axis=1)
        weak=np.all(native==0,axis=1);strong=np.all(native==upper,axis=1)
        medium=np.all((native>0)&(native<upper),axis=1)
        for label,mask in [('all_weak',weak),('all_medium',medium),('all_strong',strong),('mixed',~(weak|medium|strong|missing)),('missing',missing)]:
            add(pattern+'/strength/'+label,condition&mask,'strength_configuration','primary',direction)
        for k in range(5):add(f'{pattern}/Q4_count/{k}',condition&(strong_count==k)&~missing,'Q4_count','primary',direction)
        for k in range(1,5):
            hi=add(f'{pattern}/Q4_at_least/{k}',condition&(strong_count>=k)&~missing,'strength_configuration','primary',direction)
            lo=add(f'{pattern}/Q4_below/{k}',condition&(strong_count<k)&~missing,'strength_configuration','primary',direction)
            cmp(f'{pattern}/Q4_threshold/{k}',hi,lo,'strength_configuration','primary',direction)
        cmp(pattern+'/all_strong_minus_all_weak',pattern+'/strength/all_strong',pattern+'/strength/all_weak','strength_configuration','primary',direction)
        for field in ['strength_minimum','strength_median','strength_maximum']:
            cuts=model[pattern+'/'+field];b=buckets(frame[field],cuts)
            for k in range(-1,len(cuts)+1):add(f'{pattern}/{field}/Q{k}',condition&(b==k),'summary_strength','primary',direction)
            cmp(f'{pattern}/{field}/high_minus_low',f'{pattern}/{field}/Q{len(cuts)}',f'{pattern}/{field}/Q0','summary_strength','primary',direction)
        close=np.all(frame[[tf+'__nearest_'+side+'_in_full_band' for tf in TFS]].to_numpy(),axis=1)
        yes=add(pattern+'/geometry/all_close',condition&close,'geometry','secondary',direction)
        no=add(pattern+'/geometry/any_not_close',condition&~close,'geometry','secondary',direction)
        cmp(pattern+'/geometry/close_minus_not',yes,no,'geometry','secondary',direction)
        maximum=frame[[tf+'__nearest_'+side+'_absolute_distance' for tf in TFS]].max(axis=1,skipna=False)
        cuts=model[pattern+'/distance_max'];b=buckets(maximum,cuts)
        for k in range(-1,len(cuts)+1):add(f'{pattern}/distance/Q{k}',condition&(b==k),'geometry','secondary',direction)
        cmp(pattern+'/distance/far_minus_near',f'{pattern}/distance/Q{len(cuts)}',f'{pattern}/distance/Q0','geometry','secondary',direction)
        q=buckets(frame.joint_quantity.where(frame.flow_status=='AVAILABLE'),model['quantity'])
        for label,mask in [('low',q==0),('medium',(q>0)&(q<len(model['quantity']))),('high',q==len(model['quantity'])),('missing',q<0)]:
            add(pattern+'/quantity/'+label,condition&mask,'quantity','secondary',direction)
        cmp(pattern+'/quantity/high_minus_low',pattern+'/quantity/high',pattern+'/quantity/low','quantity','secondary',direction)
        for other in (['SSSR','SSSN','SSRR','SSNN','RSSS'] if char=='S' else ['RRRS','RRRN','RRSS','RRNN','SRRR']):
            cmp(pattern+'/vs_conflict/'+other,anchor,'pattern/'+other,'conflict','secondary',direction)
    return masks,meta,comparisons


def slope_from_sums(a):
    n,sx,sxx,sy,sxy=np.moveaxis(a,-1,0)
    with np.errstate(divide='ignore',invalid='ignore'):
        denom=sxx-sx*sx/n
        result=.1*(sxy-sx*sy/n)/denom
    return np.where((n>=2)&(denom>1e-14),result,np.nan)


def continuous(frame,values,grids,wi,weights,metrics,quarters):
    rows=[];nw=weights.shape[1]
    for pattern,direction in [('SSSS','LONG'),('RRRR','SHORT')]:
        for field in ['strength_minimum','strength_median','strength_maximum']:
            x=frame[field].to_numpy(dtype=float)
            condition=frame.pattern.eq(pattern).to_numpy()&np.isfinite(x)
            for period in ['ALL',1,2,3,4]:
                base=condition if period=='ALL' else condition&(quarters==period)
                for gi,grid in enumerate(grids):
                    if grid[0]!=direction:continue
                    selected=base&(values['complete'][:,gi]>0)
                    xx=x[selected];week=wi[selected];n=len(xx);blocks=len(np.unique(week))
                    for mi,metric in enumerate(METRICS):
                        y=metrics[selected,gi,mi]
                        sums=np.zeros((nw,5))
                        np.add.at(sums,week,np.column_stack((np.ones(n),xx,xx*xx,y,xx*y)))
                        point=float(slope_from_sums(sums.sum(axis=0)))
                        lo=hi=np.nan;finite=0
                        if period=='ALL' and blocks>=5:
                            draws=slope_from_sums(weights@sums);draws=draws[np.isfinite(draws)];finite=len(draws)
                            if finite>=950:lo,hi=np.quantile(draws,[.025,.975])
                        rows.append(dict(pattern=pattern,feature=field,period=str(period),**dict(zip(GRID,grid)),metric=metric,
                            slope_per_point_one=point,ci_low=lo,ci_high=hi,N_complete=n,week_blocks=blocks,
                            supported=n>=200 and blocks>=5,finite_bootstrap_draws=finite))
    return pd.DataFrame(rows)


def execute(phase):
    guard(phase);dest=ROOT/phase;out=dest/'analysis'
    if (out/'complete.json').exists():return
    if read(dest/'classification-audit.json')['status']!='PASS':raise ValueError('Audit before outcomes required')
    out.mkdir(exist_ok=True)
    frame=pd.read_parquet(dest/'states.parquet')
    sources=Sources(phase)
    outcomes=pd.concat([sources.frame(p) for p in sorted((PROJECT/'data/phase4/15m'/phase/'future-outcomes').glob('*.parquet'))],ignore_index=True)
    joined=outcomes.merge(frame[['event_id','decision_timestamp']],on='event_id',suffixes=('','_state'),validate='many_to_one')
    if len(joined)!=len(frame)*24 or not joined.decision_timestamp.eq(joined.decision_timestamp_state).all():raise ValueError('Outcome reuse mismatch')
    grids,values=arrays(frame[['event_id']],outcomes,'15m');sources.save()
    write(dest/'outcome-reuse.json',dict(status='EXACT_EXISTING_ROWS',rows=len(outcomes),events=len(frame),hashes=sources.hashes))
    model=fit(frame) if phase=='development' else read(ROOT/'development/analysis/buckets.json')
    write(out/'buckets.json',model)
    masks,meta,comparisons=definitions(frame,model)
    definition=dict(metadata=meta,comparisons=comparisons)
    if phase=='replication' and json.loads(canonical(definition))!=read(ROOT/'development/analysis/definitions.json'):
        raise ValueError('Replication category/comparison change')
    write(out/'definitions.json',definition)
    quarters=pd.to_datetime(frame.decision_timestamp,unit='ms',utc=True).dt.quarter.to_numpy()
    wi,weeks,weights,metrics=block_arrays(frame,values)
    rows=[]
    for name,mask in masks.items():
        for period in ['ALL',1,2,3,4]:
            selected=mask if period=='ALL' else mask&(quarters==period)
            totals={k:v[selected].sum(axis=0) for k,v in values.items()}
            for gi,g in enumerate(grids):
                complete=totals['complete'][gi]
                blocks=len(np.unique(wi[selected&(values['complete'][:,gi]>0)]))
                r=dict(category=name,**meta[name],period=str(period),**dict(zip(GRID,g)),N=int(selected.sum()),
                    complete=int(complete),censored=int(totals['censored'][gi]),week_blocks=blocks,supported=complete>=200 and blocks>=5)
                for m in METRICS:
                    r[m]=float((totals[m] if m in totals else totals[m+'_sum'])[gi]/complete) if complete else np.nan
                rows.append(r)
    summary=pd.DataFrame(rows);summary.to_parquet(out/'cohorts.parquet',index=False);summary.to_csv(out/'cohorts.csv',index=False)
    effects=[]
    for ci,(name,a,b,family,priority,direction) in enumerate(comparisons):
        for period in ['ALL',1,2,3,4]:
            select=np.ones(len(frame),bool) if period=='ALL' else quarters==period
            for r in contrast(masks[a]&select,masks[b]&select,values,wi,weights,metrics,grids,bootstrap=period=='ALL'):
                if r['direction']==direction:
                    effects.append(dict(comparison=name,a=a,b=b,family=family,priority=priority,period=str(period),**r))
        if (ci+1)%20==0:print('CURRENT_P_CONTRASTS',phase,ci+1,len(comparisons),flush=True)
    contrasts=pd.DataFrame(effects);contrasts.to_parquet(out/'contrasts.parquet',index=False);contrasts.to_csv(out/'contrasts.csv',index=False)
    slopes=continuous(frame,values,grids,wi,weights,metrics,quarters)
    slopes.to_parquet(out/'continuous-strength.parquet',index=False);slopes.to_csv(out/'continuous-strength.csv',index=False)
    vector=frame[['event_id','decision_timestamp','pattern']+[tf+'__imbalance' for tf in TFS]+['strength_minimum','strength_median','strength_maximum']].copy()
    for tf in TFS:vector[tf+'__native_quantile']=buckets(frame[tf+'__imbalance'].abs(),model[tf])
    vector['native_Q4_count']=sum((vector[tf+'__native_quantile']==len(model[tf])).astype(int) for tf in TFS)
    vector.to_parquet(out/'strength-vectors.parquet',index=False)
    appendix=frame[frame.pattern.isin(['SSSS','RRRR'])&frame.flow_status.eq('AVAILABLE')].groupby('pattern')[['joint_delta','support_delta','resistance_delta','support_normalized_delta','resistance_normalized_delta']].agg(['count','mean','median'])
    appendix.to_csv(out/'delta-appendix.csv')
    write(out/'complete.json',dict(status='COMPLETE',categories=len(masks),comparisons=len(comparisons),summary_rows=len(summary),contrast_rows=len(contrasts),
        hashes={p.name:digest(p) for p in out.iterdir() if p.is_file() and p.name!='complete.json'}))
    print('CURRENT_P_ANALYSIS_COMPLETE',phase,len(masks),len(comparisons),flush=True)
