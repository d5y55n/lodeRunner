# Predeclared Coverage Policy v4

Declared before further strategy-outcome inspection. This policy supersedes the
earlier automatic rejection of positive aggregate-ID jumps. All UTC intervals
are half-open. Development is 2021-2022, validation is 2023; no 2024 source access.

## Evidence and Units

Inspect EVERY positive aggregate-ID jump, including chunk/month boundaries.
Duplicates, reversed IDs/timestamps, invalid values or invalid checksum/CRC remain
hard integrity failures; a positive numerical jump alone is only a warning.
Preserve both adjoining complete trade records, elapsed milliseconds and price
change. Compare the containing minutes and every intervening minute, plus five
whole minutes on each side, against independently downloaded official daily
aggregate archives and official 1-minute USD-M BTCUSDT kline archives.
Daily/monthly publications share an upstream source: agreement is corroboration,
not proof of independently observed executions.

Record per-minute aggregate quantity, count, first/last timestamps, OHLC and
aggressive buy/sell quantity. Compare base-asset quantity to kline base volume;
never quote volume. Retain neighboring evidence, including absolute and relative
quantity differences and kline-vs-trade extrema differences. Report elapsed gaps
over 5 seconds and price changes over 1% as diagnostics only, never exclusions.

## Uniform Decision Rule

Use 1-minute units: the finest official comparison granularity used here.
A minute has MATERIAL_OBSERVABLE_DEFICIT when
`kline_base_quantity - aggregate_quantity > max(0.01 BTC, 0.01 * kline_base_quantity)`.
The fixed tolerances are engineering detection tolerances, not fitted research
parameters. They do not prove the root cause or guarantee absence of smaller loss.
Official aggregation can exclude some execution classes; record that limitation.

### Outcome-Blind v2 Amendment: Minute-Boundary Conservation

Before any full-development performance calculation, publication comparisons
revealed equal-and-opposite adjacent-minute differences (for example +1.760 BTC
then -1.760 BTC), without an intertrade outage. The official
[USD-M aggregate-stream documentation](https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-streams/market)
describes short-interval aggregation. A minute-bucketing difference is therefore
plausible; this is an inference, not proof of the exact mechanism for every pair.

Keep the original materiality thresholds. Before final decisions, inspect
chronologically ordered, DISJOINT adjacent minute pairs with opposite quantity
differences. Require both first/last trades within one second of each minute's
edges and at most one second between the adjoining trades. If combined quantity
differs by at most max(0.001 BTC, 0.000001 * combined kline quantity), retain both
minutes with a boundary-conservation warning. Process left to right and never
reuse a minute in another pair. The rule also applies to all prior affected
periods; publication comparisons include one neighboring minute on each side.
Keep raw minute discrepancies and old v1 reports. No timestamps or quantities are
shifted or replaced. Missing minutes and long outages cannot pass this check.
The amendment is driven only by source semantics and conservation evidence, not
detector performance. The v2 policy is separately hash-locked before outcomes.

### Outcome-Blind v3 Consistent Materiality Amendment

The v2 conservation check demanded near-exact pair equality while allowing 1%
discrepancy for single minutes. Several pairs leave a small residual (e.g.
+1.131 BTC followed by -1.138 BTC) below the original material threshold.
Use the SAME materiality criterion for the pair residual: max(0.01 BTC, 1% of
the SMALLER of the two official minute volumes). This is more conservative than
1% of their combined volume. Timing, disjoint-pair and source-agreement requirements
are unchanged. This source-quality correction precedes all development outcome
calculation and is not detector/strategy tuning. v1/v2 decisions remain archived;
only the then-active v3 manifest authorized research (none was run).

### Outcome-Blind v4 Bounded Conservation Blocks (Active)

Source-only inspection also found adjacent discrepancies spread over three minutes
(+1.822, +1.964, -3.786 BTC), and quiet minutes whose last trade was 1.148 seconds
before a minute end. These are not evidence of missing executions by themselves.
Generalize the SAME conservation check to the shortest qualifying contiguous block
of 2-5 minutes, using the original five-second time-gap diagnostic as the maximum
gap between adjoining trades. Do not require unrelated outer edges of the block
to contain a trade within one second. Require finite observed trades in every
minute, both positive and negative differences, source agreement, and residual
within max(0.01 BTC, 1% of the SMALLEST minute volume). Process chronologically,
consume the shortest qualifying block, and never reuse its minutes. Never merge
non-adjacent minutes or bridge an empty minute. Preserve original discrepancies,
the block bounds/residual and prior policy versions. No outcome inspection has
occurred; the active rule is hash-frozen as coverage-v4 before research.

When daily/monthly ordered source records agree and kline comparisons are available:
- Retain all inspected minutes without material deficits and preserve the ID warning.
- Quarantine ONLY each minute with a material deficit. Merge only adjacent such
  minutes. Do not quarantine an entire day/month or fill between separated deficits.
- Unusual timestamp/price motion alone never causes quarantine.
- Excess aggregate quantity over the same tolerance or inconsistent daily/monthly
  rows is UNRESOLVED, not silently accepted or repaired; research remains gated.

Missing official comparison sources or a missing/invalid kline minute are also
UNRESOLVED. No volume reconstruction, interpolation or kline-volume substitution.
No threshold changes after inspecting outcomes; any policy amendment must be
explicitly versioned and justified independently of strategy performance.

### Source Selection Addendum (Before Development Outcomes)

An invalid monthly publication (missing dates, duplicates or reversed records) is
preserved with its rejection report. Deterministically replace that ENTIRE source
month with checksum/CRC-verified official daily publications, not selectively with
favorable market days. Validate the concatenated daily sequence with the same
value/order/duplicate checks. Record every constituent source hash and the original
monthly failure. No record is fabricated, interpolated or silently deduplicated.
Apply the same forensic minute rule to any discontinuities remaining in the chosen
daily source. Audit rejected monthly gaps as publication discrepancies, including
daily/kline coverage evidence, before committing the final coverage manifest.

## Research Propagation and Freeze

Save source hashes, policy hash, evidence and retained/quarantined decisions before
research execution. Freeze a coverage manifest covering the full research catalog.
Raw archives and raw-derived price profiles remain unchanged by quarantine.
For the current 1h engine, omit D formation windows intersecting quarantined minutes
and mark any overlapping current/baseline volume window unavailable. A/B/C price
detectors still use independently verified official candles, so an aggregate-only
quarantine does not delete price history or alter price-only interactions/outcomes.
Retain affected interactions in S/R-only tables; group unavailable volume as MISSING,
never zero. This quarantines aggregate-volume use without selectively removing
volatile price episodes. Report both the minute quarantine and its hourly feature
impact. Validation cannot start until development and the frozen configuration exist.
