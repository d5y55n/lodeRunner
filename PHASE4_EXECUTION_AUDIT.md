# Phase 4 Execution Audit

This appendix records measured acquisition/parity and native price-generation costs. Overall completion is governed by `data/phase4/completion.json`, not this appendix.

## 15m Pre-Run Benchmark

The real-data gate compared 120 native snapshots and five physically truncated-input cases against the reference. The subsequent benchmark processed 1,000 consecutive timestamps / 5,000 A/B/C map snapshots in 118.816 seconds, with 945,463,296 peak process-memory bytes and 3,079,875 output bytes. Projection over 69,625 development-plus-replication timestamps was 8,272.558 seconds and 214,436,297 bytes.

That projection covers map generation and compact state/membership serialization only. It excludes acquisition, future-outcome labels, flow, contact features, statistical analysis and final exports; it is not an end-to-end runtime estimate.

## Measured Native Price Passes

| TF | Period | Timestamps | Map states | Separate outcome rows | Runtime seconds | Peak RAM bytes | Price-pass bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 15m | Development | 34585 | 172925 | 830040 | 3093.472 | 1031139328 | 160568818 |
| 15m | Replication | 35040 | 175200 | 840960 | 3327.131 | 1058217984 | 165742687 |
| 4h | Development | 2162 | 10810 | 51888 | 209.783 | 209268736 | 63245670 |
| 4h | Replication | 2190 | 10950 | 52560 | 68.858 | 231477248 | 64176096 |
| 1d | Development | 361 | 1805 | 8664 | 163.237 | 140918784 | 62258868 |
| 1d | Replication | 365 | 1825 | 8760 | 83.627 | 145612800 | 63008720 |

Each pass includes initialization, native price maps, daily state/membership serialization, candidate catalog and separately stored outcomes. Flow, crossings and statistics run separately and are excluded from these price-pass numbers. Concurrent machine load differs between runs. Small native clocks incur substantial per-file Parquet metadata overhead under the preserved daily partition layout; storage is not proportional to row count.

Source manifests: `data/phase4/<timeframe>/<period>/price-complete.json`.

## Trade Acquisition and Independent Parity

- Development flow history: 555,554,786 aggregate trades emitted for the required 2022 interval and initial two-hour flow history.
- Previously inspected 2023 replication: 406,537,376 aggregate trades.
- Total emitted: 962,092,162 aggregate trades, stored as exact observed-price quarter-hour profiles without duplicate raw archives.
- Original monthly archives are reused, except for already-adjudicated official daily collections such as August 2022. Official checksums/CRC, source hashes and the original coverage policy remain linked in the manifests.
- Independent reaggregation of all 24 months compared 56,933,078 exact hour/price rows against the pre-existing verified hourly trade profiles. Price indexes matched exactly. Quantity, aggressive buy and aggressive sell passed rtol=1e-10 / atol=1e-8; the observed maximum absolute difference was 4.547473508864641e-13.
- The partial first development hour is excluded only from the independent hourly parity comparison because its full hour is outside the emitted flow-history range. Native 15m research still starts at its declared eligible timestamp.
- Three empty development quarter-hours were corroborated by official zero-volume/zero-trade-count candles. They remain unavailable flow observations, not imputed zero volume. Replication had no empty observed quarter-hours. Existing quarantine intervals remain separately enforced.

Evidence: `data/phase4/profile-parity-full-months.json`, `profile-coverage-development.json`, `profile-coverage-replication.json`, and individual trade-profile manifests.

No 2024 market data, confluence performance, score summation, parameter selection or trading rules were used. This appendix makes no edge claim.
