"""Outcome-blind corroboration of empty observed quarter-hour trade intervals."""
import argparse
import pandas as pd
from .contract import ROOT,read,sha256,write_json


def audit(phase):
    year=2022 if phase=='development' else 2023 if phase=='replication' else None
    if year is None:raise ValueError('Unknown phase')
    evidence=[];sources={};problem=[]
    for month in range(1,13):
        name=f'{year}-{month:02d}'
        path=ROOT/'trade-profiles-15m'/name/'manifest.json';manifest=read(path);sources[str(path)]=sha256(path)
        times=manifest['missing_intervals']
        if not times:continue
        candles_path=ROOT/'candles/15m'/(name+'.parquet')
        coverage=read(ROOT/'candles/15m'/(phase+'-coverage.json'))
        if sha256(candles_path)!=coverage['normalized'][candles_path.name]:raise ValueError('Official candle evidence changed')
        candles=pd.read_parquet(candles_path).set_index('open_time')
        for t in times:
            r=candles.loc[t]
            empty=bool(r.volume==0 and r.trade_count==0 and r.taker_buy_volume==0)
            evidence.append(dict(start=t,end=t+900000,official_kline_quantity=float(r.volume),
                official_kline_trade_count=int(r.trade_count),official_open=float(r.open),official_close=float(r.close),
                classification='OFFICIAL_ZERO_ACTIVITY_CORROBORATED' if empty else 'MATERIAL_COVERAGE_REVIEW_REQUIRED',
                treatment='No quantity imputation; overlapping flow windows unavailable; price states retained'))
            if not empty:problem.append(t)
    result=dict(status='PASS_WITH_EMPTY_OBSERVATION_WARNINGS' if evidence and not problem else 'PASS' if not problem else 'BLOCKED',
                phase=phase,rule='Absent observed trade interval is corroborated only if official native kline quantity AND count AND taker quantity are zero; otherwise block before replication outcomes.',
                source_manifests=sources,evidence=evidence,no_new_quarantines=True,no_imputation=True)
    write_json(ROOT/('profile-coverage-'+phase+'.json'),result)
    if problem:raise ValueError('Observable trade coverage requires forensic review before proceeding')
    print('EMPTY_OBSERVATION_AUDIT',phase,result['status'],len(evidence),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['development','replication']);audit(p.parse_args().phase)
