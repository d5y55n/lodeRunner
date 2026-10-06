# PROJECT_SPEC.md

# SR Probability Trading Platform

## 0. Project Status

This document is the authoritative specification for the project.

2026-09-27 update: Phase 1 is complete and Phase 2 is approved. Phase 2 is a neutral
Support/Resistance Candidate Research Engine. Its contract in sections 11-13
and 50 supersedes the previous pivot-only / volatility-clustering plan.
Longer-term probability, signals, leverage and execution sections below are
roadmap context ONLY, not authorization to implement them in Phase 2.
See `docs/research/PHASE2.md` for exact implemented semantics and limitations.

Phase 2 and Phase 2.5 are approved. The current authorized iteration is Phase 3:
multi-year historical research with development [2021-01-01, 2023-01-01) UTC and
validation [2023-01-01, 2024-01-01) UTC. The user explicitly reserves ALL 2024 data
for final testing; no 2024 acquisition, fitting or evaluation is allowed here.
Separate underlying events from candidate/configuration/measurement identities.
Add development-fitted volume/context buckets and causal matched controls.
After development, freeze a subset and evaluate it once on validation. Stop
after reporting; do not generate live signals or proceed to trading execution.

Phase 3 coverage policy: an aggregate-ID numerical gap alone is not evidence of
missing executions. Follow `docs/research/PHASE3_COVERAGE_POLICY.md`: outcome-blind
daily/monthly/1-minute-kline forensics, retained warnings or minimal minute-level
trade-volume quarantine. Keep verified candle-based price research through those
intervals. Invalid monthly publications may be explicitly replaced by verified
official daily sources; never reconstruct, interpolate or substitute candle volume.

The project is a research and decision-support platform for short-term cryptocurrency trading, initially focused on Binance BTCUSDT Futures.

The core philosophy is:

> **Simple is best. Accuracy over complexity.**

The system must not become a collection of conventional technical indicators. It should derive as much information as possible directly from price structure, support/resistance, volume, volatility, and multi-timeframe context.

The system must be validated by historical data. A feature must not be included merely because it sounds theoretically useful.

---

# 1. Primary Trading Objective

The intended trading style is short-term.

Typical behavior:

- Hold positions for minutes to several hours.
- A common target is roughly 10–15% position return.
- BTC leverage is expected to be roughly 10x–20x.
- Actual holding time, target, and leverage may vary with market conditions.

IMPORTANT:

The 10–15% figure refers to **leveraged position return**, not a requirement for BTC itself to move 10–15%.

For example, ignoring fees/funding/slippage:

- 10x leverage: approximately 1% underlying move ≈ 10% position return.
- 20x leverage: approximately 0.5% underlying move ≈ 10% position return.

Leverage must NOT be embedded into the market-direction prediction model.

The analysis engine predicts market behavior.

A separate risk engine converts market movement into leveraged position outcomes.

---

# 2. Core Decision Philosophy

The system must not primarily ask:

> "Will the next candle close higher?"

Instead it should ask:

> "Given the current market state, if a LONG/SHORT position is held from this point, what is the probability that the desired favorable price movement occurs before the adverse movement?"

The decision is updated as new candles arrive.

Conceptually:

```text
Current market state
        ↓
Estimate favorable/adverse path probabilities
        ↓
LONG / SHORT / NO TRADE
        ↓
If position exists:
        ↓
Recalculate on every new candle
        ↓
HOLD / EXIT / optionally REVERSE
```

There is no mandatory fixed holding period.

Time is an observation dimension, not the primary trading rule.

---

# 3. Non-Negotiable Principles

## 3.1 No indicator accumulation

Do NOT automatically add:

- RSI
- MACD
- Bollinger Bands
- Stochastic
- CCI
- dozens of candlestick patterns
- arbitrary moving-average combinations
- Fibonacci levels
- arbitrary oscillator combinations

These may only be added later if controlled experiments demonstrate incremental predictive value after costs and out-of-sample validation.

## 3.2 Price-first

Initial information hierarchy:

1. Price structure
2. Support/resistance
3. Volume
4. Volatility
5. Multi-timeframe context

