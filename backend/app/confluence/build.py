"""Reconstruct only frozen nearby intervals; never rerun any detector or outcome."""
import json
from itertools import product
import numpy as np
import pandas as pd
from app.fullmap_scale.storage import restore
from .contract import *
from .geometry import nearby, union, intersect, distance, latest_indices, sign


def hourly_flow(v):
    row = {name:v[name] for name in ['observation_start','observation_end']}
    row['flow_status']=v['status']
    for side in ['support','resistance','joint']:
        values=v[side]
        if values is None and v['status']=='AVAILABLE':
            raise ValueError('Available flow cannot have missing side totals')
        for field in ['quantity','delta','normalized_delta','buy','sell']:
            row[side+'_'+field]=None if values is None else values[field]
    return row


def native(sources, tf):
    phase = sources.phase
    if tf == '1h':
        base = PROJECT / 'data/phase3r1' / phase
        folder = base / '1d8c70797dfb'
        cat_path = base / 'catalog-A/candidate-catalog.parquet'
    else:
        base = PROJECT / 'data/phase4' / tf / phase
        folder = base / 'A'
        cat_path = base / 'candidate-catalog.parquet'
    cat = sources.frame(cat_path).set_index('candidate_index')
    cat = cat.reindex(range(int(cat.index.max()) + 1))
    prices, kinds, known = cat.price.to_numpy(), cat.kind.to_numpy(), cat.known_at.to_numpy()
    rows = []
    for di, path in enumerate(sorted(folder.glob('*-states.parquet'))):
        states = sources.frame(path)
        timestamp_guard(states.decision_timestamp.to_numpy(), phase)
        memberships = list(restore(sources.frame(path.with_name(path.name.replace('-states', '-membership')))))
        if len(states) != len(memberships):
            raise ValueError('Membership length')
        extra = None
        if tf != '1h':
            extra = sources.frame(base / 'native-states' / (path.name[:10] + '.parquet'))
            extra = extra[extra.detector == 'A'].set_index('snapshot_id')
        for state, (sid, idx) in zip(states.to_dict('records'), memberships):
            t, price = state['decision_timestamp'], state['decision_price']
            if sid != state['snapshot_id'] or state['detector'] != 'A' or not np.all(known[idx] <= t):
                raise ValueError('Native membership leakage/identity')
            if not state['price_coverage_complete'] or state['lookback_end'] != t or t - state['lookback_start'] != 850 * 86400000:
                raise ValueError('Native coverage/window changed')
            score, raw = json.loads(state['native_score']), json.loads(state['raw'])
            selected = idx[nearby(prices[idx], price, WIDTHS[tf])]
            s = int(np.sum(kinds[selected] == 'SUPPORT'))
            r = int(np.sum(kinds[selected] == 'RESISTANCE'))
            if (s, r) != (score['support_contribution_count'], score['resistance_contribution_count']):
                raise ValueError('Nearby membership parity failed')
            row = dict(source_timestamp=t, snapshot_id=sid, event_id=state['event_id'], source_price=price,
                       A1=score['long_score'], A2=score['full_weight_only_long'],
                       imbalance=(s-r)/(s+r) if s+r else None,
                       support_count=state['support_count'], resistance_count=state['resistance_count'],
                       nearby_support_count=s, nearby_resistance_count=r, coverage_complete=True)
            for side, kind in [('support', 'SUPPORT'), ('resistance', 'RESISTANCE')]:
                ids = selected[kinds[selected] == kind]
                intervals = [[float(prices[i]*(1-WIDTHS[tf])), float(prices[i]*(1+WIDTHS[tf])), int(i)] for i in ids]
                row[side+'_intervals'] = canonical(intervals)
                row[side+'_union'] = canonical(union([x[:2] for x in intervals]))
                row['nearest_'+side] = raw[side]['nearest_price']
                row['nearest_'+side+'_native_distance'] = raw[side]['nearest_signed_distance_fraction']
            for name in ['A1', 'A2', 'imbalance']:
                row[name+'_sign'] = sign(row[name])
            row['map_state'] = dict(S='support-heavy', R='resistance-heavy', N='balanced', M='missing')[row['imbalance_sign']]
            a, b = raw['support']['nearest_absolute_distance_fraction'], raw['resistance']['nearest_absolute_distance_fraction']
            row['nearest_geometry'] = 'MISSING' if a is None or b is None else 'SUPPORT_CLOSER' if a < b else 'RESISTANCE_CLOSER' if b < a else 'TIE'
            if tf == '1h':
                v = json.loads(state['volume'])
                row.update(hourly_flow(v))
            else:
                v = extra.loc[sid]
                for name in ['flow_status', 'observation_start', 'observation_end']:
                    row[name] = v[name]
                for side in ['support', 'resistance', 'joint']:
                    for field in ['quantity', 'delta', 'normalized_delta', 'buy', 'sell']:
                        row[side+'_'+field] = v[side+'_'+field]
            if row['observation_end'] != t:
                raise ValueError('Future flow')
            rows.append(row)
        if (di+1) % 90 == 0:
            print('NATIVE_EXPORT', phase, tf, di+1, flush=True)
    result = pd.DataFrame(rows).sort_values('source_timestamp').reset_index(drop=True)
    if result.source_timestamp.duplicated().any() or not np.all(np.diff(result.source_timestamp) == STEPS[tf]):
        raise ValueError('Native cadence gap')
    out = ROOT / phase / 'native'
    out.mkdir(parents=True, exist_ok=True)
    result.to_parquet(out / (tf+'.parquet'), index=False, compression='zstd')
    return result


