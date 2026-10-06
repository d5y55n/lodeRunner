# Causal Volume Features

Development: the unchanged 8,647 hourly events from 2022-01-05 17:00 through 2022-12-31 23:00 UTC. Replication: 8,760 events in 2023, labeled `previously inspected replication period`. No 2024, other timeframes, D predictive comparison, or live rules.

Current-T nearby candidates use unchanged .004 full-band intervals, including candidates contributing in the outer half band. Within each side, closed intervals are merged before querying exact observed-price hourly aggregate-trade profiles. Joint union merges both sides. Windows are [T-1h,T), [T-4h,T), [T-8h,T); maps stay fixed at T. This is not a history of earlier maps. No trades at or after T.

Formulas: quantity=buy+sell; raw Delta=buy-sell; normalized Delta=(buy-sell)/quantity only for quantity>0; normalized difference=support ND-resistance ND; raw difference=support Delta-resistance Delta; buy-share difference=normalized difference/2. Side volume share=Qs/(Qs+Qr), a relative side-exposure statistic, NOT deduplicated total volume. Shared=Qs+Qr-Qjoint. Qjoint, not Qs+Qr, is combined actual volume. No opaque score.

Unavailable windows invalidate all flow values; zero covered quantity remains zero but normalized Delta is undefined, not neutral. Any existing quarantine intersecting any hour invalidates the whole window. Missing profiles are not zero-filled, even with empty intervals. Source checksums match forensic coverage. No candle volume substitution.

| phase | config | window | states | coverage_valid | support_zero | resistance_zero | shared_over_joint_median | support_resistance_delta_spearman |
|---|---|---|---|---|---|---|---|---|
| development | ('A', {}) | 1 | 8647 | 8646 | 14 | 52 | 1 | 0.99411 |
| development | ('A', {}) | 4 | 8647 | 8643 | 14 | 51 | 0.99795 | 0.99318 |
| development | ('A', {}) | 8 | 8647 | 8639 | 14 | 51 | 0.99148 | 0.99167 |
| development | ('B', {'width': 1}) | 1 | 8647 | 8646 | 35 | 88 | 1 | 0.99306 |
| development | ('B', {'width': 1}) | 4 | 8647 | 8643 | 34 | 85 | 0.99769 | 0.99106 |
| development | ('B', {'width': 1}) | 8 | 8647 | 8639 | 34 | 85 | 0.99003 | 0.98996 |
| development | ('B', {'width': 2}) | 1 | 8647 | 8646 | 150 | 129 | 1 | 0.98376 |
| development | ('B', {'width': 2}) | 4 | 8647 | 8643 | 145 | 128 | 0.99306 | 0.98215 |
| development | ('B', {'width': 2}) | 8 | 8647 | 8639 | 144 | 128 | 0.97904 | 0.98195 |
| development | ('C', {'reversal_fraction': 0.003}) | 1 | 8647 | 8646 | 1 | 46 | 1 | 0.99693 |
| development | ('C', {'reversal_fraction': 0.003}) | 4 | 8647 | 8643 | 1 | 45 | 0.99933 | 0.99599 |
| development | ('C', {'reversal_fraction': 0.003}) | 8 | 8647 | 8639 | 1 | 45 | 0.99598 | 0.9958 |
| development | ('C', {'reversal_fraction': 0.005}) | 1 | 8647 | 8646 | 1 | 51 | 1 | 0.99702 |
| development | ('C', {'reversal_fraction': 0.005}) | 4 | 8647 | 8643 | 1 | 49 | 0.99917 | 0.99573 |
| development | ('C', {'reversal_fraction': 0.005}) | 8 | 8647 | 8639 | 1 | 49 | 0.99518 | 0.99521 |
| replication | ('A', {}) | 1 | 8760 | 8758 | 9 | 0 | 1 | 0.9986 |
| replication | ('A', {}) | 4 | 8760 | 8752 | 8 | 0 | 1 | 0.99763 |
| replication | ('A', {}) | 8 | 8760 | 8744 | 7 | 0 | 0.99944 | 0.99735 |
| replication | ('B', {'width': 1}) | 1 | 8760 | 8758 | 6 | 25 | 1 | 0.99775 |
| replication | ('B', {'width': 1}) | 4 | 8760 | 8752 | 6 | 23 | 1 | 0.99664 |
| replication | ('B', {'width': 1}) | 8 | 8760 | 8744 | 6 | 23 | 0.99931 | 0.99673 |
| replication | ('B', {'width': 2}) | 1 | 8760 | 8758 | 19 | 37 | 1 | 0.99416 |
| replication | ('B', {'width': 2}) | 4 | 8760 | 8752 | 17 | 34 | 1 | 0.99105 |
| replication | ('B', {'width': 2}) | 8 | 8760 | 8744 | 17 | 34 | 0.99746 | 0.99091 |

First 24/30 rows; full table exported.

Shared-over-joint is shared quantity divided by deduplicated joint quantity when joint quantity is positive. In development A/1h its median is 1.0 and side-Delta rank correlation is about 0.9941. Support Delta's rank correlation with A1 is only about -0.0362 in that same slice: lack of simple score correlation does not by itself demonstrate useful incremental prediction.

Per-feature overall/quarter distributions, missing/zero frequencies, and Spearman correlations with A1/A2/imbalance/clusters/distances/volatility/recent return are in each analysis folder. Support/resistance side coverage is shared at window level; covered empty side unions have quantity zero. Strong side correlations can arise from overlapping intervals, not independent confirmation.

All relationships are descriptive and dependent. No p-values, threshold selection, detector/window ranking, executable return or edge claim. Complete denominators include AMBIGUOUS and NEITHER; censored rows remain recorded. Conditional gross expectancy excludes unresolved/ambiguous/censored outcomes and costs.

Machine-readable tables: `data/phase3r2/`; diagnostic plots: `data/phase3r2/reports/diagnostics.html`.
