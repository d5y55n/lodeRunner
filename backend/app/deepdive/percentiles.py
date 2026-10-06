"""Exact empirical midranks; queries precede updates for every decision timestamp."""
import numpy as np
import pandas as pd
from app.research.phase3_plan import DEVELOPMENT_START, DEVELOPMENT_END


def development_only(times):
    if np.any(np.asarray(times)<DEVELOPMENT_START) or np.any(np.asarray(times)>=DEVELOPMENT_END):
        raise ValueError('Fitting accepts development observations only')


def normalized_delta(buy, sell, quantity):
    buy, sell, quantity = map(lambda x:np.asarray(x,dtype=float), (buy,sell,quantity))
    return np.divide(buy-sell, quantity, out=np.full_like(quantity,np.nan), where=quantity>0)


def block_labels(times):
    dates=pd.to_datetime(times,unit='ms',utc=True)
    return np.asarray([f'{d.year}-Q{(d.month-1)//3+1}' for d in dates])


def historical(values, times):
    """Values must be finite and sorted by time; coordinates do not fit thresholds."""
    v=np.asarray(values,dtype=float);t=np.asarray(times,dtype=np.int64)
    development_only(t)
    if np.any(~np.isfinite(v)) or np.any(np.diff(t)<0):
        raise ValueError('Finite values in chronological order required')
    levels=np.unique(v);ranks=np.searchsorted(levels,v)+1
    tree=np.zeros((len(levels)+1,2));out=np.full((len(v),2),np.nan)
    counts=np.zeros(len(v),dtype=np.int64);total=np.zeros(2)
    boundaries=np.r_[0,np.flatnonzero(t[1:]!=t[:-1])+1,len(t)]
    def query(index):
        result=np.zeros(2)
        while index:
            result+=tree[index];index-=index&-index
        return result
    for a,b in zip(boundaries,boundaries[1:]):
        unique,inverse,n=np.unique(ranks[a:b],return_inverse=True,return_counts=True)
        scores=[]
        for r in unique:
            low=query(int(r)-1);high=query(int(r))
            scores.append((low+(high-low)/2)/total if total[0] else [np.nan,np.nan])
        out[a:b]=np.asarray(scores)[inverse];counts[a:b]=int(total[0])
        for r,c in zip(unique,n):
            amount=np.array([float(c),float(c)/(b-a)])
            while r<len(tree):tree[r]+=amount;r+=r&-r
        total+=np.array([b-a,1.])
    weights=np.zeros((len(levels),2))
    for a,b in zip(boundaries,boundaries[1:]):
        np.add.at(weights[:,0],ranks[a:b]-1,1.)
        np.add.at(weights[:,1],ranks[a:b]-1,1./(b-a))
    model=pd.DataFrame(dict(delta=levels,row_weight=weights[:,0],event_weight=weights[:,1]))
    return out[:,1],out[:,0],counts,model


def frozen_percentiles(values, model):
    values=np.asarray(values,dtype=float);levels=model.delta.to_numpy()
    weights=model[['row_weight','event_weight']].to_numpy()
    prefix=np.vstack((np.zeros(2),np.cumsum(weights,axis=0)))
    lo=np.searchsorted(levels,values,side='left');hi=np.searchsorted(levels,values,side='right')
    result=(prefix[lo]+(prefix[hi]-prefix[lo])/2)/prefix[-1]
    result[~np.isfinite(values)]=np.nan
    return result[:,1],result[:,0]
