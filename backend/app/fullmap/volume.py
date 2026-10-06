"""Incremental full rolling observed VAP, not isolated hourly D candidates."""
import numpy as np
import pandas as pd
from app.research.models import identity
from .contract import HOUR,LOOKBACK,configuration,state_identity,permitted


def bin_trades(trades,start,end,bin_size):
    permitted(start,end)
    if bin_size<=0:raise ValueError('Positive bin width required')
    result={}
    for t in trades:
        if start<=t.timestamp<end:
            b=int(np.floor(t.price/bin_size));v=result.setdefault(b,np.zeros(3))
            v+=np.array([t.quantity,0 if t.buyer_is_maker else t.quantity,t.quantity if t.buyer_is_maker else 0])
    return result


class RollingVAP:
    def __init__(self,hourly,bin_size,lookback=LOOKBACK,quarantines=()):
        if not np.isfinite(bin_size) or bin_size<=0 or lookback<=0 or lookback%HOUR:raise ValueError('Invalid bin/window configuration')
        if hourly.empty:raise ValueError('Missing hourly VAP')
        if hourly.duplicated(['hour','bin']).any():raise ValueError('Duplicate hour/bin')
        if np.any(hourly.hour.to_numpy()%HOUR):raise ValueError('Hourly alignment required')
        if not np.isfinite(hourly[['quantity','buy','sell']].to_numpy()).all():raise ValueError('Invalid VAP quantities')
        if (hourly[['quantity','buy','sell']]<0).any().any():raise ValueError('Negative VAP quantities')
        if not np.allclose(hourly.quantity,hourly.buy+hourly.sell,rtol=1e-9,atol=1e-9):raise ValueError('VAP side quantities do not conserve total')
        self.hours={int(t):g.set_index('bin')[['quantity','buy','sell']] for t,g in hourly.groupby('hour',sort=True)}
        self.bin_size=bin_size;self.lookback=lookback;self.quarantines=quarantines
        self.total={};self.t=None;self.bin_occurrences={}

    def add(self,hour,sign):
        if hour not in self.hours:raise ValueError('Missing complete hourly trade coverage')
        frame=self.hours[hour]
        for b,row in zip(frame.index,frame.to_numpy()):
            b=int(b);self.total[b]=self.total.get(b,np.zeros(3))+sign*row
            self.bin_occurrences[b]=self.bin_occurrences.get(b,0)+sign
            if self.bin_occurrences[b]==0:
                del self.total[b];del self.bin_occurrences[b]

    def advance(self,t):
        if t%HOUR:raise ValueError('Hourly decision required')
        permitted(t-self.lookback,t)
        if self.t is None:
            for hour in range(t-self.lookback,t,HOUR):self.add(hour,1)
        else:
            if t!=self.t+HOUR:raise ValueError('Advance exactly one closed candle')
            self.add(self.t-self.lookback,-1);self.add(self.t,1)
        self.t=t

    def snapshot(self,t,price,multiple=1.5):
        if price<=0 or not np.isfinite(price):raise ValueError('Invalid decision price')
        if not np.isfinite(multiple) or multiple<=0:raise ValueError('Invalid concentration multiplier')
        self.advance(t)
        cfg=configuration('D',dict(bin_size=self.bin_size,concentration_multiple=multiple),lookback=self.lookback)
        eid,sid=state_identity(cfg,t,price);mean=sum(v[0] for v in self.total.values())/len(self.total)
        rows=[];above=below=crossing=0.;concentration_above=concentration_below=0.
        for b,v in sorted(self.total.items()):
            low=b*self.bin_size;high=(b+1)*self.bin_size;q,buy,sell=map(float,v)
            relation='ABOVE' if low>=price else 'BELOW' if high<=price else 'STRADDLES'
            ratio=q/mean if mean else None;concentrated=bool(mean>0 and q>=mean*multiple)
            if relation=='ABOVE':above+=q;concentration_above+=q if concentrated else 0
            elif relation=='BELOW':below+=q;concentration_below+=q if concentrated else 0
            else:crossing+=q
            rows.append(dict(snapshot_id=sid,candidate_id=identity(['D-neutral-bin','BTCUSDT',self.bin_size,b]),
                bin_lower=float(low),bin_upper=float(high),quantity=q,buy=buy,sell=sell,delta=buy-sell,
                concentration=ratio,concentrated=concentrated,relation=relation,kind='NEUTRAL'))
        bad=[[max(t-self.lookback,a),min(t,b)] for a,b in self.quarantines if a<t and b>t-self.lookback]
        totals=np.asarray(list(self.total.values())).sum(axis=0)
        snapshot=dict(snapshot_id=sid,event_id=eid,symbol='BTCUSDT',timeframe='1h',decision_timestamp=t,decision_price=price,
            lookback_start=t-self.lookback,lookback_end=t,detector='D',detector_parameters=cfg['parameters'],
            configuration_id=cfg['configuration_id'],known_candidate_count=len(rows),support_count=None,resistance_count=None,
            known_candidate_ids=[r['candidate_id'] for r in rows],contributing_candidate_ids=[],native_score=None,
            representations=['ROLLING_OBSERVED_VOLUME_AT_PRICE'],price_coverage_complete=True,
            raw=dict(nearest_support=None,nearest_resistance=None,neutral_bins_above=sum(r['relation']=='ABOVE' for r in rows),
                neutral_bins_below=sum(r['relation']=='BELOW' for r in rows),concentration_region_count=sum(r['concentrated'] for r in rows),
                bin_intervals='half-open; adjacent bins disjoint; no directional clusters'),
            volume=dict(observation_start=t-self.lookback,observation_end=t,total_quantity=float(totals[0]),
                buy=float(totals[1]),sell=float(totals[2]),delta=float(totals[1]-totals[2]),
                above_quantity=above,below_quantity=below,straddling_quantity=crossing,
                concentrated_above_quantity=concentration_above,concentrated_below_quantity=concentration_below,
                coverage_status='INCOMPLETE_OBSERVABLE_COVERAGE' if bad else 'VERIFIED_SOURCE_COVERAGE',
                quarantine_intersections=bad,eligible_complete_coverage_comparison=not bool(bad),
                interpretation='observed aggregate-trade quantity only; no reconstruction or interpolation'))
        return snapshot,rows
