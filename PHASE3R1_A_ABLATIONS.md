# A1/A2/A3/A4 and Outer Band

A1 retains original weights. A2 removes only the outer half band. A3 analyzes
nearby support/resistance counts, imbalance and ratio. A4 analyzes continuous
distances and geometry. No representation is translated into a trading cutoff.

| phase | states | sign_flips | changed |
|---|---|---|---|
| development | 8647 | 430 | 7863 |
| replication | 8760 | 571 | 8199 |

These are paired observations at identical timestamps. `half-band-paired-cases.csv`
reports same sign, sign flip and one-zero cases; substantial magnitude difference
means a nonzero difference at least the development 75th percentile. The threshold
is descriptive and frozen in 2023, not an optimized trading parameter.
`half-band-within-A2.csv` conditions on the original full-band score bucket and
examines signed outer contribution; the quarter version checks temporal robustness.
`half-band-block-intervals.csv` uses shared time blocks rather than independent
A1/A2 sample tests. A1 and A2 cannot have different realized paths at the same T;
only the information partition differs.

The outer band materially changes many states, but state changes alone do not
establish incremental information. Interpret within-A2 and chronological/replication
contrasts together. This phase does not declare it either a winning addition or
discardable noise based on one metric. Raw count/geometry curves remain separate.

| phase | feature | first_bucket | last_bucket | observed_buckets | nondecreasing | nonincreasing | high_minus_low | rank_correlation | ends_minus_middle | min_bucket_states |
|---|---|---|---|---|---|---|---|---|---|---|
| development | A1 | 0 | 3 | 4 | False | False | 0.018348 | 0.2 | 0.02927 | 2058 |
| development | A2 | 0 | 3 | 4 | False | False | 0.02325 | 0.4 | 0.018242 | 2040 |
| development | distance_difference | 0 | 3 | 4 | False | False | 0.0023127 | 0.2 | -0.02126 | 2074 |
| development | imbalance | 0 | 3 | 4 | False | False | 0.015979 | 0.2 | 0.033943 | 1913 |
| replication | A1 | 0 | 3 | 4 | True | False | 0.035862 | 1 | -0.0065942 | 1559 |
| replication | A2 | 0 | 3 | 4 | True | False | 0.044 | 1 | 0.011474 | 1555 |
| replication | distance_difference | 0 | 3 | 4 | False | False | -0.023411 | -0.8 | 0.0059911 | 1606 |
| replication | imbalance | 0 | 3 | 4 | True | False | 0.027296 | 1 | -0.0046684 | 1690 |

These are descriptive associations in autocorrelated states, not executable returns or an edge claim. The illustrative TP=SL=0.003, 8h grid is fixed for readability; all 24 grids are exported. AMBIGUOUS and NEITHER remain in complete-state denominators. Gross expectancy excludes ambiguous, neither and censored observations and excludes costs.
