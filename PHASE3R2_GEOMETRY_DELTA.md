# Geometry and Delta

Development: the unchanged 8,647 hourly events from 2022-01-05 17:00 through 2022-12-31 23:00 UTC. Replication: 8,760 events in 2023, labeled `previously inspected replication period`. No 2024, other timeframes, D predictive comparison, or live rules.

A2, A3 imbalance and counts, A4 nearest-distance relationship, clusters and candidates-per-cluster all receive identical incremental cross-tabs. B1/B2/C.003/C.005 retain raw geometry; A weights are never copied onto them.

Conditioned tables retain same-period unconditioned TP fraction, same valid/finite-flow cohort baseline, and same-cohort map-only stratum baseline. The incremental column is conditioned fraction minus map-only fraction. One-dimensional frozen strata are not exact full-map matching; residual confounding within buckets remains. Joint cluster concentration additionally crosses map direction, cluster quartile and candidates-per-cluster quartile. Sparse/absent cells are not filled or refit.

Few-cluster/many-candidate versus many-cluster/fewer-candidate states are represented by every observed `cluster_concentration` cell. Code = direction*100 + cluster_bucket*10 + candidates_per_cluster_bucket; direction 0=resistance-heavy, 1=equal, 2=support-heavy. This categorical code is not a strength score.

2023 has a large cluster-distribution shift already documented in 3R.1. Absent frozen strata remain absent. Replication comparisons require the same observed map bucket, rather than relabeling the two periods' low/high groups. Quantity ratios and overlap can make both sides' Delta nearly identical.

All relationships are descriptive and dependent. No p-values, threshold selection, detector/window ranking, executable return or edge claim. Complete denominators include AMBIGUOUS and NEITHER; censored rows remain recorded. Conditional gross expectancy excludes unresolved/ambiguous/censored outcomes and costs.

Machine-readable tables: `data/phase3r2/`; diagnostic plots: `data/phase3r2/reports/diagnostics.html`.
