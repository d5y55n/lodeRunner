# Current-Price State Audit

## Validation-Only Amendment

One shared-close discrepancy was retained: 2023-11-10 16:00 UTC, native 1h price 37092.6 versus current 15m P 37118.4. Original scalar scoring is independently reproduced at BOTH prices. At native P, 1h support/resistance counts=11/24, A1=-14, A2=-15; at current P, counts=10/24, A1=-11.5, A2=-9. Both states are R. All timeframes use common 15m P. No source price was replaced and no row was excluded.

The original shared-close price-equality assertion stopped execution before replication outcomes. A separate validation-only runner applies a general rule: identical input prices require native-descriptor parity; differing prices require a preserved warning and scalar parity at both prices. It changes no frozen mathematical definition, membership, original code file, quantile or development result. This is not a date-specific exemption.

The runner was sealed before replication outcomes after exact replay of all 2022 states (34,585 rows, 137 columns, including dtypes). Its SHA256 is `0b2eefe04f3bfa80dbd24e1bfdd871bc2851d29b798a8d99738c353cd01954fa`; seals and replay evidence are in `data/phase5_1/validation-amendment`. Replication has exactly one price warning. Independently reconstructed carried patterns match original Phase 5 pattern fields for all 34,585 development and 35,040 replication rows. No spatial columns were read for that check.

All four timeframes are evaluated at the SAME closed 15m P(T). Native candidate membership and 850-day window are held until their next native close; only proximity counts, original A1/A2 and nearest-price geometry are re-evaluated at P. No detector is rebuilt.

Phase 5 carried higher-timeframe descriptors from their own source close price. They are not generally same-P states between native closes. Existing Phase 5 artifacts remain unchanged, and these mismatches are a semantics correction, not a threshold fit. The 15m descriptors are reused exactly.

| phase | timeframe | changed_state | same_price_native_close_parity | all_current_price_checks |
| --- | --- | --- | --- | --- |
| development | 15m | 0 | 34585 | 260 |
| development | 1h | 4968 | 8646 | 260 |
| development | 4h | 7606 | 2161 | 260 |
| development | 1d | 8038 | 360 | 260 |
| replication | 15m | 0 | 35040 | 248 |
| replication | 1h | 3900 | 8759 | 248 |
| replication | 4h | 5113 | 2190 | 248 |
| replication | 1d | 5691 | 365 | 248 |

## development

Changed complete pattern timestamps: 15505. Real example counts by requested type: {'RRRR': 3, 'SSSS': 3, 'missing': 3, 'mixed': 3, 'neutral': 3}. Real missing-pattern count: 237. Absent real types are explicitly absent; the synthetic empty-map M fixture is not a market observation.
| T | P | timeframe | source_timestamp | support_count | resistance_count | raw_difference | imbalance | A1 | A2 | state | pattern |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1641404700000 | 46151 | 15m | 1641404700000 | 119 | 87 | 32 | 0.15534 | 29.5 | 27 | S | SSSS |
| 1641404700000 | 46151 | 1h | 1641402000000 | 54 | 38 | 16 | 0.17391 | 17 | 18 | S | SSSS |
| 1641404700000 | 46151 | 4h | 1641398400000 | 37 | 20 | 17 | 0.29825 | 14 | 11 | S | SSSS |
| 1641404700000 | 46151 | 1d | 1641340800000 | 19 | 7 | 12 | 0.46154 | 11 | 10 | S | SSSS |
| 1641537900000 | 41517 | 15m | 1641537900000 | 34 | 37 | -3 | -0.042254 | -7 | -11 | R | RRRR |
| 1641537900000 | 41517 | 1h | 1641535200000 | 14 | 15 | -1 | -0.034483 | 0 | 1 | R | RRRR |
| 1641537900000 | 41517 | 4h | 1641528000000 | 5 | 8 | -3 | -0.23077 | -2.5 | -2 | R | RRRR |
| 1641537900000 | 41517 | 1d | 1641513600000 | 3 | 5 | -2 | -0.25 | -2 | -2 | R | RRRR |

## replication

Changed complete pattern timestamps: 11872. Real example counts by requested type: {'RRRR': 3, 'SSSS': 3, 'missing': 3, 'mixed': 3, 'neutral': 3}. Real missing-pattern count: 48. Absent real types are explicitly absent; the synthetic empty-map M fixture is not a market observation.
| T | P | timeframe | source_timestamp | support_count | resistance_count | raw_difference | imbalance | A1 | A2 | state | pattern |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1672531200000 | 16538 | 15m | 1672531200000 | 199 | 177 | 22 | 0.058511 | 24 | 26 | S | SSSS |
| 1672531200000 | 16538 | 1h | 1672531200000 | 93 | 70 | 23 | 0.1411 | 23 | 23 | S | SSSS |
| 1672531200000 | 16538 | 4h | 1672531200000 | 35 | 21 | 14 | 0.25 | 11 | 8 | S | SSSS |
| 1672531200000 | 16538 | 1d | 1672531200000 | 14 | 11 | 3 | 0.12 | 4.5 | 6 | S | SSSS |
| 1672802100000 | 16831 | 15m | 1672802100000 | 262 | 292 | -30 | -0.054152 | -35.5 | -41 | R | RRRR |
| 1672802100000 | 16831 | 1h | 1672801200000 | 110 | 123 | -13 | -0.055794 | -12.5 | -12 | R | RRRR |
| 1672802100000 | 16831 | 4h | 1672790400000 | 35 | 40 | -5 | -0.066667 | -4 | -3 | R | RRRR |
| 1672802100000 | 16831 | 1d | 1672790400000 | 13 | 14 | -1 | -0.037037 | -0.5 | 0 | R | RRRR |

All deterministic full examples (mixed, neutral, missing where observed, closed-clock boundaries, same-P reference and physically truncated alignment) are in per-period classification-examples.csv. Classification audit completed before loading any future outcomes for this phase.

The previous support/resistance spatial intersection counts do NOT mean SSSS/RRRR and are not evidence for or against this hypothesis. No spatial fields are read. Full predeclared definitions: data/phase5_1/plan.json.

2023 is the **previously inspected replication period**, not an untouched final test. No 2024, live trading, leverage, new detector, spatial overlap research, cross-timeframe raw-score sum or threshold optimization. Dependent grids and unadjusted multiple comparisons remain exploratory.
