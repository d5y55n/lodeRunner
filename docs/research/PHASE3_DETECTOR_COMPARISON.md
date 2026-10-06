# Development Detector Comparison

Development-only descriptive results. Overlapping zones/configurations/horizons are dependent. No edge, significance, optimal-parameter or live-trading claim. No 2024 data used.

| detector | interaction_count | unique_events | candidates | unique_candidates |
| --- | --- | --- | --- | --- |
| A | 4446141 | 17413 | 9201 | 9201 |
| B | 6320905 | 17427 | 13252 | 13252 |
| C | 15895648 | 17462 | 30624 | 30624 |
| D | 37566834 | 17514 | 62476 | 62476 |

## Predeclared Display Slice

Original 1h half-width 0.004, LONG, TP=SL=0.003, horizon=8 candles. This display slice is not a selected winner. All configured widths/directions/TP/SL/horizons remain in research_summary.csv.

| configuration | unique_event_count | measurement_count | tp_first_rate | sl_first_rate | ambiguous_rate | censored_rate | event_balanced_tp_first_rate | mfe_pct_median | mae_pct_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A {} | 17340 | 739059 | 0.332419 | 0.326823 | 0.337869 | 0.000205667 | 0.343103 | 1.12551 | 1.17123 |
| B {"width": 1} | 17346 | 658457 | 0.331603 | 0.326009 | 0.339519 | 0.000185282 | 0.342638 | 1.12571 | 1.18016 |
| B {"width": 2} | 17172 | 395498 | 0.331838 | 0.326722 | 0.338529 | 0.000192163 | 0.343257 | 1.12252 | 1.17764 |
| C {"reversal_fraction": 0.003} | 17440 | 1411692 | 0.328061 | 0.321989 | 0.347967 | 0.000151591 | 0.342167 | 1.14651 | 1.1985 |
| C {"reversal_fraction": 0.005} | 17431 | 1238571 | 0.324527 | 0.317931 | 0.356112 | 0.000100115 | 0.342172 | 1.17141 | 1.2179 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 17358 | 3996002 | 0.315245 | 0.306634 | 0.377409 | 6.3063e-05 | 0.341094 | 1.23043 | 1.26792 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 16930 | 2243371 | 0.317323 | 0.308458 | 0.373286 | 4.0564e-05 | 0.338828 | 1.2176 | 1.25757 |

## Detector D

Bin width is independent of zone width; occupied-bin mean multiplier remains 1.5.

| bin_width | candidates | mean_concentration | median_concentration |
| --- | --- | --- | --- |
| 100 | 22796 | 1.95171 | 1.85584 |
| 50 | 39680 | 1.97386 | 1.86021 |
