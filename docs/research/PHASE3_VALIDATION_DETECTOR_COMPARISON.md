# Validation Detector Comparison

Validation-only descriptive results. Overlapping zones/configurations/horizons are dependent. No edge, significance, optimal-parameter or live-trading claim. No 2024 data used.

| detector | interaction_count | unique_events | candidates | unique_candidates |
| --- | --- | --- | --- | --- |
| D | 821764 | 8582 | 15095 | 15095 |
| A | 243954 | 8571 | 4725 | 4725 |
| B | 344159 | 8573 | 6755 | 6755 |
| C | 589741 | 8623 | 11081 | 11081 |

## Predeclared Display Slice

Original 1h half-width 0.004, LONG, TP=SL=0.003, horizon=8 candles. This display slice is not a selected winner. All configured widths/directions/TP/SL/horizons remain in research_summary.csv.

| configuration | unique_event_count | measurement_count | tp_first_rate | sl_first_rate | ambiguous_rate | censored_rate | event_balanced_tp_first_rate | mfe_pct_median | mae_pct_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A {} | 8571 | 243954 | 0.424512 | 0.418473 | 0.129301 | 0.000873115 | 0.437763 | 0.621334 | 0.598105 |
| B {"width": 1} | 8548 | 216450 | 0.425432 | 0.417483 | 0.130492 | 0.000887041 | 0.437302 | 0.625262 | 0.602715 |
| B {"width": 2} | 8343 | 127709 | 0.427339 | 0.4164 | 0.13081 | 0.000696897 | 0.43786 | 0.62433 | 0.610507 |
| C {"reversal_fraction": 0.003} | 8623 | 348783 | 0.424374 | 0.417296 | 0.13457 | 0.000974818 | 0.43779 | 0.63445 | 0.620863 |
| C {"reversal_fraction": 0.005} | 8519 | 240958 | 0.423285 | 0.416954 | 0.138498 | 0.00105828 | 0.43703 | 0.639399 | 0.634193 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 8457 | 508009 | 0.421349 | 0.419246 | 0.135824 | 0.00113974 | 0.439408 | 0.63516 | 0.634194 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 7877 | 313755 | 0.423135 | 0.416677 | 0.133903 | 0.00111233 | 0.438374 | 0.635995 | 0.62062 |

## Detector D

Bin width is independent of zone width; occupied-bin mean multiplier remains 1.5.

| bin_width | candidates | mean_concentration | median_concentration |
| --- | --- | --- | --- |
| 100 | 5800 | 1.91313 | 1.83828 |
| 50 | 9295 | 1.93794 | 1.85212 |
