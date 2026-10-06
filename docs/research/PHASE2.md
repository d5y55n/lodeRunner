# Phase 2 research contract

Status: implemented foundation, not a strategy or optimized model.
The active repository is `C:/Users/82108/Desktop/lodeRunner`.

## Modules and scope

`backend/app/research/` contains:

| Module | Responsibility |
| --- | --- |
| models.py | Candle clock, candidate/zone records, canonical serialization |
| data.py | Existing Phase 1 Candle adapter and gap rejection |
| detectors.py | Common detector protocol and independent A/B/C algorithms |
| zones.py | Fixed and original widths; adaptive interface |
| interactions.py | Per-zone visit state machine and raw visit facts |
| volume.py | Trade contract, Binance aggregate adapter, bins, D, zone features |
| outcomes.py | First-boundary outcomes and full-horizon excursions |
| config.py | Full experiment configuration and chronological boundaries |
| runner.py | Independent grid execution, controls, descriptive comparison |
| smoke.py | Small BTCUSDT experiment and deterministic replay |

No production signals, strength score, probability model, leverage, ML, order
execution, parameter optimizer or frontend is added. Existing Phase 1 API and
market-data services remain the data source. Existing placeholder analysis and
probability files are not presented as implemented production components.

## Candle clock and identity

Phase 1 Binance close_time is inclusive milliseconds. Research converts it to
exclusive `end = close_time + 1`. A candle is available at end; the next candle
may start exactly at that instant. Source timestamps are candle opening times,
not invented intrabar times. Positive finite OHLC, unique IDs and contiguous
chronological candles are required. Missing candles fail rather than shortening
observation horizons silently. Dataset provenance must identify symbol/timeframe.

Every candidate records detector, kind, price, source_timestamp, known_at,
timeframe, source_ids and detector metadata. Source IDs include symbol and
timeframe when adapted from Phase 1. D has no source candles; it records trade IDs.
Candidate and zone IDs are content hashes. Config, selected candle content,
optional trades/coverage and source-code hashes produce the experiment ID.

## Exact detector algorithms

### A: original reversal candles

Original source was located at
`C:/Users/82108/Documents/Codex/2026-04-28/new-chat-3/binance_bot/src/main/resources/static/scoring.js`.
Original file SHA256:
`d530f675733d9a27b84191f95d72c3058cfaaa448efca04daa40b1bdb2b64960`.

Bullish followed by bearish: resistance at min(before.high, after.high).
Bearish followed by bullish: support at max(before.low, after.low).
Equality picks before, preserving original branches. Doji pairs emit nothing.
Source timestamp belongs to the selected reference candle; known_at is the
second candle's end. Both candle IDs are retained. All +/-1, +/-0.5, proximity
and LONG/SHORT scoring logic is omitted. Six branch/equality tests preserve prices.

### B: strict local extrema

Width N compares N candles left and right. A high must be strictly greater than
all neighboring highs; low strictly less than all neighboring lows. Ties emit
nothing. known_at is the final right-hand candle's end, not the pivot time.
Widths are independent experiments; no winner is selected.

### C: later-close confirmed reversal

Track running high and low independently. If a candle sets a new high/low,
update that tracker without confirming it on the same candle. Otherwise a later
close <= high*(1-r) confirms resistance; close >= low*(1+r) confirms support.
Each tracker resets to the confirming candle. Equal extrema retain the earlier
source. This is not an alternating ZigZag: both sides may confirm on the same
bar, and multiple nearby candidates may be emitted. All such candidates remain
raw observations. r is configurable. No optimal reversal magnitude is claimed.

### D: volume concentration

Trades are placed into zero-anchored [lower, upper) price bins using Decimal
bin indexing, while quantities use float64-compatible floats. Non-overlapping
observation windows are [start, end); a candidate is known only at window end.
An occupied bin is selected if its quantity / mean occupied-bin quantity is at
least a configured multiple. Empty bins are excluded from that explicit baseline.
Candidates are NEUTRAL, with bin midpoint as reference, original bin bounds,
trade IDs, quantity, aggressive buy/sell quantity, delta and window metadata.
Research zones can be built around midpoints; these are distinct from native bins.

Buyer-is-maker false means aggressive buy; true means aggressive sell. Unknown
side quantity is separate, and full volume delta is null if any side is unknown.
Duplicate IDs and out-of-order trades are rejected, not silently combined.

## Width and interaction choices

Fixed half-widths: 0.0005, 0.001, 0.002, 0.003, 0.005 (fractions).
Original map: 15m=0.002, 1h=0.004, 4h=0.007, 1d=0.022.
Adaptive extension receives only candles ending by known_at; no adaptive formula
is selected or silently substituted in the grid runner. A custom formula must
have a versioned name; resolved width is recorded on the zone.

Zones are not merged, expired, ranked or deduplicated across candidates. Nearby
zones may share events; observations are therefore correlated.

An interaction begins when a later candle range overlaps the zone. Candles
starting before known_at are excluded, including the confirming candle.
Approach uses previous close relative to the zone (or current open if absent).
INSIDE is explicit when the zone appears around price already inside.

