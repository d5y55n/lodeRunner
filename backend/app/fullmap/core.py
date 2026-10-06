"""Reference-first rolling reconstruction. All score comparisons match JS strictly."""
from bisect import bisect_right
import heapq
import numpy as np
from app.research.models import validate_candles
from app.research.detectors import make_detector
from .contract import HOUR,LOOKBACK,WIDTHS,configuration,state_identity,permitted


def contribution(price,current,width):
    if current<price*(1+width) and current>price*(1-width):return 1.
    if ((current>=price*(1+width) and current<price*(1+1.5*width)) or
        (current<=price*(1-width) and current>price*(1-1.5*width))):return .5
    return 0.


def score_candidates(candidates,current,width):
    counts={f'{weight}_{kind}_count':0 for weight in ['full_weight','half_weight'] for kind in ['support','resistance']}
    contributors=[];long=0.
    for c in candidates:
        weight=contribution(c.price,current,width)
        if not weight:continue
        sign=1 if c.kind=='SUPPORT' else -1
        counts[f'{"full_weight" if weight==1 else "half_weight"}_{c.kind.lower()}_count']+=1
        long+=sign*weight
        contributors.append(dict(candidate_id=c.id,weight=weight,long_contribution=sign*weight,short_contribution=-sign*weight))
    return dict(long_score=long,short_score=-long,
        full_weight_only_long=float(counts['full_weight_support_count']-counts['full_weight_resistance_count']),
        full_weight_only_short=float(counts['full_weight_resistance_count']-counts['full_weight_support_count']),
        support_contribution_count=counts['full_weight_support_count']+counts['half_weight_support_count'],
        resistance_contribution_count=counts['full_weight_resistance_count']+counts['half_weight_resistance_count'],
        **counts),contributors


def union_intervals(intervals):
    result=[]
    for low,high in sorted(intervals):
        if result and low<=result[-1][1]:result[-1][1]=max(result[-1][1],high)
        else:result.append([low,high])
    return result


def cluster_features(candidates,width):
    intervals=sorted((c.price*(1-width),c.price*(1+width)) for c in candidates)
    active=[];pairs=0
    for low,high in intervals:
        while active and active[0]<low:heapq.heappop(active)
        pairs+=len(active);heapq.heappush(active,high)
    return dict(cluster_count=len(union_intervals(intervals)),overlap_pair_count=pairs,
                duplicate_reference_price_count=len(candidates)-len(set(c.price for c in candidates)))


def raw_map(candidates,current,width,t):
    result={};nearby=[]
    for kind in ['SUPPORT','RESISTANCE']:
        cs=[c for c in candidates if c.kind==kind]
        counts=dict(total=len(cs),above=0,below=0,near=0)
        density=dict(inner=0,outer=0,one_point_five_to_three_widths=0,three_to_ten_widths=0,beyond_ten=0)
        for c in cs:
            weight=contribution(c.price,current,width)
            if weight==1:counts['near']+=1
            elif c.price>current:counts['above']+=1
            else:counts['below']+=1
            if weight:
                density['inner' if weight==1 else 'outer']+=1;nearby.append(c)
            else:
                distance=abs(current/c.price-1)
                name='one_point_five_to_three_widths' if distance<3*width else 'three_to_ten_widths' if distance<10*width else 'beyond_ten'
                density[name]+=1
        nearest=min(cs,key=lambda c:(abs(c.price-current),c.known_at,c.source_timestamp,c.price)) if cs else None
        result[kind.lower()]=dict(**counts,density=density,
            nearest_price=nearest.price if nearest else None,
            nearest_candidate_id=nearest.id if nearest else None,
            nearest_signed_distance_fraction=(nearest.price/current-1) if nearest else None,
            nearest_absolute_distance_fraction=abs(nearest.price/current-1) if nearest else None,
            mean_absolute_distance_fraction=float(np.mean([abs(c.price/current-1) for c in cs])) if cs else None)
    ages=[(t-c.source_timestamp)/HOUR for c in nearby]
    result['nearby_age_hours']={k:float(v) for k,v in zip(['min','median','mean','max'],
        [min(ages),np.median(ages),np.mean(ages),max(ages)])} if ages else None
    result.update(cluster_features(candidates,width))
    result['nearby_candidate_ids']=[c.id for c in nearby]
    return result,nearby


