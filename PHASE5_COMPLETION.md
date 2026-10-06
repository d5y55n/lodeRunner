# Phase 5 Completion

| phase | timestamps | first | last | alignment_checks |
| --- | --- | --- | --- | --- |
| development | 34585 | 1641404700000 | 1672530300000 | 792 |
| replication | 35040 | 1672531200000 | 1704066300000 | 716 |

Tests: 313; failures 0; errors 0. Preservation audit: 56898 unique artifacts unchanged. 264 SVG panels cover all 24 outcome grids.

## Completion Questions

1. Greater agreement: observed 1/2/3/4 shapes are below. No monotonic improvement is assumed or inferred from pooled TP_FIRST alone.
| phase | direction | shape | grids |
| --- | --- | --- | --- |
| development | LONG | NONLINEAR | 12 |
| development | SHORT | NONLINEAR | 12 |
| replication | LONG | MONOTONIC_DECREASING | 1 |
| replication | LONG | MONOTONIC_INCREASING | 2 |
| replication | LONG | NONLINEAR | 9 |
| replication | SHORT | NONLINEAR | 12 |
2. Four versus two/three: consult same-period nested-baseline contrasts and exact samples. This phase does not establish that four is uniformly better; supported quarterly and replication behavior are required, not one grid.
nested_baseline / TP_FIRST: 1200 supported comparison/grid cells in both periods; 657 reverse pooled sign between development and replication; 20 retain one nonzero sign across all eight supported quarters. Development effect range [-0.0293429, 0.0397325], replication [-0.0333672, 0.0465354]. These are dependent descriptive cells, not a selected strategy or independent discoveries.
3. Spatial overlap beyond sign: both agreement-count-conditioned and exact-sign-pattern-conditioned contrasts are exported. Undefined or sparse contrasts cannot establish incremental information.
| family | direction | metric | comparisons | supported_both | same_sign_dev_quarters_rep | same_sign_eight_quarters |
| --- | --- | --- | --- | --- | --- | --- |
| spatial_exact | LONG | AMBIGUOUS | 1944 | 0 | 0 | 0 |
| spatial_exact | LONG | TP_FIRST | 1944 | 0 | 0 | 0 |
| spatial_exact | SHORT | AMBIGUOUS | 1944 | 0 | 0 | 0 |
| spatial_exact | SHORT | TP_FIRST | 1944 | 0 | 0 | 0 |
spatial_exact: no contrast/grid has the predeclared sample support in both periods. No incremental-information conclusion is available.
4. Sample support: `reports/combination-sample-counts.csv` lists exact minimum/maximum complete samples and occupied blocks for every inclusive, exclusive and spatial combination. Support was predeclared as >=200 complete timestamps and >=5 weekly blocks; no category was merged.
5. Adding 1d, 6. Adding 4h, 7. Adding 1h: the following summarizes all predeclared base-cohort additions, without ranking. Stable counts require the same nonzero sign in all eight supported quarters. Positive and negative effects both count as structure, not a benefit.
| addition | direction | grids | stable_all_eight | dev_effect_min | dev_effect_max | rep_effect_min | rep_effect_max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 15m | LONG | 12 | 0 | 0.025345 | 0.084743 | 0.0039498 | 0.062855 |
| 15m | SHORT | 12 | 0 | -0.038229 | -0.010395 | -0.03359 | 0.018513 |
| 1d | LONG | 36 | 0 | -0.0030694 | 0.062051 | -0.059136 | 0.0066126 |
| 1d | SHORT | 36 | 0 | -0.052569 | -0.0091561 | -0.0514 | 0.010931 |
| 1h | LONG | 24 | 0 | -0.022195 | 0.045532 | -0.039474 | 0.032674 |
| 1h | SHORT | 24 | 0 | -0.051762 | 0.0074815 | -0.019379 | 0.048006 |
| 4h | LONG | 36 | 1 | -0.051004 | 0.013386 | -0.095771 | 0.014376 |
| 4h | SHORT | 36 | 0 | -0.059736 | -0.0051813 | -0.032767 | 0.10106 |
8. Higher/lower conflicts: SSRR/RRSS and conflicts versus fully aligned states retain all outcome labels. No dominance rule is selected.
| family | direction | metric | comparisons | supported_both | same_sign_dev_quarters_rep | same_sign_eight_quarters |
| --- | --- | --- | --- | --- | --- | --- |
| conflict | LONG | AMBIGUOUS | 36 | 36 | 0 | 0 |
| conflict | LONG | TP_FIRST | 36 | 36 | 0 | 0 |
| conflict | SHORT | AMBIGUOUS | 36 | 36 | 0 | 0 |
| conflict | SHORT | TP_FIRST | 36 | 36 | 0 | 0 |
conflict / TP_FIRST: 72 supported comparison/grid cells in both periods; 29 reverse pooled sign between development and replication; 0 retain one nonzero sign across all eight supported quarters. Development effect range [-0.0801659, 0.0772818], replication [-0.122801, 0.138641]. These are dependent descriptive cells, not a selected strategy or independent discoveries.
9. Quantity and risk: conditional high-minus-low quantity contrasts retain ambiguity, neither, directional labels and excursions. Quantity remains outside direction.
| family | direction | metric | comparisons | supported_both | same_sign_dev_quarters_rep | same_sign_eight_quarters |
| --- | --- | --- | --- | --- | --- | --- |
| quantity | LONG | AMBIGUOUS | 120 | 120 | 4 | 0 |
| quantity | LONG | TP_FIRST | 120 | 120 | 1 | 0 |
| quantity | SHORT | AMBIGUOUS | 120 | 120 | 4 | 0 |
| quantity | SHORT | TP_FIRST | 120 | 120 | 0 | 0 |
quantity / AMBIGUOUS: 120 supported comparison/grid cells in both periods; 0 reverse pooled sign between development and replication; 0 retain one nonzero sign across all eight supported quarters. Development effect range [0.0118278, 0.137699], replication [0.00423985, 0.0726872]. These are dependent descriptive cells, not a selected strategy or independent discoveries.
10. Quarterly stability, 11. Frozen replication: complete comparisons and sign reversals are in chronological-stability.csv. Sparse quarters are not treated as stable evidence, and pooled consistency is not equivalent to all-quarter consistency.
12. ONE candidate strategy for untouched testing: **not established by this descriptive phase**. Unresolved requirements are selecting a single hypothesis without grid/multiple-comparison bias, demonstrating incremental directional separation rather than activity-driven path changes, handling state persistence and overlapping events, and specifying costs/execution separately. No candidate was promoted based on a strongest cell, no leverage was chosen and no 2024 data was accessed.

STOP. See `data/phase5/reports/diagnostics.html` for offline diagnostics and analysis CSV/Parquet for the full evidence.

2023 is the **previously inspected replication period**, not a pristine test. No 2024 data, live rule, leverage, raw-score sum, threshold selection or winning timeframe selection. All comparisons are descriptive and dependent; bootstrap intervals are not adjusted for multiplicity.
