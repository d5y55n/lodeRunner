# Scoring + Converging Website v1

## Run

From `C:\Users\82108\Desktop\lodeRunner\backend`:

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8011
```

Open http://127.0.0.1:8011. No frontend build, account, order key or database is
needed. The UI uses vanilla JS and canvas, responsive CSS, and an optional remote
font with local fallbacks. The existing Python environment contains dependencies.
On a new machine install the backend project and pytest in Python 3.12+ and provide
the native archived candle partitions. Missing history returns an explicit error,
never synthetic prices. This is a local instrument, not a public hardened service.

Default mode is **historical replay**, 2023-12-15 12:00 UTC. A replay price is never
labeled a live quote. The top price is the latest fully closed 15m close at T.
Scoring uses that same P for all timeframes. Converging observes each native
timeframe at its latest fully closed native candle; source/observation times are
visible. No unfinished candle or future observation enters a calculation.

## Configuration

Edit `backend/app/website/config.json`, or point `ANALYSIS_CONFIG` to another JSON
file using the same schema. Configuration is read for each API request; the cache
key includes the entire configuration and decision time. No web-based config
mutation endpoint is exposed. Change formula versions when changing conventions.

Defaults: scoring/history 850 days; half-life 180d; recency floor .25; widths
15m .002, 1h .004, 4h .007, 1d .022; outer multiplier 1.5; importance weights
15m .85, 1h .70, 4h .55, 1d 1.00; balanced UI band +/- .05. Converging: N2/4/8,
850-day distribution, bands 75/90/95, horizons 4/8/16/32, minimum 30 comparable
samples. All are initial configuration, not fitted or validated optimal choices.

## Scoring

Adjacent bullish -> bearish: resistance=min(high1,high2). Bearish -> bullish:
support=max(low1,low2). Doji transitions are excluded. known_at is the second
close boundary. Both candles must be within the rolling scoring history.

Distance is abs(P/C-1). Inner <= width contributes 1; outer <=1.5*width contributes
.5; outside contributes zero. Decimal boundary rounding tolerance is 1e-14.
The specification's inclusive endpoints deliberately differ from the strict
inequalities in the archived legacy code. "Legacy Score" means unaged signed
proximity sum under the v1 inclusive endpoint convention, not bitwise parity at
legacy endpoints. Original candidate selection itself is preserved.

Age is (T-known_at) in UTC days. Weight=floor+(1-floor)*2^(-age/halfLife).
Candidate value=proximity*ageWeight. Per TF normalize (weightedS-weightedR) /
(weightedS+weightedR), or zero if empty; empty is separately marked unavailable.
Combined score=sum(tfScore*tfWeight); combinedNormalized divides by sum(weights).
No raw-score summation across timeframes; no arithmetic fusion with Converging.

Nearby counts include inner+outer candidates unweighted. Full-map counts and
UI age-bucket counts include all detected candidates. Bucket contribution sums
include nearby candidates only. Buckets [0,30),[30,90),[90,180),[180,365),[365,inf)
never enter the actual continuous decay. Nearest is by absolute distance within
each candidate TYPE, not restricted to above/below P; signed distance is C/P-1.

## Converging and Resolved Ambiguities

Strict swing high/low exceeds/is below every neighbor in N candles on each side.
Ties are not swings. The source becomes available at the close of candle i+N.
At each native close, retain both latest confirmed HIGH and LOW independently.
Elapsed candles is current index minus source candle index; the exact intrabar
instant of an extreme is unknowable from OHLC and is not fabricated.

signedSlope=ln(nativeClose/sourcePrice)/elapsedCandles; magnitude=abs(slope).
Actual UP/DOWN follows sign, not source type. Zero is FLAT with no directional
percentile. Distributions are separate by **TF x N x HIGH/LOW x actual sign**.
Repeated observations from one active source are intentional time sampling, not
independent events. Stable IDs include TF, source type, N and source open time.

Only historical observations with close boundary strictly before the evaluated
native T and >=T-history are included. The current sample is excluded. Median,
25/50/75/90/95/99 quantiles use linear interpolation. Percentile uses empirical
midrank ties: 100*(count less + .5*count equal)/N. Ratio=magnitude/median;
missing/zero median gives null, never infinity. Fewer than 30 samples gives
INSUFFICIENT_HISTORY, configurable and not a performance filter.

For each prior percentile use its OWN past-only rolling distribution. Velocity
is the percentile difference in percentage points only when the source ID AND
actual direction persist. New source or sign change resets it. Acceleration
requires two consecutive valid velocities with the same source. No backfilling
a new source into earlier observations, even if its historical price is visible.

For left-edge initialization, load 2*max(N)+3 extra native candles. Observations
before the first causally confirmed source are absent (not reconstructed).
This finite-history bootstrap is a documented limitation: a source from before
the loaded history can be unknown until the first confirmation. Sample counts
are explicit. Source candles can predate the distribution window; the window
selects observation times, not source ages.

## Retrospective Diagnostics

The separate diagnostics route samples extreme-state entries in the last 64
native candles (plus one preceding candle to distinguish crossings). New sources
reset entry tracking. Each entry freezes its source AND historical CDF, reporting
continuous future percentile/slope at configured horizons. Future observations
must already exist by the requested replay time; otherwise PENDING. A sign
change is DIRECTION_CHANGED, not merged with the old directional CDF. No binary
win/loss label, probability, predictive claim or trade signal. This fixed-entry
CDF convention is explicit; current dashboard velocity instead uses each point's
own rolling causal CDF. These are separate diagnostics, not interchangeable.

## APIs

- `GET /` analysis page; `/assets/*` static files.
- `GET /analysis/btcusdt?mode=replay&at=2023-12-15T12:00:00Z` full structured result.
- `GET /analysis/btcusdt?mode=live` current closed-candle public REST analysis.
- `GET /analysis/config` active parameters, formula versions.
- `GET /analysis/btcusdt/debug?tf=15m&at=...` full candidate map and contributions.
- `GET /analysis/btcusdt/observations?tf=15m&scale=medium&count=12&at=...` both
  source histories, IDs, slopes, past-only percentiles, ratios and derivatives.
- `GET /analysis/btcusdt/diagnostics?tf=15m&scale=medium&at=...` retrospective only.
- `/docs` OpenAPI; existing `/health` and `/market/*` preserved.

Debug/history/diagnostic routes are replay-only. Current UI chart has zoom/pan,
OHLC hover, current P, nearest S/R and selected high/low source overlays. A source
outside the visible chart is not drawn as a misleading in-view line. Full map
is inspectable through debug JSON rather than hundreds of default chart lines.

## Architecture and Data Safety

`app/website/config.py` validates configuration; `market.py` handles native candle
alignment/coverage; `scoring.py` is the pair/decay/normalization engine;
`converging.py` is the swing/observation/distribution engine; `api.py` orchestrates
and caches. UI formulas are formatting and chart geometry only. Pydantic validates
configuration, explicit dictionaries carry JSON results. Existing research code,
freezes, labels and outcomes are not imported into these calculations.

Replay reads original native partitions only from phase4/candles (15m/4h/1d)
and phase3 / phase3r/warmup / phase3r1/history candles (1h), never trade profiles
or outcome tables. Missing/duplicate/unordered/nonfinite/invalid OHLC or incomplete
requested history fails; no candle synthesis. HTTP errors produce an explicit
unavailable state, not a fake success. REST is read-only, sequentially paginated.

All requests overlapping 2024 are blocked BEFORE data access. As of October 2026,
the default 850-day LIVE history overlaps 2024 and therefore intentionally fails
with a clear message. Do not silently shorten it. To exercise live without 2024,
the user must explicitly configure both histories to a shorter non-overlapping
range. Live acquisition is implemented but not externally integration-tested in
this delivery; replay is the fully verified default. Live refresh is manual and
large REST history fetches are not incrementally persisted in v1.

## Verification

```powershell
.venv\Scripts\python.exe -m pytest -o addopts= -q
.venv\Scripts\python.exe scripts/verify_website_v1.py
```

The second command requires the local server on port 8011. It compares API values
to an independent vectorized pair detector and sliding-window swing reference,
not calls to the production formula functions. Three predetermined real UTC
timestamps (2022-12-15 12:15, 2023-06-15 12:15, 2023-12-15 12:00) cover 12 TF
checks and 72 scale/source checks, including higher-TF staleness. All selected
source partitions have hashes in `data/website-v1/manual-verification.json`.

Research remains descriptive. No 2024 evaluation, threshold optimization,
strategy selection, leverage, ML, combined predictive score or live orders.
