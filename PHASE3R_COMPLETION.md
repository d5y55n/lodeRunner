# Phase 3R First Deliverable: Complete

Completed only the 1h full-map reconstruction, exact original A parity,
A/B/C/D causal snapshots, small real-data sanity run and feasibility benchmark.
No full multi-year strategy experiment, other-timeframe execution, arbitrary
timeframe summation, threshold selection, live signals, or 2024 data access.
2023 remains previously inspected replication; no new replication run was made.

## Data and Window

Authorized warm-up: 2020-09-01 through 2020-12-31, history only.
89,709,690 aggregate trades, official Binance USD-M BTCUSDT sources, official
SHA-256/CRC checks. September, October and December use monthly archives;
November uses the full official daily collection after actual missing dates
were found in the checksum-valid monthly archive. Raw rejected evidence and
outcome-blind coverage decisions are preserved. No invented or interpolated
trades, and no candle-volume substitution. See the volume report for counts,
eight missing dates, minute audits and source paths.

Combined candle history: 2020-09-01 through 2022-12-31, 20,448 hourly candles.
Each real snapshot uses exactly 850 days / 20,400 candles ending at T;
decision price is the last closed candle close. Candidates must be confirmed
and sourced inside the window. Trade windows are half-open and exclude T.

First eligible decision is **2022-12-30 00:00 UTC**. The sample is the first
24 consecutive eligible hours, ending 23:00 UTC that day, selected before
outcomes. All future labels stay inside 2022. Earlier development dates lack
the authorized 850-day history and are not evaluated using shorter windows.
This is not a completed full 2021-2022 full-map performance study. More earlier
history would be needed for that; its availability has not been established.

## Results and Verification

* 168 snapshots, seven parameterizations, 24 unique underlying timestamps.
* 61,597 cataloged directional candidates and 3,372 A contribution rows.
* 42,768 D bin rows; 50/100-dollar bins, concentration multiple 1.5 retained.
* 576 separately stored future-outcome rows: both directions, TP/SL 0.003/0.005,
  horizons 4/8/24. None censored in this sample.
* A parity: 1,152 golden JavaScript comparisons plus 48 real-data comparisons,
  all exact. Original constants and strict band boundaries retained.
* Full suite: **231 passed, 0 failed, 0 skipped**; 21 Phase 3R test cases.
  One existing Starlette/httpx deprecation warning, unrelated to these changes.
* Independent saved-export audit: 168 contracts, 1,476,905 membership checks,
  24 A score reconstructions and 42,768 D bin conservation checks passed.
* Ten A/B/C truncated-future replays, four D truncated-future replays and four
  direct D aggregation comparisons passed. Deterministic JSONL/Parquet export
  and derived-cache rebuild tests passed.
* A/B/C recent trade-volume features are available on 120/120 snapshots.
  D windows intersect 62 previously quarantined development minutes, so all
  48 are explicitly observed/incomplete maps, with **zero** eligible
  complete-coverage predictive comparisons. Quarantines were not revoked.

No prior research was invalidated or relabeled as full-map performance.
194 before/after source/report/Phase 3.5 artifact hashes match. The Phase 3
code digest and its original development/validation completion hashes also
match the pre-existing Phase 3.5 lineage record. Source normalized-file hashes
were verified before reuse. Details are in `data/phase3r/verification.json`.

## Measured Feasibility

Measured on this Windows host with the existing Python environment:

| Measurement | Result |
|---|---:|
| Setup, source checks, two VAP builds and initialization | 148.70 s |
| 24-state, seven-configuration rolling loop | 83.61 s |
| Total run including exports and parity/replay checks | 288.89 s |
| Python process peak working set | 2.135 GiB |
| Generated sanity exports, JSONL plus Parquet/CSV | 217.39 MiB |
| 50-dollar hourly bin preprocessing | 52.38 s; 184,034 rows |
| 100-dollar hourly bin preprocessing | 58.98 s; 101,704 rows |

