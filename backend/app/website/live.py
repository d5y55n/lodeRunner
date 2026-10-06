"""Operational-only USD-M cache. Never reads or writes frozen research archives."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import sqlite3
import threading
import time

import httpx
import pandas as pd

from .config import PROJECT, STEPS, DAY, settings
from .market import COLUMNS, validate


def now_ms():
    return int(datetime.now(timezone.utc).timestamp()*1000)


def bounds(tf, decision, cfg):
    step = STEPS[tf]
    end = decision//step*step
    start = (end-max(cfg.history_days, cfg.converging_history_days)*DAY-(2*max(cfg.swing_ns.values())+3)*step)//step*step
    return start, end


class CoverageError(ValueError):
    pass


class PublicFeed:
    _request_lock = threading.Lock()
    _next_request = 0.0
    _blocked_until = 0.0

    def __init__(self, symbol='BTCUSDT'):
        self.symbol = symbol
        self.client = httpx.Client(base_url='https://fapi.binance.com', timeout=20)

    def get(self, path, **params):
        with PublicFeed._request_lock:
            time.sleep(max(0, max(PublicFeed._next_request, PublicFeed._blocked_until)-time.monotonic()))
            PublicFeed._next_request = time.monotonic()+.3
        r = self.client.get(path, params=params)
        if r.status_code in (418, 429):
            with PublicFeed._request_lock:
                PublicFeed._blocked_until = time.monotonic()+max(60, float(r.headers.get('Retry-After', 60)))
        r.raise_for_status()
        return r.json()

    def ticker(self):
        # Exchange time, not the workstation clock, determines closed candles.
        server = int(self.get('/fapi/v1/time')['serverTime'])
        tick = self.get('/fapi/v2/ticker/price', symbol=self.symbol)
        price, stamp = float(tick['price']), int(tick['time'])
        if not math.isfinite(price) or price <= 0 or stamp <= 0 or stamp > server+10000:
            raise ValueError('Invalid ticker')
        return dict(price=price, timestamp=stamp, server_timestamp=server)

    def candles(self, tf, start, end):
        raw = self.get('/fapi/v1/klines', symbol=self.symbol, interval=tf,
                       startTime=start, endTime=end-1, limit=1000)
        return pd.DataFrame([dict(zip(COLUMNS, [r[0], r[1], r[2], r[3], r[4], r[6]])) for r in raw], columns=COLUMNS)

    def close(self):
        self.client.close()


class Store:
    def __init__(self, root=None, symbol='BTCUSDT'):
        self.symbol = symbol
        base = PROJECT/'data/live-dashboard'
        self.root = root or (base if symbol == 'BTCUSDT' else base/'symbols'/hashlib.sha256(symbol.encode()).hexdigest()[:24])
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root/'dashboard.sqlite3'
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS candles (
                    tf TEXT, open_time INTEGER, open REAL, high REAL, low REAL,
                    close REAL, close_time INTEGER, PRIMARY KEY(tf,open_time));
                CREATE TABLE IF NOT EXISTS acquisition (
                    id INTEGER PRIMARY KEY, tf TEXT, start INTEGER, end INTEGER,
                    rows INTEGER, received_at INTEGER, sha256 TEXT, source TEXT);
                CREATE TABLE IF NOT EXISTS snapshots (
                    timestamp INTEGER, config_hash TEXT, calculated_at INTEGER,
                    payload TEXT, sha256 TEXT, PRIMARY KEY(timestamp,config_hash));
            ''')
            # Each database is bound to one symbol. Migration is additive and
            # transactional; legacy BTC payloads/checksums remain unchanged.
            db.execute('CREATE TABLE IF NOT EXISTS identity(symbol TEXT PRIMARY KEY)')
            identity = db.execute('SELECT symbol FROM identity').fetchall()
            if identity and identity != [(symbol,)]:
                raise CoverageError('Database symbol mismatch')
            if not identity and symbol != 'BTCUSDT' and db.execute('SELECT 1 FROM candles LIMIT 1').fetchone():
                raise CoverageError('Legacy BTC database cannot be relabeled')
            db.execute('INSERT OR IGNORE INTO identity VALUES(?)', (symbol,))
            for table in ('candles', 'acquisition', 'snapshots'):
                columns = {r[1] for r in db.execute(f'PRAGMA table_info({table})')}
                if 'symbol' not in columns:
                    db.execute(f'ALTER TABLE {table} ADD COLUMN symbol TEXT')
                    db.execute(f'UPDATE {table} SET symbol=?', (symbol,))
            db.execute('CREATE UNIQUE INDEX IF NOT EXISTS candles_symbol_time ON candles(symbol,tf,open_time)')
            db.execute('CREATE UNIQUE INDEX IF NOT EXISTS snapshots_symbol_time ON snapshots(symbol,timestamp,config_hash)')
            db.execute('CREATE INDEX IF NOT EXISTS acquisition_symbol_time ON acquisition(symbol,tf,start)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            db.execute('PRAGMA journal_mode=WAL')
            with db:
                yield db
        finally:
            db.close()

    def read(self, tf, start, end):
        with self.connect() as db:
            return pd.read_sql_query('SELECT open_time,open,high,low,close,close_time FROM candles WHERE tf=? AND open_time>=? AND close_time<? ORDER BY open_time', db, params=(tf,start,end))

    def insert(self, tf, frame, end):
        f = validate(frame, tf)
        if (f.close_time >= end).any():
            raise CoverageError('Open candle rejected')
        with self.connect() as db:
            old = db.execute('SELECT MAX(open_time) FROM candles WHERE tf=?', (tf,)).fetchone()[0]
            if old is not None and int(f.open_time.iloc[0]) > old+STEPS[tf]:
                raise CoverageError('Gap before received page')
            for row in f.itertuples(index=False, name=None):
                previous = db.execute('SELECT open_time,open,high,low,close,close_time FROM candles WHERE tf=? AND open_time=?', (tf,int(row[0]))).fetchone()
                if previous is not None:
                    if tuple(row) != previous:
                        raise CoverageError('Conflicting closed candle; cache not overwritten')
                    continue  # An identical retry is idempotent, not a second candle.
                db.execute('INSERT INTO candles(tf,open_time,open,high,low,close,close_time,symbol) VALUES (?,?,?,?,?,?,?,?)', (tf,*row,self.symbol))
            digest = hashlib.sha256(f.to_json(orient='records').encode()).hexdigest()
            db.execute('INSERT INTO acquisition(tf,start,end,rows,received_at,sha256,source,symbol) VALUES(?,?,?,?,?,?,?,?)',
                       (tf,int(f.open_time.iloc[0]),int(f.close_time.iloc[-1])+1,len(f),now_ms(),digest,'https://fapi.binance.com/fapi/v1/klines',self.symbol))

    def ensure(self, tf, start, end, feed, progress=lambda *args: None):
        f = self.read(tf, start, end)
        cursor = start
        if not f.empty:
            f = validate(f, tf)
            if int(f.open_time.iloc[0]) != start:
                raise CoverageError('HISTORY_INCOMPLETE: cached history starts after requested start')
            cursor = int(f.close_time.iloc[-1])+1
        while cursor < end:
            page = feed.candles(tf, cursor, end)
            if page.empty:
                raise CoverageError('HISTORY_INCOMPLETE: empty REST page')
            page = validate(page, tf)
            if int(page.open_time.iloc[0]) != cursor or int(page.close_time.iloc[-1]) >= end:
                raise CoverageError('HISTORY_INCOMPLETE: gap or open candle in REST page')
            self.insert(tf, page, end)
            cursor = int(page.close_time.iloc[-1])+1
            progress(tf, cursor, end)
            time.sleep(.15)
        return self.load(tf, start, end)

    def load(self, tf, start, end):
        f = self.read(tf, start, end)
        if f.empty:
            raise CoverageError('HISTORY_INCOMPLETE: no cached candles')
        f = validate(f, tf)
        if int(f.open_time.iloc[0]) != start or int(f.close_time.iloc[-1])+1 != end:
            raise CoverageError('HISTORY_INCOMPLETE: full configured lookback required')
        return f

    def save(self, snapshot):
        if snapshot.get('symbol') != self.symbol:
            raise CoverageError('Snapshot symbol mismatch')
        raw = json.dumps(snapshot, sort_keys=True, allow_nan=False)
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO snapshots(timestamp,config_hash,calculated_at,payload,sha256,symbol) VALUES(?,?,?,?,?,?)',
                       (snapshot['timestamp'],snapshot['config_hash'],snapshot['calculated_timestamp'],raw,hashlib.sha256(raw.encode()).hexdigest(),self.symbol))

    def history(self, limit=30, config_hash=None):
        with self.connect() as db:
            rows = db.execute('SELECT payload,sha256 FROM snapshots WHERE (? IS NULL OR config_hash=?) ORDER BY timestamp DESC LIMIT ?', (config_hash,config_hash,limit)).fetchall()
        result = []
        for raw, digest in rows:
            if hashlib.sha256(raw.encode()).hexdigest() != digest:
                raise CoverageError('Snapshot checksum mismatch')
            snapshot = json.loads(raw)
            if snapshot.get('symbol') != self.symbol:
                raise CoverageError('Snapshot symbol mismatch')
            result.append(snapshot)
        return result


class Dashboard:
    download_slot = threading.BoundedSemaphore(1)

    def __init__(self, store=None, feed_factory=None, cfg=None, symbol='BTCUSDT', onboard=0):
        self.symbol = symbol
        self.onboard = onboard
        self.store = store or Store(symbol=symbol)
        if self.store.symbol != symbol:
            raise CoverageError('Store symbol mismatch')
        self.cfg = cfg or settings()
        self.feed_factory = feed_factory or (lambda: PublicFeed(symbol))
        self.last_active = time.monotonic()
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='dashboard-analysis')
        self.thread = None
        self.future = None
        self.ticker = None
        self.received_at = None
        self.received_mono = None
        self.connection = 'CONNECTING'
        self.analysis_status = 'HISTORY_INCOMPLETE'
        self.error = None
        self.progress = None
        self.snapshot = None
        self.retry_after = 0
        self.replay_lock = threading.Lock()
        self.replay_cache = {}
        # Restore checksummed state as stale until history and exchange time verify it.
        latest = self.store.history(1, hashlib.sha256(self.cfg.model_dump_json().encode()).hexdigest())
        if latest:
            self.snapshot = latest[0]
            self.analysis_status = 'STALE'
        self.verified_decision = None

    def start(self):
        with self.lock:
            self.last_active = time.monotonic()
            if self.thread is None:
                self.thread = threading.Thread(target=self.run, daemon=True, name='dashboard-ticker')
                self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=25)
        self.pool.shutdown(wait=True)

    def run(self):
        feed = self.feed_factory()
        failures = 0
        try:
            while not self.stop_event.is_set():
                if time.monotonic()-self.last_active > 30:
                    self.stop_event.wait(1)
                    continue
                try:
                    tick = feed.ticker()
                    with self.lock:
                        if self.ticker and tick['server_timestamp'] < self.ticker['server_timestamp']:
                            raise ValueError('Server clock moved backwards')
                        self.ticker, self.received_at, self.received_mono = tick, now_ms(), time.monotonic()
                        self.connection = 'CONNECTED'
                        decision = tick['server_timestamp']//STEPS['15m']*STEPS['15m']
                        if decision != self.verified_decision and (self.future is None or self.future.done()) and time.monotonic() >= self.retry_after:
                            self.analysis_status = 'UPDATING' if self.snapshot else 'HISTORY_INCOMPLETE'
                            self.future = self.pool.submit(self.update, decision)
                    failures = 0
                except Exception as exc:
                    failures += 1
                    with self.lock:
                        self.connection, self.error = 'DISCONNECTED', str(exc)
                self.stop_event.wait(min(60, 3*2**min(failures,4)))
        finally:
            feed.close()

    def update(self, decision):
        if not self.download_slot.acquire(blocking=False):
            self.progress = dict(queued=True, missing_timeframes=list(STEPS))
            self.retry_after = time.monotonic()+3
            return
        feed = None
        try:
            feed = self.feed_factory()
            # Hard operational disk budget, without deleting any existing data.
            root = PROJECT/'data/live-dashboard'
            if sum(p.stat().st_size for p in root.rglob('*.sqlite3*')) > 8*1024**3:
                raise OSError('Operational cache exceeds 8 GiB; free space or archive it before retrying')
            frames = {}
            missing = [tf for tf in STEPS if self.onboard > bounds(tf,decision,self.cfg)[0]]
            if missing:
                raise CoverageError('HISTORY_INCOMPLETE: listing too recent for full lookback: '+','.join(missing))
            for tf in STEPS:
                if self.stop_event.is_set():
                    return
                start, end = bounds(tf, decision, self.cfg)
                # Extra storage enables 30 days of navigation; analysis still uses
                # exactly the original configured 850-day window plus warmup.
                cache_start = max(start-30*DAY, ((self.onboard+STEPS[tf]-1)//STEPS[tf])*STEPS[tf]) if self.onboard else start-30*DAY
                self.progress_start = cache_start
                self.prepared = list(frames)
                self.store.ensure(tf, cache_start, end, feed, self.set_progress)
                frames[tf] = self.store.load(tf, start, end)
            with self.lock:
                if self.snapshot and self.snapshot['timestamp'] == decision:
                    self.verified_decision = decision
                    self.analysis_status, self.error, self.progress = 'READY', None, None
                    return
            from .api import evaluate_frames
            result = evaluate_frames('live',decision,self.cfg.model_dump_json(),frames,
                                     {tf:[str(self.store.path)] for tf in STEPS}, symbol=self.symbol)
            result.update(source_timestamp=decision, calculated_timestamp=now_ms(), freshness='FRESH',
                          native_closed_at={tf:int(f.close_time.iloc[-1])+1 for tf,f in frames.items()})
            with self.lock:
                result['live_price_at_calculation'] = deepcopy(self.ticker)
            from .scoring_distribution import attach
            result = attach(result,self.store,self.cfg)
            self.store.save(result)
            with self.lock:
                self.snapshot, self.verified_decision = result, decision
                self.analysis_status, self.error, self.progress = 'READY', None, None
        except Exception as exc:
            with self.lock:
                self.analysis_status = 'HISTORY_INCOMPLETE' if isinstance(exc, (ValueError, CoverageError)) else 'DISCONNECTED'
                self.error, self.retry_after = str(exc), time.monotonic()+60
        finally:
            if feed is not None:
                feed.close()
            self.download_slot.release()

    def set_progress(self, tf, cursor, end):
        if self.stop_event.is_set() or time.monotonic()-self.last_active > 30:
            raise RuntimeError('Dashboard stopping')
        with self.lock:
            self.progress = dict(timeframe=tf, loaded_through=cursor, required_through=end,
                                 percent=round(100*(len(self.prepared)+(cursor-self.progress_start)/(end-self.progress_start))/len(STEPS),1),
                                 prepared_timeframes=self.prepared, missing_timeframes=[x for x in STEPS if x not in self.prepared])

    def status(self):
        with self.lock:
            age = time.monotonic()-self.received_mono if self.received_mono is not None else None
            server = self.ticker['server_timestamp']+int(age*1000) if self.ticker and age is not None else None
            decision = server//STEPS['15m']*STEPS['15m'] if server else None
            ticker_age = (server-self.ticker['timestamp'])/1000 if server and self.ticker else None
            fresh = self.connection == 'CONNECTED' and age is not None and age < 15 and ticker_age is not None and ticker_age < 15
            from .scoring_distribution import attach
            snap = attach(self.snapshot,self.store,self.cfg)
            if snap:
                snap['freshness'] = 'FRESH' if fresh and self.verified_decision == decision and self.analysis_status == 'READY' else 'STALE'
            return dict(symbol=self.symbol, connection=self.connection if fresh else 'DISCONNECTED' if self.ticker else self.connection,
                        ticker=deepcopy(self.ticker), market_received_at=self.received_at, market_age_seconds=age,
                        analysis_status=self.analysis_status, progress=deepcopy(self.progress), error=self.error,
                        snapshot=snap, server_timestamp=server, response_timestamp=now_ms())

    def replay(self, decision):
        # Bounded operational replay: never fetch unknown years or expand the cache.
        with self.replay_lock:
            if decision in self.replay_cache:
                from .scoring_distribution import attach
                return attach(self.replay_cache[decision],self.store,self.cfg)
            frames = {tf:self.store.load(tf,*bounds(tf,decision,self.cfg)) for tf in STEPS}
            from .api import evaluate_frames
            result = evaluate_frames('replay',decision,self.cfg.model_dump_json(),frames,
                                     {tf:[str(self.store.path)] for tf in STEPS}, symbol=self.symbol)
            result.update(source_timestamp=decision, calculated_timestamp=now_ms(), freshness='REPLAY',
                          native_closed_at={tf:int(f.close_time.iloc[-1])+1 for tf,f in frames.items()})
            if len(self.replay_cache) >= 4:
                self.replay_cache.pop(next(iter(self.replay_cache)))
            self.replay_cache[decision] = result
            from .scoring_distribution import attach
            return attach(result,self.store,self.cfg)