## 3.3 No arbitrary weights initially

Do not begin with:

```text
S/R = +3
Volume = +2
Structure = +1
```

Weights must not be chosen merely by intuition.

First collect observations and outcomes.

Only after enough data exists should statistical relationships be examined.

## 3.4 No future leakage

At timestamp T, the system may only use information that would genuinely have been available at T.

A swing point may require confirmation candles in live trading. The confirmation delay must be represented in the backtest.

Never label a historical point using future information and then pretend that label was available at the original timestamp.

## 3.5 No overfitting

Do not optimize parameters against the entire historical dataset.

Use chronological splits:

```text
Training / research period
        ↓
Validation period
        ↓
Final untouched test period
```

No random train/test shuffle for time-series strategy evaluation.

## 3.6 NO TRADE is a valid outcome

The system must be allowed to say:

```text
LONG
SHORT
NO TRADE
```

A high signal frequency is not a goal.

---

# 4. Initial Scope

The first implementation focuses on:

- Binance USDⓈ-M Futures
- BTCUSDT
- Candlestick intervals:
  - 15m
  - 1h
  - 4h
  - 1d

The first MVP may initially operate on 1h BTCUSDT only to simplify validation.

Do not implement live trading or order execution in the first MVP.

No API keys should be required for public historical market-data collection.

---

# 5. Recommended Technology Stack

## Backend

- Python 3.12+
- FastAPI
- Pydantic
- NumPy
- pandas

## Frontend

- Next.js
- TypeScript
- TradingView Lightweight Charts or equivalent candle-chart library

## Testing

- pytest
- deterministic unit tests
- backtest regression tests

## Package management

- uv

## Database

Do NOT require PostgreSQL for the first algorithmic MVP.

Use local Parquet/CSV artifacts during research if convenient.

PostgreSQL can be introduced after the data model and strategy behavior stabilize.

## Development

The implementation is intended to be developed with Codex as the coding agent.

---

# 6. Repository Structure

Use this structure:

```text
sr-probability-trading/
│
├── PROJECT_SPEC.md
├── README.md
├── .gitignore
│
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   │
│   │   ├── market/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── binance_client.py
│   │   │   └── data_service.py
│   │   │
│   │   ├── analysis/
│   │   │   ├── __init__.py
│   │   │   ├── swings.py
│   │   │   ├── zones.py
│   │   │   ├── structure.py
│   │   │   ├── volume.py
│   │   │   ├── volatility.py
│   │   │   └── features.py
│   │   │
│   │   ├── probability/
│   │   │   ├── __init__.py
│   │   │   ├── outcomes.py
│   │   │   ├── empirical.py
│   │   │   └── calibration.py
│   │   │
│   │   ├── backtest/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py
│   │   │   ├── metrics.py
│   │   │   └── reports.py
│   │   │
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── market_routes.py
│   │       ├── analysis_routes.py
│   │       └── backtest_routes.py
│   │
│   └── tests/
│       ├── test_binance_client.py
│       ├── test_swings.py
│       ├── test_zones.py
│       ├── test_structure.py
│       ├── test_outcomes.py
│       └── test_backtest.py
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── app/
│   ├── components/
│   └── lib/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── research/
│
└── docs/
    └── research/
```

Keep analysis modules independent of Binance.

---

# 7. Market Data Model

Create a normalized candle model.

Required fields:

```text
open_time
close_time
open
high
low
close
volume
quote_volume
trade_count
taker_buy_volume
taker_buy_quote_volume
```

Use:

- integer timestamps in UTC internally
- float64/double precision for research calculations
- Decimal only where exact monetary arithmetic is explicitly required

Do not use float32 for prices.

---

# 8. Binance Data Layer

Implement a public-data client for Binance Futures klines.

The client must support:

- symbol
- interval
- start time
- end time
- limit
- pagination

Do not assume one API request can retrieve the complete historical dataset.

The data service must:

1. request batches,
2. detect the last returned candle,
3. advance the query window,
4. prevent duplicates,
5. sort chronologically,
6. validate timestamps,
7. validate OHLC consistency.

The system must never silently drop missing candles.

