"""Reporting only: no fitting, rule selection, or new outcome measurements."""
import html
from xml.etree import ElementTree
import numpy as np
import pandas as pd
from .common import *
from .analyze import GRID,GRIDS

def table(f,limit=24):
    def fmt(x):
        if isinstance(x,(float,np.floating)):return f'{x:.5g}' if np.isfinite(x) else 'NA'
        return str(x)
    return '\n'.join(['| '+' | '.join(map(str,f.columns))+' |','|'+'|'.join(['---']*len(f.columns))+'|']+
        ['| '+' | '.join(fmt(x) for x in row)+' |' for row in f.head(limit).itertuples(index=False,name=None)]+([f'\nFirst {limit}/{len(f)} rows; full table exported.'] if len(f)>limit else []))

def svg(path,title,lines,xlabel,yrange=None,ylabel='TP_FIRST / complete (not return)'):
    w,h=1000,470;left,right,top,bottom=80,960,115,390
    xs=[x for _,pairs in lines for x,y in pairs if np.isfinite(x) and np.isfinite(y)]
    ys=[y for _,pairs in lines for x,y in pairs if np.isfinite(x) and np.isfinite(y)]
    lo,hi=(min(xs),max(xs)) if xs else (0,1)
    if hi==lo:hi+=1
    yl,yh=yrange or ((min(ys)-.02,max(ys)+.02) if ys else (0,1))
    if yl==yh:yh=yl+.01
    X=lambda x:left+(x-lo)/(hi-lo)*(right-left)
    Y=lambda y:bottom-(y-yl)/(yh-yl)*(bottom-top)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
        '<rect width="100%" height="100%" fill="#fbf8f1"/>',f'<text x="28" y="30" font-family="Georgia" font-size="19">{html.escape(title)}</text>']
    for y in np.linspace(yl,yh,6):out.append(f'<path d="M{left} {Y(y)}H{right}" stroke="#ded9cc"/><text x="14" y="{Y(y)+4}" font-size="12">{y:.3f}</text>')
    colors=['#11657b','#a95727','#55793b','#924559','#3564a0','#70683a','#333333','#946baa']
    for i,(name,pairs) in enumerate(lines):
        color=colors[i%len(colors)];pairs=[(x,y) for x,y in pairs if np.isfinite(x) and np.isfinite(y)]
        pts=' '.join(f'{X(x):.2f},{Y(y):.2f}' for x,y in pairs);dash='stroke-dasharray="5 4"' if 'replication' in name else ''
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2" {dash}/>')
        for x,y in pairs:out.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="2.5" fill="{color}"/>')
        out.append(f'<text x="{45+(i%3)*320}" y="{53+(i//3)*18}" font-size="12" fill="{color}">{html.escape(name)}</text>')
    ticks=sorted(set(xs)) if xs and len(set(xs))<=12 and all(float(x).is_integer() for x in xs) else np.linspace(lo,hi,6)
    for x in ticks:out.append(f'<text x="{X(x)-12}" y="413" font-size="12">{x:.3g}</text>')
    out.append(f'<text x="80" y="448" font-size="12">{html.escape(xlabel)}; y={html.escape(ylabel)}</text></svg>')
    path.write_text(''.join(out),encoding='utf-8');ElementTree.parse(path)

def pair_contrasts(f,low,high):
    keys=['period','map_bucket']+GRID
    cols=keys+['tp_first_rate','complete','SL_FIRST','AMBIGUOUS','NEITHER','tp_first_rate_map_only']
    a=f[f.flow_bucket.eq(low)][cols];b=f[f.flow_bucket.eq(high)][cols]
    result=a.merge(b,on=keys,how='outer',suffixes=('_moderate','_extreme'),validate='one_to_one')
    result['moderate_minus_extreme']=result.tp_first_rate_moderate-result.tp_first_rate_extreme
    result['minimum_complete']=result[['complete_moderate','complete_extreme']].min(axis=1,skipna=False)
    result['comparable']=result.minimum_complete.gt(0)&result.tp_first_rate_moderate.notna()&result.tp_first_rate_extreme.notna()
    return result

