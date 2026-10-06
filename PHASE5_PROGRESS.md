# Phase 5 Progress (Complete)

Final status: COMPLETE, `STOP_NO_2024_NO_LIVE_RULE`.
See `PHASE5_COMPLETION.md` and `data/phase5/completion.json`.

Phase 5 is a separate read-only derived layer in `backend/app/confluence`.
Native Phase 3R/3R.1/3R.2 and Phase 4 code/data are not edited.

## Current Boundary

The 2022 development-only run completed and was reviewed before any 2023
source access. The full suite passed 313 tests with no failures/errors/skips.
The complete development definition, code, buckets and artifacts were frozen
under ID `145606c8498c8031366b0c4a709924dd86e836a0658e71840118fb18ee320fcd`.
The finite completion pipeline completed 2023 previously inspected replication
under that unchanged definition. No 2024 data was accessed.

The initial 18 new tests and the existing suite passed. An actual hourly
QUARANTINED native volume record exposed null side totals; the adapter now
preserves those as unavailable, not zero. A regression test was added.
The development build was restarted with that adapter correction.

## Evidence and Execution

- Contract: `PHASE5_CONFLUENCE_CONTRACT.md`.
- Status: `data/phase5/pipeline-status.json`.
- Completed run logs: `data/phase5/logs/completion.stdout.log` and
  `completion.stderr.log`; development logs are retained separately.
- Native inputs remain authoritative; candidate sets/scores are not refit.
- State alignment is closed-bar latest-at-or-before T; intervals are held
  with their native source state, with current-price distance separately stored.
- Empty/missing categories, unavailable flow and censoring remain explicit.

Development includes 34,585 decisions, 792 passing deterministic alignment/
truncation checks, 1,927 predeclared categories and 419 contrasts across all
24 outcome grids. Pooled 1/2/3/4 TP_FIRST shapes were nonlinear for all 12 LONG
and all 12 SHORT grids; definitions were not changed in response.

Replication includes 35,040 decisions and 716 passing alignment/truncation
checks. It uses exactly the same 1,927 categories, 419 contrasts and frozen
bucket boundaries. Existing 15m outcomes were reused: 830,040 development
rows and 840,960 replication rows, without regenerated labels.

The preservation audit passed for 56,898 unique artifacts. The final full
suite passed 313 tests with zero failures/errors/skips. All ten report hashes,
the development freeze, bucket/category equality and all 264 SVG XML files
and HTML image references were independently checked after completion.
Browser visual inspection of local HTML was blocked by the browser URL policy;
no browser workaround was attempted. Structural validation passed, but the
rendered layout was not visually inspected.

All requested reports, CSV/Parquet tables and offline SVG diagnostics exist.
No single candidate strategy was established. No live rule, leverage, winner
selection or untouched-2024 evaluation was performed. The pipeline stopped;
no recurring automation or next research phase was started.

Run from backend: `.venv/Scripts/python.exe -m app.confluence.pipeline`.
There is no active pipeline process and no need to rerun the completed research.
