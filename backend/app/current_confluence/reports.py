"""Narrow current-price evidence; no spatial conclusions or winner selection."""
import numpy as np
import pandas as pd
from app.confluence.reports import markdown,summarize_evidence
from .contract import *

FOOTER='\n2023 is the **previously inspected replication period**, not an untouched final test. No 2024, live trading, leverage, new detector, spatial overlap research, cross-timeframe raw-score sum or threshold optimization. Dependent grids and unadjusted multiple comparisons remain exploratory.\n'


def save(name,body):
    if not name.startswith('PHASE5_1_'):raise ValueError('Only new reports')
    (PROJECT/name).write_text(body+FOOTER,encoding='utf-8')


def ranges(f):
    if f.empty:return pd.DataFrame()
    return f.groupby(['phase','comparison','metric']).agg(grids=('effect','size'),
        supported=('supported','sum'),minimum_effect=('effect','min'),maximum_effect=('effect','max'),
        positive=('effect',lambda v:int((v>0).sum())),negative=('effect',lambda v:int((v<0).sum())),
        CI_above_zero=('ci_low',lambda v:int((v>0).sum())),CI_below_zero=('ci_high',lambda v:int((v<0).sum())),
        minimum_A_complete=('a_complete','min'),minimum_B_complete=('b_complete','min')).reset_index()


def shape(values,supported):
    if len(values)!=4 or not np.isfinite(values).all() or not np.all(supported):return 'SPARSE'
    d=np.diff(values)
    if np.all(d==0):return 'FLAT'
    if np.all(d>=0):return 'MONOTONIC_INCREASING'
    if np.all(d<=0):return 'MONOTONIC_DECREASING'
    return 'NONLINEAR'


def qualitative(f,metric='TP_FIRST'):
    g=f[(f.metric==metric)&(f.period=='ALL')]
    if g.empty:return 'No comparisons.'
    supported=g[g.supported]
    if supported.empty:return 'No comparison/grid meets predeclared sample support; no conclusion from absent/sparse cells.'
    return (f'{len(supported)} supported pooled comparison/grid cells: {(supported.effect>0).sum()} positive, '
            f'{(supported.effect<0).sum()} negative {metric} differences. Range '
            f'[{supported.effect.min():.6g}, {supported.effect.max():.6g}]. '
            f'{(supported.ci_low>0).sum()} intervals entirely above zero; {(supported.ci_high<0).sum()} entirely below. '
            'These dependent cells are not separate discoveries or selected rules.')