def collect():
    dest=ROOT/'reports';dest.mkdir(exist_ok=True);pairs=[];negative_pairs=[];raw_pairs=[];volume_pairs=[];shapes=[];availability=[];coverage=[]
    for phase in ['development','replication']:
        assert read(ROOT/phase/'analysis/complete.json')['status']=='COMPLETE'
        for config in CONFIGS:
            ck=key(config)
            for window in WINDOWS:
                folder=ROOT/phase/'analysis'/f'{ck}-{window}h'
                states=pd.read_parquet(folder/'states.parquet');available=states.status.eq('AVAILABLE')
                paired=states[['support_normalized_delta','resistance_normalized_delta']].dropna()
                coverage.append(dict(phase=phase,config=str(config),window=window,states=len(states),coverage_valid=int(available.sum()),
                    support_zero=int((available&states.support_quantity.eq(0)).sum()),resistance_zero=int((available&states.resistance_quantity.eq(0)).sum()),
                    shared_over_joint_median=float((states.shared_quantity/states.joint_quantity.where(states.joint_quantity.gt(0))).median()),
                    support_resistance_delta_spearman=paired.support_normalized_delta.rank().corr(paired.resistance_normalized_delta.rank())))
                m=read(ROOT/'development/analysis'/folder.name/'model.json')
                for field in DELTA:
                    f=pd.read_parquet(folder/f'curve-{field}-decile.parquet')
                    for g,t in f.groupby(['period']+GRID,sort=True):
                        t=t.sort_values('flow_bucket');v=t.tp_first_rate.to_numpy();v=v[np.isfinite(v)]
                        if len(v)<2:continue
                        shapes.append(dict(phase=phase,config=str(config),window=window,feature=field,**dict(zip(['period']+GRID,g)),
                            bins=len(v),nondecreasing=bool(np.all(np.diff(v)>=0)),nonincreasing=bool(np.all(np.diff(v)<=0)),
                            last_minus_first=float(v[-1]-v[0]),ends_minus_middle=float((v[0]+v[-1])/2-np.mean(v[1:-1])) if len(v)>2 else np.nan))
                    for cond in ['ALL',*CONDITIONS]:
                        path=folder/(f'curve-{field}-shape.parquet' if cond=='ALL' else f'within-{cond}-{field}.parquet')
                        if not path.exists():continue
                        f=pd.read_parquet(path)
                        if f.empty:continue
                        out=pair_contrasts(f,2,3)
                        neg=pair_contrasts(f,2,0)
                        for col,value in [('phase',phase),('config',str(config)),('window',window),('feature',field),('condition',cond)]:out[col]=value
                        for col,value in [('phase',phase),('config',str(config)),('window',window),('feature',field),('condition',cond)]:neg[col]=value
                        pairs.append(out)
                        negative_pairs.append(neg)
                if config[0]=='A':
                    for field in ['support_delta','resistance_delta']:
                        for cond in ['A1','imbalance','clusters']:
                            out=pair_contrasts(pd.read_parquet(folder/f'within-{cond}-{field}.parquet'),2,3)
                            for col,value in [('phase',phase),('config',str(config)),('window',window),('feature',field),('condition',cond)]:out[col]=value
                            raw_pairs.append(out)
                for cond in ['A1','A2','imbalance','clusters','candidates_per_cluster','distance_difference','volatility','recent_return']:
                    path=folder/f'within-{cond}-joint_quantity.parquet'
                    if not path.exists():continue
                    out=pair_contrasts(pd.read_parquet(path),3,0).rename(columns=lambda c:c.replace('moderate','high_volume').replace('extreme','low_volume'))
                    out['ambiguity_high_minus_low']=out.AMBIGUOUS_high_volume/out.complete_high_volume.replace(0,np.nan)-out.AMBIGUOUS_low_volume/out.complete_low_volume.replace(0,np.nan)
                    for col,value in [('phase',phase),('config',str(config)),('window',window),('feature','joint_quantity'),('condition',cond)]:out[col]=value
                    volume_pairs.append(out)
                for field,model in m.items():availability.append(dict(config=str(config),window=window,feature=field,ventile_supported=model['ventile_supported']))
    pair=pd.concat(pairs,ignore_index=True);shape_frame=pd.DataFrame(shapes)
    pair.to_parquet(dest/'moderate-extreme-contrasts.parquet',index=False,compression='zstd')
    negative=pd.concat(negative_pairs,ignore_index=True).rename(columns=lambda c:c.replace('extreme','negative'))
    negative.to_parquet(dest/'moderate-negative-contrasts.parquet',index=False,compression='zstd')
    raw=pd.concat(raw_pairs,ignore_index=True).rename(columns=lambda c:c.replace('moderate','raw_q3').replace('extreme','raw_q4'))
    raw.to_parquet(dest/'raw-quartile-reconciliation.parquet',index=False,compression='zstd')
    volume=pd.concat(volume_pairs,ignore_index=True)
    volume.to_parquet(dest/'volume-composition-contrasts.parquet',index=False,compression='zstd')
    shape_frame.to_csv(dest/'delta-shapes.csv',index=False);pd.DataFrame(coverage).to_csv(dest/'coverage.csv',index=False)
    pd.DataFrame(availability).drop_duplicates().to_csv(dest/'ventile-eligibility.csv',index=False)
    return pair,shape_frame,pd.DataFrame(coverage),negative,raw,volume

