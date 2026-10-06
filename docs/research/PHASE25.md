# Phase 2.5: real aggregate trades and sanity inspection

This iteration uses the first UTC day of Phase 2's research period, fixed before
observing results: [2024-01-01 00:00, 2024-01-02 00:00). It does not inspect or
evaluate the reserved final test starting 2024-01-06 14:00 UTC. No ranking,
optimization, signals, orders or Phase 3 work is included.

## Acquisition and integrity contract

`app.market.aggregate_trades` downloads official USD-M daily archive ZIPs from
`https://data.binance.vision/data/futures/um/daily/aggTrades/BTCUSDT/` plus each
published `.CHECKSUM`. It streams downloads to `.partial` files and renames only
on success. Existing raw sources are pinned locally and rechecked, not silently
replaced if an upstream archive changes. Every day has an integrity report.

The archive contains aggregate ID, price, quantity, first/last constituent trade
IDs, transaction timestamp and buyer-is-maker flag. Headered and headerless files
are parsed. Booleans and integer fields are strict; prices/quantities must be
finite and positive. Times must fit the requested day in UTC milliseconds.

Verify SHA256 against the official filename/hash and ZIP CRC. Count malformed
records, duplicate aggregate IDs, exact normalized duplicate records, reversed
time/ID order, aggregate ID gaps and constituent ID boundary discontinuities.
Record expected coverage separately from first/last observed timestamp, boundary
distances and largest intertrade gap. Reports cap examples at 100 but count all.

Malformed data, duplicate aggregate IDs, order violations, timestamp errors and
aggregate ID gaps fail the dataset. Raw source and failure report remain. No
repair, sorting, deduplication or synthetic fill is performed. Constituent ID
discontinuities produce PASS_WITH_WARNINGS and retain the original ranges; their
presence is not automatically proof that an aggregate archive row was lost.
They remain unresolved observations, not a claim of complete individual-trade
coverage. Cross-day aggregate boundaries are checked and constituent boundaries
reported. Failed days stop a multi-day run.

Sources and derived outputs are separate:

- `data/raw/binance/aggTrades/`: original ZIP, official checksum, per-day report.
- `data/processed/aggTrades/`: normalized Parquet and range-integrity manifest.
- `data/research/phase25/`: bins, features, labels, sample, visualization.

The parser code hash and source/normalized checksums identify the acquired dataset.
Replay verifies both raw archive and normalized file hashes before research.

Supplementary `fetch_rest(start,end,raw_dir,client)` supports bounded windows up
to one hour, aggregate-ID pagination, raw JSON page preservation and local SHA256
hashes. Those are NOT official checksums. A fromId page can contain records after
the requested end; those are parsed, retained raw, counted as excluded and not
included in the bounded normalized dataset. REST errors produce failure reports.
The actual historical run used archives, not REST. REST tests use deterministic
mock responses; production REST acquisition was not exercised this iteration.

