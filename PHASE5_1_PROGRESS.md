# Phase 5.1 Progress: Complete

## Current-Price Semantics

The development classification audit completed BEFORE reading future outcomes.
Phase 5 carried higher-timeframe descriptors at their native source close price;
those were not generally the same as evaluating every timeframe at current 15m P.
Frozen candidate memberships, detector A, widths and 850-day native windows are
unchanged. This layer only recomputes proximity counts, A1/A2 and distances at P.
No spatial union/intersection is read or calculated.

Development: 34,585 eligible decisions; 15,505 complete patterns change from the
Phase 5 carried-price semantics. Current-price SSSS=4,712, RRRR=8,306.
The 15m fields are reused exactly. Higher-timeframe source-price parity passed for
8,647 hourly, 2,162 four-hour and 361 daily snapshots. Deterministic same-P scalar
reference and truncated alignment checks passed for 260 timeframe/example rows.
Real SSSS, RRRR, mixed, neutral and missing examples all exist and were inspected.
237 real decision rows contain at least one empty/unavailable current neighborhood.

An independent read-only comparison against ONLY the stored Phase 5 event ID,
timestamp and imbalance_pattern columns passed for all 34,585 development rows:
the old carried pattern reconstructed for the audit equals the stored old pattern.
No spatial feature columns were used. This distinction is not evidence against
the current-price SSSS/RRRR hypothesis.

## Development Review and Freeze

Narrow development analysis completed: 411 categories (including all exact
S/R/N/M patterns as descriptive cells), 72 predeclared contrasts, and separate
continuous-strength slope tables. No strongest-cell selection was performed.
The exact primary LONG hierarchy had 11 monotonically increasing TP_FIRST grids
and one nonlinear grid in pooled 2022. SHORT had nine nonlinear and three
monotonically decreasing grids. These are development observations, not a rule.

The full suite passed 327 tests, with zero failures/errors/skips. Complete
definitions, code, development results and bucket boundaries were frozen before
any 2023 source read under ID
`db6bd4971bab364cc8469c3143f4ca8d55aee7c771a5d279068ce787b3d8af85`.

## Completion

The finite pipeline completed: 35,040 replication timestamps, SSSS=8,381,
RRRR=6,199; unchanged 411 categories and 72 comparisons. All ten requested
reports exist. Final suite: 331 passed, zero failures/errors/skips. Preservation:
58,382 artifacts verified, zero changes. Original outcome rows reused:
830,040 development and 840,960 replication. No candidate is promoted because
the primary hierarchy and directional relationships do not consistently replicate.
See `PHASE5_1_COMPLETION.md` for all 13 direct answers and evidence tables.

New code: `backend/app/current_confluence`; tests: `backend/tests/test_phase5_1.py`.
New data: `data/phase5_1`; status: `pipeline-status.json` within that directory.
The original pipeline stopped before replication outcomes because one shared
native close had differing stored source prices: 2023-11-10 16:00 UTC, 15m
P=37118.4 versus frozen 1h P=37092.6. 4h and 1d agree with the 15m price at their
shared close. At either price the original scalar A scoring is reproduced; the
1h direction is R at both, but its degree/A1/A2 differs as expected.

No original frozen code, data, definition or freeze manifest was edited. A separate
validation-only runner (`backend/scripts/phase5_1_validation_amendment.py`) retains
both source prices and verifies the scalar rule at BOTH prices instead of assuming
different authoritative timeframe archives must share the same close. It always
uses current 15m P, never replaces prices, excludes a row or refits a threshold.
This is a general rule, not a hardcoded date exception. Four added regression tests
pass. This amendment was sealed before replication outcomes; replication analysis
has now completed under unchanged definitions and development bucket boundaries.

The runner verified exact equality of every 2022 current-state row/column
(34,585 rows, 137 columns, including dtypes) against the frozen output, then sealed
its validation-only definition before rebuilding replication states. Its logs are
`data/phase5_1/logs/validation-amendment.stdout.log` and `.stderr.log`.
The original implementation/freeze remains verifiable. The resumed pipeline log
is `data/phase5_1/logs/completion-resumed.stdout.log`; final pipeline status is
`COMPLETE / STOP_NO_2024_NO_LIVE_RULE`. No background research run remains.

No 2024 data, live trading, leverage, detector changes, arbitrary search or native
artifact edits are authorized or performed. No next phase or recurring job exists.
