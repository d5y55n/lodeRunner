# Chronological Stability

Deterministic calendar quarters, no shuffled split, no per-quarter tuning:

| phase | quarter | states | A1_mean | A1_min | A1_max | clusters_mean |
|---|---|---|---|---|---|---|
| development | 2022Q1 | 2047 | -2.1637 | -36 | 31 | 23 |
| development | 2022Q2 | 2184 | 1.2255 | -33 | 34 | 22.095 |
| development | 2022Q3 | 2208 | -1.1506 | -28 | 33.5 | 10.888 |
| development | 2022Q4 | 2208 | -0.84307 | -33.5 | 49 | 7.5272 |
| replication | 2023Q1 | 2160 | -2.6562 | -40.5 | 49 | 6.2667 |
| replication | 2023Q2 | 2184 | 2.3622 | -29 | 33.5 | 1.4565 |
| replication | 2023Q3 | 2208 | 2.0444 | -36.5 | 37.5 | 1.4108 |
| replication | 2023Q4 | 2208 | 0.16621 | -48 | 32 | 2.452 |

Every feature/outcome grid has quarterly curves in `*-quarter-curves.parquet`
and shape diagnostics in `reports/quarter-curve-shapes.csv`. Exact A scores also
have quarterly and causal 24-hour volatility/recent-return regime tables.
Regime cuts are estimated on development only and frozen for replication.
Unconditioned quarterly baselines retain the same horizon/censoring conventions.

Check effect sign and shape across all four development quarters and all four
replication quarters rather than choosing a favorable quarter. Candidate counts,
clusters and price regimes are temporally correlated; a pooled relationship can
be driven by their changing composition. The partial 2022Q1 starts at the first
eligible timestamp; unavailable earlier dates are not treated as zero-effect data.

Seven-day time-block intervals supplement these quarterly comparisons, not
ordinary independent-hour significance tests. No p-value-based selection is made.
