# Phase 3.5 Predeclared Descriptive Design

BTCUSDT, 1h, Detector A only. Original detector and existing six zone widths,
TP/SL grid and 4/8/24-candle horizons are unchanged. No 2024 reads, new detector,
other timeframe, leverage, signal, score, threshold optimization or trading rule.
2021-2022 is primary research. 2023 is a previously inspected replication period,
never pristine validation. Its A-only missing widths are generated separately,
only after development summaries and the descriptive configuration are sealed.
Frozen Phase 3 code and artifacts are preserved.

## Delta and Dependence

Preserve every A interaction including unavailable-volume rows. Preserve raw buy,
sell, delta, quantity, relative volume, normalized delta, type, visit, geometry,
reference close and decision time. Normalized delta is null when quantity is zero.
Unavailable volume is never replaced by zero. Exact historical midrank percentiles
use strictly earlier decision times, separately per width, with ties kept together.
Primary ECDF gives each earlier hourly event total weight one across its zones;
row-weighted ECDF is a sensitivity. Coordinate compression is computational only.
The first 100 prior valid rows are a calibration-coverage flag, not a tuned cutoff.
2023 uses the fixed full-development ECDF without updates. This adaptation-policy
difference is explicit: development percentiles expand, replication percentiles
are frozen. Legacy Phase 3 pooled full-development quartiles are retrospective
sensitivity labels only, never claimed to be available online in development.

## Breakdowns

Analyze deciles, ventiles (flag fewer than 100 unique events), quartiles, normalized
delta bins of width 0.2 on [-1,1], exact sign, and balanced/negative/positive delta
using abs(normalized delta)<=0.05. Descriptive sign sensitivities use 0/0.01/0.10,
without selecting a winner. Overlapping 20-percentile-point windows at 5-point
increments are visualization-only. Tied percentiles can leave empty buckets.

Separate support, resistance, and explicitly labeled pooled sensitivity; both
LONG/SHORT; visits 1/2/3/4+; all existing widths/TP/SL/horizons; UTC quarters;
low/middle/high volatility and negative/neutral/positive recent-return contexts.
Volatility uses January 2021 Q1/Q3. Return neutral width uses January absolute
return Q25; signs outside it are negative/positive. These fits are unavailable
before February 2021; January remains a separately labeled calibration context.
No full factorial of every facet simultaneously is claimed: each facet is crossed
with delta groups, type, width and the full outcome grid, keeping sample counts.

## Incremental Comparisons

For every delta subgroup compare all A at the same type/width/outcome setting,
and all A in the same facet. Matched controls are nearest earlier A events with
the same type/width/facet and causal regime cell, whose full outcome horizon ended
by the target decision. Matching sees no labels and never conditions on delta.
Report the matched-target subset separately, unmatched counts and reused unique
control counts. A-alone includes the subgroup; it is not a disjoint experiment.

Collapse same-event geometry for event-balanced rates; retain measurement weights
for row-weighted metrics. Separate outcomes and features. Adjacent events and
overlapping groups/horizons are dependent. No naive confidence intervals or
p-values are produced; quarter consistency is descriptive, not an independence
claim. Gross expectancy is conditional on unambiguous resolved complete horizons,
excludes costs and is not an executable strategy return. No automatic rule freeze.
