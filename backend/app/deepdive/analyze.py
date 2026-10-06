"""Multiplicity-preserving, event-balanced descriptive summaries; no ranking."""
import json
import numpy as np
import pandas as pd
from .design import ROOT, design
from .prepare import a_configs, context_columns


def percent_bucket(values, groups):
    v=np.asarray(values,dtype=float);out=np.zeros(len(v),dtype=np.int16)
    valid=np.isfinite(v)
    out[valid]=np.minimum((v[valid]*groups).astype(int)+1,groups)
    return out


def weights_for(events, buckets, n_events, n_buckets):
    return np.bincount(np.asarray(buckets,dtype=np.int64)*n_events+np.asarray(events,dtype=np.int64),minlength=n_events*n_buckets).reshape(n_buckets,n_events).astype(float)


def memberships(frame,event_index):
    codes=event_index.get_indexer(frame.event_id)
    if np.any(codes<0):raise ValueError('Unknown event')
    n=len(event_index);metadata=[];matrices=[];baselines={}
    p=frame.historical_delta_percentile.to_numpy().copy()
    p[frame.percentile_history_rows.to_numpy()<design()['minimum_history_rows']]=np.nan
    rowp=frame.historical_row_percentile.to_numpy().copy()
    rowp[frame.percentile_history_rows.to_numpy()<design()['minimum_history_rows']]=np.nan
    norm=frame.normalized_delta.to_numpy();delta=frame.volume_delta.to_numpy()
    facets=[('ALL','ALL',np.ones(len(frame),dtype=bool))]
    for col in ['visit_group','quarter','volatility_regime','return_regime']:
        facets.extend((col,str(value),frame[col].to_numpy()==value) for value in sorted(frame[col].unique()))
    def add(family,facet,value,mask,buckets,labels):
        w=weights_for(codes[mask],buckets[mask],n,len(labels))
        for i,label in enumerate(labels):
            metadata.append(dict(family=family,facet=facet,facet_value=value,bucket=str(label)))
        matrices.append(w)
    for facet,value,mask in facets:
        baselines[(facet,value)]=len(metadata)
        add('A_ALONE',facet,value,mask,np.zeros(len(frame),dtype=int),['ALL'])
        add('decile',facet,value,mask,percent_bucket(p,10),['MISSING',*range(1,11)])
        if facet!='ALL':continue
        for name,vals,k in [('ventile',p,20),('quartile',p,4),('row_ecdf_decile',rowp,10)]:
            add(name,facet,value,mask,percent_bucket(vals,k),['MISSING',*range(1,k+1)])
        add('legacy_quartile',facet,value,mask,frame.legacy_delta_quartile.to_numpy(),['MISSING',1,2,3,4])
        nb=np.where(np.isfinite(norm),np.clip(np.floor((np.nan_to_num(norm)+1)*5).astype(int)+1,1,10),0)
        add('normalized_delta',facet,value,mask,nb,['MISSING',*range(1,11)])
        for epsilon in [0.,.01,.05,.10]:
            b=np.where(~np.isfinite(norm),0,np.where(norm < -epsilon,1,np.where(norm>epsilon,3,2)))
            add(f'normalized_sign_{epsilon:g}',facet,value,mask,b,['MISSING','NEGATIVE','NEAR_ZERO','POSITIVE'])
        b=np.where(~np.isfinite(delta),0,np.where(delta<0,1,np.where(delta>0,3,2)))
        add('raw_sign',facet,value,mask,b,['MISSING','NEGATIVE','ZERO','POSITIVE'])
        for low,high in design()['rolling_windows']:
            selected=mask&np.isfinite(p)&(p>=low)&((p<high)|(high==1))
            add('rolling_visual_only',facet,value,selected,np.zeros(len(frame),dtype=int),[f'{low:.2f}-{high:.2f}'])
    return pd.DataFrame(metadata),np.vstack(matrices),baselines


