# Alignment Audit

| phase | timeframe | checks | maximum_age_ms | truncation_pass |
| --- | --- | --- | --- | --- |
| development | 15m | 198 | 0 | True |
| development | 1d | 198 | 85500000 | True |
| development | 1h | 198 | 2700000 | True |
| development | 4h | 198 | 13500000 | True |
| replication | 15m | 179 | 0 | True |
| replication | 1d | 179 | 85500000 | True |
| replication | 1h | 179 | 2700000 | True |
| replication | 4h | 179 | 13500000 | True |

Samples are deterministic: evenly spaced timestamps plus before/at/after hourly, four-hourly and daily closes. Full sequence changes were checked to occur only on native closes. Source arrays were physically truncated at each sampled T. Existing 15m outcomes were reused with exact event/timestamp and complete-grid equality checks; no higher-timeframe labels were used.

2023 is the **previously inspected replication period**, not a pristine test. No 2024 data, live rule, leverage, raw-score sum, threshold selection or winning timeframe selection. All comparisons are descriptive and dependent; bootstrap intervals are not adjusted for multiplicity.