If gaps are detected, report them.

---

# 9. Candle Integrity Rules

For every candle:

```text
high >= max(open, close)
low  <= min(open, close)
high >= low
volume >= 0
```

Reject or flag invalid records.

Ensure chronological ordering.

Duplicate timestamps must be removed deterministically.

---

# 10. Support / Resistance Philosophy

Support and resistance are the central research hypothesis.

A level is NOT merely a horizontal line.

Represent it as a price zone.

A zone should contain:

```text
lower_price
upper_price
center_price
touch_count
reaction_count
first_seen
last_seen
timeframes
volume_statistics
```

Phase 2 stores candidate identity, zone bounds and raw interaction observations.
There is no strength formula, weighted score, probability or directional signal.

---

# 11. Independent Candidate Detectors A/B/C/D

Separate candidate detection, zone construction, interaction tracking, future
outcome measurement and statistical comparison. No detector is primary or a winner.

Every candidate preserves detector, SUPPORT/RESISTANCE/NEUTRAL type, reference
price, source timestamp, known_at, timeframe, source candle IDs and metadata.
All candle detectors expose `detect(candles, timeframe, as_of)` and use closed
candles only. D implements that contract with explicitly supplied trade data.

- A: preserve original scoring.js exactly for reference selection. Bullish then
  bearish selects MIN of the two highs; bearish then bullish selects MAX of lows.
  Equal highs/lows select the earlier candle. Dojis generate no candidate.
  Known only at the second candle's exclusive close boundary. No old scores.
- B: strict local high/low against configurable N candles on each side. Equal
  extrema are excluded. Known at the last right-side candle's close boundary.
- C: independent running high/low trackers. A later candle CLOSE confirms a
  configurable fractional reversal. A new-extreme candle cannot confirm itself.
  Reset each tracker to its confirming candle. Preserve extreme and confirmation
  times separately. This is a documented research variant, not an optimal formula.
- D: true trades/aggregate trades into fixed price bins and completed fixed
  windows. Select concentration relative to mean occupied-bin quantity with a
  configurable multiple. Output NEUTRAL areas; high volume has no direction.

D and A/B/C volume attachments require trade-level price, quantity, timestamp,
ID, and buyer-maker flag when available. OHLCV is not a substitute.

---

# 12. Zone Width Experiments

One immutable zone per candidate and width configuration. Do not merge zones or
select volatility-normalized clustering as the final method in this phase.

- Fixed half-width grid: +/-0.05%, 0.10%, 0.20%, 0.30%, 0.50%.
- Original timeframe configuration: 15m=0.20%, 1h=0.40%, 4h=0.70%, 1d=2.20%.
- Adaptive-width extension receives only history available at known_at; no
  formula is selected and it is not the default runner configuration.

Every zone retains the candidate and exact width model and parameter.

---

# 13. Zone Interaction

For every newly formed/known zone, identify later interactions.

Only candles starting at/after known_at can interact. A continuous visit follows
OUTSIDE -> ENTERED -> INTERACTING -> EXITED; entry may exit on the same candle.
Store start/end, sequential visit number, approach side, wick overlap, close
inside, maximum penetration, candles spent, exit side and close-confirmed crossing.
Unknown approach from inside stays explicit rather than inventing direction.

Compare close-outside-boundary exits against close-outside-plus-configurable-
separation exits. Neither is declared optimal. Finished visit statistics are
descriptive facts, never retrospectively used as entry-time predictors.

Outcome entry is the first interaction candle's close; future measurement starts
with the next candle. Both hypothetical LONG and SHORT are measured, irrespective
of zone type, over configurable TP/SL and horizon grids. Labels: TP_FIRST,
SL_FIRST, NEITHER, AMBIGUOUS. Same-candle double hits are ambiguous unless the
open already establishes the first boundary hit. Incomplete horizons are flagged
censored and unresolved labels stay null. MFE/MAE cover the whole observation
window, with candle-end time resolution.

Optional A/B/C volume features use exact in-zone trades and the previous equal-
duration in-zone window as an explicit baseline. Zero baseline yields no ratio;
missing coverage remains missing. No directional conversion is performed.

