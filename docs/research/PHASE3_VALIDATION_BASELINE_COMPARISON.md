# Validation Baseline Comparison

Validation-only descriptive results. Overlapping zones/configurations/horizons are dependent. No edge, significance, optimal-parameter or live-trading claim. No 2024 data used.

Schedule: every fourth closed candle. Matcher: January 2021 context quantiles, only earlier controls whose full horizon has elapsed at target time. No matching before February 2021. Matching never sees outcomes. Control reuse is not independence.

## Schedule Display Slice

| unique_event_count | measurement_count | tp_first_rate | sl_first_rate | ambiguous_rate |
| --- | --- | --- | --- | --- |
| 2190 | 2190 | 0.42596 | 0.443327 | 0.0850091 |

## Matched Controls (Same Display Slice)

Unique events below count reused CONTROL events; matched_target_count separately counts target events.

| configuration | unique_event_count | measurement_count | tp_first_rate | event_balanced_tp_first_rate | matched_target_count | eligible_target_count |
| --- | --- | --- | --- | --- | --- | --- |
| A {} | 6124 | 8500 | 0.429882 | 0.423743 | 8500 | 8571 |
| B {"width": 1} | 6109 | 8480 | 0.429717 | 0.423801 | 8480 | 8548 |
| B {"width": 2} | 5986 | 8280 | 0.429106 | 0.423989 | 8280 | 8343 |
| C {"reversal_fraction": 0.003} | 6153 | 8561 | 0.430324 | 0.424833 | 8561 | 8623 |
| C {"reversal_fraction": 0.005} | 6089 | 8468 | 0.428436 | 0.423058 | 8468 | 8519 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 5997 | 8387 | 0.431501 | 0.428714 | 8387 | 8457 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 5579 | 7813 | 0.432868 | 0.429826 | 7813 | 7877 |

## Matched Targets Only

Compare controls with this matched target subset, not unmatched S/R rows.

| configuration | unique_event_count | measurement_count | tp_first_rate | event_balanced_tp_first_rate |
| --- | --- | --- | --- | --- |
| A {} | 8500 | 8500 | 0.438126 | 0.438126 |
| B {"width": 1} | 8480 | 8480 | 0.437389 | 0.437389 |
| B {"width": 2} | 8280 | 8280 | 0.437931 | 0.437931 |
| C {"reversal_fraction": 0.003} | 8561 | 8561 | 0.438041 | 0.438041 |
| C {"reversal_fraction": 0.005} | 8468 | 8468 | 0.437419 | 0.437419 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 8387 | 8387 | 0.439737 | 0.439737 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 7813 | 7813 | 0.438765 | 0.438765 |
