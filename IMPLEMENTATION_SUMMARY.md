# Website v4: Scoring directional percentile

Added symbol/config/formula-version scoped, prior-only directional Scoring
distributions. Exact-zero semantics, Converging midrank convention and minimum
sample rule, persistent incremental operational cache, manual-price percentile,
history enrichment and a detail histogram are implemented. Original Scoring and
Converging source files are unchanged. 416 Python / 20 Node tests pass.
Actual full-lookback observation coverage is currently about 30-32 days, NOT
850 days of observations; score lookback remains 850 days. See
docs/SCORING_PERCENTILE.md for population limits and BTC/ETH/SOL evidence.

# Website v4: Calendar iframe revision

Calendar parsing, polling, cache and economic alerts have been removed. The
requested Investing iframe is isolated in a responsive scroll wrapper. Existing
calendar SQLite rows are removed while YouTube state/deduplication is preserved.
Manual Scoring and Converging are unchanged; real API parity verified.
402 Python and 18 Node tests passed. Desktop/mobile checks have no page overflow
or JavaScript errors. Investing currently returns HTTP 403 inside the iframe,
so successful calendar content remains unverified; no bypass attempted.
See docs/WEBSITE_V4.md and data/live-dashboard/v4-iframe-browser.json.

# Website v4: Initial implementation (historical, superseded above)

Added backend-authoritative manual Scoring with bounded per-symbol candidate
map reuse; actual market Converging and candles remain unchanged. Added a
compact public events area, isolated Investing adapter, official YouTube API
monitor, durable deduplicated local alerts and opt-in browser notifications.

The supplied YouTube key is stored outside this repository in Windows
user-bound DPAPI encryption. Official API resolved EZPZNOW to
`UCZJ9ZukOgTjKcjN9SJQPf7w` and verified a live title/video. Investing direct
retrieval returns HTTP 403: no bypass or fabricated events; live calendar
success remains unverified. See `docs/WEBSITE_V4.md` for exact limitations.

Tests: 407 Python and 15 Node. Real manual P=70000 changes Scoring only;
current-price and legacy BTC parity verified. Reports: `v4-tests.xml` and
`v4-verification.json` under `data/live-dashboard`.

Changed/added: website `manual.py`, `events.py`, candidate-map injection in
`scoring.py`, main routes/lifecycle, frontend manual controls/`events.js`/`v4.css`,
v4 tests, formula-file hash guard, verification script and v4 documentation.
Scoring arithmetic and Converging formulas are unchanged; no orders added.

# Website v3: Multi-Symbol + Simple UI

Implemented dynamic Binance USD-M perpetual discovery, on-demand per-symbol
analysis and additive symbol-aware SQLite migration preserving BTC data.
Added bounded workers/downloads/rate/cache resources, searchable selection,
local favorites/recent symbols, two primary cards, larger chart, collapsed
details and responsive layout. Scoring/Converging/config formulas are unchanged.

Verification: 382 Python tests and 15 Node tests passed. Real BTC/ETH/SOL
snapshots are isolated; CTUSDT correctly has insufficient history. The v1 BTC
replay baseline remains semantically identical. See `docs/WEBSITE_V3.md` and
`data/live-dashboard/v3-verification.json` for scope, migration, limits and evidence.

Changed: `backend/app/website/{live.py,api.py,symbols.py}`, `backend/app/main.py`,
`frontend/analysis/{index.html,v2.js,chart.js,v3.css,symbol-model.js,ko.test.cjs,symbol.test.cjs}`,
`backend/tests/test_website_symbols.py`, `backend/scripts/verify_website_v3.py`,
and this summary plus `docs/WEBSITE_V3.md`. No trading or full-market scanner.

# Scoring + Converging Website v1

## Added / Changed

Added `backend/app/website/{__init__.py,config.py,config.json,market.py,scoring.py,
converging.py,api.py}`, `frontend/analysis/{index.html,style.css,app.js}`,
`backend/tests/test_website_analysis.py`, `backend/scripts/verify_website_v1.py`,
and `docs/WEBSITE_V1.md`. Updated `backend/app/main.py` to mount the site/routes;
updated the root README with the new entry point. No frozen research formulas,
source partitions, outcomes or previous reports were modified by this work.

## Implemented Formulas / Configuration

Original adjacent-pair detector; inclusive proximity 1/.5/0; exponential recency
with 180-day half-life and .25 floor; per-TF weighted imbalance; normalized
combined Scoring with weights 1d=1,15m=.85,1h=.70,4h=.55. History defaults 850d.

Converging: strict causal N2/4/8 swing confirmation; log return per native candle;
historical median/quantiles, midrank CDF percentile and ratio. Distributions are
TF x N x HIGH/LOW x actual UP/DOWN. Both sources remain separate. Source-ID or
direction changes reset velocity; acceleration requires consecutive valid
same-source velocities. Config/version/hash are returned. No Scoring/Converging
arithmetic fusion. See `docs/WEBSITE_V1.md` for every convention and API route.

