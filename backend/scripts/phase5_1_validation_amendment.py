"""Validation-only runner amendment; original frozen implementation stays untouched.

Some authoritative stored native bars have different close prices at the same T.
Same-P evaluation is unchanged. Equality to a source-price score is required only
when P equals that source price; otherwise both prices are independently checked
with the ORIGINAL scalar contribution rule and the discrepancy is retained.
No timestamp-specific exception, exclusion, price repair, or outcome input exists.
"""
import sys
import traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from app.current_confluence.contract import *
from app.current_confluence.states import NATIVE_COLUMNS,Memberships,evaluate,from_15m,classify,audit_examples
from app.confluence.geometry import latest_indices

AMEND=ROOT/'validation-amendment'
RULE=dict(version='shared-close-price-validation-v1',
    mathematical_definitions_changed=False,original_frozen_files_modified=False,
    rule='At shared close and identical P/source price require identical descriptors; otherwise retain warning, require independent scalar parity at BOTH prices, retain current 15m P and all original native memberships',
    forbidden=['source price replacement','row exclusion','quantile refit','outcome-conditioned change','timestamp-specific exception'],
    cause='stored native close prices need not agree across authoritative historical timeframe artifacts',
    outcome_access='No replication outcome or analysis file read by this runner')


def shared_close_validation(t,tf,P,old,v,args):
    if t%STEPS[tf]:return None
    old_state=classify(int(old.nearby_support_count),int(old.nearby_resistance_count),old.coverage_complete)
    if P==old.source_price:
        if v['state']!=old_state or v['A1']!=old.A1 or v['A2']!=old.A2:
            raise ValueError('Identical-price native parity failed')
        return None
    if args is None:raise ValueError('15m current/source price mismatch')
    native=evaluate(*args,float(old.source_price),WIDTHS[tf],available=old.coverage_complete,reference=True)
    current=evaluate(*args,P,WIDTHS[tf],available=old.coverage_complete,reference=True)
    if native['state']!=old_state or native['A1']!=old.A1 or native['A2']!=old.A2:
        raise ValueError('Original native source-price reference failed')
    for field in ['state','support_count','resistance_count','raw_difference','imbalance','A1','A2','nearest_support','nearest_resistance']:
        if current[field]!=v[field] and not (pd.isna(current[field]) and pd.isna(v[field])):
            raise ValueError('Same-current-P scalar reference failed '+field)
    return dict(T=int(t),timeframe=tf,current_15m_P=float(P),native_source_P=float(old.source_price),
        source_snapshot_id=old.snapshot_id,native_A1=float(old.A1),native_A2=float(old.A2),
        current_A1=v['A1'],current_A2=v['A2'],native_state=old_state,current_state=v['state'],
        native_and_current_scalar_parity=True,retained=True,price_replaced=False)


def construct(phase):
    sources=Sources(phase)
    natives={tf:sources.frame(PROJECT/'data/phase5'/phase/'native'/(tf+'.parquet'),columns=NATIVE_COLUMNS).sort_values('source_timestamp').reset_index(drop=True) for tf in TFS}
    low=natives['15m'];times=low.source_timestamp.to_numpy()
    lo,hi=(START,REP) if phase=='development' else (REP,END)
    if not ((times>=lo)&(times<hi)).all() or not np.all(np.diff(times)==STEPS['15m']):raise ValueError('Wrong decision clock')
    indices={}
    for tf,n in natives.items():
        ix,ok=latest_indices(n.source_timestamp,times,STEPS[tf])
        if not ok.all():raise ValueError('Unavailable alignment')
        indices[tf]=ix
    engines={tf:Memberships(sources,tf,natives[tf]) for tf in TFS if tf!='15m'}
    rows=[];warnings=[];changed={tf:0 for tf in TFS};closes={tf:0 for tf in TFS}
    for i,t in enumerate(times):
        lr=low.iloc[i];P=float(lr.source_price)
        row=dict(decision_timestamp=int(t),decision_price=P,event_id=lr.event_id)
        pattern='';old_pattern=''
        for tf in TFS:
            old=natives[tf].iloc[indices[tf][i]]
            old_state=classify(int(old.nearby_support_count),int(old.nearby_resistance_count),old.coverage_complete)
            if tf=='15m':v=from_15m(lr);stamp=int(t);sid=lr.snapshot_id;args=None
            else:
                stamp,sid,args=engines[tf].at(int(t))
                if sid!=old.snapshot_id:raise ValueError('Membership alignment mismatch')
                v=evaluate(*args,P,WIDTHS[tf],available=old.coverage_complete)
            if v['evaluation_price']!=P:raise ValueError('Noncurrent evaluation price')
            warning=shared_close_validation(int(t),tf,P,old,v,args)
            if warning is not None:warnings.append(warning)
            if t%STEPS[tf]==0 and warning is None:closes[tf]+=1
            changed[tf]+=v['state']!=old_state
            v.update(source_timestamp=int(stamp),source_age_ms=int(t-stamp),snapshot_id=sid,
                native_source_price=float(old.source_price),old_carried_state=old_state,
                old_carried_imbalance=old.imbalance,old_carried_A1=old.A1,old_carried_A2=old.A2)
            for k,value in v.items():row[tf+'__'+k]=value
            pattern+=v['state'];old_pattern+=old_state
        row['pattern']=pattern;row['phase5_carried_pattern']=old_pattern
        for field in ['flow_status','observation_start','observation_end','joint_quantity','joint_delta','support_delta','resistance_delta','support_normalized_delta','resistance_normalized_delta']:
            row[field]=lr[field]
        if row['observation_end']!=t:raise ValueError('Future flow')
        vector=np.abs(np.array([row[tf+'__imbalance'] for tf in TFS],dtype=float))
        for label,fn in [('minimum',np.min),('median',np.median),('maximum',np.max)]:
            row['strength_'+label]=float(fn(vector)) if np.isfinite(vector).all() else np.nan
        rows.append(row)
        if (i+1)%5000==0:print('VALIDATION_REPLAY',phase,i+1,len(times),flush=True)
    return pd.DataFrame(rows),natives,sources,engines,warnings,changed,closes


