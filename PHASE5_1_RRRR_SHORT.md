# RRRR / SHORT at Current Price

Baseline 0=all eligible; 1=15m only condition; 2=15m+1h; 3=15m+1h+4h. Baselines are inclusive and nested, evaluated on one common 15m future path. Differences are RRRR minus baseline.

| phase | comparison | metric | grids | supported | minimum_effect | maximum_effect | positive | negative | CI_above_zero | CI_below_zero | minimum_A_complete | minimum_B_complete |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | RRRR/vs_baseline_0 | AMBIGUOUS | 12 | 12 | -0.0123 | -0.0017411 | 0 | 12 | 0 | 3 | 8306 | 34490 |
| development | RRRR/vs_baseline_0 | NEITHER | 12 | 12 | 0.00018421 | 0.027348 | 12 | 0 | 0 | 0 | 8306 | 34490 |
| development | RRRR/vs_baseline_0 | SL_FIRST | 12 | 12 | -0.0087148 | 0.014203 | 8 | 4 | 0 | 0 | 8306 | 34490 |
| development | RRRR/vs_baseline_0 | TP_FIRST | 12 | 12 | -0.01818 | -0.0011733 | 0 | 12 | 0 | 0 | 8306 | 34490 |
| development | RRRR/vs_baseline_0 | mae_pct | 12 | 12 | -0.10723 | -0.051767 | 0 | 12 | 0 | 0 | 8306 | 34490 |
| development | RRRR/vs_baseline_0 | mfe_pct | 12 | 12 | -0.31336 | -0.13926 | 0 | 12 | 0 | 8 | 8306 | 34490 |
| development | RRRR/vs_baseline_1 | AMBIGUOUS | 12 | 12 | -0.0062135 | -0.0004497 | 0 | 12 | 0 | 0 | 8306 | 18021 |
| development | RRRR/vs_baseline_1 | NEITHER | 12 | 12 | -0.00029233 | 0.012592 | 11 | 1 | 0 | 0 | 8306 | 18021 |
| development | RRRR/vs_baseline_1 | SL_FIRST | 12 | 12 | -0.0039416 | 0.013259 | 10 | 2 | 0 | 0 | 8306 | 18021 |
| development | RRRR/vs_baseline_1 | TP_FIRST | 12 | 12 | -0.0098737 | -0.0043526 | 0 | 12 | 0 | 0 | 8306 | 18021 |
| development | RRRR/vs_baseline_1 | mae_pct | 12 | 12 | -0.022364 | -0.0061358 | 0 | 12 | 0 | 0 | 8306 | 18021 |
| development | RRRR/vs_baseline_1 | mfe_pct | 12 | 12 | -0.1925 | -0.072058 | 0 | 12 | 0 | 0 | 8306 | 18021 |
| development | RRRR/vs_baseline_2 | AMBIGUOUS | 12 | 12 | -0.004964 | 0.00026661 | 1 | 11 | 0 | 0 | 8306 | 14011 |
| development | RRRR/vs_baseline_2 | NEITHER | 12 | 12 | -0.00027758 | 0.013288 | 10 | 2 | 0 | 0 | 8306 | 14011 |
| development | RRRR/vs_baseline_2 | SL_FIRST | 12 | 12 | -0.0062702 | 0.012615 | 9 | 3 | 0 | 0 | 8306 | 14011 |
| development | RRRR/vs_baseline_2 | TP_FIRST | 12 | 12 | -0.010511 | -0.0038808 | 0 | 12 | 0 | 0 | 8306 | 14011 |
| development | RRRR/vs_baseline_2 | mae_pct | 12 | 12 | -0.013467 | 0.00025331 | 4 | 8 | 0 | 0 | 8306 | 14011 |
| development | RRRR/vs_baseline_2 | mfe_pct | 12 | 12 | -0.14449 | -0.055191 | 0 | 12 | 0 | 0 | 8306 | 14011 |
| development | RRRR/vs_baseline_3 | AMBIGUOUS | 12 | 12 | -0.0018997 | 0.0014153 | 9 | 3 | 0 | 0 | 8306 | 11117 |
| development | RRRR/vs_baseline_3 | NEITHER | 12 | 12 | 0.00066974 | 0.0081885 | 12 | 0 | 0 | 0 | 8306 | 11117 |
| development | RRRR/vs_baseline_3 | SL_FIRST | 12 | 12 | -0.0012587 | 0.0076956 | 10 | 2 | 0 | 0 | 8306 | 11117 |
| development | RRRR/vs_baseline_3 | TP_FIRST | 12 | 12 | -0.010311 | -0.0050726 | 0 | 12 | 0 | 0 | 8306 | 11117 |
| development | RRRR/vs_baseline_3 | mae_pct | 12 | 12 | -0.0016587 | 0.020219 | 8 | 4 | 0 | 0 | 8306 | 11117 |
| development | RRRR/vs_baseline_3 | mfe_pct | 12 | 12 | -0.044657 | -0.033672 | 0 | 12 | 0 | 0 | 8306 | 11117 |
| replication | RRRR/vs_baseline_0 | AMBIGUOUS | 12 | 12 | -0.00089152 | 0.0036695 | 9 | 3 | 0 | 0 | 6139 | 34945 |
| replication | RRRR/vs_baseline_0 | NEITHER | 12 | 12 | -0.036696 | -0.0025337 | 0 | 12 | 0 | 0 | 6139 | 34945 |
| replication | RRRR/vs_baseline_0 | SL_FIRST | 12 | 12 | -0.019359 | 0.0088146 | 4 | 8 | 0 | 0 | 6139 | 34945 |
| replication | RRRR/vs_baseline_0 | TP_FIRST | 12 | 12 | 0.010587 | 0.027316 | 12 | 0 | 0 | 0 | 6139 | 34945 |
| replication | RRRR/vs_baseline_0 | mae_pct | 12 | 12 | 0.02252 | 0.089202 | 12 | 0 | 0 | 0 | 6139 | 34945 |
| replication | RRRR/vs_baseline_0 | mfe_pct | 12 | 12 | 0.038038 | 0.15175 | 12 | 0 | 0 | 0 | 6139 | 34945 |
| replication | RRRR/vs_baseline_1 | AMBIGUOUS | 12 | 12 | 0.00037756 | 0.0042175 | 12 | 0 | 3 | 0 | 6139 | 18345 |
| replication | RRRR/vs_baseline_1 | NEITHER | 12 | 12 | -0.05188 | -0.0071607 | 0 | 12 | 0 | 2 | 6139 | 18345 |
| replication | RRRR/vs_baseline_1 | SL_FIRST | 12 | 12 | -0.0053091 | 0.019666 | 10 | 2 | 0 | 0 | 6139 | 18345 |
| replication | RRRR/vs_baseline_1 | TP_FIRST | 12 | 12 | -0.0022301 | 0.031006 | 11 | 1 | 0 | 0 | 6139 | 18345 |
| replication | RRRR/vs_baseline_1 | mae_pct | 12 | 12 | 0.05325 | 0.15803 | 12 | 0 | 0 | 0 | 6139 | 18345 |
| replication | RRRR/vs_baseline_1 | mfe_pct | 12 | 12 | 0.049369 | 0.15473 | 12 | 0 | 0 | 0 | 6139 | 18345 |
| replication | RRRR/vs_baseline_2 | AMBIGUOUS | 12 | 12 | -9.5613e-06 | 0.0037176 | 11 | 1 | 3 | 0 | 6139 | 12999 |
| replication | RRRR/vs_baseline_2 | NEITHER | 12 | 12 | -0.031145 | -0.0058882 | 0 | 12 | 0 | 0 | 6139 | 12999 |
| replication | RRRR/vs_baseline_2 | SL_FIRST | 12 | 12 | 0.00051019 | 0.020751 | 12 | 0 | 0 | 0 | 6139 | 12999 |
| replication | RRRR/vs_baseline_2 | TP_FIRST | 12 | 12 | -0.013484 | 0.016398 | 8 | 4 | 0 | 0 | 6139 | 12999 |
| replication | RRRR/vs_baseline_2 | mae_pct | 12 | 12 | 0.038301 | 0.056727 | 12 | 0 | 0 | 0 | 6139 | 12999 |
| replication | RRRR/vs_baseline_2 | mfe_pct | 12 | 12 | 0.035593 | 0.09168 | 12 | 0 | 0 | 0 | 6139 | 12999 |
| replication | RRRR/vs_baseline_3 | AMBIGUOUS | 12 | 12 | 0.00018164 | 0.0015975 | 12 | 0 | 0 | 0 | 6139 | 9178 |
| replication | RRRR/vs_baseline_3 | NEITHER | 12 | 12 | -0.0022504 | 0.021206 | 8 | 4 | 0 | 0 | 6139 | 9178 |
| replication | RRRR/vs_baseline_3 | SL_FIRST | 12 | 12 | -0.0084312 | 0.012316 | 8 | 4 | 0 | 0 | 6139 | 9178 |
| replication | RRRR/vs_baseline_3 | TP_FIRST | 12 | 12 | -0.018846 | -0.0021936 | 0 | 12 | 0 | 0 | 6139 | 9178 |
| replication | RRRR/vs_baseline_3 | mae_pct | 12 | 12 | -0.082885 | -0.0041684 | 0 | 12 | 0 | 0 | 6139 | 9178 |
| replication | RRRR/vs_baseline_3 | mfe_pct | 12 | 12 | -0.052983 | -0.01248 | 0 | 12 | 0 | 0 | 6139 | 9178 |

Full per-grid and quarterly effects, exact A/B denominators, weekly blocks and six-metric paired bootstrap intervals are in per-period analysis/contrasts.csv. Positive TP_FIRST alone is not sufficient evidence of a better outcome composition.

2023 is the **previously inspected replication period**, not an untouched final test. No 2024, live trading, leverage, new detector, spatial overlap research, cross-timeframe raw-score sum or threshold optimization. Dependent grids and unadjusted multiple comparisons remain exploratory.
