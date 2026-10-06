"""All-grid descriptive cohorts and paired UTC-block uncertainty, no selection."""
from itertools import product, combinations
import numpy as np
import pandas as pd
from app.multimap.analyze import arrays, quartiles, buckets
from .contract import *

GRID = ['direction', 'tp', 'sl', 'horizon']
METRICS = ['TP_FIRST', 'SL_FIRST', 'NEITHER', 'AMBIGUOUS', 'mfe_pct', 'mae_pct']


def load_states(phase):
    phase_guard(phase)
    return pd.concat([pd.read_parquet(p) for p in sorted((ROOT/phase/'states').glob('*.parquet'))], ignore_index=True)


def fit_buckets(frame):
    model = {tf: quartiles(np.abs(frame[tf+'__imbalance'])) for tf in TFS}
    for field in ['joint_quantity', 'support_normalized_delta', 'resistance_normalized_delta', 'joint_delta']:
        model[field] = quartiles(frame[field].where(frame.flow_status == 'AVAILABLE'))
    return model


def cohorts(frame, model):
    """Definitions are independent of outcomes; even empty planned cells are retained."""
    n = len(frame); masks = {'all': np.ones(n, bool)}; metadata = {'all': ('baseline', 'ALL')}
    comparisons = []
    def add(name, mask, family, interpretation='BOTH'):
        masks[name] = np.asarray(mask, dtype=bool)
        metadata[name] = (family, interpretation)
        return name
    def compare(name, a, b, family):
        comparisons.append((name, a, b, family))
    for descriptor in ['imbalance', 'A1', 'A2']:
        patterns = frame[descriptor+'_pattern'].to_numpy(dtype=str)
        chars = np.array([list(s) for s in patterns])
        for side, target, opposite, interpretation in [('support','S','R','LONG'), ('resistance','R','S','SHORT')]:
            counts = np.sum(chars == target, axis=1)
            opposing = np.sum(chars == opposite, axis=1)
            missing = np.any(chars == 'M', axis=1)
            for count in range(5):
                k = add(f'{descriptor}/{side}/count/{count}', (counts==count)&~missing, 'sign_count', interpretation)
                if descriptor == 'imbalance':
                    compare(k+'/vs_all', k, 'all', 'sign_baseline')
                add(f'{descriptor}/{side}/unopposed/{count}', (counts==count)&(opposing==0)&~missing, 'unopposed_count', interpretation)
            for subset in SUBSETS:
                ids = [TFS.index(tf) for tf in subset]
                aligned = np.all(chars[:,ids] == target, axis=1)
                combo = '+'.join(subset)
                name = add(f'{descriptor}/{side}/aligned/{combo}', aligned, 'hierarchy_inclusive', interpretation)
                add(f'{descriptor}/{side}/only/{combo}', aligned&(counts==len(subset))&~missing, 'hierarchy_exclusive', interpretation)
                if descriptor == 'imbalance':
                    compare(name+'/vs_all', name, 'all', 'hierarchy_baseline')
                    for m in range(1, len(subset)):
                        for lower in combinations(subset, m):
                            b = f'{descriptor}/{side}/aligned/'+ '+'.join(lower)
                            compare(name+'/vs/'+ '+'.join(lower), name, b, 'nested_baseline')
            if descriptor == 'imbalance':
                for base, added in ADDITIONS:
                    condition = np.all(chars[:,[TFS.index(tf) for tf in base]] == target, axis=1)
                    a = chars[:,TFS.index(added)]
                    prefix = f'incremental/{side}/{"+".join(base)}/add_{added}'
                    for label, mask in [('agrees',a==target), ('neutral',a=='N'), ('conflicts',a==opposite), ('missing',a=='M'), ('not_agrees',(a=='N')|(a==opposite))]:
                        add(prefix+'/'+label, condition&mask, 'incremental', interpretation)
                    for b in ['not_agrees', 'neutral', 'conflicts']:
                        compare(prefix+'/agrees_vs_'+b, prefix+'/agrees', prefix+'/'+b, 'incremental')
        # Complete exact pattern grid: no post-replication category creation or merging.
        for pattern in map(''.join, product('SRNM', repeat=4)):
            add(descriptor+'/pattern/'+pattern, patterns==pattern, 'exact_pattern')
    primary = np.array([list(s) for s in frame.imbalance_pattern])
    for side, target, interpretation in [('support','S','LONG'), ('resistance','R','SHORT')]:
        count = np.sum(primary==target, axis=1)
        spatial = frame[side+'_overlap_count'].to_numpy()
        opposition = np.sum(primary==('R' if target=='S' else 'S'), axis=1)
        for direction_state,condition in [('agrees',(count>=2)&(opposition==0)),
                                          ('conflicts',(count>0)&(opposition>0))]:
            for overlap,condition2 in [('overlap',spatial>=2),('no_overlap',spatial<2)]:
                add(f'direction_space/{side}/{direction_state}/{overlap}',condition&condition2,
                    'direction_space',interpretation)
        for k in range(5):
            name = add(f'zone/{side}/count/{k}', spatial==k, 'zone_count', interpretation)
            compare(name+'/vs_all', name, 'all', 'zone_baseline')
        for subset in SUBSETS:
            combo = '+'.join(subset)
            mask = frame[side+'_overlap_'+combo].to_numpy()
            name = add(f'zone/{side}/combo/{combo}', mask, 'zone_combination', interpretation)
            compare(name+'/vs_all', name, 'all', 'zone_baseline')
        for k in range(5):
            for overlap in range(5):
                add(f'joint/{side}/sign{k}/zone{overlap}', (count==k)&(spatial==overlap), 'direction_x_space', interpretation)
            prefix = f'spatial_increment/{side}/sign{k}'
            a = add(prefix+'/overlap', (count==k)&(spatial>=2), 'spatial_increment', interpretation)
            b = add(prefix+'/no_overlap', (count==k)&(spatial<2), 'spatial_increment', interpretation)
            compare(prefix, a, b, 'spatial_increment')
        # Exact direction-pattern conditioning prevents confounding by TF identity.
        for pattern in map(''.join, product('SRN', repeat=4)):
            condition = frame.imbalance_pattern.eq(pattern).to_numpy()
            prefix = f'spatial_exact/{side}/{pattern}'
            a = add(prefix+'/overlap', condition&(spatial>=2), 'spatial_exact', interpretation)
            b = add(prefix+'/no_overlap', condition&(spatial<2), 'spatial_exact', interpretation)
            compare(prefix, a, b, 'spatial_exact')
        q = buckets(frame.joint_quantity.where(frame.flow_status=='AVAILABLE'), model['joint_quantity'])
        for k in range(5):
            for bucket in range(-1, len(model['joint_quantity'])+1):
                add(f'quantity/{side}/count{k}/Q{bucket}', (count==k)&(q==bucket), 'quantity', interpretation)
            compare(f'quantity/{side}/count{k}/high_minus_low', f'quantity/{side}/count{k}/Q{len(model["joint_quantity"])}', f'quantity/{side}/count{k}/Q0', 'quantity')
        aligned4 = count==4
        for field in ['support_normalized_delta', 'resistance_normalized_delta', 'joint_delta']:
            b = buckets(frame[field].where(frame.flow_status=='AVAILABLE'), model[field])
            for k in range(-1, len(model[field])+1):
                add(f'delta/{side}/{field}/Q{k}', aligned4&(b==k), 'delta_exploratory', interpretation)
        native = []
        for tf in TFS:
            b = buckets(np.abs(frame[tf+'__imbalance']), model[tf]); native.append(b)
            for k in range(-1, len(model[tf])+1):
                add(f'magnitude/{side}/{tf}/Q{k}', aligned4&(b==k), 'magnitude', interpretation)
        native = np.array(native).T
        missing = np.any(native<0, axis=1)
        weak = np.all(native==0, axis=1)
        strong = np.all(native==np.array([len(model[tf]) for tf in TFS]), axis=1)
        moderate = np.all((native>0)&(native<np.array([len(model[tf]) for tf in TFS])), axis=1)
        for name, mask in [('weak',weak), ('moderate',moderate), ('strong',strong), ('mixed',~(weak|moderate|strong|missing)), ('missing',missing)]:
            add(f'magnitude/{side}/joint/{name}', aligned4&mask, 'magnitude', interpretation)
    for pattern in map(''.join, product('SRNM', repeat=4)):
        add('conflict/'+pattern[:2]+'/'+pattern[2:], frame.imbalance_pattern.eq(pattern), 'conflict')
    for name, a, b in [('lower_support_higher_resistance','SSRR','RRSS'), ('lower_support_vs_all_support','SSRR','SSSS'), ('lower_resistance_vs_all_resistance','RRSS','RRRR')]:
        compare('conflict/'+name, 'imbalance/pattern/'+a, 'imbalance/pattern/'+b, 'conflict')
    return masks, metadata, comparisons


