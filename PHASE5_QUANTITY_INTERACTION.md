# Quantity Interaction

Existing 15m one-candle zone-union quantity is not total-market volume. Development quartiles are unchanged in replication. Delta tables and per-timeframe magnitude sensitivity remain secondary and are not direction definitions.

quantity / TP_FIRST: 120 supported comparison/grid cells in both periods; 36 reverse pooled sign between development and replication; 0 retain one nonzero sign across all eight supported quarters. Development effect range [-0.0979377, 0.142333], replication [-0.0578331, 0.241356]. These are dependent descriptive cells, not a selected strategy or independent discoveries.

quantity / AMBIGUOUS: 120 supported comparison/grid cells in both periods; 0 reverse pooled sign between development and replication; 0 retain one nonzero sign across all eight supported quarters. Development effect range [0.0118278, 0.137699], replication [0.00423985, 0.0726872]. These are dependent descriptive cells, not a selected strategy or independent discoveries.

## Supported Directional Stability
| family | direction | metric | comparisons | supported_both | same_sign_dev_quarters_rep | same_sign_eight_quarters |
| --- | --- | --- | --- | --- | --- | --- |
| quantity | LONG | AMBIGUOUS | 120 | 120 | 4 | 0 |
| quantity | LONG | TP_FIRST | 120 | 120 | 1 | 0 |
| quantity | SHORT | AMBIGUOUS | 120 | 120 | 4 | 0 |
| quantity | SHORT | TP_FIRST | 120 | 120 | 0 | 0 |

Full exact denominators, all four labels, censoring, MFE/MAE and pooled shared-block intervals: `data/phase5/<period>/analysis/`. These counts span multiple dependent grids; they are not independent successful discoveries.

2023 is the **previously inspected replication period**, not a pristine test. No 2024 data, live rule, leverage, raw-score sum, threshold selection or winning timeframe selection. All comparisons are descriptive and dependent; bootstrap intervals are not adjusted for multiplicity.