def alignment_audit(frames, decisions):
    rows = []
    times = decisions.decision_timestamp.to_numpy()
    chosen = set(np.linspace(0, len(times)-1, 64, dtype=int))
    for step in STEPS.values():
        boundaries = np.flatnonzero(times % step == 0)
        for i in boundaries[np.linspace(0, len(boundaries)-1, min(12, len(boundaries)), dtype=int)]:
            chosen.update(j for j in (i-1, i, i+1) if 0 <= j < len(times))
    for tf, f in frames.items():
        ts = f.source_timestamp.to_numpy()
        index, valid = latest_indices(ts, times, STEPS[tf])
        for i in sorted(chosen):
            t = int(times[i]); truncated = ts[ts <= t]
            ti, tv = latest_indices(truncated, [t], STEPS[tf])
            if not valid[i] or not tv[0] or ts[index[i]] != truncated[ti[0]]:
                raise ValueError('Alignment truncation failure')
            rows.append(dict(T=t, timeframe=tf, source_timestamp=int(ts[index[i]]),
                             age_ms=int(t-ts[index[i]]), truncation_equal=True))
        changed = np.flatnonzero(np.diff(index) != 0) + 1
        if np.any(times[changed] % STEPS[tf]):
            raise ValueError('Held state changed before native close')
    return pd.DataFrame(rows)


def overlap_rows(t, price, states):
    features = {}
    details = []
    for side in ['support', 'resistance']:
        unions = {tf: json.loads(states[tf][side+'_union']) for tf in TFS}
        intervals = {tf: json.loads(states[tf][side+'_intervals']) for tf in TFS}
        maximum = 0
        best = []
        for subset in SUBSETS:
            region = unions[subset[0]]
            for tf in subset[1:]:
                region = intersect(region, unions[tf])
            name = '+'.join(subset)
            features[side+'_overlap_'+name] = bool(region)
            if region and len(subset) >= maximum:
                if len(subset) > maximum:
                    best = []
                maximum = len(subset)
                best.append(name)
            for component, (low, high) in enumerate(region):
                count_by_tf = {tf: sum(x[0] <= high and x[1] >= low for x in intervals[tf]) for tf in subset}
                details.append(dict(decision_timestamp=t, side=side, combination=name,
                    timeframe_count=len(subset), component=component, lower=low, upper=high,
                    width=high-low, price_distance=distance(price, low, high),
                    price_distance_fraction=distance(price, low, high)/price,
                    candidate_interval_count=sum(count_by_tf.values()), candidate_counts=canonical(count_by_tf)))
        features[side+'_overlap_count'] = maximum
        features[side+'_overlap_identities'] = '|'.join(best)
        maximal = [r for r in details if r['side'] == side and r['timeframe_count'] == maximum]
        features[side+'_common_regions'] = canonical([{k: r[k] for k in ['combination', 'lower', 'upper', 'width', 'price_distance', 'candidate_interval_count']} for r in maximal])
    return features, details


