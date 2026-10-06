# Raw Delta and Legacy Boundaries

The same legacy boundaries are retained in both periods: [-252.39299999999594, -5.96999999999764, 214.41500000002725]. They were pooled across detectors/full development in Phase 3, not fitted on 2023 and not interpretable as a stable online percentile during development. Values below are row-weighted descriptive distributions, not selected thresholds. Zero quantity makes normalized delta undefined.

| phase | legacy_quartile | measurement_rows | unique_events | raw_delta_min | raw_delta_median | raw_delta_max | normalized_delta_median | quantity_median | zero_quantity_fraction | negative_delta_fraction | positive_delta_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | 1 | 229779 | 11111 | -8173.64 | -690.743 | -252.4 | -0.122317 | 6664 | 0 | 1 | 0 |
| development | 2 | 141611 | 15072 | -252.391 | -100.81 | -5.97 | -0.111713 | 930.574 | 0 | 1 | 0 |
| development | 3 | 143579 | 15437 | -5.969 | 73.325 | 214.413 | 0.0930598 | 679.589 | 0 | 0.0577382 | 0.942262 |
| development | 4 | 223446 | 11227 | 214.422 | 629.849 | 8786.01 | 0.117062 | 6314.05 | 0 | 0 | 1 |
| replication | 1 | 78196 | 4943 | -8640.64 | -860.652 | -252.401 | -0.135599 | 7303.02 | 0 | 1 | 0 |
| replication | 2 | 42278 | 6718 | -252.384 | -94.671 | -5.97 | -0.122201 | 777.281 | 0 | 1 | 0 |
| replication | 3 | 43852 | 6752 | -5.968 | 67.368 | 214.41 | 0.0917688 | 626.405 | 0 | 0.0639652 | 0.936035 |
| replication | 4 | 79032 | 4929 | 214.445 | 763.259 | 8536.77 | 0.127766 | 6993.06 | 0 | 0 | 1 |

All widths and separated types: data/phase35/raw-delta-distribution.csv.
