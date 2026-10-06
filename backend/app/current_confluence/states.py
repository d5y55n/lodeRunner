"""Same-P evaluation, retaining unchanged native A candidate memberships."""
import numpy as np
import pandas as pd
from app.fullmap_scale.storage import restore
from app.fullmap.core import contribution
from app.confluence.geometry import latest_indices
from .contract import *

NATIVE_COLUMNS=['source_timestamp','snapshot_id','event_id','source_price','A1','A2','imbalance',
    'support_count','resistance_count','nearby_support_count','nearby_resistance_count',
    'nearest_support','nearest_resistance','coverage_complete','flow_status','observation_start','observation_end',
    'joint_quantity','joint_delta','support_delta','resistance_delta','support_normalized_delta','resistance_normalized_delta']


def classify(s,r,available=True):
    return 'M' if not available or s+r==0 else 'S' if s>r else 'R' if r>s else 'N'


def evaluate(prices,kinds,known,source_times,P,width,available=True,reference=False):
    if not np.isfinite(P) or P<=0:raise ValueError('Invalid current P')
    if reference:
        weights=np.array([contribution(float(p),P,width) for p in prices])
    else:
        full=(P<prices*(1+width))&(P>prices*(1-width))
        half=((P>=prices*(1+width))&(P<prices*(1+1.5*width)))|((P<=prices*(1-width))&(P>prices*(1-1.5*width)))
        weights=np.where(full,1.,np.where(half,.5,0.))
    row=dict(evaluation_price=float(P),available=bool(available))
    full_counts=[];half_counts=[]
    for side,kind in [('support','SUPPORT'),('resistance','RESISTANCE')]:
        match=kinds==kind;indices=np.flatnonzero(match)
        fc=int(np.sum((weights==1)&match));hc=int(np.sum((weights==.5)&match))
        row[side+'_count']=fc+hc;row[side+'_full_count']=fc;row[side+'_half_count']=hc
        row['full_map_'+side+'_count']=len(indices);full_counts.append(fc);half_counts.append(hc)
        if len(indices):
            if reference:
                idx=min(indices,key=lambda i:(abs(prices[i]-P),known[i],source_times[i],prices[i]))
            else:
                distances=np.abs(prices[indices]-P)
                ties=indices[distances==distances.min()]
                idx=ties[np.lexsort((prices[ties],source_times[ties],known[ties]))[0]]
            row['nearest_'+side]=float(prices[idx])
            row['nearest_'+side+'_distance']=float(prices[idx]/P-1)
            row['nearest_'+side+'_absolute_distance']=float(abs(prices[idx]/P-1))
            row['nearest_'+side+'_in_full_band']=bool(contribution(float(prices[idx]),P,width)==1)
        else:
            row['nearest_'+side]=None;row['nearest_'+side+'_distance']=None
            row['nearest_'+side+'_absolute_distance']=None;row['nearest_'+side+'_in_full_band']=False
    s,r=row['support_count'],row['resistance_count']
    row.update(raw_difference=s-r,imbalance=(s-r)/(s+r) if available and s+r else None,
        A1=float(full_counts[0]-full_counts[1]+.5*(half_counts[0]-half_counts[1])),
        A2=float(full_counts[0]-full_counts[1]),state=classify(s,r,available))
    return row


def from_15m(r):
    s,res=int(r.nearby_support_count),int(r.nearby_resistance_count)
    row=dict(evaluation_price=float(r.source_price),available=bool(r.coverage_complete),
        support_count=s,resistance_count=res,raw_difference=s-res,imbalance=r.imbalance,
        A1=r.A1,A2=r.A2,state=classify(s,res,r.coverage_complete),
        full_map_support_count=int(r.support_count),full_map_resistance_count=int(r.resistance_count))
    for side in ['support','resistance']:
        p=r['nearest_'+side]
        row['nearest_'+side]=p
        row['nearest_'+side+'_distance']=p/r.source_price-1 if pd.notna(p) else None
        row['nearest_'+side+'_absolute_distance']=abs(p/r.source_price-1) if pd.notna(p) else None
        row['nearest_'+side+'_in_full_band']=bool(pd.notna(p) and contribution(p,r.source_price,WIDTHS['15m'])==1)
    return row


