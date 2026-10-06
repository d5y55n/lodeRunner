"""Native-clock adapter of the proven catalog and C state-synchronization algorithm."""
from bisect import bisect_right
import numpy as np
from app.fullmap_scale.engine import Engine as FrozenEngine
from app.fullmap.core import raw_map,score_candidates
from app.fullmap.contract import configuration,state_identity
from app.research.detectors import make_detector,ConfirmedReversal
from .contract import *

class Engine:
    register=FrozenEngine.register
    raw=FrozenEngine.raw

    def __init__(self,candles,timeframe,lookback=LOOKBACK):
        self.timeframe=timeframe;self.step=STEPS[timeframe];self.width=WIDTHS[timeframe]
        self.reference=Clock(candles,timeframe,lookback);self.cs=candles;self.lookback=lookback;self.n=lookback//self.step
        self.high=[c.high for c in candles];self.low=[c.low for c in candles];self.close=[c.close for c in candles]
        self.catalog=[];self.ids=[];self.objects=[];self.index={};self.c_cache={};self.fixed={};self.trackers={}
        self.capacity=max(1024,len(candles)*16)
        self.prices=np.empty(self.capacity);self.kinds=np.empty(self.capacity,dtype=np.int8)
        self.sources=np.empty(self.capacity,dtype=np.int64);self.known=np.empty(self.capacity,dtype=np.int64);self.dependencies=np.empty(self.capacity,dtype=np.int64)
        starts={c.id:c.start for c in candles}
        for name,params in CONFIGS[:3]:
            indices=[self.register(c,min(starts[x] for x in c.source_ids)) for c in make_detector(name,params).detect(candles,timeframe,candles[-1].end)]
            self.fixed[(name,params.get('width',0))]=np.asarray(indices,dtype=np.int64)
        for fraction in [.003,.005]:
            high=low=0;states=[];indices=[]
            for i in range(len(candles)):
                if i:
                    if self.high[i]>self.high[high]:high=i
                    elif self.close[i]<=self.high[high]*(1-fraction):
                        indices.append(self.c_event(fraction,-1,high,i));high=i
                    if self.low[i]<self.low[low]:low=i
                    elif self.close[i]>=self.low[low]*(1+fraction):
                        indices.append(self.c_event(fraction,1,low,i));low=i
                states.append((high,low))
            self.trackers[fraction]=states;self.fixed[('C',fraction)]=np.asarray(indices,dtype=np.int64)

    def c_event(self,fraction,side,source,confirmation):
        key=(fraction,side,source,confirmation)
        if key not in self.c_cache:
            c=ConfirmedReversal(fraction).event('SUPPORT' if side==1 else 'RESISTANCE',self.cs[source],
                self.low[source] if side==1 else self.high[source],self.cs[confirmation],self.timeframe)
            self.c_cache[key]=self.register(c,self.cs[source].start)
        return self.c_cache[key]

    def membership(self,t,name,params):
        self.reference.window(t);right=bisect_right(self.reference.ends,t);left=right-self.n
        if name in ['A','B']:
            a=self.fixed[(name,params.get('width',0))]
            return a[(self.known[a]<=t)&(self.dependencies[a]>=t-self.lookback)]
        if name!='C':raise ValueError('Only directional A/B/C')
        fraction=params['reversal_fraction'];states=self.trackers[fraction];high=low=left;indices=[]
        def suffix(after):
            a=self.fixed[('C',fraction)];a=a[(self.known[a]>self.cs[after].end)&(self.known[a]<=t)]
            if np.any(self.dependencies[a]<t-self.lookback):raise AssertionError('C suffix escaped rolling window')
            return np.concatenate((np.asarray(indices,dtype=np.int64),a))
        # Identical pair of tracker indices at the same bar proves an identical suffix.
        if states[left]==(high,low):return suffix(left)
        for i in range(left+1,right):
            if self.high[i]>self.high[high]:high=i
            elif self.close[i]<=self.high[high]*(1-fraction):indices.append(self.c_event(fraction,-1,high,i));high=i
            if self.low[i]<self.low[low]:low=i
            elif self.close[i]>=self.low[low]*(1+fraction):indices.append(self.c_event(fraction,1,low,i));low=i
            if states[i]==(high,low):return suffix(i)
        return np.asarray(indices,dtype=np.int64)

    def snapshot(self,t,name,params):
        members=self.membership(t,name,params);price=self.cs[bisect_right(self.reference.ends,t)-1].close
        cfg=configuration(name,params,timeframe=self.timeframe,lookback=self.lookback)
        if self.timeframe!='1h':
            cfg.pop('configuration_id');cfg['directional_volume_window_ms']=self.step;cfg['schema']='native-full-map-v1';cfg['configuration_id']=identity(cfg)
        eid,sid=state_identity(cfg,t,price);raw,nearby,weights=self.raw(members,price,t,self.width)
        native=score_candidates([self.objects[i] for i in members[weights>0]],price,self.width)[0] if name=='A' else None
        return dict(snapshot_id=sid,event_id=eid,symbol='BTCUSDT',timeframe=self.timeframe,decision_timestamp=t,
            last_closed_candle_end=t,decision_price=price,lookback_start=t-self.lookback,lookback_end=t,
            detector=name,detector_parameters=params,configuration_id=cfg['configuration_id'],
            known_candidate_count=len(members),support_count=raw['support']['total'],resistance_count=raw['resistance']['total'],
            known_candidate_ids=[self.ids[i] for i in members],native_score=native,raw=raw,price_coverage_complete=True),members

    def reference_snapshot(self,t,name,params):
        cs=self.reference.window(t);candidates=make_detector(name,params).detect(cs,self.timeframe,t)
        raw,_=raw_map(candidates,cs[-1].close,self.width,t)
        native=score_candidates(candidates,cs[-1].close,self.width)[0] if name=='A' else None
        return candidates,raw,native
