# Development Baseline Comparison

Development-only descriptive results. Overlapping zones/configurations/horizons are dependent. No edge, significance, optimal-parameter or live-trading claim. No 2024 data used.

Schedule: every fourth closed candle. Matcher: January 2021 context quantiles, only earlier controls whose full horizon has elapsed at target time. No matching before February 2021. Matching never sees outcomes. Control reuse is not independence.

## Schedule Display Slice

| unique_event_count | measurement_count | tp_first_rate | sl_first_rate | ambiguous_rate |
| --- | --- | --- | --- | --- |
| 4380 | 4380 | 0.340795 | 0.356099 | 0.297396 |

## Matched Controls (Same Display Slice)

Unique events below count reused CONTROL events; matched_target_count separately counts target events.

| configuration | unique_event_count | measurement_count | tp_first_rate | event_balanced_tp_first_rate | matched_target_count | eligible_target_count |
| --- | --- | --- | --- | --- | --- | --- |
| A {} | 10396 | 16622 | 0.348394 | 0.357157 | 16622 | 17318 |
| A {} | 10399 | 16624 | 0.348292 | 0.357054 | 16624 | 17319 |
| A {} | 10404 | 16639 | 0.348338 | 0.357363 | 16639 | 17333 |
| A {} | 10398 | 16638 | 0.348299 | 0.35728 | 16638 | 17331 |
| A {} | 10405 | 16652 | 0.348307 | 0.357328 | 16652 | 17352 |
| A {} | 10402 | 16641 | 0.348477 | 0.357335 | 16641 | 17340 |
| B {"width": 1} | 10382 | 16623 | 0.348433 | 0.357349 | 16623 | 17327 |
| B {"width": 1} | 10383 | 16625 | 0.348692 | 0.357604 | 16625 | 17325 |
| B {"width": 1} | 10389 | 16640 | 0.348498 | 0.357686 | 16640 | 17341 |
| B {"width": 1} | 10400 | 16645 | 0.348333 | 0.357404 | 16645 | 17348 |
| B {"width": 1} | 10395 | 16650 | 0.348529 | 0.357768 | 16650 | 17356 |
| B {"width": 1} | 10396 | 16642 | 0.348396 | 0.357541 | 16642 | 17346 |
| B {"width": 2} | 10322 | 16505 | 0.349046 | 0.357101 | 16505 | 17159 |
| B {"width": 2} | 10315 | 16494 | 0.3494 | 0.357635 | 16494 | 17146 |
| B {"width": 2} | 10322 | 16497 | 0.349094 | 0.357586 | 16497 | 17147 |
| B {"width": 2} | 10328 | 16501 | 0.348767 | 0.357281 | 16501 | 17153 |
| B {"width": 2} | 10331 | 16518 | 0.349013 | 0.357565 | 16518 | 17170 |
| B {"width": 2} | 10341 | 16517 | 0.349095 | 0.357606 | 16517 | 17172 |
| C {"reversal_fraction": 0.003} | 10423 | 16702 | 0.347922 | 0.357095 | 16702 | 17422 |
| C {"reversal_fraction": 0.003} | 10428 | 16707 | 0.347878 | 0.356924 | 16707 | 17426 |
| C {"reversal_fraction": 0.003} | 10426 | 16708 | 0.347917 | 0.35728 | 16708 | 17429 |
| C {"reversal_fraction": 0.003} | 10431 | 16710 | 0.347935 | 0.357204 | 16710 | 17431 |
| C {"reversal_fraction": 0.003} | 10426 | 16715 | 0.348071 | 0.357376 | 16715 | 17438 |
| C {"reversal_fraction": 0.003} | 10432 | 16718 | 0.347948 | 0.35717 | 16718 | 17440 |
| C {"reversal_fraction": 0.005} | 10422 | 16698 | 0.347946 | 0.357129 | 16698 | 17413 |
| C {"reversal_fraction": 0.005} | 10427 | 16701 | 0.347883 | 0.356958 | 16701 | 17415 |
| C {"reversal_fraction": 0.005} | 10422 | 16702 | 0.347982 | 0.357321 | 16702 | 17417 |
| C {"reversal_fraction": 0.005} | 10430 | 16707 | 0.347938 | 0.357143 | 16707 | 17423 |
| C {"reversal_fraction": 0.005} | 10425 | 16711 | 0.348094 | 0.35741 | 16711 | 17432 |
| C {"reversal_fraction": 0.005} | 10429 | 16713 | 0.347933 | 0.357081 | 16713 | 17431 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 10291 | 16578 | 0.346845 | 0.356622 | 16578 | 17319 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 10303 | 16593 | 0.347134 | 0.356886 | 16593 | 17334 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 10315 | 16604 | 0.347446 | 0.357731 | 16604 | 17345 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 10350 | 16655 | 0.347463 | 0.357488 | 16655 | 17396 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 10322 | 16614 | 0.347538 | 0.357586 | 16614 | 17355 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 10321 | 16617 | 0.346814 | 0.356651 | 16617 | 17358 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 9927 | 16069 | 0.34439 | 0.353581 | 16069 | 16806 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 9971 | 16137 | 0.345355 | 0.355631 | 16137 | 16877 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 9998 | 16177 | 0.345676 | 0.356071 | 16177 | 16916 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 10015 | 16194 | 0.34661 | 0.356565 | 16194 | 16934 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 10029 | 16225 | 0.344777 | 0.354273 | 16225 | 16965 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 10010 | 16190 | 0.345213 | 0.354845 | 16190 | 16930 |

