# Phase 3.5 Reconciliation

Development: the unchanged 8,647 hourly events from 2022-01-05 17:00 through 2022-12-31 23:00 UTC. Replication: 8,760 events in 2023, labeled `previously inspected replication period`. No 2024, other timeframes, D predictive comparison, or live rules.

Phase 3.5's documented display case had raw-Delta Q3 TP-first about 34.7742% versus 34.3103% A alone in development, and 44.2402% versus 43.7763% in previously inspected 2023. Its raw Q3 boundaries were about -5.97 to 214.415 BTC, not a universally positive normalized-Delta interval. See unchanged docs/research/PHASE35_REVIEW_KO.md.

The old study used single-zone interactions, 2021-2022 development and event-balanced zone measurements; this study uses one full-map state per hour starting January 5, 2022, deduplicated union quantities and frozen whole-development flow partitions. It is not an identical-estimand replication. Do not subtract the reported effects as if they were paired.

Raw support/resistance Delta quartile-conditioned tables are included alongside normalized features. Moderate-positive versus extreme-positive normalized contrasts are a separate transparent shape diagnostic, not the legacy Q3 label.

Full-map raw-Delta Q3 minus Q4 after A1/imbalance conditioning, same fixed display grid. These are NEW development-frozen full-map quartiles, not the legacy numeric cut. All windows/grids/quarters including cluster conditioning are in `raw-quartile-reconciliation.parquet`.

| phase | feature | condition | map_bucket | complete_raw_q3 | complete_raw_q4 | raw_q3_minus_raw_q4 |
|---|---|---|---|---|---|---|
| development | support_delta | A1 | 0 | 521 | 503 | -0.0045523 |
| development | support_delta | A1 | 1 | 536 | 567 | 0.03658 |
| development | support_delta | A1 | 2 | 568 | 617 | 0.045906 |
| development | support_delta | A1 | 3 | 539 | 475 | 0.075137 |
| development | support_delta | imbalance | 0 | 475 | 469 | 0.022467 |
| development | support_delta | imbalance | 1 | 619 | 640 | 0.0075045 |
| development | support_delta | imbalance | 2 | 492 | 548 | 0.072355 |
| development | support_delta | imbalance | 3 | 578 | 505 | 0.055809 |
| development | resistance_delta | A1 | 0 | 528 | 500 | -0.0064848 |
| development | resistance_delta | A1 | 1 | 530 | 573 | 0.048224 |
| development | resistance_delta | A1 | 2 | 587 | 610 | 0.025735 |
| development | resistance_delta | A1 | 3 | 552 | 479 | 0.050339 |
| development | resistance_delta | imbalance | 0 | 483 | 465 | 0.0187 |
| development | resistance_delta | imbalance | 1 | 610 | 648 | 0.017481 |
| development | resistance_delta | imbalance | 2 | 510 | 542 | 0.046791 |
| development | resistance_delta | imbalance | 3 | 594 | 507 | 0.036599 |
| replication | support_delta | A1 | 0 | 594 | 489 | -0.014945 |
| replication | support_delta | A1 | 1 | 440 | 302 | 0.049925 |
| replication | support_delta | A1 | 2 | 507 | 426 | 0.083979 |
| replication | support_delta | A1 | 3 | 816 | 636 | 0.0019654 |
| replication | support_delta | imbalance | 0 | 552 | 447 | -0.0032706 |
| replication | support_delta | imbalance | 1 | 471 | 360 | 0.061377 |
| replication | support_delta | imbalance | 2 | 455 | 355 | 0.068751 |
| replication | support_delta | imbalance | 3 | 879 | 691 | 0.0011508 |
| replication | resistance_delta | A1 | 0 | 597 | 493 | -0.0031462 |
| replication | resistance_delta | A1 | 1 | 434 | 306 | 0.06423 |
| replication | resistance_delta | A1 | 2 | 513 | 420 | 0.086229 |
| replication | resistance_delta | A1 | 3 | 815 | 637 | 0.0059828 |
| replication | resistance_delta | imbalance | 0 | 555 | 450 | 0.0067267 |
| replication | resistance_delta | imbalance | 1 | 465 | 365 | 0.077036 |
| replication | resistance_delta | imbalance | 2 | 461 | 349 | 0.070962 |
| replication | resistance_delta | imbalance | 3 | 878 | 692 | 0.0048356 |

Normalized positive-tail comparison, separately:

| phase | condition | map_bucket | complete_moderate | complete_extreme | moderate_minus_extreme |
|---|---|---|---|---|---|
| development | ALL | 0 | 3485 | 388 | 0.0013401 |
| development | A1 | 0 | 825 | 97 | 0.014908 |
| development | A1 | 1 | 893 | 111 | -0.022275 |
| development | A1 | 2 | 957 | 93 | -0.05019 |
| development | A1 | 3 | 810 | 87 | 0.07284 |
| development | imbalance | 0 | 764 | 83 | 0.010787 |
| development | imbalance | 1 | 1012 | 135 | 0.014998 |
| development | imbalance | 2 | 850 | 76 | -0.11347 |
| development | imbalance | 3 | 859 | 94 | 0.069353 |
| development | clusters | 0 | 645 | 88 | 0.025018 |
| development | clusters | 1 | 987 | 85 | 0.017653 |
| development | clusters | 2 | 447 | 58 | -0.058474 |
| development | clusters | 3 | 1406 | 157 | -0.00023104 |
| replication | ALL | 0 | 3257 | 565 | 0.025906 |
| replication | A1 | 0 | 834 | 149 | 0.082661 |
| replication | A1 | 1 | 560 | 98 | -0.043367 |
| replication | A1 | 2 | 738 | 106 | -0.00046019 |
| replication | A1 | 3 | 1125 | 212 | 0.034067 |
| replication | imbalance | 0 | 772 | 135 | 0.062637 |
| replication | imbalance | 1 | 638 | 107 | 0.0089649 |
| replication | imbalance | 2 | 622 | 106 | -0.022174 |
| replication | imbalance | 3 | 1225 | 217 | 0.034997 |
| replication | clusters | 0 | 2801 | 516 | 0.026236 |
| replication | clusters | 1 | 456 | 49 | 0.0071608 |

Some residual within-stratum differences can remain after coarse A1/imbalance conditioning. That alone cannot prove the old Q3 was a geometry proxy or prove the old effect survives unchanged. Conditioning one feature at a time leaves joint-map/regime confounding. The old nonlinear observation remains component research, neither rewritten nor invalidated.

All relationships are descriptive and dependent. No p-values, threshold selection, detector/window ranking, executable return or edge claim. Complete denominators include AMBIGUOUS and NEITHER; censored rows remain recorded. Conditional gross expectancy excludes unresolved/ambiguous/censored outcomes and costs.

Machine-readable tables: `data/phase3r2/`; diagnostic plots: `data/phase3r2/reports/diagnostics.html`.
