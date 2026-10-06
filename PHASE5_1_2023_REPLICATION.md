# Frozen 2023 Replication

Validation disclosure: original research definitions/code and development results remain frozen. A separately sealed validation-only runner was added after a shared-native-close price discrepancy stopped classification, BEFORE replication outcomes. It replayed every 2022 state exactly, then retained the one discrepant 1h row using common 15m P and scalar checks at both stored prices. No thresholds, outcomes, memberships or source prices changed. See `PHASE5_1_CURRENT_PRICE_STATE_AUDIT.md` and `data/phase5_1/validation-amendment`. The original freeze statement below does not imply this later validation runner was in that original code manifest.

Previously inspected replication period. Complete definitions, code, distributions, hierarchy and comparison methods were frozen after development and tests, before any 2023 source read. No rebinning, threshold fitting or category merging.
Freeze: `db6bd4971bab364cc8469c3143f4ca8d55aee7c771a5d279068ce787b3d8af85`.

| phase | pattern | N |
| --- | --- | --- |
| development | RRRR | 8306 |
| development | SSSS | 4712 |
| replication | RRRR | 6199 |
| replication | SSSS | 8381 |

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

Phase 5.1 uses common P; it must not be substituted with Phase 5 carried-price patterns or spatial counts.

2023 is the **previously inspected replication period**, not an untouched final test. No 2024, live trading, leverage, new detector, spatial overlap research, cross-timeframe raw-score sum or threshold optimization. Dependent grids and unadjusted multiple comparisons remain exploratory.