---

# 14. Zone Strength

Do not initially create one arbitrary weighted score.

Instead expose raw features:

```text
touch_count
reaction_count
age
recency
timeframe_count
volume_percentile
reaction_magnitude
rejection_rate
break_rate
distance_from_current_price
```

Later, statistical testing can determine which features have predictive value.

---

# 15. Market Structure

Detect:

- Higher High (HH)
- Higher Low (HL)
- Lower High (LH)
- Lower Low (LL)

The structure engine should produce events such as:

```text
HH
HL
LH
LL
```

and derive a transparent state:

```text
BULLISH
BEARISH
RANGE
TRANSITION
UNKNOWN
```

Do not use subjective chartist language without defining the exact rules.

All structure transitions must be reproducible.

---

# 16. Volume

Volume is initially a confirmation/context feature.

Do NOT interpret:

```text
high volume = LONG
```

or:

```text
low volume = SHORT
```

Instead measure:

- relative volume
- volume percentile
- volume around zones
- volume during rejection
- volume during breakout
- volume compared with recent baseline

The primary hypothesis is:

> Volume can help distinguish meaningful S/R interactions from weak interactions.

This hypothesis must be tested.

---

# 17. Volatility

Volatility is used primarily to normalize price distances.

Initial candidate:

- ATR or true-range based rolling volatility.

Possible normalized distances:

```text
distance_to_support / volatility
distance_to_resistance / volatility
reaction_size / volatility
```

Do not automatically use volatility as a directional signal.

---

# 18. Multi-Timeframe Analysis

Initial timeframes:

```text
15m
1h
4h
1d
```

The system should independently calculate:

- swings
- zones
- market structure
- volume context
- volatility

for each timeframe.

Then expose cross-timeframe relationships.

Examples:

```text
1d resistance overlaps 4h resistance
4h support overlaps 1h support
15m signal conflicts with 4h structure
```

Do not simply sum timeframe scores.

Cross-timeframe relationships are separate features until statistical validation demonstrates an appropriate combination.

---

# 19. The Core Prediction Target

This is the most important part of the project.

The target is NOT simply:

```text
next candle close > current close
```

Instead define a path-dependent outcome.

For a hypothetical LONG:

```text
Entry price = P

Take-profit boundary = P * (1 + tp_return)
Stop-loss boundary = P * (1 - sl_return)
```

For a SHORT:

```text
Entry price = P

Take-profit boundary = P * (1 - tp_return)
Stop-loss boundary = P * (1 + sl_return)
```

Then examine future candles and determine which boundary is reached first.

Possible outcomes:

```text
TP_FIRST
SL_FIRST
NEITHER_WITHIN_HORIZON
```

This is the primary outcome framework.

---

# 20. Do Not Hardcode One TP/SL Pair

The research engine must support multiple TP/SL configurations.

Example research grid:

```text
TP:
0.3%
0.5%
0.7%
1.0%
1.5%
2.0%

SL:
0.2%
0.3%
0.5%
0.7%
1.0%
```

These are research examples, not final trading parameters.

The final production parameters must be determined from validation.

---

# 21. Horizon

Do not force a fixed 1-hour, 2-hour, 4-hour or 6-hour exit.

However, for statistical labeling, the engine may evaluate multiple horizons:

```text
1 candle
2 candles
4 candles
8 candles
12 candles
24 candles
```

The horizon is a measurement dimension.

The live strategy can continue until:

- TP,
- SL,
- probability/expected-value condition deteriorates,
- risk rule triggers,
- or another explicitly defined exit rule triggers.

---

# 22. MFE / MAE

For every hypothetical trade, calculate:

### MFE

Maximum favorable excursion after entry.

### MAE

Maximum adverse excursion after entry.

Record:

```text
mfe_percent
mae_percent
mfe_time
mae_time
```

Also calculate excursion relative to volatility where appropriate.

This is essential for understanding whether a signal reaches its target cleanly or only after severe adverse movement.

---

# 23. Dynamic Re-Evaluation

When a real position exists, the system should reassess on every completed candle.

Example:

