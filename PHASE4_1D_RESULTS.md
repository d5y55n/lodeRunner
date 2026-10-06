# 1d Independent Full-Map Results

| phase | feature | count | missing | median | q25 | q75 |
| --- | --- | --- | --- | --- | --- | --- |
| development | A1 | 361 | 0 | -0.5 | -2 | 2 |
| development | A2 | 361 | 0 | 0 | -2 | 1 |
| development | imbalance | 361 | 0 | -0.043478 | -0.22222 | 0.17647 |
| development | nearby_count | 361 | 0 | 13 | 7 | 19 |
| development | cluster_count | 361 | 0 | 11 | 5 | 11 |
| development | candidates_per_cluster | 361 | 0 | 43.818 | 43.455 | 91.8 |
| development | nearby_age_mean_hours | 361 | 0 | 3943.2 | 2981.1 | 5592 |
| development | mean_prior_crossings | 361 | 0 | 5.2 | 3 | 7.2 |
| development | mean_prior_visits | 361 | 0 | 5.0714 | 3 | 7.5625 |
| development | quantity | 360 | 1 | 3.9646e+05 | 2.8832e+05 | 5.543e+05 |
| development | delta | 360 | 1 | 242.7 | -5494.8 | 6680.8 |
| replication | A1 | 365 | 0 | 1 | -3 | 6 |
| replication | A2 | 365 | 0 | 1 | -3 | 6 |
| replication | imbalance | 365 | 0 | 0.066667 | -0.125 | 0.27273 |
| replication | nearby_count | 365 | 0 | 22 | 16 | 28 |
| replication | cluster_count | 365 | 0 | 1 | 1 | 2 |
| replication | candidates_per_cluster | 365 | 0 | 447 | 224 | 453 |
| replication | nearby_age_mean_hours | 365 | 0 | 4073.7 | 2377 | 6465.8 |
| replication | mean_prior_crossings | 365 | 0 | 5.7692 | 4 | 7.3947 |
| replication | mean_prior_visits | 365 | 0 | 5.4348 | 4.0435 | 6.7391 |
| replication | quantity | 363 | 2 | 3.4642e+05 | 2.3644e+05 | 5.2409e+05 |
| replication | delta | 363 | 2 | -1205.4 | -6854.4 | 3734.9 |

## Outcome Grid Ranges
| phase | tp_first_rate_min | tp_first_rate_max | ambiguous_rate_min | ambiguous_rate_max | mfe_pct_min | mfe_pct_max | mae_pct_min | mae_pct_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | 0.072022 | 0.16667 | 0.7036 | 0.83844 | 2.2634 | 4.7127 | 2.2634 | 4.7127 |
| replication | 0.11507 | 0.23691 | 0.55068 | 0.74451 | 1.5549 | 3.6748 | 1.5549 | 3.6748 |

## A1/A2 Curve Shapes
| phase | feature | period | shape | grid_cells |
| --- | --- | --- | --- | --- |
| development | A1 | 2022-Q1 | NONMONOTONIC | 24 |
| development | A1 | 2022-Q2 | INCREASING | 12 |
| development | A1 | 2022-Q2 | NONMONOTONIC | 12 |
| development | A1 | 2022-Q3 | NONMONOTONIC | 24 |
| development | A1 | 2022-Q4 | NONMONOTONIC | 24 |
| development | A1 | ALL | DECREASING | 6 |
| development | A1 | ALL | NONMONOTONIC | 18 |
| development | A2 | 2022-Q1 | DECREASING | 6 |
| development | A2 | 2022-Q1 | NONMONOTONIC | 18 |
| development | A2 | 2022-Q2 | NONMONOTONIC | 24 |
| development | A2 | 2022-Q3 | INCREASING | 6 |
| development | A2 | 2022-Q3 | NONMONOTONIC | 18 |
| development | A2 | 2022-Q4 | INCREASING | 2 |
| development | A2 | 2022-Q4 | NONMONOTONIC | 22 |
| development | A2 | ALL | NONMONOTONIC | 24 |
| replication | A1 | 2023-Q1 | INCREASING | 2 |
| replication | A1 | 2023-Q1 | NONMONOTONIC | 22 |
| replication | A1 | 2023-Q2 | NONMONOTONIC | 24 |
| replication | A1 | 2023-Q3 | NONMONOTONIC | 24 |
| replication | A1 | 2023-Q4 | NONMONOTONIC | 24 |
| replication | A1 | ALL | NONMONOTONIC | 24 |
| replication | A2 | 2023-Q1 | NONMONOTONIC | 24 |
| replication | A2 | 2023-Q2 | NONMONOTONIC | 24 |
| replication | A2 | 2023-Q3 | NONMONOTONIC | 24 |
| replication | A2 | 2023-Q4 | NONMONOTONIC | 24 |
| replication | A2 | ALL | NONMONOTONIC | 24 |

Shape labels describe observed frozen-bucket TP-first rates, separately by direction and grid. At least three supported buckets are required; they are not significance tests or fitted monotonic predictions. Quarter-specific differences show regime sensitivity rather than a selected winning regime.

Ranges cover every predeclared direction/TP/SL/horizon combination and are not a selected result. A1/A2 retain native units; B/C receive no A score transformation. Crossing/visit features use only closed candles after known_at and no later than T.

Daily maps are structural/context layers. Native 24/48/72-hour outcomes cannot resolve 4-hour entry timing; ambiguity is retained rather than rescaled away.

2023 is the **previously inspected replication period**, not an untouched final test. No 2024 market data, confluence performance, score summation, parameter ranking, or trading rule is used. All findings are descriptive, with overlapping outcomes and unadjusted multiple comparisons; no edge claim.
