"""Exact-price union flow; no candle volume, no unavailable-hour zero fill."""
import argparse
import numpy as np
import pandas as pd
from app.fullmap.core import union_intervals
from app.fullmap_scale.storage import unpack
from app.research.phase3_profiles import Profiles
from app.research.phase3_engine import load_coverage
from .common import *

def intervals(prices,kinds,current):
    weights=np.where((current<prices*1.004)&(current>prices*.996),1.,
        np.where(((current>=prices*1.004)&(current<prices*1.006))|((current<=prices*.996)&(current>prices*.994)),.5,0.))
    selected=weights>0
    result={name:union_intervals([(float(p*.996),float(p*1.004)) for p in prices[selected&(kinds==kind)]])
        for name,kind in [('support','SUPPORT'),('resistance','RESISTANCE')]}
    result['joint']=union_intervals(result['support']+result['resistance'])
    return result

def flow(profile,t,hours,spans):
    guard(t,hours);start=t-hours*HOUR
    result=dict(observation_start=start,observation_end=t,window_hours=hours,status='AVAILABLE')
    if profile.quarantined(start,t):result['status']='QUARANTINED'
    elif any(profile.hour(h) is None for h in range(start,t,HOUR)):result['status']='MISSING_PROFILE'
    for side in ['support','resistance','joint']:
        totals=np.zeros(3)
        if result['status']=='AVAILABLE':
            for h in range(start,t,HOUR):
                for low,high in spans[side]:
                    q=profile.quantity(h,low,high)
                    totals += [q['quantity'],q['aggressive_buy_quantity'],q['aggressive_sell_quantity']]
        else:totals[:]=np.nan
        q,b,s=totals
        for name,value in [('quantity',q),('buy',b),('sell',s),('delta',b-s),('normalized_delta',(b-s)/q if q>0 else np.nan)]:
            result[side+'_'+name]=float(value)
        result[side+'_interval_count']=len(spans[side])
    result['shared_quantity']=result['support_quantity']+result['resistance_quantity']-result['joint_quantity']
    result['normalized_delta_difference']=result['support_normalized_delta']-result['resistance_normalized_delta']
    result['raw_delta_difference']=result['support_delta']-result['resistance_delta']
    result['buy_share_difference']=result['normalized_delta_difference']/2
    denom=result['support_quantity']+result['resistance_quantity']
    result['support_volume_share']=result['support_quantity']/denom if denom>0 else np.nan
    # The share denominator compares side exposures; it is NOT deduplicated total volume.
    return result

def generate(phase):
    initialize()
    if phase=='replication':check_freeze()
    start,end=bounds(phase);dest=ROOT/phase/'features';dest.mkdir(parents=True,exist_ok=True)
    coverage=load_coverage(SOURCE);profile=Profiles(SOURCE/'profiles',coverage['quarantine_intervals'])
    months=pd.date_range(pd.Timestamp(start-8*HOUR,unit='ms',tz='UTC').normalize().replace(day=1),pd.Timestamp(end-1,unit='ms',tz='UTC'),freq='MS').strftime('%Y-%m')
    source_hashes={}
    for month in months:
        if int(month[:4])>=2024:raise ValueError('Forbidden source')
        p=SOURCE/'profiles'/f'{month}.parquet';digest=sha256(p)
        if coverage['source_profile_hashes'][month]!=digest:raise ValueError('Profile differs from forensic coverage')
        source_hashes[month]=digest
    arrays={}
    for stage in ['A','BC']:
        cat=pd.read_parquet(BASE/phase/f'catalog-{stage}/candidate-catalog.parquet').set_index('candidate_index')
        cat=cat.reindex(range(int(cat.index.max())+1));arrays[stage]=(cat.price.to_numpy(),cat.kind.to_numpy(),cat.known_at.to_numpy())
    stats={};parity=0
    days=pd.date_range(pd.Timestamp(start,unit='ms',tz='UTC').normalize(),pd.Timestamp(end-1,unit='ms',tz='UTC').normalize(),freq='D')
    for day_i,day in enumerate(days):
        day=day.strftime('%Y-%m-%d')
        for config in CONFIGS:
            ck=key(config);folder=BASE/phase/ck
            states=pd.read_parquet(folder/f'{day}-states.parquet')
            memberships=pd.read_parquet(folder/f'{day}-membership.parquet');assert len(states)==len(memberships)
            prices,kinds,known=arrays['A' if config[0]=='A' else 'BC'];active=set();rows=[]
            for s,m in zip(states.to_dict('records'),memberships.to_dict('records')):
                if m['checkpoint']:active=set()
                active.difference_update(map(int,unpack(m['removed'])));active.update(map(int,unpack(m['added'])))
                idx=np.array(sorted(active),dtype=int);t=s['decision_timestamp']
                assert s['snapshot_id']==m['snapshot_id'] and start<=t<end and np.all(known[idx]<=t)
                spans=intervals(prices[idx],kinds[idx],s['decision_price'])
                for window in WINDOWS:
                    r=flow(profile,t,window,spans)
                    if window==1:
                        old=__import__('json').loads(s['volume']);assert r['status']==old['status']
                        if r['status']=='AVAILABLE':
                            for side in ['support','resistance','joint']:
                                for field in ['quantity','buy','sell','delta','normalized_delta']:
                                    value=old[side][field]
                                    assert np.isclose(r[side+'_'+field],np.nan if value is None else value,rtol=1e-10,atol=1e-8,equal_nan=True)
                        parity+=1
                    rows.append(dict(event_id=s['event_id'],snapshot_id=s['snapshot_id'],timestamp=t,**r))
                    counter=f'{ck}/{window}/{r["status"]}';stats[counter]=stats.get(counter,0)+1
            pd.DataFrame(rows).to_parquet(dest/f'{ck}-{day}.parquet',index=False,compression='zstd')
        if (day_i+1)%30==0:print('FLOW',phase,day_i+1,len(days),flush=True)
    write_json(ROOT/phase/'features-complete.json',dict(status='COMPLETE',counts=stats,one_hour_parity_rows=parity,source_profile_sha256=source_hashes,coverage_policy_sha256=sha256(SOURCE/'coverage'/'coverage-decisions.json') if (SOURCE/'coverage'/'coverage-decisions.json').exists() else identity(coverage),no_2024=True))
    print('FEATURES_COMPLETE',phase,parity,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['development','replication']);generate(p.parse_args().phase)