def execute(phase):
    initialize(); sources = Sources(phase)
    dest = ROOT / phase
    dest.mkdir(exist_ok=True)
    if (dest/'build-complete.json').exists():
        return
    frames = {}
    for tf in TFS:
        frames[tf] = native(sources, tf)
    low = frames['15m']
    times = low.source_timestamp.to_numpy()
    indices = {}; valid = np.ones(len(times), dtype=bool)
    for tf in TFS:
        idx, ok = latest_indices(frames[tf].source_timestamp, times, STEPS[tf])
        indices[tf] = idx; valid &= ok
    excluded = pd.DataFrame(dict(decision_timestamp=times[~valid], reason='NO_COMPLETE_NATIVE_SOURCE'))
    excluded.to_csv(dest/'ineligible.csv', index=False)
    if not valid.all():
        raise ValueError('Unexpected missing native source; inspect before excluding')
    rows = []; details = []
    records = {tf: f.to_dict('records') for tf, f in frames.items()}
    (dest/'states').mkdir(exist_ok=True); (dest/'overlaps').mkdir(exist_ok=True)
    day = None
    def flush():
        if rows:
            pd.DataFrame(rows).to_parquet(dest/'states'/(day+'.parquet'), index=False, compression='zstd')
            pd.DataFrame(details).to_parquet(dest/'overlaps'/(day+'.parquet'), index=False, compression='zstd')
            rows.clear(); details.clear()
    for i, t in enumerate(times):
        current_day = pd.Timestamp(t, unit='ms', tz='UTC').strftime('%Y-%m-%d')
        if day != current_day:
            flush(); day = current_day
        states = {tf: records[tf][indices[tf][i]] for tf in TFS}
        row = dict(decision_timestamp=int(t), decision_price=states['15m']['source_price'], event_id=states['15m']['event_id'])
        for tf, s in states.items():
            for field, v in s.items():
                # Original candidate intervals are normalized by snapshot in native/*.parquet.
                if not field.endswith('_intervals'):
                    row[tf+'__'+field] = v
            row[tf+'__source_age_ms'] = int(t-s['source_timestamp'])
            row[tf+'__interval_reference'] = f'native/{tf}.parquet#{s["snapshot_id"]}'
        for descriptor in ['imbalance', 'A1', 'A2']:
            pattern = ''.join(states[tf][descriptor+'_sign'] for tf in TFS)
            row[descriptor+'_pattern'] = pattern
            for label, char in [('support', 'S'), ('resistance', 'R'), ('neutral', 'N'), ('missing', 'M')]:
                row[descriptor+'_'+label+'_count'] = pattern.count(char)
        pattern = row['imbalance_pattern']
        row['conflict_pattern'] = pattern[:2] + '/' + pattern[2:]
        for field in ['joint_quantity', 'support_normalized_delta', 'resistance_normalized_delta', 'joint_delta', 'support_delta', 'resistance_delta', 'flow_status']:
            row[field] = states['15m'][field]
        f, d = overlap_rows(int(t), row['decision_price'], states)
        row.update(f); rows.append(row); details.extend(d)
        if (i+1) % 5000 == 0:
            print('CONFLUENCE_BUILD', phase, i+1, len(times), flush=True)
    flush()
    audit = alignment_audit(frames, pd.DataFrame({'decision_timestamp': times}))
    audit.to_csv(dest/'alignment-audit.csv', index=False)
    sources.save()
    hashes = {str(p.relative_to(dest)): digest(p) for folder in ['native', 'states', 'overlaps'] for p in (dest/folder).glob('*.parquet')}
    write(dest/'build-complete.json', dict(status='COMPLETE', timestamps=len(times), first=int(times[0]),
        last=int(times[-1]), alignment_checks=len(audit), hashes=hashes, no_2024=True))
    print('BUILD_COMPLETE', phase, len(times), flush=True)
