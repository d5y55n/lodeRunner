# Phase 5.1: same-current-price A state confluence

This is not a new map engine. It evaluates the frozen latest native candidate
membership at the current closed 15m price P for each timeframe. Native 850-day
membership only advances at the native close. Strict full/half weights are the
original ones, without new thresholds. 15m existing descriptors are reused.

Commands from backend:

- `.venv/Scripts/python.exe -m app.current_confluence.pipeline --states-only`
- `.venv/Scripts/python.exe -m app.current_confluence.pipeline --development-only`
- `.venv/Scripts/python.exe -m app.current_confluence.pipeline`

The first stops after an outcome-blind current-P classification audit; the second
stops after 2022 analysis. The final command reviews/tests/freezes development
before any 2023 access, then runs frozen replication, preservation and final reports.
Do not launch duplicate jobs. Use single-thread BLAS for bounded matrix work.

## Completed-run validation amendment

The original frozen builder's shared-close price-equality assertion encountered
one stored 1h/15m close discrepancy in 2023. Do not edit frozen code to bypass it.
The outcome-blind `scripts/phase5_1_validation_amendment.py` runner replays every
2022 state exactly, seals its general validation rule, and builds replication
states with scalar checks at both source prices, retaining common 15m P and a
warning. It must run after the development freeze and BEFORE replication analysis;
it deliberately refuses to run if replication analysis already exists. The normal
pipeline can then resume from the amended audited states. Do not delete artifacts
to force another run. Evidence is in data/phase5_1/validation-amendment.

The completed reports include manually reviewed direct answers and amendment
disclosures after generation. Re-running the frozen report generator overwrites
those notes; preserve/review them and refresh report hashes if regenerating.
Original frozen Python files and development artifacts remain unchanged.

Outputs under data/phase5_1 keep states separate from reused future labels.
Each timeframe has source timestamp/age, evaluation P, nearby/raw/full-map counts,
imbalance, A1/A2 and nearest geometry. Native strength quantiles and raw 4D vectors
are retained without summing scores/counts. Continuous univariate strength slopes
are descriptive, not weighted direction scores. Quantity and Delta are separate.

Primary hypotheses: SSSS LONG; RRRR SHORT; the exact lower-to-higher hierarchy;
strength within SSSS/RRRR. Exact patterns and secondary paths are never ranked.
No spatial intersections, 2024 evaluation, live execution or leverage logic exists.
