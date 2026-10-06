# Incremental Information

Development: the unchanged 8,647 hourly events from 2022-01-05 17:00 through 2022-12-31 23:00 UTC. Replication: 8,760 events in 2023, labeled `previously inspected replication period`. No 2024, other timeframes, D predictive comparison, or live rules.

Conditioned tables retain same-period unconditioned TP fraction, same valid/finite-flow cohort baseline, and same-cohort map-only stratum baseline. The incremental column is conditioned fraction minus map-only fraction. One-dimensional frozen strata are not exact full-map matching; residual confounding within buckets remains. Joint cluster concentration additionally crosses map direction, cluster quartile and candidates-per-cluster quartile. Sparse/absent cells are not filled or refit.

Same-sign moderate-minus-extreme comparisons and quarter consistency across every grid/window/map (not independent votes):

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

Moderate-positive minus negative flow in the SAME map stratum (separate from the tail question):

| condition | feature | observed_pairs | same_sign_pairs |
|---|---|---|---|
| A1 | normalized_delta_difference | 288 | 114 |
| A1 | resistance_normalized_delta | 288 | 185 |
| A1 | support_normalized_delta | 288 | 184 |
| A2 | normalized_delta_difference | 288 | 143 |
| A2 | resistance_normalized_delta | 288 | 190 |
| A2 | support_normalized_delta | 288 | 197 |
| clusters | normalized_delta_difference | 720 | 224 |
| clusters | resistance_normalized_delta | 720 | 457 |
| clusters | support_normalized_delta | 720 | 467 |
| imbalance | normalized_delta_difference | 1440 | 625 |
| imbalance | resistance_normalized_delta | 1440 | 856 |
| imbalance | support_normalized_delta | 1440 | 869 |

Each CI uses shared 1,000 seven-day block resamples for cell and map-only baseline, seed 3202; blocks are floor(timestamp_ms / 604800000), anchored at 1970-01-01 00:00 UTC, with partial boundary blocks retained. At least five represented blocks and 950 finite draws are required. Predeclared CI scope is A, all three windows, support/resistance normalized Delta and their difference within A1/imbalance/clusters, all outcome grids. B/C and other strata have chronological descriptive comparisons, not row-level inference. Cell-minus-baseline CIs are NOT CIs for the difference between two cells. Seven days does not eliminate every long-memory or regime-dependence concern.

## Quantity Is Not the Same Question as Directional Delta

High-minus-low JOINT quantity quartiles within the SAME map stratum show a substantial outcome-composition association. Compare both TP_FIRST and SL_FIRST with AMBIGUOUS, not just directional success. The table counts matched development/replication cells with higher ambiguity in the high-volume quartile, plus development four-quarter consistency. These are descriptive dependent comparisons, not independent significance tests or a fitted rule.

| condition | observed_pairs | higher_ambiguity_both | lower_tp_fraction_both | four_quarter_cells | higher_ambiguity_four_quarters |
|---|---|---|---|---|---|
| A1 | 288 | 228 | 83 | 288 | 130 |
| A2 | 288 | 232 | 76 | 288 | 134 |
| candidates_per_cluster | 720 | 622 | 172 | 0 | 0 |
| clusters | 720 | 636 | 171 | 0 | 0 |
| distance_difference | 1440 | 1090 | 374 | 1440 | 664 |
| imbalance | 1440 | 1118 | 406 | 1440 | 620 |
| recent_return | 1440 | 984 | 389 | 1440 | 568 |
| volatility | 1440 | 960 | 373 | 1320 | 288 |

In the fixed A/1h LONG .003/.003 8h display slice, marginal ambiguity rises from about 8.81% to 37.33% from lowest to highest quantity quartile in development, and from 2.31% to 23.92% in replication. LONG TP_FIRST falls from about 43.04% to 31.87%, and 44.77% to 39.51%, respectively. SHORT TP_FIRST also falls between these endpoints. The within-stratum table above, rather than this marginal example alone, addresses incremental composition information. This can reflect path volatility and barrier-order ambiguity, not direction forecasting. Causation is not established.

No pooled rate, same-sign percentage, or isolated CI is sufficient evidence for tradable predictive utility. Quantile conditioning controls only coarse geometry; causal attribution and exact-state matching are not established.

All relationships are descriptive and dependent. No p-values, threshold selection, detector/window ranking, executable return or edge claim. Complete denominators include AMBIGUOUS and NEITHER; censored rows remain recorded. Conditional gross expectancy excludes unresolved/ambiguous/censored outcomes and costs.

Machine-readable tables: `data/phase3r2/`; diagnostic plots: `data/phase3r2/reports/diagnostics.html`.
