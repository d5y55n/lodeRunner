"""Deterministic tables and offline SVG diagnostics, without rule selection."""
from html import escape
import json
import numpy as np
import pandas as pd
from .design import ROOT, design


NOTICE = ('Descriptive research only. 2021-2022 is primary research; 2023 is a '
          'previously inspected replication period, not untouched validation. No 2024 data, '
          'p-values, independence claims, threshold selection, scores or live trading. '
          'Rates exclude censored horizons; ambiguous outcomes remain ambiguous. '
          'Gross expectancy is conditional on unambiguous resolved horizons and excludes costs.')


def markdown(frame):
    def cell(v):
        if pd.isna(v):return 'NA'
        if isinstance(v,(float,np.floating)):return f'{v:.6g}'
        return str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(frame.columns)+' |','| '+' | '.join(['---']*len(frame.columns))+' |']+
                     ['| '+' | '.join(cell(v) for v in r)+' |' for r in frame.itertuples(index=False,name=None)])


def svg_lines(title, series, xlabel):
    colors=['#15616d','#b24c32','#6a753b','#74617d','#303b51','#a97916']
    points=[(x,y) for _,xs,ys in series for x,y in zip(xs,ys) if np.isfinite(x) and np.isfinite(y)]
    if not points:return '<svg xmlns="http://www.w3.org/2000/svg"><text y="20">Insufficient data</text></svg>'
    xs,ys=zip(*points);xmin,xmax=min(xs),max(xs);ymin,ymax=min(ys),max(ys)
    if xmin==xmax:xmax=xmin+1
    pad=max((ymax-ymin)*.1,.001);ymin-=pad;ymax+=pad
    px=lambda x:70+(x-xmin)/(xmax-xmin)*660
    py=lambda y:330-(y-ymin)/(ymax-ymin)*240
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="440" viewBox="0 0 900 440">',
        '<rect width="900" height="440" fill="#faf7ef"/>',
        '<g font-family="Georgia,serif" fill="#253137">',f'<text x="40" y="30" font-size="20">{escape(title)}</text>',
        '<text x="40" y="53" font-size="12">Descriptive diagnostic; not a trading signal. No uncertainty interval shown.</text>']
    for j in range(5):
        y=ymin+(ymax-ymin)*j/4
        parts.extend([f'<line x1="70" y1="{py(y):.2f}" x2="730" y2="{py(y):.2f}" stroke="#d4d4c8"/>',
                      f'<text x="8" y="{py(y)+4:.2f}" font-size="12">{y:.3f}</text>'])
    for j,(label,x,y) in enumerate(series):
        path=' '.join(f'{px(a):.2f},{py(b):.2f}' for a,b in zip(x,y) if np.isfinite(a) and np.isfinite(b))
        parts.append(f'<polyline points="{path}" fill="none" stroke="{colors[j%len(colors)]}" stroke-width="2"/>')
        parts.append(f'<text x="{40+(j%3)*280}" y="{395+(j//3)*18}" font-size="12" fill="{colors[j%len(colors)]}">{escape(label)}</text>')
    for x in sorted(set(xs)):
        if len(set(xs))<=21:parts.append(f'<text x="{px(x):.2f}" y="350" text-anchor="middle" font-size="11">{x:g}</text>')
    parts.append(f'<text x="300" y="375" font-size="13">{escape(xlabel)}</text></g></svg>')
    return '\n'.join(parts)


KEYS=['period','configuration_id','width_model','width_parameter','kind','direction','tp','sl','horizon','facet','facet_value']


def contrasts(table):
    d=table[(table.family=='decile')&table.bucket.isin(['1','10'])]
    cols=KEYS+['unique_event_count','event_balanced_tp_first_rate','matched_incremental_tp']
    a=d[d.bucket=='1'][cols];b=d[d.bucket=='10'][cols]
    out=a.merge(b,on=KEYS,suffixes=('_low','_high'))
    out['high_minus_low_event_tp']=out.event_balanced_tp_first_rate_high-out.event_balanced_tp_first_rate_low
    out['high_minus_low_matched_increment']=out.matched_incremental_tp_high-out.matched_incremental_tp_low
    out['both_buckets_at_least_100']=(out.unique_event_count_low>=100)&(out.unique_event_count_high>=100)
    return out


