# Sign Confluence

| phase | direction | period | shape | grid_cells |
| --- | --- | --- | --- | --- |
| development | LONG | 1 | NONLINEAR | 12 |
| development | LONG | 2 | MONOTONIC_INCREASING | 2 |
| development | LONG | 2 | NONLINEAR | 10 |
| development | LONG | 3 | NONLINEAR | 12 |
| development | LONG | 4 | NONLINEAR | 12 |
| development | LONG | ALL | NONLINEAR | 12 |
| development | SHORT | 1 | MONOTONIC_DECREASING | 1 |
| development | SHORT | 1 | NONLINEAR | 11 |
| development | SHORT | 2 | NONLINEAR | 12 |
| development | SHORT | 3 | NONLINEAR | 12 |
| development | SHORT | 4 | NONLINEAR | 12 |
| development | SHORT | ALL | NONLINEAR | 12 |
| replication | LONG | 1 | NONLINEAR | 12 |
| replication | LONG | 2 | NONLINEAR | 12 |
| replication | LONG | 3 | NONLINEAR | 12 |
| replication | LONG | 4 | NONLINEAR | 12 |
| replication | LONG | ALL | MONOTONIC_DECREASING | 1 |
| replication | LONG | ALL | MONOTONIC_INCREASING | 2 |
| replication | LONG | ALL | NONLINEAR | 9 |
| replication | SHORT | 1 | NONLINEAR | 12 |
| replication | SHORT | 2 | NONLINEAR | 12 |
| replication | SHORT | 3 | SPARSE | 12 |
| replication | SHORT | 4 | MONOTONIC_INCREASING | 9 |
| replication | SHORT | 4 | NONLINEAR | 3 |
| replication | SHORT | ALL | NONLINEAR | 12 |

| phase | category | interpretation | min_complete | max_complete | min_blocks |
| --- | --- | --- | --- | --- | --- |
| development | imbalance/resistance/count/0 | SHORT | 6116 | 6148 | 47 |
| development | imbalance/resistance/count/1 | SHORT | 6753 | 6801 | 53 |
| development | imbalance/resistance/count/2 | SHORT | 6651 | 6651 | 52 |
| development | imbalance/resistance/count/3 | SHORT | 7513 | 7513 | 51 |
| development | imbalance/resistance/count/4 | SHORT | 7202 | 7202 | 40 |
| development | imbalance/support/count/0 | LONG | 8958 | 8958 | 43 |
| development | imbalance/support/count/1 | LONG | 8029 | 8029 | 51 |
| development | imbalance/support/count/2 | LONG | 6429 | 6429 | 52 |
| development | imbalance/support/count/3 | LONG | 6598 | 6646 | 53 |
| development | imbalance/support/count/4 | LONG | 4221 | 4253 | 38 |
| replication | imbalance/resistance/count/0 | SHORT | 8805 | 8805 | 42 |
| replication | imbalance/resistance/count/1 | SHORT | 7726 | 7726 | 53 |
| replication | imbalance/resistance/count/2 | SHORT | 7106 | 7123 | 53 |
| replication | imbalance/resistance/count/3 | SHORT | 5527 | 5590 | 49 |
| replication | imbalance/resistance/count/4 | SHORT | 5764 | 5764 | 30 |
| replication | imbalance/support/count/0 | LONG | 7065 | 7065 | 35 |
| replication | imbalance/support/count/1 | LONG | 5739 | 5818 | 49 |
| replication | imbalance/support/count/2 | LONG | 7257 | 7258 | 53 |
| replication | imbalance/support/count/3 | LONG | 7244 | 7244 | 52 |
| replication | imbalance/support/count/4 | LONG | 7623 | 7623 | 41 |

sign_baseline / TP_FIRST: 120 supported comparison/grid cells in both periods; 64 reverse pooled sign between development and replication; 4 retain one nonzero sign across all eight supported quarters. Development effect range [-0.0303222, 0.0365863], replication [-0.0352545, 0.0607353]. These are dependent descriptive cells, not a selected strategy or independent discoveries.

sign_baseline / AMBIGUOUS: 120 supported comparison/grid cells in both periods; 58 reverse pooled sign between development and replication; 0 retain one nonzero sign across all eight supported quarters. Development effect range [-0.0186805, 0.00840501], replication [-0.00467384, 0.00429519]. These are dependent descriptive cells, not a selected strategy or independent discoveries.

## Supported Directional Stability
| family | direction | metric | comparisons | supported_both | same_sign_dev_quarters_rep | same_sign_eight_quarters |
| --- | --- | --- | --- | --- | --- | --- |
| sign_baseline | LONG | AMBIGUOUS | 120 | 120 | 15 | 0 |
| sign_baseline | LONG | TP_FIRST | 120 | 120 | 16 | 4 |
| sign_baseline | SHORT | AMBIGUOUS | 120 | 120 | 15 | 0 |
| sign_baseline | SHORT | TP_FIRST | 120 | 120 | 8 | 4 |

Full exact denominators, all four labels, censoring, MFE/MAE and pooled shared-block intervals: `data/phase5/<period>/analysis/`. These counts span multiple dependent grids; they are not independent successful discoveries.

2023 is the **previously inspected replication period**, not a pristine test. No 2024 data, live rule, leverage, raw-score sum, threshold selection or winning timeframe selection. All comparisons are descriptive and dependent; bootstrap intervals are not adjusted for multiplicity.
