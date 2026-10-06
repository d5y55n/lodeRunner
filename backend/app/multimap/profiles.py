"""Streaming exact observed-price quarter-hour profiles; no candle-volume input."""
import argparse
import time
import zipfile
from collections import OrderedDict
import numpy as np
import pandas as pd
from app.market.phase3_archives import trade_chunks, validate_trade_chunk, month_bounds
from app.research.phase3_engine import load_coverage
from app.research.models import identity
from .contract import ROOT, PROJECT, STEPS, FINAL_START, permitted, read, sha256, write_json

SOURCE = PROJECT / 'data/phase3'
DEST = ROOT / 'trade-profiles-15m'
STEP = STEPS['15m']
DAY = 86400000
VALUES = ['quantity', 'buy', 'sell']
# Source selection only changed; aggregation semantics of these completed files are identical.
COMPATIBLE_CODE = {'e814a275017b1de64dc725b91e9bcb774de8d3b0b510f68b8eb5af002e0c44d4'}


def aggregate(frame):
    """Timestamp intervals are [start,end); buyer-is-maker means aggressive sell."""
    if frame.empty:
        return pd.DataFrame(columns=['start', 'price', *VALUES, 'delta'])
    f = frame.assign(start=frame.timestamp // STEP * STEP,
                     buy=frame.quantity.where(~frame.maker, 0.),
                     sell=frame.quantity.where(frame.maker, 0.))
    result = f.groupby(['start', 'price'], sort=True)[VALUES].sum().reset_index()
    result['delta'] = result.buy - result.sell
    return result


def combine(pieces):
    result = pd.concat(pieces).groupby(['start', 'price'], sort=True)[VALUES].sum().reset_index()
    result['delta'] = result.buy - result.sell
    return result


def bounds():
    coverage = read(ROOT / 'candles/15m/development-coverage.json')
    # Two hours before the very first decision supplies the largest native flow variant.
    return coverage['earliest_850_day_decision'] - 8 * STEP, FINAL_START


def verify_source(month, coverage):
    start, end = month_bounds(month)
    permitted(start, end)
    archive = SOURCE / 'raw/aggTrades' / f'BTCUSDT-aggTrades-{month}.zip'
    report = read(SOURCE / 'integrity' / f'{month}-aggTrades.json')
    if report.get('source_kind') == 'official_daily_collection':
        parts = report['source_parts']
        if not report['passed'] or identity(parts) != report['sha256'] or coverage['source_hashes'].get(month) != report['sha256']:
            raise ValueError('Unadjudicated daily collection')
        expected = [f'BTCUSDT-aggTrades-{pd.Timestamp(t, unit="ms", tz="UTC").strftime("%Y-%m-%d")}.zip'
                    for t in range(start, end, DAY)]
        if [s['url'].rsplit('/', 1)[-1] for s in parts] != expected:
            raise ValueError('Incomplete or reordered daily collection')
        archives = []
        for source, filename in zip(parts, expected):
            path = SOURCE / 'raw/daily-audit' / filename
            checksum = path.with_name(path.name + '.CHECKSUM').read_text().split()
            digest = sha256(path)
            if (digest != source['sha256'] or len(checksum) != 2 or checksum[0].lower() != digest
                    or checksum[1].lstrip('*') != filename):
                raise ValueError('Daily archive checksum mismatch')
            with zipfile.ZipFile(path) as z:
                if len(z.namelist()) != 1 or not z.namelist()[0].endswith('.csv'):
                    raise ValueError('Unexpected daily archive members')
            archives.append(path)
        return archives, report
    checksum = archive.with_name(archive.name + '.CHECKSUM').read_text().split()
    digest = sha256(archive)
    if (not report['passed'] or coverage['source_hashes'].get(month) != digest
            or report['sha256'] != digest or len(checksum) != 2
            or checksum[0].lower() != digest or checksum[1].lstrip('*') != archive.name):
        raise ValueError('Unadjudicated/modified source archive: ' + month)
    with zipfile.ZipFile(archive) as z:
        if len(z.namelist()) != 1 or not z.namelist()[0].endswith('.csv'):
            raise ValueError('Unexpected archive members')
    # Iterating the whole ZIP member below also enforces its CRC at EOF.
    return archive, report