```text
LONG ENTRY

Candle 1:
expected value positive
→ HOLD

Candle 2:
expected value positive
→ HOLD

Candle 3:
expected value deteriorates
→ EXIT

Candle 4:
new SHORT opportunity
→ evaluate independently
```

The strategy must NOT blindly hold until a fixed time expires.

---

# 24. Probability Estimation — Phase 1

Do not start with a complex ML model.

First build an empirical probability engine.

For a defined market-state feature bucket:

```text
number_of_TP_first
number_of_SL_first
number_of_neither
```

Estimate:

```text
P(TP_FIRST)
P(SL_FIRST)
P(NEITHER)
```

with sample counts.

Always expose sample size.

A probability without sample size is insufficient.

Example:

```text
P(TP_FIRST) = 0.68
sample_size = 1,842
```

is meaningful.

```text
P(TP_FIRST) = 0.80
sample_size = 5
```

is not reliable.

---

# 25. Expected Value

For a simplified gross-return model:

```text
EV =
P(TP) * TP
-
P(SL) * SL
```

If NEITHER is possible, explicitly model its treatment.

Do not silently treat NEITHER as a win or loss.

For production evaluation, include:

- trading fees
- funding where applicable
- estimated slippage

after the gross model is validated.

---

# 26. Probability Thresholds

Do NOT arbitrarily declare:

```text
70% = buy
60% = hold
```

Thresholds must be researched.

The system should initially expose raw:

```text
p_tp
p_sl
p_neither
expected_value
sample_size
confidence/calibration information
```

A later decision layer can determine:

```text
LONG
SHORT
NO TRADE
```

based on validated thresholds.

---

# 27. Probability Calibration

If probability estimates are used for decisions, evaluate calibration.

For example:

Predicted probability bucket:

```text
50–55%
55–60%
60–65%
65–70%
70–75%
75–80%
```

Compare predicted probability with actual frequency.

A model claiming 70% should produce approximately 70% outcomes over sufficiently large comparable samples.

Do not call an uncalibrated score a probability.

---

# 28. Data Splitting

Use chronological splits.

Example:

```text
TRAIN       60%
VALIDATION  20%
TEST        20%
```

Exact dates must be recorded.

Never optimize parameters using the final test set.

The final test set must remain untouched until the strategy design is frozen.

---

# 29. Walk-Forward Validation

After the basic backtester works, implement walk-forward testing.

Conceptually:

```text
Train → Validate → Test
       slide window →
Train → Validate → Test
       slide window →
...
```

This is preferable to one lucky historical period.

---

# 30. Trading Costs

Backtests must eventually include:

- maker/taker fees
- slippage
- funding
- spread where relevant

First produce a gross result.

Then produce a net result.

Never report gross backtest performance as if it were executable profit.

---

# 31. Leverage and Risk Engine

Leverage is NOT a prediction feature.

The risk engine accepts:

```text
entry_price
exit_price
position_side
leverage
capital
position_size
fee_rate
funding
```

and calculates:

```text
underlying_return
leveraged_gross_return
fees
funding
leveraged_net_return
```

The system should support:

```text
1x
5x
10x
15x
20x
```

as configurable values.

Do not assume that higher leverage creates higher strategy edge.

Higher leverage increases both gains and losses and introduces liquidation risk.

Liquidation calculations must be isolated and explicitly modeled if later implemented.

---

# 32. Position Sizing

Do not initially implement automatic capital allocation.

The first version should report hypothetical returns.

Later, add a risk engine with:

- maximum account risk per trade
- maximum notional
- maximum leverage
- maximum daily loss
- maximum concurrent exposure

No live order placement until the research system has passed validation.

---

# 33. Backtest Metrics

Every backtest report must include:

- number of trades
- win rate
- loss rate
- neutral rate
- average win
- average loss
- expectancy
- profit factor
- cumulative return
- maximum drawdown
- Sharpe-like risk metric where appropriate
- Sortino-like metric where appropriate
- average holding time
- median holding time
- maximum consecutive losses
- fees
- funding
- slippage
- net return

Also compare against a simple baseline.

---

# 34. Baselines