Median per-state detector times: A 0.518 s, B1 0.502 s, B2 0.336 s,
C0.003 0.978 s, C0.005 0.820 s, D50 0.0093 s, D100 0.0043 s. D's initial seed
is slower and is included in total loop time. Memory is parent Python process
peak, not a machine-wide total or the separate Node oracle process peak.

A naive linear projection to 17,520 hourly steps is about **16.95 hours of
map-loop compute and 154.97 GiB of these duplicated inspection exports**.
This is a compute/storage projection, not a measured multi-year run, coverage
claim or production capacity guarantee. It excludes extrapolated outcome,
serialization and download costs; repeated seed/check costs also make linear
scaling approximate. The current small-run writer retains state in memory;
full-scale execution would require streaming exports and more compact
membership storage before scaling. Do not launch it unchanged for years.

Two initial preprocessing attempts exceeded DuckDB's 2GB limit (years at once,
then monthly ordered-aggregate buffers). The completed version processes
months separately with sorted input and serial aggregation; it did not reduce
the 850-day window, change bins, or alter source quantities. Failed attempts
are excluded from the successful-run timings above.

## Files and Inspection

New Phase 3R code is isolated under `backend/app/fullmap/`:
`__init__.py`, `contract.py`, `core.py`, `volume.py`, `acquire.py`, `data.py`,
`run.py`, `verify.py`. Tests are `backend/tests/test_phase3r.py` and
`backend/tests/fixtures/phase3r/{original-script.js,original-oracle.cjs}`.
Existing `app/research` and `app/deepdive` implementations were not edited.

The six reports are this file plus:

* [Original A reconstruction](PHASE3R_A_ORIGINAL_RECONSTRUCTION.md)
* [Full-map contract and field semantics](PHASE3R_FULL_MAP_CONTRACT.md)
* [A score distribution and ablations](PHASE3R_A_SCORE_ANALYSIS.md)
* [B/C/D counts and inspection findings](PHASE3R_BCD_FULL_MAP_SANITY.md)
* [Volume integration and integrity limitations](PHASE3R_VOLUME_INTEGRATION_NOTES.md)

All new data artifacts are under `data/phase3r/`: warm-up raw/integrity/coverage,
derived bins with exact configuration manifests, `plan.json`,
`source-lineage.json`, `run-results.json`, `verification.json`,
`preserved-before.json`, `test-results.xml` and `sanity/` exports.
The original reports and artifacts remain in their previous directories.

Reproduce from `backend` using the existing virtual environment:

```powershell
.venv\Scripts\python.exe -m app.fullmap.acquire
.venv\Scripts\python.exe -m app.fullmap.run
.venv\Scripts\python.exe -m pytest -q --junitxml=../data/phase3r/test-results.xml
.venv\Scripts\python.exe -m app.fullmap.verify
```

The run command repeats only the declared 24-state sanity sample, not a
multi-year search. Future outcomes are separated from creation-time features.
All candidate prices and memberships remain joinable for further plotting.

## Deviations, Ambiguities and Stop

Closed-candle close replaces the original manually entered/live ticker price;
unfinished candles are excluded. C uses an explicitly window-local reset,
not global-history tracker initialization. A/B/C volume uses the last closed
hour, while D uses the full 850-day observed window. D remains neutral and
incomplete-coverage status is not hidden. B/C do not inherit A's scoring.

Inspection found very dense overlapping candidate maps, repeated prices and
C's high candidate count from independent trackers. A LONG scores are positive
throughout this one-day sample; zero/negative A1 states are absent. These are
important descriptive limitations, not reasons to retune parameters or discard
unfavorable observations. The half band changes 21/24 A scores, but its utility
is not established. No monotonicity or edge claim is made.

**Stopped at the requested first deliverable.** Other timeframes, confluence,
full multi-year evaluation and live trading are not automatically started.
