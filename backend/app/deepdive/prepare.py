"""Read-only reuse of Phase 3; all new artifacts live under phase35."""
import json
import shutil
import numpy as np
import pandas as pd
from app.market.aggregate_trades import write_json, sha256
from app.research.phase3_engine import configurations, generate
from app.research.phase3_plan import manifest, DEVELOPMENT_START, DEVELOPMENT_END, VALIDATION_END
from app.research.phase3_storage import connect, literal
from app.research.runner import code_digest
from .design import ROOT, SOURCE, design, guard, code_hash
from .percentiles import historical, frozen_percentiles, normalized_delta, block_labels


def a_configs():
    return [c for c in configurations(manifest()) if c['detector']=='A']


def initialize(root=ROOT, source=SOURCE):
    root.mkdir(parents=True,exist_ok=True)
    path=root/'design.json'
    if path.exists() and json.loads(path.read_text())!=design():raise ValueError('Design changed')
    write_json(path,design())
    frozen=json.loads((source/'frozen-validation.json').read_text())
    if code_digest()!=frozen['research_code_digest']:raise ValueError('Original Phase 3 code changed')
    write_json(root/'source-lineage.json',dict(phase3_freeze_id=frozen['freeze_id'],
        coverage_id=frozen['coverage_id'],phase3_code_digest=code_digest(),
        artifact_hashes={f'{phase}/{name}':sha256(source/phase/name)
            for phase in ['development','validation']
            for name in ['configuration-manifest.json','evaluation-complete.json']}))


def fit_context(root=ROOT,source=SOURCE):
    events=pd.read_parquet(source/'development/events.parquet')
    end=design()['context_fit_end'];early=events[(events.timestamp<end)&events.volatility.notna()]
    model=dict(fit_end=end,volatility_cuts=np.quantile(early.volatility,[.25,.75]).tolist(),
               neutral_return=float(np.quantile(np.abs(early.recent_return),.25)))
    frozen=json.loads((source/'frozen-validation.json').read_text())
    model['legacy_delta_cuts']=next(m['cuts'] for m in frozen['bucket_models'] if m['field']=='volume_delta')
    write_json(root/'context-model.json',model)
    return model


def context_columns(frame,model):
    result=frame.copy();v=result.volatility.to_numpy();r=result.recent_return.to_numpy()
    eligible=(result.observed_at.to_numpy()>=model['fit_end'])&np.isfinite(v)&np.isfinite(r)
    result['volatility_regime']=np.where(eligible,np.asarray(['LOW','MIDDLE','HIGH'])[np.searchsorted(model['volatility_cuts'],v,side='right')],'CALIBRATION')
    z=model['neutral_return']
    result['return_regime']=np.where(eligible,np.where(r < -z,'NEGATIVE',np.where(r>z,'POSITIVE','NEUTRAL')),'CALIBRATION')
    result['quarter']=block_labels(result.observed_at)
    return result