The system must include simple baselines.

At minimum:

1. Buy-and-hold
2. Random entry with identical TP/SL framework
3. Simple S/R-only strategy

The purpose is to determine whether complexity adds value.

---

# 35. Ablation Testing

Every additional feature must be evaluated by ablation.

Example:

```text
Model A:
S/R only

Model B:
S/R + Volume

Model C:
S/R + Volume + Volatility

Model D:
S/R + Volume + Volatility + Structure

Model E:
all + MTF
```

Compare out-of-sample performance.

If a feature does not improve robustly, remove it.

---

# 36. Avoid Double Counting

Many features are derived from the same price information.

The system must avoid pretending that:

```text
RSI
MACD
Bollinger
moving average slope
```

are four independent pieces of evidence.

The initial model should deliberately remain close to raw market structure.

---

# 37. Signal Explainability

Every signal must be explainable.

Example:

```text
Signal: LONG

Reasons:
- Current price is near a historically reactive support zone.
- Support was tested 4 times.
- Recent rejection magnitude is above baseline.
- 4h structure is bullish.
- Current distance to support is 0.22 volatility units.
- Comparable historical cases show positive expectancy.

Statistics:
P(TP_FIRST): 0.67
P(SL_FIRST): 0.21
P(NEITHER): 0.12
Sample size: 1,842
Expected value: +0.41%
```

Never show only:

```text
LONG 82
```

without explaining what produced it.

---

# 38. Frontend MVP

The first frontend should show:

- symbol
- timeframe
- candlestick chart
- current price
- detected support zones
- detected resistance zones
- swing points
- market structure events
- current signal
- probability estimates
- expected value
- sample size
- TP/SL research parameters

Allow selecting:

```text
15m
1h
4h
1d
```

The chart must make zones visually understandable.

---

# 39. Historical Research UI

Provide a basic backtest panel:

```text
Symbol
Timeframe
Start date
End date

TP
SL

Pivot strength
Zone parameters

[Run Backtest]
```

Results:

```text
Trades
Win rate
Expectancy
Profit factor
MDD
Net return
Average holding time
```

Also show a trade list.

---

# 40. API Requirements

Initial endpoints:

```text
GET /health

GET /market/binance/klines
GET /analysis/swings
GET /analysis/zones
GET /analysis/current
POST /backtest/run
```

The exact request/response schemas should use Pydantic models.

---

# 41. Research Reproducibility

Every backtest must record:

```text
dataset identifier
symbol
timeframe
date range
parameters
code/version identifier where available
transaction-cost assumptions
timestamp of execution
```

A result must be reproducible.

---

# 42. Logging

Use structured logging.

Important events:

- data download
- missing candle detection
- analysis execution
- backtest execution
- parameter set
- errors

Do not log secrets.

---

# 43. Error Handling

The system must gracefully handle:

- Binance API errors
- rate limits
- network failure
- malformed candles
- missing data
- duplicate candles
- invalid parameters
- insufficient historical sample size

Never silently return an empty dataset as if the request succeeded.

---

# 44. Testing Requirements

At minimum, write unit tests for:

### Market data

- OHLC validation
- chronological sorting
- duplicate removal
- pagination

### Swings

- known synthetic swing sequences
- confirmation timing
- no future leakage

### Zones

- deterministic clustering
- interaction grouping
- repeated visits

### Outcomes

- TP first
- SL first
- neither
- same-candle ambiguity

### Backtest

- fees
- long return
- short return
- MFE
- MAE
- drawdown

Use synthetic deterministic data for critical logic.

---

# 45. Same-Candle TP/SL Ambiguity

This is a critical backtesting issue.

If one candle's:

```text
high >= TP
AND
low <= SL
```

then OHLC data alone does not reveal which boundary happened first.

Do NOT arbitrarily assume TP first.

The backtest must mark this as:

```text
AMBIGUOUS
```

or apply a documented conservative rule.

The default research behavior should be conservative and clearly documented.

---

# 46. Closed-Candle Rule

Signals based on candle data must only be generated after the relevant candle has closed unless the strategy explicitly supports intrabar data.

