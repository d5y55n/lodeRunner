"""Independent vectorized reference against the running website API; no outcomes."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
import numpy as np
from app.website.config import PROJECT, STEPS, DAY, settings
from app.website.market import load, timestamp


def reference_stream(f, n, side):
    v=f[side].to_numpy();windows=np.lib.stride_tricks.sliding_window_view(v,2*n+1)
    neighbors=np.delete(windows,n,axis=1)
    good=(windows[:,n]>neighbors.max(axis=1)) if side=='high' else (windows[:,n]<neighbors.min(axis=1))
    src=np.full(len(f),-1,dtype=int);centers=np.where(good)[0]+n;src[centers+n]=centers
    src=np.maximum.accumulate(src);slope=np.full(len(f),np.nan);ix=np.where(src>=0)[0]
    slope[ix]=np.log(f.close.to_numpy()[ix]/v[src[ix]])/(ix-src[ix])
    return src,slope


def run():
    cfg=settings();records=[];hashes={}
    with httpx.Client(timeout=180) as client:
        for at in ['2022-12-15T12:15:00Z','2023-06-15T12:15:00Z','2023-12-15T12:00:00Z']:
            response=client.get('http://127.0.0.1:8011/analysis/btcusdt',params={'at':at});response.raise_for_status();a=response.json()
            t=timestamp(at);combined=0
            for tf in STEPS:
                f,paths=load(tf,t,cfg,'replay')
                for rel in paths:
                    assert '2024' not in rel
                    if rel not in hashes:hashes[rel]=hashlib.sha256((PROJECT/rel).read_bytes()).hexdigest()
                g=f[f.open_time>=t-cfg.history_days*DAY];o,h,l,cl=(g[k].to_numpy() for k in ['open','high','low','close'])
                resistance=(cl[:-1]>o[:-1])&(cl[1:]<o[1:]);support=(cl[:-1]<o[:-1])&(cl[1:]>o[1:])
                prices=np.where(support,np.maximum(l[:-1],l[1:]),np.minimum(h[:-1],h[1:]))
                dist=np.abs(a['price']/prices-1);inner=dist<=cfg.widths[tf]+1e-14;outer=dist<=cfg.widths[tf]*cfg.outer_multiplier+1e-14
                proximity=np.where(inner,1,np.where(outer,.5,0));age=(t-(g.close_time.to_numpy()[1:]+1))/DAY
                weight=cfg.recency_floor+(1-cfg.recency_floor)*np.exp2(-age/cfg.half_life_days)
                ws=float((proximity*weight)[support].sum());wr=float((proximity*weight)[resistance].sum());norm=(ws-wr)/(ws+wr) if ws+wr else 0
                actual=a['scoring']['timeframes'][tf]
                expected=dict(weighted_support=ws,weighted_resistance=wr,normalized=norm,legacy_score=float(proximity[support].sum()-proximity[resistance].sum()),raw_support_count=int((support&outer).sum()),raw_resistance_count=int((resistance&outer).sum()))
                for key,value in expected.items():assert np.isclose(actual[key],value,rtol=1e-10,atol=1e-10),(at,tf,key)
                combined+=norm*cfg.tf_weights[tf]
                for scale,n in cfg.swing_ns.items():
                    for side in ['high','low']:
                        src,slopes=reference_stream(f,n,side);j=len(f)-1;i=src[j];r=a['converging'][tf][scale][side]
                        if i<0:assert r['state']=='NO_CONFIRMED_SWING';continue
                        assert r['source_time']==int(f.open_time.iloc[i]) and r['elapsed_candles']==j-i
                        percentiles=[]
                        for k in [j-2,j-1,j]:
                            if src[k]!=i:percentiles.append(None);continue
                            obs=int(f.close_time.iloc[k])+1;direction=np.sign(slopes[k]);times=f.close_time.to_numpy()+1
                            hist=np.abs(slopes[(times<obs)&(times>=obs-cfg.converging_history_days*DAY)&(slopes*direction>0)])
                            percentiles.append(float(((hist<abs(slopes[k])).sum()+.5*(hist==abs(slopes[k])).sum())/len(hist)*100) if len(hist)>=cfg.min_distribution_samples and direction else None)
                        for got,ref in zip(r['recent_percentiles'],percentiles):assert got is None if ref is None else np.isclose(got,ref)
                        obs=int(f.close_time.iloc[j])+1;times=f.close_time.to_numpy()+1
                        hist=np.abs(slopes[(times<obs)&(times>=obs-cfg.converging_history_days*DAY)&(slopes*slopes[j]>0)])
                        assert np.isclose(r['signed_slope'],slopes[j])
                        if len(hist)>=cfg.min_distribution_samples:
                            assert np.isclose(r['historical_median'],np.median(hist));assert np.isclose(r['stretch_ratio'],abs(slopes[j])/np.median(hist))
                        valid=lambda x,y:percentiles[x] is not None and percentiles[y] is not None and np.sign(slopes[j-2+x])==np.sign(slopes[j-2+y])
                        velocity=percentiles[2]-percentiles[1] if valid(2,1) else None
                        acceleration=velocity-(percentiles[1]-percentiles[0]) if velocity is not None and valid(1,0) else None
                        for key,ref in [('velocity',velocity),('acceleration',acceleration)]:assert r[key] is None if ref is None else np.isclose(r[key],ref)
                records.append(dict(at=at,tf=tf,scoring=actual,converging=a['converging'][tf],independent_check='PASS'))
            assert np.isclose(a['scoring']['overall']['combined_score'],combined)
            assert np.isclose(a['scoring']['overall']['combined_normalized'],combined/sum(cfg.tf_weights.values()))
            print('REAL_REFERENCE_PASS',at,a['price'],a['scoring']['overall']['combined_normalized'],flush=True)
    out=PROJECT/'data/website-v1';out.mkdir(exist_ok=True)
    (out/'manual-verification.json').write_text(json.dumps(dict(status='PASS',timestamps=3,timeframe_checks=12,swing_side_checks=72,records=records,source_sha256=hashes),indent=2,allow_nan=False),encoding='utf-8')


if __name__=='__main__':run()
