# 2023: previously inspected replication period

This is not untouched validation. Development A and B/C analyses were completed
before freeze `6b8bfc02671f6f9621b522bf65412e697f5f114bec47e371d5cefb9feb431c95`. The same code, detector parameters, feature
definitions, score distributions, grids and development quantile boundaries were
then used for 8,760 2023 timestamps. No score threshold or regime cut was refit.

Development versus replication shape comparison:

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

Raw feature distributions may shift beyond development quantile ranges; outer
buckets keep their frozen bounds and no balancing/refit is performed. Compare
the entire shape and quarter-specific effects, not one overall rate. Half-band
case tables and within-A2 contrasts use the same frozen definitions; B/C geometry
is compared under the same event framework. No single metric selects a winner.

Future outcomes for late December 2023 are censored at 2024-01-01, using only
closed candles with open times in 2023. No 2024 candle is read to complete a label.