The first MVP uses closed candles.

Do not use the current unfinished candle as if it were complete.

---

# 47. Data Leakage Audit

Before trusting any backtest, inspect:

- swing confirmation timing
- zone creation timing
- zone interaction timing
- normalization calculations
- rolling statistics
- probability bucket creation
- train/test boundaries
- feature standardization
- outcome labeling

All rolling statistics must only use past information at the decision timestamp.

---

# 48. No Machine Learning Initially

Do not introduce neural networks or large ML models in MVP.

First establish whether a transparent empirical S/R-based framework has genuine predictive value.

Only consider ML later if:

```text
simple model
    ↓
validated edge
    ↓
ML can demonstrate robust incremental improvement
```

Otherwise remain simple.

---

# 49. Research Questions

The project should eventually answer these questions empirically:

1. Do historically reactive S/R zones predict short-term future movement?
2. Does repeated reaction increase predictive value?
3. Does recency matter?
4. Does volume around the zone improve prediction?
5. Does volatility-normalized distance improve prediction?
6. Does market structure improve S/R signals?
7. Does multi-timeframe agreement improve prediction?
8. Which TP/SL combinations have the best expectancy?
9. How quickly does signal quality decay?
10. When should a live position be exited because the expected value deteriorates?
11. Does dynamic re-evaluation outperform fixed holding periods?
12. Does each added feature improve out-of-sample performance after costs?

---

# 50. Development Phases

## Phase 1 — Data

Implement:

- Python project
- uv
- FastAPI
- Binance public data client
- Candle model
- pagination
- local dataset storage
- validation
- tests

Definition of done:

> Download a reliable BTCUSDT historical dataset and verify its integrity.

---

## Phase 2 — Support/Resistance Candidate Research Engine

Implement:

- independent A/B/C/D candidate detection and known_at timing
- fixed/original zone width experiments and adaptive extension point
- explicit interaction state machine and configurable exit separation
- trade-price bins and raw volume attachments
- first-touch LONG/SHORT hypothetical outcomes, censoring, MFE/MAE
- full configuration, dataset/code fingerprints and deterministic run identity
- fixed-schedule neutral controls with identical outcome definitions
- chronological research/validation/final-test boundaries, with final test locked
- deterministic synthetic tests and a small BTCUSDT smoke experiment

Definition of done:

> Identical data/configuration produces identical raw observations and results.
> Every candidate is causal. No winner, arbitrary score or edge is declared.
> Complete the tests and smoke report, then STOP before optimization or Phase 3.

---

## Phase 2.5 — Real Trades and Sanity Validation

- Official daily aggregate-trade ZIPs and published SHA256 checksums retained as raw sources.
- Separate normalized Parquet, integrity reports and derived Volume-at-Price artifacts.
- Validate IDs, duplicate records, ordering, timestamp units/range, positive price/quantity,
  archive CRC/checksum and detectable aggregate/constituent ID discontinuities.
- No sorting away problems, deduplication, gap repair or candle-volume substitution.
- Run existing D concentration rule at documented bin sizes and attach past-only volume
  to A/B/C candidates and interactions. Preserve exact configuration and hashes.
- CSV/JSON decision features, retrospective visit facts and future outcomes are separate.
- Self-contained HTML displays candles, candidate source/known_at, zones and later visits;
  detector toggles and an as-of clock expose causal availability.
- Deterministic earliest/repeated/overlap samples use no outcome labels.
- Complete existing and new tests, real-data checks and report suspicious behavior; STOP.

## Phase 3 — Deferred Research Review

The old mandatory clustering/volatility-zone plan is superseded. Further methods,
full historical trade acquisition, matched controls and statistical inference
require a separate research iteration. Phase 2 does not select parameters.

---

## Phase 4 — Future Outcome Extensions (Deferred)

Implement:

- TP/SL labeling
- first-touch outcome
- ambiguous candle handling
- MFE
- MAE
- multiple horizons
- multiple TP/SL configurations

Definition of done:

> The initial labeling foundation is already included in Phase 2. Any extensions
> remain outside this iteration.

---

## Phase 5 — Empirical Probability

Implement:

