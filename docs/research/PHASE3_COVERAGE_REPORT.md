# Outcome-Blind Coverage Report

Active policy: coverage-v4. Coverage ID: f0638681b19ff0ecac4f6167bbdd75d0d460f59edf077649a5b147f58d425e80. All decisions precede research outcomes. No reconstructed trades.

## Selected-Source ID Discontinuities

| utc_after | missing_ID_numbers | timestamp_gap_seconds | price_change_fraction | publications_agree | decision |
| --- | --- | --- | --- | --- | --- |
| 2021-02-09T05:35:35.345000+00:00 | 22785 | 1626.88 | -2.14798e-05 | True | PARTIAL_MINUTE_QUARANTINE |
| 2021-02-09T09:39:35.972000+00:00 | 8 | 0.645 | 9.19042e-05 | True | RETAIN_WARNING |
| 2021-02-24T06:28:55.219000+00:00 | 13 | 0.473 | 0.000167664 | True | PARTIAL_MINUTE_QUARANTINE |
| 2021-05-19T13:40:10.709000+00:00 | 557026 | 1476.71 | 0.109394 | True | PARTIAL_MINUTE_QUARANTINE |
| 2022-09-06T17:20:57.627000+00:00 | 31645 | 381.024 | -0.000996759 | True | PARTIAL_MINUTE_QUARANTINE |
| 2022-09-06T17:58:10.719000+00:00 | 11 | 0.899 | 0 | True | RETAIN_WARNING |

## Rejected Monthly Publications

| month | monthly_rows | selected_daily_rows | monthly_duplicate_rows | unresolved_minutes |
| --- | --- | --- | --- | --- |
| 2022-08 | 40556504 | 44534075 | 0 | 0 |
| 2022-09 | 44223166 | 42362890 | 4316651 | 0 |
| 2022-10 | 27752738 | 28597576 | 0 | 0 |
| 2022-11 | 33974166 | 36885751 | 0 | 0 |
| 2023-05 | 35641068 | 36757013 | 0 | 0 |
| 2023-10 | 38272235 | 38272235 | 0 | 0 |

## Minute-Level Trade-Volume Quarantine

| start_utc | end_utc_exclusive | minutes |
| --- | --- | --- |
| 2021-02-09T05:08:00+00:00 | 2021-02-09T05:36:00+00:00 | 28 |
| 2021-02-24T06:28:00+00:00 | 2021-02-24T06:29:00+00:00 | 1 |
| 2021-05-19T13:15:00+00:00 | 2021-05-19T13:41:00+00:00 | 26 |
| 2022-09-06T17:14:00+00:00 | 2022-09-06T17:21:00+00:00 | 7 |
| 2023-10-05T17:04:00+00:00 | 2023-10-05T17:05:00+00:00 | 1 |
| 2023-10-23T00:06:00+00:00 | 2023-10-23T00:07:00+00:00 | 1 |

A/B/C verified candle history is retained. D formation windows intersecting these intervals are omitted; overlapping current/baseline zone-volume features are unavailable, not zero. Price/time jumps alone never trigger exclusion. Boundary conservation warnings do not shift timestamps or volume. Daily/monthly sources are not independent observations of execution. See the versioned policy and raw forensic evidence for assumptions and amendments.
