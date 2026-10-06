# Phase 3R.2 replay

Run from `backend` with the existing virtual environment. No new dependencies.
Do not invoke previous-phase runners: their artifacts are read-only inputs here.

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
.venv/Scripts/python.exe -m app.fullmap_flow.features development
.venv/Scripts/python.exe -m app.fullmap_flow.analyze development
.venv/Scripts/python.exe -m app.fullmap_flow.analyze freeze
.venv/Scripts/python.exe -m app.fullmap_flow.features replication
.venv/Scripts/python.exe -m app.fullmap_flow.analyze replication
.venv/Scripts/python.exe -m pytest --junitxml=../data/phase3r2/test-results.xml -q
.venv/Scripts/python.exe -m app.fullmap_flow.audit
.venv/Scripts/python.exe -m app.fullmap_flow.reports
```

Treat the completed run as sealed research. A deliberate new definition needs
a new version/output directory, not an overwrite of a completed freeze.

Data layout under `data/phase3r2`:

- `plan.json`: predeclared feature, window, grouping and uncertainty definitions.
- `preserved-before.json`: prior Phase 3R.1 artifact and implementation hashes.
- `<phase>/features/`: daily exact-price flow, five configs, three windows.
- `<phase>/features-complete.json`: status counts, source hashes, 1h parity count.
- `<phase>/analysis/<config>-<window>h/states.parquet`: event-aligned causal features only.
- `model.json` in development folders: frozen flow cuts. Price cuts are the existing Phase 3R.1 cuts.
- `curve-*.parquet`: marginal shape tables; `within-*.parquet`: conditional outcome compositions and baselines.
- `ci-*.csv`: paired weekly-block cell-minus-map-baseline uncertainty.
- `development-freeze.json`: development outputs and research-definition code seal.
- `reports/`: cross-period/quarter comparisons and offline SVG diagnostics.
- `verification.json`: final preservation, causality, accounting and join checks.

`period=ALL` and quarter rows are separate summaries of the same hourly events.
Do not add them together. Flow groups are descriptive, not executable signals.
`complete` excludes censored horizons but includes ambiguous/neither outcomes.
Missing normalized flow is not neutral. Conditional comparisons use the same
coverage-valid finite-flow cohort for both the conditioned and map-only baseline.
Map bucket -1 means undefined geometry, not a low map state. Cluster categorical
codes retain all observed combinations; they are not ordered strength scores.
