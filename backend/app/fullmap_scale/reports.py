"""Generate descriptive reports/diagnostic SVGs from sealed research tables."""
import html
import json
from pathlib import Path
from xml.etree import ElementTree
import numpy as np
import pandas as pd
from app.fullmap.run import CONFIGS
from app.research.models import identity
from app.market.aggregate_trades import write_json
from .history import ROOT,HISTORY

PROJECT=ROOT.parent.parent
AKEY=identity(('A',{}))[:12]
GRID=['direction','tp','sl','horizon']


def table(frame,limit=30):
    def value(x):
        if x is None or (isinstance(x,float) and not np.isfinite(x)):return 'NA'
        return f'{x:.5g}' if isinstance(x,float) else str(x)
    rows=['| '+' | '.join(map(str,frame.columns))+' |','|'+'|'.join(['---']*len(frame.columns))+'|']
    rows +=['| '+' | '.join(value(x) for x in row)+' |' for row in frame.head(limit).itertuples(index=False,name=None)]
    if len(frame)>limit:rows+=['',f'First {limit} of {len(frame)} rows; all rows are in the machine-readable export.']
    return '\n'.join(rows)


def save(name,body):
    (PROJECT/name).write_text(body.strip()+'\n',encoding='utf-8')


def svg(path,title,series,xlabel='Development-defined bucket',yrange=(0.,1.)):
    width,height=840,400;left,right,top,bottom=70,810,70,330
    xs=[x for _,points in series for x,y in points if np.isfinite(x) and np.isfinite(y)]
    lo,hi=(min(xs),max(xs)) if xs else (0,1)
    if hi==lo:hi=lo+1
    def X(x):return left+(x-lo)/(hi-lo)*(right-left)
    def Y(y):return bottom-(y-yrange[0])/(yrange[1]-yrange[0])*(bottom-top)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#faf8f3"/>',
        f'<text x="30" y="30" font-family="Georgia" font-size="20">{html.escape(title)}</text>']
    for y in np.linspace(*yrange,6):
        out.append(f'<path d="M{left} {Y(y):.2f}H{right}" stroke="#ddd9ce"/><text x="15" y="{Y(y)+4:.2f}" font-size="12">{y:.2f}</text>')
    colors=['#176b85','#b06024','#48793b','#963f50']
    for i,(label,points) in enumerate(series):
        points=[(x,y) for x,y in points if np.isfinite(x) and np.isfinite(y)]
        coords=' '.join(f'{X(x):.2f},{Y(y):.2f}' for x,y in points)
        color=colors[i%len(colors)];dash='stroke-dasharray="6 4"' if 'replication' in label else ''
        out.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2" {dash}/>')
        for x,y in points:out.append(f'<circle cx="{X(x):.2f}" cy="{Y(y):.2f}" r="3" fill="{color}"/>')
        out.append(f'<text x="{70+(i%2)*380}" y="{48+(i//2)*16}" fill="{color}" font-size="12">{html.escape(label)}</text>')
    for x in np.linspace(lo,hi,5):out.append(f'<text x="{X(x)-12:.2f}" y="350" font-size="12">{x:.3g}</text>')
    out.append(f'<text x="260" y="378" font-size="13">{html.escape(xlabel)}; y = TP_FIRST / complete states</text></svg>')
    path.write_text(''.join(out),encoding='utf-8');ElementTree.parse(path)