## Matched Targets Only

Compare controls with this matched target subset, not unmatched S/R rows.

| configuration | unique_event_count | measurement_count | tp_first_rate | event_balanced_tp_first_rate |
| --- | --- | --- | --- | --- |
| A {} | 16622 | 16622 | 0.350587 | 0.350587 |
| A {} | 16624 | 16624 | 0.350424 | 0.350424 |
| A {} | 16639 | 16639 | 0.350289 | 0.350289 |
| A {} | 16638 | 16638 | 0.349769 | 0.349769 |
| A {} | 16652 | 16652 | 0.349715 | 0.349715 |
| A {} | 16641 | 16641 | 0.349946 | 0.349946 |
| B {"width": 1} | 16623 | 16623 | 0.350084 | 0.350084 |
| B {"width": 1} | 16625 | 16625 | 0.350162 | 0.350162 |
| B {"width": 1} | 16640 | 16640 | 0.349726 | 0.349726 |
| B {"width": 1} | 16645 | 16645 | 0.349561 | 0.349561 |
| B {"width": 1} | 16650 | 16650 | 0.349576 | 0.349576 |
| B {"width": 1} | 16642 | 16642 | 0.349564 | 0.349564 |
| B {"width": 2} | 16505 | 16505 | 0.350406 | 0.350406 |
| B {"width": 2} | 16494 | 16494 | 0.350337 | 0.350337 |
| B {"width": 2} | 16497 | 16497 | 0.350455 | 0.350455 |
| B {"width": 2} | 16501 | 16501 | 0.350127 | 0.350127 |
| B {"width": 2} | 16518 | 16518 | 0.349827 | 0.349827 |
| B {"width": 2} | 16517 | 16517 | 0.349909 | 0.349909 |
| C {"reversal_fraction": 0.003} | 16702 | 16702 | 0.349805 | 0.349805 |
| C {"reversal_fraction": 0.003} | 16707 | 16707 | 0.349701 | 0.349701 |
| C {"reversal_fraction": 0.003} | 16708 | 16708 | 0.3495 | 0.3495 |
| C {"reversal_fraction": 0.003} | 16710 | 16710 | 0.349518 | 0.349518 |
| C {"reversal_fraction": 0.003} | 16715 | 16715 | 0.349294 | 0.349294 |
| C {"reversal_fraction": 0.003} | 16718 | 16718 | 0.349231 | 0.349231 |
| C {"reversal_fraction": 0.005} | 16698 | 16698 | 0.349769 | 0.349769 |
| C {"reversal_fraction": 0.005} | 16701 | 16701 | 0.349647 | 0.349647 |
| C {"reversal_fraction": 0.005} | 16702 | 16702 | 0.349446 | 0.349446 |
| C {"reversal_fraction": 0.005} | 16707 | 16707 | 0.349581 | 0.349581 |
| C {"reversal_fraction": 0.005} | 16711 | 16711 | 0.349377 | 0.349377 |
| C {"reversal_fraction": 0.005} | 16713 | 16713 | 0.349216 | 0.349216 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 16578 | 16578 | 0.347915 | 0.347915 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 16593 | 16593 | 0.348204 | 0.348204 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 16604 | 16604 | 0.348214 | 0.348214 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 16655 | 16655 | 0.348568 | 0.348568 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 16614 | 16614 | 0.348064 | 0.348064 |
| D {"bin_size": 50, "concentration_multiple": 1.5} | 16617 | 16617 | 0.348182 | 0.348182 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 16069 | 16069 | 0.345531 | 0.345531 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 16137 | 16137 | 0.345875 | 0.345875 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 16177 | 16177 | 0.346071 | 0.346071 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 16194 | 16194 | 0.34651 | 0.34651 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 16225 | 16225 | 0.347081 | 0.347081 |
| D {"bin_size": 100, "concentration_multiple": 1.5} | 16190 | 16190 | 0.345978 | 0.345978 |
