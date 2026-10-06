# Authoritative Data Coverage

Earliest available REST BTCUSDT USD-M 1h candle: **2019-09-08 17:00 UTC**.
REST was queried from 2019-01-01, not inferred from a launch announcement.
Monthly archives start 2020-01; daily archives include 2019-12-31. Exact REST
responses and local SHA-256 are retained. REST has no official publisher checksum;
the overlapping December 31 official checksum/CRC archive matches exactly.
All hourly sequence/OHLC validation passed. No candle gaps are interpolated.

First exact 850-day price history: **2022-01-05 17:00 UTC**.
2021 is unavailable for this strategy definition; only the 8,647 eligible 2022
timestamps are development observations. Earlier 2019/2020 candles are history,
not performance observations. Zero-volume authoritative candles are not silently
removed from the regular hourly clock. 2023 is already-inspected replication.

Earliest authoritative aggregate archive: **2019-12-31**, first trade timestamp
2019-12-31T00:00:02.288000+00:00.
The historical aggregate REST probe was rejected by Binance's recent-history
restriction; it cannot establish earlier trade coverage. First possible 850-day
archived-trade window is **2022-04-29 00:00 UTC**, but known quarantines make it
incomplete in observable coverage. There are **zero** complete-coverage D windows
before 2024. No earlier clean trade history is assumed.

Additional selected aggregate rows: 117,925,990. April and May 2020 monthly files
omit dates despite valid checksum/CRC, so complete daily publications were used.
Daily/monthly evidence and official 1m volume checks follow unchanged coverage-v4.
New quarantine: 2020-04-15 11:37-11:38 UTC (one minute); original quarantines remain.
Do not confuse complete archive publication coverage with recovered missing trades.

Evidence: `data/phase3r1/history/discovery/`, `history/raw/`, `history/integrity/`,
`history/coverage/`, `history/trade-coverage.json`, `coverage-final.json`.
Raw and normalized/derived data are separate. No 2024 archive request or market
file is used. 2023 outcome generation is gated behind completed development analysis.
