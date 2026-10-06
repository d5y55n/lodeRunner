# Phase 4 Completion

| timeframe | phase | earliest_850_day_decision_UTC | decision_timestamps | map_states | complete_contiguous |
| --- | --- | --- | --- | --- | --- |
| 15m | development | 2022-01-05T17:45:00+00:00 | 34585 | 172925 | True |
| 15m | replication | 2022-01-05T17:45:00+00:00 | 35040 | 175200 | True |
| 4h | development | 2022-01-05T16:00:00+00:00 | 2162 | 10810 | True |
| 4h | replication | 2022-01-05T16:00:00+00:00 | 2190 | 10950 | True |
| 1d | development | 2022-01-05T00:00:00+00:00 | 361 | 1805 | True |
| 1d | replication | 2022-01-05T00:00:00+00:00 | 365 | 1825 | True |

Final suite: 294 tests, 0 failures, 0 errors. Frozen artifact preservation: 17758 files unchanged.

## Completion Questions

1. Architecture: native parity gates and full one-candle coverage checks passed for all three timeframes.
2. Shared feature shapes: No feature/direction pair has a uniform nonzero pooled high-minus-low TP-first sign across every supported grid and all three new timeframes. Native-scale distributions and full contrasts are provided separately.
3. Timeframe-specific effects: daily timing resolution and differing widths/densities are structural, not predictive superiority.
4. A versus B/C: raw-imbalance stable/replicated cell counts for every detector are in PHASE4_BC_RESULTS.md. This is a controlled descriptive comparison, not evidence of a winning detector.
5. Cluster concentration: No supported comparison cells..
6. Candidate age: 15m LONG: 0/12 cells have the same nonzero sign in all four development quarters and pooled replication; 15m SHORT: 0/12 cells have the same nonzero sign in all four development quarters and pooled replication; 1d LONG: 6/12 cells have the same nonzero sign in all four development quarters and pooled replication; 1d SHORT: 0/12 cells have the same nonzero sign in all four development quarters and pooled replication; 4h LONG: 4/12 cells have the same nonzero sign in all four development quarters and pooled replication; 4h SHORT: 0/12 cells have the same nonzero sign in all four development quarters and pooled replication. Contact metrics are also exported.
7. Quantity versus ambiguity: 15m LONG: 12/12 cells have the same nonzero sign in all four development quarters and pooled replication; 15m SHORT: 12/12 cells have the same nonzero sign in all four development quarters and pooled replication; 1d LONG: 12/12 cells have the same nonzero sign in all four development quarters and pooled replication; 1d SHORT: 12/12 cells have the same nonzero sign in all four development quarters and pooled replication; 4h LONG: 12/12 cells have the same nonzero sign in all four development quarters and pooled replication; 4h SHORT: 12/12 cells have the same nonzero sign in all four development quarters and pooled replication. Conditional tables retain fixed map buckets.
8. Support normalized Delta: 15m LONG: 7/12 cells have the same nonzero sign in all four development quarters and pooled replication; 15m SHORT: 5/12 cells have the same nonzero sign in all four development quarters and pooled replication; 1d LONG: 0/12 cells have the same nonzero sign in all four development quarters and pooled replication; 1d SHORT: 0/12 cells have the same nonzero sign in all four development quarters and pooled replication; 4h LONG: 0/12 cells have the same nonzero sign in all four development quarters and pooled replication; 4h SHORT: 0/12 cells have the same nonzero sign in all four development quarters and pooled replication. No directional trading rule is established; other variants and missingness are retained.
9. Alignment: native outputs and frozen 1h passed causal lookup checks.
10. Remaining structural limitations: observed-only D history, daily OHLC ambiguity, quarantine-conditioned coverage, prior inspection of 2023 and multiple comparisons must carry into any later phase. No confluence evaluation was executed.

Detailed evidence: data/phase4/reports/*.csv and *.parquet; per-timeframe analysis directories retain full grids and bootstrap tables. STOP after this phase.

2023 is the **previously inspected replication period**, not an untouched final test. No 2024 market data, confluence performance, score summation, parameter ranking, or trading rule is used. All findings are descriptive, with overlapping outcomes and unadjusted multiple comparisons; no edge claim.
