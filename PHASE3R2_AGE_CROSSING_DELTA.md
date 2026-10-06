# Age, Crossing and Delta

Development: the unchanged 8,647 hourly events from 2022-01-05 17:00 through 2022-12-31 23:00 UTC. Replication: 8,760 events in 2023, labeled `previously inspected replication period`. No 2024, other timeframes, D predictive comparison, or live rules.

Nearby mean source age is split at 30/180/365 days. Existing recent/medium/old/very-old fractions and causal crossing/visit/contact features are preserved in states; very-old fraction also has a frozen quartile conditioner. Mean age is a map summary, not a claim that every nearby level has the same age.

Crossing, visit and time-since-contact strata use unchanged 3R.1 definitions and development cuts. These features are available for A only; no invented B/C crossing feature. Old levels are not invalidated or decayed.

| condition | feature | observed_pairs | same_sign_pairs | four_quarter_cells | consistent_four_quarters |
|---|---|---|---|---|---|
| age_band | normalized_delta_difference | 768 | 334 | 48 | 12 |
| age_band | resistance_normalized_delta | 1392 | 897 | 720 | 122 |
| age_band | support_normalized_delta | 1392 | 848 | 720 | 138 |
| mean_age | normalized_delta_difference | 768 | 352 | 0 | 0 |
| mean_age | resistance_normalized_delta | 1440 | 825 | 1440 | 204 |
| mean_age | support_normalized_delta | 1440 | 865 | 1440 | 248 |
| mean_hours_since_last_contact | normalized_delta_difference | 168 | 115 | 0 | 0 |
| mean_hours_since_last_contact | resistance_normalized_delta | 288 | 154 | 288 | 31 |
| mean_hours_since_last_contact | support_normalized_delta | 288 | 161 | 288 | 58 |
| mean_prior_crossings | normalized_delta_difference | 72 | 51 | 0 | 0 |
| mean_prior_crossings | resistance_normalized_delta | 288 | 157 | 288 | 30 |
| mean_prior_crossings | support_normalized_delta | 288 | 163 | 288 | 12 |
| mean_prior_visits | normalized_delta_difference | 72 | 49 | 0 | 0 |
| mean_prior_visits | resistance_normalized_delta | 288 | 161 | 216 | 18 |
| mean_prior_visits | support_normalized_delta | 288 | 171 | 216 | 18 |
| very_old_over_365d_fraction | normalized_delta_difference | 168 | 101 | 0 | 0 |
| very_old_over_365d_fraction | resistance_normalized_delta | 288 | 219 | 264 | 34 |
| very_old_over_365d_fraction | support_normalized_delta | 288 | 209 | 264 | 41 |

Residual separation by fresh/stale strata does not demonstrate that flow confirms an individual old level. Quarter and replication changes are retained in quarter-stability.parquet and replication-comparison.parquet.

All relationships are descriptive and dependent. No p-values, threshold selection, detector/window ranking, executable return or edge claim. Complete denominators include AMBIGUOUS and NEITHER; censored rows remain recorded. Conditional gross expectancy excludes unresolved/ambiguous/censored outcomes and costs.

Machine-readable tables: `data/phase3r2/`; diagnostic plots: `data/phase3r2/reports/diagnostics.html`.