def shapes(table):
    records=[]
    d=table[(table.family=='decile')&(table.facet=='ALL')&(table.bucket!='MISSING')].copy()
    d['position']=d.bucket.astype(int)
    for key,group in d.groupby(KEYS,sort=True):
        group=group.sort_values('position');y=group.event_balanced_tp_first_rate.to_numpy();diff=np.diff(y)
        enough=bool((group.unique_event_count>=100).all())
        records.append({**dict(zip(KEYS,key)), 'all_deciles_at_least_100':enough,
            'increasing_steps':int((diff>1e-12).sum()),'decreasing_steps':int((diff < -1e-12).sum()),
            'strictly_monotonic_descriptive':bool(enough and (np.all(diff>=0) or np.all(diff<=0))),
            'max_minus_min_event_tp':float(np.nanmax(y)-np.nanmin(y)) if np.isfinite(y).any() else np.nan})
    return pd.DataFrame(records)


def display(table):
    return table[(table.width_model=='original_timeframe')&(table.tp==.003)&(table.sl==.003)&(table.horizon==8)]


def reports(phase,root=ROOT):
    dest=root/phase;table=pd.read_parquet(dest/'summary.parquet')
    folder=dest/'reports';folder.mkdir(exist_ok=True);plots=folder/'plots';plots.mkdir(exist_ok=True)
    shape=shapes(table);contrast=contrasts(table)
    shape.to_csv(dest/'curve-shapes.csv',index=False,float_format='%.12g',lineterminator='\n')
    contrast.to_csv(dest/'contrasts.csv',index=False,float_format='%.12g',lineterminator='\n')
    small=display(table);metrics=['unique_event_count','measurement_count','event_balanced_tp_first_rate',
        'delta_vs_A_alone','delta_vs_facet_A_alone','matched_complete_targets','unique_control_events','matched_incremental_tp']
    standard='\n\nDisplay slice only: original half-width 0.004, TP=SL=0.003, horizon=8. Both types/directions remain separate. All widths and outcome combinations are in summary.csv/parquet. Empty/sparse buckets are retained and flagged, not promoted as discoveries.\n\n'
    def save(name,title,body):
        (folder/name).write_text('# '+title+'\n\n'+NOTICE+'\n\nPeriod: '+('2021-2022 primary development' if phase=='development' else '2023 previously inspected replication period')+standard+body+'\n',encoding='utf-8')
    continuous=small[(small.facet=='ALL')&(small.kind=='ALL')&(small.direction=='LONG')&small.family.isin(['A_ALONE','decile','ventile','quartile','row_ecdf_decile','legacy_quartile','normalized_delta','normalized_sign_0.05'])]
    save('PHASE35_DELTA_CONTINUOUS.md','Continuous Delta',
        'Historical percentiles use event-balanced strictly past ECDFs in development and frozen development ECDFs in replication. Row ECDF and legacy pooled quartiles are separate sensitivities. The legacy label uses full-development boundaries and is not an online development feature.\n\n'+
        markdown(continuous[['family','bucket',*metrics]])+'\n\nNormalized bucket j covers [-1+0.2*(j-1), -1+0.2*j), with +1 included in bucket 10. Normalized zero-volume rows are MISSING, not balanced flow.\n\n![Delta curve](plots/delta-percentile.svg)\n\n![Normalized curve](plots/normalized-delta.svg)')
    split=small[(small.facet=='ALL')&(small.kind!='ALL')&small.family.isin(['A_ALONE','normalized_sign_0.05'])]
    save('PHASE35_SUPPORT_RESISTANCE_SPLIT.md','Support and Resistance',markdown(split[['kind','direction','family','bucket',*metrics]])+
        '\n\nThe fixed near-zero normalized interval is [-0.05,0.05]; sensitivities 0/0.01/0.10 and raw sign are in the full table. No microstructure explanation is imposed.\n\n![Type split](plots/support-resistance.svg)')
    v=display(contrast)
    save('PHASE35_VISIT_ORDER.md','Visit Order',
        'The descriptive contrast below is decile 10 minus decile 1, not a selected trading region. Positive values do not establish significance.\n\n'+
        markdown(v[(v.facet=='visit_group')&(v.kind!='ALL')][['kind','direction','facet_value','unique_event_count_low','unique_event_count_high','high_minus_low_event_tp','high_minus_low_matched_increment']])+
        '\n\n![Visit curves](plots/visit-order.svg)')
    t=contrast[(contrast.width_model=='original_timeframe')&(contrast.facet=='ALL')&(contrast.kind!='ALL')]
    save('PHASE35_TPSL_HORIZON.md','TP SL and Horizon',markdown(t[['kind','direction','tp','sl','horizon','unique_event_count_low','unique_event_count_high','high_minus_low_event_tp','high_minus_low_matched_increment']])+
        '\n\nGross expectancy in full summaries conditions on resolved outcomes and is not total return. The horizon is not a mandatory live exit. Width robustness is available for all six configurations in contrasts.csv.\n\n![Horizon diagnostic](plots/horizon.svg)')
    r=v[v.facet.isin(['quarter','volatility_regime','return_regime'])&(v.kind!='ALL')]
    save('PHASE35_REGIME_STABILITY.md','Regime and Chronological Stability',
        'Regimes use January 2021 price-only fits. Earlier rows are CALIBRATION; matched controls are unavailable there. Calendar-quarter splits are deterministic and never shuffled.\n\n'+
        markdown(r[['kind','direction','facet','facet_value','unique_event_count_low','unique_event_count_high','high_minus_low_event_tp','high_minus_low_matched_increment']])+
        '\n\n![Quarter stability](plots/quarter-stability.svg)')
    def curve(family,facet='ALL',kind='ALL',directions=['LONG']):
        d=small[(small.family==family)&(small.facet==facet)&(small.bucket!='MISSING')]
        d=d[d.direction.isin(directions)]
        if kind is not None:d=d[d.kind==kind]
        return d
    series=[]
    for family in ['decile','row_ecdf_decile']:
        d=curve(family).sort_values('bucket',key=lambda x:x.astype(int))
        series.append((family,d.bucket.astype(int).to_numpy(),d.event_balanced_tp_first_rate.to_numpy()))
    (plots/'delta-percentile.svg').write_text(svg_lines('Delta percentile: event-balanced TP-first',series,'Decile'),encoding='utf-8')
    series=[]
    for kind in ['SUPPORT','RESISTANCE']:
        d=curve('normalized_delta',kind=kind).sort_values('bucket',key=lambda x:x.astype(int))
        series.append((kind,-1+(d.bucket.astype(int).to_numpy()-.5)*.2,d.event_balanced_tp_first_rate.to_numpy()))
    (plots/'normalized-delta.svg').write_text(svg_lines('Normalized delta: LONG',series,'Delta / quantity (bin midpoint)'),encoding='utf-8')
    series=[]
    for kind in ['SUPPORT','RESISTANCE']:
        for direction in ['LONG','SHORT']:
            d=curve('decile',kind=kind,directions=[direction]).sort_values('bucket',key=lambda x:x.astype(int))
            series.append((kind+' '+direction,d.bucket.astype(int).to_numpy(),d.event_balanced_tp_first_rate.to_numpy()))
    (plots/'support-resistance.svg').write_text(svg_lines('Type and direction',series,'Historical delta decile'),encoding='utf-8')
    series=[]
    for visit in ['1','2','3','4+']:
        d=curve('decile',facet='visit_group',kind='SUPPORT');d=d[d.facet_value==visit].sort_values('bucket',key=lambda x:x.astype(int))
        series.append(('SUPPORT LONG visit '+visit,d.bucket.astype(int).to_numpy(),d.event_balanced_tp_first_rate.to_numpy()))
    (plots/'visit-order.svg').write_text(svg_lines('Visit order: SUPPORT LONG',series,'Historical delta decile'),encoding='utf-8')
    series=[]
    for kind in ['SUPPORT','RESISTANCE']:
        d=v[(v.facet=='quarter')&(v.kind==kind)&(v.direction=='LONG')].sort_values('facet_value')
        series.append((kind+' LONG',np.arange(1,len(d)+1),d.high_minus_low_event_tp.to_numpy()))
    (plots/'quarter-stability.svg').write_text(svg_lines('Quarter stability: decile 10 minus 1',series,'Chronological UTC quarter'),encoding='utf-8')
    series=[]
    for kind in ['SUPPORT','RESISTANCE']:
        d=t[(t.kind==kind)&(t.direction=='LONG')&(t.tp==.003)&(t.sl==.003)].sort_values('horizon')
        series.append((kind+' LONG',d.horizon.to_numpy(),d.high_minus_low_event_tp.to_numpy()))
    (plots/'horizon.svg').write_text(svg_lines('Horizon: decile 10 minus 1',series,'Future candles (not live exits)'),encoding='utf-8')
    return table


