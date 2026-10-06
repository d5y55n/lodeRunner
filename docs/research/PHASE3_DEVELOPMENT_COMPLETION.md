# Phase 3 Development Completion

Development-only descriptive results. Overlapping zones/configurations/horizons are dependent. No edge, significance, optimal-parameter or live-trading claim. No 2024 data used.

Development [2021-01-01,2023-01-01) UTC. Reserved validation [2023-01-01,2024-01-01). All 2024 untouched.

Verified acquisition: 36 months, 1,738,637,391 aggregate trades in selected official publications. Quarantined trade-volume minutes: 64.

Development configurations: 42; interactions: 64,229,528; unique decision-close events: 17,514.

Frozen validation configurations: 7. Selection is coverage-only (original 1h width and >=100 unique development events), never a win-rate ranking. Freeze ID: 677753eca72646eacf04a0e0075839f04ad9481a2f4e47e473c2926bc8d3fc7f.

Measurements use a lossless normalized representation: interactions.parquet + future_outcomes.parquet and the measurements view in research.duckdb, with reproducible measurement IDs. research_summary.csv carries exact row multiplicities and unique-event counts. Future interaction durations/exits are separate from decision-time features.

Scope: this long-range run uses 1h candles. Fixed half-widths are 0.0005/0.001/0.002/0.003/0.005; original 1h width is 0.004. Other timeframe mappings are not evaluated here. B widths 1/2, C reversals 0.003/0.005, D bins 50/100; no parameter ranking.

Limitations: event identity conservatively combines same-timestamp zones; adjacent horizons remain dependent. Quantile cuts can repeat, creating empty descriptive buckets. Gross expectancy is conditional boundary return on unambiguous resolved full-horizon observations, excludes costs and is not strategy P&L. Source agreement is not proof of complete executions; the predeclared tolerance can miss small deficits.

See PHASE3_COVERAGE_POLICY.md, coverage-manifest.json, forensic evidence, detector comparison, volume ablation and baseline comparison. Validation status is recorded separately; development completion is not evidence of an edge.
