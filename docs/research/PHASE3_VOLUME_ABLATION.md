# Development Volume Ablation

Development-only descriptive results. Overlapping zones/configurations/horizons are dependent. No edge, significance, optimal-parameter or live-trading claim. No 2024 data used.

| detector | status | interactions |
| --- | --- | --- |
| A | QUARANTINED_TRADE_COVERAGE | 3913 |
| B | AVAILABLE | 6315325 |
| C | AVAILABLE | 15879416 |
| D | AVAILABLE | 37526814 |
| A | AVAILABLE | 4442228 |
| B | QUARANTINED_TRADE_COVERAGE | 5580 |
| C | QUARANTINED_TRADE_COVERAGE | 16232 |
| D | QUARANTINED_TRADE_COVERAGE | 40020 |

Quarantined overlapping current/baseline windows are MISSING, not zero. A/B/C price interactions remain in S/R-only tables. Full-development quantiles describe development retrospectively and are frozen for future validation. They are not online-available thresholds during their own fit period.

A, original 1h width, LONG, TP=SL=0.003, horizon=8 display slice:

| table | bucket | unique_event_count | measurement_count | tp_first_rate | sl_first_rate | ambiguous_rate | event_balanced_tp_first_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sr_only | ALL | 17340 | 739059 | 0.332419 | 0.326823 | 0.337869 | 0.343103 |
| relative_zone_volume_bucket | MISSING | 13290 | 311318 | 0.320759 | 0.304536 | 0.372154 | 0.340986 |
| relative_zone_volume_bucket | Q1 | 13292 | 115334 | 0.343741 | 0.352448 | 0.301296 | 0.34688 |
| relative_zone_volume_bucket | Q2 | 9799 | 95357 | 0.341603 | 0.347048 | 0.307551 | 0.34242 |
| relative_zone_volume_bucket | Q3 | 9848 | 95801 | 0.330776 | 0.3411 | 0.324585 | 0.342712 |
| relative_zone_volume_bucket | Q4 | 12668 | 121249 | 0.345669 | 0.332495 | 0.318957 | 0.341914 |
| volume_delta_bucket | MISSING | 6 | 644 | 0 | 0.122671 | 0.877329 | 0 |
| volume_delta_bucket | Q1 | 11111 | 229779 | 0.314591 | 0.305306 | 0.377965 | 0.330782 |
| volume_delta_bucket | Q2 | 15072 | 141611 | 0.346392 | 0.35438 | 0.295273 | 0.344969 |
| volume_delta_bucket | Q3 | 15437 | 143579 | 0.354987 | 0.352555 | 0.288374 | 0.347742 |
| volume_delta_bucket | Q4 | 11227 | 223446 | 0.328357 | 0.315543 | 0.353876 | 0.337313 |
