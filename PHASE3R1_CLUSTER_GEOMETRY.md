# Cluster Geometry, Age and Crossings

Raw full-map geometry is analyzed independently: imbalance, support/resistance
ratio, nearest distances/difference, above/below asymmetry, cluster count,
candidates per connected cluster, overlap pairs and repeated prices. No weighted
strength formula is introduced. Closed +/-0.004 intervals connect transitively,
so a small connected-component count does not imply a small number of observations.

| phase | feature | first_bucket | last_bucket | observed_buckets | nondecreasing | nonincreasing | high_minus_low | rank_correlation | ends_minus_middle | min_bucket_states |
|---|---|---|---|---|---|---|---|---|---|---|
| development | candidates_per_cluster | 0 | 3 | 4 | False | False | 0.032941 | 0.4 | 0.058996 | 2139 |
| development | clusters | 0 | 3 | 4 | False | False | -0.0475 | -0.8 | 0.049487 | 1072 |
| development | distance_difference | 0 | 3 | 4 | False | False | 0.0023127 | 0.2 | -0.02126 | 2074 |
| development | imbalance | 0 | 3 | 4 | False | False | 0.015979 | 0.2 | 0.033943 | 1913 |
| replication | candidates_per_cluster | 2 | 3 | 2 | True | False | 0.0066235 | 1 | NA | 827 |
| replication | clusters | 0 | 1 | 2 | True | False | 0.010146 | 1 | NA | 1122 |
| replication | distance_difference | 0 | 3 | 4 | False | False | -0.023411 | -0.8 | 0.0059911 | 1606 |
| replication | imbalance | 0 | 3 | 4 | True | False | 0.027296 | 1 | -0.0046684 | 1690 |

`*-clusters-within-count.csv` checks cluster relationships within candidate-count
buckets, rather than interpreting correlated count/cluster curves as independent
effects. `*-quarter-curves.parquet` distinguishes time/regime changes. Thousands
of candidates per connected region are spatial density, not thousands of independent
reactions. No superior strength formula is inferred from these dense maps.

A contributing level source-age buckets are <=30d, (30,180]d, (180,365]d and >365d.
Counts/type composition, prior crossing/visit means and full/half-band mean ages
are causal extra fields on A states. All original candidates remain active;
neither age nor crossing count changes A1. `old-levels-crossings.csv` studies the
joint old-level fraction and prior-crossing description. All per-feature curves
are available for age fractions, age-specific crossing/visit means and proximity.

| phase | feature | first_bucket | last_bucket | high_minus_low | min_bucket_states |
|---|---|---|---|---|---|
| development | full_mean_source_age_hours | 0 | 3 | -0.030864 | 2152 |
| development | half_mean_source_age_hours | 0 | 3 | -0.035268 | 2142 |
| development | mean_age | 0 | 3 | -0.028508 | 2154 |
| development | mean_prior_crossings | 0 | 3 | 0.056918 | 2153 |
| development | very_old_over_365d_fraction | 0 | 3 | -0.022774 | 2136 |
| replication | full_mean_source_age_hours | 0 | 3 | -0.0097858 | 1362 |
| replication | half_mean_source_age_hours | 0 | 3 | -0.010669 | 1424 |
| replication | mean_age | 0 | 3 | -0.012367 | 1296 |
| replication | mean_prior_crossings | 0 | 3 | -0.021176 | 1686 |
| replication | very_old_over_365d_fraction | 0 | 3 | -0.005409 | 1246 |

The A cluster distribution shifts from a development mean of about 15.73 to
about 2.88 in replication. Frozen cluster buckets 2 and 3 are absent in 2023;
do not relabel or refit them to manufacture a comparable four-bin curve.
Cluster associations may also change resolution/ambiguity rates for BOTH
directions, rather than offer directional information. Outcome composition
and within-count/quarter controls must accompany the TP fraction curves.

A crossing is a strict side change between consecutive closed prices after known_at;
equal closes are not strict crossings. A visit begins a run of closed candles whose
high/low contains the exact reference price. Last contact uses only end <= T.
This is not a claim about intrabar path order. Future event-time arrays may be
precomputed but queries count only events available by T; truncation tests pass.

These are market-state associations. They cannot by themselves prove an old level
caused a reaction or that crossing invalidates it. Decay/invalidation was not added.
