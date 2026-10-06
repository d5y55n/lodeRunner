"""Causal explanatory features only; these never change native A1 membership."""
import numpy as np
from app.fullmap.contract import HOUR

AGE_BOUNDS=[30*24,180*24,365*24]
AGE_LABELS=['recent_0_30d','medium_30_180d','old_180_365d','very_old_over_365d']


class Crossings:
    def __init__(self,engine):
        self.engine=engine;self.ends=np.asarray(engine.reference.ends);self.close=np.asarray(engine.close)
        self.low=np.asarray(engine.low);self.high=np.asarray(engine.high);self.cache={}

    def history(self,index,t):
        if index not in self.cache:
            known=self.engine.known[index];price=self.engine.prices[index]
            first=int(np.searchsorted(self.ends,known,side='right'))
            # Equality is not a strict crossing; contact visits are separate runs.
            previous=self.close[first-1:-1] if first else self.close[:0]
            current=self.close[first:]
            cross=((previous<price)&(current>price))|((previous>price)&(current<price))
            touch=(self.low[first:]<=price)&(self.high[first:]>=price)
            starts=touch&~np.r_[False,touch[:-1]]
            self.cache[index]=(self.ends[first:][cross],self.ends[first:][starts],self.ends[first:][touch])
        crosses,visits,touches=self.cache[index]
        n=int(np.searchsorted(touches,t,side='right'))
        return (int(np.searchsorted(crosses,t,side='right')),int(np.searchsorted(visits,t,side='right')),
                (t-touches[n-1])/HOUR if n else None)

    def features(self,members,t,price):
        e=self.engine;prices=e.prices[members]
        full=(price<prices*1.004)&(price>prices*.996)
        half=((price>=prices*1.004)&(price<prices*1.006))|((price<=prices*.996)&(price>prices*.994))
        nearby=members[full|half];result={};values=[]
        for i in nearby:
            values.append(self.history(int(i),t))
        ages=(t-e.sources[nearby])/HOUR
        for j,label in enumerate(AGE_LABELS):
            mask=np.searchsorted(AGE_BOUNDS,ages,side='left')==j
            chosen=np.flatnonzero(mask)
            result[label]=dict(count=int(mask.sum()),support=int((e.kinds[nearby[mask]]==1).sum()),
                resistance=int((e.kinds[nearby[mask]]==-1).sum()),
                mean_crossings=float(np.mean([values[k][0] for k in chosen])) if len(chosen) else None,
                mean_visits=float(np.mean([values[k][1] for k in chosen])) if len(chosen) else None)
        last=[v[2] for v in values if v[2] is not None]
        result.update(mean_prior_crossings=float(np.mean([v[0] for v in values])) if values else None,
            mean_prior_visits=float(np.mean([v[1] for v in values])) if values else None,
            mean_hours_since_last_contact=float(np.mean(last)) if last else None,
            crossing_definition='strict consecutive closed-close side change after known_at; ties excluded',
            visit_definition='start of a contiguous closed-candle high/low contact run after known_at',
            as_of=t)
        for label,mask in [('full',full),('half',half)]:
            result[label+'_mean_source_age_hours']=float(np.mean((t-e.sources[members[mask]])/HOUR)) if mask.any() else None
        return result