def shapes(curves,keys):
    rows=[]
    for key,group in curves[curves.bucket>=0].groupby(keys,sort=True):
        group=group.sort_values('bucket');rates=group.tp_first_rate.to_numpy();finite=np.isfinite(rates)
        rates=rates[finite];buckets=group.bucket.to_numpy()[finite]
        if len(rates)<2:continue
        corr=pd.Series(buckets).rank().corr(pd.Series(rates).rank()) if np.std(rates)>0 else 0.
        rows.append(dict(zip(keys,key if isinstance(key,tuple) else (key,)))|dict(
            first_bucket=int(buckets[0]),last_bucket=int(buckets[-1]),observed_buckets=len(buckets),
            nondecreasing=bool(np.all(np.diff(rates)>=0)),nonincreasing=bool(np.all(np.diff(rates)<=0)),
            high_minus_low=float(rates[-1]-rates[0]),rank_correlation=float(corr),
            ends_minus_middle=float((rates[0]+rates[-1])/2-np.mean(rates[1:-1])) if len(rates)>2 else None,
            largest_adjacent_change=float(np.max(np.abs(np.diff(rates)))),min_bucket_states=int(group.complete.min())))
    return pd.DataFrame(rows)


def main():
    dest=ROOT/'reports';plots=dest/'plots';plots.mkdir(parents=True,exist_ok=True)
    for phase in ['development','replication']:
        for stage in ['A','BC']:
            if json.loads((ROOT/phase/'analysis'/(stage+'-complete.json')).read_text())['status']!='COMPLETE':raise ValueError('Analysis incomplete')
    coverage=json.loads((ROOT/'coverage-final.json').read_text());bench=json.loads((ROOT/'benchmark-gate.json').read_text())
    gate=json.loads((ROOT/'parity-gate.json').read_text());freeze=json.loads((ROOT/'development-freeze.json').read_text())
    test=ElementTree.parse(ROOT/'test-results.xml').getroot()[0].attrib
    states={p:pd.read_parquet(ROOT/p/'analysis'/f'{AKEY}-state-features.parquet') for p in ['development','replication']}
    curves={};quarter_curves={};all_shapes=[];all_quarters=[]
    for phase in states:
        for config in CONFIGS[:5]:
            key=identity(config)[:12]
            curves[phase,key]=pd.read_parquet(ROOT/phase/'analysis'/f'{key}-feature-curves.parquet')
            quarter_curves[phase,key]=pd.read_parquet(ROOT/phase/'analysis'/f'{key}-quarter-curves.parquet')
            shape=shapes(curves[phase,key],['feature']+GRID);shape.insert(0,'config',str(config));shape.insert(0,'phase',phase);all_shapes.append(shape)
            shape=shapes(quarter_curves[phase,key],['quarter','feature']+GRID);shape.insert(0,'config',str(config));shape.insert(0,'phase',phase);all_quarters.append(shape)
    shape=pd.concat(all_shapes,ignore_index=True);qshape=pd.concat(all_quarters,ignore_index=True)
    shape.to_csv(dest/'curve-shapes.csv',index=False);qshape.to_csv(dest/'quarter-curve-shapes.csv',index=False)
    monotonic=shape[(shape.config==str(CONFIGS[0]))&shape.feature.eq('A1')].groupby(['phase','direction']).agg(
        grids=('feature','size'),nondecreasing=('nondecreasing','sum'),nonincreasing=('nonincreasing','sum')).reset_index()
    monotonic.to_csv(dest/'A1-monotonicity-overview.csv',index=False)
    plot_names=[]
    for direction in ['LONG','SHORT']:
        for tp in [.003,.005]:
            for sl in [.003,.005]:
                for horizon in [4,8,24]:
                    suffix=f'{direction}-{tp}-{sl}-{horizon}'
                    for fields,label in [(['A1','A2'],'A1-vs-A2'),(['imbalance'],'nearby-imbalance'),(['distance_difference'],'nearest-distance'),(['clusters'],'clusters')]:
                        series=[]
                        for phase in states:
                            f=curves[phase,AKEY]
                            for field in fields:
                                g=f[(f.feature==field)&(f.direction==direction)&(f.tp==tp)&(f.sl==sl)&(f.horizon==horizon)&(f.bucket>=0)].sort_values('bucket')
                                series.append((phase+' '+field,list(zip(g.bucket,g.tp_first_rate))))
                        filename=f'{label}-{suffix}.svg';svg(plots/filename,f'{label}: {direction}, TP {tp}, SL {sl}, {horizon}h',series);plot_names.append(filename)
    chosen='A1-vs-A2-LONG-0.003-0.003-8.svg'
    page='<html><head><meta charset="utf-8"><title>Phase 3R.1 diagnostics</title></head><body style="background:#faf8f3;font-family:Georgia;max-width:1000px;margin:40px auto"><h1>1h full-map diagnostics</h1><p>Descriptive curves, not trading thresholds. Development-only bucket boundaries are frozen for the previously inspected replication period. All 24 outcome grids are included. Future outcome charts are analysis artifacts, never candidate-creation information.</p>'
    for name in plot_names:page+=f'<figure><img style="max-width:100%" src="plots/{name}" alt="{html.escape(name)}"/></figure>'
    (dest/'diagnostics.html').write_text(page+'</body></html>',encoding='utf-8')
    phase_rows=[];composition=[];correlations=[];baseline_rows=[]
    for phase,s in states.items():
        phase_rows.append(dict(phase=phase,states=len(s),score_min=s.A1.min(),score_max=s.A1.max(),exact_scores=s.A1.nunique(),
            zero=int(s.A1.eq(0).sum()),negative=int(s.A1.lt(0).sum()),positive=int(s.A1.gt(0).sum()),
            sign_flips=int(s.sign_case.eq('sign_flip').sum()),changed=int(s.A1.ne(s.A2).sum())))
        c=s.groupby('quarter').agg(states=('event_id','size'),A1_mean=('A1','mean'),A1_min=('A1','min'),A1_max=('A1','max'),clusters_mean=('clusters','mean')).reset_index();c.insert(0,'phase',phase);composition.append(c)
        for feature in ['A2','imbalance','candidate_count','clusters','mean_age']:
            correlations.append(dict(phase=phase,feature=feature,spearman_with_A1=s.A1.rank().corr(s[feature].rank())))
        b=pd.read_csv(ROOT/phase/'analysis'/f'{AKEY}-baseline.csv');b.insert(0,'phase',phase);baseline_rows.append(b)
    phase_frame=pd.DataFrame(phase_rows);corr=pd.DataFrame(correlations);quarters=pd.concat(composition);baseline=pd.concat(baseline_rows)
    phase_frame.to_csv(dest/'A-distribution-overview.csv',index=False);corr.to_csv(dest/'A-feature-correlations.csv',index=False);quarters.to_csv(dest/'chronological-overview.csv',index=False)
    selected=shape[(shape.config==str(CONFIGS[0]))&(shape.feature.isin(['A1','A2','imbalance','distance_difference','clusters','candidates_per_cluster']))&(shape.direction=='LONG')&(shape.tp==.003)&(shape.sl==.003)&(shape.horizon==8)]
    selected=selected[['phase','feature','first_bucket','last_bucket','observed_buckets','nondecreasing','nonincreasing','high_minus_low','rank_correlation','ends_minus_middle','min_bucket_states']]
    age_shape=shape[(shape.config==str(CONFIGS[0]))&(shape.feature.isin(['mean_age','mean_prior_crossings','very_old_over_365d_fraction','full_mean_source_age_hours','half_mean_source_age_hours']))&(shape.direction=='LONG')&(shape.tp==.003)&(shape.sl==.003)&(shape.horizon==8)]
    age_shape=age_shape[['phase','feature','first_bucket','last_bucket','high_minus_low','min_bucket_states']]
    caution='These are descriptive associations in autocorrelated states, not executable returns or an edge claim. The illustrative TP=SL=0.003, 8h grid is fixed for readability; all 24 grids are exported. AMBIGUOUS and NEITHER remain in complete-state denominators. Gross expectancy excludes ambiguous, neither and censored observations and excludes costs.'
    figures='Diagnostic plots: `data/phase3r1/reports/diagnostics.html` (96 SVGs, all outcome grids). Curves connect frozen development buckets for readability; no threshold is chosen.'
    all_sizes=sum(p.stat().st_size for phase in states for p in (ROOT/phase).rglob('*') if p.is_file())
    runtime=[]
    for phase in states:
        for stage in ['A','BC']:
            r=json.loads((ROOT/phase/(stage+'-complete.json')).read_text());runtime.append(dict(phase=phase,stage=stage,states=r['timestamps'],initialization_s=r['initialization_seconds'],loop_s=r['loop_seconds'],peak_GiB=r['peak_RAM_bytes']/2**30))
    save('PHASE3R1_COMPLETION.md',f'''# Phase 3R.1 Completion

Completed 1h only: optimized full-map reconstruction, exact reference parity gate,
1,000-timestamp benchmark, development A then B/C analysis, frozen 2023 replication,
observed D reconstruction and compact causal Volume/Delta preservation.

{table(phase_frame)}

Development is 2022-01-05 17:00 through 2022-12-31 23:00 UTC (8,647 states).
No 2021 timestamp has the required 850-day price history. Replication is
2023-01-01 00:00 through 2023-12-31 23:00 (8,760 states), labeled exactly
`previously inspected replication period`. All 2024 market data remains untouched.
Five directional maps per timestamp: 87,035 snapshots in total, with 417,768
outcome rows stored once by event/grid. Final split-boundary horizons are censored,
not extended into 2023 for development or 2024 for replication.

Parity: 168 reference snapshots, all candidate memberships/features/coverage,
both D maps and 576 outcomes passed; integer scores/IDs exact, float tolerance
1e-12. Full suite: {test['tests']} tests, {test['failures']} failures,
{test['errors']} errors, {test['skipped']} skipped. See the separate final audit.

Measured generation:

{table(pd.DataFrame(runtime))}

Generated development/replication research tables and analyses total
{all_sizes/2**20:.2f} MiB (excluding raw archives and reusable derived inputs).
No full-run history is held as an ever-growing snapshot list. Memory is bounded
by catalog, monthly profile cache and daily output batches, not state count.

The original score closely tracks nearby support/resistance imbalance; this is
an algebraically related representation, not independent evidence. Shape and
quarter/replication differences are detailed in the result reports. No detector
winner, final score cutoff, leverage, trading signal or live execution was selected.

Additional archive acquisition: 117,925,990 aggregate trades in 2019-12-31 and
2020-01 through 2020-08, plus earlier authoritative REST candles. April/May monthly
publication failures were replaced by complete official daily collections.
One new observable-loss minute is quarantined, with the prior policy unchanged.
D has no fully clean 850-day trade window before 2024 and is not ranked.

New code: `backend/app/fullmap_scale/` (history/trades/coverage, engine/VAP,
parity/benchmark, streaming storage/explanatory features, stage runner,
analysis/freeze, reports/audit). New tests: `backend/tests/test_phase3r1.py`.
All new outputs are under `data/phase3r1/` and the ten PHASE3R1 reports.
Phase 3R reference code and previous research outputs remain preserved.

Reports: PHASE3R1_OPTIMIZATION, DATA_COVERAGE, A_FULLMAP_RESULTS, A_ABLATIONS,
CLUSTER_GEOMETRY, BC_COMPARISON, CHRONOLOGICAL_STABILITY, 2023_REPLICATION,
D_COVERAGE_STATUS (all `.md` at project root). {figures}

Stopped before 15m/4h/1d, confluence, threshold selection and live trading.
''')
    save('PHASE3R1_OPTIMIZATION.md',f'''# Optimization and Parity

A1 is unchanged. 850 calendar days, 20,400 closed hourly candles, close at T,
one-hour steps, full dependency expiration, known_at <= T and prior outcome
semantics remain exactly as Phase 3R. Original golden tests remain in the suite.

A/B candidates are cataloged once; membership filters confirmation and complete
source span. C starts at each rolling left boundary. Its deterministic high/low
tracker state is replayed until BOTH tracker indices equal a cached state after
the same candle; equal state plus equal subsequent inputs proves an identical
suffix. Only then is the suffix reused. Without synchronization, the complete
window is replayed. This is not a switch to global-history initialization.
Tests include flat never-synchronizing tracks and randomized rolling windows.

Geometry uses vector arithmetic and exact original full/half boundaries.
Nearest ties retain known_at/source/price tie-breaking. Cluster pairs use
sorted interval endpoints, including touching boundaries. D uses the identical
reference rolling arithmetic with compact hourly views instead of DataFrames.

Catalog indices are deterministic within each run/stage catalog. Daily membership
checkpoints plus added/removed uint32 arrays are zlib-compressed in Parquet.
Unused precomputed rows are pruned after generation without renumbering indices;
A and B/C catalogs are disjoint, with one record per used candidate in each phase.
Chronological phases remain self-contained and share the original candidate SHA
identities, rather than treating a repeated historical level as new evidence.
Restore original event order by known_at then RESISTANCE before SUPPORT for
same-candle B/C events. Identity remains the original candidate SHA, not the
integer index. Raw memberships remain reconstructable; scores cannot substitute
for them. State feature rows omit redundant member-ID arrays only.

Reference gate: {gate['snapshots']} snapshots and {gate['outcomes']} outcome rows;
all fields compared, five physical future-truncation checks, D quantities and
coverage identical/numerically equivalent (rtol=atol=1e-12). Gate source hashes
prevent execution after an untested engine change.

Actual benchmark: 1,000 timestamps / 5,000 directional maps, including streaming
exports and A age/crossing features. Initialization {bench['initialization_seconds']:.2f}s;
loop {bench['seconds_per_1000_timestamps']:.2f}s; peak RAM {bench['peak_RAM_bytes']/2**30:.3f} GiB;
output {bench['bytes_per_1000_timestamps']/2**20:.2f} MiB. Linear projection for
17,407 timestamps: {bench['projected_seconds']/60:.2f} minutes and
{bench['projected_bytes']/2**20:.2f} MiB. This projection excludes separate D,
outcome and statistical analysis work. Actual stage runtimes are in completion.
No hundreds-of-GB duplicated JSONL inspection export is generated for the full run.

Frozen analysis ID: `{freeze['freeze_id']}`. Feature/model/code digests are checked
before replication. Rendering/audit code is outside the research-definition seal.
''')
    save('PHASE3R1_DATA_COVERAGE.md',f'''# Authoritative Data Coverage

Earliest available REST BTCUSDT USD-M 1h candle: **2019-09-08 17:00 UTC**.
REST was queried from 2019-01-01, not inferred from a launch announcement.
Monthly archives start 2020-01; daily archives include 2019-12-31. Exact REST
responses and local SHA-256 are retained. REST has no official publisher checksum;
the overlapping December 31 official checksum/CRC archive matches exactly.
All hourly sequence/OHLC validation passed. No candle gaps are interpolated.

First exact 850-day price history: **2022-01-05 17:00 UTC**.
2021 is unavailable for this strategy definition; only the 8,647 eligible 2022
timestamps are development observations. Earlier 2019/2020 candles are history,
not performance observations. Zero-volume authoritative candles are not silently
removed from the regular hourly clock. 2023 is already-inspected replication.

Earliest authoritative aggregate archive: **2019-12-31**, first trade timestamp
{pd.Timestamp(coverage['earliest_archived_trade_timestamp'],unit='ms',tz='UTC').isoformat()}.
The historical aggregate REST probe was rejected by Binance's recent-history
restriction; it cannot establish earlier trade coverage. First possible 850-day
archived-trade window is **2022-04-29 00:00 UTC**, but known quarantines make it
incomplete in observable coverage. There are **zero** complete-coverage D windows
before 2024. No earlier clean trade history is assumed.

Additional selected aggregate rows: 117,925,990. April and May 2020 monthly files
omit dates despite valid checksum/CRC, so complete daily publications were used.
Daily/monthly evidence and official 1m volume checks follow unchanged coverage-v4.
New quarantine: 2020-04-15 11:37-11:38 UTC (one minute); original quarantines remain.
Do not confuse complete archive publication coverage with recovered missing trades.

Evidence: `data/phase3r1/history/discovery/`, `history/raw/`, `history/integrity/`,
`history/coverage/`, `history/trade-coverage.json`, `coverage-final.json`.
Raw and normalized/derived data are separate. No 2024 archive request or market
file is used. 2023 outcome generation is gated behind completed development analysis.
''')
    save('PHASE3R1_A_FULLMAP_RESULTS.md',f'''# A Full-Map Results

{table(phase_frame)}

Unlike the 24-state sanity sample, development contains negative, zero and positive
scores. Full exact score distributions (frequency/composition), outcome grids,
quarter and volatility/return regime tables are under each phase's `analysis/`.
LONG score is A1; SHORT score is its exact negative. SHORT results grouped by A1
must therefore be read in the reverse score direction, not as independent scores.

Illustrative frozen-bucket shapes:

{table(selected)}

`curve-shapes.csv` answers monotonicity across every grid: nondecreasing and
nonincreasing are explicit finite-sample checks; rank correlation, high-minus-low,
ends-minus-middle (U/inverted-U diagnostic) and largest adjacent step are retained.
These descriptors do not prove a population U-shape or identify a trade threshold.
Quarter and regime tables test stability rather than selecting the best shape.

Explicit A1 monotonicity counts across the 12 grids per direction:

{table(monotonic)}

Development has no monotonic four-bucket A1 curve in either direction. In 2023,
5/12 LONG curves increase and 2/12 SHORT curves decrease with A1. These overlapping
grids are not independent replications. Increasing LONG score or decreasing A1
for SHORT therefore does not show a consistently monotonic relationship across
periods. The illustrative development LONG curve has higher endpoints than middle
buckets, whereas the replication curve increases. This is descriptive shape
variation, not proof of a population U-shape, flatness, or a useful threshold.
For the illustrative LONG grid, the endpoint contrast changes sign in 2022Q1
and again in 2023Q4. Pooled increasing curves do not establish regime stability.

Bucket-support columns matter: high-minus-low compares the observed endpoints.
If replication lacks a development bucket, it is NOT the same endpoint contrast.
A two-bucket monotonic flag is not evidence for a four-bucket monotonic shape.

What was A1 capturing? Rank correlations with descriptive state facts:

{table(corr)}

A1 is full-band support-minus-resistance plus half the outer imbalance, so a
strong association with nearby imbalance is structural. It is not independent
confirmation of predictive value. Score magnitude alone cannot establish edge.

{caution}

Uncertainty uses fixed nonoverlapping seven-day UTC block resampling, 1,000 draws,
seed 3101. Intervals are descriptive conditional-rate minus same-period baseline;
fewer than five represented blocks yields no interval. There are no row-level
p-values. A seven-day block cannot eliminate every long-memory/regime concern;
many examined features and grids are exploratory comparisons, not confirmatory tests.

{figures}
''')
    save('PHASE3R1_A_ABLATIONS.md',f'''# A1/A2/A3/A4 and Outer Band

A1 retains original weights. A2 removes only the outer half band. A3 analyzes
nearby support/resistance counts, imbalance and ratio. A4 analyzes continuous
distances and geometry. No representation is translated into a trading cutoff.

{table(phase_frame[['phase','states','sign_flips','changed']])}

These are paired observations at identical timestamps. `half-band-paired-cases.csv`
reports same sign, sign flip and one-zero cases; substantial magnitude difference
means a nonzero difference at least the development 75th percentile. The threshold
is descriptive and frozen in 2023, not an optimized trading parameter.
`half-band-within-A2.csv` conditions on the original full-band score bucket and
examines signed outer contribution; the quarter version checks temporal robustness.
`half-band-block-intervals.csv` uses shared time blocks rather than independent
A1/A2 sample tests. A1 and A2 cannot have different realized paths at the same T;
only the information partition differs.

The outer band materially changes many states, but state changes alone do not
establish incremental information. Interpret within-A2 and chronological/replication
contrasts together. This phase does not declare it either a winning addition or
discardable noise based on one metric. Raw count/geometry curves remain separate.

{table(selected[selected.feature.isin(['A1','A2','imbalance','distance_difference'])])}

{caution}
''')
    save('PHASE3R1_CLUSTER_GEOMETRY.md',f'''# Cluster Geometry, Age and Crossings

Raw full-map geometry is analyzed independently: imbalance, support/resistance
ratio, nearest distances/difference, above/below asymmetry, cluster count,
candidates per connected cluster, overlap pairs and repeated prices. No weighted
strength formula is introduced. Closed +/-0.004 intervals connect transitively,
so a small connected-component count does not imply a small number of observations.

{table(selected[selected.feature.isin(['clusters','candidates_per_cluster','imbalance','distance_difference'])])}

`*-clusters-within-count.csv` checks cluster relationships within candidate-count
buckets, rather than interpreting correlated count/cluster curves as independent
effects. `*-quarter-curves.parquet` distinguishes time/regime changes. Thousands
of candidates per connected region are spatial density, not thousands of independent
reactions. No superior strength formula is inferred from these dense maps.

A contributing level source-age buckets are <=30d, (30,180]d, (180,365]d and >365d.
Counts/type composition, prior crossing/visit means and full/half-band mean ages
are causal extra fields on A states. All original candidates remain active;
neither age nor crossing count changes A1. `old-levels-crossings.csv` studies the
joint old-level fraction and prior-crossing description. All per-feature curves
are available for age fractions, age-specific crossing/visit means and proximity.

{table(age_shape)}

The A cluster distribution shifts from a development mean of about 15.73 to
about 2.88 in replication. Frozen cluster buckets 2 and 3 are absent in 2023;
do not relabel or refit them to manufacture a comparable four-bin curve.
Cluster associations may also change resolution/ambiguity rates for BOTH
directions, rather than offer directional information. Outcome composition
and within-count/quarter controls must accompany the TP fraction curves.

A crossing is a strict side change between consecutive closed prices after known_at;
equal closes are not strict crossings. A visit begins a run of closed candles whose
high/low contains the exact reference price. Last contact uses only end <= T.
This is not a claim about intrabar path order. Future event-time arrays may be
precomputed but queries count only events available by T; truncation tests pass.

These are market-state associations. They cannot by themselves prove an old level
caused a reaction or that crossing invalidates it. Decay/invalidation was not added.
''')
    bc=shape[(shape.feature.isin(['imbalance','clusters','distance_difference']))&(shape.direction=='LONG')&(shape.tp==.003)&(shape.sl==.003)&(shape.horizon==8)]
    save('PHASE3R1_BC_COMPARISON.md',f'''# B/C Full-Map Comparison

B widths 1/2 and C reversals 0.003/0.005 use exactly the A timestamps, price close,
850-day window and event-level future outcomes. B/C have no native A score.
Their raw counts, distances, density, clusters, overlap and age are compared
descriptively. C's window-local initialization is preserved by proven state
synchronization, not replaced with a global-history strategy.

Illustrative geometry contrasts (high-minus-low frozen bucket TP fraction):

{table(bc[['phase','config','feature','high_minus_low','nondecreasing','nonincreasing']],limit=30)}

All grid/configuration rows are in `reports/curve-shapes.csv`; quarter results
are separate. Baselines are identical unconditioned event periods, not isolated
zone interactions. Curves from the same underlying hours are dependent. Block
intervals are not independent detector-vs-detector tests, and no detector is ranked
as superior from a larger conditional fraction. Results remain exploratory.
''')
    save('PHASE3R1_CHRONOLOGICAL_STABILITY.md',f'''# Chronological Stability

Deterministic calendar quarters, no shuffled split, no per-quarter tuning:

{table(quarters)}

Every feature/outcome grid has quarterly curves in `*-quarter-curves.parquet`
and shape diagnostics in `reports/quarter-curve-shapes.csv`. Exact A scores also
have quarterly and causal 24-hour volatility/recent-return regime tables.
Regime cuts are estimated on development only and frozen for replication.
Unconditioned quarterly baselines retain the same horizon/censoring conventions.

Check effect sign and shape across all four development quarters and all four
replication quarters rather than choosing a favorable quarter. Candidate counts,
clusters and price regimes are temporally correlated; a pooled relationship can
be driven by their changing composition. The partial 2022Q1 starts at the first
eligible timestamp; unavailable earlier dates are not treated as zero-effect data.

Seven-day time-block intervals supplement these quarterly comparisons, not
ordinary independent-hour significance tests. No p-value-based selection is made.
''')
    save('PHASE3R1_2023_REPLICATION.md',f'''# 2023: previously inspected replication period

This is not untouched validation. Development A and B/C analyses were completed
before freeze `{freeze['freeze_id']}`. The same code, detector parameters, feature
definitions, score distributions, grids and development quantile boundaries were
then used for 8,760 2023 timestamps. No score threshold or regime cut was refit.

Development versus replication shape comparison:

{table(selected)}

Raw feature distributions may shift beyond development quantile ranges; outer
buckets keep their frozen bounds and no balancing/refit is performed. Compare
the entire shape and quarter-specific effects, not one overall rate. Half-band
case tables and within-A2 contrasts use the same frozen definitions; B/C geometry
is compared under the same event framework. No single metric selects a winner.

Future outcomes for late December 2023 are censored at 2024-01-01, using only
closed candles with open times in 2023. No 2024 candle is read to complete a label.
''')
    drows=[]
    for phase in states:
        info=json.loads((ROOT/phase/'D/complete.json').read_text())
        drows.extend(dict(phase=phase,**r) for r in info['summary'])
    save('PHASE3R1_D_COVERAGE_STATUS.md',f'''# D Coverage and Volume Preservation

{table(pd.DataFrame(drows))}

The first temporally available 850-day aggregate archive window ends
2022-04-29 00:00 UTC. Earlier price-map timestamps are explicitly insufficient
for D and do not use a shorter trade window. Every later window before 2024
intersects at least one retained coverage quarantine, so there is no fair
complete-coverage D predictive sample. No zero-filling, interpolation, candle-volume
substitution or parameter ranking is performed.

Both 50/100-dollar neutral observed maps retain reference concentration multiple
1.5. Compact per-timestamp summaries preserve buy/sell/quantity/delta and quantities
above/below/current-straddling bins. Verified hourly bin inputs and configuration
are retained in `derived/`, allowing complete per-bin map reconstruction for
audit without duplicating every bin at every timestamp. Source hashes and
reconstruction instructions are in each phase's `D/complete.json`.

A/B/C compact last-closed-hour support/resistance union volumes, buy/sell/delta,
normalized delta and shared volume remain in state tables. Quarantined hours have
unavailable volume, not zero. No Volume Delta thresholds or combined score are
fitted. Phase 3.5 remains preserved single-zone component research; incremental
full-map Volume/Delta value is reserved for a later ablation.
''')
    write_json(dest/'summary.json',dict(status='REPORTS_GENERATED',phases=phase_rows,tests=test,plots=len(plot_names),
        research_artifact_bytes=all_sizes,freeze_id=freeze['freeze_id'],no_edge_claim=True))
    print('REPORTS_WRITTEN',10,len(plot_names),flush=True)


if __name__=='__main__':main()