class Memberships:
    def __init__(self,sources,tf,native):
        self.sources=sources;self.tf=tf;self.native=native.set_index('source_timestamp')
        base=PROJECT/'data/phase3r1'/sources.phase if tf=='1h' else PROJECT/'data/phase4'/tf/sources.phase
        self.folder=base/('1d8c70797dfb' if tf=='1h' else 'A')
        cat_path=base/('catalog-A/candidate-catalog.parquet' if tf=='1h' else 'candidate-catalog.parquet')
        cat=sources.frame(cat_path).set_index('candidate_index')
        cat=cat.reindex(range(int(cat.index.max())+1))
        self.prices=cat.price.to_numpy();self.kinds=cat.kind.to_numpy()
        self.known=cat.known_at.to_numpy();self.source_times=cat.source_timestamp.to_numpy()
        self.dependency=cat.dependency_start.to_numpy()
        self.iterator=self.records();self.pending=next(self.iterator,None);self.current=None;self.parity=0

    def records(self):
        for p in sorted(self.folder.glob('*-membership.parquet')):
            f=self.sources.frame(p)
            for record,(sid,ids) in zip(f.itertuples(),restore(f)):
                yield int(record.timestamp),sid,ids

    def at(self,t):
        while self.pending is not None and self.pending[0]<=t:
            stamp,sid,ids=self.pending
            r=self.native.loc[stamp]
            if sid!=r.snapshot_id or not np.all(self.known[ids]<=stamp) or not np.all(self.dependency[ids]>=stamp-850*86400000):
                raise ValueError('Membership identity, future candidate or lookback mismatch')
            if len(ids)!=int(r.support_count+r.resistance_count):raise ValueError('Full native membership count changed')
            args=(self.prices[ids],self.kinds[ids],self.known[ids],self.source_times[ids])
            v=evaluate(*args,r.source_price,WIDTHS[self.tf])
            for field,expected in [('support_count',r.nearby_support_count),('resistance_count',r.nearby_resistance_count),('A1',r.A1),('A2',r.A2)]:
                if v[field]!=expected:raise ValueError('Frozen native source-price parity failed '+field)
            for side in ['support','resistance']:
                if not np.isclose(v['nearest_'+side],r['nearest_'+side],equal_nan=True):raise ValueError('Nearest native parity')
            self.parity+=1;self.current=(stamp,sid,args)
            self.pending=next(self.iterator,None)
        if self.current is None or not 0<=t-self.current[0]<STEPS[self.tf]:raise ValueError('Missing/stale source state')
        return self.current


def audit_examples(frame,natives,sources):
    choices={};patterns=frame.pattern
    conditions={'SSSS':patterns.eq('SSSS'),'RRRR':patterns.eq('RRRR'),
        'mixed':patterns.str.contains('S')&patterns.str.contains('R'),
        'neutral':patterns.str.contains('N'),'missing':patterns.str.contains('M')}
    for label,mask in conditions.items():choices[label]=frame.index[mask][:3].tolist()
    selected=set(np.linspace(0,len(frame)-1,16,dtype=int))
    for indices in choices.values():selected.update(indices)
    for step in STEPS.values():
        boundary=frame.index[frame.decision_timestamp%step==0]
        for i in boundary[np.linspace(0,len(boundary)-1,min(4,len(boundary)),dtype=int)]:
            selected.update(j for j in [i-1,i,i+1] if 0<=j<len(frame))
    engines={tf:Memberships(sources,tf,natives[tf]) for tf in TFS}
    rows=[];day_cache={}
    fields=['support_count','resistance_count','raw_difference','imbalance','A1','A2','nearest_support_distance','nearest_resistance_distance']
    for i in sorted(selected):
        r=frame.iloc[i];t=int(r.decision_timestamp);p=float(r.decision_price)
        for tf in TFS:
            ts=natives[tf].source_timestamp.to_numpy()
            index,ok=latest_indices(ts,[t],STEPS[tf])
            if not ok[0]:raise ValueError('Audit source unavailable')
            source=natives[tf].iloc[index[0]];stamp=int(source.source_timestamp);sid=source.snapshot_id
            day=pd.Timestamp(stamp,unit='ms',tz='UTC').strftime('%Y-%m-%d')
            engine=engines[tf]
            if tf not in day_cache or day_cache[tf][0]!=day:
                memberships=sources.frame(engine.folder/(day+'-membership.parquet'))
                day_cache[tf]=(day,dict(restore(memberships)))
            ids=day_cache[tf][1][sid]
            if not np.all(engine.known[ids]<=stamp):raise ValueError('Future audit candidate')
            args=(engine.prices[ids],engine.kinds[ids],engine.known[ids],engine.source_times[ids])
            reference=evaluate(*args,p,WIDTHS[tf],reference=True)
            for field in fields:
                a,b=reference[field],r[tf+'__'+field]
                if not (pd.isna(a) and pd.isna(b)) and not np.isclose(a,b,rtol=1e-12,atol=1e-12):
                    raise ValueError('Current-P reference parity '+tf+'/'+field)
            if reference['state']!=r[tf+'__state']:raise ValueError('Current-P pattern differs from reference')
            truncated=ts[ts<=t]
            ix,valid=latest_indices(truncated,[t],STEPS[tf])
            if not valid[0] or truncated[ix[0]]!=stamp:raise ValueError('Truncation alignment')
            rows.append(dict(T=t,P=p,timeframe=tf,source_timestamp=stamp,source_age_ms=t-stamp,
                pattern=r.pattern,**reference,reference_equal=True,truncated_source_equal=True))
    # Empty current-price structure is a valid M, never inferred as neutral.
    empty=evaluate(np.array([]),np.array([],dtype=str),np.array([]),np.array([]),100.,WIDTHS['1h'],reference=True)
    if empty['state']!='M':raise ValueError('Missing classification fixture failed')
    return pd.DataFrame(rows),dict(real_examples={k:len(v) for k,v in choices.items()},
        real_missing_pattern_count=int(conditions['missing'].sum()),synthetic_empty_M=empty,
        absent_real_types=[k for k,v in choices.items() if not v],no_outcomes_read=True)


