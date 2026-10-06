"""Complete-grid evidence exports and offline SVG diagnostics; no winning rule."""
from html import escape
from itertools import product
import numpy as np
import pandas as pd
from .contract import *

FOOTER = '\n2023 is the **previously inspected replication period**, not a pristine test. No 2024 data, live rule, leverage, raw-score sum, threshold selection or winning timeframe selection. All comparisons are descriptive and dependent; bootstrap intervals are not adjusted for multiplicity.\n'


def markdown(frame):
    if frame.empty:
        return 'No supported cells. Missing is not zero.\n'
    lines = ['| '+' | '.join(map(str,frame.columns))+' |', '| '+' | '.join(['---']*len(frame.columns))+' |']
    for row in frame.itertuples(index=False,name=None):
        lines.append('| '+' | '.join('NA' if pd.isna(v) else f'{v:.5g}' if isinstance(v,float) else str(v) for v in row)+' |')
    return '\n'.join(lines)+'\n'


def document(name, body):
    if not name.startswith('PHASE5_') or not name.endswith('.md'):
        raise ValueError('Only new Phase 5 reports may be written')
    (PROJECT/name).write_text(body+FOOTER, encoding='utf-8')


def contract_report():
    body = '# Phase 5 Confluence Contract\n\n'
    for key, value in PLAN.items():
        body += f'## {key}\n\n{value}\n\n'
    body += '''## Mathematical Spatial Definition

For type k and timeframe f, let C(f,k,t_f) be the frozen nearby candidate set at native closed time t_f <= T.
For candidate price p, J(f,p) = [p(1-w_f), p(1+w_f)].
U(f,k) is the union of these closed intervals, without double-counting same-timeframe overlaps.
For each nonempty subset S of timeframes, I(S,k) = intersection over f in S of U(f,k).
Every connected component [L,H] of I is retained, including L=H contact.
Width = H-L; price distance = max(L-P(T), 0, P(T)-H).
The raw participant count is the number of distinct candidate intervals intersecting that component, summed across contributing timeframes. Duplicate-price candidates remain distinct native candidates.

No global candidate Cartesian product is constructed. A four-way intersection must exist at a common price; pairwise intersections at different prices cannot manufacture a four-way region.
Native intervals are selected at their source close and carried with the native STATE. They are not reselected or rescored at the 15m price. Common-price distance exposes when carried regions have moved away from current price.
State tables include source snapshot/interval references; native tables contain every [lower,upper,candidate_index] and frozen source-catalog hashes. The common table preserves native unions and source ages. The overlap table preserves every combination/component, not only the largest one.

## Interpretation and Dependence

Primary support-heavy is positive raw nearby imbalance; resistance-heavy is negative; balanced is exact zero with at least one nearby candidate. Empty neighborhoods are missing. A1 and A2 signs are separate sensitivity families, not combined votes.
An inclusive singleton allows other aligned timeframes; exclusive 'only' requires exactly that participating set. Counts include conflicts unless explicitly marked unopposed. Exact S/R/N/M patterns follow 15m,1h,4h,1d order.
An incremental contrast fixes the base-aligned cohort and compares added-TF agreement against nonagreement, neutral or conflict. Shared weekly resampling preserves temporal dependence and overlap between nested masks. There is no individual-counterfactual causal claim.
Pooled bootstrap intervals cover every declared grid and six metrics. Quarterly effects, support and sign consistency are separate; no independent-row p-values. Block duration sensitivity and multiplicity-adjusted confirmatory inference remain limitations.
'''
    document('PHASE5_CONFLUENCE_CONTRACT.md', body)


def shape(group):
    if len(group)!=4 or not group.supported.all():
        return 'SPARSE'
    v = group.sort_values('count').TP_FIRST.to_numpy()
    d = np.diff(v)
    if np.all(d==0): return 'FLAT'
    if np.all(d>=0): return 'MONOTONIC_INCREASING'
    if np.all(d<=0): return 'MONOTONIC_DECREASING'
    return 'NONLINEAR'


