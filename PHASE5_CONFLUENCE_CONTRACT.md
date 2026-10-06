# Phase 5 Confluence Contract

## version

phase5-A-confluence-v1

## timeframes

('15m', '1h', '4h', '1d')

## steps

{'15m': 900000, '1h': 3600000, '4h': 14400000, '1d': 86400000}

## widths

{'15m': 0.002, '1h': 0.004, '4h': 0.007, '1d': 0.022}

## development

2022 eligible frozen 850-day maps only

## replication

2023 previously inspected replication period; gated by complete development freeze

## clock

15m closed timestamps; latest source<=T; age<one native step; no candle fill

## direction

primary sign of nearby raw (support-resistance)/(support+resistance); exact zero balanced; empty neighborhood missing, not balanced

## descriptors

separate A1 sign, A2 sign, raw imbalance sign, full-map and nearby counts, nearest geometry; no summed score

## sign_sensitivity

['A1', 'A2']

## nearby

unchanged original full/half native membership at source decision price; held with source state until next close

## intervals

candidate p: closed [p*(1-w_tf),p*(1+w_tf)]; nearby uses original strict outer 1.5w boundary; no new proximity width

## overlap

U_tf=union of native nearby intervals of one type; I_subset=intersection of U_tf; touching counts; preserve every connected component and every nonempty subset; maximum count is descriptive only

## distance

max(lower-current_price,0,current_price-upper); also divided by current_price; no reclassification of held native scores at current price

## participant_count

unique native candidate intervals intersecting each common component, counted per timeframe; candidate indices reference frozen catalog

## categories

all 15 nonempty TF subsets, exact S/R/N/M pattern, separate marginal aligned counts and no-opposition counts, lower(15m,1h)/higher(4h,1d) exact patterns

## incremental

within fixed base-aligned cohort: added agrees vs added neutral/conflicts; missing separately; same UTC block draws on both groups

## baselines

all same-period eligible T; each constituent single-TF aligned; each proper lower-order aligned subset; explicit inclusive vs exclusive-only distinction

## quantity

unchanged 15m A joint quantity from native 1-candle flow only as primary risk covariate; unavailable remains missing; quartiles development only

## delta

unchanged support/resistance normalized Delta and joint/raw Delta; secondary quartile tables only

## magnitude

per-timeframe development quartiles of abs(nearby imbalance); separate native bucket vector; all-four weak Q1, moderate Q2/Q3, strong Q4, mixed, missing; never summed

## outcomes

reuse frozen Phase4 15m event_id/timestamp rows, LONG/SHORT x TP .003/.005 x SL .003/.005 x horizons 16/32/96; no regeneration

## censoring

report all counts; rates/MFE/MAE conditional on complete horizon; censored retained explicitly

## quarters

UTC 2022 and 2023 Q1-Q4 separately plus ALL

## uncertainty

1000 shared multinomial resamples of epoch-aligned seven-day UTC blocks, seed 5105; paired subset/baseline or disjoint conditional contrasts; all 24 grids, all outcome rates and MFE/MAE

## sparsity

supported>=200 complete timestamps and>=5 occupied seven-day blocks in BOTH contrast groups; CI needs>=950 finite draws; no rare-category merge; still report all cells

## shapes

1/2/3/4: sparse if any unsupported; exact flat if all equal; monotonic up/down if ordered; otherwise nonlinear; quarterly sign changes reported not pooled away

## no_2024

True

## no_live_rules

True

## no_winner

True

## no_BC

True

## hierarchy

[['15m'], ['1h'], ['4h'], ['1d'], ['15m', '1h'], ['15m', '4h'], ['15m', '1d'], ['1h', '4h'], ['1h', '1d'], ['4h', '1d'], ['15m', '1h', '4h'], ['15m', '1h', '1d'], ['15m', '4h', '1d'], ['1h', '4h', '1d'], ['15m', '1h', '4h', '1d']]

## additions

[(['15m'], '1h'), (['1h'], '4h'), (['4h'], '1d'), (['15m', '1h'], '4h'), (['1h', '4h'], '1d'), (['15m', '1h', '4h'], '1d'), (['15m', '1h', '1d'], '4h'), (['15m', '4h', '1d'], '1h'), (['1h', '4h', '1d'], '15m')]

## Mathematical Spatial Definition

For type k and timeframe f, let C(f,k,t_f) be the frozen nearby candidate set at native closed time t_f <= T.
For candidate price p, J(f,p) = [p(1-w_f), p(1+w_f)].
U(f,k) is the union of these closed intervals, without double-counting same-timeframe overlaps.
For each nonempty subset S of timeframes, I(S,k) = intersection over f in S of U(f,k).
Every connected component [L,H] of I is retained, including L=H contact.
Width = H-L; price distance = max(L-P(T), 0, P(T)-H).
The raw participant count is the number of distinct candidate intervals intersecting that component, summed across contributing timeframes. Duplicate-price candidates remain distinct native candidates.

No global candidate Cartesian product is constructed. A four-way intersection must exist at a common price; pairwise intersections at different prices cannot manufacture a four-way region.
Native intervals are selected at their source close and carried with the native STATE. They are not reselected or rescored at the 15m price. Common-price distance exposes when carried regions have moved away from current price.
State tables include source snapshot/interval references; native tables contain every [lower,upper,candidate_index] and frozen source-catalog hashes. The common table preserves native unions and source ages. The overlap table preserves every combination/component, not only the largest one.

## Interpretation and Dependence

Primary support-heavy is positive raw nearby imbalance; resistance-heavy is negative; balanced is exact zero with at least one nearby candidate. Empty neighborhoods are missing. A1 and A2 signs are separate sensitivity families, not combined votes.
An inclusive singleton allows other aligned timeframes; exclusive 'only' requires exactly that participating set. Counts include conflicts unless explicitly marked unopposed. Exact S/R/N/M patterns follow 15m,1h,4h,1d order.
An incremental contrast fixes the base-aligned cohort and compares added-TF agreement against nonagreement, neutral or conflict. Shared weekly resampling preserves temporal dependence and overlap between nested masks. There is no individual-counterfactual causal claim.
Pooled bootstrap intervals cover every declared grid and six metrics. Quarterly effects, support and sign consistency are separate; no independent-row p-values. Block duration sensitivity and multiplicity-adjusted confirmatory inference remain limitations.

2023 is the **previously inspected replication period**, not a pristine test. No 2024 data, live rule, leverage, raw-score sum, threshold selection or winning timeframe selection. All comparisons are descriptive and dependent; bootstrap intervals are not adjusted for multiplicity.
