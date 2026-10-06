# Phase 5.1 Completion

## Direct Answers

All counts below use the predeclared 12 TP/SL/horizon grids per direction, not selected cells. These dependent grids are not independent discoveries. Detailed denominators, censored counts, blocks, six outcome metrics and intervals follow below and in the exports.

1. Current-price SSSS: **4,712 / 34,585** eligible 2022 timestamps and **8,381 / 35,040** in previously inspected 2023.
2. Current-price RRRR: **8,306 / 34,585** in 2022 and **6,199 / 35,040** in 2023. Pattern counts include censored horizons; outcome denominators exclude them.
3. SSSS LONG: in pooled 2022, TP_FIRST rises and SL_FIRST falls in all 12 grids against each of all timestamps, 15m S, 15m+1h S and 15m+1h+4h S. In 2023, TP_FIRST rises in respectively **10/12, 3/12, 3/12, 9/12**, while SL_FIRST falls in **12/12, 10/12, 10/12, 12/12**. Consistent incremental improvement is **not reproduced**. All 2023 primary TP_FIRST/SL_FIRST difference intervals include zero.
4. RRRR SHORT: 2022 TP_FIRST is lower in all 12 grids against every baseline. In 2023 it rises in **12/12, 11/12, 8/12, 0/12**, respectively; SL_FIRST is higher in all 12 grids against the 2TF baseline. No consistent improvement is established. All 2023 primary TP_FIRST/SL_FIRST difference intervals include zero.
5. Exact 1TF -> 2TF -> 3TF -> 4TF TP_FIRST hierarchy: LONG 2022 has 11 increasing and 1 nonlinear grid; LONG 2023 has 11 nonlinear and 1 decreasing grid. SHORT 2022 has 9 nonlinear and 3 decreasing grids; SHORT 2023 has 12 nonlinear grids. **Monotonic improvement is not stable.** Other outcome hierarchy shapes are exported separately.
6. Stronger native imbalance within SSSS does **not consistently improve LONG**. Native high-minus-low TP_FIRST is positive in 2/48 supported comparison/grid cells in 2022 and 20/48 in 2023. Continuous and Q4-configuration results also vary by period; no cutoff is selected.
7. Within RRRR, stronger native imbalance is **mixed**, not a stable SHORT improvement: corresponding positive native high-minus-low cells are 30/48 in 2022 and 24/48 in 2023.
8. Weakest-timeframe strength has descriptive association but **not a reproducible beneficial effect**. SSSS minimum-strength TP_FIRST slopes per +0.1 imbalance are negative across all 12 grids in 2022 (-0.039936 to -0.007619; 8 intervals below zero), but mixed in 2023 (-0.026553 to +0.022876; all intervals include zero). RRRR slopes are mixed in both periods, with no intervals excluding zero.
9. Current-price distance gives **period-dependent structure**, not a robust rule. Within SSSS, the far-minus-near maximum-distance quartile TP_FIRST contrast is negative in all 12 development grids and positive in all 12 replication grids. Stricter all-four-close versus any-not-close comparisons fail the predeclared sample-support rule; their absence is not evidence of no effect. No threshold is relaxed.
10. SSSS/RRRR relationships are **not uniformly stable across 2022 quarters**. For example, only 1/12 SSSS-versus-all TP_FIRST grids has the same nonzero sign in all four development quarters and pooled replication. Full quarterly signs/support flags are retained; pooled improvement is not quarterly stability.
11. Frozen 2023 replication does **not reproduce the complete primary directional/hierarchy hypothesis**. SSSS's pooled SL_FIRST reduction partly persists, but incremental TP_FIRST and hierarchy behavior do not. Strength/distance effects are also inconsistent. This is previously inspected replication, not an untouched test.
12. Quantity's most consistent pooled relationship is **increased ambiguity/path risk, not stable directional improvement**. High-minus-low AMBIGUOUS is positive with intervals above zero in all 12 grids for each pattern in each year. TP_FIRST signs vary across periods. This is association, not causality: no quantity contrast passes the all-eight-supported-quarter same-sign criterion, and quantity can also affect directional composition. It remains outside S/R and strength definitions.
13. **No single candidate is justified for untouched 2024 testing from this phase.** The main LONG hierarchy fails replication, SHORT improvement is inconsistent, and strength/distance refinements are unstable or sparse. Choosing a favorable cell now would be post-hoc selection. No candidate, live rule or 2024 evaluation is promoted.

