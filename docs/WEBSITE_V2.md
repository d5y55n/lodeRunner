# Website v2: Live Dashboard

## Run

From `backend`, run `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8011`.
Open http://127.0.0.1:8011/ and select 실시간. One server process is supported.
Market ingestion starts on the first market-status request and continues while
the server runs, even if the browser is closed. No exchange account or key is used.

## Architecture and Storage

`website/live.py` separates the public REST feed, SQLite storage and worker.
`data/live-dashboard/dashboard.sqlite3` is operational storage only. Its candle,
acquisition and snapshot tables never modify or import frozen research datasets.
The operational bootstrap can include 2024 because the v2 live window requires it;
the original replay provider and its reserved-year guard are unchanged.

Four native BTCUSDT USD-M timeframes are downloaded independently. The exchange
server clock defines completed candles. Ingestion checks finite positive OHLC,
open/close alignment, order, duplicates, spacing and exact requested coverage.
Identical retries are idempotent. Conflicting closed candles are rejected, not
overwritten. Gaps and incomplete lookbacks surface explicitly without interpolation.
Each accepted page records source, receive time, range, count and content SHA256.

## Closed-Candle Semantics

The unchanged v1 engine is shared through `api.evaluate_frames`. Formula versions,
config values and hash are exposed. Scoring evaluates all four maps at the same
last closed 15m price. Converging uses each native timeframe's closed price and
native elapsed-candle count. Ticker price is displayed separately and never enters
the analysis engine. The chart contains closed candles, not a fabricated forming bar.

## Refresh, Freshness and Failures

The backend polls exchange time and ticker approximately every three seconds;
errors use bounded exponential backoff. One analysis worker updates on new 15m
decision timestamps. Complete snapshots are reused between closes; no full-window
recalculation occurs for ticker changes. Full deterministic calculations run at
each close, rather than introducing a new incremental percentile algorithm.

The frontend polls the backend without page reloads. It preserves the user's
chart view and marks stale/disconnected data. Status uses exchange timestamps,
receive age, connection state and expected 15m decision. Local timers also expire
freshness if requests hang. Previous valid data remains visible on failure.
Restart restores a checksummed snapshot as stale until candle history is validated.
SQLite transactions and uniqueness protect against partial or duplicate writes.

## Chart and Replay

Locally vendored TradingView Lightweight Charts 5.0.8 provides pan, zoom, crosshair
and responsive canvas sizing. The UI offers 15m/1h/4h/1d, N2/N4/N8 and HIGH/LOW
selection. Only one selected source slope is drawn. Source ID, confirmation time,
comparison sample count and numerical metrics are inspectable. When the source
is outside the 240-candle display range its geometry is retained and labeled.

Enable 캔들 클릭으로 과거 탐색 to select a candle's close timestamp, or use the
KST date input/history row. Replay switches off live chart following and always
requests authoritative backend values. 현재로 돌아가기 restores live selection.
Ticker in the separate live-price strip remains explicitly current, not replayed.

Existing pre-2024 replay uses the guarded read-only research provider. Operational
replay uses cached candles only; it never triggers arbitrary historical downloads.
Bootstrap stores an extra 30 days for navigation while each calculation still
uses exactly the configured 850-day lookback plus original swing warmup. Earlier
times without complete history return HISTORY_INCOMPLETE. No future candle or
unconfirmed swing is supplied to the shared engine. A four-entry replay cache is
bounded and returns copies to prevent cross-request mutation.

## API and State History

- `/market/btcusdt/status`: connection, ticker, progress, latest snapshot and clocks.
- `/market/btcusdt/candles?tf=15m`: validated closed operational candles.
- `/dashboard/btcusdt/replay?at=<ISO offset time>`: causal backend replay.
- `/analysis/btcusdt/history?limit=12`: persisted operational snapshots.
- Original `/analysis/btcusdt` remains compatible for v1 callers.

Snapshots have source/decision and calculated timestamps, formula configuration,
per-TF Scoring, all Converging scales/sources, provenance, raw slopes, derivatives
and the ticker observed at calculation. Primary key is decision time plus config
hash; ticker movements alone never append state rows. The UI shows N4 high/low
percentiles explicitly, not an average. Missed downtime snapshots are not invented.
Developer raw-value diagnostics are collapsed by default. The original retrospective
future-outcome diagnostics remain restricted to the old research replay provider.

## Verification and Limitations

Completion checks: 371 Python tests and 11 frontend Node tests passed. JavaScript
syntax checks passed. One pre-existing Starlette/httpx deprecation warning remains.
Captured v1 response parity is byte-for-byte, and the Scoring/Converging/config
hashes equal the pre-v2 baseline. Real-data audit contains 84,564 15m candles,
21,155 1h candles, 5,303 4h candles and 900 daily candles at capture time.
Ongoing ingestion increases these counts. Acquisition is official Binance REST.

Manual Korean UI cases: 2023-12-15 21:00 KST baseline (+0.009),
2026-09-28 07:45 KST N2 high extreme DOWN (95.4%),
2026-09-28 15:15 KST N2 low extreme UP (95.1%), and
2026-09-27 21:15 KST N2 low source reset (both derivatives null).
These are descriptive inspection fixtures, not evidence of a trading edge.
Browser verification also covered timeframe/N/source switching, chart zoom and
candle-click navigation (selected close 2026-09-26 15:30 KST), and 1440px/390px
layouts without horizontal page overflow. Stopping the server preserved the last
analysis price while changing the UI to disconnected/stale; restarting reuses
the persisted data rather than reconstructing it from scratch.

Tests cover invalid/duplicate/open/gapped candles, restart/idempotent retries,
cached-vs-full v1 parity, replay future exclusion, native-close alignment,
snapshot deduplication/checksums, stale states and overlay source selection.
`scripts.verify_website_v2` records deterministic real-data inspection cases and
coverage in `data/live-dashboard/verification.json`. It selects the first matching
normal/extreme-up/extreme-down/source-reset observations, not successful reactions.

The site is a local monitoring prototype, not a production authenticated service.
Keep it bound to loopback. Multi-process workers, high availability, full-map
debug overlays and forming-candle streaming are not included. Initial history
download and historical full recomputation can take time. No trade alerts,
orders, optimization, ML or numeric combination of the two analytical axes exist.

## References

- https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data
- https://tradingview.github.io/lightweight-charts/docs/5.0
- `frontend/analysis/vendor/LICENSE` and `NOTICE` retain third-party licensing.
