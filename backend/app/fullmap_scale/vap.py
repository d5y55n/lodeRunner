"""Same rolling VAP arithmetic, compact hourly views instead of tiny DataFrames."""
import numpy as np
from app.fullmap.volume import RollingVAP
from app.fullmap.contract import HOUR,LOOKBACK


class HourView:
    def __init__(self,index,values):self.index=index;self.values=values
    def to_numpy(self):return self.values


class FastVAP(RollingVAP):
    def __init__(self,hourly,bin_size,lookback=LOOKBACK,quarantines=()):
        if not np.isfinite(bin_size) or bin_size<=0 or lookback<=0 or lookback%HOUR:raise ValueError('Invalid bin/window configuration')
        if hourly.empty or hourly.duplicated(['hour','bin']).any():raise ValueError('Missing/duplicate hourly VAP')
        if np.any(hourly.hour.to_numpy()%HOUR):raise ValueError('Hourly alignment required')
        values=hourly[['quantity','buy','sell']].to_numpy()
        if not np.isfinite(values).all() or (values<0).any():raise ValueError('Invalid VAP quantities')
        if not np.allclose(hourly.quantity,hourly.buy+hourly.sell,rtol=1e-9,atol=1e-9):raise ValueError('VAP side quantities do not conserve total')
        # Stable hour sort preserves per-hour row order from the reference groupby.
        order=np.argsort(hourly.hour.to_numpy(),kind='stable');hours=hourly.hour.to_numpy()[order]
        bins=hourly.bin.to_numpy()[order];values=values[order]
        unique,starts=np.unique(hours,return_index=True);ends=np.r_[starts[1:],len(hours)]
        self.hours={int(t):HourView(bins[a:b],values[a:b]) for t,a,b in zip(unique,starts,ends)}
        self.bin_size=bin_size;self.lookback=lookback;self.quarantines=quarantines
        self.total={};self.t=None;self.bin_occurrences={}
