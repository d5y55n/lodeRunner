# Scoring Directional Percentile

## Unchanged Analysis

`app/website/scoring.py` and `converging.py` are byte-for-byte unchanged.
Detector A, common closed 15m decision price, proximity endpoints, recency,
normalization and TF weights remain exactly as before. The new response field
`scoring_percentile` does not rescale or replace `scoring.overall`.
Historical computations vectorize the same weights and chronological side sums;
parity with the authoritative scorer is tested to absolute tolerance 1e-14.
Current and manual scoring still use the original scorer, not the vectorized path.

## Population And Causality

Scope: symbol x full configuration hash x scoring source hash x distribution
version x lookback. The population is each available 15m decision, not selected
reactions or successful outcomes. Every historical score uses that decision's
actual latest closed 15m price for all four native TFs. Candidate known_at must
be <= the decision; both candles must be inside its 850-day scoring window.
Only samples in [T - history_days, T) enter the CDF and all reported statistics.
Current and future samples are excluded, even when the cache contains later data.
Historical replay can backfill earlier missing observations independently.

The configured distribution window is 850 days, but coverage is limited to
available operational candles with the FULL original analysis lookback and
bootstrap. The existing operational cache has about 880 days of candles, not
1700 days. Thus this revision verifies roughly 30-32 days of eligible decisions,
NOT an 850-day-long distribution of full-lookback decisions. No partial 850-day
scoring windows are substituted and no sparse downsampling is used. UI/API expose
actual population dates and counts. Missing periods are not synthesized. Existing
frozen research archives are neither changed nor used to pool live symbols.

Positive scores compare against historical positive scores only. Negative scores
compare absolute magnitude against historical negative scores only. Exact zero
has direction BALANCED and null percentile. No near-zero threshold is introduced.
The old scoring.overall.state still retains its original balanced-band semantics;
the main card's directional display explicitly follows the new exact-sign rule.

Converging's existing function is reused:
100 * (count(samples < magnitude) + 0.5 * count(samples == magnitude)) / N.
Minimum N is the configured min_distribution_samples (currently 30), counted in
the same direction. Insufficient histories have null percentile. Quantiles use
NumPy's default linear interpolation. Zero samples remain in the signed summary
and histogram but never enter either directional population.

## Manual Price, Cache, And History

Manual P changes only the current observation. It never enters or reconstructs
the historical baseline. The same symbol/config/decision baseline is reused.
Each symbol's operational directory contains scoring-distribution.sqlite3 with
immutable observation values and completed-request records. Only missing
eligible decision values are computed on cache misses. Earlier source availability
invalidates completion records, allowing backfill. Closed input candles are
immutable under Store.insert, which rejects conflicts. Direct external edits of
SQLite input candles are unsupported. No network downloads are added by this
feature. Initial backfill is synchronous; later same-decision requests reuse it.

Live/current/manual and operational replay snapshots expose scoring_percentile
additively. New saved snapshots include it; old persisted snapshots are not
rewritten. History responses enrich old snapshots using their own config and
decision time. Existing frozen legacy research responses may omit it and the UI
shows unavailable history without breaking them. No original consumer fields or
stored snapshot checksums are changed.

## Presentation

The main card shows signed score and directional percentile. No percent sign is
used. A value just below 100 is displayed as <100.0 instead of rounding up.
Labels: <75 normal, [75,90) elevated, [90,95) strong, >=95 extreme.
These are descriptive presentation bins, not trading rules or optimized cutoffs.
The signed 40-bin histogram is in Details only, with a current-price marker.
Counts, coverage, configuration key, signed min/max/mean/median and all requested
quantiles are available in Details and the JSON response.

Percentile describes historical same-direction strength, NOT a win rate,
probability of rising/falling, prediction, or LONG/SHORT recommendation.
Adjacent 15m observations are serially dependent; sample count is not an
independent-trial count. No outcome labels, calibration or edge claims are added.

## Verification

Final regression run: 416 Python tests and 20 Node tests passed. The existing
Starlette/httpx deprecation warning remains. Website v4 real API verification
also passed current-score parity and unchanged Converging/candles.

Python tests cover frozen formula hash, nonzero historical scorer parity, future
candle perturbation, current/future exclusion, both directions, exact/near zero,
ties, insufficient samples, window expiry, bounds, config/version/symbol cache
isolation, replay backfill, manual baseline reuse, and old snapshot compatibility.
Node tests cover presentation, near-100 rounding, signed histogram and existing UI.
Browser checks exercise manual P=70000 and restoration, unchanged baseline,
desktop/mobile histogram and no page overflow or JavaScript errors.

Reproduce:

```text
backend/.venv/Scripts/python.exe -m pytest -q
node --test frontend/analysis/*.test.cjs
backend/.venv/Scripts/python.exe backend/scripts/verify_scoring_distribution.py
```

Run Python tests from backend; verification script supports either working directory.
Evidence: data/live-dashboard/scoring-percentile-verification.json,
scoring-percentile-tests.xml, scoring-percentile-desktop.png and
scoring-percentile-mobile.png. Verification uses each symbol's latest locally
stored snapshot; timestamps differ and are recorded, not presented as simultaneous
live observations.

Recorded BTC example: score +0.05057915298425257, SUPPORT, 22.18370883882149
percentile, 1731 directional samples / 3101 signed observations.
Positive q50/q75/q90/q95/q99:
0.106279 / 0.173393 / 0.227644 / 0.246440 / 0.275871.
Negative magnitude q50/q75/q90/q95/q99:
0.114877 / 0.157310 / 0.199199 / 0.224896 / 0.280842.
ETH: -0.2646420915, RESISTANCE, 92.2636 percentile, N=2094.
SOL: +0.1029356651, SUPPORT, 27.5079 percentile, N=1894.
All three use distinct distribution identities and independently computed data.
