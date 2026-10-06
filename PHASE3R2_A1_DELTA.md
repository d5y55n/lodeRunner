# A1 and Delta

Development: the unchanged 8,647 hourly events from 2022-01-05 17:00 through 2022-12-31 23:00 UTC. Replication: 8,760 events in 2023, labeled `previously inspected replication period`. No 2024, other timeframes, D predictive comparison, or live rules.

Original A1 and A2 are unchanged. Frozen A1/A2 bins come from Phase 3R.1, not current flow availability. Support-side, resistance-side and difference features are separate. Support-heavy/resistance-heavy maps also have map_direction cross-tabs for both LONG and SHORT.

Illustrative predeclared LONG TP=SL=.003, 8h, 1h support Delta (all other grids exported):

| phase | condition | map_bucket | complete_moderate | complete_extreme | moderate_minus_extreme |
|---|---|---|---|---|---|
| development | ALL | 0 | 3485 | 388 | 0.0013401 |
| development | A1 | 0 | 825 | 97 | 0.014908 |
| development | A1 | 1 | 893 | 111 | -0.022275 |
| development | A1 | 2 | 957 | 93 | -0.05019 |
| development | A1 | 3 | 810 | 87 | 0.07284 |
| development | imbalance | 0 | 764 | 83 | 0.010787 |
| development | imbalance | 1 | 1012 | 135 | 0.014998 |
| development | imbalance | 2 | 850 | 76 | -0.11347 |
| development | imbalance | 3 | 859 | 94 | 0.069353 |
| development | clusters | 0 | 645 | 88 | 0.025018 |
| development | clusters | 1 | 987 | 85 | 0.017653 |
| development | clusters | 2 | 447 | 58 | -0.058474 |
| development | clusters | 3 | 1406 | 157 | -0.00023104 |
| replication | ALL | 0 | 3257 | 565 | 0.025906 |
| replication | A1 | 0 | 834 | 149 | 0.082661 |
| replication | A1 | 1 | 560 | 98 | -0.043367 |
| replication | A1 | 2 | 738 | 106 | -0.00046019 |
| replication | A1 | 3 | 1125 | 212 | 0.034067 |
| replication | imbalance | 0 | 772 | 135 | 0.062637 |
| replication | imbalance | 1 | 638 | 107 | 0.0089649 |
| replication | imbalance | 2 | 622 | 106 | -0.022174 |
| replication | imbalance | 3 | 1225 | 217 | 0.034997 |
| replication | clusters | 0 | 2801 | 516 | 0.026236 |
| replication | clusters | 1 | 456 | 49 | 0.0071608 |

In this fixed display grid, 4/4 observed A1 strata retain the pooled moderate-minus-extreme sign in 2023, but only 0/4 keep one sign across all four development quarters. Partial pooled replication and chronological stability are different questions.

Compare the within-A1 increment with its map-only baseline, not only unconditioned flow. Marginal correlation with A1 and within-bucket separation can coexist. Sparse sign-flip or extreme-flow cells cannot establish that Delta changes the original score's meaning. No cutoff or combined score was constructed.

All relationships are descriptive and dependent. No p-values, threshold selection, detector/window ranking, executable return or edge claim. Complete denominators include AMBIGUOUS and NEITHER; censored rows remain recorded. Conditional gross expectancy excludes unresolved/ambiguous/censored outcomes and costs.

Machine-readable tables: `data/phase3r2/`; diagnostic plots: `data/phase3r2/reports/diagnostics.html`.