States: OUTSIDE -> ENTERED -> INTERACTING -> EXITED. A wick-only visit can enter
and exit at one candle close. Boundary exit is close strictly outside zone;
confirmed exit additionally requires separation_fraction * reference_price.
Touches while a visit remains active never increment the visit number. A later
return after confirmed exit starts a new visit. Separation is configurable.

Wick overlap and close-inside are separate booleans. Penetration is measured
from the approached edge to the deepest opposing extreme, in price units and
zone-width units; it can exceed 1 zone width. INSIDE approach has null directional
penetration/crossing. Crossed-through means a close reached the opposite side,
not an assumed intrabar path. Candles spent includes entry and exit bars, and
bars waiting for confirmed separation. Unfinished visits keep end/exit null.
Completed visit facts must never be used as predictors at the first visit close.

## Volume attachments

At the first interaction close T, optional zone features sum exact trades within
zone bounds for [T-W,T). Baseline is the same zone during [T-2W,T-W), an equal
duration. Relative volume is current / baseline; zero baseline gives null.
Only completed trade coverage is accepted. Missing data or incomplete baseline
coverage is explicitly marked. Unknown-side delta stays null. No direction score.
Both windows must fit within the current chronological split. Candidate/zone IDs
allow future A+volume/B+volume/C+volume and combination studies without rebuilding
the detection logic. No combination weighting or fitting is implemented.

## Outcomes and controls

Hypothetical entry = first interaction candle CLOSE, not the zone midpoint or an
assumed intrabar fill. LONG and SHORT are both measured, regardless of zone kind.
Only subsequent candles are used. TP/SL fractions and horizon candle counts form
a Cartesian grid. Open beyond a boundary is the first hit at candle start.
Otherwise both boundaries within one OHLC bar => AMBIGUOUS, never TP-first by fiat.
First label never changes on later bars.

NEITHER means a full observed horizon with no hit. Incomplete horizons are
censored; label stays null if not yet resolved. Observed early hits remain stored
but censored rows are excluded from complete-horizon descriptive fractions.
MFE/MAE are non-negative percentages over the entire available horizon, even
after TP/SL. Times are earliest maximizing candle END offsets, not exact trade
times; zero excursions have null time. No fills, costs, forced exits or P&L.

Controls are every control_stride-th candle from the split start. They use the
same symbol, timeframe, close entry, TP/SL and horizons, independently of detectors
and future behavior. Controls may coincide with interactions; excluding overlaps
using future information is not allowed. This is a neutral scheduled baseline,
not a regime-matched causal control or a claim of independent samples.

Comparison reports label counts, complete/censored sample counts, TP_FIRST
fraction and event-minus-control descriptive difference for each direction,
TP, SL and horizon. No best-parameter selection, significance test or edge claim.
A raw success rate above 50% is not evidence of incremental predictive information.

## Chronological validation and reproducibility

Periods are explicit half-open research, validation and final test date ranges.
Each research/validation run resets detectors and zones at its own boundary.
No cross-split candidates, visits, feature windows or labels. Horizon tails are
censored instead of borrowing validation/test candles. The final test is locked
in this iteration. No shuffle, optimizer or final-test evaluation is provided.

Canonical JSON excludes wall-clock execution times and absolute output paths.
It includes complete config, data ID, data content hash, source code hash, split
policy, control rule and trade coverage. Identical input/config/code gives identical
JSON. Code changes intentionally change experiment identity. Acquisition files
are retained so smoke replay does not depend on a live API response.

## Historical trade data still needed

D currently has deterministic synthetic coverage and an aggregate-trade adapter.
For real BTCUSDT studies acquire Binance USD-M Futures aggTrades for the exact
observation dates, including earlier baseline windows when used. Required fields:
aggregate trade ID (a), price (p), quantity (q), trade time in UTC ms (T), buyer
maker flag (m); retain first/last constituent IDs (f/l) and acquisition manifest
when available. Retain symbol, source, downloaded range, checksums, duplicates
and missing-range reports. `trade_coverage` is an acquisition completeness claim,
not inferred from the first/last observed trade. Normalize and validate it first.

For this smoke the full reserved range is 2024-01-01T00:00Z to 2024-01-08T00:00Z;
research is only through 2024-01-05T04:00Z. No historical trades were downloaded.
Official sources: [aggregate trades API](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Compressed-Aggregate-Trades-List)
and [Binance public-data archives](https://github.com/binance/binance-public-data).
Use the USD-M futures archive, not spot/COIN-M. Archive pagination/coverage work
is deferred; candle OHLCV and taker candle totals cannot reconstruct exact VAP.

## Smoke configuration

168 real BTCUSDT 1h candles, 2024-01-01 through 2024-01-07 UTC.
Research: first 100; validation: next 34; reserved final test: last 34.
A: five fixed widths plus original 1h width. B: N=1,2. C: r=0.003,0.005.
All compare boundary exit and confirmed exit separation=0.001. TP/SL each
0.003,0.005; horizons 4,8; both directions. Twenty configurations total.
B/C use width=0.002 only to bound this smoke; run_grid accepts other widths.
These values exercise functionality and are not winning parameters.

Run instructions and output locations are in the root README. Stop after tests
and this smoke; do not proceed automatically to optimization or Phase 3.
