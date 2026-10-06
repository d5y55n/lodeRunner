# Phase 3 Status

Snapshot UTC: 2026-09-27T15:26:21.717339+00:00

Development: [2021-01-01, 2023-01-01) UTC. Validation: [2023-01-01, 2024-01-01) UTC.
All 2024 data remains reserved. No live signals or trading execution.

Official source groups checked: 72/72; passed 72, failed 0.
Aggregate rows in passed sources: 1,738,637,391.
Passed trade months: 2021-01, 2021-02, 2021-03, 2021-04, 2021-05, 2021-06, 2021-07, 2021-08, 2021-09, 2021-10, 2021-11, 2021-12, 2022-01, 2022-02, 2022-03, 2022-04, 2022-05, 2022-06, 2022-07, 2022-08, 2022-09, 2022-10, 2022-11, 2022-12, 2023-01, 2023-02, 2023-03, 2023-04, 2023-05, 2023-06, 2023-07, 2023-08, 2023-09, 2023-10, 2023-11, 2023-12

## Coverage Decisions

Outcome-blind coverage ready: True. Trade-volume quarantine: 64 minutes.
Numerical ID gaps alone do not exclude periods. The active coverage policy and its versions
are documented in PHASE3_COVERAGE_POLICY.md. Consistent ID/boundary warnings are retained.
Invalid monthly publications are preserved and explicitly replaced by verified official daily sources.
Verified candle-based price history remains included through volume-only quarantine.
No trade reconstruction, interpolation or candle-volume substitution.

## Implemented and Tested

Monthly archive capture, official checksums, ZIP CRC, integrity checks, raw/derived separation;
trade-derived hourly price profiles; A/B/C volume attachment; D real-volume execution;
stable identities, unique-event counts, causal control index, development-only bucket fitting;
hash-locked validation configuration; separate decision features and future outcomes/lifecycles.

Latest test report: 194 tests; failures=0, errors=0.

## Research State

Development completion report exists: True. Validation configuration frozen: True.
Validation completion report exists: True. Final test used: false.
Long-range scope is 1h; other original timeframe mappings are not evaluated in this run.
No edge claim, parameter ranking, live signal or trading execution.

## Files Added or Updated

- PROJECT_SPEC.md; docs/research/PHASE3_DESIGN.md; this status report.
- backend/app/market/phase3_archives.py; phase3_gap_audit.py.
- backend/app/market/phase3_coverage.py; phase3_daily_fallback.py; phase3_publication_audit.py.
- backend/app/research/phase3_plan.py; phase3_identity.py; phase3_context.py; phase3_fast.py.
- backend/app/research/phase3_profiles.py; phase3_statistics.py; phase3_engine.py; phase3_status.py.
- backend/app/research/phase3_storage.py; phase3_disk_summary.py; phase3_reports.py.
- backend/tests/test_phase3_foundations.py; test_phase3_acquisition.py; test_phase3_fast.py;
  test_phase3_statistics.py; test_phase3_pipeline.py.

- backend/tests/test_phase3_coverage.py; test_phase3_publications.py; test_phase3_disk.py.
- backend/pyproject.toml; backend/uv.lock.

See PHASE3_DESIGN.md and data/phase3/integrity for details.
