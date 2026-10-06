# Phase 3R.1 Completion

Completed 1h only: optimized full-map reconstruction, exact reference parity gate,
1,000-timestamp benchmark, development A then B/C analysis, frozen 2023 replication,
observed D reconstruction and compact causal Volume/Delta preservation.

| phase | states | score_min | score_max | exact_scores | zero | negative | positive | sign_flips | changed |
|---|---|---|---|---|---|---|---|---|---|
| development | 8647 | -36 | 49 | 153 | 193 | 4714 | 3740 | 430 | 7863 |
| replication | 8760 | -48 | 49 | 165 | 163 | 4228 | 4369 | 571 | 8199 |

Development is 2022-01-05 17:00 through 2022-12-31 23:00 UTC (8,647 states).
No 2021 timestamp has the required 850-day price history. Replication is
2023-01-01 00:00 through 2023-12-31 23:00 (8,760 states), labeled exactly
`previously inspected replication period`. All 2024 market data remains untouched.
Five directional maps per timestamp: 87,035 snapshots in total, with 417,768
outcome rows stored once by event/grid. Final split-boundary horizons are censored,
not extended into 2023 for development or 2024 for replication.

Parity: 168 reference snapshots, all candidate memberships/features/coverage,
both D maps and 576 outcomes passed; integer scores/IDs exact, float tolerance
1e-12. Full suite: 243 tests, 0 failures,
0 errors, 0 skipped. See the separate final audit.

Measured generation:

| phase | stage | states | initialization_s | loop_s | peak_GiB |
|---|---|---|---|---|---|
| development | A | 8647 | 3.715 | 81.679 | 2.4474 |
| development | BC | 8647 | 3.5856 | 220.78 | 2.4355 |
| replication | A | 8760 | 4.3583 | 97.45 | 0.81236 |
| replication | BC | 8760 | 4.2691 | 202.28 | 0.78693 |

Generated development/replication research tables and analyses total
209.85 MiB (excluding raw archives and reusable derived inputs).
No full-run history is held as an ever-growing snapshot list. Memory is bounded
by catalog, monthly profile cache and daily output batches, not state count.

The original score closely tracks nearby support/resistance imbalance; this is
an algebraically related representation, not independent evidence. Shape and
quarter/replication differences are detailed in the result reports. No detector
winner, final score cutoff, leverage, trading signal or live execution was selected.

Additional archive acquisition: 117,925,990 aggregate trades in 2019-12-31 and
2020-01 through 2020-08, plus earlier authoritative REST candles. April/May monthly
publication failures were replaced by complete official daily collections.
One new observable-loss minute is quarantined, with the prior policy unchanged.
D has no fully clean 850-day trade window before 2024 and is not ranked.

New code: `backend/app/fullmap_scale/` (history/trades/coverage, engine/VAP,
parity/benchmark, streaming storage/explanatory features, stage runner,
analysis/freeze, reports/audit). New tests: `backend/tests/test_phase3r1.py`.
All new outputs are under `data/phase3r1/` and the ten PHASE3R1 reports.
Phase 3R reference code and previous research outputs remain preserved.

Reports: PHASE3R1_OPTIMIZATION, DATA_COVERAGE, A_FULLMAP_RESULTS, A_ABLATIONS,
CLUSTER_GEOMETRY, BC_COMPARISON, CHRONOLOGICAL_STABILITY, 2023_REPLICATION,
D_COVERAGE_STATUS (all `.md` at project root). Diagnostic plots: `data/phase3r1/reports/diagnostics.html` (96 SVGs, all outcome grids). Curves connect frozen development buckets for readability; no threshold is chosen.

Stopped before 15m/4h/1d, confluence, threshold selection and live trading.