- comparable-case grouping
- TP probability
- SL probability
- neutral probability
- sample size
- calibration report

Definition of done:

> The system can say what happened historically for comparable market states.

---

## Phase 6 — Structure / Volume / Volatility

Add each feature independently.

Run ablation experiments after each addition.

Definition of done:

> We know whether each feature adds out-of-sample value.

---

## Phase 7 — Dynamic Position Logic

Implement:

```text
ENTER
HOLD
EXIT
```

based on validated probability/EV rules.

Definition of done:

> A position is re-evaluated after every closed candle.

---

## Phase 8 — Frontend

Implement:

- chart
- zones
- structure
- signal
- probabilities
- backtest dashboard
- trade history

---

## Phase 9 — Live Market Data

Only after historical validation.

Implement:

- live Binance WebSocket market data
- candle aggregation
- closed-candle event
- real-time analysis

No live orders yet.

---

## Phase 10 — Paper Trading

Run the strategy without real money.

Compare:

```text
predicted probabilities
vs
actual outcomes
```

for a meaningful live sample.

---

## Phase 11 — Risk Engine

Implement:

- leverage
- position sizing
- fees
- funding
- liquidation-risk calculations
- max-loss controls

---

## Phase 12 — Order Execution

Only after all previous phases are validated.

Live trading must be disabled by default.

---

# 51. Codex Operating Instructions

Codex must follow this workflow.

## Rule 1

Do not implement all phases at once.

Current authorized work is Phase 2.5 only; Phase 1 and Phase 2 are complete.

## Rule 2

After each phase:

1. implement,
2. run tests,
3. inspect failures,
4. fix failures,
5. document what was implemented,
6. stop and wait for approval before moving to the next major phase.

## Rule 3

Never silently change the strategy specification.

If an implementation choice materially changes strategy behavior:

> STOP and ask for confirmation.

## Rule 4

Do not introduce technical indicators that are not explicitly specified.

## Rule 5

Do not add ML.

## Rule 6

Do not add trading/order execution.

## Rule 7

Do not optimize parameters using the final test set.

## Rule 8

Do not use future information.

## Rule 9

Prefer transparent code over clever abstractions.

## Rule 10

Every important calculation must have tests.

---

# 52. First Codex Task

Historical Phase 1 task retained for reference; not the current task.

Tasks:

1. Create the repository structure.
2. Create the Python backend.
3. Configure uv.
4. Configure FastAPI.
5. Implement normalized Candle model.
6. Implement Binance public Futures Kline client.
7. Implement pagination.
8. Implement data validation.
9. Implement local dataset saving.
10. Add `/health`.
11. Add `GET /market/binance/klines`.
12. Write tests.
13. Run tests.
14. Run a small BTCUSDT historical data download.
15. Verify the downloaded data.
16. Update README with exact setup/run/test commands.

Do NOT implement:

- S/R
- scoring
- trading signals
- machine learning
- live trading
- leverage
- frontend

during Phase 1.

---

# 53. Phase 1 Acceptance Criteria

Phase 1 is complete only when:

```text
[ ] Project installs cleanly
[ ] FastAPI starts
[ ] /health works
[ ] Binance public Kline request works
[ ] Pagination works
[ ] Duplicate candles are handled
[ ] OHLC integrity is checked
[ ] Chronological ordering is guaranteed
[ ] Missing candles are detected
[ ] Data can be saved locally
[ ] Tests pass
[ ] README is complete
```

After this, stop.

Do not continue to Phase 2 automatically.

---

# 54. Definition of Success

The goal is NOT:

> maximize historical backtest return.

The goal is:

> discover whether a simple, interpretable, price-first S/R framework contains a robust, repeatable short-term predictive edge after realistic trading costs.

If the answer is no, the project must be able to demonstrate that clearly.

A strategy that earns less but remains robust out-of-sample is preferable to a spectacular but overfit backtest.

---

# 55. Final Design Principle

The entire project should continually ask:

> **"Can this complexity be removed without reducing genuine predictive power?"**

If yes, remove it.

The final system should be as simple as the data allows, not as complicated as the developer can make it.
