"""Compact candidate catalog and vector geometry with unchanged reference rules."""
from bisect import bisect_right
from dataclasses import asdict
import numpy as np
from app.research.detectors import make_detector,ConfirmedReversal
from app.fullmap.contract import HOUR,LOOKBACK,configuration,state_identity
from app.fullmap.core import FullMapEngine,nearby_volume


class Engine:
    def __init__(self,candles,lookback=LOOKBACK):
        self.reference=FullMapEngine(candles,lookback=lookback)
        self.cs=candles;self.lookback=lookback;self.n=lookback//HOUR
        self.high=[c.high for c in candles];self.low=[c.low for c in candles];self.close=[c.close for c in candles]
        self.catalog=[];self.ids=[];self.objects=[];self.index={};self.c_cache={};self.fixed={}
        self.capacity=max(1024,len(candles)*16)
        self.prices=np.empty(self.capacity);self.kinds=np.empty(self.capacity,dtype=np.int8)
        self.sources=np.empty(self.capacity,dtype=np.int64);self.known=np.empty(self.capacity,dtype=np.int64)
        self.dependencies=np.empty(self.capacity,dtype=np.int64)
        starts={c.id:c.start for c in candles}
        for name,params in [('A',{}),('B',{'width':1}),('B',{'width':2})]:
            key=(name,params.get('width',0));indices=[]
            for c in make_detector(name,params).detect(candles,'1h',candles[-1].end):
                indices.append(self.register(c,min(starts[x] for x in c.source_ids)))
            self.fixed[key]=np.asarray(indices,dtype=np.int64)
        self.trackers={}
        for fraction in [.003,.005]:
            detector=ConfirmedReversal(fraction);high=low=0;states=[];indices=[]
            for i in range(len(candles)):
                if i:
                    if self.high[i]>self.high[high]:high=i
                    elif self.close[i]<=self.high[high]*(1-fraction):
                        key=(fraction,-1,high,i)
                        c=detector.event('RESISTANCE',self.cs[high],self.high[high],self.cs[i],'1h')
                        self.c_cache[key]=self.register(c,self.cs[high].start);indices.append(self.c_cache[key]);high=i
                    if self.low[i]<self.low[low]:low=i
                    elif self.close[i]>=self.low[low]*(1+fraction):
                        key=(fraction,1,low,i)
                        c=detector.event('SUPPORT',self.cs[low],self.low[low],self.cs[i],'1h')
                        self.c_cache[key]=self.register(c,self.cs[low].start);indices.append(self.c_cache[key]);low=i
                states.append((high,low))
            self.trackers[fraction]=states;self.fixed[('C',fraction)]=np.asarray(indices,dtype=np.int64)

    def register(self,c,dependency):
        cid=c.id
        if cid in self.index:return self.index[cid]
        i=len(self.catalog)
        if i>=self.capacity:raise MemoryError('Candidate catalog capacity exceeded; never silently discard')
        self.index[cid]=i;self.ids.append(cid);self.objects.append(c)
        self.catalog.append(dict(candidate_index=i,candidate_id=cid,**asdict(c),dependency_start=dependency))
        self.prices[i]=c.price;self.kinds[i]=1 if c.kind=='SUPPORT' else -1
        self.sources[i]=c.source_timestamp;self.known[i]=c.known_at;self.dependencies[i]=dependency
        return i

    def membership(self,t,name,params):
        self.reference.window(t)
        right=bisect_right(self.reference.ends,t);left=right-self.n
        if name in ['A','B']:
            members=self.fixed[(name,params.get('width',0))]
            return members[(self.known[members]<=t)&(self.dependencies[members]>=t-self.lookback)]
        if name!='C':raise ValueError('Directional engine supports A/B/C only')
        fraction=params['reversal_fraction'];high=low=left;indices=[]
        detector=ConfirmedReversal(fraction)
        states=self.trackers.get(fraction)
        def suffix(after):
            global_indices=self.fixed[('C',fraction)]
            chosen=global_indices[(self.known[global_indices]>self.cs[after].end)&(self.known[global_indices]<=t)]
            if np.any(self.dependencies[chosen]<t-self.lookback):raise AssertionError('Synchronized suffix escaped local window')
            return np.concatenate((np.asarray(indices,dtype=np.int64),chosen))
        # Proof: C is a deterministic two-tracker automaton. Reuse a suffix only
        # after BOTH tracker indices equal the precomputed state after that bar.
        # Equal state + equal subsequent inputs implies identical future events.
        # Until synchronization, replay locally; without it, replay the full window.
        if states and states[left]==(high,low):return suffix(left)
        for i in range(left+1,right):
            if self.high[i]>self.high[high]:high=i
            elif self.close[i]<=self.high[high]*(1-fraction):
                key=(fraction,-1,high,i)
                if key not in self.c_cache:
                    c=detector.event('RESISTANCE',self.cs[high],self.high[high],self.cs[i],'1h')
                    self.c_cache[key]=self.register(c,self.cs[high].start)
                indices.append(self.c_cache[key]);high=i
            if self.low[i]<self.low[low]:low=i
            elif self.close[i]>=self.low[low]*(1+fraction):
                key=(fraction,1,low,i)
                if key not in self.c_cache:
                    c=detector.event('SUPPORT',self.cs[low],self.low[low],self.cs[i],'1h')
                    self.c_cache[key]=self.register(c,self.cs[low].start)
                indices.append(self.c_cache[key]);low=i
            if states and states[i]==(high,low):return suffix(i)
        return np.asarray(indices,dtype=np.int64)

    def raw(self,members,current,t,w):
        raw={};nearby=[];p=self.prices[members]
        full=(current<p*(1+w))&(current>p*(1-w))
        half=((current>=p*(1+w))&(current<p*(1+1.5*w)))|((current<=p*(1-w))&(current>p*(1-1.5*w)))
        weights=full.astype(float)+.5*half
        for kind,value in [('support',1),('resistance',-1)]:
            mask=self.kinds[members]==value;indices=members[mask];prices=p[mask];f=full[mask];h=half[mask]
            nearby.extend(indices[f|h].tolist());distance=np.abs(current/prices-1)
            outside=~(f|h)
            if len(indices):
                distances=np.abs(prices-current);ties=indices[distances==distances.min()]
                nearest=int(min(ties,key=lambda i:(self.known[i],self.sources[i],self.prices[i])))
                price=float(self.prices[nearest])
            else:nearest=None;price=None
            raw[kind]=dict(total=len(indices),near=int(f.sum()),above=int(((~f)&(prices>current)).sum()),
                below=int(((~f)&(prices<=current)).sum()),density=dict(inner=int(f.sum()),outer=int(h.sum()),
                    one_point_five_to_three_widths=int((outside&(distance<3*w)).sum()),
                    three_to_ten_widths=int((outside&(distance>=3*w)&(distance<10*w)).sum()),
                    beyond_ten=int((outside&(distance>=10*w)).sum())),
                nearest_price=price,nearest_candidate_id=self.ids[nearest] if nearest is not None else None,
                nearest_signed_distance_fraction=price/current-1 if price is not None else None,
                nearest_absolute_distance_fraction=abs(price/current-1) if price is not None else None,
                mean_absolute_distance_fraction=float(np.mean(np.abs(prices/current-1))) if len(prices) else None)
        age=(t-self.sources[nearby])/HOUR
        raw['nearby_age_hours']=dict(min=float(age.min()),median=float(np.median(age)),mean=float(age.mean()),max=float(age.max())) if len(age) else None
        sorted_p=np.sort(p);lower=sorted_p*(1-w);upper=sorted_p*(1+w)
        raw.update(cluster_count=int(1+np.sum(lower[1:]>upper[:-1])) if len(p) else 0,
            overlap_pair_count=int(np.sum(np.arange(len(p))-np.searchsorted(upper,lower,side='left'))),
            duplicate_reference_price_count=len(p)-len(np.unique(p)),nearby_candidate_ids=[self.ids[i] for i in nearby])
        return raw,nearby,weights

    def snapshot(self,t,name,params,profile=None):
        members=self.membership(t,name,params);price=self.cs[bisect_right(self.reference.ends,t)-1].close
        cfg=configuration(name,params,lookback=self.lookback);eid,sid=state_identity(cfg,t,price)
        raw,nearby,weights=self.raw(members,price,t,.004);native=None;contributions=[]
        if name=='A':
            counts={f'{label}_{kind}_count':int(((weights==weight)&(self.kinds[members]==sign)).sum())
                for label,weight in [('full_weight',1.),('half_weight',.5)] for kind,sign in [('support',1),('resistance',-1)]}
            long=float(np.sum(weights*self.kinds[members]));full=float(counts['full_weight_support_count']-counts['full_weight_resistance_count'])
            native=dict(long_score=long,short_score=-long,full_weight_only_long=full,full_weight_only_short=-full,
                support_contribution_count=counts['full_weight_support_count']+counts['half_weight_support_count'],
                resistance_contribution_count=counts['full_weight_resistance_count']+counts['half_weight_resistance_count'],**counts)
            contributions=[dict(snapshot_id=sid,candidate_id=self.ids[int(i)],weight=float(w),
                long_contribution=float(w*self.kinds[i]),short_contribution=float(-w*self.kinds[i])) for i,w in zip(members[weights>0],weights[weights>0])]
        snapshot=dict(snapshot_id=sid,event_id=eid,symbol='BTCUSDT',timeframe='1h',decision_timestamp=t,decision_price=price,
            lookback_start=t-self.lookback,lookback_end=t,detector=name,detector_parameters=params,configuration_id=cfg['configuration_id'],
            known_candidate_count=len(members),support_count=raw['support']['total'],resistance_count=raw['resistance']['total'],
            known_candidate_ids=[self.ids[i] for i in members],contributing_candidate_ids=[r['candidate_id'] for r in contributions],
            representations=['A_ORIGINAL_FULL_MAP','RAW_FULL_MAP'] if name=='A' else ['RAW_FULL_MAP'],native_score=native,
            raw=raw,price_coverage_complete=True,volume=nearby_volume([self.objects[i] for i in nearby],price,.004,t,profile) if profile is not None else None)
        return snapshot,contributions,members