def match_indices(times,cells,eligible,horizon):
    """No outcomes or delta enter matching. All arrays use timestamp order."""
    times=np.asarray(times);result=np.full(len(times),-1,dtype=np.int64)
    for cell in sorted(set(cells[eligible])):
        if 'CALIBRATION' in cell:continue
        indices=np.flatnonzero(eligible&(cells==cell))
        position=np.searchsorted(times[indices],times[indices]-horizon*3600000,side='right')-1
        valid=position>=0
        result[indices[valid]]=indices[position[valid]]
    return result


def safe_ratio(a,b):
    a,b=np.broadcast_arrays(np.asarray(a,dtype=float),np.asarray(b,dtype=float))
    return np.divide(a,b,out=np.full(a.shape,np.nan),where=b>0)


def movement(weights,values,complete):
    valid=complete&np.isfinite(values)
    order=np.argsort(np.where(valid,values,np.inf),kind='stable')
    w=weights[:,order]*valid[order];count=w.sum(axis=1)
    cumulative=np.cumsum(w,axis=1);rank=(count-1)/2
    lo=(cumulative<=np.floor(rank)[:,None]).sum(axis=1)
    hi=(cumulative<=np.ceil(rank)[:,None]).sum(axis=1)
    lo=np.minimum(lo,len(values)-1);hi=np.minimum(hi,len(values)-1)
    ordered=values[order]
    med=(ordered[lo]+ordered[hi])/2
    med[count==0]=np.nan
    mean=safe_ratio(weights@np.where(valid,values,0.),weights@valid.astype(float))
    return mean,med


def summarize_matrix(meta,weights,baselines,events,outcomes):
    present=weights>0;binary=present.astype(float)
    count=weights.sum(axis=1);unique=present.sum(axis=1)
    times=events.timestamp.to_numpy()
    cells=(events.volatility_regime+'|'+events.return_regime).to_numpy()
    match_cache={};movement_cache={};results=[];links=[]
    for key,labels in outcomes.groupby(['direction','tp','sl','horizon'],sort=True):
        direction,tp,sl,h=key
        labels=labels.set_index('event_id').reindex(events.index)
        if labels.censored.isna().any():raise ValueError('Missing outcome')
        complete=~labels.censored.to_numpy(dtype=bool);values=labels.label.to_numpy()
        ccount=weights@complete.astype(float);ecount=binary@complete.astype(float)
        result=meta.copy();result['direction']=direction;result['tp']=tp;result['sl']=sl;result['horizon']=h
        result['measurement_count']=count.astype(np.int64);result['unique_event_count']=unique
        result['complete_measurement_count']=ccount.astype(np.int64);result['complete_unique_events']=ecount.astype(np.int64)
        result['censored_rate']=safe_ratio(count-ccount,count)
        result['event_balanced_censored_rate']=safe_ratio(unique-ecount,unique)
        for label in ['TP_FIRST','SL_FIRST','NEITHER','AMBIGUOUS']:
            mask=complete&(values==label)
            result[label.lower()+'_rate']=safe_ratio(weights@mask.astype(float),ccount)
            result['event_balanced_'+label.lower()+'_rate']=safe_ratio(binary@mask.astype(float),ecount)
        for field in ['mfe_pct','mae_pct']:
            mk=(direction,h,field)
            if mk not in movement_cache:movement_cache[mk]=movement(weights,labels[field].to_numpy(),complete)
            result[field+'_mean'],result[field+'_median']=movement_cache[mk]
        for prefix in ['', 'event_balanced_']:
            t=result[prefix+'tp_first_rate'];s=result[prefix+'sl_first_rate']
            result[prefix+'gross_expectancy_conditional_pct']=safe_ratio((t*tp-s*sl)*100,t+s)
        rate=result.event_balanced_tp_first_rate.to_numpy()
        result['A_alone_event_tp_rate']=rate[baselines[('ALL','ALL')]]
        baseids=np.asarray([baselines[(r.facet,r.facet_value)] for r in meta.itertuples()])
        result['facet_A_alone_event_tp_rate']=rate[baseids]
        result['delta_vs_A_alone']=rate-result.A_alone_event_tp_rate
        result['delta_vs_facet_A_alone']=rate-result.facet_A_alone_event_tp_rate
        paired=[]
        for g,row in enumerate(meta.itertuples()):
            mk=(row.facet,row.facet_value,int(h))
            if mk not in match_cache:
                eligible=present[baselines[(row.facet,row.facet_value)]]
                mapping=match_indices(times,cells,eligible,int(h));match_cache[mk]=mapping
                valid=np.flatnonzero(mapping>=0)
                links.append(pd.DataFrame(dict(target_index=valid,control_index=mapping[valid],
                    facet=row.facet,facet_value=row.facet_value,horizon=int(h))))
            mapping=match_cache[mk];target=np.flatnonzero(present[g]&(mapping>=0));control=mapping[target]
            valid=complete[target]&complete[control];target=target[valid];control=control[valid]
            target_rate=float(np.mean(values[target]=='TP_FIRST')) if len(target) else np.nan
            control_rate=float(np.mean(values[control]=='TP_FIRST')) if len(control) else np.nan
            paired.append(dict(matched_complete_targets=len(target),unique_control_events=len(np.unique(control)),
                unmatched_or_censored_targets=int(unique[g]-len(target)),
                matched_target_tp_rate=target_rate,matched_control_tp_rate=control_rate,
                matched_incremental_tp=target_rate-control_rate))
        result=pd.concat([result,pd.DataFrame(paired)],axis=1)
        result['sufficient_unique_events']=result.unique_event_count>=100
        result['visualization_only']=result.family=='rolling_visual_only'
        results.append(result)
    return pd.concat(results,ignore_index=True),pd.concat(links,ignore_index=True)


