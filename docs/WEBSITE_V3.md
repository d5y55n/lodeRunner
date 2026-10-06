# Website v3: multi-symbol selectable dashboard

## Scope and eligibility

Public Binance USD-M Futures only. `/fapi/v1/exchangeInfo` supplies the
universe: `TRADING` and `PERPETUAL`, not a hardcoded coin list. Spot, COIN-M,
inactive and dated contracts are excluded. Symbols are alphabetically sorted;
favorites precede the full search list. Metadata retains base/quote assets,
contract type/status, listing time, price/quantity precision and tick size.
The verification run on 2026-10-05 KST discovered 571 contracts. This count
is dynamic and is not a guarantee that every contract has adequate history.

Listing date is an early rejection check, not evidence of complete coverage.
All four native intervals (15m/1h/4h/1d) must pass the existing finite OHLC,
chronology, spacing, closed-candle and exact-range validation. New listings
remain selectable with a live quote and `데이터 부족`, but no fabricated
Scoring/Converging or shortened lookback. `UNCHECKED` means not yet downloaded
and validated, not eligible for analysis. Required history remains 850 days
plus the unchanged swing warmup. Partial TF readiness never yields a combined
score. Detailed failure reasons are visible under developer information.

## On-demand bootstrap and resources

Only a requested symbol starts a worker. Cached rows are validated, then only
missing tail pages are fetched. Acquisition keeps official REST source URLs,
received times and payload checksums. The optional 30-day navigation margin
is storage only; the engine still receives its exact original lookback.
Listing time limits that extra margin; it does not shorten analysis history.
Replay reads cached history only. Missing history returns HTTP 422 and never
triggers arbitrary old-date downloads. BTC's existing pre-2024 research replay
route remains compatible; new operational data never changes research files.

- One process-wide historical download/analysis slot; other workers queue.
- At most three retained live workers; excess rapid selections receive 429
  and the frontend retries. Idle workers are eligible for LRU eviction.
- Polling stops after 30 seconds without status requests. An abandoned
  bootstrap stops at its next page boundary and resumes from validated rows.
- Public request starts are globally spaced by at least 300 ms. Kline pages
  use limit 1000. HTTP 418/429 applies shared Retry-After backoff (at least 60s).
  This is a single-process local server, not a distributed rate coordinator.
- Metadata TTL is one hour. There is no full-market price/analysis scanner.
- Four replay entries per worker, at most three workers, 40 search results,
  30 favorites, six recent symbols, history response capped at 100 snapshots.
- An 8 GiB operational SQLite/WAL budget stops new analysis writes on the next
  update. It does not silently delete data; already-running work may exceed
  the boundary by one update. Existing files require explicit archiving.

## Storage and migration

BTC keeps `data/live-dashboard/dashboard.sqlite3`. Other symbols use
`data/live-dashboard/symbols/<sha256(symbol)[:24]>/dashboard.sqlite3`.
Hash paths also handle non-ASCII exchange symbols without path traversal.
Only metadata-allowlisted symbols reach production store construction.

Migration is additive and transactional: add `symbol` to candles, acquisition
and snapshots; backfill legacy BTC rows; create symbol/timeframe/time indexes;
bind each database to one symbol in `identity`. Existing candle rows, snapshot
JSON/checksums and legacy primary keys stay intact. New records include symbol.
The database identity prevents reopening another coin's store under a different
symbol. Legacy populated BTC databases cannot be relabeled. No reset or data
deletion occurs. Take an ordinary SQLite backup before manual migration work.

## Engine and cache isolation

`evaluate_frames(..., symbol=...)` uses the same shared engine with only that
symbol's validated frames. Scoring and Converging formula files and config
hashes are unchanged. Distribution scope is symbol (isolated frames/worker)
x timeframe x N x source type x actual slope direction. No cross-symbol
normalization or pooled distribution exists. New non-BTC source IDs are symbol
qualified; older v3 snapshots can retain their original source ID spelling.
All snapshots carry their symbol at the root and have checksum verification.

Persisted latest snapshots are restored as stale, then verified against current
exchange time and complete cache coverage. If the same decision is already
computed, validation reuses it without recalculating the entire distribution.
No worker shares replay caches with another symbol. Switching UI increments an
epoch, clears all previous price/chart/summary/history fields and ignores late
responses from a different symbol. Replay additionally uses a request token.

## Endpoints

`GET /market/symbols`

`GET /market/{symbol}/status`

`GET /market/{symbol}/candles?tf=15m&count=240`

`GET /analysis/{symbol}` (current status plus snapshot)

`GET /analysis/{symbol}/history?limit=30`

`GET /dashboard/{symbol}/replay?at=<ISO timestamp>`

Existing lowercase BTC routes remain unchanged. Generic routes accept
case-insensitive symbol names. The old `/analysis/btcusdt` default remains
historical replay for compatibility, unlike generic current-state routes.

## UI

The header contains searchable symbol selection, current quote, connection and
last update. Favorites and recent symbols are localStorage only. Search renders
at most 40 filtered entries and supports Tab, arrows, Enter and Escape.
The two primary cards show Scoring and selected Converging, followed by one
descriptive sentence. A larger chart is the visual center, with compact TF,
N and source controls. Support and resistance use consistent restrained colors.
Small-priced assets retain significant digits rather than rounding to zero.
State history, detailed calculations and developer information are collapsed.
Mobile stacks the cards; tables scroll inside their own disclosure, not the page.
Asset URLs contain content hashes to avoid partially updated cached UIs.

## Verification

- Full Python suite: 382 passed, zero failures/errors/skips. Existing
  Starlette/httpx deprecation warning remains. XML: `data/live-dashboard/v3-tests.xml`.
- Frontend Node suite: 15 passed. Coverage includes search/favorites ordering,
  bounded lists, recent deduplication, small prices, localization, content
  hashes, selection geometry and causal replay timestamps.
- New Python tests cover discovery filtering, listing ages, first bootstrap,
  no redundant downloads, incomplete history, symbol-aware feeds, safe migration,
  candle/snapshot/history/distribution/replay isolation, bounded workers,
  shared download slot, generic routes and unchanged formula hashes.
- Real BTCUSDT, ETHUSDT and SOLUSDT caches produced separate valid snapshots.
  CTUSDT had insufficient listing history, no candle substitution, no snapshot.
  The original BTC default replay equals the saved v1 baseline semantically.
- Reproducible verifier: `backend/scripts/verify_website_v3.py`; results in
  `data/live-dashboard/v3-verification.json`. This explicitly checks four
  samples, not every symbol in the exchange universe.
- Browser inspection covers real bootstrap progress, search, favorites retained
  after reload, recent symbols, symbol switching, summary/detail controls,
  SOL cached replay, desktop and mobile layout, and insufficient history.
  Screenshots: `data/live-dashboard/v3-desktop.png`, `v3-mobile.png`,
  `v3-insufficient.png`. Missing-cache replay errors were also checked in the UI.

## Limitations

This local app needs Binance public endpoint access; exchange metadata outages
prevent discovering new symbols. No fallback exchange or synthetic candles.
Only selected symbols have verified coverage. A symbol can have gaps despite
an old listing date; such gaps are reported, never repaired by interpolation.
Rapidly selecting more than three busy symbols can require waiting for an idle
worker. First bootstrap and full causal calculations can take minutes.
Disk limits are conservative stop conditions, not automatic retention policies.
Multi-process uvicorn deployments are not supported by the in-process resource
coordinator. No trades, alerts, leverage, optimization, ML or market scanner.
