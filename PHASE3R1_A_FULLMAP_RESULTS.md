# A Full-Map Results

| phase | states | score_min | score_max | exact_scores | zero | negative | positive | sign_flips | changed |
|---|---|---|---|---|---|---|---|---|---|
| development | 8647 | -36 | 49 | 153 | 193 | 4714 | 3740 | 430 | 7863 |
| replication | 8760 | -48 | 49 | 165 | 163 | 4228 | 4369 | 571 | 8199 |

Unlike the 24-state sanity sample, development contains negative, zero and positive
scores. Full exact score distributions (frequency/composition), outcome grids,
quarter and volatility/return regime tables are under each phase's `analysis/`.
LONG score is A1; SHORT score is its exact negative. SHORT results grouped by A1
must therefore be read in the reverse score direction, not as independent scores.

Illustrative frozen-bucket shapes:

| phase | feature | first_bucket | last_bucket | observed_buckets | nondecreasing | nonincreasing | high_minus_low | rank_correlation | ends_minus_middle | min_bucket_states |
|---|---|---|---|---|---|---|---|---|---|---|
| development | A1 | 0 | 3 | 4 | False | False | 0.018348 | 0.2 | 0.02927 | 2058 |
| development | A2 | 0 | 3 | 4 | False | False | 0.02325 | 0.4 | 0.018242 | 2040 |
| development | candidates_per_cluster | 0 | 3 | 4 | False | False | 0.032941 | 0.4 | 0.058996 | 2139 |
| development | clusters | 0 | 3 | 4 | False | False | -0.0475 | -0.8 | 0.049487 | 1072 |
| development | distance_difference | 0 | 3 | 4 | False | False | 0.0023127 | 0.2 | -0.02126 | 2074 |
| development | imbalance | 0 | 3 | 4 | False | False | 0.015979 | 0.2 | 0.033943 | 1913 |
| replication | A1 | 0 | 3 | 4 | True | False | 0.035862 | 1 | -0.0065942 | 1559 |
| replication | A2 | 0 | 3 | 4 | True | False | 0.044 | 1 | 0.011474 | 1555 |
| replication | candidates_per_cluster | 2 | 3 | 2 | True | False | 0.0066235 | 1 | NA | 827 |
| replication | clusters | 0 | 1 | 2 | True | False | 0.010146 | 1 | NA | 1122 |
| replication | distance_difference | 0 | 3 | 4 | False | False | -0.023411 | -0.8 | 0.0059911 | 1606 |
| replication | imbalance | 0 | 3 | 4 | True | False | 0.027296 | 1 | -0.0046684 | 1690 |

`curve-shapes.csv` answers monotonicity across every grid: nondecreasing and
nonincreasing are explicit finite-sample checks; rank correlation, high-minus-low,
ends-minus-middle (U/inverted-U diagnostic) and largest adjacent step are retained.
These descriptors do not prove a population U-shape or identify a trade threshold.
Quarter and regime tables test stability rather than selecting the best shape.

Explicit A1 monotonicity counts across the 12 grids per direction:

| phase | direction | grids | nondecreasing | nonincreasing |
|---|---|---|---|---|
| development | LONG | 12 | 0 | 0 |
| development | SHORT | 12 | 0 | 0 |
| replication | LONG | 12 | 5 | 0 |
| replication | SHORT | 12 | 0 | 2 |

Development has no monotonic four-bucket A1 curve in either direction. In 2023,
5/12 LONG curves increase and 2/12 SHORT curves decrease with A1. These overlapping
grids are not independent replications. Increasing LONG score or decreasing A1
for SHORT therefore does not show a consistently monotonic relationship across
periods. The illustrative development LONG curve has higher endpoints than middle
buckets, whereas the replication curve increases. This is descriptive shape
variation, not proof of a population U-shape, flatness, or a useful threshold.
For the illustrative LONG grid, the endpoint contrast changes sign in 2022Q1
and again in 2023Q4. Pooled increasing curves do not establish regime stability.

Bucket-support columns matter: high-minus-low compares the observed endpoints.
If replication lacks a development bucket, it is NOT the same endpoint contrast.
A two-bucket monotonic flag is not evidence for a four-bucket monotonic shape.

What was A1 capturing? Rank correlations with descriptive state facts:

| phase | feature | spearman_with_A1 |
|---|---|---|
| development | A2 | 0.95749 |
| development | imbalance | 0.97703 |
| development | candidate_count | 0.006535 |
| development | clusters | 0.015725 |
| development | mean_age | 0.026317 |
| replication | A2 | 0.94974 |
| replication | imbalance | 0.96867 |
| replication | candidate_count | 0.074952 |
| replication | clusters | -0.044522 |
| replication | mean_age | -0.0946 |

A1 is full-band support-minus-resistance plus half the outer imbalance, so a
strong association with nearby imbalance is structural. It is not independent
confirmation of predictive value. Score magnitude alone cannot establish edge.

These are descriptive associations in autocorrelated states, not executable returns or an edge claim. The illustrative TP=SL=0.003, 8h grid is fixed for readability; all 24 grids are exported. AMBIGUOUS and NEITHER remain in complete-state denominators. Gross expectancy excludes ambiguous, neither and censored observations and excludes costs.

Uncertainty uses fixed nonoverlapping seven-day UTC block resampling, 1,000 draws,
seed 3101. Intervals are descriptive conditional-rate minus same-period baseline;
fewer than five represented blocks yields no interval. There are no row-level
p-values. A seven-day block cannot eliminate every long-memory/regime concern;
many examined features and grids are exploratory comparisons, not confirmatory tests.

Diagnostic plots: `data/phase3r1/reports/diagnostics.html` (96 SVGs, all outcome grids). Curves connect frozen development buckets for readability; no threshold is chosen.