def analyze(phase,root=ROOT):
    dest=root/phase
    if not (dest/'prepared.json').exists():raise ValueError('Preparation required')
    outdir=dest/'summary-parts';outdir.mkdir(exist_ok=True)
    events=pd.read_parquet(dest/'events.parquet').sort_values('timestamp').reset_index(drop=True)
    events['observed_at']=events.timestamp
    events=context_columns(events,json.loads((root/'context-model.json').read_text())).set_index('event_id')
    events.to_parquet(dest/'event-index.parquet')
    outcomes=pd.read_parquet(dest/'future_outcomes.parquet')
    for cfg in a_configs():
        cid=cfg['configuration_id'];frame=pd.read_parquet(dest/'features'/f'{cid}.parquet')
        for kind in ['ALL','SUPPORT','RESISTANCE']:
            path=outdir/f'{cid}-{kind}.parquet'
            if path.exists():continue
            selected=frame if kind=='ALL' else frame[frame.kind==kind]
            meta,w,base=memberships(selected,events.index)
            table,links=summarize_matrix(meta,w,base,events,outcomes)
            table['configuration_id']=cid;table['width_model']=cfg['width_model'];table['width_parameter']=cfg['width_parameter']
            table['kind']=kind;table['period']=phase
            table.to_parquet(path,index=False)
            links.to_parquet(outdir/f'{cid}-{kind}-controls.parquet',index=False)
            print('ANALYZED',phase,cfg['width_parameter'],kind,len(table),flush=True)
    tables=[pd.read_parquet(p) for p in sorted(outdir.glob('*.parquet')) if not p.name.endswith('-controls.parquet')]
    table=pd.concat(tables,ignore_index=True).sort_values(['configuration_id','kind','family','facet','facet_value','bucket','direction','tp','sl','horizon'])
    table.to_parquet(dest/'summary.parquet',index=False)
    table.to_csv(dest/'summary.csv',index=False,float_format='%.12g',lineterminator='\n')
    return table
