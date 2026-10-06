# 15m Independent Full-Map Results

| phase | feature | count | missing | median | q25 | q75 |
| --- | --- | --- | --- | --- | --- | --- |
| development | A1 | 34585 | 0 | -1 | -10.5 | 7 |
| development | A2 | 34585 | 0 | -1 | -10 | 7 |
| development | imbalance | 34572 | 13 | -0.010101 | -0.089509 | 0.074627 |
| development | nearby_count | 34585 | 0 | 136 | 80 | 203 |
| development | cluster_count | 34585 | 0 | 24 | 8 | 28 |
| development | candidates_per_cluster | 34585 | 0 | 1790.7 | 1544 | 5350.1 |
| development | nearby_age_mean_hours | 34572 | 13 | 3486.1 | 1800.3 | 5599.6 |
| development | mean_prior_crossings | 34572 | 13 | 47.967 | 30.858 | 71.494 |
| development | mean_prior_visits | 34572 | 13 | 45.272 | 29.724 | 66.689 |
| development | quantity | 34580 | 5 | 3198.6 | 1851.6 | 5589.8 |
| development | delta | 34580 | 5 | 3.6005 | -278.79 | 291.6 |
| replication | A1 | 35040 | 0 | -1.5 | -11.5 | 11 |
| replication | A2 | 35040 | 0 | -1 | -10 | 10 |
| replication | imbalance | 35039 | 1 | -0.0095602 | -0.07067 | 0.06792 |
| replication | nearby_count | 35040 | 0 | 213 | 124 | 310 |
| replication | cluster_count | 35040 | 0 | 2 | 2 | 3 |
| replication | candidates_per_cluster | 35040 | 0 | 21414 | 14309 | 21463 |
| replication | nearby_age_mean_hours | 35039 | 1 | 3977.9 | 1921.9 | 6735.6 |
| replication | mean_prior_crossings | 35039 | 1 | 50.211 | 33.148 | 68.642 |
| replication | mean_prior_visits | 35039 | 1 | 47.149 | 31.982 | 65.259 |
| replication | quantity | 35038 | 2 | 2369.2 | 1323.9 | 4555.7 |
| replication | delta | 35038 | 2 | -12.864 | -265.84 | 238.53 |

## Outcome Grid Ranges
| phase | tp_first_rate_min | tp_first_rate_max | ambiguous_rate_min | ambiguous_rate_max | mfe_pct_min | mfe_pct_max | mae_pct_min | mae_pct_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | 0.32589 | 0.61279 | 0.016546 | 0.057379 | 0.9469 | 2.5991 | 0.9469 | 2.5991 |
| replication | 0.28368 | 0.62206 | 0.004768 | 0.018973 | 0.62411 | 1.8921 | 0.62411 | 1.8921 |

## A1/A2 Curve Shapes
| phase | feature | period | shape | grid_cells |
| --- | --- | --- | --- | --- |
| development | A1 | 2022-Q1 | NONMONOTONIC | 24 |
| development | A1 | 2022-Q2 | NONMONOTONIC | 24 |
| development | A1 | 2022-Q3 | NONMONOTONIC | 24 |
| development | A1 | 2022-Q4 | DECREASING | 1 |
| development | A1 | 2022-Q4 | INCREASING | 9 |
| development | A1 | 2022-Q4 | NONMONOTONIC | 14 |
| development | A1 | ALL | INCREASING | 3 |
| development | A1 | ALL | NONMONOTONIC | 21 |
| development | A2 | 2022-Q1 | DECREASING | 1 |
| development | A2 | 2022-Q1 | NONMONOTONIC | 23 |
| development | A2 | 2022-Q2 | NONMONOTONIC | 24 |
| development | A2 | 2022-Q3 | NONMONOTONIC | 24 |
| development | A2 | 2022-Q4 | INCREASING | 6 |
| development | A2 | 2022-Q4 | NONMONOTONIC | 18 |
| development | A2 | ALL | INCREASING | 4 |
| development | A2 | ALL | NONMONOTONIC | 20 |
| replication | A1 | 2023-Q1 | DECREASING | 1 |
| replication | A1 | 2023-Q1 | INCREASING | 2 |
| replication | A1 | 2023-Q1 | NONMONOTONIC | 21 |
| replication | A1 | 2023-Q2 | DECREASING | 6 |
| replication | A1 | 2023-Q2 | INCREASING | 2 |
| replication | A1 | 2023-Q2 | NONMONOTONIC | 16 |
| replication | A1 | 2023-Q3 | NONMONOTONIC | 24 |
| replication | A1 | 2023-Q4 | NONMONOTONIC | 24 |
| replication | A1 | ALL | DECREASING | 4 |
| replication | A1 | ALL | NONMONOTONIC | 20 |
| replication | A2 | 2023-Q1 | INCREASING | 4 |
| replication | A2 | 2023-Q1 | NONMONOTONIC | 20 |
| replication | A2 | 2023-Q2 | DECREASING | 3 |
| replication | A2 | 2023-Q2 | NONMONOTONIC | 21 |
| replication | A2 | 2023-Q3 | NONMONOTONIC | 24 |
| replication | A2 | 2023-Q4 | DECREASING | 3 |
| replication | A2 | 2023-Q4 | INCREASING | 2 |
| replication | A2 | 2023-Q4 | NONMONOTONIC | 19 |
| replication | A2 | ALL | DECREASING | 1 |
| replication | A2 | ALL | INCREASING | 4 |
| replication | A2 | ALL | NONMONOTONIC | 19 |

Shape labels describe observed frozen-bucket TP-first rates, separately by direction and grid. At least three supported buckets are required; they are not significance tests or fitted monotonic predictions. Quarter-specific differences show regime sensitivity rather than a selected winning regime.

Ranges cover every predeclared direction/TP/SL/horizon combination and are not a selected result. A1/A2 retain native units; B/C receive no A score transformation. Crossing/visit features use only closed candles after known_at and no later than T.

2023 is the **previously inspected replication period**, not an untouched final test. No 2024 market data, confluence performance, score summation, parameter ranking, or trading rule is used. All findings are descriptive, with overlapping outcomes and unadjusted multiple comparisons; no edge claim.
