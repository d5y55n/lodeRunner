# Phase 4 Progress (Complete)

Final status: COMPLETE. The finite pipeline stopped at `STOP_NO_CONFLUENCE`.
See `PHASE4_COMPLETION.md` and `data/phase4/completion.json` for acceptance evidence.

## Boundaries

- BTCUSDT USD-M Futures only. No 2024 market data is requested or read.
- Existing 1h engines and Phase 3R / 3R.1 / 3R.2 outputs are not rewritten.
- Native closed-candle clocks and the complete 850-calendar-day lookback are retained.
- Development precedes a reviewed configuration/bucket freeze; 2023 remains the previously inspected replication period.
- No confluence evaluation, cross-timeframe score sum, trading rule, threshold optimization, or edge claim.

## Verified Gates

All three new native clocks passed 120 real-data A/B/C parity comparisons each and five physically truncated-input comparisons each.

15m benchmark: 1,000 consecutive decision timestamps, 5,000 map states, 118.82 seconds for state generation/serialization, 945,463,296 peak process-memory bytes, 3,079,875 output bytes. Projection for development plus replication: approximately 8,273 seconds and 214 MB of compact state/membership data. This excludes outcome generation, flow attachments, crossings, analysis, acquisition, and concurrent-work overhead. It is not a completion ETA.

## Authoritative Candle Coverage

| Timeframe | First complete 850-day decision (UTC) | Development status |
| --- | --- | --- |
| 15m | 2022-01-05 17:45 | 34,585 decision timestamps, 172,925 map states generated |
| 4h | 2022-01-05 16:00 | 2,162 decision timestamps, 10,810 map states generated |
| 1d | 2022-01-05 00:00 | 361 decision timestamps, 1,805 map states generated |

2019 REST history is independently overlapped with an official daily archive; 2020-2022 official monthly archives have checksum, CRC, native-grid and continuity checks. Coverage manifests are under `data/phase4/candles/<timeframe>/development-coverage.json`.

Daily outcome horizons are 24/48/72 hours on native daily bars. They are structural/context measurements, not intraday entry timing. 15m and 4h horizons are 4/8/24 elapsed hours. Native OHLC ambiguity and end-of-period censoring remain explicit.

## Exact 15m Trade Profiles

The user approved building new quarter-hour profiles from existing original aggregate-trade archives, without splitting hourly profiles. The implementation streams raw chunks and publishes daily Parquet partitions, retaining exact observed float64 prices, total quantity, aggressive buy, aggressive sell, and raw Delta. Buyer-is-maker means aggressive sell.

Only the development evaluation interval and its preceding two-hour flow history are emitted initially, beginning 2022-01-05 15:45 UTC. Raw monthly files may be scanned outside this interval for original-integrity checks but are not duplicated or emitted as extra profile history. The 2023 build is gated behind the development freeze.

The deterministic sample gate passed on 493,608 actual trades in 48 complete quarter-hour intervals: direct quantity parity, buy/sell interpretation, chunk invariance, hourly reaggregation parity, and future exclusion. Official source hashes are matched to the existing outcome-blind forensic coverage manifest. Entire-file CRC is verified at full-build EOF. ID gaps alone do not trigger new exclusions. Quarantines stay in provenance and cannot become usable flow observations; absent intervals stay missing, not zero.

Outputs: `data/phase4/trade-profiles-15m/YYYY-MM/YYYY-MM-DD.parquet`. A month is consumable only after its completed manifest is written. `progress.json` records source rows, selected rows, and completed partitions. The reader supports causal 1/4/8-native-candle windows.

## Completed Execution

All development price maps, causal crossing/visit passes, twelve 2022 quarter-hour trade-profile months, flow attachments, expanded descriptive analyses and development reviews are complete. The 15m attachment has 518,775 flow rows and 172,925 crossing/visit feature rows. Numerically equivalent shared-window/prefix caches passed 375 real-data parity comparisons.

The global development freeze has completed. Per-timeframe immutable contracts are at `data/phase4/<timeframe>/development-freeze.json`; their verified IDs are:

- 15m: `5ca2c971b6ea21c5591e3de29cb16109d5737170ebd075af7adb18d5efc7b7d3`
- 4h: `26cdac11436c004344abbbe9d97ffc9a80c98fb0050f4c3c8e7cef95a66f1bc4`
- 1d: `91933c1439be2377a1417d22cac5dfc41b8ad1de623f64449832cacf6c8d20c5`

Only after this freeze, 2023 native candles and all twelve exact quarter-hour trade-profile months were completed. The 2023 empty-interval audit passed without empty intervals. All three replication price maps, contact features, flow attachments and statistical analyses are complete. Frozen research settings were preserved throughout replication.

An independent, read-only 24-month cross-check reaggregated 15m profiles to the previously verified exact-price hourly profiles: 56,933,078 hour/price rows passed, with maximum quantity/buy/sell absolute difference 4.547473508864641e-13. Evidence: `data/phase4/profile-parity-full-months.json`. This audit did not change frozen research code or parameters.

On October 1, the prior process was found absent despite a stale RUNNING record. Completed stage manifests were reused. The finite pipeline was resumed in a separate hidden Windows process and completed, with host output/error logs at `data/phase4/logs/persistent-pipeline.stdout.log` and `persistent-pipeline.stderr.log`. No recurring automation was created.

The 2022 emitted profile range contains 555,554,786 selected aggregate trades. Three empty observed 15-minute intervals occur on May 1 at 22:30 UTC and May 28 at 16:45/17:00 UTC. Official native candles independently report zero quantity, trade count and taker quantity in all three. They remain explicit unavailable flow intervals, without imputation or exclusion of price states. Evidence is in `data/phase4/profile-coverage-development.json`. Existing quarantines remain unchanged.

The previously frozen artifacts passed a 17,758-file preservation audit. The final full suite passed 294 tests with zero failures, errors or skips; one existing Starlette/httpx deprecation warning remains. See `data/phase4/final-tests.json`. All eleven completion-manifest report hashes and all three frozen contracts were independently rechecked successfully after report generation.

The finite continuation command was `.venv/Scripts/python.exe -m app.multimap.finish` from backend. Its final completion state is in `data/phase4/pipeline-status.json`, with per-stage logs under `data/phase4/logs`. It performed development review/freeze before any 2023 acquisition, verified 2023 empty-profile coverage before price outcomes, then completed replication, preservation audit, the whole suite and the ten requested reports. There is no recurring task, automatic strategy selection, or confluence run.

Completed acceptance deliverables:

1. Exact observed trade profiles for development and 2023: 962,092,162 selected aggregate trades, with outcome-blind coverage checks and independent hourly parity.
2. Native price maps, contact features, flow attachments and frozen-bucket analyses: 373,515 map states across 74,703 native decision timestamps and 1,792,872 outcome rows.
3. Final preservation audit, full suite, causal alignment checks including the frozen 1h reference, ten requested reports and the supplementary execution audit.

The intermediate normalized price-stage table deliberately carries `PENDING_SEPARATE_TRADE_ATTACHMENT`, not fabricated zero quantities. Use the completed `normalized-with-flow` tables and final report exports for attached volume features. No 2024 data, confluence evaluation, optimization or trading rules were used. Phase 4 is complete; no further research phase was started.