def execute(phase):
    initialize();sources=Sources(phase);dest=ROOT/phase;dest.mkdir(exist_ok=True)
    if (dest/'states-complete.json').exists():return
    natives={tf:sources.frame(PROJECT/'data/phase5'/phase/'native'/(tf+'.parquet'),columns=NATIVE_COLUMNS).sort_values('source_timestamp').reset_index(drop=True) for tf in TFS}
    low=natives['15m'];times=low.source_timestamp.to_numpy()
    lo,hi=(START,REP) if phase=='development' else (REP,END)
    if not ((times>=lo)&(times<hi)).all() or not np.all(np.diff(times)==STEPS['15m']):raise ValueError('Wrong decision clock')
    indices={}
    for tf,n in natives.items():
        ix,ok=latest_indices(n.source_timestamp,times,STEPS[tf])
        if not ok.all():raise ValueError('Native alignment unavailable')
        indices[tf]=ix
    engines={tf:Memberships(sources,tf,natives[tf]) for tf in TFS if tf!='15m'}
    rows=[];changed={tf:0 for tf in TFS};native_closes={tf:0 for tf in TFS}
    for i,t in enumerate(times):
        lr=low.iloc[i];p=float(lr.source_price)
        row=dict(decision_timestamp=int(t),decision_price=p,event_id=lr.event_id)
        old_pattern='';pattern=''
        for tf in TFS:
            old=natives[tf].iloc[indices[tf][i]]
            old_state=classify(int(old.nearby_support_count),int(old.nearby_resistance_count),old.coverage_complete)
            if tf=='15m':v=from_15m(lr);stamp=int(t);sid=lr.snapshot_id
            else:
                stamp,sid,args=engines[tf].at(int(t))
                if sid!=old.snapshot_id:raise ValueError('Alignment/membership source mismatch')
                v=evaluate(*args,p,WIDTHS[tf],available=old.coverage_complete)
            if v['evaluation_price']!=p:raise ValueError('A timeframe used a different current P')
            if t%STEPS[tf]==0:
                if p!=old.source_price or v['state']!=old_state or v['A1']!=old.A1 or v['A2']!=old.A2:
                    raise ValueError('Shared-close native parity failed')
                native_closes[tf]+=1
            changed[tf]+=v['state']!=old_state
            v.update(source_timestamp=int(stamp),source_age_ms=int(t-stamp),snapshot_id=sid,
                native_source_price=float(old.source_price),old_carried_state=old_state,
                old_carried_imbalance=old.imbalance,old_carried_A1=old.A1,old_carried_A2=old.A2)
            for k,value in v.items():row[tf+'__'+k]=value
            pattern+=v['state'];old_pattern+=old_state
        row['pattern']=pattern;row['phase5_carried_pattern']=old_pattern
        for field in ['flow_status','observation_start','observation_end','joint_quantity','joint_delta','support_delta','resistance_delta','support_normalized_delta','resistance_normalized_delta']:
            row[field]=lr[field]
        if row['observation_end']!=t:raise ValueError('Future flow observation')
        vector=np.abs(np.array([row[tf+'__imbalance'] for tf in TFS],dtype=float))
        for label,fn in [('minimum',np.min),('median',np.median),('maximum',np.max)]:
            row['strength_'+label]=float(fn(vector)) if np.isfinite(vector).all() else np.nan
        rows.append(row)
        if (i+1)%5000==0:print('CURRENT_P_STATES',phase,i+1,len(times),flush=True)
    frame=pd.DataFrame(rows)
    frame.to_parquet(dest/'states.parquet',index=False,compression='zstd')
    audit,details=audit_examples(frame,natives,sources)
    audit.to_csv(dest/'classification-examples.csv',index=False)
    audit.to_parquet(dest/'classification-examples.parquet',index=False)
    details.update(status='PASS',same_P_all_timeframes=True,reference_checks=len(audit),
        changed_from_phase5_by_timeframe=changed,changed_pattern_timestamps=int(frame.pattern.ne(frame.phase5_carried_pattern).sum()),
        shared_native_close_parity=native_closes,native_source_price_parity={tf:e.parity for tf,e in engines.items()},
        phase5_15m_reused_rows=len(frame),source_maps_rebuilt=False,no_spatial=True)
    write(dest/'classification-audit.json',details);sources.save()
    write(dest/'states-complete.json',dict(status='COMPLETE',timestamps=len(frame),first=int(times[0]),last=int(times[-1]),
        hashes={p.name:digest(p) for p in [dest/'states.parquet',dest/'classification-examples.csv',dest/'classification-examples.parquet',dest/'classification-audit.json']}))
    print('CURRENT_P_AUDIT_PASS',phase,details['changed_pattern_timestamps'],flush=True)
