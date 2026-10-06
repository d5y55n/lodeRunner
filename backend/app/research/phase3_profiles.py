"""Exact observed-price quantity profiles derived solely from aggregate trades."""
from pathlib import Path
from collections import OrderedDict
import numpy as np
import pandas as pd
from .models import Candidate


class Profiles:
    def __init__(self,root,quarantine_intervals=()):
        self.root=Path(root);self.months=OrderedDict();self.quarantines=tuple(quarantine_intervals)

    def quarantined(self,start,end):
        return any(start<b and end>a for a,b in self.quarantines)

    def hour(self,timestamp):
        month=pd.Timestamp(timestamp,unit="ms",tz="UTC").strftime("%Y-%m")
        if month not in self.months:
            frame=pd.read_parquet(self.root/f"{month}.parquet")
            hours={}
            for t,g in frame.groupby("hour",sort=True):
                g=g.sort_values("price")
                g.attrs["prefix"]=np.vstack((np.zeros(3),np.cumsum(g[["quantity","buy","sell"]].to_numpy(),axis=0)))
                hours[int(t)]=g
            self.months[month]=hours
            if len(self.months)>2:self.months.popitem(last=False)
        self.months.move_to_end(month)
        return self.months[month].get(timestamp)

    def quantity(self,start,lower,upper):
        frame=self.hour(start)
        if frame is None:return None
        prices=frame.price.to_numpy()
        left,right=np.searchsorted(prices,[lower,upper],side="left")
        right=int(np.searchsorted(prices,upper,side="right"))
        q,b,s=frame.attrs["prefix"][right]-frame.attrs["prefix"][int(left)]
        return {"quantity":q,"aggressive_buy_quantity":b,"aggressive_sell_quantity":s,"volume_delta":b-s}

    def features(self,zone,timestamp,period_start):
        return self.features_bounds(zone.lower,zone.upper,zone.candidate.known_at,timestamp,period_start)

    def features_bounds(self,lower,upper,known_at,timestamp,period_start):
        if timestamp%3600000:raise ValueError("Exact hourly profiles require an aligned decision timestamp")
        if timestamp-7200000<period_start:return {"status":"MISSING_TRADE_COVERAGE"}
        if timestamp<known_at:raise ValueError("Pre-confirmation features")
        if self.quarantined(timestamp-7200000,timestamp):
            return {"status":"QUARANTINED_TRADE_COVERAGE","as_of":timestamp}
        current=self.quantity(timestamp-3600000,lower,upper)
        baseline=self.quantity(timestamp-7200000,lower,upper)
        if current is None or baseline is None:return {"status":"MISSING_TRADE_COVERAGE"}
        return {"status":"AVAILABLE",**current,"as_of":timestamp,"window_start":timestamp-3600000,
                "baseline_start":timestamp-7200000,"baseline_end":timestamp-3600000,
                "baseline_quantity":baseline["quantity"],
                "relative_zone_volume":current["quantity"]/baseline["quantity"] if baseline["quantity"] else None}

    def d_candidates(self,start,end,bin_width,multiple=1.5):
        events=[]
        for timestamp in range(start,end,3600000):
            if self.quarantined(timestamp,timestamp+3600000):continue
            frame=self.hour(timestamp)
            if frame is None:raise ValueError(f"Missing trade profile hour: {timestamp}")
            bins=frame.assign(bin=np.floor(frame.price/bin_width).astype("int64")).groupby("bin")[["quantity","buy","sell"]].sum()
            mean=float(bins.quantity.mean())
            for i,row in bins.iterrows():
                ratio=float(row.quantity/mean)
                if row.quantity>=mean*multiple:
                    lower,upper=float(i*bin_width),float((i+1)*bin_width)
                    events.append(Candidate("D","NEUTRAL",(lower+upper)/2,timestamp,timestamp+3600000,"1h",(),
                        {"bin_lower":lower,"bin_upper":upper,"quantity":float(row.quantity),
                         "buy":float(row.buy),"sell":float(row.sell),"observed_ratio":ratio,
                         "bin_size":bin_width,"window_ms":3600000,"concentration_multiple":multiple,
                         "baseline":"mean_occupied_bin_quantity","lineage":"verified_exact_price_profile"}))
        return events
