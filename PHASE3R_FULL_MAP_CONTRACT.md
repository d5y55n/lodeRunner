# Phase 3R: Full-Map Contract

## Clock and Identity

All timestamps are UTC milliseconds. A candle covers `[start,end)`, and its
OHLC becomes available at `end`. At hourly decision T, use exactly 20,400
contiguous candles with `start >= T-850 days` and `end <= T`. Decision price is
the final close. Step exactly one hour; remove the expired leftmost candle.
Missing history raises `INSUFFICIENT_850_DAY_HISTORY`; no shorter substitute.
Trade observations use `[observation_start,observation_end)`, excluding trades
at T. Hourly profiles are aggregates of actual trades, never candle volume.

`event_id` hashes symbol, timeframe and T. It is shared by A, both B widths,
both C reversal fractions and both D bins. `snapshot_id` additionally hashes
the complete configuration and price. Parameter sets, window semantics and
volume definitions are frozen in `data/phase3r/plan.json`. One A snapshot
contains both original-score and raw-map representations, not two independent
market observations.

## Candidates and Raw Features

A/B/C replay the existing detectors over the exact rolling candle window.
Candidates must be confirmed (`known_at <= T`) and their source dependencies
must be inside that window. `known_candidate_ids` joins the complete catalog,
which stores all reference prices, source timestamps, known_at, source IDs,
dependency start and detector metadata. There is no arbitrary top-N filter.

B retains strict local extrema independently at widths 1 and 2. It requires
both left and right confirming neighbors. C uses reversal fractions 0.003
and 0.005 separately, and never exposes an unconfirmed running extreme.
**Explicit initialization choice:** C trackers reset at each rolling left
boundary and replay the existing rules; this is not global-history C followed
by a date filter. Both conventions are plausible; this deliverable chooses
window-local reconstruction to avoid dependence on pre-window data.

A/B/C raw maps contain support/resistance totals, above/below/near partitions,
nearest price and candidate ID, signed/absolute relative distances and mean
absolute relative distance, density bands and nearby source-age statistics.
Nearest means nearest candidate of the given kind, regardless of which side
of current price it lies. Near means the strict original full-width band;
above/below are the remaining candidates. Density inner/outer use original
full/half geometry; remaining bands are 1.5-3, 3-10, and >=10 widths, using
`abs(current/reference-1)`. Distances reported as fractions of current price
instead use `reference/current-1`. These distinct denominators are explicit.

Nearby age summaries cover full and half band candidates, measured from source
time. Closed +/-width intervals define connected clusters and overlap pairs;
touching intervals connect. Duplicate reference counts do not deduplicate
scores. A has native scores; B/C do not. No distance-weighted strength score.

## D and Coverage

D is a neutral full rolling observed Volume-at-Price map, with fixed bins
50 and 100 USD independently. Bins are half-open, origin zero, floor-based.
All occupied bins are retained, not just concentration bins. Concentration
is quantity divided by mean occupied-bin quantity; the existing threshold
rule is `quantity >= mean * 1.5`. Adjacent concentration bins are not merged;
`concentration_region_count` counts qualifying bins, not connected regions.

Each bin stores lower/upper, buy/sell/total/delta, concentration, neutral kind,
and ABOVE/BELOW/STRADDLES relation. Stable bin identity is a spatial identity;
the snapshot ID distinguishes its changing rolling content. D has no directional
support/resistance count, source-candle timestamp, or native A score. Window
and availability are inherited from its snapshot, not invented candle sources.

Existing observable-coverage quarantines remain authoritative. An intersection
marks `INCOMPLETE_OBSERVABLE_COVERAGE` and sets
`eligible_complete_coverage_comparison=false`. Observed sums are inspectable,
but never treated as a complete traded-volume history. Nothing is reconstructed,
interpolated, zero-filled, or replaced with candle volume. A/B/C price history
can remain valid independently. See the volume integration report.

## Exports and Outcomes

`data/phase3r/sanity/` contains both JSONL and Parquet:

* `snapshots`: decision-time full states and complete candidate membership.
* `candidates`: A/B/C candidate catalog and provenance.
* `a-contributions`: explainable A weights per snapshot and candidate.
* `d-bins`: complete neutral rolling map by snapshot.
* `events`: one row per underlying market timestamp.
* `future-outcomes`: future-only labels and path statistics, joined by event ID.

Nested objects/lists are native in JSONL and canonical JSON strings in Parquet.
Do not merge future columns into decision-time feature inputs. Outcomes use
the existing engine, LONG/SHORT, TP and SL independently 0.003/0.005, horizons
4/8/24. The first future candle starts at T; current-candle extremes are excluded.
TP_FIRST, SL_FIRST, NEITHER, AMBIGUOUS, censoring, MFE/MAE and times are retained.
These are descriptive paths, not levered returns or executable orders.

Exact-score outcome tables and A1/A2/A3/A4 state/outcome exports are separate
analysis files. Repeated parameterizations and overlapping horizons are not
independent evidence. No strategy threshold, ranking or edge claim is made.
