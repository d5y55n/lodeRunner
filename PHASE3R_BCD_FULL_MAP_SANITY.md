# Phase 3R: B/C/D Full-Map Sanity

## Same Market-State Unit

Each configuration has 24 snapshots at the same hourly decision prices and
timestamps as A. All use the same exact 850-day window and share 24 event IDs.
The 576 outcome rows are stored once by underlying event, not duplicated
into thousands of candidate interaction observations. No B/C A-score transform.

| Configuration | All candidates per state, min-max | Supports, min-max | Resistances, min-max |
|---|---:|---:|---:|
| A reference | 10,753-10,755 | 5,376-5,377 | 5,376-5,378 |
| B width 1 | 9,617-9,622 | 4,822-4,826 | 4,793-4,797 |
| B width 2 | 5,802-5,806 | 2,887-2,889 | 2,915-2,917 |
| C reversal 0.003 | 19,267-19,273 | 9,791-9,800 | 9,472-9,477 |
| C reversal 0.005 | 16,090-16,096 | 8,251-8,258 | 7,838-7,840 |
| D bin 50 | 1,188 occupied bins | Not applicable | Not applicable |
| D bin 100 | 594 occupied bins | Not applicable | Not applicable |

Directional candidate catalog: 61,597 unique IDs across the run. Total saved
D bin rows: 42,768. D concentration threshold is 1.5 times mean occupied-bin
quantity in both configurations: 211 qualifying 50-dollar bins and 107
qualifying 100-dollar bins at each sampled timestamp. These are qualifying
bins, not merged connected regions. Neither size nor B/C parameter is selected.

## Checks Performed

All 168 snapshot contracts and 1,476,905 directional candidate memberships
were checked: complete membership length, confirmation at/before T, source
and dependency boundaries, raw count/density partitions. The first and last
decision were rebuilt for all five A/B/C configurations with candles after
T physically removed: ten exact snapshot matches.

D was rebuilt from time-truncated hourly trade data for two decisions and
both bin widths: four exact snapshot matches. First/last rolling D maps
were separately compared bin-by-bin with direct window aggregation at both
widths: four numerical matches (rtol 1e-10, atol 1e-7). All 42,768 bin rows
passed buy+sell conservation, delta and positive-quantity checks. Unit tests
also cover exact window edges, expired hours, missing hours and configuration
validation. No future trade data is included in decision-time sums.

## Inspection Findings and Limitations

At the first timestamp, connected cluster counts are A=7, B1=6, B2=7,
C0.003=3, C0.005=3. Corresponding overlap-pair counts are 769,779; 600,030;
217,730; 2,396,206; 1,669,341. This is a dense historical map, not independent
evidence from that many zones. Transitive interval chains explain why a
large candidate count can collapse into very few connected components.

Repeated reference prices are preserved: first-state duplicate-price counts
are 473, 681, 328, 1,522 and 1,156 respectively. C is especially dense because
the existing logic uses independent high/low trackers and confirmation resets,
not an alternating single ZigZag path. No deduplication or C-rule change was
introduced to make it look more like A/B. Window-local C initialization remains
an explicit interpretation choice, documented in the common contract.

D's broad 850-day structure changes slowly over this 24-hour sample; identical
concentration-bin counts do not mean per-bin quantities were frozen. The
first 50-dollar map contains about 361,116,464.587 BTC of observed cumulative
quantity, and the high share above current price is historical volume, not an
automatic resistance signal. Crucially, every D window intersects existing
coverage quarantines: **0/48 D snapshots qualify for complete-coverage
predictive comparison**. No fair predictive ranking of A/B/C/D is claimed.

The first A map has contributing source ages from 2 to 18,557 hours; original
logic does not expire a level merely because price crossed it. Its positive
LONG score at all 24 timestamps is faithfully reproduced but highlights this
sample's limited score coverage. No visually successful reaction was selected.
