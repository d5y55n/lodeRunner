# Phase 3R: A Score Sanity Analysis

## Scope, Not a Performance Claim

The deterministic sample is the first 24 hourly decisions with the authorized
full 850-day history: 2022-12-30 00:00 through 23:00 UTC. These are consecutive,
strongly dependent states of one market, not 24 independent trials. Every
TP/SL/horizon configuration is retained, without ranking. A1 and A2 describe
the same future price paths, not separate executed strategies.

No negative or zero A1 LONG scores occur here. SHORT is the exact negative of
LONG, so there are no positive or zero A1 SHORT scores either. We retain exact
discrete values instead of inventing strongly/moderately positive buckets
from this narrow one-day sample.

## Exact A1 Distribution

The final three columns illustrate the already-declared LONG, TP=SL=0.003,
horizon=8 configuration; this is not a selected best configuration. All grids,
both directions and A1/A2 are in `data/phase3r/sanity/a-exact-score-outcomes.csv`,
including censoring, MFE/MAE and time-to-extreme summaries.

| LONG score | SHORT score | State count | TP_FIRST | SL_FIRST | NEITHER |
|---:|---:|---:|---:|---:|---:|
| 2.5 | -2.5 | 1 | 0 | 1 | 0 |
| 6.5 | -6.5 | 1 | 0 | 1 | 0 |
| 9.5 | -9.5 | 1 | 0 | 1 | 0 |
| 10 | -10 | 1 | 0 | 1 | 0 |
| 10.5 | -10.5 | 1 | 0 | 1 | 0 |
| 11 | -11 | 1 | 0 | 1 | 0 |
| 15.5 | -15.5 | 4 | 2 | 1 | 1 |
| 17.5 | -17.5 | 1 | 1 | 0 | 0 |
| 20.5 | -20.5 | 2 | 2 | 0 | 0 |
| 21 | -21 | 2 | 0 | 2 | 0 |
| 21.5 | -21.5 | 2 | 2 | 0 | 0 |
| 28 | -28 | 1 | 0 | 1 | 0 |
| 28.5 | -28.5 | 1 | 0 | 1 | 0 |
| 29 | -29 | 1 | 0 | 1 | 0 |
| 29.5 | -29.5 | 1 | 0 | 1 | 0 |
| 30 | -30 | 1 | 0 | 1 | 0 |
| 31 | -31 | 1 | 0 | 1 | 0 |
| 33 | -33 | 1 | 1 | 0 | 0 |

This illustrated configuration has zero AMBIGUOUS and zero censored rows.
All 576 future-outcome rows across the full grid are uncensored; the sample
schedule was chosen before outcomes and leaves the required future horizon
inside 2022. No future 2023 or 2024 candles are needed.

## A1/A2/A3/A4 Comparison

| Representation | Observed range or change | Interpretation |
|---|---|---|
| A1 original LONG | 2.5 to 33 | Exact original function parity |
| A2 full-weight LONG | -3 to 29 | Original half band removed, nothing fitted |
| A3 nearby support count | 38 to 101 | Full plus half band candidates, unweighted |
| A3 nearby resistance count | 17 to 82 | Same geometry, separate type |
| A4 nearest support distance | 0 to about 0.000241 of price | Continuous, unsigned distance; signed also in raw map |
| A4 nearest resistance distance | about 0.000006 to 0.000658 | Continuous, no proximity weighting |

Outer contributions change the numeric score at 21/24 timestamps. A2 LONG
is negative at two timestamps where A1 is positive. This proves the outer
band can materially affect the reference, not that the effect is useful.
The original A1 remains unchanged. `a-ablation-states.csv` contains all 24
paired states, and `a-ablation-outcomes.csv` attaches every grid outcome to
all four representations for inspection. Raw signed/mean distances remain
available through the snapshot/event join. No thresholds or fitted model.

## Six Research Questions

1. Do LONG outcomes improve as LONG score rises? Not established. The displayed
   sample has reversals in observed TP fractions; most exact scores have n=1.
2. Do SHORT outcomes improve as SHORT score rises? Not established. Only negative
   SHORT scores occur, and its outcome paths overlap the LONG observations.
3. Is the relationship monotonic? The displayed finite-sample table is not
   monotonic. This neither proves nor disproves population monotonicity.
4. Is zero meaningfully different from large absolute values? Not testable
   here: zero A1 states are absent. A2 zeros cannot substitute for A1 zeros.
5. Are extreme scores too rare? Every observed value has only 1-4 states;
   the global frequency or meaning of an extreme cannot be estimated here.
6. Does the outer half band add useful information? It changes states, but
   incremental predictive utility is not established by this sanity sample.

Negative/zero coverage, broad regimes, dependence-aware uncertainty and
adequate historical windows are missing. No edge claim or final rule follows.
