"""Native full-map price research, independent from the trade-profile build."""
import argparse
from bisect import bisect_right
from dataclasses import asdict
from itertools import product
import time
import pandas as pd
from app.fullmap_scale.storage import Stream, catalog
from app.fullmap.run import peak_memory
from app.research.outcomes import measure
from .contract import *
from .data import load
from .engine import Engine


def key(name, parameters):
    return name + ('_' + '_'.join(f'{k}-{v}' for k, v in sorted(parameters.items())) if parameters else '')


def normalized(snapshot):
    raw = snapshot['raw']; native = snapshot['native_score'] or {}
    total = snapshot['support_count'] + snapshot['resistance_count']
    nearby_s = raw['support']['density']['inner'] + raw['support']['density']['outer']
    nearby_r = raw['resistance']['density']['inner'] + raw['resistance']['density']['outer']
    row = {k: snapshot[k] for k in ['snapshot_id', 'event_id', 'symbol', 'timeframe',
        'decision_timestamp', 'last_closed_candle_end', 'decision_price', 'lookback_start', 'lookback_end',
        'detector', 'configuration_id', 'support_count', 'resistance_count', 'price_coverage_complete']}
    row.update(A1=native.get('long_score'), A2=native.get('full_weight_only_long'),
        imbalance=(nearby_s-nearby_r)/(nearby_s+nearby_r) if nearby_s+nearby_r else None,
        full_map_imbalance=(snapshot['support_count']-snapshot['resistance_count'])/total if total else None,
        nearby_support_count=nearby_s, nearby_resistance_count=nearby_r,
        nearby_count=nearby_s+nearby_r, cluster_count=raw['cluster_count'],
        candidates_per_cluster=total/raw['cluster_count'] if raw['cluster_count'] else None,
        overlap_pair_count=raw['overlap_pair_count'],
        quantity=None, delta=None, flow_status='PENDING_SEPARATE_TRADE_ATTACHMENT',
        D_status='OBSERVED_ONLY_NOT_850_DAY_COMPLETE', crossings_status='PENDING_CAUSAL_EXPLANATORY_PASS')
    for side in ['support', 'resistance']:
        row['nearest_'+side+'_distance'] = raw[side]['nearest_signed_distance_fraction']
        for field in ['above', 'below', 'near']:
            row[side+'_'+field] = raw[side][field]
        for field, value in raw[side]['density'].items():
            row[side+'_density_'+field] = value
    for field in ['min', 'median', 'mean', 'max']:
        row['nearby_age_'+field+'_hours'] = (raw['nearby_age_hours'] or {}).get(field)
    return row


def outcomes(candles, t, tf, event_id, phase_end):
    right = bisect_right([c.end for c in candles], t)
    future = [c for c in candles[right:right+max(HORIZONS[tf])] if c.end <= phase_end]
    price = candles[right-1].close
    return [dict(event_id=event_id, decision_timestamp=t, timeframe=tf,
                 elapsed_horizon_hours=h*STEPS[tf]/HOUR,
                 **asdict(measure(price, t, future, direction, tp, sl, h)))
            for direction, tp, sl, h in product(['LONG','SHORT'], [.003,.005], [.003,.005], HORIZONS[tf])]


def execute(tf, phase):
    initialize()
    if phase=='replication':
        from .freeze import check
        from .profile_coverage import audit
        check(tf)
        audit(phase)
    gate = read(ROOT/tf/'parity.json')
    if gate['status'] != 'PASS':raise ValueError('Native parity required')
    for name, digest in gate['code'].items():
        if sha256(Path(__file__).parent/name) != digest:raise ValueError('Native parity code changed')
    if tf == '15m' and read(ROOT/tf/'benchmark.json')['status'] != 'PASS':
        raise ValueError('Benchmark required')
    if phase == 'replication' and not (ROOT/tf/'development-freeze.json').exists():
        raise ValueError('Development analysis and frozen buckets required first')
    dest = ROOT/tf/phase
    if (dest/'price-complete.json').exists():raise ValueError('Completed output is immutable')
    dest.mkdir(parents=True, exist_ok=True)
    start_clock = time.perf_counter()
    cs = load(tf, replication=phase=='replication'); engine = Engine(cs, tf)
    start = cs[0].start + LOOKBACK if phase=='development' else 1672531200000
    end = 1672531200000 if phase=='development' else FINAL_START
    writers = {key(n,p):Stream(dest/key(n,p)) for n,p in CONFIGS}
    for folder in ['normalized', 'future-outcomes']:(dest/folder).mkdir(exist_ok=True)
    rows = []; labels = []; current_day = None; count = 0; hashes = {}
    ends = engine.reference.ends

    def flush():
        if not rows:return
        for folder, records in [('normalized', rows), ('future-outcomes', labels)]:
            path = dest/folder/(current_day+'.parquet')
            pd.DataFrame(records).to_parquet(path, index=False, compression='zstd')
            hashes[str(path.relative_to(dest))] = sha256(path)
        for writer in writers.values():writer.flush()
        write_json(dest/'price-progress.json', dict(timeframe=tf, phase=phase, timestamps=count,
            last_completed_day=current_day, elapsed_seconds=time.perf_counter()-start_clock,
            status='RUNNING_PRICE_ONLY', no_2024=True))
        rows.clear(); labels.clear()

    for t in range(start, end, STEPS[tf]):
        day = pd.Timestamp(t, unit='ms', tz='UTC').strftime('%Y-%m-%d')
        if current_day != day:
            flush(); current_day = day
        eid = None
        for name, params in CONFIGS:
            snapshot, members = engine.snapshot(t, name, params)
            writers[key(name, params)].add(snapshot, members)
            rows.append(normalized(snapshot)); eid = snapshot['event_id']
        right = bisect_right(ends, t)
        # The local slice keeps label generation independent of total history length.
        labels.extend(outcomes(cs[right-1:right+max(HORIZONS[tf])], t, tf, eid, end))
        count += 1
        if count % 1000 == 0:print('NATIVE_PRICE_PROGRESS', tf, phase, count, flush=True)
    flush()
    catalog(dest, engine)
    for p in dest.rglob('*.parquet'):
        hashes[str(p.relative_to(dest))] = sha256(p)
    write_json(dest/'price-complete.json', dict(status='PRICE_MAP_COMPLETE_FLOW_ANALYSIS_PENDING',
        timeframe=tf, phase=phase, timestamps=count, states=count*len(CONFIGS), outcomes=count*24,
        first_decision=start, end_exclusive=end, one_native_candle_stride=STEPS[tf],
        runtime_seconds=time.perf_counter()-start_clock, peak_RAM_bytes=peak_memory(),
        output_bytes=sum(p.stat().st_size for p in dest.rglob('*.parquet')),
        hashes=hashes, code_sha256=sha256(__file__), no_2024=True))
    print('NATIVE_PRICE_COMPLETE', tf, phase, count, flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('timeframe',choices=list(HORIZONS))
    p.add_argument('phase',choices=['development','replication']);a=p.parse_args();execute(a.timeframe,a.phase)
