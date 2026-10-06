# Phase 3 execution design

Phase 2/2.5 are approved. Phase 3 adds multi-year development and a single frozen
validation evaluation. User-confirmed periods: development [2021-01-01,2023-01-01)
UTC, validation [2023-01-01,2024-01-01) UTC. ALL 2024 data is reserved and must
remain untouched. No live signals or trading execution are authorized.

## Identity

Underlying event identity is symbol + timeframe + decision-close timestamp.
This conservative identity intentionally collapses simultaneous spatially distinct
zones. Candidate identity, configuration identity, zone-visit identity and outcome
measurement identity remain separate. Counts must not substitute measurement rows
for independent observations. Adjacent events and overlapping horizons also remain
dependent even after this deduplication; no naive significance claims are allowed.

## Context and controls

Context uses only closed prices up to the decision timestamp: standard deviation
of trailing log returns and trailing directional return. Quantile fitting rejects
records outside the declared development fitting interval. Matching rejects
thresholds fitted after the target timestamp. For causal development comparisons,
use an earlier calibration segment or expanding past-only fits. Full-development
volume quantiles can describe development retrospectively but are not online
features within their own fitting period. Validation uses frozen development fits.

The matched control is the most recent earlier context observation in the same
volatility/return quantile cells whose outcome horizon ends no later than the
target timestamp. Labels are never passed to the matcher. Missing matches remain
missing. Control reuse must be counted and reported, not treated as independent
new control observations.

## Aggregate-trade warning investigation

The [official Binance aggregate-trade documentation](https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-streams/market)
describes aggregation of same-price, same-taking-side fills and excludes insurance
fund/ADL trades. A numerical ID gap alone does not establish lost executions.
Specific gap causes cannot be inferred from this general documentation. This run
uses only 2021-2023 sources and the outcome-blind coverage policy and forensic
manifest. Earlier Phase 2.5 observations are not re-evaluated using reserved data.
Preserve constituent-ID warnings and do not reconstruct purported missing quantity.
Source agreement is not proof of coverage of every underlying execution type.

Preflight HEAD checks: official monthly BTCUSDT aggregate ZIP sizes are
917,138,866 bytes (2021-01), 782,927,921 (2022-01), 388,543,348 (2023-01).
Do not extrapolate these three files as a verified total download size.

Execution status is recorded in data/phase3/research-progress.json and per-phase completion
artifacts, rather than inferred from partially written CSVs. No empirical edge claims.

## Current scope and execution gates

The current runner supports 1h candles, fixed half-widths 0.0005/0.001/0.002/0.003/0.005
and the original 1h half-width 0.004. Other original timeframe mappings remain in
the Phase 2 engine but are NOT yet covered by this long-range runner. Do not claim
that 15m/4h/1d research is complete. D bins are independently 50 and 100 USD;
concentration threshold remains 1.5 times occupied-bin mean quantity.

The acquisition CLI scans all 36 months and writes per-source integrity reports.
An aggregate-ID discontinuity now requires the predeclared coverage forensics in
PHASE3_COVERAGE_POLICY.md; numerical gaps alone do not exclude a period. Selected
official monthly or daily sources must pass ordering/value/duplicate checks.
Volume-only quarantine affects D formation and volume features, never verified
A/B/C price history. No synthetic replacement rows or candle-volume substitution.
The runner uses bounded parquet sinks and exact multiplicity-weighted summaries;
measurements are losslessly normalized through a DuckDB view with stable IDs.
Full-scale completion is recorded separately from the small real-data smoke test.

Decision features use [T-1h,T), with same-zone baseline [T-2h,T-1h). Exact observed
prices are grouped before range queries; float64 sums have normal numerical
roundoff, not mathematically exact decimal arithmetic. Two monthly caches and
prefix sums avoid repeated raw-trade scans. Outcomes and retrospective interaction
duration/exit facts are stored separately from decision-time features.

Development volume quantiles are retrospective distribution descriptions, fitted
over zone-interaction rows. They are not online-available thresholds inside that
same development period and can overweight frequently revisited zone geometries.
Context matching thresholds use January 2021 only; no matched development result
before February 2021 is eligible. Matching may reuse controls, so both matched
target counts and unique control event counts are reported. Rates are shown both
row-weighted and deduplicated by event and outcome configuration. Neither implies
independent samples or statistical significance.

Validation inclusion is predeclared: all original-width detector settings with
at least 100 unique development events; no win-rate ranking. The entire selected
configuration, bucket thresholds, selection rule and plan are hash-locked before
the single validation invocation. Validation cannot automatically rerun after its
start marker is written, including after a failure; operational recovery needs
explicit review of prior artifacts, not a new tuned evaluation.

## 2021-02 archive discrepancy

The checksum-verified monthly source contains 55,186,588 rows and three aggregate
ID jumps, identified by the first row after each jump:

| UTC timestamp | Previous ID | Next ID | Missing ID numbers |
| --- | ---: | ---: | ---: |
| 2021-02-09 05:35:35.345 | 308181841 | 308204627 | 22,785 |
| 2021-02-09 09:39:35.972 | 308680643 | 308680652 | 8 |
| 2021-02-24 06:28:55.219 | 338732069 | 338732083 | 13 |

The official daily archives for February 9 and 24 pass checksum and ZIP CRC,
but contain NONE of these absent IDs. This is not evidence that the missing IDs
necessarily correspond to actual executions; the cause remains unresolved.
No repair was applied. User input was requested on explicit exclusion of affected
segments versus postponing research until complete source coverage is available.
May 2021 contains 97,970,934 archive rows and one aggregate jump from 504067347 to
504624374, first timestamp after the jump 2021-05-19 13:40:10.709 UTC. The 557,026
absent ID numbers are also absent from the checksum/CRC-verified official daily
archive. Excluding a severe market-move interval can introduce selection bias;
this limitation must accompany any future explicit exclusion policy. No repair
or exclusion has yet been applied. Reports are in data/phase3/integrity.