def summarize_evidence(contrasts):
    keys = ['comparison','family','direction','tp','sl','horizon','metric']
    dev = contrasts[contrasts.phase=='development']
    rep = contrasts[contrasts.phase=='replication']
    rows = []
    pooled = dev[dev.period=='ALL'].merge(rep[rep.period=='ALL'], on=keys, suffixes=('_dev','_rep'), validate='one_to_one')
    for record in pooled.to_dict('records'):
        # Boolean lookup in a pre-indexed table avoids scanning the full table per row.
        rows.append(record)
    if not rows:
        return pd.DataFrame()
    result = pd.DataFrame(rows)
    for phase, f in [('dev',dev),('rep',rep)]:
        q = f[f.period!='ALL'].copy()
        q['positive'] = q.effect.gt(0)&q.supported
        q['negative'] = q.effect.lt(0)&q.supported
        q['absolute_effect'] = q.effect.abs()
        stats = q.groupby(keys, dropna=False).agg(quarters=('period','nunique'), supported_quarters=('supported','sum'),
            positive_quarters=('positive','sum'), negative_quarters=('negative','sum'),
            min_quarter_effect=('effect','min'), max_quarter_effect=('effect','max'),
            sum_abs_quarter_effect=('absolute_effect','sum'), max_abs_quarter_effect=('absolute_effect','max')).reset_index()
        stats['largest_abs_quarter_share'] = stats.max_abs_quarter_effect/stats.sum_abs_quarter_effect.replace(0,np.nan)
        stats = stats.rename(columns={k:k+'_'+phase for k in stats if k not in keys})
        result = result.merge(stats,on=keys,validate='one_to_one')
    result['same_nonzero_sign_all_dev_quarters_and_rep'] = result.supported_dev & result.supported_rep & (
        ((result.positive_quarters_dev==4)&(result.effect_dev>0)&(result.effect_rep>0)) |
        ((result.negative_quarters_dev==4)&(result.effect_dev<0)&(result.effect_rep<0)))
    result['same_nonzero_sign_all_eight_quarters'] = result.same_nonzero_sign_all_dev_quarters_and_rep & (
        ((result.positive_quarters_dev==4)&(result.positive_quarters_rep==4)) |
        ((result.negative_quarters_dev==4)&(result.negative_quarters_rep==4)))
    return result


def plot_svg(title, lines, labels):
    colors = ['#146c94','#c45b32','#347c55','#85603f','#535a91','#8d4267','#557b79','#845c4a']
    width, height = 940, 370
    finite = [v for _, values in lines for v in values if np.isfinite(v)]
    low = min(finite+[0]); high = max(finite+[.05]); span=max(high-low,.01)
    low-=span*.07; high+=span*.07
    x = lambda i: 65+i*630/max(len(labels)-1,1)
    y = lambda v: 300-(v-low)*245/(high-low)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
           '<rect width="940" height="370" fill="#faf7ef"/>',f'<text x="20" y="25" font-size="16">{escape(title)}</text>']
    for v in np.linspace(low,high,5):
        parts.append(f'<path d="M65 {y(v):.2f} H695" stroke="#ddd8cc"/><text x="8" y="{y(v):.2f}" font-size="11">{v:.3f}</text>')
    for j,(name,values) in enumerate(lines):
        color=colors[j%len(colors)]; prior=None
        for i,v in enumerate(values):
            if not np.isfinite(v): prior=None; continue
            if prior is not None:
                parts.append(f'<path d="M{x(prior[0]):.2f} {y(prior[1]):.2f} L{x(i):.2f} {y(v):.2f}" stroke="{color}" fill="none"/>')
            parts.append(f'<circle cx="{x(i):.2f}" cy="{y(v):.2f}" r="3" fill="{color}"/>'); prior=(i,v)
        parts.append(f'<text x="712" y="{55+j*20}" fill="{color}" font-size="11">{escape(name)}</text>')
    for i,label in enumerate(labels):
        parts.append(f'<text x="{x(i):.2f}" y="320" text-anchor="middle" font-size="10">{escape(str(label))}</text>')
    return ''.join(parts)+'</svg>'


