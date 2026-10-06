# 2023: previously inspected replication period

Development: the unchanged 8,647 hourly events from 2022-01-05 17:00 through 2022-12-31 23:00 UTC. Replication: 8,760 events in 2023, labeled `previously inspected replication period`. No 2024, other timeframes, D predictive comparison, or live rules.

Development analysis and feature/bucket definitions were sealed before reading 2023 flow in this phase. Freeze ID: `aea5826effaf10a5b0b1d1d30de92e3869500a66904aa6b3bc7a041a14391107`. Frozen code, models and all development outputs are hashed and checked before replication. No percentile, near-zero boundary, positive-tail cut, map grouping or window is refit.

| condition | feature | observed_pairs | same_sign_pairs | four_quarter_cells | consistent_four_quarters |
|---|---|---|---|---|---|
| A1 | normalized_delta_difference | 216 | 120 | 0 | 0 |
| A1 | resistance_normalized_delta | 288 | 197 | 288 | 55 |
| A1 | support_normalized_delta | 288 | 205 | 288 | 60 |
| A2 | normalized_delta_difference | 192 | 81 | 0 | 0 |
| A2 | resistance_normalized_delta | 288 | 199 | 288 | 41 |
| A2 | support_normalized_delta | 288 | 197 | 288 | 44 |
| candidates_per_cluster | normalized_delta_difference | 312 | 119 | 0 | 0 |
| candidates_per_cluster | resistance_normalized_delta | 672 | 361 | 0 | 0 |
| candidates_per_cluster | support_normalized_delta | 672 | 373 | 0 | 0 |
| clusters | normalized_delta_difference | 384 | 147 | 0 | 0 |
| clusters | resistance_normalized_delta | 720 | 374 | 0 | 0 |
| clusters | support_normalized_delta | 720 | 362 | 0 | 0 |
| distance_difference | normalized_delta_difference | 672 | 262 | 72 | 51 |
| distance_difference | resistance_normalized_delta | 1440 | 937 | 1440 | 208 |
| distance_difference | support_normalized_delta | 1440 | 958 | 1440 | 207 |
| imbalance | normalized_delta_difference | 696 | 327 | 48 | 6 |
| imbalance | resistance_normalized_delta | 1440 | 920 | 1440 | 185 |
| imbalance | support_normalized_delta | 1440 | 937 | 1440 | 183 |

Replication comparison includes missing cells using an outer join and an explicit both_observed flag. Same-sign counts use only comparable cells; absence is not success. Different outcome compositions and base rates can alter apparent shapes. This is not untouched validation and cannot independently confirm an edge.

All relationships are descriptive and dependent. No p-values, threshold selection, detector/window ranking, executable return or edge claim. Complete denominators include AMBIGUOUS and NEITHER; censored rows remain recorded. Conditional gross expectancy excludes unresolved/ambiguous/censored outcomes and costs.

Machine-readable tables: `data/phase3r2/`; diagnostic plots: `data/phase3r2/reports/diagnostics.html`.
