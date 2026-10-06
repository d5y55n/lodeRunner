# 4h Independent Full-Map Results

| phase | feature | count | missing | median | q25 | q75 |
| --- | --- | --- | --- | --- | --- | --- |
| development | A1 | 2162 | 0 | -0.5 | -4.5 | 3.5 |
| development | A2 | 2162 | 0 | 0 | -4 | 3 |
| development | imbalance | 2147 | 15 | -0.018868 | -0.18275 | 0.16667 |
| development | nearby_count | 2162 | 0 | 31 | 18 | 43 |
| development | cluster_count | 2162 | 0 | 21 | 8 | 21 |
| development | candidates_per_cluster | 2162 | 0 | 133.86 | 133.48 | 349.88 |
| development | nearby_age_mean_hours | 2147 | 15 | 3654.4 | 2045 | 5642.2 |
| development | mean_prior_crossings | 2147 | 15 | 11.935 | 7.25 | 18.157 |
| development | mean_prior_visits | 2147 | 15 | 11.818 | 7.375 | 18.434 |
| development | quantity | 2161 | 1 | 58416 | 37447 | 87837 |
| development | delta | 2161 | 1 | 74.011 | -1538.9 | 1738.4 |
| replication | A1 | 2190 | 0 | 1 | -4 | 7 |
| replication | A2 | 2190 | 0 | 1 | -4 | 6 |
| replication | imbalance | 2189 | 1 | 0.047619 | -0.12 | 0.18367 |
| replication | nearby_count | 2190 | 0 | 48 | 30 | 68.75 |
| replication | cluster_count | 2190 | 0 | 3 | 3 | 4 |
| replication | candidates_per_cluster | 2190 | 0 | 931.33 | 699 | 936 |
| replication | nearby_age_mean_hours | 2189 | 1 | 4243.8 | 1942.1 | 6709 |
| replication | mean_prior_crossings | 2189 | 1 | 12.795 | 9.0286 | 17 |
| replication | mean_prior_visits | 2189 | 1 | 13.602 | 8.5385 | 17.03 |
| replication | quantity | 2188 | 2 | 47556 | 28814 | 84614 |
| replication | delta | 2188 | 2 | -218.56 | -1577.4 | 1159.9 |

## Outcome Grid Ranges
| phase | tp_first_rate_min | tp_first_rate_max | ambiguous_rate_min | ambiguous_rate_max | mfe_pct_min | mfe_pct_max | mae_pct_min | mae_pct_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | 0.18316 | 0.38943 | 0.29972 | 0.52758 | 0.95299 | 2.6043 | 0.95299 | 2.6043 |
| replication | 0.20137 | 0.48879 | 0.13196 | 0.3405 | 0.62895 | 1.896 | 0.62895 | 1.896 |

## A1/A2 Curve Shapes
| phase | feature | period | shape | grid_cells |
| --- | --- | --- | --- | --- |
| development | A1 | 2022-Q1 | NONMONOTONIC | 24 |
| development | A1 | 2022-Q2 | NONMONOTONIC | 24 |
| development | A1 | 2022-Q3 | INCREASING | 2 |
| development | A1 | 2022-Q3 | NONMONOTONIC | 22 |
| development | A1 | 2022-Q4 | NONMONOTONIC | 24 |
| development | A1 | ALL | NONMONOTONIC | 24 |
| development | A2 | 2022-Q1 | NONMONOTONIC | 24 |
| development | A2 | 2022-Q2 | NONMONOTONIC | 24 |
| development | A2 | 2022-Q3 | INCREASING | 8 |
| development | A2 | 2022-Q3 | NONMONOTONIC | 16 |
| development | A2 | 2022-Q4 | NONMONOTONIC | 24 |
| development | A2 | ALL | NONMONOTONIC | 24 |
| replication | A1 | 2023-Q1 | DECREASING | 1 |
| replication | A1 | 2023-Q1 | INCREASING | 1 |
| replication | A1 | 2023-Q1 | NONMONOTONIC | 22 |
| replication | A1 | 2023-Q2 | NONMONOTONIC | 24 |
| replication | A1 | 2023-Q3 | DECREASING | 2 |
| replication | A1 | 2023-Q3 | NONMONOTONIC | 22 |
| replication | A1 | 2023-Q4 | NONMONOTONIC | 24 |
| replication | A1 | ALL | DECREASING | 2 |
| replication | A1 | ALL | NONMONOTONIC | 22 |
| replication | A2 | 2023-Q1 | DECREASING | 3 |
| replication | A2 | 2023-Q1 | NONMONOTONIC | 21 |
| replication | A2 | 2023-Q2 | NONMONOTONIC | 24 |
| replication | A2 | 2023-Q3 | NONMONOTONIC | 24 |
| replication | A2 | 2023-Q4 | NONMONOTONIC | 24 |
| replication | A2 | ALL | DECREASING | 2 |
| replication | A2 | ALL | INCREASING | 1 |
| replication | A2 | ALL | NONMONOTONIC | 21 |

Shape labels describe observed frozen-bucket TP-first rates, separately by direction and grid. At least three supported buckets are required; they are not significance tests or fitted monotonic predictions. Quarter-specific differences show regime sensitivity rather than a selected winning regime.

Ranges cover every predeclared direction/TP/SL/horizon combination and are not a selected result. A1/A2 retain native units; B/C receive no A score transformation. Crossing/visit features use only closed candles after known_at and no later than T.

2023 is the **previously inspected replication period**, not an untouched final test. No 2024 market data, confluence performance, score summation, parameter ranking, or trading rule is used. All findings are descriptive, with overlapping outcomes and unadjusted multiple comparisons; no edge claim.