def conflict_matrix_svg(title, frame):
    labels=['SS','SR','RS','RR','NN']
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 780 530" role="img">',
           '<rect width="780" height="530" fill="#faf7ef"/>',f'<text x="16" y="25" font-size="16">{escape(title)}</text>',
           '<text x="220" y="55">Higher: 4h / 1d</text><text x="8" y="85">Lower: 15m / 1h</text>']
    for j,upper in enumerate(labels):parts.append(f'<text x="{210+j*105}" y="90">{upper}</text>')
    for i,lower in enumerate(labels):
        parts.append(f'<text x="110" y="{140+i*80}">{lower}</text>')
        for j,upper in enumerate(labels):
            k=f'conflict/{lower}/{upper}'
            r=frame.loc[k];rate=r.TP_FIRST
            fill='#dfddd6' if not np.isfinite(rate) else f'rgb({int(240-130*rate)},{int(242-70*rate)},{int(237-30*rate)})'
            x,y=170+j*105,105+i*80
            value='NA' if not np.isfinite(rate) else f'{rate:.3f}'
            parts.append(f'<rect x="{x}" y="{y}" width="101" height="76" fill="{fill}" stroke="#fff"/><text x="{x+8}" y="{y+27}" font-size="16">{value}</text><text x="{x+8}" y="{y+48}" font-size="11">n={int(r.complete)}</text><text x="{x+8}" y="{y+65}" font-size="10">{"supported" if r.supported else "sparse"}</text>')
    return ''.join(parts)+'</svg>'


