# Delta Shape

Development: the unchanged 8,647 hourly events from 2022-01-05 17:00 through 2022-12-31 23:00 UTC. Replication: 8,760 events in 2023, labeled `previously inspected replication period`. No 2024, other timeframes, D predictive comparison, or live rules.

All 24 grids, three windows and five maps are retained. Development-defined deciles are always shown. Ventiles require all 20 bins to contain >=200 development states and >=5 weekly blocks. No 2023 refit. Observed median flow on continuous-x plots is descriptive; connected bin averages are not a fitted response function.

Near-zero is [-0.01,0.01]. Negative is below -0.01. Positive is above 0.01; moderate positive ends at the development positive-value 90th percentile and extreme positive is above it. These are predeclared reporting partitions, not entries. Phase 3.5 used a different near-zero definition; comparisons are qualitative, not identical thresholds.

| phase | feature | curves | increasing | decreasing |
|---|---|---|---|---|
| development | normalized_delta_difference | 360 | 0 | 0 |
| development | resistance_normalized_delta | 360 | 0 | 0 |
| development | support_normalized_delta | 360 | 0 | 0 |
| replication | normalized_delta_difference | 360 | 5 | 1 |
| replication | resistance_normalized_delta | 360 | 0 | 0 |
| replication | support_normalized_delta | 360 | 0 | 0 |

Finite-sample monotonicity and endpoint/middle curvature diagnostics are in delta-shapes.csv for every quarter. Nonmonotonicity alone does not prove an inverted-U effect or a useful threshold. Moderate/extreme contrasts are shown with cell counts, not only favorable cells.

All relationships are descriptive and dependent. No p-values, threshold selection, detector/window ranking, executable return or edge claim. Complete denominators include AMBIGUOUS and NEITHER; censored rows remain recorded. Conditional gross expectancy excludes unresolved/ambiguous/censored outcomes and costs.

Machine-readable tables: `data/phase3r2/`; diagnostic plots: `data/phase3r2/reports/diagnostics.html`.