## Validation-Only Amendment Disclosure

The original mathematical definition, research code freeze and frozen development artifacts remain unchanged. The first replication state run stopped BEFORE replication outcomes because an assertion assumed identical prices at every shared native close. A separately sealed validation runner replaced only that assumption, before replication outcomes were read. This is an execution-validation amendment, not a claim that every execution file was in the original freeze.

At 2023-11-10 16:00 UTC, stored 1h close=37092.6 while current closed 15m P=37118.4. The one affected row was retained, original prices were not replaced, and independent original scalar scoring passes at BOTH prices. Common 15m P remains authoritative for all four evaluations. The 1h state is R at both prices, with different counts/A1/A2. No timestamp-specific exception, row exclusion, refit or outcome-conditioned change was used.

Before replication, the runner reproduced all **34,585 rows x 137 columns** of 2022 states exactly, including dtypes. Independent comparison of reconstructed carried-price patterns against only Phase 5 event ID/timestamp/pattern fields passed for every 2022 and 2023 row; no spatial feature was used.

Evidence: `data/phase5_1/validation-amendment/{definition.json,development-equivalence.json,frozen.json}`, `replication/classification-audit.json`, and `backend/scripts/phase5_1_validation_amendment.py` (SHA256 `0b2eefe04f3bfa80dbd24e1bfdd871bc2851d29b798a8d99738c353cd01954fa`). Original freeze ID: `db6bd4971bab364cc8469c3143f4ca8d55aee7c771a5d279068ce787b3d8af85`.

## Detailed Evidence

Tests: 331, failures 0, errors 0. Preserved artifacts checked: 58382, changed: 0. Native maps and outcomes were reused; no detector rebuild.

## Exact Completion Questions

1. CURRENT-PRICE SSSS counts; 2. CURRENT-PRICE RRRR counts:
| phase | pattern | N |
| --- | --- | --- |
| development | RRRR | 8306 |
| development | SSSS | 4712 |
| replication | RRRR | 6199 |
| replication | SSSS | 8381 |

3. Does SSSS improve LONG versus all / 15m / 15m+1h / 15m+1h+4h?
| phase | comparison | metric | grids | supported | minimum_effect | maximum_effect | positive | negative | CI_above_zero | CI_below_zero | minimum_A_complete | minimum_B_complete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | SSSS/vs_baseline_0 | SL_FIRST | 12 | 12 | -0.039553 | -0.014677 | 0 | 12 | 0 | 7 | 4670 | 34490 |
| development | SSSS/vs_baseline_0 | TP_FIRST | 12 | 12 | 0.013249 | 0.037602 | 12 | 0 | 2 | 0 | 4670 | 34490 |
| development | SSSS/vs_baseline_1 | SL_FIRST | 12 | 12 | -0.039064 | -0.025436 | 0 | 12 | 0 | 11 | 4670 | 15499 |
| development | SSSS/vs_baseline_1 | TP_FIRST | 12 | 12 | 0.0070551 | 0.038287 | 12 | 0 | 3 | 0 | 4670 | 15499 |
| development | SSSS/vs_baseline_2 | SL_FIRST | 12 | 12 | -0.033157 | -0.021702 | 0 | 12 | 0 | 8 | 4670 | 10789 |
| development | SSSS/vs_baseline_2 | TP_FIRST | 12 | 12 | 0.0039665 | 0.030658 | 12 | 0 | 2 | 0 | 4670 | 10789 |
| development | SSSS/vs_baseline_3 | SL_FIRST | 12 | 12 | -0.029426 | -0.019173 | 0 | 12 | 0 | 11 | 4670 | 8516 |
| development | SSSS/vs_baseline_3 | TP_FIRST | 12 | 12 | 0.0031908 | 0.026159 | 12 | 0 | 2 | 0 | 4670 | 8516 |
| replication | SSSS/vs_baseline_0 | SL_FIRST | 12 | 12 | -0.019521 | -0.0042415 | 0 | 12 | 0 | 0 | 8381 | 34945 |
| replication | SSSS/vs_baseline_0 | TP_FIRST | 12 | 12 | -0.0050078 | 0.024301 | 10 | 2 | 0 | 0 | 8381 | 34945 |
| replication | SSSS/vs_baseline_1 | SL_FIRST | 12 | 12 | -0.019357 | 0.0046703 | 2 | 10 | 0 | 0 | 8381 | 15943 |
| replication | SSSS/vs_baseline_1 | TP_FIRST | 12 | 12 | -0.015849 | 0.0051294 | 3 | 9 | 0 | 0 | 8381 | 15943 |
| replication | SSSS/vs_baseline_2 | SL_FIRST | 12 | 12 | -0.017866 | 0.0026473 | 2 | 10 | 0 | 0 | 8381 | 12870 |
| replication | SSSS/vs_baseline_2 | TP_FIRST | 12 | 12 | -0.017552 | 0.0045448 | 3 | 9 | 0 | 0 | 8381 | 12870 |
| replication | SSSS/vs_baseline_3 | SL_FIRST | 12 | 12 | -0.011792 | -0.0037705 | 0 | 12 | 0 | 0 | 8381 | 10060 |
| replication | SSSS/vs_baseline_3 | TP_FIRST | 12 | 12 | -0.0052037 | 0.0082431 | 9 | 3 | 0 | 0 | 8381 | 10060 |
Improvement is not declared from a positive TP_FIRST cell alone; SL_FIRST, ambiguity, excursions, intervals and quarterly replication are retained in the dedicated report.

