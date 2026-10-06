# Phase 3R: Volume Integration

## Authorized Warm-up

The user authorized 2020-09 through 2020-12 exclusively to complete the
850-day lookback. These dates are not performance observations. Sources are
official Binance USD-M Futures BTCUSDT monthly aggregate-trade and 1h kline
archives, with complete daily-publication replacement where necessary.
Raw archives, official checksum files and source URLs remain separate from
derived exact-price profiles in `data/phase3r/warmup/`.

| Month | Selected aggregate trades | Publication |
|---|---:|---|
| 2020-09 | 12,640,277 | Monthly |
| 2020-10 | 14,203,490 | Monthly |
| 2020-11 | 28,930,383 | Complete official daily collection |
| 2020-12 | 33,935,540 | Monthly |
| Total | 89,709,690 | Warm-up/history only |

Every selected archive has official SHA-256 and ZIP CRC verification. Existing
streaming validators check positive finite prices/quantities, timestamps,
chronology, duplicate records/IDs, date coverage and ID discontinuities.
Selected aggregate-ID sequences are continuous, including month boundaries
and the join to January 2021. Constituent first/last-trade-ID gaps remain
warnings rather than invented aggregate trades.

The November monthly archive passes its official checksum/CRC but has exactly
20,000,000 rows and lacks November 3, 5, 9, 12, 21, 25, 27 and 30. Therefore a
valid checksum is not by itself a coverage guarantee. The rejected archive and
integrity report remain unchanged. The whole month was reprocessed from all
30 official daily archives, not patched with synthetic or candle-volume rows.
The missing dates were checked against official 1m klines under the existing
outcome-blind coverage-v4 tolerances: 11,455 retained minute warnings and 65
boundary-conservation warnings; zero unresolved or newly quarantined minutes.
The audit covers all 11,520 minutes across the eight dates. Source selection
and coverage decisions precede map outcome evaluation.

Evidence: `warmup/plan.json`, `warmup/integrity/*.json`,
`warmup/coverage/2020-11-publication.json`, `warmup/coverage.json`.
Existing 2021-2022 normalized sources are read-only and re-hashed before use.
The Phase 3 coverage-v4 adjudication, including retained ID warnings and small
observable-loss quarantines, is reused without reversal. No 2024 data access.

## Two Deliberately Different Volume Windows

D integrates the full 850-day observed history. Hourly exact-price profiles
are regrouped into 50/100-dollar half-open bins, then rolling updates subtract
the expired hour and add the next closed hour. Bin configuration and input
hashes are preserved. Single-thread ordered input and bounded monthly batches
avoid retaining years of raw trades in memory. No bin size is called optimal.

A/B/C volume describes **only the last closed hour** around nearby candidates,
not all 850 days. Candidates in full or half proximity bands contribute their
full +/-width intervals. Within each kind, overlapping intervals are unioned
before summing exact observed-price quantities. Support and resistance can
share trades; joint-union volume and shared quantity are explicitly reported,
so adding both type totals is not a valid unique-volume total. Buy is aggressive
buy (buyer-is-maker false), sell is aggressive sell; delta=buy-sell and
normalized delta=(buy-sell)/quantity, null for zero volume. A quarantined hour
returns unavailable volume rather than a numeric zero.

There is no combined price/volume score, no fitted volume baseline, no new
relative-volume calibration, and no volume-based signal in this deliverable.
D also stores total and concentrated quantity above/below current price and
quantity straddling it. Neutral volume above price is not automatically
resistance, nor is neutral volume below price automatically support.

## Coverage Limitation and Prior Findings

The 850-day windows include the 62 minutes already quarantined in development.
Consequently all D sanity snapshots are observed-map reconstructions only,
not eligible complete-coverage predictive comparisons. The arithmetic is
validated against direct per-bin aggregation at the first and last decisions;
that does not establish that missing executed trades have been recovered.

Phase 3.5 artifacts remain untouched, including nonlinear Delta patterns,
support/resistance splits, visit-order, TP/SL/horizon and regime descriptions.
These remain single-zone component findings. They are not relabeled as
performance of the full rolling S/R map. Whether volume/Delta adds predictive
information to the complete map remains unanswered by this 24-state sanity run.