def plots(summary, contrasts, output):
    plots_dir=output/'plots';plots_dir.mkdir(exist_ok=True)
    links=[]
    combos=['15m','1h','4h','1d','15m+1h','1h+4h','4h+1d','15m+1h+4h','1h+4h+1d','15m+1h+4h+1d']
    for direction in ['LONG','SHORT']:
        side='support' if direction=='LONG' else 'resistance'
        for tp,sl,horizon in product([.003,.005],[.003,.005],[16,32,96]):
            f=summary[(summary.direction==direction)&(summary.tp==tp)&(summary.sl==sl)&(summary.horizon==horizon)]
            c=contrasts[(contrasts.direction==direction)&(contrasts.tp==tp)&(contrasts.sl==sl)&(contrasts.horizon==horizon)]
            for phase in ['development','replication']:
                sub=f[(f.phase==phase)&(f.period=='ALL')].set_index('category')
                stem=f'conflict-matrix-{phase}-{direction}-{tp}-{sl}-{horizon}'
                title=f'Conflict matrix: {phase}, {direction}, TP={tp}, SL={sl}, {horizon/4:g}h'
                (plots_dir/(stem+'.svg')).write_text(conflict_matrix_svg(title,sub),encoding='utf-8');links.append((stem,title))
            specs=[('agreement', [f'imbalance/{side}/count/{k}' for k in range(1,5)],list('1234'),'TP_FIRST'),
                ('unopposed', [f'imbalance/{side}/unopposed/{k}' for k in range(1,5)],list('1234'),'TP_FIRST'),
                ('combination',[f'imbalance/{side}/aligned/{s}' for s in combos],[s.replace('15m','15').replace('1h','1').replace('4h','4').replace('1d','D') for s in combos],'TP_FIRST'),
                ('zone',[f'zone/{side}/count/{k}' for k in range(5)],list('01234'),'TP_FIRST'),
                ('sign-space',[f'joint/{side}/sign{k}/zone{z}' for k in [1,2,3,4] for z in [0,1,2,3,4]],[f'{k}/{z}' for k in [1,2,3,4] for z in range(5)],'TP_FIRST'),
                ('conflict',[f'conflict/{p[:2]}/{p[2:]}' for p in ['SSSS','SSRR','RRSS','RRRR','SSNN','NNSS','RRNN','NNRR']],['SSSS','SSRR','RRSS','RRRR','SSNN','NNSS','RRNN','NNRR'],'TP_FIRST'),
                ('quantity',[f'quantity/{side}/count{k}/Q{q}' for k in [1,2,3,4] for q in range(4)],[f'{k}/Q{q+1}' for k in [1,2,3,4] for q in range(4)],'AMBIGUOUS')]
            for name,categories,labels,metric in specs:
                lines=[]
                for phase in ['development','replication']:
                    sub=f[(f.phase==phase)&(f.period=='ALL')].set_index('category')
                    lines.append((phase,[float(sub.loc[k,metric]) if k in sub.index else np.nan for k in categories]))
                stem=f'{name}-{direction}-{tp}-{sl}-{horizon}'
                title=f'{name}: {direction}, TP={tp}, SL={sl}, {horizon/4:g}h, {metric}'
                (plots_dir/(stem+'.svg')).write_text(plot_svg(title,lines,labels),encoding='utf-8');links.append((stem,title))
            category=f'imbalance/{side}/count/4';lines=[]
            for phase in ['development','replication']:
                sub=f[(f.phase==phase)&(f.category==category)].set_index('period')
                lines.append((phase,[sub.loc[str(q),'TP_FIRST'] for q in range(1,5)]))
            stem=f'quarters-{direction}-{tp}-{sl}-{horizon}'
            title=f'4TF quarterly TP_FIRST: {direction}, TP={tp}, SL={sl}, {horizon/4:g}h'
            (plots_dir/(stem+'.svg')).write_text(plot_svg(title,lines,['Q1','Q2','Q3','Q4']),encoding='utf-8');links.append((stem,title))
            lines=[]
            comp=f'incremental/{side}/15m+1h+4h/add_1d/agrees_vs_not_agrees'
            for phase in ['development','replication']:
                sub=c[(c.phase==phase)&(c.comparison==comp)&(c.metric=='TP_FIRST')].set_index('period')
                lines.append((phase,[sub.loc[p,'effect'] for p in ['ALL','1','2','3','4']]))
            stem=f'fourth-increment-{direction}-{tp}-{sl}-{horizon}';title=f'Added 1d agree minus nonagree: {direction}, TP={tp}, SL={sl}, {horizon/4:g}h'
            (plots_dir/(stem+'.svg')).write_text(plot_svg(title,lines,['ALL','Q1','Q2','Q3','Q4']),encoding='utf-8');links.append((stem,title))
    page='<!doctype html><meta charset="utf-8"><title>Phase 5 diagnostics</title><style>body{background:#e8e3d7;color:#203744;font:16px Georgia;margin:3vw}img{width:100%;max-width:1100px}details{margin:12px 0}summary{cursor:pointer}</style><h1>Phase 5 | Every declared grid</h1><p>Descriptive rates, not trading rules. Raw supported and sparse cells shown; consult CSV for sample sizes, censoring and intervals. Missing points are gaps, never zero. 2023 previously inspected replication. No 2024.</p>'
    page+=''.join(f'<details><summary>{escape(title)}</summary><img loading="lazy" src="plots/{stem}.svg" alt="{escape(title)}"></details>' for stem,title in links)
    (output/'diagnostics.html').write_text(page,encoding='utf-8')
    return len(links)


def evidence_text(stable, family, metric='TP_FIRST'):
    f=stable[(stable.family==family)&(stable.metric==metric)]
    f=f[((f.direction=='LONG')&f.comparison.str.contains('/support/'))|((f.direction=='SHORT')&f.comparison.str.contains('/resistance/'))] if family!='conflict' else f
    supported=f[f.supported_dev & f.supported_rep]
    if supported.empty:
        return f'{family}: no contrast/grid has the predeclared sample support in both periods. No incremental-information conclusion is available.\n'
    flips=int(((np.sign(supported.effect_dev)!=np.sign(supported.effect_rep))&supported.effect_dev.ne(0)&supported.effect_rep.ne(0)).sum())
    stable_count=int(supported.same_nonzero_sign_all_eight_quarters.sum())
    return (f'{family} / {metric}: {len(supported)} supported comparison/grid cells in both periods; '
            f'{flips} reverse pooled sign between development and replication; {stable_count} retain one nonzero sign across all eight supported quarters. '
            f'Development effect range [{supported.effect_dev.min():.6g}, {supported.effect_dev.max():.6g}], '
            f'replication [{supported.effect_rep.min():.6g}, {supported.effect_rep.max():.6g}]. '
            'These are dependent descriptive cells, not a selected strategy or independent discoveries.\n')