def sample_gate():
    coverage = load_coverage(SOURCE)
    archive, source = verify_source('2022-01', coverage)
    frame, _, _ = validate_trade_chunk(next(trade_chunks([archive])),
                                       *month_bounds('2022-01'), allow_id_gaps=True)
    end = int(frame.timestamp.iloc[-1] // STEP * STEP)
    past = frame[frame.timestamp < end]
    quarter = aggregate(past)
    split = len(past) // 2
    chunked = combine([aggregate(past.iloc[:split]), aggregate(past.iloc[split:])])
    pd.testing.assert_frame_equal(quarter, chunked, check_exact=False, rtol=1e-12, atol=1e-9)
    for t in sorted(quarter.start.unique()):
        direct = past[(past.timestamp >= t) & (past.timestamp < t + STEP)]
        actual = quarter[quarter.start == t][VALUES].sum().to_numpy()
        expected = [direct.quantity.sum(), direct.loc[~direct.maker, 'quantity'].sum(),
                    direct.loc[direct.maker, 'quantity'].sum()]
        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-8)
    future_included = aggregate(frame)
    pd.testing.assert_frame_equal(quarter, future_included[future_included.start < end].reset_index(drop=True))
    # An independent hourly group-by must equal the sum of its quarter-hour profiles.
    direct = past.assign(hour=past.timestamp // 3600000 * 3600000).groupby(['hour', 'price']).quantity.sum()
    rebuilt = quarter.assign(hour=quarter.start // 3600000 * 3600000).groupby(['hour', 'price']).quantity.sum()
    np.testing.assert_allclose(direct, rebuilt, rtol=1e-12, atol=1e-9)
    DEST.mkdir(parents=True, exist_ok=True)
    report = dict(status='PASS', source_sha256=source['sha256'], coverage_id=coverage['coverage_id'],
                  profile_code_sha256=sha256(__file__), trades=len(past), quarter_intervals=len(quarter.start.unique()),
                  observation_start=int(past.timestamp.min()), observation_end_exclusive=end,
                  tests=['direct trade sums', 'chunk boundary invariance', 'buy/sell direction',
                         'hourly reaggregation parity', 'physical future exclusion'],
                  scope='deterministic first 500000 January 2022 trades; complete quarter intervals only')
    write_json(DEST / 'sample-gate.json', report)
    print('PROFILE_SAMPLE_PASS', report, flush=True)


def build(month):
    low, high = bounds()
    start, end = month_bounds(month)
    if start >= high or end <= low:
        raise ValueError('Outside Phase 4 required flow history')
    if start >= 1672531200000 and not (ROOT / '15m/development-freeze.json').exists():
        raise ValueError('2023 profile build waits for the completed development freeze')
    gate = read(DEST / 'sample-gate.json')
    if gate['status'] != 'PASS' or gate['profile_code_sha256'] != sha256(__file__):
        raise ValueError('Run current profile sample gate first')
    coverage = load_coverage(SOURCE)
    target = DEST / month
    target.mkdir(parents=True, exist_ok=True)
    complete = target / 'manifest.json'
    if complete.exists():
        old = read(complete)
        if (old['source_sha256'] != coverage['source_hashes'][month]
                or old['coverage_id'] != coverage['coverage_id']
                or old['profile_code_sha256'] not in COMPATIBLE_CODE | {sha256(__file__)}
                or any(sha256(target / p) != h for p, h in old['partitions'].items())):
            raise ValueError('Existing profile provenance changed')
        print('PROFILE_ALREADY_VERIFIED', month, flush=True)
        return
    before = time.perf_counter()
    archive, report = verify_source(month, coverage)
    previous = None
    carry = None
    totals = {}
    partitions = {}
    emitted_starts = []
    selected_rows = 0
    selected_quantity = 0.
    profile_quantity = 0.

    def publish(f):
        nonlocal profile_quantity
        if f.empty:
            return
        for day, part in f.groupby(f.start // DAY, sort=True):
            date = pd.Timestamp(int(day) * DAY, unit='ms', tz='UTC').strftime('%Y-%m-%d')
            path = target / (date + '.parquet')
            if path.name in partitions:
                raise AssertionError('Partition emitted twice')
            part = part.sort_values(['start', 'price']).reset_index(drop=True)
            part['end'] = part.start + STEP
            part['coverage_status'] = [
                'QUARANTINED' if any(t < b and t + STEP > a for a, b in coverage['quarantine_intervals'])
                else 'OBSERVED' for t in part.start]
            part.to_parquet(path, index=False, compression='zstd')
            partitions[path.name] = sha256(path)
            emitted_starts.extend(map(int, part.start.unique()))
            profile_quantity += float(part.quantity.sum())

    for chunk in trade_chunks(archive if isinstance(archive, list) else [archive]):
        frame, stats, previous = validate_trade_chunk(chunk, start, end, previous, allow_id_gaps=True)
        for k, v in stats.items():
            totals[k] = totals.get(k, 0) + v
        frame = frame[(frame.timestamp >= low) & (frame.timestamp < high)]
        if frame.empty:
            continue
        selected_rows += len(frame)
        selected_quantity += float(frame.quantity.sum())
        group = aggregate(frame)
        merged = combine([carry, group]) if carry is not None else group
        last_day = int(merged.start.max() // DAY)
        publish(merged[merged.start // DAY < last_day])
        carry = merged[merged.start // DAY == last_day].copy()
        write_json(target / 'progress.json', dict(month=month, source_rows=totals['rows'],
                   selected_rows=selected_rows, completed_days=len(partitions),
                   latest_timestamp=int(frame.timestamp.iloc[-1]), elapsed_seconds=time.perf_counter()-before))
    if carry is not None:
        publish(carry)
    if totals.get('rows') != report['rows']:
        raise ValueError('Source row count differs from adjudicated source')
    np.testing.assert_allclose(profile_quantity, selected_quantity, rtol=1e-11, atol=1e-7)
    expected = set(range(max(start, low), min(end, high), STEP))
    missing = sorted(expected - set(emitted_starts))
    manifest = dict(status='COMPLETE_WITH_MISSING_INTERVALS' if missing else 'COMPLETE',
                    symbol='BTCUSDT', interval_ms=STEP, price_mode='exact observed float64; no coarse bins',
                    interval_semantics='[start,end); usable only when end <= decision time',
                    source_sha256=report['sha256'], official_checksum_verified=True, zip_crc_verified=True,
                    coverage_id=coverage['coverage_id'], quarantines=coverage['quarantine_intervals'],
                    source_integrity=totals, selected_trades=selected_rows, quantity=profile_quantity,
                    observation_start=max(start, low), observation_end=min(end, high),
                    missing_intervals=missing, partitions=partitions,
                    profile_code_sha256=sha256(__file__), elapsed_seconds=time.perf_counter()-before)
    write_json(complete, manifest)
    print('PROFILE_MONTH_COMPLETE', month, selected_rows, len(partitions), len(missing), flush=True)


class Profiles15m:
    def __init__(self, root=DEST):
        self.root = root
        self.days = OrderedDict()
        self.manifests = {}

    def interval(self, start, decision_time):
        permitted(start, start + STEP)
        if start % STEP or start + STEP > decision_time or decision_time >= FINAL_START:
            raise ValueError('Future or unaligned profile')
        date = pd.Timestamp(start, unit='ms', tz='UTC').strftime('%Y-%m-%d')
        month = date[:7]
        path = self.root / month / (date + '.parquet')
        if month not in self.manifests:
            manifest_path = self.root / month / 'manifest.json'
            if not manifest_path.exists():
                return None
            self.manifests[month] = read(manifest_path)
        manifest = self.manifests[month]
        if any(start < b and start + STEP > a for a, b in manifest['quarantines']):
            return None
        if date not in self.days:
            digest = manifest['partitions'].get(path.name)
            if digest is None:
                return None
            if sha256(path) != digest:
                raise ValueError('Profile partition checksum changed')
            self.days[date] = pd.read_parquet(path)
            if len(self.days) > 3:
                self.days.popitem(last=False)
        self.days.move_to_end(date)
        f = self.days[date]
        rows = f[f.start == start]
        return None if rows.empty else rows

    def window(self, decision_time, candles):
        if candles not in [1, 4, 8]:
            raise ValueError('Undeclared flow window')
        pieces = [self.interval(t, decision_time)
                  for t in range(decision_time - candles * STEP, decision_time, STEP)]
        if any(p is None for p in pieces):
            return None
        result = pd.concat(pieces).groupby('price', sort=True)[VALUES].sum().reset_index()
        result['delta'] = result.buy - result.sell
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['gate', 'development', 'replication'])
    args = parser.parse_args()
    if args.action == 'gate':
        sample_gate()
    else:
        for m in range(1, 13):
            build(f'{2022 if args.action == "development" else 2023}-{m:02d}')