def completion(root=ROOT):
    dev=pd.read_parquet(root/'development/summary.parquet');rep=pd.read_parquet(root/'replication/summary.parquet')
    keys=[k for k in KEYS if k!='period']+['family','bucket']
    metrics=['unique_event_count','measurement_count','event_balanced_tp_first_rate','delta_vs_A_alone','matched_incremental_tp','sufficient_unique_events']
    comparison=dev[keys+metrics].merge(rep[keys+metrics],on=keys,suffixes=('_development','_replication'),how='outer')
    comparison.to_csv(root/'replication-comparison.csv',index=False,float_format='%.12g',lineterminator='\n')
    docs=root.parents[1]/'docs/research'
    for path in (root/'development/reports').glob('*.md'):
        # Plot links stay valid through a shared, uniquely named directory below.
        text=path.read_text(encoding='utf-8').replace('(plots/','(phase35-plots/development/')
        (docs/path.name).write_text(text,encoding='utf-8')
    import shutil
    for phase in ['development','replication']:
        target=docs/'phase35-plots'/phase;target.mkdir(parents=True,exist_ok=True)
        for path in (root/phase/'reports/plots').glob('*.svg'):shutil.copyfile(path,target/path.name)
    show=comparison[(comparison.width_model=='original_timeframe')&(comparison.kind!='ALL')&(comparison.direction=='LONG')&
        (comparison.tp==.003)&(comparison.sl==.003)&(comparison.horizon==8)&(comparison.facet=='ALL')&(comparison.family=='decile')]
    (docs/'PHASE35_2023_REPLICATION.md').write_text('# 2023 Previously Inspected Replication\n\n'+NOTICE+
        '\n\nSame descriptive design, six widths and outcome grid; no refitting using 2023. 2023 ECDFs are frozen whereas development ECDFs expand. That calibration-policy change can itself affect bucket membership. Quarterly labels naturally differ by year; do not merge them as the same quarter.\n\n'+
        markdown(show[['kind','bucket','unique_event_count_development','unique_event_count_replication','delta_vs_A_alone_development','delta_vs_A_alone_replication','matched_incremental_tp_development','matched_incremental_tp_replication']])+
        '\n\nAll replication breakdown reports are in data/phase35/replication/reports; complete comparison is replication-comparison.csv.\n\n![Replication curve](phase35-plots/replication/support-resistance.svg)\n',encoding='utf-8')
    # Questions are answered with descriptive quantities, not a selected threshold.
    ds=pd.read_csv(root/'development/curve-shapes.csv');dc=pd.read_csv(root/'development/contrasts.csv')
    eligible=ds[ds.all_deciles_at_least_100]
    legacy=display(dev);legacy=legacy[(legacy.family=='legacy_quartile')&(legacy.facet=='ALL')&(legacy.kind=='ALL')&(legacy.direction=='LONG')]
    quarter=dc[(dc.facet=='quarter')&(dc.width_model=='original_timeframe')&(dc.kind!='ALL')&(dc.direction=='LONG')&(dc.tp==.003)&(dc.sl==.003)&(dc.horizon==8)]
    rc=pd.read_csv(root/'replication/contrasts.csv')
    primary=dc[(dc.facet=='ALL')&(dc.kind!='ALL')&dc.both_buckets_at_least_100]
    def sign_consistency(frame, varying):
        base=[k for k in KEYS if k not in ['period','facet','facet_value',*varying]]
        if varying==['quarter']:base=[k for k in base if k!='quarter']
        fractions=[]
        for _,g in frame.groupby(base,sort=True):
            y=g.high_minus_low_event_tp.dropna()
            if len(y)>1:fractions.append(bool((y>0).all() or (y<0).all()))
        return f'{sum(fractions)}/{len(fractions)}'
    shapes_split=ds[(ds.kind!='ALL')&ds.all_deciles_at_least_100]
    type_span=shapes_split.groupby('kind').max_minus_min_event_tp.median().to_dict()
    direction_span=shapes_split.groupby('direction').max_minus_min_event_tp.median().to_dict()
    visit_data=dc[(dc.facet=='visit_group')&(dc.kind!='ALL')&dc.both_buckets_at_least_100]
    quarter_data=dc[(dc.facet=='quarter')&(dc.kind!='ALL')&dc.both_buckets_at_least_100]
    comparison_keys=[k for k in KEYS if k!='period']
    paired=primary.merge(rc[(rc.facet=='ALL')&rc.both_buckets_at_least_100],on=comparison_keys,suffixes=('_dev','_rep'))
    agreement=int(((paired.high_minus_low_event_tp_dev*paired.high_minus_low_event_tp_rep)>0).sum())
    horizon=primary.groupby('horizon').high_minus_low_event_tp.agg(['median','min','max'])
    legacy_grid=dev[(dev.family=='legacy_quartile')&(dev.facet=='ALL')&(dev.bucket!='MISSING')&(dev.kind!='ALL')]
    group_keys=['configuration_id','kind','direction','tp','sl','horizon']
    legacy_best=legacy_grid.loc[legacy_grid.groupby(group_keys).event_balanced_tp_first_rate.idxmax()]
    q3_top=int((legacy_best.bucket=='3').sum())
    incremental=primary.high_minus_low_matched_increment.dropna()
    answers=[
        f'1. **Monotonic or nonlinear?** {int(eligible.strictly_monotonic_descriptive.sum())}/{len(eligible)} sufficiently populated type/width/outcome decile curves are monotonic in all nine steps. Nonmonotonic descriptive curves do not establish a true nonlinear function; noise and subgroup composition remain explanations.',
        f'2. **Q3 stable or binning artifact?** Legacy Q3 is the highest displayed quartile in {q3_top}/{len(legacy_best)} separated type/width/outcome development settings (ties use fixed bucket order). This is a diagnostic of the prior observation, not selection. A Q3 maximum alone is not a stable continuous region; the boundaries were pooled across Phase 3 detectors/full development. Historical deciles and ECDF sensitivities below test a different, causal definition.',
        f'3. **Support or resistance?** Median within-curve max-minus-min event TP rate by type is {type_span}. This measures descriptive variation, not predictive strength; matching, contexts and multiple comparisons prevent declaring one type universally more informative.',
        f'4. **LONG or SHORT?** The corresponding median curve ranges are {direction_span}. Both directions exhibit the reported heterogeneity; ranges do not prove a directional edge or justify support=LONG/resistance=SHORT.',
        f'5. **Visit number?** Decile-10-minus-1 keeps one sign across available sufficiently populated visit groups in {sign_consistency(visit_data,[])} comparable settings. Changes in the remaining settings mean that a pooled relationship does not transfer uniformly across visits. Full curves/counts accompany the contrast.',
        f'6. **Width sensitivity?** The same contrast keeps one sign across sufficiently populated widths in {sign_consistency(primary,["configuration_id","width_model","width_parameter"])} comparable settings. Magnitudes and curves still vary; agreement shares events and is not independent replication. No width is selected.',
        f'7. **TP/SL robustness?** Contrast sign is consistent across the four existing pairs in {sign_consistency(primary,["tp","sl"])} comparable settings. This is a sign-consistency diagnostic, not proof of survival after costs or of a winning pair.',
        '8. **Decay with horizon?** Median/min/max decile contrast at 4/8/24 candles is shown below. A single universal decay time is not identified; changing ambiguous/censored composition and overlapping horizons preclude interpreting this as an execution horizon.',
        f'9. **Persistence across 2021-2022?** Contrast sign is consistent across sufficiently populated quarters in {sign_consistency(quarter_data,[])} comparable settings. Quarter reversals/heterogeneity are explicit evidence against treating a pooled shape as universally persistent; these are not independent significance tests.',
        f'10. **2023 similarity?** Development/replication high-minus-low signs agree in {agreement}/{len(paired)} comparable separated type/width/outcome settings. Similarities and differences are therefore quantifiable, but the exposed replication period and changed expanding/frozen calibration policy cannot validate a threshold.',
        f'11. **Incremental information beyond A alone?** The matched-A high-minus-low increment ranges from {incremental.min():.6g} to {incremental.max():.6g}, median {incremental.median():.6g}. Subgroup-vs-A differences exist descriptively, but are not a demonstrated incremental predictive edge: reused controls, time dependence, composition and many comparisons remain. No significance claim is made.',
        '12. **Enough evidence to freeze a rule?** This descriptive iteration alone does not justify an automatic rule freeze. No rule or candidate trading region is selected. Any later explicitly chosen simple hypothesis requires a later untouched test; 2024 remains unopened.'
    ]
    (docs/'PHASE35_COMPLETION.md').write_text('# Phase 3.5 Completion\n\n'+NOTICE+'\n\n## Questions and Evidence\n\n'+ '\n\n'.join(answers)+
        '\n\n## Legacy Q3 Reconstruction (Development, Display Slice)\n\n'+markdown(legacy[['bucket','unique_event_count','measurement_count','event_balanced_tp_first_rate','delta_vs_A_alone','matched_incremental_tp']])+
        '\n\n## Chronological Contrast (Display Slice, LONG)\n\n'+markdown(quarter[['kind','facet_value','unique_event_count_low','unique_event_count_high','high_minus_low_event_tp','high_minus_low_matched_increment']])+
        '\n\n## Horizon Contrast Across Settings\n\n'+markdown(horizon.reset_index())+
        '\n\n## Artifacts and Limitations\n\nRaw features: data/phase35/{development,replication}/features/*.parquet. Outcome data is separate. Summaries: summary.csv/parquet; contrasts.csv; curve-shapes.csv. Controls use indices into event-index.parquet, with mappings saved per width/type in summary-parts/*-controls.parquet. design.json and development-seal.json lock the descriptive process, not a trading rule.\n\nAll five development diagnostic reports and PHASE35_2023_REPLICATION.md accompany this document; detailed replication reports and plots are under data/phase35/replication/reports. No bootstrap intervals or significance claims were added. Sparse ventiles remain flagged. Full phase tests and final artifact checks are recorded in verification.json.\n',encoding='utf-8')

