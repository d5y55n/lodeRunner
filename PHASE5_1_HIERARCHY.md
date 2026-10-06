# Exact 1TF -> 2TF -> 3TF -> 4TF Hierarchy

The primary path is 15m -> 15m+1h -> 15m+1h+4h -> all four, not generic any-k counts.

| phase | direction | period | shape | grids |
| --- | --- | --- | --- | --- |
| development | LONG | 1 | NONLINEAR | 12 |
| development | LONG | 2 | NONLINEAR | 12 |
| development | LONG | 3 | MONOTONIC_INCREASING | 5 |
| development | LONG | 3 | NONLINEAR | 7 |
| development | LONG | 4 | MONOTONIC_INCREASING | 7 |
| development | LONG | 4 | NONLINEAR | 5 |
| development | LONG | ALL | MONOTONIC_INCREASING | 11 |
| development | LONG | ALL | NONLINEAR | 1 |
| development | SHORT | 1 | NONLINEAR | 12 |
| development | SHORT | 2 | NONLINEAR | 12 |
| development | SHORT | 3 | MONOTONIC_INCREASING | 5 |
| development | SHORT | 3 | NONLINEAR | 7 |
| development | SHORT | 4 | MONOTONIC_DECREASING | 10 |
| development | SHORT | 4 | NONLINEAR | 2 |
| development | SHORT | ALL | MONOTONIC_DECREASING | 3 |
| development | SHORT | ALL | NONLINEAR | 9 |
| replication | LONG | 1 | MONOTONIC_INCREASING | 10 |
| replication | LONG | 1 | NONLINEAR | 2 |
| replication | LONG | 2 | MONOTONIC_DECREASING | 3 |
| replication | LONG | 2 | NONLINEAR | 9 |
| replication | LONG | 3 | MONOTONIC_DECREASING | 3 |
| replication | LONG | 3 | NONLINEAR | 9 |
| replication | LONG | 4 | MONOTONIC_INCREASING | 2 |
| replication | LONG | 4 | NONLINEAR | 10 |
| replication | LONG | ALL | MONOTONIC_DECREASING | 1 |
| replication | LONG | ALL | NONLINEAR | 11 |
| replication | SHORT | 1 | MONOTONIC_INCREASING | 1 |
| replication | SHORT | 1 | NONLINEAR | 11 |
| replication | SHORT | 2 | MONOTONIC_INCREASING | 4 |
| replication | SHORT | 2 | NONLINEAR | 8 |
| replication | SHORT | 3 | MONOTONIC_INCREASING | 4 |
| replication | SHORT | 3 | NONLINEAR | 8 |
| replication | SHORT | 4 | MONOTONIC_DECREASING | 1 |
| replication | SHORT | 4 | NONLINEAR | 11 |
| replication | SHORT | ALL | NONLINEAR | 12 |

development: 72 supported pooled comparison/grid cells: 44 positive, 28 negative TP_FIRST differences. Range [-0.0103114, 0.0261586]. 2 intervals entirely above zero; 0 entirely below. These dependent cells are not separate discoveries or selected rules.

replication: 72 supported pooled comparison/grid cells: 38 positive, 34 negative TP_FIRST differences. Range [-0.0188464, 0.0307448]. 4 intervals entirely above zero; 1 entirely below. These dependent cells are not separate discoveries or selected rules.

| family | direction | metric | grids | supported_both | all_2022_quarters_and_rep | all_eight_quarters |
| --- | --- | --- | --- | --- | --- | --- |
| conditional_hierarchy | LONG | AMBIGUOUS | 36 | 36 | 2 | 1 |
| conditional_hierarchy | LONG | SL_FIRST | 36 | 36 | 11 | 0 |
| conditional_hierarchy | LONG | TP_FIRST | 36 | 36 | 5 | 1 |
| conditional_hierarchy | SHORT | AMBIGUOUS | 36 | 36 | 3 | 0 |
| conditional_hierarchy | SHORT | SL_FIRST | 36 | 36 | 4 | 0 |
| conditional_hierarchy | SHORT | TP_FIRST | 36 | 36 | 2 | 1 |
| hierarchy_increment | LONG | AMBIGUOUS | 36 | 36 | 2 | 1 |
| hierarchy_increment | LONG | SL_FIRST | 36 | 36 | 11 | 0 |
| hierarchy_increment | LONG | TP_FIRST | 36 | 36 | 3 | 1 |
| hierarchy_increment | SHORT | AMBIGUOUS | 36 | 36 | 0 | 0 |
| hierarchy_increment | SHORT | SL_FIRST | 36 | 36 | 4 | 0 |
| hierarchy_increment | SHORT | TP_FIRST | 36 | 36 | 2 | 1 |

Secondary paths are separately labeled in cohorts.csv. No path is ranked or selected.

2023 is the **previously inspected replication period**, not an untouched final test. No 2024, live trading, leverage, new detector, spatial overlap research, cross-timeframe raw-score sum or threshold optimization. Dependent grids and unadjusted multiple comparisons remain exploratory.
