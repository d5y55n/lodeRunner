"""Read-only native replay, and an explicit public REST live mode."""
from functools import lru_cache
from datetime import datetime, timezone
import time
import numpy as np
import pandas as pd
from .config import PROJECT, STEPS, DAY

COLUMNS = ["open_time", "open", "high", "low", "close", "close_time"]
FORBIDDEN_START = 1704067200000
FORBIDDEN_END = 1735689600000


def no_2024(start, end):
    if start < FORBIDDEN_END and end > FORBIDDEN_START:
        raise ValueError("2024 is reserved. This history request intersects 2024; no data was read. Configure an explicit shorter history or use 2023 replay.")


def timestamp(value):
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("Timestamp must include UTC offset")
    return int(d.timestamp()*1000)


def validate(frame, tf):
    f = frame[COLUMNS].copy()
    for col in COLUMNS:
        f[col] = pd.to_numeric(f[col], errors="raise")
    if f.empty or not np.isfinite(f.to_numpy()).all():
        raise ValueError("Empty/nonfinite candle data")
    for col in ["open_time", "close_time"]:
        if not f[col].eq(f[col].astype('int64')).all():
            raise ValueError("Fractional timestamp")
        f[col] = f[col].astype('int64')
    step = STEPS[tf]
    if not f.open_time.diff().dropna().eq(step).all() or (f.open_time % step).any():
        raise ValueError("Gap, duplicate or unordered native candles; no silent repair")
    if not f.close_time.eq(f.open_time+step-1).all():
        raise ValueError("Invalid close clock")
    if (f[["open", "high", "low", "close"]] <= 0).any().any() or not (f.high >= f[["open", "close", "low"]].max(axis=1)).all() or not (f.low <= f[["open", "close"]].min(axis=1)).all():
        raise ValueError("Invalid OHLC")
    return f.reset_index(drop=True)


@lru_cache(maxsize=128)
def read_partition(path, mtime):
    return pd.read_parquet(path, columns=COLUMNS)


def replay(tf, start, end):
    no_2024(start, end)
    if end > FORBIDDEN_START:
        raise ValueError("Replay is limited to existing pre-2024 native archives")
    frames, sources = [], []
    first = pd.Timestamp(start, unit="ms", tz="UTC").strftime('%Y-%m')
    last = pd.Timestamp(end-1, unit="ms", tz="UTC").strftime('%Y-%m')
    for month in pd.period_range(first, last, freq='M').astype(str):
        if tf == '1h':
            folder = 'phase3r1/history' if month < '2020-09' else 'phase3r/warmup' if month < '2021-01' else 'phase3'
            path = PROJECT/'data'/folder/'candles'/f'{month}.parquet'
        else:
            path = PROJECT/'data/phase4/candles'/tf/f'{month}.parquet'
        if not path.is_file():
            raise ValueError(f"Missing native history: {path.name} ({tf}); not approximated")
        frames.append(read_partition(str(path), path.stat().st_mtime_ns))
        sources.append(str(path.relative_to(PROJECT)))
    f = pd.concat(frames, ignore_index=True)
    f = f[(f.open_time >= start) & (f.close_time < end)]
    return validate(f, tf), sources


def live(tf, start, end):
    no_2024(start, end)
    from app.market.binance_client import BinanceFuturesClient
    client = BinanceFuturesClient()
    rows = []
    cursor = start
    try:
        while cursor < end:
            page = client.get_klines(symbol='BTCUSDT', interval=tf, start_time=cursor, end_time=end-1, limit=1500)
            if not page:
                raise ValueError("Incomplete REST coverage")
            if int(page[0][0]) != cursor:
                raise ValueError("REST coverage gap")
            rows.extend(dict(zip(COLUMNS, [r[0], r[1], r[2], r[3], r[4], r[6]])) for r in page)
            nxt = int(page[-1][0])+STEPS[tf]
            if nxt <= cursor:
                raise ValueError("REST pagination made no progress")
            cursor = nxt
            time.sleep(.15)
    finally:
        client.close()
    f = pd.DataFrame(rows)
    f = f[pd.to_numeric(f.close_time) < end]
    return validate(f, tf), ['https://fapi.binance.com/fapi/v1/klines']


def load(tf, decision, cfg, mode):
    step = STEPS[tf]
    end = decision//step*step
    # Explicit warmup for swing confirmation and derivatives, not a shorter baseline.
    warmup = (2*max(cfg.swing_ns.values())+3)*step
    start = (end-max(cfg.history_days, cfg.converging_history_days)*DAY-warmup)//step*step
    f, sources = (replay if mode == 'replay' else live)(tf, start, end)
    if int(f.open_time.iloc[0]) != start or int(f.close_time.iloc[-1])+1 != end:
        raise ValueError("Incomplete requested history; no silent window shortening")
    return f, sources