def main():
    check_freeze();AMEND.mkdir(exist_ok=True)
    if (ROOT/'replication/analysis').exists():raise ValueError('Amendment must precede replication outcomes')
    definition=dict(rule=RULE,original_freeze_id=read(ROOT/'development-freeze.json')['freeze_id'],
        original_freeze_sha256=digest(ROOT/'development-freeze.json'),runner_sha256=digest(__file__),plan_sha256=digest(ROOT/'plan.json'))
    if (AMEND/'definition.json').exists() and read(AMEND/'definition.json')!=definition:raise ValueError('Amendment changed')
    write(AMEND/'definition.json',definition)
    write(ROOT/'pipeline-status.json',dict(status='RUNNING',stage='validation-amendment-development-equivalence'))
    if not (AMEND/'development-equivalence.json').exists():
        f,n,s,e,w,c,cl=construct('development')
        frozen=pd.read_parquet(ROOT/'development/states.parquet')
        pd.testing.assert_frame_equal(f,frozen,check_exact=True)
        if w:raise ValueError('Unexpected development price divergence; review required')
        write(AMEND/'development-equivalence.json',dict(status='PASS',rows=len(f),columns=len(f.columns),
            comparison='exact every-column every-row equality including dtypes to frozen 2022 states',
            frozen_states_sha256=digest(ROOT/'development/states.parquet'),source_hashes=s.hashes,
            current_price_definition_unchanged=True,runner_sha256=digest(__file__)))
        print('FULL_DEVELOPMENT_EQUIVALENCE_PASS',len(f),flush=True)
    verify=read(AMEND/'development-equivalence.json')
    if verify['runner_sha256']!=digest(__file__) or verify['frozen_states_sha256']!=digest(ROOT/'development/states.parquet'):
        raise ValueError('Equivalence seal mismatch')
    write(AMEND/'frozen.json',dict(status='FROZEN_BEFORE_REPLICATION_OUTCOMES',definition_sha256=digest(AMEND/'definition.json'),
        development_equivalence_sha256=digest(AMEND/'development-equivalence.json'),original_freeze_sha256=digest(ROOT/'development-freeze.json')))
    check_freeze()
    write(ROOT/'pipeline-status.json',dict(status='RUNNING',stage='validation-amendment-replication-states'))
    f,natives,sources,engines,warnings,changed,closes=construct('replication')
    dest=ROOT/'replication';dest.mkdir(exist_ok=True)
    f.to_parquet(dest/'states.parquet',index=False,compression='zstd')
    a,details=audit_examples(f,natives,sources)
    a.to_csv(dest/'classification-examples.csv',index=False);a.to_parquet(dest/'classification-examples.parquet',index=False)
    details.update(status='PASS',same_P_all_timeframes=True,reference_checks=len(a),
        changed_from_phase5_by_timeframe=changed,changed_pattern_timestamps=int(f.pattern.ne(f.phase5_carried_pattern).sum()),
        shared_native_close_parity=closes,native_source_price_parity={tf:e.parity for tf,e in engines.items()},
        phase5_15m_reused_rows=len(f),source_maps_rebuilt=False,no_spatial=True,native_close_price_warnings=warnings,
        validation_amendment_sha256=digest(AMEND/'frozen.json'),original_definition_freeze_id=definition['original_freeze_id'])
    write(dest/'classification-audit.json',details);sources.save()
    write(dest/'states-complete.json',dict(status='COMPLETE',timestamps=len(f),first=int(f.decision_timestamp.min()),last=int(f.decision_timestamp.max()),
        validation_amendment_sha256=digest(AMEND/'frozen.json'),
        hashes={p.name:digest(p) for p in [dest/'states.parquet',dest/'classification-examples.csv',dest/'classification-examples.parquet',dest/'classification-audit.json']}))
    write(ROOT/'pipeline-status.json',dict(status='REPLICATION_CLASSIFICATION_AUDITED',stage='READY_FOR_FROZEN_ANALYSIS',price_warnings=len(warnings)))
    print('AMENDED_VALIDATION_COMPLETE',len(warnings),flush=True)


if __name__=='__main__':
    try:main()
    except Exception:
        write(ROOT/'pipeline-status.json',dict(status='FAILED',stage='validation-amendment',error=traceback.format_exc()))
        raise
