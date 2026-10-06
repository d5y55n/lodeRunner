# Phase 3 Completion

Development and separately frozen validation descriptive results. Overlapping zones/configurations/horizons are dependent. No edge, significance, optimal-parameter or live-trading claim. No 2024 data used.

Completed the 1h historical research scope: development 2021-2022, one frozen validation evaluation in 2023. All 2024 remains untouched. No live signals or trading. Other timeframe mappings were not evaluated.

| phase | configurations | interaction_rows | unique_events | measurement_rows |
| --- | --- | --- | --- | --- |
| development | 42 | 64229528 | 17514 | 1541508672 |
| validation | 7 | 1999618 | 8749 | 47990832 |

Coverage policy: coverage-v4; quarantined trade-volume minutes: 64; retained price history is unchanged. Source groups: 72/72, aggregate rows: 1,738,637,391.

Frozen configuration ID: 677753eca72646eacf04a0e0075839f04ad9481a2f4e47e473c2926bc8d3fc7f. Selection used development coverage only, not win-rate ranking. Validation was not used to refit quantiles or choose settings.

See separate development and validation detector/volume/baseline reports and PHASE3_COVERAGE_POLICY.md for source-quality amendments made before outcomes. No final strategy or edge conclusion is made.

## Final Verification

The entire test suite passed: 194 tests, zero failures/errors/skips, one existing
Starlette/httpx deprecation warning. Final saved-artifact checks confirmed both
period boundaries, unique event IDs, causal matched-control horizons, exact
measurement multiplicities, matching completion/freeze IDs, unchanged frozen
research code and unchanged coverage adjudication.

Development candidates: A 9,201; B 13,252; C 30,624; D 62,476.
See PHASE3_INSPECTION_NOTES.md for overlapping-event, ambiguity, missing-volume
and detector-rule caveats. No additional tuning or evaluation follows this run.

## Report Index

- PHASE3_DETECTOR_COMPARISON.md and PHASE3_VALIDATION_DETECTOR_COMPARISON.md
- PHASE3_VOLUME_ABLATION.md and PHASE3_VALIDATION_VOLUME_ABLATION.md
- PHASE3_BASELINE_COMPARISON.md and PHASE3_VALIDATION_BASELINE_COMPARISON.md
- PHASE3_COVERAGE_REPORT.md and PHASE3_COVERAGE_POLICY.md
- PHASE3_STATUS.md for acquisition, tests and major implementation files

Machine-readable artifacts remain under data/phase3/development and
data/phase3/validation. The validation configuration is frozen-validation.json.
Additional completion/recovery implementation files are phase3_feature_batch.py,
phase3_recover.py, phase3_finish.py and test_phase3_completion_guard.py.
