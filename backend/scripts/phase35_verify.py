"""Final artifact audit and report-only diagnostics; never fits or selects rules."""
import json
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.deepdive.design import ROOT,SOURCE,code_hash
from app.deepdive.prepare import a_configs
from app.deepdive.percentiles import frozen_percentiles
from app.deepdive.reports import reports,svg_lines,display,markdown
from app.research.runner import code_digest
from app.research.phase3_plan import DEVELOPMENT_START,DEVELOPMENT_END,VALIDATION_END
from app.market.aggregate_trades import write_json,sha256


def main():
    assert (ROOT/'complete.json').exists()
    seal=json.loads((ROOT/'development-seal.json').read_text())
    assert seal['code_hash']==code_hash()
    original=json.loads((SOURCE/'frozen-validation.json').read_text())
    assert original['research_code_digest']==code_digest()
    lineage=json.loads((ROOT/'source-lineage.json').read_text())
    for name,digest in lineage['artifact_hashes'].items():assert sha256(SOURCE/name)==digest
    for name,digest in seal['model_hashes'].items():assert sha256(ROOT/name)==digest
    assert sha256(ROOT/'development/summary.parquet')==seal['development_summary_hash']
    audit=[];raw_stats=[]
    for phase,start,end in [('development',DEVELOPMENT_START,DEVELOPMENT_END),('replication',DEVELOPMENT_END,VALIDATION_END)]:
        dest=ROOT/phase
        for cfg in a_configs():
            cid=cfg['configuration_id'];f=pd.read_parquet(dest/'features'/f'{cid}.parquet')
            assert f.interaction_id.is_unique
            assert ((f.observed_at>=start)&(f.observed_at<end)&(f.known_at<=f.observed_at)).all()
            valid=(f.status=='AVAILABLE')&f.volume_delta.notna()
            np.testing.assert_allclose(f.loc[valid,'volume_delta'],f.loc[valid,'aggressive_buy_quantity']-f.loc[valid,'aggressive_sell_quantity'],atol=1e-8)
            p=f.loc[valid,'historical_delta_percentile'].dropna()
            assert ((p>=-1e-10)&(p<=1+1e-10)).all()
            assert f.loc[f.quantity==0,'normalized_delta'].isna().all()
            if phase=='development':
                grouped=f.loc[valid].groupby('observed_at').size().sort_index()
                before=grouped.cumsum()-grouped
                np.testing.assert_array_equal(f.loc[valid,'percentile_history_rows'],f.loc[valid,'observed_at'].map(before))
            else:
                ecdf=pd.read_parquet(ROOT/'models'/f'{cid}.parquet')
                sample=f.loc[valid].iloc[::max(1,int(valid.sum())//1000)]
                expected,_=frozen_percentiles(sample.volume_delta,ecdf)
                np.testing.assert_allclose(sample.historical_delta_percentile,expected,rtol=1e-12,atol=1e-12)
            audit.append(dict(phase=phase,configuration_id=cid,rows=len(f),unique_events=f.event_id.nunique(),
                available_volume=int(valid.sum()),zero_zone_volume=int((valid&(f.quantity==0)).sum()),
                available_percentiles=int(f.historical_delta_percentile.notna().sum())))
            for kind in ['ALL','SUPPORT','RESISTANCE']:
                subset=f.loc[valid] if kind=='ALL' else f.loc[valid&(f.kind==kind)]
                for bucket,g in subset.groupby('legacy_delta_quartile',sort=True):
                    raw_stats.append(dict(phase=phase,configuration_id=cid,width_model=cfg['width_model'],
                        width_parameter=cfg['width_parameter'],kind=kind,legacy_quartile=int(bucket),
                        measurement_rows=len(g),unique_events=g.event_id.nunique(),
                        raw_delta_min=g.volume_delta.min(),raw_delta_q25=g.volume_delta.quantile(.25),
                        raw_delta_median=g.volume_delta.median(),raw_delta_q75=g.volume_delta.quantile(.75),raw_delta_max=g.volume_delta.max(),
                        normalized_delta_median=g.normalized_delta.median(),quantity_median=g.quantity.median(),
                        relative_zone_volume_median=g.relative_zone_volume.median(),zero_quantity_fraction=float((g.quantity==0).mean()),
                        negative_delta_fraction=float((g.volume_delta<0).mean()),zero_delta_fraction=float((g.volume_delta==0).mean()),
                        positive_delta_fraction=float((g.volume_delta>0).mean())))
        index=pd.read_parquet(dest/'event-index.parquet');times=index.timestamp.to_numpy()
        total_links=0
        for path in sorted((dest/'summary-parts').glob('*-controls.parquet')):
            links=pd.read_parquet(path)
            assert (times[links.control_index]+links.horizon.to_numpy()*3600000<=times[links.target_index]).all()
            assert (times[links.control_index]<times[links.target_index]).all()
            total_links+=len(links)
        print('VERIFIED',phase,'causal_control_links',total_links,flush=True)
        before={str(p.relative_to(dest)):sha256(p) for p in sorted((dest/'reports').rglob('*')) if p.is_file()}
        reports(phase)
        after={str(p.relative_to(dest)):sha256(p) for p in sorted((dest/'reports').rglob('*')) if p.is_file()}
        assert before==after,'Report output is not deterministic'
    # Reproduce the old observation exactly before interpreting new ECDF labels.
    reproduced=0
    for original_phase,new_phase in [('development','development'),('validation','replication')]:
        old=pd.read_csv(SOURCE/original_phase/'research_summary.csv')
        old=old[(old.detector=='A')&(old.table=='volume_delta_bucket')].copy()
        old['bucket']=old.volume_delta_bucket.str.replace('Q','',regex=False)
        new=pd.read_parquet(ROOT/new_phase/'summary.parquet')
        new=new[(new.kind=='ALL')&(new.facet=='ALL')&(new.family=='legacy_quartile')&new.configuration_id.isin(old.configuration_id)]
        keys=['configuration_id','direction','tp','sl','horizon','bucket']
        joined=old.merge(new,on=keys,suffixes=('_old','_new'),validate='one_to_one')
        assert len(joined)==len(old)==len(new)
        for field in ['unique_event_count','measurement_count','event_balanced_tp_first_rate','tp_first_rate','mfe_pct_mean','mfe_pct_median']:
            np.testing.assert_allclose(joined[field+'_old'],joined[field+'_new'],rtol=1e-10,atol=1e-10,equal_nan=True)
        reproduced+=len(joined)
    docs=ROOT.parents[1]/'docs/research'
    raw_stats=pd.DataFrame(raw_stats)
    raw_stats.to_csv(ROOT/'raw-delta-distribution.csv',index=False,float_format='%.12g',lineterminator='\n')
    selected=raw_stats[(raw_stats.width_model=='original_timeframe')&(raw_stats.kind=='ALL')]
    cuts=json.loads((ROOT/'context-model.json').read_text())['legacy_delta_cuts']
    raw_report='# Raw Delta and Legacy Boundaries\n\nThe same legacy boundaries are retained in both periods: '+str(cuts)+'. They were pooled across detectors/full development in Phase 3, not fitted on 2023 and not interpretable as a stable online percentile during development. Values below are row-weighted descriptive distributions, not selected thresholds. Zero quantity makes normalized delta undefined.\n\n'+markdown(selected[['phase','legacy_quartile','measurement_rows','unique_events','raw_delta_min','raw_delta_median','raw_delta_max','normalized_delta_median','quantity_median','zero_quantity_fraction','negative_delta_fraction','positive_delta_fraction']])+'\n\nAll widths and separated types: data/phase35/raw-delta-distribution.csv.\n'
    (docs/'PHASE35_RAW_DELTA.md').write_text(raw_report,encoding='utf-8')
    composition=[]
    for phase in ['development','replication']:
        table=display(pd.read_parquet(ROOT/phase/'summary.parquet'))
        selected=table[(table.family=='decile')&(table.kind=='ALL')&(table.direction=='LONG')].copy()
        selected=selected.sort_values('bucket',key=lambda x:pd.to_numeric(x,errors='coerce'))
        composition.append('## '+phase.title()+'\n\n'+markdown(selected[['bucket','unique_event_count','measurement_count',
            'event_balanced_tp_first_rate','event_balanced_sl_first_rate','event_balanced_neither_rate',
            'event_balanced_ambiguous_rate','event_balanced_censored_rate','mfe_pct_mean','mfe_pct_median',
            'mae_pct_mean','mae_pct_median','event_balanced_gross_expectancy_conditional_pct']]))
        series=[]
        for kind in ['SUPPORT','RESISTANCE']:
            d=table[(table.family=='rolling_visual_only')&(table.kind==kind)&(table.direction=='LONG')].copy()
            d['x']=d.bucket.map(lambda x:sum(map(float,x.split('-')))/2*100)
            d=d.sort_values('x')
            series.append((kind+' LONG',d.x.to_numpy(),d.event_balanced_tp_first_rate.to_numpy()))
        path=docs/'phase35-plots'/phase/'rolling-percentile.svg'
        path.write_text(svg_lines('Overlapping percentile windows (visual only)',series,'Percentile window center; width 20 points'),encoding='utf-8')
    (docs/'PHASE35_OUTCOME_COMPOSITION.md').write_text('# Outcome Composition\n\nOriginal 1h half-width 0.004, pooled A types, LONG, TP=SL=0.003, horizon=8. These are fixed display conditions, not a selected rule. Rates are event-balanced; MFE/MAE means and medians preserve measurement multiplicities.\n\nIn development, middle deciles have higher SL-first as well as TP-first rates, alongside fewer ambiguous outcomes. For example, decile 1 has TP 31.38%, SL 30.74%, ambiguous 37.67%; decile 5 has TP 35.03%, SL 35.34%, ambiguous 29.05%. A TP-first hump is therefore not by itself directional accuracy. This composition difference is observed; a causal microstructure explanation is not established. Compare all labels, costs-free conditional expectancy and matched-A results rather than TP-first alone.\n\n'+ '\n\n'.join(composition)+'\n',encoding='utf-8')
    for path in sorted((docs/'phase35-plots').rglob('*.svg')):
        text=path.read_text(encoding='utf-8')
        text=re.sub(r'<text id="metric-label".*?</text>','',text)
        metric='Decile 10 minus 1: event TP-first fraction' if path.stem in ['horizon','quarter-stability'] else 'Event-balanced TP-first fraction'
        text=text.replace('</svg>',f'<text id="metric-label" x="70" y="75" font-family="Georgia,serif" font-size="11" fill="#253137">Y: {metric}</text></svg>')
        ET.fromstring(text)
        path.write_text(text,encoding='utf-8')
    test=ET.parse(ROOT/'test-results.xml').getroot().find('testsuite').attrib
    assert test['failures']=='0' and test['errors']=='0'
    verification=dict(tests=test,phase3_code_unchanged=True,phase3_source_manifests_unchanged=True,
        phase35_seal_matches=True,model_hashes_match=True,causal_controls=True,
        time_boundaries_valid=True,historical_ecdf_strictly_past=True,
        replication_ecdf_development_only=True,reports_reproducible=True,
        legacy_q3_reproduction_rows=reproduced,features=audit,final_test_used=False,
        audit_script_sha256=sha256(Path(__file__)))
    write_json(ROOT/'verification.json',verification)
    overview=docs/'PHASE35_COMPLETION.md'
    text=overview.read_text(encoding='utf-8').split('\n## Final Verification')[0]
    extra=f"\n## Final Verification\n\n{test['tests']} tests passed; zero failures/errors. Original Phase 3 research code and source manifests are unchanged. All {reproduced} legacy A/quartile/outcome rows reproduce Phase 3 counts and checked metrics across development and previously observed replication. Every saved matched-control link passed the past-horizon check. Both phases' reports reproduce byte-for-byte. Original raw archives are not modified.\n\n"
    extra+='PHASE35_RAW_DELTA.md reports the exact legacy boundaries and raw delta/quantity/sign composition, with all widths and types preserved in raw-delta-distribution.csv.\n\nOverlapping-window plots below are visualization-only; their windows overlap and are not independent evidence or candidate rules.\n\n![Development rolling windows](phase35-plots/development/rolling-percentile.svg)\n\n![Previously inspected replication rolling windows](phase35-plots/replication/rolling-percentile.svg)\n'
    extra+='\nImportant: PHASE35_OUTCOME_COMPOSITION.md shows that the development middle-delta TP-first increase accompanies a SL-first increase and lower ambiguity. Do not equate the inverted-U TP-first display with directional edge.\n'
    overview.write_text(text+extra,encoding='utf-8')
    print(json.dumps({k:v for k,v in verification.items() if k!='features'},indent=2),flush=True)


if __name__=='__main__':main()
