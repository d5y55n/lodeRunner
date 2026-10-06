# Validation Volume Ablation

Validation-only descriptive results. Overlapping zones/configurations/horizons are dependent. No edge, significance, optimal-parameter or live-trading claim. No 2024 data used.

| detector | status | interactions |
| --- | --- | --- |
| A | AVAILABLE | 243358 |
| B | QUARANTINED_TRADE_COVERAGE | 820 |
| C | QUARANTINED_TRADE_COVERAGE | 1283 |
| D | QUARANTINED_TRADE_COVERAGE | 1853 |
| A | QUARANTINED_TRADE_COVERAGE | 596 |
| B | AVAILABLE | 343339 |
| C | AVAILABLE | 588458 |
| D | AVAILABLE | 819911 |

Quarantined overlapping current/baseline windows are MISSING, not zero. A/B/C price interactions remain in S/R-only tables. Full-development quantiles describe development retrospectively and are frozen for future validation. They are not online-available thresholds during their own fit period.

A, original 1h width, LONG, TP=SL=0.003, horizon=8 display slice:

| table | bucket | unique_event_count | measurement_count | tp_first_rate | sl_first_rate | ambiguous_rate | event_balanced_tp_first_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sr_only | ALL | 8571 | 243954 | 0.424512 | 0.418473 | 0.129301 | 0.437763 |
| relative_zone_volume_bucket | MISSING | 5881 | 103806 | 0.402983 | 0.404449 | 0.168879 | 0.427769 |
| relative_zone_volume_bucket | Q1 | 5721 | 39002 | 0.452912 | 0.427578 | 0.0942273 | 0.442947 |
| relative_zone_volume_bucket | Q2 | 4519 | 31822 | 0.426909 | 0.450659 | 0.0888987 | 0.440284 |
| relative_zone_volume_bucket | Q3 | 4444 | 30184 | 0.445509 | 0.425113 | 0.0904418 | 0.439513 |
| relative_zone_volume_bucket | Q4 | 5275 | 39140 | 0.435177 | 0.415316 | 0.12208 | 0.43456 |
| volume_delta_bucket | MISSING | 4 | 596 | 0.251678 | 0.748322 | 0 | 0.25 |
| volume_delta_bucket | Q1 | 4943 | 78196 | 0.407741 | 0.412116 | 0.162641 | 0.433313 |
| volume_delta_bucket | Q2 | 6718 | 42278 | 0.443575 | 0.422835 | 0.0833156 | 0.435936 |
| volume_delta_bucket | Q3 | 6752 | 43852 | 0.454369 | 0.418184 | 0.077213 | 0.442402 |
| volume_delta_bucket | Q4 | 4929 | 79032 | 0.415687 | 0.420104 | 0.150707 | 0.439099 |
