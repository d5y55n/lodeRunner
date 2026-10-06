"""Public perpetual universe and bounded, on-demand operational workers."""
import threading
import time
from fastapi import APIRouter, HTTPException, Query
from typing import Literal
from .live import PublicFeed, Dashboard, bounds
from .config import STEPS, settings
from .market import timestamp, FORBIDDEN_START

router = APIRouter(tags=['multi-symbol'])


def discover(payload):
    rows = []
    for s in payload['symbols']:
        if s.get('status') != 'TRADING' or s.get('contractType') != 'PERPETUAL':
            continue
        rows.append(dict(symbol=s['symbol'], base_asset=s['baseAsset'], quote_asset=s['quoteAsset'],
                         contract_type=s['contractType'], status=s['status'], onboard_date=s.get('onboardDate',0),
                         price_precision=s['pricePrecision'], quantity_precision=s.get('quantityPrecision'),
                         tick_size=next((f['tickSize'] for f in s.get('filters',[]) if f['filterType']=='PRICE_FILTER'),None),
                         history_readiness='UNCHECKED'))
    return sorted(rows, key=lambda s:s['symbol'])


class Registry:
    def __init__(self):
        self.lock = threading.RLock()
        self.metadata = {}
        self.expires = 0
        self.workers = {}

    def universe(self):
        with self.lock:
            if time.monotonic() >= self.expires:
                feed = PublicFeed()
                try:
                    payload = feed.get('/fapi/v1/exchangeInfo')
                    rows = discover(payload)
                    decision = int(payload['serverTime'])
                    cfg = settings()
                    for row in rows:
                        if any(row['onboard_date'] > bounds(tf,decision,cfg)[0] for tf in STEPS):
                            row['history_readiness'] = 'HISTORY_INCOMPLETE'
                    self.metadata = {r['symbol']:r for r in rows}
                    self.expires = time.monotonic()+3600
                finally:
                    feed.close()
            rows = []
            for symbol, metadata in self.metadata.items():
                row = dict(metadata)
                d = self.workers.get(symbol)
                if d:
                    state = d.status()
                    row.update(history_readiness=state['analysis_status'],latest_price=(state['ticker'] or {}).get('price'),last_update=state['market_received_at'])
                rows.append(row)
            return rows

    def get(self, symbol):
        symbol = symbol.upper()
        self.universe()
        with self.lock:
            if symbol not in self.metadata:
                raise HTTPException(404, 'Unsupported or inactive USD-M perpetual symbol')
            if symbol not in self.workers:
                # Do not create an unbounded queue on rapid selection.
                if len(self.workers) >= 3:
                    candidates = [(s,d) for s,d in self.workers.items() if (d.future is None or d.future.done()) and time.monotonic()-d.last_active > 30]
                    if not candidates:
                        raise HTTPException(429, 'Worker limit: retry after 30 seconds')
                    old,d = min(candidates,key=lambda p:p[1].last_active)
                    d.stop()
                    if old == 'BTCUSDT':
                        from .live_api import dashboard
                        dashboard.cache_clear()
                    del self.workers[old]
                if symbol == 'BTCUSDT':
                    from .live_api import dashboard
                    self.workers[symbol] = dashboard()
                else:
                    self.workers[symbol] = Dashboard(symbol=symbol,onboard=self.metadata[symbol]['onboard_date'])
            return self.workers[symbol]

    def close(self):
        for d in self.workers.values():
            d.stop()
        self.workers.clear()


registry = Registry()


@router.get('/market/symbols')
def symbols():
    try:
        return dict(symbols=registry.universe(), scope='USD-M TRADING PERPETUAL', sort='alphabetical')
    except Exception as exc:
        raise HTTPException(503, 'Exchange metadata unavailable') from exc


@router.get('/market/{symbol}/status')
def status(symbol: str):
    d = registry.get(symbol)
    d.start()
    return d.status()


@router.get('/analysis/{symbol}')
def analysis(symbol: str):
    return status(symbol)


@router.get('/dashboard/{symbol}/replay')
def replay(symbol: str, at: str):
    d = registry.get(symbol)
    try:
        decision = timestamp(at)//STEPS['15m']*STEPS['15m']
        if d.symbol == 'BTCUSDT' and decision <= FORBIDDEN_START:
            from .live_api import replay as legacy_replay
            return legacy_replay(at)
        return d.replay(decision)
    except ValueError as exc:
        raise HTTPException(422, 'HISTORY_INCOMPLETE: '+str(exc)) from exc


@router.get('/analysis/{symbol}/history')
def history(symbol: str, limit: int = Query(30,ge=1,le=100)):
    d = registry.get(symbol)
    from .scoring_distribution import attach
    return dict(symbol=d.symbol,rows=[attach(r,d.store,d.cfg) for r in d.store.history(limit)])


@router.get('/market/{symbol}/candles')
def candles(symbol: str, tf: Literal['15m','1h','4h','1d']='15m', count: int = Query(240,ge=20,le=2000)):
    d = registry.get(symbol)
    s = d.status()['snapshot']
    if not s:
        return dict(symbol=d.symbol,status='HISTORY_INCOMPLETE',candles=[])
    end = s['timestamp']//STEPS[tf]*STEPS[tf]
    try:
        return dict(symbol=d.symbol,status=s['freshness'],candles=d.store.load(tf,end-count*STEPS[tf],end).to_dict('records'))
    except ValueError as exc:
        raise HTTPException(422, 'HISTORY_INCOMPLETE: '+str(exc)) from exc
