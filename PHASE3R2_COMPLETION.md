# Phase 3R.2 Completion

Development: the unchanged 8,647 hourly events from 2022-01-05 17:00 through 2022-12-31 23:00 UTC. Replication: 8,760 events in 2023, labeled `previously inspected replication period`. No 2024, other timeframes, D predictive comparison, or live rules.

Completed five map configurations x three parallel flow windows across 17,407 unchanged events: 261,105 flow-state rows. Existing 417,768 distinct event/grid outcome rows are reused, not regenerated. Reports: eleven PHASE3R2 Markdown files, compact Parquet/CSV summaries and 152 SVG diagnostics.

Verification PASS: 260 tests, 0 failures, 0 errors, 0 skipped. All 87035 existing 1h map-flow rows matched (quantity rtol=1e-10, atol=1e-8); original price-map state columns are unchanged. 9730 prior artifacts remain byte-identical. All 30 flow/state tables passed time-window, quantity, shared-volume, geometry-preservation and outcome-identity audits. Existing Starlette/httpx deprecation warning remains unrelated to this research.

1. Beyond A1: Quantity carries descriptive outcome-composition information: 228/288 matched cells have higher ambiguity in the high-volume quartile in both periods. This is not directional edge. Stable additional directional Delta information is not established. For support normalized Delta moderate-minus-extreme, 60/288 observed cells keep one sign in all four development quarters; 205/288 comparable development/2023 cells retain the pooled sign (all grids/windows; dependent comparisons). This is not proof of zero Delta information.
2. Beyond imbalance: Quantity carries descriptive outcome-composition information: 1118/1440 matched cells have higher ambiguity in the high-volume quartile in both periods. This is not directional edge. Delta separation is not a consistently established extra directional signal. For support normalized Delta moderate-minus-extreme, 183/1440 observed cells keep one sign in all four development quarters; 937/1440 comparable development/2023 cells retain the pooled sign (all grids/windows; dependent comparisons). Coarse conditioning still leaves residual map/regime confounding.
3. Beyond clusters: Quantity carries descriptive outcome-composition information: 636/720 matched cells have higher ambiguity in the high-volume quartile in both periods. This is not directional edge. Delta evidence is limited by sparse cells and the large cluster-distribution shift. For support normalized Delta moderate-minus-extreme, no unchanged stratum is observed in all four development quarters, so four-quarter stability cannot be assessed; 362/720 comparable development/2023 cells retain the pooled sign (all grids/windows; dependent comparisons). Missing strata cannot be called replication.
4. Shape: 2154/2160 pooled decile curves are nonmonotonic. This is not a universal monotonic rule, nor proof of a population inverted-U/U shape or threshold.
5. Moderate versus extreme: not universally. Moderate positive exceeds extreme positive in 71694/111072 observed pooled conditional/marginal cells across both phases; these dependent cells are not independent votes or a significance test.
6. Support versus resistance: their observed curves can differ, but they are strongly coupled by overlapping intervals. Across phase/map/window tables their normalized-Delta Spearman correlation ranges 0.9819 to 0.9992. They cannot be treated as independent confirmations; difference-feature tables test residual contrast separately.
7. Quarter stability: Delta separation is not generally stable across all quarters; the condition-specific counts above show sign changes and sparse tails. Quantity/ambiguity has a separate four-quarter stability table in the incremental-value report. Missing common strata cannot establish stability. No favorable quarter is promoted.
8. Replication: the exact frozen analysis runs successfully. Quantity's composition association and Delta's partial shape agreement must be separated; neither is untouched validation or tradable edge. Implementation reproducibility alone is not predictive reproducibility.
9. Phase 3.5 survival: not established as the same robust effect. Residual contrasts do not resolve whether the legacy Q3 association was a geometry proxy; estimand, timestamps, weighting and Delta partitions differ. Component research is preserved rather than invalidated.
10. Later experiments: retain quantity as a descriptive path/ambiguity covariate and Delta as exploratory if later experiments are authorized, not as a confirmed directional signal or selected window. Current evidence does not justify freezing an entry rule; other timeframes are not started.

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

| phase | feature | curves | increasing | decreasing |
|---|---|---|---|---|
| development | normalized_delta_difference | 360 | 0 | 0 |
| development | resistance_normalized_delta | 360 | 0 | 0 |
| development | support_normalized_delta | 360 | 0 | 0 |
| replication | normalized_delta_difference | 360 | 5 | 1 |
| replication | resistance_normalized_delta | 360 | 0 | 0 |
| replication | support_normalized_delta | 360 | 0 | 0 |

See verification.json and test-results.xml for final audit/tests. New implementation: backend/app/fullmap_flow; tests: backend/tests/test_phase3r2.py. Prior Phase 3R.1 report/data/code hashes are preserved. No old artifact is rewritten. Stop before other timeframes, confluence, 2024, rule selection or live execution.

All relationships are descriptive and dependent. No p-values, threshold selection, detector/window ranking, executable return or edge claim. Complete denominators include AMBIGUOUS and NEITHER; censored rows remain recorded. Conditional gross expectancy excludes unresolved/ambiguous/censored outcomes and costs.

Machine-readable tables: `data/phase3r2/`; diagnostic plots: `data/phase3r2/reports/diagnostics.html`.