def main():
    seal=check_freeze();verification=read(ROOT/'verification.json')
    if verification['status']!='PASS':raise ValueError('Final audit required')
    pair,shapes,coverage,negative,raw,volume=collect();dest=ROOT/'reports';plots=dest/'plots';plots.mkdir(exist_ok=True)
    keys=['config','window','feature','condition','map_bucket']+GRID
    overall=pair[pair.period.eq('ALL')]
    comparison=overall[overall.phase.eq('development')].merge(overall[overall.phase.eq('replication')],on=keys,suffixes=('_development','_replication'),how='outer')
    comparison['same_sign']=np.sign(comparison.moderate_minus_extreme_development)==np.sign(comparison.moderate_minus_extreme_replication)
    comparison['both_observed']=comparison.comparable_development.fillna(False)&comparison.comparable_replication.fillna(False)
    comparison.to_parquet(dest/'replication-comparison.parquet',index=False,compression='zstd')
    stability=[]
    for k,g in pair[~pair.period.eq('ALL')].groupby(['phase']+keys,sort=True):
        finite=g[g.comparable&g.moderate_minus_extreme.notna()]
        stability.append(dict(zip(['phase']+keys,k))|dict(observed_quarters=len(finite),
            same_sign_four_quarters=bool(len(finite)==4 and (finite.moderate_minus_extreme.gt(0).all() or finite.moderate_minus_extreme.lt(0).all())),
            minimum_cell_complete=float(finite.minimum_complete.min()) if len(finite) else np.nan))
    stability=pd.DataFrame(stability);stability.to_parquet(dest/'quarter-stability.parquet',index=False)
    diagnostic=[]
    for (condition,feature),g in comparison.groupby(['condition','feature']):
        matched=g[g.both_observed];s=stability[(stability.phase=='development')&(stability.condition==condition)&(stability.feature==feature)]
        diagnostic.append(dict(condition=condition,feature=feature,observed_pairs=len(matched),
            same_sign_pairs=int(matched.same_sign.sum()),four_quarter_cells=int(s.observed_quarters.eq(4).sum()),
            consistent_four_quarters=int(s.same_sign_four_quarters.sum())))
    diagnostic=pd.DataFrame(diagnostic);diagnostic.to_csv(dest/'stability-overview.csv',index=False)
    neg_all=negative[negative.period.eq('ALL')]
    neg_compare=neg_all[neg_all.phase.eq('development')].merge(neg_all[neg_all.phase.eq('replication')],on=keys,suffixes=('_development','_replication'),how='outer')
    neg_compare['both_observed']=neg_compare.comparable_development.fillna(False)&neg_compare.comparable_replication.fillna(False)
    neg_compare['same_sign']=np.sign(neg_compare.moderate_minus_negative_development)==np.sign(neg_compare.moderate_minus_negative_replication)
    neg_compare.to_parquet(dest/'moderate-negative-replication.parquet',index=False)
    negative_summary=[]
    for (condition,feature),g in neg_compare.groupby(['condition','feature']):
        g=g[g.both_observed]
        negative_summary.append(dict(condition=condition,feature=feature,observed_pairs=len(g),same_sign_pairs=int(g.same_sign.sum())))
    negative_summary=pd.DataFrame(negative_summary);negative_summary.to_csv(dest/'moderate-negative-overview.csv',index=False)
    v=volume[volume.period.eq('ALL')]
    v=v[v.phase.eq('development')].merge(v[v.phase.eq('replication')],on=keys,suffixes=('_development','_replication'),how='outer')
    volume_summary=[]
    for condition,g in v.groupby('condition'):
        g=g[g.comparable_development.fillna(False)&g.comparable_replication.fillna(False)]
        volume_summary.append(dict(condition=condition,observed_pairs=len(g),
            higher_ambiguity_both=int((g.ambiguity_high_minus_low_development.gt(0)&g.ambiguity_high_minus_low_replication.gt(0)).sum()),
            lower_tp_fraction_both=int((g.high_volume_minus_low_volume_development.lt(0)&g.high_volume_minus_low_volume_replication.lt(0)).sum())))
    volume_summary=pd.DataFrame(volume_summary);volume_summary.to_csv(dest/'volume-composition-overview.csv',index=False)
    vq=volume[volume.phase.eq('development')&~volume.period.eq('ALL')&volume.comparable].groupby(keys).agg(
        observed_quarters=('period','nunique'),higher_ambiguity_all=('ambiguity_high_minus_low',lambda x:bool(x.gt(0).all()))).reset_index()
    vq.to_parquet(dest/'volume-quarter-stability.parquet',index=False)
    for i,r in volume_summary.iterrows():
        g=vq[vq.condition.eq(r.condition)&vq.observed_quarters.eq(4)]
        volume_summary.loc[i,'four_quarter_cells']=len(g)
        volume_summary.loc[i,'higher_ambiguity_four_quarters']=int(g.higher_ambiguity_all.sum())
    volume_summary.to_csv(dest/'volume-composition-overview.csv',index=False)
    akey=key(CONFIGS[0]);a_config=str(CONFIGS[0]);plotnames=[]
    for direction,tp,sl,h in GRIDS:
        suffix=f'{direction}-{tp}-{sl}-{h}'
        def selected(f):return f[f.period.eq('ALL')&f.direction.eq(direction)&f.tp.eq(tp)&f.sl.eq(sl)&f.horizon.eq(h)]
        for window in WINDOWS:
            lines=[]
            for phase in ['development','replication']:
                for field in DELTA[:2]:
                    f=selected(pd.read_parquet(ROOT/phase/'analysis'/f'{akey}-{window}h'/f'curve-{field}-decile.parquet')).sort_values('flow_bucket')
                    lines.append((phase+' '+field.split('_')[0],list(zip(f.observed_flow_median,f.tp_first_rate))))
            name=f'side-delta-{window}h-{suffix}.svg';svg(plots/name,f'Side Delta, {window}h: {suffix}',lines,'Observed median normalized Delta in frozen bins');plotnames.append(name)
        for cond in ['A1','imbalance','clusters']:
            lines=[]
            for phase in ['development','replication']:
                f=selected(pd.read_parquet(ROOT/phase/'analysis'/f'{akey}-1h'/f'within-{cond}-support_normalized_delta.parquet'))
                for b,g in f.groupby('map_bucket'):
                    g=g.sort_values('flow_bucket');lines.append((phase+f' map bucket {b}',list(zip(g.flow_bucket,g.tp_first_rate))))
            name=f'within-{cond}-{suffix}.svg';svg(plots/name,f'Support Delta within {cond}, 1h: {suffix}',lines,'0 negative; 1 near zero; 2 moderate positive; 3 extreme positive');plotnames.append(name)
    # Window and chronological views of the predeclared display grid, without selecting a best window.
    display=pair[(pair.config==a_config)&pair.direction.eq('LONG')&pair.tp.eq(.003)&pair.sl.eq(.003)&pair.horizon.eq(8)]
    for condition in ['ALL','A1','imbalance','clusters','age_band','mean_prior_crossings']:
        lines=[]
        f=display[display.condition.eq(condition)&display.feature.eq(DELTA[0])&display.window.eq(1)&~display.period.eq('ALL')]
        for (phase,b),g in f.groupby(['phase','map_bucket']):
            g=g.sort_values('period');lines.append((phase+f' bucket {b}',[(int(p[-1]),v) for p,v in zip(g.period,g.tp_first_rate_moderate)]))
        name=f'quarter-{condition}.svg';svg(plots/name,f'Moderate support Delta by quarter within {condition}',lines,'Quarter number; missing cells omitted');plotnames.append(name)
    lines=[]
    for (phase,feature),g in display[display.condition.eq('ALL')&display.period.eq('ALL')].groupby(['phase','feature']):
        g=g.sort_values('window');lines.append((phase+' '+feature.replace('_normalized_delta',''),list(zip(g.window,g.tp_first_rate_moderate))))
    name='window-sensitivity.svg';svg(plots/name,'Moderate-positive flow, parallel 1h/4h/8h variants',lines,'Observation hours; no winner selected');plotnames.append(name)
    lines=[]
    for phase in ['development','replication']:
        f=pd.read_parquet(ROOT/phase/'analysis'/f'{akey}-1h/within-A1-joint_quantity.parquet')
        f=f[f.period.eq('ALL')&f.direction.eq('LONG')&f.tp.eq(.003)&f.sl.eq(.003)&f.horizon.eq(8)]
        g=f.groupby('flow_bucket')[['TP_FIRST','SL_FIRST','AMBIGUOUS','complete']].sum()
        for label in ['TP_FIRST','SL_FIRST','AMBIGUOUS']:lines.append((phase+' '+label,list(zip(g.index,g[label]/g.complete))))
    name='joint-volume-composition.svg';svg(plots/name,'Joint volume and outcome composition: LONG .003/.003 8h',lines,'Frozen volume quartile',yrange=(0,1),ylabel='outcome / complete (not return)');plotnames.append(name)
    page='<html><head><meta charset="utf-8"><title>Phase 3R.2</title></head><body style="background:#fbf8f1;font-family:Georgia;max-width:1100px;margin:35px auto"><h1>Full-map + flow diagnostics</h1><p>Future outcomes for research only. Not creation-time information or trading rules. Frozen development bins; 2023 is previously inspected replication. Y axes may be truncated to show shape; inspect labels. Shared intervals deduplicated. Shapes are descriptive binned curves, not fitted causal response functions.</p>'
    for name in plotnames:page+=f'<figure><img style="width:100%" src="plots/{name}" alt="{html.escape(name)}"/></figure>'
    (dest/'diagnostics.html').write_text(page+'</body></html>',encoding='utf-8')
    warn='All relationships are descriptive and dependent. No p-values, threshold selection, detector/window ranking, executable return or edge claim. Complete denominators include AMBIGUOUS and NEITHER; censored rows remain recorded. Conditional gross expectancy excludes unresolved/ambiguous/censored outcomes and costs.'
    scope='Development: the unchanged 8,647 hourly events from 2022-01-05 17:00 through 2022-12-31 23:00 UTC. Replication: 8,760 events in 2023, labeled `previously inspected replication period`. No 2024, other timeframes, D predictive comparison, or live rules.'
    methods='Conditioned tables retain same-period unconditioned TP fraction, same valid/finite-flow cohort baseline, and same-cohort map-only stratum baseline. The incremental column is conditioned fraction minus map-only fraction. One-dimensional frozen strata are not exact full-map matching; residual confounding within buckets remains. Joint cluster concentration additionally crosses map direction, cluster quartile and candidates-per-cluster quartile. Sparse/absent cells are not filled or refit.'
    illustrative=display[display.period.eq('ALL')&display.condition.isin(['ALL','A1','imbalance','clusters'])&display.window.eq(1)&display.feature.eq(DELTA[0])][['phase','condition','map_bucket','complete_moderate','complete_extreme','moderate_minus_extreme']]
    example_match=comparison[(comparison.config==a_config)&comparison.window.eq(1)&comparison.condition.eq('A1')&comparison.feature.eq(DELTA[0])&comparison.direction.eq('LONG')&comparison.tp.eq(.003)&comparison.sl.eq(.003)&comparison.horizon.eq(8)&comparison.both_observed]
    example_quarters=stability[(stability.config==a_config)&stability.phase.eq('development')&stability.window.eq(1)&stability.condition.eq('A1')&stability.feature.eq(DELTA[0])&stability.direction.eq('LONG')&stability.tp.eq(.003)&stability.sl.eq(.003)&stability.horizon.eq(8)]
    example_note=f"In this fixed display grid, {int(example_match.same_sign.sum())}/{len(example_match)} observed A1 strata retain the pooled moderate-minus-extreme sign in 2023, but only {int(example_quarters.same_sign_four_quarters.sum())}/{len(example_quarters)} keep one sign across all four development quarters. Partial pooled replication and chronological stability are different questions."
    diag=diagnostic[diagnostic.condition.isin(['A1','A2','imbalance','clusters','candidates_per_cluster','distance_difference'])]
    mono=shapes[shapes.period.eq('ALL')].groupby(['phase','feature']).agg(curves=('bins','size'),increasing=('nondecreasing','sum'),decreasing=('nonincreasing','sum')).reset_index()
    def save(name,body):(PROJECT/name).write_text(body.strip()+'\n',encoding='utf-8')
    def report(name,title,body):save(name,f'# {title}\n\n{scope}\n\n{body}\n\n{warn}\n\nMachine-readable tables: `data/phase3r2/`; diagnostic plots: `data/phase3r2/reports/diagnostics.html`.\n')
    report('PHASE3R2_VOLUME_FEATURES.md','Causal Volume Features',f'''Current-T nearby candidates use unchanged .004 full-band intervals, including candidates contributing in the outer half band. Within each side, closed intervals are merged before querying exact observed-price hourly aggregate-trade profiles. Joint union merges both sides. Windows are [T-1h,T), [T-4h,T), [T-8h,T); maps stay fixed at T. This is not a history of earlier maps. No trades at or after T.

Formulas: quantity=buy+sell; raw Delta=buy-sell; normalized Delta=(buy-sell)/quantity only for quantity>0; normalized difference=support ND-resistance ND; raw difference=support Delta-resistance Delta; buy-share difference=normalized difference/2. Side volume share=Qs/(Qs+Qr), a relative side-exposure statistic, NOT deduplicated total volume. Shared=Qs+Qr-Qjoint. Qjoint, not Qs+Qr, is combined actual volume. No opaque score.

Unavailable windows invalidate all flow values; zero covered quantity remains zero but normalized Delta is undefined, not neutral. Any existing quarantine intersecting any hour invalidates the whole window. Missing profiles are not zero-filled, even with empty intervals. Source checksums match forensic coverage. No candle volume substitution.

{table(coverage)}

Shared-over-joint is shared quantity divided by deduplicated joint quantity when joint quantity is positive. In development A/1h its median is 1.0 and side-Delta rank correlation is about 0.9941. Support Delta's rank correlation with A1 is only about -0.0362 in that same slice: lack of simple score correlation does not by itself demonstrate useful incremental prediction.

Per-feature overall/quarter distributions, missing/zero frequencies, and Spearman correlations with A1/A2/imbalance/clusters/distances/volatility/recent return are in each analysis folder. Support/resistance side coverage is shared at window level; covered empty side unions have quantity zero. Strong side correlations can arise from overlapping intervals, not independent confirmation.''')
    report('PHASE3R2_DELTA_SHAPE.md','Delta Shape',f'''All 24 grids, three windows and five maps are retained. Development-defined deciles are always shown. Ventiles require all 20 bins to contain >=200 development states and >=5 weekly blocks. No 2023 refit. Observed median flow on continuous-x plots is descriptive; connected bin averages are not a fitted response function.

Near-zero is [-0.01,0.01]. Negative is below -0.01. Positive is above 0.01; moderate positive ends at the development positive-value 90th percentile and extreme positive is above it. These are predeclared reporting partitions, not entries. Phase 3.5 used a different near-zero definition; comparisons are qualitative, not identical thresholds.

{table(mono)}

Finite-sample monotonicity and endpoint/middle curvature diagnostics are in delta-shapes.csv for every quarter. Nonmonotonicity alone does not prove an inverted-U effect or a useful threshold. Moderate/extreme contrasts are shown with cell counts, not only favorable cells.''')
    report('PHASE3R2_INCREMENTAL_VALUE.md','Incremental Information',f'''{methods}

Same-sign moderate-minus-extreme comparisons and quarter consistency across every grid/window/map (not independent votes):

{table(diag)}

Moderate-positive minus negative flow in the SAME map stratum (separate from the tail question):

{table(negative_summary[negative_summary.condition.isin(['A1','A2','imbalance','clusters'])])}

Each CI uses shared 1,000 seven-day block resamples for cell and map-only baseline, seed 3202; blocks are floor(timestamp_ms / 604800000), anchored at 1970-01-01 00:00 UTC, with partial boundary blocks retained. At least five represented blocks and 950 finite draws are required. Predeclared CI scope is A, all three windows, support/resistance normalized Delta and their difference within A1/imbalance/clusters, all outcome grids. B/C and other strata have chronological descriptive comparisons, not row-level inference. Cell-minus-baseline CIs are NOT CIs for the difference between two cells. Seven days does not eliminate every long-memory or regime-dependence concern.

## Quantity Is Not the Same Question as Directional Delta

High-minus-low JOINT quantity quartiles within the SAME map stratum show a substantial outcome-composition association. Compare both TP_FIRST and SL_FIRST with AMBIGUOUS, not just directional success. The table counts matched development/replication cells with higher ambiguity in the high-volume quartile, plus development four-quarter consistency. These are descriptive dependent comparisons, not independent significance tests or a fitted rule.

{table(volume_summary)}

In the fixed A/1h LONG .003/.003 8h display slice, marginal ambiguity rises from about 8.81% to 37.33% from lowest to highest quantity quartile in development, and from 2.31% to 23.92% in replication. LONG TP_FIRST falls from about 43.04% to 31.87%, and 44.77% to 39.51%, respectively. SHORT TP_FIRST also falls between these endpoints. The within-stratum table above, rather than this marginal example alone, addresses incremental composition information. This can reflect path volatility and barrier-order ambiguity, not direction forecasting. Causation is not established.

No pooled rate, same-sign percentage, or isolated CI is sufficient evidence for tradable predictive utility. Quantile conditioning controls only coarse geometry; causal attribution and exact-state matching are not established.''')
    report('PHASE3R2_A1_DELTA.md','A1 and Delta',f'''Original A1 and A2 are unchanged. Frozen A1/A2 bins come from Phase 3R.1, not current flow availability. Support-side, resistance-side and difference features are separate. Support-heavy/resistance-heavy maps also have map_direction cross-tabs for both LONG and SHORT.

Illustrative predeclared LONG TP=SL=.003, 8h, 1h support Delta (all other grids exported):

{table(illustrative,40)}

{example_note}

Compare the within-A1 increment with its map-only baseline, not only unconditioned flow. Marginal correlation with A1 and within-bucket separation can coexist. Sparse sign-flip or extreme-flow cells cannot establish that Delta changes the original score's meaning. No cutoff or combined score was constructed.''')
    report('PHASE3R2_GEOMETRY_DELTA.md','Geometry and Delta',f'''A2, A3 imbalance and counts, A4 nearest-distance relationship, clusters and candidates-per-cluster all receive identical incremental cross-tabs. B1/B2/C.003/C.005 retain raw geometry; A weights are never copied onto them.

{methods}

Few-cluster/many-candidate versus many-cluster/fewer-candidate states are represented by every observed `cluster_concentration` cell. Code = direction*100 + cluster_bucket*10 + candidates_per_cluster_bucket; direction 0=resistance-heavy, 1=equal, 2=support-heavy. This categorical code is not a strength score.

2023 has a large cluster-distribution shift already documented in 3R.1. Absent frozen strata remain absent. Replication comparisons require the same observed map bucket, rather than relabeling the two periods' low/high groups. Quantity ratios and overlap can make both sides' Delta nearly identical.''')
    age_diag=diagnostic[diagnostic.condition.isin(['age_band','mean_age','mean_prior_crossings','mean_prior_visits','mean_hours_since_last_contact','very_old_over_365d_fraction'])]
    report('PHASE3R2_AGE_CROSSING_DELTA.md','Age, Crossing and Delta',f'''Nearby mean source age is split at 30/180/365 days. Existing recent/medium/old/very-old fractions and causal crossing/visit/contact features are preserved in states; very-old fraction also has a frozen quartile conditioner. Mean age is a map summary, not a claim that every nearby level has the same age.

Crossing, visit and time-since-contact strata use unchanged 3R.1 definitions and development cuts. These features are available for A only; no invented B/C crossing feature. Old levels are not invalidated or decayed.

{table(age_diag,24)}

Residual separation by fresh/stale strata does not demonstrate that flow confirms an individual old level. Quarter and replication changes are retained in quarter-stability.parquet and replication-comparison.parquet.''')
    report('PHASE3R2_CHRONOLOGICAL_STABILITY.md','Chronological Stability',f'''Every major curve and interaction contains ALL and calendar-quarter rows. No random split or quarter-specific retuning. Stability overview counts whether moderate-minus-extreme has the same nonzero sign in all four observed quarters; missing quarters do not count as stable. These dependent comparisons are descriptive, not significance votes.

{table(diag)}

Different windows can include different quarantines/zero-side quantities, so compare eligibility before interpreting apparent window improvements. A pattern confined to one quarter is not promoted.''')
    report('PHASE3R2_2023_REPLICATION.md','2023: previously inspected replication period',f'''Development analysis and feature/bucket definitions were sealed before reading 2023 flow in this phase. Freeze ID: `{seal['freeze_id']}`. Frozen code, models and all development outputs are hashed and checked before replication. No percentile, near-zero boundary, positive-tail cut, map grouping or window is refit.

{table(diag)}

Replication comparison includes missing cells using an outer join and an explicit both_observed flag. Same-sign counts use only comparable cells; absence is not success. Different outcome compositions and base rates can alter apparent shapes. This is not untouched validation and cannot independently confirm an edge.''')
    raw_display=raw[raw.period.eq('ALL')&raw.window.eq(1)&raw.condition.isin(['A1','imbalance'])&raw.direction.eq('LONG')&raw.tp.eq(.003)&raw.sl.eq(.003)&raw.horizon.eq(8)][['phase','feature','condition','map_bucket','complete_raw_q3','complete_raw_q4','raw_q3_minus_raw_q4']]
    report('PHASE3R2_PHASE35_RECONCILIATION.md','Phase 3.5 Reconciliation',f'''Phase 3.5's documented display case had raw-Delta Q3 TP-first about 34.7742% versus 34.3103% A alone in development, and 44.2402% versus 43.7763% in previously inspected 2023. Its raw Q3 boundaries were about -5.97 to 214.415 BTC, not a universally positive normalized-Delta interval. See unchanged docs/research/PHASE35_REVIEW_KO.md.

The old study used single-zone interactions, 2021-2022 development and event-balanced zone measurements; this study uses one full-map state per hour starting January 5, 2022, deduplicated union quantities and frozen whole-development flow partitions. It is not an identical-estimand replication. Do not subtract the reported effects as if they were paired.

Raw support/resistance Delta quartile-conditioned tables are included alongside normalized features. Moderate-positive versus extreme-positive normalized contrasts are a separate transparent shape diagnostic, not the legacy Q3 label.

Full-map raw-Delta Q3 minus Q4 after A1/imbalance conditioning, same fixed display grid. These are NEW development-frozen full-map quartiles, not the legacy numeric cut. All windows/grids/quarters including cluster conditioning are in `raw-quartile-reconciliation.parquet`.

{table(raw_display,32)}

Normalized positive-tail comparison, separately:

{table(illustrative,40)}

Some residual within-stratum differences can remain after coarse A1/imbalance conditioning. That alone cannot prove the old Q3 was a geometry proxy or prove the old effect survives unchanged. Conditioning one feature at a time leaves joint-map/regime confounding. The old nonlinear observation remains component research, neither rewritten nor invalidated.''')
    report('PHASE3R2_D_STATUS.md','D Status','D remains observed-only. Phase 3R.1 established zero complete-coverage 850-day D windows before 2024. No D predictive competitor, rerun, zero-fill, interpolation, or candle-volume replacement is introduced. Local A/B/C flow can be coverage-valid despite a quarantined minute elsewhere in the 850-day D lookback.')
    def evidence(condition):
        row=diagnostic[(diagnostic.condition==condition)&(diagnostic.feature==DELTA[0])].iloc[0]
        quarter=(f'{int(row.consistent_four_quarters)}/{int(row.four_quarter_cells)} observed cells keep one sign in all four development quarters'
            if row.four_quarter_cells else 'no unchanged stratum is observed in all four development quarters, so four-quarter stability cannot be assessed')
        return (f"For support normalized Delta moderate-minus-extreme, {quarter}; {int(row.same_sign_pairs)}/{int(row.observed_pairs)} "
            'comparable development/2023 cells retain the pooled sign (all grids/windows; dependent comparisons).')
    def volume_evidence(condition):
        r=volume_summary[volume_summary.condition.eq(condition)].iloc[0]
        return f"Quantity carries descriptive outcome-composition information: {int(r.higher_ambiguity_both)}/{int(r.observed_pairs)} matched cells have higher ambiguity in the high-volume quartile in both periods. This is not directional edge."
    pooled=shapes[shapes.period.eq('ALL')]
    nonmono=int((~(pooled.nondecreasing|pooled.nonincreasing)).sum())
    valid_pair=overall[overall.comparable]
    better=int(valid_pair.moderate_minus_extreme.gt(0).sum())
    sidecorr=coverage.support_resistance_delta_spearman
    questions=f'''1. Beyond A1: {volume_evidence('A1')} Stable additional directional Delta information is not established. {evidence('A1')} This is not proof of zero Delta information.
2. Beyond imbalance: {volume_evidence('imbalance')} Delta separation is not a consistently established extra directional signal. {evidence('imbalance')} Coarse conditioning still leaves residual map/regime confounding.
3. Beyond clusters: {volume_evidence('clusters')} Delta evidence is limited by sparse cells and the large cluster-distribution shift. {evidence('clusters')} Missing strata cannot be called replication.
4. Shape: {nonmono}/{len(pooled)} pooled decile curves are nonmonotonic. This is not a universal monotonic rule, nor proof of a population inverted-U/U shape or threshold.
5. Moderate versus extreme: not universally. Moderate positive exceeds extreme positive in {better}/{len(valid_pair)} observed pooled conditional/marginal cells across both phases; these dependent cells are not independent votes or a significance test.
6. Support versus resistance: their observed curves can differ, but they are strongly coupled by overlapping intervals. Across phase/map/window tables their normalized-Delta Spearman correlation ranges {sidecorr.min():.4f} to {sidecorr.max():.4f}. They cannot be treated as independent confirmations; difference-feature tables test residual contrast separately.
7. Quarter stability: Delta separation is not generally stable across all quarters; the condition-specific counts above show sign changes and sparse tails. Quantity/ambiguity has a separate four-quarter stability table in the incremental-value report. Missing common strata cannot establish stability. No favorable quarter is promoted.
8. Replication: the exact frozen analysis runs successfully. Quantity's composition association and Delta's partial shape agreement must be separated; neither is untouched validation or tradable edge. Implementation reproducibility alone is not predictive reproducibility.
9. Phase 3.5 survival: not established as the same robust effect. Residual contrasts do not resolve whether the legacy Q3 association was a geometry proxy; estimand, timestamps, weighting and Delta partitions differ. Component research is preserved rather than invalidated.
10. Later experiments: retain quantity as a descriptive path/ambiguity covariate and Delta as exploratory if later experiments are authorized, not as a confirmed directional signal or selected window. Current evidence does not justify freezing an entry rule; other timeframes are not started.'''
    report('PHASE3R2_COMPLETION.md','Phase 3R.2 Completion',f'''Completed five map configurations x three parallel flow windows across 17,407 unchanged events: 261,105 flow-state rows. Existing 417,768 distinct event/grid outcome rows are reused, not regenerated. Reports: eleven PHASE3R2 Markdown files, compact Parquet/CSV summaries and {len(plotnames)} SVG diagnostics.

Verification PASS: {verification['tests']['tests']} tests, {verification['tests']['failures']} failures, {verification['tests']['errors']} errors, {verification['tests']['skipped']} skipped. All {verification['one_hour_parity_rows']} existing 1h map-flow rows matched (quantity rtol=1e-10, atol=1e-8); original price-map state columns are unchanged. {verification['prior_artifacts_unchanged']} prior artifacts remain byte-identical. All 30 flow/state tables passed time-window, quantity, shared-volume, geometry-preservation and outcome-identity audits. Existing Starlette/httpx deprecation warning remains unrelated to this research.

{questions}

{table(diag,18)}

{table(mono)}

See verification.json and test-results.xml for final audit/tests. New implementation: backend/app/fullmap_flow; tests: backend/tests/test_phase3r2.py. Prior Phase 3R.1 report/data/code hashes are preserved. No old artifact is rewritten. Stop before other timeframes, confluence, 2024, rule selection or live execution.''')
    write_json(dest/'complete.json',dict(status='COMPLETE',reports=11,plots=len(plotnames),contrast_rows=len(pair),freeze_id=seal['freeze_id']))
    print('REPORTS_COMPLETE',11,len(plotnames),flush=True)

if __name__=='__main__':main()