4. Does RRRR improve SHORT versus all / 15m / 15m+1h / 15m+1h+4h?
| phase | comparison | metric | grids | supported | minimum_effect | maximum_effect | positive | negative | CI_above_zero | CI_below_zero | minimum_A_complete | minimum_B_complete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | RRRR/vs_baseline_0 | SL_FIRST | 12 | 12 | -0.0087148 | 0.014203 | 8 | 4 | 0 | 0 | 8306 | 34490 |
| development | RRRR/vs_baseline_0 | TP_FIRST | 12 | 12 | -0.01818 | -0.0011733 | 0 | 12 | 0 | 0 | 8306 | 34490 |
| development | RRRR/vs_baseline_1 | SL_FIRST | 12 | 12 | -0.0039416 | 0.013259 | 10 | 2 | 0 | 0 | 8306 | 18021 |
| development | RRRR/vs_baseline_1 | TP_FIRST | 12 | 12 | -0.0098737 | -0.0043526 | 0 | 12 | 0 | 0 | 8306 | 18021 |
| development | RRRR/vs_baseline_2 | SL_FIRST | 12 | 12 | -0.0062702 | 0.012615 | 9 | 3 | 0 | 0 | 8306 | 14011 |
| development | RRRR/vs_baseline_2 | TP_FIRST | 12 | 12 | -0.010511 | -0.0038808 | 0 | 12 | 0 | 0 | 8306 | 14011 |
| development | RRRR/vs_baseline_3 | SL_FIRST | 12 | 12 | -0.0012587 | 0.0076956 | 10 | 2 | 0 | 0 | 8306 | 11117 |
| development | RRRR/vs_baseline_3 | TP_FIRST | 12 | 12 | -0.010311 | -0.0050726 | 0 | 12 | 0 | 0 | 8306 | 11117 |
| replication | RRRR/vs_baseline_0 | SL_FIRST | 12 | 12 | -0.019359 | 0.0088146 | 4 | 8 | 0 | 0 | 6139 | 34945 |
| replication | RRRR/vs_baseline_0 | TP_FIRST | 12 | 12 | 0.010587 | 0.027316 | 12 | 0 | 0 | 0 | 6139 | 34945 |
| replication | RRRR/vs_baseline_1 | SL_FIRST | 12 | 12 | -0.0053091 | 0.019666 | 10 | 2 | 0 | 0 | 6139 | 18345 |
| replication | RRRR/vs_baseline_1 | TP_FIRST | 12 | 12 | -0.0022301 | 0.031006 | 11 | 1 | 0 | 0 | 6139 | 18345 |
| replication | RRRR/vs_baseline_2 | SL_FIRST | 12 | 12 | 0.00051019 | 0.020751 | 12 | 0 | 0 | 0 | 6139 | 12999 |
| replication | RRRR/vs_baseline_2 | TP_FIRST | 12 | 12 | -0.013484 | 0.016398 | 8 | 4 | 0 | 0 | 6139 | 12999 |
| replication | RRRR/vs_baseline_3 | SL_FIRST | 12 | 12 | -0.0084312 | 0.012316 | 8 | 4 | 0 | 0 | 6139 | 9178 |
| replication | RRRR/vs_baseline_3 | TP_FIRST | 12 | 12 | -0.018846 | -0.0021936 | 0 | 12 | 0 | 0 | 6139 | 9178 |
Improvement is not declared from a positive TP_FIRST cell alone; SL_FIRST, ambiguity, excursions, intervals and quarterly replication are retained in the dedicated report.

