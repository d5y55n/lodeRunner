"""Native-timeframe zone-union flow. Profiles retain exact observed trade prices."""
import argparse
import json
import numpy as np
import pandas as pd
from app.fullmap.core import union_intervals
from app.fullmap_scale.storage import restore
from app.research.phase3_profiles import Profiles
from app.research.phase3_engine import load_coverage
from .contract import *
from .profiles import Profiles15m, SOURCE, DEST
from .run import key


class CachedProfiles15m(Profiles15m):
    """Reuse identical flow windows across detectors, bounded to one UTC decision day."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.window_day=None;self.windows={}

    def window(self,decision_time,candles):
        day=decision_time//86400000
        if day!=self.window_day:
            self.windows={};self.window_day=day
        key=(decision_time,candles)
        if key not in self.windows:self.windows[key]=super().window(decision_time,candles)
        return self.windows[key]

    def interval(self,start,decision_time):
        step=STEPS['15m'];permitted(start,start+step)
        if start%step or start+step>decision_time or decision_time>=FINAL_START:
            raise ValueError('Future or unaligned profile')
        date=pd.Timestamp(start,unit='ms',tz='UTC').strftime('%Y-%m-%d')
        if date not in self.days:return super().interval(start,decision_time)
        manifest=self.manifests[date[:7]]
        if any(start<b and start+step>a for a,b in manifest['quarantines']):return None
        self.days.move_to_end(date);frame=self.days[date]
        left=np.searchsorted(frame.start.to_numpy(),start,side='left')
        right=np.searchsorted(frame.start.to_numpy(),start,side='right')
        return None if left==right else frame.iloc[left:right]


def spans(prices, kinds, current, width):
    full=(current<prices*(1+width)) & (current>prices*(1-width))
    half=((current>=prices*(1+width)) & (current<prices*(1+1.5*width))) | (
        (current<=prices*(1-width)) & (current>prices*(1-1.5*width)))
    nearby=full|half
    result={side:union_intervals([(float(p*(1-width)),float(p*(1+width)))
        for p in prices[nearby & (kinds==kind)]])
        for side,kind in [('support','SUPPORT'),('resistance','RESISTANCE')]}
    result['joint']=union_intervals(result['support']+result['resistance'])
    return result


def measure_flow(profile, tf, t, window, intervals, quarantines):
    if window not in FLOW_CANDLES[tf] or t%STEPS[tf] or t>=FINAL_START:
        raise ValueError('Undeclared or non-native flow clock')
    start=t-window*STEPS[tf];permitted(start,t)
    status='AVAILABLE'
    quarter=None
    if any(start<b and t>a for a,b in quarantines):status='QUARANTINED'
    elif tf=='15m':
        quarter=profile.window(t,window)
        if quarter is None:status='MISSING_PROFILE'
    elif any(profile.hour(h) is None for h in range(start,t,HOUR)):
        status='MISSING_PROFILE'
    result=dict(timeframe=tf,decision_timestamp=t,observation_start=start,observation_end=t,
                native_flow_candles=window,flow_hours=(t-start)/HOUR,flow_status=status)
    if status=='AVAILABLE' and tf=='15m':
        # A window is identical for all detectors and sides; build its cumulative sums once.
        if 'flow_prefix' not in quarter.attrs:
            quarter.attrs['flow_prefix']=(quarter.price.to_numpy(),
                np.vstack((np.zeros(3),np.cumsum(quarter[['quantity','buy','sell']].to_numpy(),axis=0))))
        prices,prefix=quarter.attrs['flow_prefix']
    for side in ['support','resistance','joint']:
        totals=np.zeros(3) if status=='AVAILABLE' else np.full(3,np.nan)
        if status=='AVAILABLE':
            if tf=='15m':
                for low,high in intervals[side]:
                    left=np.searchsorted(prices,low,side='left');right=np.searchsorted(prices,high,side='right')
                    totals+=prefix[right]-prefix[left]
            else:
                for h in range(start,t,HOUR):
                    for low,high in intervals[side]:
                        q=profile.quantity(h,low,high)
                        totals += [q['quantity'],q['aggressive_buy_quantity'],q['aggressive_sell_quantity']]
        q,b,s=totals
        for name,value in [('quantity',q),('buy',b),('sell',s),('delta',b-s),
                           ('normalized_delta',(b-s)/q if q>0 else np.nan)]:
            result[side+'_'+name]=float(value)
        result[side+'_interval_count']=len(intervals[side])
    result['shared_quantity']=result['support_quantity']+result['resistance_quantity']-result['joint_quantity']
    result['normalized_delta_difference']=result['support_normalized_delta']-result['resistance_normalized_delta']
    result['raw_delta_difference']=result['support_delta']-result['resistance_delta']
    return result


def execute(tf,phase):
    dest=ROOT/tf/phase;complete=read(dest/'price-complete.json')
    if phase=='replication' and not (ROOT/tf/'development-freeze.json').exists():
        raise ValueError('Development freeze required')
    coverage=load_coverage(SOURCE)
    start=complete['first_decision']-max(FLOW_CANDLES[tf])*STEPS[tf]
    end=complete['end_exclusive'];permitted(start,end)
    months=pd.period_range(pd.Timestamp(start,unit='ms').strftime('%Y-%m'),
                           pd.Timestamp(end-1,unit='ms').strftime('%Y-%m'),freq='M').astype(str)
    provenance={}
    for month in months:
        if tf=='15m':
            p=DEST/month/'manifest.json';m=read(p)
            if m['coverage_id']!=coverage['coverage_id'] or m['source_sha256']!=coverage['source_hashes'][month]:
                raise ValueError('Unadjudicated quarter-hour profile')
        else:
            p=SOURCE/'profiles'/(month+'.parquet')
            if sha256(p)!=coverage['source_profile_hashes'][month]:raise ValueError('Hourly profile changed')
        provenance[str(p)]=sha256(p)
    profile=CachedProfiles15m() if tf=='15m' else Profiles(SOURCE/'profiles',coverage['quarantine_intervals'])
    cat=pd.read_parquet(dest/'candidate-catalog.parquet').set_index('candidate_index')
    cat=cat.reindex(range(int(cat.index.max())+1))
    prices=cat.price.to_numpy();kinds=cat.kind.to_numpy();known=cat.known_at.to_numpy()
    for folder in ['flow','normalized-with-flow']:(dest/folder).mkdir(exist_ok=True)
    counts={};hashes={}
    for day_i,path in enumerate(sorted((dest/'normalized').glob('*.parquet'))):
        day=path.stem;rows=[]
        for name,params in CONFIGS:
            folder=dest/key(name,params)
            state_path=folder/(day+'-states.parquet');member_path=folder/(day+'-membership.parquet')
            for source in [state_path,member_path]:
                if sha256(source)!=complete['hashes'][str(source.relative_to(dest))]:raise ValueError('Price state changed')
            states=pd.read_parquet(state_path).to_dict('records')
            membership=list(restore(pd.read_parquet(member_path)))
            if len(states)!=len(membership):raise ValueError('State membership mismatch')
            for state,(sid,idx) in zip(states,membership):
                t=state['decision_timestamp']
                assert sid==state['snapshot_id'] and np.all(known[idx]<=t)
                intervals=spans(prices[idx],kinds[idx],state['decision_price'],WIDTHS[tf])
                for window in FLOW_CANDLES[tf]:
                    r=measure_flow(profile,tf,t,window,intervals,coverage['quarantine_intervals'])
                    rows.append(dict(snapshot_id=sid,event_id=state['event_id'],**r))
                    label=f'{key(name,params)}/{window}/{r["flow_status"]}';counts[label]=counts.get(label,0)+1
        f=pd.DataFrame(rows);out=dest/'flow'/path.name;f.to_parquet(out,index=False,compression='zstd')
        hashes[str(out.relative_to(dest))]=sha256(out)
        common=pd.read_parquet(path).drop(columns=['quantity','delta','flow_status'])
        first=f[f.native_flow_candles==1].drop(columns=['event_id','timeframe','decision_timestamp'])
        common=common.merge(first,on='snapshot_id',how='left',validate='one_to_one')
        common['quantity']=common.joint_quantity;common['delta']=common.joint_delta
        out=dest/'normalized-with-flow'/path.name;common.to_parquet(out,index=False,compression='zstd')
        hashes[str(out.relative_to(dest))]=sha256(out)
        if (day_i+1)%30==0:print('NATIVE_FLOW_PROGRESS',tf,phase,day_i+1,flush=True)
    write_json(dest/'flow-complete.json',dict(status='COMPLETE',counts=counts,hashes=hashes,
        source_hashes=provenance,coverage_id=coverage['coverage_id'],code_sha256=sha256(__file__),no_2024=True))
    print('NATIVE_FLOW_COMPLETE',tf,phase,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('timeframe',choices=list(HORIZONS))
    p.add_argument('phase',choices=['development','replication']);a=p.parse_args();execute(a.timeframe,a.phase)