Official format/checksum reference:
[Binance public data](https://github.com/binance/binance-public-data).

## Real data and integrity findings

Downloaded 761,222 aggregate trades for BTCUSDT, 2024-01-01 UTC.
Official SHA256 and archive CRC pass. Invalid rows, duplicate IDs/records,
reversed ordering and aggregate ID discontinuities: all zero.
Observed first timestamp: 1704067200038; last: 1704153599978.
Leading boundary distance: 38 ms; trailing: 22 ms; largest gap: 6,959 ms.

There are **28 constituent first/last trade ID discontinuities**. The report is
PASS_WITH_WARNINGS, not a clean assertion of underlying individual-trade coverage.
No rows were inserted to fill them. An independent check against the existing
hourly kline quantities finds differences, with max absolute hourly difference
**1.564 BTC**. Some adjacent hourly differences offset; the precise cause of the
archive/kline discrepancy is unconfirmed. Both raw values are retained in
`run-report.json`. Kline volume is a diagnostic reference only, never VAP input.

## Unchanged detector rules and fixed inspection configuration

Phase 2 A/B/C algorithms and D's concentration rule are unchanged. Trade adds
optional first/last IDs. An immutable timestamp index uses bisect to restrict
work to the requested window. Tests verify identical indexed/plain aggregation
and decision features. This is computational indexing, not parameter optimization.

- A: original reversal candle references; no weights.
- B: strict local extrema, comparison width 1.
- C: later-close confirmation, reversal fraction 0.003.
- D: completed one-hour windows; 50 and 100 USDT price bins; quantity divided by
  mean occupied-bin quantity >= 1.5. Empty bins do not enter the baseline.
- A/B/C/D candidate research zones use +/-0.2% half-width and boundary-close exit.
- Volume features: one-hour trailing window, preceding equal one-hour baseline.
- Hypothetical outcomes: LONG and SHORT, TP=SL=0.3%, horizon=4 hourly candles.

These are inspectable fixed configurations, not selected winners. D's native
50/100-USDT bin bounds remain available separately from its midpoint-centered
percentage research zone. Around BTC price 42,000 the latter is about 168 USDT
wide and can be materially wider than its native bin. Do not confuse the two.

Native bins are zero-anchored [lower,upper). Zone volume uses inclusive zone
bounds, matching Phase 2. Both use trade timestamps in [start,end). Buyer maker
false is aggressive buy; true is aggressive sell. Delta = buy minus sell.
No candle volume is input to either aggregation.

All decision features at T use trades strictly before T: [T-W,T). Baseline is
[T-2W,T-W). Zero baseline gives null ratio rather than infinity. Missing coverage
is explicitly MISSING_TRADE_COVERAGE. Candidate confirmation features and later
interaction features each have their own as-of timestamps. Historical event-time
availability is assumed; network receipt latency is not reconstructed.

## Exports and inspection

| Artifact | Contents |
| --- | --- |
| plan.json | All detector, width, exit, TP/SL, horizon, source/code/template hash settings |
| candles.csv/json | Selected research-day OHLC only |
| candidates.csv/json | Source/known_at, type, price, zone bounds, confirmation-time volume |
| decision_features.csv/json | First-visit time/number, reference close, past-only volume |
| interactions_retrospective.csv/json | Completed visit facts, explicitly retrospective |
| outcomes_future.csv/json | Future labels/excursions, linked only by event ID |
| volume_at_price.csv/json | Exact bins, quantities/sides/delta, interval and bin config |
| sample.json | Deterministic selected zone IDs and selection reasons |
| summary.json / run-report.json | Counts, integrity provenance and reconciliation |
| export-manifest.json | SHA256 of export files for repeatability |
| sanity.html | Offline candlesticks, toggles, confirmation timeline, inspection tables |

Bin lineage stores trade count and trade-ID hash instead of embedding hundreds of
thousands of IDs in the chart. The pinned raw/normalized sources and exact bin
config reconstruct constituent membership. Complete IDs are still available
inside the existing Phase 2 aggregation API.

The HTML is standalone and makes no network requests. The as-of clock filters
candles, known candidates and observed interactions, including price-axis bounds.
Zone shading starts at known_at. The hollow source marker and dashed confirmation
delay appear only after confirmation. Future outcomes and completed-visit facts
are not embedded in the page. A source marker is not a pre-confirmation signal.

Sampling is deterministic: order by known_at then candidate ID; take first 3
per detector-configuration and support/resistance kind (first 6 for each D
configuration), add earliest 2 repeated-visit zones per detector and earliest
3 cross-detector overlapping pairs. All candidates remain in exports. Repeated
visit selection is retrospective and declared as such; no outcome is consulted.

## Real-data counts and interpretation

- A: 6 supports, 6 resistances; real-volume features on 17 interactions.
- B: 4 supports, 4 resistances; features on 13 interactions.
- C: 14 supports, 6 resistances; features on 26 interactions.
- D: 44 concentration candidates for 50-USDT bins; 19 for 100-USDT bins.
- 232 VAP bins across both configurations; 177 visits, 49 repeatedly visited zones.
- 354 hypothetical outcome rows are stored separately, not interpreted as trades.
- 4 early D candidates lack the preceding baseline window; no pre-period data is
  invented. All later interaction features in this run have window coverage.
- 21 interaction features have zero baseline quantity and a null relative ratio.

C emits more supports than resistances in this slice (14 vs 6); its independent
resetting extrema can create nearby repeated candidates. D percentage zones can
overlap broadly. There are 807 cross-detector overlapping zone pairs, so these
are not 807 independent confirmations. Some horizons are censored at day end.
These observations justify inspection, not algorithm changes or predictive claims.

## Validation and limits

Run the full suite from backend with `.venv/Scripts/python.exe -m pytest` or
`uv run pytest`. Added tests cover source parsing/checksums, corruption reports,
duplicates, timestamp units, ordering, invalid trades, REST pagination, bin edges,
side/delta, exact indexed aggregation, future-mutation leakage, baseline windows,
D contract, final-period exclusion, deterministic sampling and reproducible exports.

The real build repeats computation and file writing, comparing both content and
file hashes. `tests/check_sanity_script.cjs` compiles the HTML JavaScript without
opening a browser and checks for external dependencies. The browser tool blocked
the local file URL under its security policy; that restriction was not bypassed.
Visual browser rendering and interactive screenshot QA are therefore unverified.
The report remains directly usable as a local offline HTML file for human inspection.

No final-test evaluation, parameter ranking, optimization or Phase 3 was performed.