## Real BTC Checks

Independent calculations match all 12 TF and 72 scale/source results at three
predetermined timestamps. Full source IDs, native observation times, slopes,
medians, percentiles, velocities and accelerations are preserved in
`data/website-v1/manual-verification.json`, together with input SHA256 hashes.

| UTC decision | 15m closed price | Combined normalized Scoring |
| --- | ---: | ---: |
| 2022-12-15 12:15 | 17687.5 | 0.1255581673 |
| 2023-06-15 12:15 | 24968.6 | -0.3606171262 |
| 2023-12-15 12:00 | 42800.0 | 0.0089066586 |

Example at 2023-12-15 12:00 UTC (same P for all scoring TFs):

| TF | Nearby S/R counts | Weighted S | Weighted R | TF score |
| --- | --- | ---: | ---: | ---: |
| 15m | 124 / 133 | 43.872080 | 42.642020 | 0.014218 |
| 1h | 64 / 71 | 22.325467 | 22.095828 | 0.005170 |
| 4h | 31 / 36 | 10.672750 | 10.649883 | 0.001072 |
| 1d | 8 / 13 | 3.355438 | 3.280342 | 0.011317 |

N4 HIGH-origin details (slopes are raw log-return per candle, not percentages):

| TF | Source price | Elapsed | Signed slope | Median magnitude | Percentile | Velocity | Acceleration |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 15m | 43054.0 | 11 | -0.000537913 | 0.000661052 | 41.81624 | -0.74646 | 13.91178 |
| 1h | 43193.9 | 12 | -0.000763432 | 0.001439678 | 26.00945 | 2.65391 | 5.79341 |
| 4h | 43450.1 | 4 | -0.003768763 | 0.003228526 | 56.65967 | null | null |
| 1d | 44779.3 | 6 | -0.006632110 | 0.009024744 | 35.35503 | -12.79312 | 22.14479 |

The 4h source is newly confirmed; derivatives correctly reset. UI displays these
API values rounded, separately preserving each LOW-origin result and other Ns.

## Tests / Limitations / Explicit Differences

27 new tests cover the detector, boundaries, recency/floor, normalization/empty
denominator, weights/bounds, swing causality, future exclusion, source/sign
distribution separation, median/percentile/ratio, same-source derivatives/reset,
native higher-TF alignment, invalid data, reserved-year guard and HTTP/static UI.
Full suite results are recorded in `data/website-v1/tests.xml`.
Final full suite: **358 passed**, zero failures, with one existing Starlette/httpx
deprecation warning. JavaScript syntax check passed. Browser checks covered real
values, expanded scoring details, timeframe/scale changes and desktop/mobile
layouts; screenshots are under `data/website-v1`.

The default replay works with existing native data. Live REST code is present,
but default 850-day live history intersects reserved 2024 and is intentionally
blocked, not silently shortened. External live integration is unverified.
No automatic timer; refresh is explicit. No online config editor or incremental
live cache persistence. No production authentication/rate limiting/deployment.

The requested inclusive proximity endpoints are versioned and differ from strict
legacy endpoint inequalities. Candidate age begins at known_at. Common closed
15m P is used for Scoring; Converging uses native closed price and elapsed native
candles. Midrank ties, minimum 30 samples, finite left-edge swing bootstrap,
direction-change resets and frozen-entry-CDF diagnostics are explicit decisions,
not optimized replacements. Baseline samples before the first confirmed source
are absent; see architecture notes. A zero denominator is not proof of balance.

Retrospective diagnostics are isolated from current features; last-64-candle entry
sampling is bounded and no future horizon beyond requested T is fabricated.
Full-map debugging is JSON, while the chart keeps nearest/source overlays only.
Fonts optionally use Google Fonts; local fallback keeps offline replay usable.

STOP: no optimization, winner selection, 2024 market data, ML, leverage or orders.

## Website v2 - Operational Live Dashboard

Added isolated `data/live-dashboard/` SQLite candle acquisition and analysis history,
public BTCUSDT ticker polling, native closed-candle bootstrap, retry/integrity checks,
state persistence and causal operational replay. The v2 operational window may
include 2024; this does not remove the original research guard or modify frozen data.
Scoring, Converging and config files remain unchanged. Shared `evaluate_frames`
produces the same v1 historical response byte-for-byte for the captured baseline.

The Korean UI now defaults to live mode with separate ticker/analysis prices,
freshness timestamps, a vendored Lightweight Charts chart, native timeframe and
N/high-low selection, source geometry, KST historical navigation and recent history.
Content-hash asset URLs prevent mixing old scripts with new markup.

See `docs/WEBSITE_V2.md` for architecture, launch instructions, semantics and limits.
Backend test report: `data/live-dashboard/tests.xml`; real-data inspection evidence:
`data/live-dashboard/verification.json`. No automated trading or strategy research.