def block_arrays(frame, values):
    weeks = frame.decision_timestamp.to_numpy() // (7*86400000)
    unique, wi = np.unique(weeks, return_inverse=True)
    rng = np.random.default_rng(5105)
    weights = rng.multinomial(len(unique), np.full(len(unique), 1/len(unique)), size=1000)
    metrics = np.stack([values[m] if m in values else values[m+'_sum'] for m in METRICS], axis=-1)
    return wi, unique, weights, metrics


def contrast(mask_a, mask_b, values, wi, weights, metrics, grids, bootstrap=True):
    ng, nm = metrics.shape[1:]
    nw = weights.shape[1]
    data = []
    for mask in [mask_a, mask_b]:
        denom = np.zeros((nw, ng)); num = np.zeros((nw, ng, nm))
        np.add.at(denom, wi[mask], values['complete'][mask])
        np.add.at(num, wi[mask], metrics[mask])
        data.append((denom, num))
    (ad, an), (bd, bn) = data
    ac, bc = ad.sum(axis=0), bd.sum(axis=0)
    ab, bb = (ad>0).sum(axis=0), (bd>0).sum(axis=0)
    with np.errstate(divide='ignore', invalid='ignore'):
        effect = an.sum(axis=0)/ac[:,None] - bn.sum(axis=0)/bc[:,None]
    lo = np.full((ng,nm), np.nan); hi = lo.copy(); finite = np.zeros((ng,nm), int)
    if bootstrap and np.any((ab>=5)&(bb>=5)):
        with np.errstate(divide='ignore', invalid='ignore'):
            samples = (weights@an.reshape(nw,-1)).reshape(1000,ng,nm)/(weights@ad)[:,:,None] - (weights@bn.reshape(nw,-1)).reshape(1000,ng,nm)/(weights@bd)[:,:,None]
        finite = np.isfinite(samples).sum(axis=0)
        for g in range(ng):
            for m in range(nm):
                if ab[g]>=5 and bb[g]>=5 and finite[g,m]>=950:
                    lo[g,m], hi[g,m] = np.quantile(samples[:,g,m][np.isfinite(samples[:,g,m])], [.025,.975])
    for g, grid in enumerate(grids):
        for m, metric in enumerate(METRICS):
            yield dict(zip(GRID,grid)) | dict(metric=metric, effect=float(effect[g,m]),
                ci_low=float(lo[g,m]), ci_high=float(hi[g,m]), a_complete=int(ac[g]), b_complete=int(bc[g]),
                a_blocks=int(ab[g]), b_blocks=int(bb[g]), supported=bool(ac[g]>=200 and bc[g]>=200 and ab[g]>=5 and bb[g]>=5),
                finite_bootstrap_draws=int(finite[g,m]), uncertainty='shared seven-day UTC blocks' if bootstrap else 'quarter effect only; pooled CI separate')


