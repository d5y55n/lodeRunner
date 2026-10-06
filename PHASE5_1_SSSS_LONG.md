# SSSS / LONG at Current Price

Baseline 0=all eligible; 1=15m only condition; 2=15m+1h; 3=15m+1h+4h. Baselines are inclusive and nested, evaluated on one common 15m future path. Differences are SSSS minus baseline.

| phase | comparison | metric | grids | supported | minimum_effect | maximum_effect | positive | negative | CI_above_zero | CI_below_zero | minimum_A_complete | minimum_B_complete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | SSSS/vs_baseline_0 | AMBIGUOUS | 12 | 12 | 0.0027635 | 0.014946 | 12 | 0 | 0 | 0 | 4670 | 34490 |
| development | SSSS/vs_baseline_0 | NEITHER | 12 | 12 | -0.014364 | 0.0051176 | 1 | 11 | 0 | 1 | 4670 | 34490 |
| development | SSSS/vs_baseline_0 | SL_FIRST | 12 | 12 | -0.039553 | -0.014677 | 0 | 12 | 0 | 7 | 4670 | 34490 |
| development | SSSS/vs_baseline_0 | TP_FIRST | 12 | 12 | 0.013249 | 0.037602 | 12 | 0 | 2 | 0 | 4670 | 34490 |
| development | SSSS/vs_baseline_0 | mae_pct | 12 | 12 | 0.19558 | 0.48746 | 12 | 0 | 4 | 0 | 4670 | 34490 |
| development | SSSS/vs_baseline_0 | mfe_pct | 12 | 12 | 0.03489 | 0.047418 | 12 | 0 | 0 | 0 | 4670 | 34490 |
| development | SSSS/vs_baseline_1 | AMBIGUOUS | 12 | 12 | 0.0030016 | 0.0094734 | 12 | 0 | 0 | 0 | 4670 | 15499 |
| development | SSSS/vs_baseline_1 | NEITHER | 12 | 12 | -0.0023667 | 0.015567 | 7 | 5 | 0 | 0 | 4670 | 15499 |
| development | SSSS/vs_baseline_1 | SL_FIRST | 12 | 12 | -0.039064 | -0.025436 | 0 | 12 | 0 | 11 | 4670 | 15499 |
| development | SSSS/vs_baseline_1 | TP_FIRST | 12 | 12 | 0.0070551 | 0.038287 | 12 | 0 | 3 | 0 | 4670 | 15499 |
| development | SSSS/vs_baseline_1 | mae_pct | 12 | 12 | 0.12602 | 0.3778 | 12 | 0 | 0 | 0 | 4670 | 15499 |
| development | SSSS/vs_baseline_1 | mfe_pct | 12 | 12 | -0.046432 | 0.018512 | 4 | 8 | 0 | 0 | 4670 | 15499 |
| development | SSSS/vs_baseline_2 | AMBIGUOUS | 12 | 12 | 0.0022951 | 0.0061696 | 12 | 0 | 0 | 0 | 4670 | 10789 |
| development | SSSS/vs_baseline_2 | NEITHER | 12 | 12 | -0.0002493 | 0.018564 | 9 | 1 | 0 | 0 | 4670 | 10789 |
| development | SSSS/vs_baseline_2 | SL_FIRST | 12 | 12 | -0.033157 | -0.021702 | 0 | 12 | 0 | 8 | 4670 | 10789 |
| development | SSSS/vs_baseline_2 | TP_FIRST | 12 | 12 | 0.0039665 | 0.030658 | 12 | 0 | 2 | 0 | 4670 | 10789 |
| development | SSSS/vs_baseline_2 | mae_pct | 12 | 12 | 0.10627 | 0.34536 | 12 | 0 | 0 | 0 | 4670 | 10789 |
| development | SSSS/vs_baseline_2 | mfe_pct | 12 | 12 | -0.041101 | 0.012275 | 4 | 8 | 0 | 0 | 4670 | 10789 |
| development | SSSS/vs_baseline_3 | AMBIGUOUS | 12 | 12 | 0.002805 | 0.0079307 | 12 | 0 | 0 | 0 | 4670 | 8516 |
| development | SSSS/vs_baseline_3 | NEITHER | 12 | 12 | 0 | 0.012806 | 10 | 0 | 0 | 0 | 4670 | 8516 |
| development | SSSS/vs_baseline_3 | SL_FIRST | 12 | 12 | -0.029426 | -0.019173 | 0 | 12 | 0 | 11 | 4670 | 8516 |
| development | SSSS/vs_baseline_3 | TP_FIRST | 12 | 12 | 0.0031908 | 0.026159 | 12 | 0 | 2 | 0 | 4670 | 8516 |
| development | SSSS/vs_baseline_3 | mae_pct | 12 | 12 | 0.10147 | 0.31078 | 12 | 0 | 0 | 0 | 4670 | 8516 |
| development | SSSS/vs_baseline_3 | mfe_pct | 12 | 12 | 0.032678 | 0.036728 | 12 | 0 | 0 | 0 | 4670 | 8516 |
| replication | SSSS/vs_baseline_0 | AMBIGUOUS | 12 | 12 | -0.0042966 | 0.0018671 | 3 | 9 | 0 | 5 | 8381 | 34945 |
| replication | SSSS/vs_baseline_0 | NEITHER | 12 | 12 | -0.0064294 | 0.018491 | 7 | 5 | 0 | 0 | 8381 | 34945 |
| replication | SSSS/vs_baseline_0 | SL_FIRST | 12 | 12 | -0.019521 | -0.0042415 | 0 | 12 | 0 | 0 | 8381 | 34945 |
| replication | SSSS/vs_baseline_0 | TP_FIRST | 12 | 12 | -0.0050078 | 0.024301 | 10 | 2 | 0 | 0 | 8381 | 34945 |
| replication | SSSS/vs_baseline_0 | mae_pct | 12 | 12 | -0.048224 | -0.026241 | 0 | 12 | 0 | 0 | 8381 | 34945 |
| replication | SSSS/vs_baseline_0 | mfe_pct | 12 | 12 | -0.053672 | -0.023439 | 0 | 12 | 0 | 0 | 8381 | 34945 |
| replication | SSSS/vs_baseline_1 | AMBIGUOUS | 12 | 12 | -0.0045173 | -0.00073297 | 0 | 12 | 0 | 6 | 8381 | 15943 |
| replication | SSSS/vs_baseline_1 | NEITHER | 12 | 12 | -0.00018531 | 0.029133 | 11 | 1 | 0 | 0 | 8381 | 15943 |
| replication | SSSS/vs_baseline_1 | SL_FIRST | 12 | 12 | -0.019357 | 0.0046703 | 2 | 10 | 0 | 0 | 8381 | 15943 |
| replication | SSSS/vs_baseline_1 | TP_FIRST | 12 | 12 | -0.015849 | 0.0051294 | 3 | 9 | 0 | 0 | 8381 | 15943 |
| replication | SSSS/vs_baseline_1 | mae_pct | 12 | 12 | -0.051857 | -0.030668 | 0 | 12 | 0 | 0 | 8381 | 15943 |
| replication | SSSS/vs_baseline_1 | mfe_pct | 12 | 12 | -0.13018 | -0.044822 | 0 | 12 | 0 | 0 | 8381 | 15943 |
| replication | SSSS/vs_baseline_2 | AMBIGUOUS | 12 | 12 | -0.0052929 | -0.0016875 | 0 | 12 | 0 | 6 | 8381 | 12870 |
| replication | SSSS/vs_baseline_2 | NEITHER | 12 | 12 | 0.00083235 | 0.030971 | 12 | 0 | 4 | 0 | 8381 | 12870 |
| replication | SSSS/vs_baseline_2 | SL_FIRST | 12 | 12 | -0.017866 | 0.0026473 | 2 | 10 | 0 | 0 | 8381 | 12870 |
| replication | SSSS/vs_baseline_2 | TP_FIRST | 12 | 12 | -0.017552 | 0.0045448 | 3 | 9 | 0 | 0 | 8381 | 12870 |
| replication | SSSS/vs_baseline_2 | mae_pct | 12 | 12 | -0.064378 | -0.046634 | 0 | 12 | 0 | 8 | 8381 | 12870 |
| replication | SSSS/vs_baseline_2 | mfe_pct | 12 | 12 | -0.091233 | -0.045105 | 0 | 12 | 0 | 0 | 8381 | 12870 |
| replication | SSSS/vs_baseline_3 | AMBIGUOUS | 12 | 12 | -0.004929 | -0.0018676 | 0 | 12 | 0 | 6 | 8381 | 10060 |
| replication | SSSS/vs_baseline_3 | NEITHER | 12 | 12 | 0.00039828 | 0.015104 | 12 | 0 | 0 | 0 | 8381 | 10060 |
| replication | SSSS/vs_baseline_3 | SL_FIRST | 12 | 12 | -0.011792 | -0.0037705 | 0 | 12 | 0 | 0 | 8381 | 10060 |
| replication | SSSS/vs_baseline_3 | TP_FIRST | 12 | 12 | -0.0052037 | 0.0082431 | 9 | 3 | 0 | 0 | 8381 | 10060 |
| replication | SSSS/vs_baseline_3 | mae_pct | 12 | 12 | -0.02735 | -0.020952 | 0 | 12 | 0 | 8 | 8381 | 10060 |
| replication | SSSS/vs_baseline_3 | mfe_pct | 12 | 12 | -0.068668 | -0.013035 | 0 | 12 | 0 | 0 | 8381 | 10060 |

Full per-grid and quarterly effects, exact A/B denominators, weekly blocks and six-metric paired bootstrap intervals are in per-period analysis/contrasts.csv. Positive TP_FIRST alone is not sufficient evidence of a better outcome composition.

2023 is the **previously inspected replication period**, not an untouched final test. No 2024, live trading, leverage, new detector, spatial overlap research, cross-timeframe raw-score sum or threshold optimization. Dependent grids and unadjusted multiple comparisons remain exploratory.