def generate():
    check_freeze()
    output=ROOT/'reports';output.mkdir(exist_ok=True)
    frames=[];effects=[];coverage=[]
    for phase in ['development','replication']:
        s=pd.read_parquet(ROOT/phase/'analysis/cohorts.parquet');s['phase']=phase;frames.append(s)
        c=pd.read_parquet(ROOT/phase/'analysis/contrasts.parquet');c['phase']=phase;effects.append(c)
        coverage.append(dict(phase=phase,**{k:read(ROOT/phase/'build-complete.json')[k] for k in ['timestamps','first','last','alignment_checks']}))
    summary=pd.concat(frames,ignore_index=True);contrasts=pd.concat(effects,ignore_index=True)
    spatial_prevalence=[]
    for phase in ['development','replication']:
        data=pd.concat([pd.read_parquet(p,columns=['support_overlap_count','resistance_overlap_count'])
                        for p in sorted((ROOT/phase/'states').glob('*.parquet'))],ignore_index=True)
        for (support,resistance),n in data.groupby(['support_overlap_count','resistance_overlap_count']).size().items():
            spatial_prevalence.append(dict(phase=phase,support_overlap_count=support,resistance_overlap_count=resistance,
                                           timestamps=int(n),fraction=n/len(data)))
    prevalence=pd.DataFrame(spatial_prevalence)
    prevalence.to_csv(output/'spatial-prevalence.csv',index=False)
    stable=summarize_evidence(contrasts)
    for name,f in [('chronological-stability',stable),('coverage',pd.DataFrame(coverage))]:
        f.to_parquet(output/(name+'.parquet'),index=False);f.to_csv(output/(name+'.csv'),index=False)
    shapes=[]
    for phase in ['development','replication']:
        for side,direction in [('support','LONG'),('resistance','SHORT')]:
            f=summary[(summary.phase==phase)&(summary.direction==direction)&summary.category.str.startswith(f'imbalance/{side}/count/')].copy()
            f['count']=f.category.str.rsplit('/',n=1).str[-1].astype(int);f=f[f['count']>0]
            for keys,g in f.groupby(['period','direction','tp','sl','horizon']):
                shapes.append(dict(phase=phase,**dict(zip(['period','direction','tp','sl','horizon'],keys)),shape=shape(g)))
    shapes=pd.DataFrame(shapes);shapes.to_csv(output/'alignment-shapes.csv',index=False)
    stable['supported_both']=stable.supported_dev & stable.supported_rep
    stability_counts=stable.groupby(['family','direction','metric']).agg(comparisons=('comparison','size'),supported_both=('supported_both','sum'),
        same_sign_dev_quarters_rep=('same_nonzero_sign_all_dev_quarters_and_rep','sum'),same_sign_eight_quarters=('same_nonzero_sign_all_eight_quarters','sum')).reset_index()
    stability_counts.to_csv(output/'stability-counts.csv',index=False)
    count_table=summary[(summary.period=='ALL')&(summary.family=='sign_count')&summary.category.str.startswith('imbalance/')].groupby(['phase','category','interpretation']).agg(min_complete=('complete','min'),max_complete=('complete','max'),min_blocks=('week_blocks','min')).reset_index()
    count_table.to_csv(output/'sign-sample-counts.csv',index=False)
    sample_combo=summary[(summary.period=='ALL')&summary.family.isin(['hierarchy_inclusive','hierarchy_exclusive','zone_combination'])&~summary.category.str.startswith(('A1/','A2/'))].groupby(['phase','category']).agg(min_complete=('complete','min'),max_complete=('complete','max'),min_blocks=('week_blocks','min')).reset_index()
    sample_combo.to_csv(output/'combination-sample-counts.csv',index=False)
    def counts(family):
        return markdown(stability_counts[(stability_counts.family==family)&(stability_counts.metric.isin(['TP_FIRST','AMBIGUOUS']))])
    for name,family,title,extra in [
        ('SIGN_CONFLUENCE','sign_baseline','Sign Confluence',markdown(shapes.groupby(['phase','direction','period','shape']).size().reset_index(name='grid_cells'))+'\n'+markdown(count_table)),
        ('ZONE_OVERLAP','spatial_increment','Price-Space Confluence','Native intervals and every nonempty TF-subset component are under development/overlaps and replication/overlaps. No relaxed overlap rule. Dense nearby maps can yield simultaneous support AND resistance intersections: overlap alone is not directional confirmation.\n'+markdown(prevalence)+'\n'+counts('spatial_exact')),
        ('CONFLICT_STATES','conflict','Lower/Higher Conflict','All 256 exact S/R/N/M patterns retained. SSRR and RRSS are explicit contrasts; no higher-TF dominance is assumed.\n'),
        ('INCREMENTAL_TIMEFRAME_VALUE','incremental','Incremental Timeframe Value','Each contrast conditions on the same base-aligned cohort. Agreement and neutral/conflicting complements are disjoint, not independent nested observations. See all metrics and grids in contrasts.parquet.\n'),
        ('QUANTITY_INTERACTION','quantity','Quantity Interaction','Existing 15m one-candle zone-union quantity is not total-market volume. Development quartiles are unchanged in replication. Delta tables and per-timeframe magnitude sensitivity remain secondary and are not direction definitions.\n'),
        ('CHRONOLOGICAL_STABILITY','nested_baseline','Chronological Stability','Every quarter is retained. largest_abs_quarter_share reports effect-magnitude concentration, not causal attribution. Opposite quarterly signs must not be hidden by pooled averages.\n'),
        ('2023_REPLICATION','hierarchy_baseline','Frozen 2023 Replication','Definition/code/output-grid hashes were sealed only after development analysis and tests. No 2023 refitting or category merging. Missing and sparse cells remain explicit.\n')]:
        document('PHASE5_'+name+'.md','# '+title+'\n\n'+extra+'\n'+evidence_text(stable,family)+'\n'+evidence_text(stable,family,'AMBIGUOUS')+'\n## Supported Directional Stability\n'+counts(family)+'\nFull exact denominators, all four labels, censoring, MFE/MAE and pooled shared-block intervals: `data/phase5/<period>/analysis/`. These counts span multiple dependent grids; they are not independent successful discoveries.\n')
    alignment=pd.concat([pd.read_csv(ROOT/p/'alignment-audit.csv').assign(phase=p) for p in ['development','replication']],ignore_index=True)
    alignment.to_csv(output/'alignment-audit.csv',index=False)
    document('PHASE5_ALIGNMENT_AUDIT.md','# Alignment Audit\n\n'+markdown(alignment.groupby(['phase','timeframe']).agg(checks=('T','size'),maximum_age_ms=('age_ms','max'),truncation_pass=('truncation_equal','all')).reset_index())+'\nSamples are deterministic: evenly spaced timestamps plus before/at/after hourly, four-hourly and daily closes. Full sequence changes were checked to occur only on native closes. Source arrays were physically truncated at each sampled T. Existing 15m outcomes were reused with exact event/timestamp and complete-grid equality checks; no higher-timeframe labels were used.\n')
    nplots=plots(summary,contrasts,output)
    inc=stable[(stable.family=='incremental')&(stable.metric=='TP_FIRST')].copy()
    inc=inc[((inc.direction=='LONG')&inc.comparison.str.contains('/support/'))|((inc.direction=='SHORT')&inc.comparison.str.contains('/resistance/'))]
    inc=inc[inc.comparison.str.endswith('agrees_vs_not_agrees')]
    inc['addition']=inc.comparison.str.extract(r'/add_([^/]+)/')[0]
    inc_summary=inc.groupby(['addition','direction']).agg(grids=('comparison','size'),stable_all_eight=('same_nonzero_sign_all_eight_quarters','sum'),dev_effect_min=('effect_dev','min'),dev_effect_max=('effect_dev','max'),rep_effect_min=('effect_rep','min'),rep_effect_max=('effect_rep','max')).reset_index()
    inc_summary.to_csv(output/'incremental-summary.csv',index=False)
    monotonic=shapes[shapes.period=='ALL'].groupby(['phase','direction','shape']).size().reset_index(name='grids')
    tests=read(ROOT/'final-tests.json');pres=read(ROOT/'preservation-audit.json')
    if tests['returncode'] or pres['status']!='PASS':raise ValueError('Completion gates failed')
    body='# Phase 5 Completion\n\n'+markdown(pd.DataFrame(coverage))+f'\nTests: {tests["tests"]}; failures {tests["failures"]}; errors {tests["errors"]}. Preservation audit: {pres["files"]} unique artifacts unchanged. {nplots} SVG panels cover all 24 outcome grids.\n\n'
    body+='## Completion Questions\n\n'
    body+='1. Greater agreement: observed 1/2/3/4 shapes are below. No monotonic improvement is assumed or inferred from pooled TP_FIRST alone.\n'+markdown(monotonic)
    body+='2. Four versus two/three: consult same-period nested-baseline contrasts and exact samples. This phase does not establish that four is uniformly better; supported quarterly and replication behavior are required, not one grid.\n'
    body+=evidence_text(stable,'nested_baseline')
    body+='3. Spatial overlap beyond sign: both agreement-count-conditioned and exact-sign-pattern-conditioned contrasts are exported. Undefined or sparse contrasts cannot establish incremental information.\n'+counts('spatial_exact')
    body+=evidence_text(stable,'spatial_exact')
    body+='4. Sample support: `reports/combination-sample-counts.csv` lists exact minimum/maximum complete samples and occupied blocks for every inclusive, exclusive and spatial combination. Support was predeclared as >=200 complete timestamps and >=5 weekly blocks; no category was merged.\n'
    body+='5. Adding 1d, 6. Adding 4h, 7. Adding 1h: the following summarizes all predeclared base-cohort additions, without ranking. Stable counts require the same nonzero sign in all eight supported quarters. Positive and negative effects both count as structure, not a benefit.\n'+markdown(inc_summary)
    body+='8. Higher/lower conflicts: SSRR/RRSS and conflicts versus fully aligned states retain all outcome labels. No dominance rule is selected.\n'+counts('conflict')
    body+=evidence_text(stable,'conflict')
    body+='9. Quantity and risk: conditional high-minus-low quantity contrasts retain ambiguity, neither, directional labels and excursions. Quantity remains outside direction.\n'+counts('quantity')
    body+=evidence_text(stable,'quantity','AMBIGUOUS')
    body+='10. Quarterly stability, 11. Frozen replication: complete comparisons and sign reversals are in chronological-stability.csv. Sparse quarters are not treated as stable evidence, and pooled consistency is not equivalent to all-quarter consistency.\n'
    body+='12. ONE candidate strategy for untouched testing: **not established by this descriptive phase**. Unresolved requirements are selecting a single hypothesis without grid/multiple-comparison bias, demonstrating incremental directional separation rather than activity-driven path changes, handling state persistence and overlapping events, and specifying costs/execution separately. No candidate was promoted based on a strongest cell, no leverage was chosen and no 2024 data was accessed.\n\nSTOP. See `data/phase5/reports/diagnostics.html` for offline diagnostics and analysis CSV/Parquet for the full evidence.\n'
    document('PHASE5_COMPLETION.md',body)
    write(ROOT/'completion.json',dict(status='COMPLETE',no_2024=True,no_live_rule=True,plots=nplots,
        reports={p.name:digest(p) for p in PROJECT.glob('PHASE5_*.md') if p.name!='PHASE5_PROGRESS.md'}))