def prepare(phase,root=ROOT,source=SOURCE):
    if phase not in ['development','replication']:raise ValueError('Unknown phase')
    start,end=(DEVELOPMENT_START,DEVELOPMENT_END) if phase=='development' else (DEVELOPMENT_END,VALIDATION_END)
    guard(start,end);dest=root/phase;dest.mkdir(parents=True,exist_ok=True)
    if (dest/'prepared.json').exists():
        saved=json.loads((dest/'prepared.json').read_text())
        for name,digest in saved['hashes'].items():
            if sha256(dest/name)!=digest:raise ValueError('Prepared artifact modified')
        return dest
    if phase=='development':
        src=source/'development';model=fit_context(root,source)
    else:
        seal=json.loads((root/'development-seal.json').read_text())
        if seal['code_hash']!=code_hash() or seal['design_id']!=design()['design_id']:raise ValueError('Descriptive design/code changed before replication')
        for name,digest in seal['model_hashes'].items():
            if sha256(root/name)!=digest:raise ValueError('Development fitting changed')
        if not (root/'development/summary.parquet').exists():raise ValueError('Complete development first')
        src=root/'replication-source'
        if not (src/'configuration-manifest.json').exists():
            generate(source,'validation',a_configs(),manifest(),output_name=str(src.resolve()))
        model=json.loads((root/'context-model.json').read_text())
    for name in ['events.parquet','future_outcomes.parquet']:
        shutil.copyfile(src/name,dest/name)
    con=connect(dest)
    con.execute('SET enable_progress_bar=false')
    partition=dest/'raw'
    con.execute(f"COPY (SELECT i.*, f.* EXCLUDE(interaction_id,event_id,timestamp), e.volatility,e.recent_return FROM read_parquet({literal(src/'interactions.parquet')}) i JOIN read_parquet({literal(src/'decision_features.parquet')}) f USING(interaction_id) JOIN read_parquet({literal(src/'events.parquet')}) e ON e.event_id=i.event_id WHERE i.detector='A') TO {literal(partition)} (FORMAT PARQUET,PARTITION_BY(configuration_id),OVERWRITE_OR_IGNORE true,COMPRESSION ZSTD)")
    con.close();(dest/'features').mkdir(exist_ok=True);(root/'models').mkdir(exist_ok=True)
    inventory=[]
    for cfg in a_configs():
        cid=cfg['configuration_id'];frame=pd.read_parquet(partition/f'configuration_id={cid}')
        frame=frame.sort_values(['observed_at','interaction_id'],kind='stable').reset_index(drop=True)
        if not ((frame.observed_at>=start)&(frame.observed_at<end)).all():raise ValueError('Out-of-period data')
        valid=(frame.status=='AVAILABLE')&np.isfinite(frame.volume_delta)
        frame['normalized_delta']=normalized_delta(frame.aggressive_buy_quantity,frame.aggressive_sell_quantity,frame.quantity)
        frame['historical_delta_percentile']=np.nan;frame['historical_row_percentile']=np.nan
        frame['percentile_history_rows']=0
        model_path=root/'models'/f'{cid}.parquet'
        if phase=='development':
            primary,row,n,ecdf=historical(frame.loc[valid,'volume_delta'].to_numpy(),frame.loc[valid,'observed_at'].to_numpy())
            ecdf.to_parquet(model_path,index=False)
        else:
            ecdf=pd.read_parquet(model_path);primary,row=frozen_percentiles(frame.loc[valid,'volume_delta'],ecdf)
            n=np.full(valid.sum(),int(ecdf.row_weight.sum()),dtype=np.int64)
        frame.loc[valid,'historical_delta_percentile']=primary
        frame.loc[valid,'historical_row_percentile']=row
        frame.loc[valid,'percentile_history_rows']=n
        frame['legacy_delta_quartile']=np.where(valid,np.searchsorted(model['legacy_delta_cuts'],frame.volume_delta,side='right')+1,0)
        frame=context_columns(frame,model)
        frame['configuration_id']=cid
        frame.to_parquet(dest/'features'/f'{cid}.parquet',index=False,compression='zstd')
        inventory.append(dict(configuration_id=cid,width_model=cfg['width_model'],width_parameter=cfg['width_parameter'],
            rows=len(frame),unique_events=frame.event_id.nunique(),available_volume=int(valid.sum()),
            zero_volume=int((valid&(frame.quantity==0)).sum()),undefined_normalized=int(frame.normalized_delta.isna().sum())))
        print('PREPARED',phase,cfg['width_parameter'],len(frame),flush=True)
    pd.DataFrame(inventory).to_csv(dest/'feature-inventory.csv',index=False)
    write_json(dest/'prepared.json',dict(phase=phase,design_id=design()['design_id'],configurations=a_configs(),
        hashes={str(p.relative_to(dest)):sha256(p) for p in sorted((dest/'features').glob('*.parquet'))},
        outcomes_file='future_outcomes.parquet',features_separate_from_outcomes=True))
    return dest