def execute(phase):
    phase_guard(phase); dest = ROOT/phase; output = dest/'analysis'
    if (output/'complete.json').exists():
        return
    output.mkdir(exist_ok=True)
    frame = load_states(phase)
    timestamp_guard(frame.decision_timestamp.to_numpy(), phase)
    if frame.event_id.duplicated().any():
        raise ValueError('Duplicate common event')
    sources = Sources(phase)
    ys = pd.concat([sources.frame(p) for p in sorted((PROJECT/'data/phase4/15m'/phase/'future-outcomes').glob('*.parquet'))], ignore_index=True)
    joined = ys.merge(frame[['event_id','decision_timestamp']], on='event_id', suffixes=('', '_common'), validate='many_to_one')
    if len(joined) != len(frame)*24 or not joined.decision_timestamp.eq(joined.decision_timestamp_common).all():
        raise ValueError('Outcome identity mismatch')
    grids, values = arrays(frame[['event_id']], ys, '15m')
    provenance = read(dest/'source-hashes.json'); provenance.update(sources.hashes)
    write(dest/'source-hashes.json', provenance)
    write(dest/'outcome-reuse.json', dict(status='EXACT_EXISTING_ROWS_NO_REGENERATION', rows=len(ys), events=len(frame), hashes=sources.hashes))
    model = fit_buckets(frame) if phase=='development' else read(ROOT/'development/analysis/buckets.json')
    write(output/'buckets.json', model)
    masks, meta, comparisons = cohorts(frame, model)
    write(output/'category-definitions.json', dict(metadata=meta, comparisons=comparisons))
    quarters = pd.to_datetime(frame.decision_timestamp, unit='ms', utc=True).dt.quarter.to_numpy()
    wi, weeks, weights, metrics = block_arrays(frame, values)
    rows = []
    for name, mask in masks.items():
        family, interpretation = meta[name]
        for period in ['ALL', 1, 2, 3, 4]:
            selected = mask if period=='ALL' else mask&(quarters==period)
            totals = {k: v[selected].sum(axis=0) for k, v in values.items()}
            for gi, g in enumerate(grids):
                total = totals['complete'][gi]
                blocks = len(np.unique(wi[selected & (values['complete'][:,gi]>0)]))
                row = dict(category=name, family=family, interpretation=interpretation, period=str(period),
                    **dict(zip(GRID,g)), n=int(selected.sum()), complete=int(total), censored=int(totals['censored'][gi]),
                    week_blocks=blocks, supported=bool(total>=200 and blocks>=5))
                for m in METRICS:
                    v = totals[m] if m in totals else totals[m+'_sum']
                    row[m] = float(v[gi]/total) if total else np.nan
                rows.append(row)
    summary = pd.DataFrame(rows)
    summary.to_parquet(output/'cohorts.parquet', index=False, compression='zstd')
    summary.to_csv(output/'cohorts.csv', index=False)
    contrast_rows = []
    for ci, (name, a, b, family) in enumerate(comparisons):
        for period in ['ALL', 1, 2, 3, 4]:
            condition = np.ones(len(frame),bool) if period=='ALL' else quarters==period
            for row in contrast(masks[a]&condition, masks[b]&condition, values, wi, weights, metrics, grids, bootstrap=period=='ALL'):
                contrast_rows.append(dict(comparison=name, family=family, period=str(period), a=a, b=b, **row))
        if (ci+1)%50==0:
            print('CONFLUENCE_CONTRASTS', phase, ci+1, len(comparisons), flush=True)
    contrasts = pd.DataFrame(contrast_rows)
    contrasts.to_parquet(output/'contrasts.parquet', index=False, compression='zstd')
    contrasts.to_csv(output/'contrasts.csv', index=False)
    # Native magnitude vectors are auditable, not summed into a score.
    sensitivity = frame[['event_id','decision_timestamp','imbalance_pattern']].copy()
    for tf in TFS:
        sensitivity[tf+'_magnitude_bucket'] = buckets(np.abs(frame[tf+'__imbalance']), model[tf])
    sensitivity.to_parquet(output/'native-magnitude-vectors.parquet', index=False)
    hashes = {p.name:digest(p) for p in output.iterdir() if p.is_file() and p.name!='complete.json'}
    write(output/'complete.json', dict(status='COMPLETE', categories=len(masks), comparisons=len(comparisons),
        outcome_rows=len(ys), summary_rows=len(summary), contrast_rows=len(contrasts), hashes=hashes))
    print('ANALYSIS_COMPLETE',phase,len(masks),len(comparisons),flush=True)
