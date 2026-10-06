# Phase 4 Data Coverage

| timeframe | phase | earliest_850_day_decision_UTC | decision_timestamps | map_states | complete_contiguous |
| --- | --- | --- | --- | --- | --- |
| 15m | development | 2022-01-05T17:45:00+00:00 | 34585 | 172925 | True |
| 15m | replication | 2022-01-05T17:45:00+00:00 | 35040 | 175200 | True |
| 4h | development | 2022-01-05T16:00:00+00:00 | 2162 | 10810 | True |
| 4h | replication | 2022-01-05T16:00:00+00:00 | 2190 | 10950 | True |
| 1d | development | 2022-01-05T00:00:00+00:00 | 361 | 1805 | True |
| 1d | replication | 2022-01-05T00:00:00+00:00 | 365 | 1825 | True |

Native exchange alignment determines the first eligible decision; no shortened 850-day fallback. Official candle SHA/CRC and complete-continuity evidence are in each coverage manifest. Exact aggregate-trade profiles retain existing quarantine decisions and source hashes. August 2022 uses the previously adjudicated official daily collection, not the rejected monthly publication.

## Empty Observed Intervals
| phase | classification | end | official_close | official_kline_quantity | official_kline_trade_count | official_open | start | treatment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | OFFICIAL_ZERO_ACTIVITY_CORROBORATED | 1651445100000 | 38275 | 0 | 0 | 38275 | 1651444200000 | No quantity imputation; overlapping flow windows unavailable; price states retained |
| development | OFFICIAL_ZERO_ACTIVITY_CORROBORATED | 1653757200000 | 28999 | 0 | 0 | 28999 | 1653756300000 | No quantity imputation; overlapping flow windows unavailable; price states retained |
| development | OFFICIAL_ZERO_ACTIVITY_CORROBORATED | 1653758100000 | 28999 | 0 | 0 | 28999 | 1653757200000 | No quantity imputation; overlapping flow windows unavailable; price states retained |

Official zero-activity candles are corroborating evidence only, not replacement trade volume. No price states are selectively excluded and no empty profile is zero-filled.

2023 is the **previously inspected replication period**, not an untouched final test. No 2024 market data, confluence performance, score summation, parameter ranking, or trading rule is used. All findings are descriptive, with overlapping outcomes and unadjusted multiple comparisons; no edge claim.