5. Is the exact hierarchy monotonic?
| phase | direction | shape | grids |
| --- | --- | --- | --- |
| development | LONG | MONOTONIC_INCREASING | 11 |
| development | LONG | NONLINEAR | 1 |
| development | SHORT | MONOTONIC_DECREASING | 3 |
| development | SHORT | NONLINEAR | 9 |
| replication | LONG | MONOTONIC_DECREASING | 1 |
| replication | LONG | NONLINEAR | 11 |
| replication | SHORT | NONLINEAR | 12 |

6. Stronger per-timeframe imbalance within SSSS for LONG:
development: 48 supported pooled comparison/grid cells: 2 positive, 46 negative TP_FIRST differences. Range [-0.113329, 0.0252909]. 0 intervals entirely above zero; 9 entirely below. These dependent cells are not separate discoveries or selected rules.
replication: 48 supported pooled comparison/grid cells: 20 positive, 28 negative TP_FIRST differences. Range [-0.0608911, 0.0686165]. 0 intervals entirely above zero; 0 entirely below. These dependent cells are not separate discoveries or selected rules.

7. Stronger per-timeframe imbalance within RRRR for SHORT:
development: 48 supported pooled comparison/grid cells: 30 positive, 18 negative TP_FIRST differences. Range [-0.07023, 0.0602539]. 0 intervals entirely above zero; 1 entirely below. These dependent cells are not separate discoveries or selected rules.
replication: 48 supported pooled comparison/grid cells: 24 positive, 24 negative TP_FIRST differences. Range [-0.111395, 0.192693]. 3 intervals entirely above zero; 0 entirely below. These dependent cells are not separate discoveries or selected rules.

8. Does weakest-timeframe strength matter? Continuous minimum-strength slopes per +0.1 (all 12 grids, not a selected threshold):
| phase | pattern | feature | metric | min_slope | max_slope | supported | CI_positive | CI_negative |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | RRRR | strength_minimum | SL_FIRST | -0.0049029 | 0.019888 | 12 | 0 | 0 |
| development | RRRR | strength_minimum | TP_FIRST | -0.0080232 | 0.018405 | 12 | 0 | 0 |
| development | SSSS | strength_minimum | SL_FIRST | 0.0010844 | 0.032879 | 12 | 6 | 0 |
| development | SSSS | strength_minimum | TP_FIRST | -0.039936 | -0.0076188 | 12 | 0 | 8 |
| replication | RRRR | strength_minimum | SL_FIRST | 0.0018364 | 0.023168 | 12 | 0 | 0 |
| replication | RRRR | strength_minimum | TP_FIRST | -0.0096681 | 0.02131 | 12 | 0 | 0 |
| replication | SSSS | strength_minimum | SL_FIRST | -0.00097723 | 0.038445 | 12 | 1 | 0 |
| replication | SSSS | strength_minimum | TP_FIRST | -0.026553 | 0.022876 | 12 | 0 | 0 |

9. Current-price nearest distances: 
development: 24 supported pooled comparison/grid cells: 10 positive, 13 negative TP_FIRST differences. Range [-0.06777, 0.0423688]. 0 intervals entirely above zero; 0 entirely below. These dependent cells are not separate discoveries or selected rules.

replication: 24 supported pooled comparison/grid cells: 22 positive, 2 negative TP_FIRST differences. Range [-0.0145319, 0.166826]. 6 intervals entirely above zero; 0 entirely below. These dependent cells are not separate discoveries or selected rules.
Sparse near/far comparisons are not evidence of no effect; no proximity width was relaxed.