class FullMapEngine:
    def __init__(self,candles,lookback=LOOKBACK,timeframe='1h'):
        if timeframe!='1h':raise ValueError('First deliverable executes 1h only')
        validate_candles(candles)
        if any(c.end-c.start!=HOUR for c in candles):raise ValueError('Expected exact closed hourly candles')
        if lookback<=0 or lookback%HOUR:raise ValueError('Lookback must be positive whole hours')
        if not candles:raise ValueError('No candles')
        permitted(candles[0].start,candles[-1].end)
        self.candles=candles;self.ends=[c.end for c in candles]
        self.lookback=lookback;self.timeframe=timeframe;self.catalog={}

    def window(self,t):
        if t%HOUR or t>self.ends[-1]:raise ValueError('Decision requires an available hourly close')
        right=bisect_right(self.ends,t);left=right-self.lookback//HOUR
        if left<0 or right==0 or self.candles[right-1].end!=t:raise ValueError('INSUFFICIENT_850_DAY_HISTORY')
        permitted(t-self.lookback,t)
        cs=self.candles[left:right]
        if cs[0].start!=t-self.lookback:raise ValueError('Incomplete rolling coverage')
        return cs

    def snapshot(self,t,detector,parameters,profile=None):
        cs=self.window(t);price=cs[-1].close
        cfg=configuration(detector,parameters,self.timeframe,self.lookback)
        candidates=make_detector(detector,parameters).detect(cs,self.timeframe,t)
        source_starts={c.id:c.start for c in cs}
        for c in candidates:
            if c.known_at>t or c.source_timestamp<t-self.lookback:raise ValueError('Noncausal candidate')
            if any(cid not in source_starts for cid in c.source_ids):raise ValueError('Candidate dependency outside window')
            self.catalog[c.id]=dict(candidate_id=c.id,detector=c.detector,kind=c.kind,price=c.price,
                source_timestamp=c.source_timestamp,known_at=c.known_at,timeframe=c.timeframe,
                source_ids=list(c.source_ids),metadata=c.metadata,
                dependency_start=min(source_starts[cid] for cid in c.source_ids))
        raw,nearby=raw_map(candidates,price,cfg['proximity_half_width'],t)
        native,contributions=score_candidates(candidates,price,cfg['proximity_half_width']) if detector=='A' else (None,[])
        eid,sid=state_identity(cfg,t,price)
        snapshot=dict(snapshot_id=sid,event_id=eid,symbol='BTCUSDT',timeframe=self.timeframe,
            decision_timestamp=t,decision_price=price,lookback_start=t-self.lookback,lookback_end=t,
            detector=detector,detector_parameters=parameters,configuration_id=cfg['configuration_id'],
            known_candidate_count=len(candidates),support_count=raw['support']['total'],resistance_count=raw['resistance']['total'],
            known_candidate_ids=[c.id for c in candidates],contributing_candidate_ids=[r['candidate_id'] for r in contributions],
            representations=['A_ORIGINAL_FULL_MAP','RAW_FULL_MAP'] if detector=='A' else ['RAW_FULL_MAP'],
            native_score=native,raw=raw,price_coverage_complete=True,
            volume=nearby_volume(nearby,price,cfg['proximity_half_width'],t,profile) if profile is not None else None)
        return snapshot,[dict(snapshot_id=sid,**r) for r in contributions]


def nearby_volume(candidates,current,width,t,profile):
    # Distinct price unions avoid repeatedly counting trades at overlapping levels.
    intervals={kind:union_intervals([(c.price*(1-width),c.price*(1+width)) for c in candidates if c.kind==kind])
               for kind in ['SUPPORT','RESISTANCE']}
    intervals['JOINT']=union_intervals(intervals['SUPPORT']+intervals['RESISTANCE'])
    result=dict(observation_start=t-HOUR,observation_end=t,window='last closed hour, not 850 days',
                status='QUARANTINED' if profile.quarantined(t-HOUR,t) else 'AVAILABLE')
    for kind,spans in intervals.items():
        if result['status']!='AVAILABLE':result[kind.lower()]=None;continue
        totals=np.zeros(3)
        for low,high in spans:
            row=profile.quantity(t-HOUR,low,high)
            if row is None:raise ValueError('Missing hourly profile')
            totals+=np.array([row['quantity'],row['aggressive_buy_quantity'],row['aggressive_sell_quantity']])
        q,b,s=totals
        result[kind.lower()]=dict(quantity=float(q),buy=float(b),sell=float(s),delta=float(b-s),
                                normalized_delta=float((b-s)/q) if q>0 else None,union_interval_count=len(spans))
    if result['status']=='AVAILABLE':
        result['shared_support_resistance_quantity']=result['support']['quantity']+result['resistance']['quantity']-result['joint']['quantity']
    return result
