"""Frozen descriptive full-map analysis; no fitted trading rule or row p-values."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from app.market.aggregate_trades import write_json,sha256
from app.research.models import identity
from app.research.phase3_context import contexts
from app.fullmap.run import CONFIGS
from .history import ROOT,load_prices

GRID=['direction','tp','sl','horizon']
PLAN=dict(version='phase3r1-descriptive-v1',groups=4,quantiles=[.25,.5,.75],
    half_band_substantial='development 75th percentile of absolute A1-A2, strictly nonzero',
    age_buckets_days=[30,180,365],time_blocks='calendar quarters UTC',
    uncertainty='1000 resamples of fixed nonoverlapping 7-day UTC blocks, deterministic seed 3101',
    intervals='descriptive 95% percentile intervals for conditioned TP_FIRST minus same-period baseline; minimum 5 represented blocks',
    expectancy='boundary_return_conditional_on_unambiguous_resolved_complete_horizon_no_costs',
    baseline='all eligible unconditioned timestamps in same phase/quarter and outcome grid',
    no_threshold_selection=True,replication_label='previously inspected replication period')


def state_features(directory,config):
    paths=sorted((directory/identity(config)[:12]).glob('*-states.parquet'))
    if not paths:raise ValueError('Missing state partitions')
    rows=[]
    for path in paths:
        for s in pd.read_parquet(path).to_dict('records'):
            raw=json.loads(s['raw']);su=raw['support'];re=raw['resistance'];age=raw['nearby_age_hours'] or {}
            near_s=su['density']['inner']+su['density']['outer'];near_r=re['density']['inner']+re['density']['outer']
            record=dict(event_id=s['event_id'],timestamp=s['decision_timestamp'],candidate_count=s['known_candidate_count'],
                support_count=su['total'],resistance_count=re['total'],nearby_support=near_s,nearby_resistance=near_r,
                imbalance=near_s-near_r,count_ratio=near_s/near_r if near_r else np.nan,
                nearest_support=su['nearest_absolute_distance_fraction'],nearest_resistance=re['nearest_absolute_distance_fraction'],
                distance_difference=(su['nearest_absolute_distance_fraction']-re['nearest_absolute_distance_fraction']) if su['nearest_price'] is not None and re['nearest_price'] is not None else np.nan,
                above_below_asymmetry=su['above']+re['above']-su['below']-re['below'],
                clusters=raw['cluster_count'],overlap_pairs=raw['overlap_pair_count'],duplicate_prices=raw['duplicate_reference_price_count'],
                candidates_per_cluster=s['known_candidate_count']/raw['cluster_count'] if raw['cluster_count'] else np.nan,
                mean_age=age.get('mean'),median_age=age.get('median'))
            for kind,r in [('support',su),('resistance',re)]:
                record.update({kind+'_'+key:r[key] for key in ['above','below','near']})
                record[kind+'_full']=r['density']['inner'];record[kind+'_half']=r['density']['outer']
            if s['native_score']:
                native=json.loads(s['native_score']);record.update(A1=native['long_score'],A2=native['full_weight_only_long'])
                extra=json.loads(s['extra']);record.update({k:extra[k] for k in ['mean_prior_crossings','mean_prior_visits','mean_hours_since_last_contact','full_mean_source_age_hours','half_mean_source_age_hours']})
                for label in ['recent_0_30d','medium_30_180d','old_180_365d','very_old_over_365d']:
                    record[label+'_fraction']=extra[label]['count']/(near_s+near_r) if near_s+near_r else np.nan
                    record[label+'_crossings']=extra[label]['mean_crossings']
                    record[label+'_visits']=extra[label]['mean_visits']
                record['half_band_difference']=record['A1']-record['A2']
                record['half_band_absolute_difference']=abs(record['half_band_difference'])
                record['sign_case']='same_sign' if np.sign(record['A1'])==np.sign(record['A2']) else 'sign_flip' if record['A1']*record['A2']<0 else 'one_zero'
            rows.append(record)
    frame=pd.DataFrame(rows).sort_values('timestamp').reset_index(drop=True)
    dates=pd.to_datetime(frame.timestamp,unit='ms',utc=True)
    frame['quarter']=dates.dt.year.astype(str)+'Q'+dates.dt.quarter.astype(str)
    frame['week']=frame.timestamp//(7*86400000)
    return frame


def metric_table(frame,keys):
    f=frame.copy();complete=~f.censored
    for label in ['TP_FIRST','SL_FIRST','NEITHER','AMBIGUOUS']:f[label]=(f.label.eq(label)&complete).astype(int)
    f['complete']=complete.astype(int);f['resolved']=(complete&f.label.isin(['TP_FIRST','SL_FIRST'])).astype(int)
    f['gross_sum']=np.where(f['TP_FIRST'].eq(1),f.tp,np.where(f['SL_FIRST'].eq(1),-f.sl,0.))*100
    for col in ['mfe_pct','mae_pct','time_to_mfe_ms','time_to_mae_ms']:f.loc[~complete,col]=np.nan
    agg=dict(state_count=('event_id','size'),complete=('complete','sum'),censored=('censored','sum'),
        TP_FIRST=('TP_FIRST','sum'),SL_FIRST=('SL_FIRST','sum'),NEITHER=('NEITHER','sum'),AMBIGUOUS=('AMBIGUOUS','sum'),
        resolved=('resolved','sum'),gross_sum=('gross_sum','sum'),mfe_pct=('mfe_pct','mean'),mae_pct=('mae_pct','mean'),
        time_to_mfe_ms=('time_to_mfe_ms','mean'),time_to_mae_ms=('time_to_mae_ms','mean'))
    result=f.groupby(keys,dropna=False,sort=True).agg(**agg).reset_index()
    result['tp_first_rate']=result.TP_FIRST/result.complete.replace(0,np.nan)
    result['gross_resolved_expectancy_pct']=result.gross_sum/result.resolved.replace(0,np.nan)
    return result


def block_intervals(joined,bucket_column):
    results=[];rng=np.random.default_rng(3101)
    for key,f in joined.groupby(GRID,sort=True):
        f=f[~f.censored];weeks=sorted(f.week.unique())
        if not weeks:continue
        baseline=f.groupby('week').agg(n=('event_id','size'),tp=('label',lambda x:x.eq('TP_FIRST').sum())).reindex(weeks,fill_value=0)
        weights=rng.multinomial(len(weeks),np.full(len(weeks),1/len(weeks)),size=1000)
        base=(weights@baseline.tp.to_numpy())/(weights@baseline.n.to_numpy())
        for bucket,g in f.groupby(bucket_column,dropna=False,sort=True):
            counts=g.groupby('week').agg(n=('event_id','size'),tp=('label',lambda x:x.eq('TP_FIRST').sum())).reindex(weeks,fill_value=0)
            denominator=weights@counts.n.to_numpy();num=weights@counts.tp.to_numpy()
            delta=np.divide(num,denominator,out=np.full(1000,np.nan),where=denominator>0)-base
            represented=int((counts.n>0).sum());finite=delta[np.isfinite(delta)]
            low,high=np.quantile(finite,[.025,.975]) if represented>=5 and len(finite)>=950 else (np.nan,np.nan)
            results.append(dict(zip(GRID,key))|dict(bucket=bucket,represented_week_blocks=represented,
                delta_vs_baseline=float(g.label.eq('TP_FIRST').mean()-f.label.eq('TP_FIRST').mean()),ci_low=low,ci_high=high))
    return pd.DataFrame(results)


def analyze(phase,stage):
    directory=ROOT/phase;dest=directory/'analysis';dest.mkdir(exist_ok=True)
    if not (directory/(stage+'-complete.json')).exists():raise ValueError('Generation stage incomplete')
    write_json(ROOT/'analysis-plan.json',PLAN)
    cs=load_prices(phase=='replication');context=pd.DataFrame(contexts(cs))[['timestamp','volatility','recent_return']]
    outcomes=pd.concat([pd.read_parquet(p) for p in sorted(directory.glob('*-outcomes.parquet'))],ignore_index=True)
    configs=CONFIGS[:1] if stage=='A' else CONFIGS[1:5]
    for config in configs:
        name=identity(config)[:12];states=state_features(directory,config).merge(context,on='timestamp',validate='one_to_one')
        feature_names=[k for k in states if k not in ['event_id','timestamp','quarter','week','sign_case']]
        model_path=ROOT/'development/analysis'/f'{name}-model.json'
        if phase=='development':
            model=dict(config=config,plan_id=identity(PLAN),cuts={field:sorted(set(map(float,np.nanquantile(states[field].dropna(),[.25,.5,.75]))))
                if states[field].notna().any() else [] for field in feature_names},
                substantial=float(states.half_band_absolute_difference.quantile(.75)) if 'A1' in states else None)
            write_json(model_path,model)
        else:
            model=json.loads(model_path.read_text())
            if model['plan_id']!=identity(PLAN):raise ValueError('Analysis plan differs from development freeze')
        for field in feature_names:
            states[field+'_bucket']=np.where(states[field].notna(),np.searchsorted(model['cuts'][field],states[field],side='right'),-1)
        if 'A1' in states:
            states['magnitude_case']=np.where((states.half_band_absolute_difference>=model['substantial'])&(states.half_band_absolute_difference>0),'substantial','other')
        states.to_parquet(dest/f'{name}-state-features.parquet',index=False)
        joined=outcomes.merge(states,on='event_id',validate='many_to_one')
        baseline=metric_table(joined,GRID);baseline.to_csv(dest/f'{name}-baseline.csv',index=False)
        metric_table(joined,['quarter']+GRID).to_csv(dest/f'{name}-quarter-baseline.csv',index=False)
        # All feature/grid curves and chronological contrasts use the same market events.
        all_tables=[];quarter_tables=[];uncertainty=[]
        for field in feature_names:
            bucket=field+'_bucket'
            tab=metric_table(joined,[bucket]+GRID).rename(columns={bucket:'bucket'});tab.insert(0,'feature',field)
            tab=tab.merge(baseline[GRID+['tp_first_rate']],on=GRID,suffixes=('','_baseline'))
            tab['delta_vs_baseline']=tab.tp_first_rate-tab.tp_first_rate_baseline;all_tables.append(tab)
            qt=metric_table(joined,['quarter',bucket]+GRID).rename(columns={bucket:'bucket'});qt.insert(0,'feature',field);quarter_tables.append(qt)
            # Predeclared core geometry/ablation uncertainty; other curves remain descriptive.
            if field in ['A1','A2','imbalance','distance_difference','clusters','candidates_per_cluster','mean_age','mean_prior_crossings']:
                ci=block_intervals(joined,bucket);ci.insert(0,'feature',field);uncertainty.append(ci)
        pd.concat(all_tables,ignore_index=True).to_parquet(dest/f'{name}-feature-curves.parquet',index=False)
        pd.concat(quarter_tables,ignore_index=True).to_parquet(dest/f'{name}-quarter-curves.parquet',index=False)
        metric_table(joined,['candidate_count_bucket','clusters_bucket']+GRID).to_csv(dest/f'{name}-clusters-within-count.csv',index=False)
        if uncertainty:pd.concat(uncertainty,ignore_index=True).to_csv(dest/f'{name}-block-intervals.csv',index=False)
        for regime in ['volatility_bucket','recent_return_bucket']:
            metric_table(joined,[regime,'imbalance_bucket']+GRID).to_csv(dest/f'{name}-{regime}-geometry.csv',index=False)
        if 'A1' in states:
            for variant in ['A1','A2']:
                metric_table(joined,[variant]+GRID).to_parquet(dest/f'{variant}-exact-outcomes.parquet',index=False)
                metric_table(joined,['quarter',variant]+GRID).to_parquet(dest/f'{variant}-quarter-exact.parquet',index=False)
                metric_table(joined,['volatility_bucket',variant]+GRID).to_parquet(dest/f'{variant}-volatility-exact.parquet',index=False)
                metric_table(joined,['recent_return_bucket',variant]+GRID).to_parquet(dest/f'{variant}-trend-exact.parquet',index=False)
                dist=states.groupby(variant).agg(state_count=('event_id','size'),candidate_count=('candidate_count','mean'),
                    nearby_support=('nearby_support','mean'),nearby_resistance=('nearby_resistance','mean'),
                    support_count=('support_count','mean'),resistance_count=('resistance_count','mean')).reset_index()
                dist['frequency']=dist.state_count/len(states);dist.to_csv(dest/f'{variant}-exact-distribution.csv',index=False)
            metric_table(joined,['sign_case','magnitude_case']+GRID).to_csv(dest/'half-band-paired-cases.csv',index=False)
            metric_table(joined,['quarter','sign_case','magnitude_case']+GRID).to_csv(dest/'half-band-quarter-cases.csv',index=False)
            metric_table(joined,['A2_bucket','half_band_difference_bucket']+GRID).to_csv(dest/'half-band-within-A2.csv',index=False)
            metric_table(joined,['quarter','A2_bucket','half_band_difference_bucket']+GRID).to_csv(dest/'half-band-within-A2-quarter.csv',index=False)
            metric_table(joined,['very_old_over_365d_fraction_bucket','mean_prior_crossings_bucket']+GRID).to_csv(dest/'old-levels-crossings.csv',index=False)
            intervals=[]
            for field in ['sign_case','magnitude_case']:
                ci=block_intervals(joined,field);ci.insert(0,'case_definition',field);intervals.append(ci)
            pd.concat(intervals).to_csv(dest/'half-band-block-intervals.csv',index=False)
        print('ANALYSIS',phase,config,len(states),flush=True)
    write_json(dest/(stage+'-complete.json'),dict(status='COMPLETE',phase=phase,stage=stage,plan_id=identity(PLAN),
        replication_label=PLAN['replication_label'] if phase=='replication' else None,no_selection=True))


def freeze():
    dest=ROOT/'development/analysis'
    for stage in ['A','BC']:
        if not (dest/(stage+'-complete.json')).exists():raise ValueError('Finalize development A and BC first')
    files={str(p.relative_to(ROOT)):sha256(p) for p in sorted(dest.iterdir()) if p.is_file()}
    code={p.name:sha256(p) for p in sorted(Path(__file__).parent.glob('*.py')) if p.name not in ['reports.py','audit.py']}
    result=dict(status='FROZEN',plan=PLAN,files=files,code=code,no_2023_refit=True,no_rule_selected=True)
    write_json(ROOT/'development-freeze.json',{**result,'freeze_id':identity(result)})
    print('DEVELOPMENT_FROZEN',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['development','replication','freeze']);parser.add_argument('stage',nargs='?',choices=['A','BC'])
    args=parser.parse_args()
    freeze() if args.phase=='freeze' else analyze(args.phase,args.stage)