10. Stable across 2022 quarters; 11. Reproduced in frozen 2023:
| family | direction | metric | grids | supported_both | all_2022_quarters_and_rep | all_eight_quarters |
| --- | --- | --- | --- | --- | --- | --- |
| all_four_baselines | LONG | AMBIGUOUS | 48 | 48 | 1 | 0 |
| all_four_baselines | LONG | SL_FIRST | 48 | 48 | 33 | 1 |
| all_four_baselines | LONG | TP_FIRST | 48 | 48 | 5 | 1 |
| all_four_baselines | SHORT | AMBIGUOUS | 48 | 48 | 0 | 0 |
| all_four_baselines | SHORT | SL_FIRST | 48 | 48 | 6 | 0 |
| all_four_baselines | SHORT | TP_FIRST | 48 | 48 | 2 | 1 |
| hierarchy_increment | LONG | AMBIGUOUS | 36 | 36 | 2 | 1 |
| hierarchy_increment | LONG | SL_FIRST | 36 | 36 | 11 | 0 |
| hierarchy_increment | LONG | TP_FIRST | 36 | 36 | 3 | 1 |
| hierarchy_increment | SHORT | AMBIGUOUS | 36 | 36 | 0 | 0 |
| hierarchy_increment | SHORT | SL_FIRST | 36 | 36 | 4 | 0 |
| hierarchy_increment | SHORT | TP_FIRST | 36 | 36 | 2 | 1 |
| native_strength | LONG | AMBIGUOUS | 48 | 48 | 0 | 0 |
| native_strength | LONG | SL_FIRST | 48 | 48 | 0 | 0 |
| native_strength | LONG | TP_FIRST | 48 | 48 | 0 | 0 |
| native_strength | SHORT | AMBIGUOUS | 48 | 48 | 0 | 0 |
| native_strength | SHORT | SL_FIRST | 48 | 48 | 1 | 0 |
| native_strength | SHORT | TP_FIRST | 48 | 48 | 0 | 0 |
| summary_strength | LONG | AMBIGUOUS | 36 | 36 | 0 | 0 |
| summary_strength | LONG | SL_FIRST | 36 | 36 | 0 | 0 |
| summary_strength | LONG | TP_FIRST | 36 | 36 | 0 | 0 |
| summary_strength | SHORT | AMBIGUOUS | 36 | 36 | 0 | 0 |
| summary_strength | SHORT | SL_FIRST | 36 | 36 | 0 | 0 |
| summary_strength | SHORT | TP_FIRST | 36 | 36 | 0 | 0 |

12. Quantity: ambiguity and directional contrasts are reported separately, not treated as direction.

development: 24 supported pooled comparison/grid cells: 24 positive, 0 negative AMBIGUOUS differences. Range [0.0195633, 0.127061]. 24 intervals entirely above zero; 0 entirely below. These dependent cells are not separate discoveries or selected rules.

replication: 24 supported pooled comparison/grid cells: 24 positive, 0 negative AMBIGUOUS differences. Range [0.0102997, 0.0768982]. 24 intervals entirely above zero; 0 entirely below. These dependent cells are not separate discoveries or selected rules.

development: 24 supported pooled comparison/grid cells: 12 positive, 12 negative TP_FIRST differences. Range [-0.105654, 0.10892]. 2 intervals entirely above zero; 4 entirely below. These dependent cells are not separate discoveries or selected rules.

replication: 24 supported pooled comparison/grid cells: 19 positive, 5 negative TP_FIRST differences. Range [-0.0428966, 0.198294]. 9 intervals entirely above zero; 0 entirely below. These dependent cells are not separate discoveries or selected rules.

13. Single candidate for untouched 2024: **not promoted from this descriptive phase**. The tables above must demonstrate a coherent primary hierarchy and current-price directional composition, not a selected positive grid or strength cutoff. Quarterly/replication reversals, sparse strength configurations, overlapping event paths, unadjusted multiple comparisons, and unspecified costs/execution remain unresolved. No arbitrary best cell was used to invent a candidate.

## Scope Correction

Phase 5 carried some higher-timeframe descriptors at their native close price. Phase 5.1 re-evaluates the frozen candidate membership at the same current 15m P. Existing Phase 5 artifacts are unchanged. Historical-axis spatial intersections are a different question and are NOT cited as evidence against SSSS/RRRR.

All compact evidence: data/phase5_1/<period>/analysis and data/phase5_1/reports. STOP; no next phase run.

2023 is the **previously inspected replication period**, not an untouched final test. No 2024, live trading, leverage, new detector, spatial overlap research, cross-timeframe raw-score sum or threshold optimization. Dependent grids and unadjusted multiple comparisons remain exploratory.