def generate():
    check_freeze();out=ROOT/'reports';out.mkdir(exist_ok=True)
    summary=[];effects=[];slopes=[];counts=[];audits=[];flow=[]
    for phase in ['development','replication']:
        root=ROOT/phase
        summary.append(pd.read_parquet(root/'analysis/cohorts.parquet').assign(phase=phase))
        effects.append(pd.read_parquet(root/'analysis/contrasts.parquet').assign(phase=phase))
        slopes.append(pd.read_parquet(root/'analysis/continuous-strength.parquet').assign(phase=phase))
        f=pd.read_parquet(root/'states.parquet')
        for pattern,n in f.pattern.value_counts().sort_index().items():counts.append(dict(phase=phase,pattern=pattern,N=int(n)))
        a=read(root/'classification-audit.json')
        for tf in TFS:audits.append(dict(phase=phase,timeframe=tf,changed_state=a['changed_from_phase5_by_timeframe'][tf],
            same_price_native_close_parity=a['shared_native_close_parity'][tf],all_current_price_checks=a['reference_checks']))
        flow.extend(dict(phase=phase,status=s,N=int(n)) for s,n in f.flow_status.value_counts().items())
    summary=pd.concat(summary,ignore_index=True);effects=pd.concat(effects,ignore_index=True);slopes=pd.concat(slopes,ignore_index=True)
    stable=summarize_evidence(effects)
    for name,frame in [('stability',stable),('current-pattern-counts',pd.DataFrame(counts)),('source-price-parity',pd.DataFrame(audits)),('flow-coverage',pd.DataFrame(flow))]:
        frame.to_csv(out/(name+'.csv'),index=False);frame.to_parquet(out/(name+'.parquet'),index=False)
    shape_rows=[]
    for phase in ['development','replication']:
        for side,direction in [('support','LONG'),('resistance','SHORT')]:
            for period in ['ALL','1','2','3','4']:
                f=summary[(summary.phase==phase)&(summary.direction==direction)&(summary.period==period)]
                f=f[f.category.isin([side+'/path/'+'+'.join(p) for p in HIERARCHY])].copy()
                f['order']=f.category.map({side+'/path/'+'+'.join(p):i for i,p in enumerate(HIERARCHY)})
                for keys,g in f.groupby(['tp','sl','horizon']):
                    g=g.sort_values('order')
                    for metric in ['TP_FIRST','SL_FIRST','AMBIGUOUS','mfe_pct','mae_pct']:
                        shape_rows.append(dict(phase=phase,direction=direction,period=period,**dict(zip(['tp','sl','horizon'],keys)),metric=metric,
                            shape=shape(g[metric].to_numpy(),g.supported.to_numpy())))
    shapes=pd.DataFrame(shape_rows);shapes.to_csv(out/'exact-hierarchy-shapes.csv',index=False)
    primary_ranges=ranges(effects[(effects.period=='ALL')&(effects.family=='all_four_baselines')])
    primary_ranges.to_csv(out/'primary-comparison-ranges.csv',index=False)
    stability_counts=stable.assign(supported_both=stable.supported_dev&stable.supported_rep).groupby(['family','direction','metric']).agg(
        grids=('comparison','size'),supported_both=('supported_both','sum'),all_2022_quarters_and_rep=('same_nonzero_sign_all_dev_quarters_and_rep','sum'),
        all_eight_quarters=('same_nonzero_sign_all_eight_quarters','sum')).reset_index()
    stability_counts.to_csv(out/'stability-counts.csv',index=False)
    def stable_table(families):return markdown(stability_counts[stability_counts.family.isin(families)&stability_counts.metric.isin(['TP_FIRST','SL_FIRST','AMBIGUOUS'])])
    def description(families,metric='TP_FIRST'):
        text=''
        for phase in ['development','replication']:
            text+=f'\n{phase}: '+qualitative(effects[(effects.phase==phase)&effects.family.isin(families)],metric)+'\n'
        return text
    audit_body='# Current-Price State Audit\n\nAll four timeframes are evaluated at the SAME closed 15m P(T). Native candidate membership and 850-day window are held until their next native close; only proximity counts, original A1/A2 and nearest-price geometry are re-evaluated at P. No detector is rebuilt.\n\n'
    audit_body+='Phase 5 carried higher-timeframe descriptors from their own source close price. They are not generally same-P states between native closes. Existing Phase 5 artifacts remain unchanged, and these mismatches are a semantics correction, not a threshold fit. The 15m descriptors are reused exactly.\n\n'+markdown(pd.DataFrame(audits))
    for phase in ['development','replication']:
        a=read(ROOT/phase/'classification-audit.json')
        sample=pd.read_csv(ROOT/phase/'classification-examples.csv')
        audit_body+=f'\n## {phase}\n\nChanged complete pattern timestamps: {a["changed_pattern_timestamps"]}. Real example counts by requested type: {a["real_examples"]}. Real missing-pattern count: {a["real_missing_pattern_count"]}. Absent real types are explicitly absent; the synthetic empty-map M fixture is not a market observation.\n'
        chosen=[]
        for pattern in ['SSSS','RRRR']:
            subset=sample[sample.pattern==pattern]
            if not subset.empty:chosen.append(subset[subset['T']==subset['T'].min()])
        if chosen:audit_body+=markdown(pd.concat(chosen)[['T','P','timeframe','source_timestamp','support_count','resistance_count','raw_difference','imbalance','A1','A2','state','pattern']])
    audit_body+='\nAll deterministic full examples (mixed, neutral, missing where observed, closed-clock boundaries, same-P reference and physically truncated alignment) are in per-period classification-examples.csv. Classification audit completed before loading any future outcomes for this phase.\n\nThe previous support/resistance spatial intersection counts do NOT mean SSSS/RRRR and are not evidence for or against this hypothesis. No spatial fields are read. Full predeclared definitions: data/phase5_1/plan.json.\n'
    save('PHASE5_1_CURRENT_PRICE_STATE_AUDIT.md',audit_body)
    for pattern,direction,name in [('SSSS','LONG','SSSS_LONG'),('RRRR','SHORT','RRRR_SHORT')]:
        selected=effects[effects.comparison.str.startswith(pattern+'/vs_baseline_')]
        body=f'# {pattern} / {direction} at Current Price\n\n'
        body+='Baseline 0=all eligible; 1=15m only condition; 2=15m+1h; 3=15m+1h+4h. Baselines are inclusive and nested, evaluated on one common 15m future path. Differences are '+pattern+' minus baseline.\n\n'
        body+=markdown(primary_ranges[primary_ranges.comparison.str.startswith(pattern+'/')])
        body+='\nFull per-grid and quarterly effects, exact A/B denominators, weekly blocks and six-metric paired bootstrap intervals are in per-period analysis/contrasts.csv. Positive TP_FIRST alone is not sufficient evidence of a better outcome composition.\n'
        save('PHASE5_1_'+name+'.md',body)
    save('PHASE5_1_HIERARCHY.md','# Exact 1TF -> 2TF -> 3TF -> 4TF Hierarchy\n\nThe primary path is 15m -> 15m+1h -> 15m+1h+4h -> all four, not generic any-k counts.\n\n'+markdown(shapes[shapes.metric=='TP_FIRST'].groupby(['phase','direction','period','shape']).size().reset_index(name='grids'))+
        description(['hierarchy_increment'])+'\n'+stable_table(['hierarchy_increment','conditional_hierarchy'])+'\nSecondary paths are separately labeled in cohorts.csv. No path is ranked or selected.\n')
    slope_summary=slopes[slopes.period=='ALL'].groupby(['phase','pattern','feature','metric']).agg(
        min_slope=('slope_per_point_one','min'),max_slope=('slope_per_point_one','max'),
        supported=('supported','sum'),CI_positive=('ci_low',lambda v:int((v>0).sum())),
        CI_negative=('ci_high',lambda v:int((v<0).sum()))).reset_index()
    slope_summary.to_csv(out/'continuous-strength-summary.csv',index=False)
    save('PHASE5_1_STRENGTH.md','# Strength Within SSSS/RRRR\n\nNative signed/absolute 4D vectors remain intact. Native development quantiles are separate for each timeframe. Q4 counts are descriptive and not weighted scores. All-weak, all-medium, mixed, >=1/2/3/4 strong, native Q1-Q4 and continuous min/median/max are retained.\n'+description(['native_strength','strength_configuration','summary_strength'])+'\n'+stable_table(['native_strength','strength_configuration','summary_strength'])+
        '\n## Continuous Strength\n\nThese are separate univariate slopes per +0.1 absolute imbalance, with time-block intervals. They are NOT a fitted multivariate direction score and do not control confounding by quantity/regime.\n'+markdown(slope_summary[slope_summary.metric.isin(['TP_FIRST','SL_FIRST'])])+
        '\n## Current-Price Distance\n\nAll four nearest favored-type candidates inside their own frozen full-weight bands are compared to any outside, within the same SSSS/RRRR pattern. Max nearest absolute distance quartiles are an additional descriptive view; no historical intersection search.\n'+description(['geometry'])+'\n'+stable_table(['geometry']))
    save('PHASE5_1_CONFLICTS.md','# Secondary Current-Price Conflicts\n\nSSSR/RRRS, SSSN/RRRN, SSRR/RRSS, SSNN/RRNN and opposite-fast-timeframe states are retained without merging. No higher-timeframe dominance is assumed.\n'+description(['conflict'])+'\n'+stable_table(['conflict']))
    save('PHASE5_1_QUANTITY_RISK.md','# Quantity as Separate Path Risk\n\nWithin SSSS/RRRR, native 15m one-candle joint zone quantity is split using development-only Q1 / Q2-Q3 / Q4. It is not total-market volume and is not part of S/R or strength. Missing/quarantined observations remain missing.\n'+markdown(pd.DataFrame(flow))+'\n'+description(['quantity'],'AMBIGUOUS')+'\n'+description(['quantity'],'TP_FIRST')+'\n'+stable_table(['quantity'])+
        '\nDelta is retained only as raw descriptive appendix fields and means; it is not a classification, confluence or strength input.\n')
    save('PHASE5_1_CHRONOLOGICAL_STABILITY.md','# Chronological Stability\n\nAll UTC quarters retained, with no performance-driven period exclusion. Pooled bootstrap intervals and quarterly effect signs are distinct evidence; sparse quarters are not assumed stable.\n'+stable_table(['all_four_baselines','hierarchy_increment','native_strength','summary_strength','geometry','quantity'])+
        '\nFull same-sign flags, effects, intervals, min/max quarter effects and largest absolute quarter-effect share: reports/stability.csv. Continuous quarterly slopes: analysis/continuous-strength.csv.\n')
    save('PHASE5_1_2023_REPLICATION.md','# Frozen 2023 Replication\n\nPreviously inspected replication period. Complete definitions, code, distributions, hierarchy and comparison methods were frozen after development and tests, before any 2023 source read. No rebinning, threshold fitting or category merging.\nFreeze: `'+check_freeze()['freeze_id']+'`.\n\n'+markdown(pd.DataFrame(counts)[pd.DataFrame(counts).pattern.isin(['SSSS','RRRR'])])+'\n'+stable_table(['all_four_baselines','hierarchy_increment','native_strength','summary_strength'])+
        '\nPhase 5.1 uses common P; it must not be substituted with Phase 5 carried-price patterns or spatial counts.\n')
    test=read(ROOT/'final-tests.json');pres=read(ROOT/'preservation-audit.json')
    if test['returncode'] or pres['status']!='PASS':raise ValueError('Final gates failed')
    patterns=pd.DataFrame(counts)
    body='# Phase 5.1 Completion\n\n'
    body+=f'Tests: {test["tests"]}, failures {test["failures"]}, errors {test["errors"]}. Preserved artifacts checked: {pres["files"]}, changed: 0. Native maps and outcomes were reused; no detector rebuild.\n\n'
    body+='## Exact Completion Questions\n\n1. CURRENT-PRICE SSSS counts; 2. CURRENT-PRICE RRRR counts:\n'+markdown(patterns[patterns.pattern.isin(['SSSS','RRRR'])])
    for number,pattern,direction in [(3,'SSSS','LONG'),(4,'RRRR','SHORT')]:
        f=effects[effects.comparison.str.startswith(pattern+'/vs_baseline_')]
        body+=f'\n{number}. Does {pattern} improve {direction} versus all / 15m / 15m+1h / 15m+1h+4h?\n'
        body+=markdown(ranges(f[(f.period=='ALL')&f.metric.isin(['TP_FIRST','SL_FIRST'])]))
        body+='Improvement is not declared from a positive TP_FIRST cell alone; SL_FIRST, ambiguity, excursions, intervals and quarterly replication are retained in the dedicated report.\n'
    body+='\n5. Is the exact hierarchy monotonic?\n'+markdown(shapes[(shapes.metric=='TP_FIRST')&(shapes.period=='ALL')].groupby(['phase','direction','shape']).size().reset_index(name='grids'))
    for number,pattern,direction in [(6,'SSSS','LONG'),(7,'RRRR','SHORT')]:
        body+=f'\n{number}. Stronger per-timeframe imbalance within {pattern} for {direction}:\n'
        for phase in ['development','replication']:
            body+=phase+': '+qualitative(effects[(effects.phase==phase)&(effects.family=='native_strength')&effects.comparison.str.startswith(pattern+'/')])+'\n'
    body+='\n8. Does weakest-timeframe strength matter? Continuous minimum-strength slopes per +0.1 (all 12 grids, not a selected threshold):\n'+markdown(slope_summary[(slope_summary.feature=='strength_minimum')&slope_summary.metric.isin(['TP_FIRST','SL_FIRST'])])
    body+='\n9. Current-price nearest distances: '+description(['geometry'])+'Sparse near/far comparisons are not evidence of no effect; no proximity width was relaxed.\n'
    body+='\n10. Stable across 2022 quarters; 11. Reproduced in frozen 2023:\n'+stable_table(['all_four_baselines','hierarchy_increment','native_strength','summary_strength'])
    body+='\n12. Quantity: ambiguity and directional contrasts are reported separately, not treated as direction.\n'+description(['quantity'],'AMBIGUOUS')+description(['quantity'],'TP_FIRST')
    body+='\n13. Single candidate for untouched 2024: **not promoted from this descriptive phase**. The tables above must demonstrate a coherent primary hierarchy and current-price directional composition, not a selected positive grid or strength cutoff. Quarterly/replication reversals, sparse strength configurations, overlapping event paths, unadjusted multiple comparisons, and unspecified costs/execution remain unresolved. No arbitrary best cell was used to invent a candidate.\n'
    body+='\n## Scope Correction\n\nPhase 5 carried some higher-timeframe descriptors at their native close price. Phase 5.1 re-evaluates the frozen candidate membership at the same current 15m P. Existing Phase 5 artifacts are unchanged. Historical-axis spatial intersections are a different question and are NOT cited as evidence against SSSS/RRRR.\n\nAll compact evidence: data/phase5_1/<period>/analysis and data/phase5_1/reports. STOP; no next phase run.\n'
    save('PHASE5_1_COMPLETION.md',body)
    write(ROOT/'completion.json',dict(status='COMPLETE',no_2024=True,no_live_rule=True,no_spatial=True,
        reports={p.name:digest(p) for p in PROJECT.glob('PHASE5_1_*.md') if p.name!='PHASE5_1_PROGRESS.md'}))
