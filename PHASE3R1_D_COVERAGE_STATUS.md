# D Coverage and Volume Preservation

| phase | bin_width | eligible_complete_coverage | insufficient_history | observed_maps |
|---|---|---|---|---|
| development | 50 | 0 | 2719 | 5928 |
| development | 100 | 0 | 2719 | 5928 |
| replication | 50 | 0 | 0 | 8760 |
| replication | 100 | 0 | 0 | 8760 |

The first temporally available 850-day aggregate archive window ends
2022-04-29 00:00 UTC. Earlier price-map timestamps are explicitly insufficient
for D and do not use a shorter trade window. Every later window before 2024
intersects at least one retained coverage quarantine, so there is no fair
complete-coverage D predictive sample. No zero-filling, interpolation, candle-volume
substitution or parameter ranking is performed.

Both 50/100-dollar neutral observed maps retain reference concentration multiple
1.5. Compact per-timestamp summaries preserve buy/sell/quantity/delta and quantities
above/below/current-straddling bins. Verified hourly bin inputs and configuration
are retained in `derived/`, allowing complete per-bin map reconstruction for
audit without duplicating every bin at every timestamp. Source hashes and
reconstruction instructions are in each phase's `D/complete.json`.

A/B/C compact last-closed-hour support/resistance union volumes, buy/sell/delta,
normalized delta and shared volume remain in state tables. Quarantined hours have
unavailable volume, not zero. No Volume Delta thresholds or combined score are
fitted. Phase 3.5 remains preserved single-zone component research; incremental
full-map Volume/Delta value is reserved for a later ablation.
