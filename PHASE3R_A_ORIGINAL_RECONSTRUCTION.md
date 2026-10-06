# Phase 3R: Original A Reconstruction

## Reference and Scope

Reference: `C:\Users\82108\Desktop\script.js`. The unchanged copy is
`backend/tests/fixtures/phase3r/original-script.js`, SHA-256
`e926b86aaa48765369ead55f78ce44ba76dccbfd7a02466d0cc0364c64b4864f`.
The oracle extracts and executes the actual `scoring` function in Node's VM;
it does not reimplement the reference in JavaScript. Inert DOM outputs prevent
browser side effects. This validates the scoring function, not browser fetching,
DOM rendering, or the syntax of the complete original browser wrapper.

Only 1h is executed on historical market data. The four original constants are
independently golden-tested: 1d 0.022 (850 candles), 4h 0.007 (5,100),
1h 0.004 (20,400), 15m 0.002 (81,600). No timeframe scores are summed.

## Exact Rules

Each snapshot scans every adjacent pair in exactly 850 calendar days of closed
hourly candles. Bullish followed by bearish produces resistance at the minimum
of the two highs. Bearish followed by bullish produces support at the maximum
of the two lows. Strict candle direction excludes dojis. Equal eligible highs
or lows retain the earlier source candle, matching the existing A detector.

For reference price `p`, decision price `x`, width `w`:

* Full weight: `p*(1-w) < x < p*(1+w)`.
* Half weight: `p*(1-1.5*w) < x <= p*(1-w)` or
  `p*(1+w) <= x < p*(1+1.5*w)`.
* Exact outer boundaries contribute zero; exact inner boundaries contribute half.
* Support contributes +weight to LONG and -weight to SHORT.
* Resistance contributes -weight to LONG and +weight to SHORT.

Every qualifying historical candidate contributes, including repeated prices.
No deduplication, decay, invalidation after a crossing, or cap is introduced.
LONG and SHORT are exact negatives, not independent measurements.
Per-candidate weights and signed contributions are in `a-contributions.*`.

## Parity and Intentional Differences

The golden test runs 1,152 comparisons against the original function across
four timeframes, both directions, randomized candles, reversals, dojis and
exact proximity boundaries. Real-data parity additionally compares both
directions at every sanity timestamp. Results are in
`data/phase3r/run-results.json` and `data/phase3r/test-results.xml`.

Historical decision price is the last closed candle close at exclusive end T.
It is not the browser's manually entered/live ticker price. Unfinished candles
that a live REST response could include are deliberately not used. A pair
requires both candles inside `[T-850 days,T)`; a reference from a crossing-left-
boundary pair is not retained. Reference identity, known_at and both source IDs
are preserved. No browser trading actions are reproduced.

## Ablations, Not Selection

A1 preserves the reference exactly. A2 removes half-weight contributions only.
A3 stores nearby support/resistance counts without directional score weights.
A4 stores nearest signed/absolute and mean absolute relative distances in the
raw map; the tabular comparison includes the nearest absolute distances.
All share the same underlying timestamp and future outcomes. They are not
independent samples. No ablation winner, threshold or final strength formula
is selected.
