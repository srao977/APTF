# Adaptive Parametric Trading Framework --- v2

## 1. Purpose

This document defines a system architecture for applying an adaptive
parametric model to short-horizon financial-market trading.

The framework is intended to observe live market conditions, estimate an
evolving market state, produce bounded trading signals, apply
independent risk controls, and route approved orders to a broker or
execution venue.

This is an architecture document. Mathematical model definitions,
parameter-estimation methods, feature equations, statistical tests, and
training procedures belong in separate model-design and experiment
documents.

The central architectural principle is separation of responsibilities:

**Market observation -\> state/model inference -\> trading decision -\>
risk authorization -\> execution -\> outcome feedback**

The model does not directly place trades.

------------------------------------------------------------------------

## 2. Architectural Goals

The framework should support:

-   Short decision horizons measured in seconds or minutes.
-   Continuous ingestion of market observations.
-   Adaptive model state that can change as market behavior changes.
-   Multiple instruments and multiple prediction horizons.
-   Explicit BUY, SELL, HOLD, EXIT, or NO-ACTION decisions.
-   Independent risk controls that can veto any model decision.
-   Paper, shadow, and live execution modes.
-   Complete recording of signals, decisions, orders, fills, and
    outcomes.
-   Replay of historical market streams through the same decision
    pipeline.
-   Progressive addition of external signals without redesigning the
    execution system.
-   Safe degradation when data, models, or broker connectivity fail.

------------------------------------------------------------------------

## 3. High-Level Architecture

``` text
Market / External Data
        |
        v
+----------------------+
| Market Data Gateway  |
+----------------------+
        |
        v
+----------------------+
| Signal / State       |
| Engine               |
+----------------------+
        |
        v
+----------------------+
| Adaptive Parametric  |
| Model Engine         |
+----------------------+
        |
        v
+----------------------+
| Decision Engine      |
+----------------------+
        |
        v
+----------------------+
| Independent Risk     |
| Engine               |
+----------------------+
        |
        v
+----------------------+
| Execution Engine     |
+----------------------+
        |
        v
+----------------------+
| Broker / Venue       |
+----------------------+
        |
        v
 Orders, Fills, Positions
        |
        +-----------------------------+
                                      |
                                      v
                              +------------------+
                              | Outcome /        |
                              | Feedback Engine  |
                              +------------------+
                                      |
                                      v
                         State, Model & Analytics
```

The architecture deliberately prevents a model output from being treated
as an order.

------------------------------------------------------------------------

## 4. Market Data Gateway

### Responsibility

The Market Data Gateway is the boundary between external market-data
providers and the internal trading system.

It receives market observations and converts provider-specific messages
into a common internal format.

### Typical Inputs

Depending on the data service and experiment, inputs may include:

-   Last traded price
-   Bid and ask
-   Trade size
-   Quote size
-   Volume
-   OHLC bars
-   VWAP
-   Order-book information
-   Trading-session status
-   Exchange timestamps

External signals can later be added, such as index data, volatility
measures, interest rates, commodities, economic releases, or other
market instruments.

### Responsibilities

The gateway should:

-   Normalize symbols and instrument identifiers.
-   Normalize timestamps.
-   Detect stale data.
-   Detect gaps.
-   Reject malformed observations.
-   Maintain source-health information.
-   Publish normalized observations to downstream consumers.

The adaptive model should not contain vendor-specific market-data logic.

------------------------------------------------------------------------

## 5. Signal / State Engine

### Responsibility

The Signal / State Engine converts raw observations into the current
observable market state.

It is the bridge between raw market data and the adaptive model.

Examples of state information include:

-   Recent direction
-   Rate of movement
-   Change in rate of movement
-   Short-term volatility
-   Volume behavior
-   Distance from a reference level
-   Liquidity condition
-   Spread condition
-   Time-of-day context
-   Recent local behavior

The exact definitions are model concerns and should not be embedded in
the system architecture.

### Output

The engine emits a versioned state snapshot.

Example:

``` text
Instrument: SPY
Observation time: 10:31:20.000
State version: 184221

Price state: VALID
Liquidity state: NORMAL
Volatility state: EXPANDING
Data freshness: 42 ms

Feature set version: F006
```

Every downstream model result must identify the state snapshot from
which it was produced.

------------------------------------------------------------------------

## 6. Adaptive Parametric Model Engine

### Responsibility

The Adaptive Parametric Model Engine evaluates the current state and
produces a machine-readable assessment of possible near-term market
behavior.

It owns:

-   Model versions
-   Parameter versions
-   Current adaptive parameter state
-   Prediction horizons
-   Prediction thresholds
-   Confidence and quality measures
-   Model health

It does **not** own:

-   Account balances
-   Position limits
-   Order placement
-   Broker connectivity
-   Trading permissions

### Example Output Contract

``` text
Instrument: SPY
Model version: AP-001
State version: 184221
Generated: 10:31:20.025

Horizon: 5 minutes

Up-threshold assessment: AVAILABLE
Down-threshold assessment: AVAILABLE
Expected-move assessment: AVAILABLE

Confidence: 0.74
Model state: VALID
Regime label: MOMENTUM_EXPANSION
```

The numerical content of these fields is defined by the model
specification rather than this architecture.

### Multiple Horizons

One model invocation may produce assessments for several horizons, for
example:

-   1 minute
-   3 minutes
-   5 minutes
-   15 minutes

This allows the decision layer to distinguish a very short-lived event
from a broader market movement.

------------------------------------------------------------------------

## 7. Decision Engine

### Responsibility

The Decision Engine converts model assessments into a proposed trading
action.

Possible outputs include:

-   BUY
-   SELL
-   HOLD
-   EXIT
-   REDUCE
-   NO ACTION

The Decision Engine is where trading policy resides.

The model answers:

> What does the current market state imply?

The Decision Engine answers:

> Given that assessment, should the trading strategy propose an action?

### Decision Context

The engine can consider:

-   Model state
-   Model confidence
-   Forecast horizon
-   Current position
-   Existing pending orders
-   Estimated transaction cost
-   Market liquidity
-   Spread
-   Strategy-specific entry conditions
-   Strategy-specific exit conditions
-   Signal age

### Proposed Action

A decision is still **not an executable order**.

Example:

``` text
Decision ID: D-582199
Instrument: SPY
Action: BUY
Decision horizon: 5 minutes
Signal age: 18 ms
Requested exposure: SMALL
Decision status: PROPOSED
```

The proposal is passed to the Risk Engine.

------------------------------------------------------------------------

## 8. Independent Risk Engine

### Responsibility

The Risk Engine is an independent authorization boundary.

It can approve, reduce, defer, or reject any proposed action.

The Risk Engine must remain capable of blocking trades even when the
adaptive model and Decision Engine are functioning normally.

### Typical Controls

Controls can include:

-   Maximum position size
-   Maximum order size
-   Maximum instrument exposure
-   Maximum total exposure
-   Maximum daily loss
-   Maximum strategy loss
-   Maximum number of open positions
-   Maximum order rate
-   Duplicate-order detection
-   Stale-signal rejection
-   Stale-market-data rejection
-   Excessive-spread rejection
-   Abnormal-volatility protection
-   Trading-session restrictions
-   Broker connectivity health
-   Account state
-   Manual trading halt
-   Global kill switch

### Output

``` text
Decision ID: D-582199
Risk status: APPROVED
Approved exposure: SMALL
Authorization ID: R-44182
```

or:

``` text
Decision ID: D-582199
Risk status: REJECTED
Reason: DAILY_LOSS_LIMIT
```

The Execution Engine accepts only risk-authorized actions.

------------------------------------------------------------------------

## 9. Execution Engine

### Responsibility

The Execution Engine converts an authorized trading action into
broker-compatible orders and manages the order lifecycle.

It owns:

-   Order creation
-   Broker API communication
-   Order identifiers
-   Submission
-   Cancellation
-   Replacement
-   Acknowledgement
-   Partial fills
-   Complete fills
-   Rejections
-   Position reconciliation

It does not reinterpret the model.

### Order Lifecycle

``` text
AUTHORIZED
    |
    v
CREATED
    |
    v
SUBMITTED
    |
    v
ACKNOWLEDGED
    |
    +------> PARTIALLY_FILLED
    |              |
    |              v
    +----------> FILLED
    |
    +----------> CANCELLED
    |
    +----------> REJECTED
```

Every transition should be persisted.

------------------------------------------------------------------------

## 10. Broker / Execution Venue Adapter

Broker-specific integration should sit behind an adapter.

This prevents the rest of the framework from depending on one broker
API.

The adapter translates internal commands such as:

``` text
BUY SPY
quantity = ...
order_type = ...
limit = ...
```

into the broker's required API format.

It also converts broker responses back into standard internal events.

This allows a paper broker, simulator, and live broker to expose the
same internal interface.

------------------------------------------------------------------------

## 11. Outcome and Feedback Engine

### Responsibility

The Outcome / Feedback Engine determines what happened after a decision
and makes the result available to analytics and adaptive-model
processes.

It records:

-   Entry decision
-   Actual execution price
-   Fill latency
-   Slippage
-   Position evolution
-   Exit decision
-   Exit execution
-   Realized result
-   Market behavior after the original signal
-   Whether the forecast event occurred
-   Risk interventions

This creates a closed observational loop:

``` text
Observe
  ->
Estimate state
  ->
Generate model assessment
  ->
Decide
  ->
Authorize risk
  ->
Execute
  ->
Observe outcome
  ->
Adapt / evaluate
```

The feedback system should not silently modify a live model. Model
adaptation must follow an explicitly defined update policy.

------------------------------------------------------------------------

## 12. Time Boundaries

The architecture should not assume that market sampling, model
evaluation, prediction, and execution all occur at the same frequency.

For example:

``` text
Market observations     continuous / event driven
State update            1 second
Model evaluation        5 seconds
Forecast horizons       1, 3, 5, 15 minutes
Decision evaluation     event driven
Risk evaluation         every proposed action
Execution               immediately after authorization
```

These are configuration examples, not fixed requirements.

The separation is important because the model may observe the market
much more frequently than it trades.

------------------------------------------------------------------------

## 13. Event-Driven Operation

The system should support event-driven processing.

Important events can include:

``` text
MARKET_OBSERVATION
STATE_UPDATED
MODEL_ASSESSMENT_CREATED
TRADE_DECISION_PROPOSED
RISK_APPROVED
RISK_REJECTED
ORDER_CREATED
ORDER_SUBMITTED
ORDER_ACKNOWLEDGED
ORDER_PARTIALLY_FILLED
ORDER_FILLED
ORDER_CANCELLED
POSITION_CHANGED
EXIT_PROPOSED
MODEL_STATE_CHANGED
DATA_STALE
TRADING_HALTED
```

This makes the architecture suitable for both real-time operation and
historical replay.

------------------------------------------------------------------------

## 14. Trading Modes

The same architecture should support several operating modes.

### Historical Replay

Previously recorded market data is replayed through the state, model,
decision, and risk components.

No broker is involved.

Purpose:

-   Model development
-   Walk-forward evaluation
-   Strategy evaluation
-   Regression testing

### Paper Trading

The system operates on current market data but orders are routed to a
simulated or broker-provided paper environment.

Purpose:

-   End-to-end integration
-   Order lifecycle testing
-   Position accounting
-   Strategy behavior

### Shadow Live

The complete production pipeline runs against live data.

The system creates decisions and would-be orders, but the execution
boundary prevents transmission to a live broker.

Purpose:

-   Measure real-time latency
-   Measure signal age
-   Validate market-data reliability
-   Estimate live slippage
-   Detect operational faults

### Limited Live

Orders are transmitted using deliberately restricted capital and risk
limits.

Purpose:

-   Validate real execution behavior
-   Measure fills and slippage
-   Compare live outcomes with shadow assumptions

### Scaled Live

Exposure can increase only after predefined operational and performance
criteria are satisfied.

------------------------------------------------------------------------

## 15. Safety and Failure Handling

Short-horizon automated trading requires explicit failure states.

The system should default to **no new trade** when critical dependencies
are uncertain.

Examples:

### Stale Market Data

``` text
Market data stale
    ->
Invalidate state
    ->
Invalidate model assessment
    ->
Block new decisions
```

### Model Failure

``` text
Model unavailable
    ->
Decision engine receives MODEL_INVALID
    ->
No new model-driven trade
```

### Risk Engine Failure

``` text
Risk engine unavailable
    ->
Execution authorization unavailable
    ->
No order submission
```

### Broker Failure

``` text
Broker connection lost
    ->
Stop new submissions
    ->
Reconcile open orders and positions
    ->
Raise operational alert
```

### Global Kill Switch

The framework should support an immediate trading halt independent of
the model.

------------------------------------------------------------------------

## 16. State and Audit Storage

Every important stage should be reproducible.

Persist at least:

### Market Observation Record

-   Instrument
-   Source
-   Timestamp
-   Price / quote information
-   Sequence identifier

### State Record

-   State version
-   Feature-set version
-   Input observation range
-   Generation timestamp

### Model Assessment Record

-   Model version
-   Parameter version
-   State version
-   Horizon
-   Assessment
-   Confidence
-   Generation timestamp

### Decision Record

-   Decision ID
-   Model assessment reference
-   Proposed action
-   Decision policy version
-   Timestamp

### Risk Record

-   Decision ID
-   Risk-policy version
-   Approval/rejection
-   Approved exposure
-   Reason codes

### Execution Record

-   Internal order ID
-   Broker order ID
-   Submission time
-   Acknowledgement time
-   Fill records
-   Execution prices
-   Status

### Outcome Record

-   Decision ID
-   Position result
-   Forecast outcome
-   Slippage
-   Holding duration
-   Exit reason

This provides a complete chain:

``` text
Market observation
      |
      v
State
      |
      v
Model assessment
      |
      v
Decision
      |
      v
Risk authorization
      |
      v
Order
      |
      v
Fill
      |
      v
Outcome
```

------------------------------------------------------------------------

## 17. Model Versioning

A live adaptive system needs two different concepts:

### Model Definition

The stable definition of the model, features, and interpretation.

Example:

``` text
AP_MODEL_VERSION = 1.3
FEATURE_VERSION = F006
```

### Adaptive State

The current estimated state or parameters produced by that model.

Example:

``` text
PARAMETER_STATE_VERSION = 849221
STATE_TIME = 10:31:20
```

The distinction allows the parameters to evolve rapidly without
pretending that a new software/model release occurs every few seconds.

Every decision should be traceable to both.

------------------------------------------------------------------------

## 18. Separation of Adaptation and Execution

The model may adapt rapidly.

The execution policy should not automatically adapt merely because the
model parameters changed.

These should remain separate:

``` text
Adaptive Model
      |
      | assessment
      v
Fixed / controlled trading policy
      |
      v
Independent risk controls
```

Changes to decision thresholds, risk limits, execution behavior, or
position-sizing rules should be controlled configuration changes rather
than emergent model behavior unless a later architecture explicitly
permits otherwise.

------------------------------------------------------------------------

## 19. Initial Experimental Deployment

A practical first implementation can remain deliberately small.

### Instrument

One highly liquid market instrument.

### Market Input

Price, bid/ask, volume, and short interval bars.

### Horizons

A small set such as:

-   1 minute
-   3 minutes
-   5 minutes

### Model

One adaptive parametric model.

### Decisions

-   BUY
-   SELL
-   HOLD
-   EXIT

### Execution

Paper or shadow mode only.

### Storage

Persist every state, assessment, decision, and simulated order.

The first objective is not maximizing profit.

It is proving that the complete system can repeatedly:

1.  observe a market state,
2.  generate a timely adaptive assessment,
3.  translate it into a controlled decision,
4.  apply independent risk checks,
5.  execute or simulate execution,
6.  measure the outcome,
7.  reproduce exactly why the action occurred.

------------------------------------------------------------------------

## 20. Future Expansion

Once the single-instrument framework is stable, the architecture can
expand without changing its fundamental boundaries.

Possible additions include:

### Additional Instruments

-   Broad equity indexes
-   Sector instruments
-   Individual equities
-   Treasury instruments
-   Commodities
-   Currency markets

### Additional Signal Producers

-   Volatility measures
-   Related-market movement
-   Interest rates
-   Economic-event signals
-   Market breadth
-   Order-flow signals
-   News/event signals

### Multiple Models

Several models can publish assessments to a higher-level decision
process while retaining the same Risk and Execution Engines.

### Market-State Service

The adaptive parameter state can eventually become a reusable system
service consumed by multiple strategies rather than belonging to a
single trading strategy.

------------------------------------------------------------------------

## 21. Architectural Principle

The adaptive parametric model should be treated as a **market-state
intelligence component**, not as the trading system itself.

The complete framework is:

``` text
OBSERVE
   |
   v
ESTIMATE MARKET STATE
   |
   v
ASSESS FORWARD CONDITIONS
   |
   v
PROPOSE ACTION
   |
   v
AUTHORIZE RISK
   |
   v
EXECUTE
   |
   v
MEASURE OUTCOME
   |
   v
FEEDBACK
```

This separation allows the model to evolve independently of brokerage,
execution, account management, and risk infrastructure.

It also provides the central safety boundary of the architecture:

**No adaptive model output becomes a market order without an independent
trading decision and risk authorization.**

------------------------------------------------------------------------

## 22. Two Interconnected Model Systems

The production design uses two interconnected systems with different
responsibilities and different operating timescales.

### Adaptive Learning System

The Adaptive Learning System discovers and maintains the validated
intelligence used by the real-time system.

It consumes:

-   Historical market observations
-   Accumulated live observations
-   Outcomes from executed trades
-   Outcomes from rejected/no-trade opportunities
-   Market-state and regime histories
-   Execution and slippage observations

It can estimate and validate:

-   Adaptive parameters
-   Parameter interactions
-   Nonlinear response functions
-   Candidate polynomial degree
-   Market regimes
-   Time-window behavior
-   Reward/risk behavior
-   Stability across rolling windows
-   Model confidence and eligibility criteria

Its output is a controlled, versioned model state or parameter snapshot
suitable for production use.

### Real-Time Decision System

The Real-Time Decision System consumes live market observations and
validated intelligence from the Adaptive Learning System.

Its responsibility is to determine what the current market state means
now and whether a tradable opportunity exists.

It performs:

-   Trigger detection
-   Current-state calculation
-   Regime identification
-   Fast model inference
-   Opportunity evaluation
-   Reward/risk and horizon selection
-   Trading eligibility
-   BUY / SELL / HOLD / EXIT proposal

The real-time system does not perform large parameter-estimation
experiments while attempting to trade.

### Bidirectional Relationship

``` text
             ADAPTIVE LEARNING SYSTEM
                       |
                       | validated model /
                       | parameters / regimes
                       v
             REAL-TIME DECISION SYSTEM
                       |
                       | observations /
                       | decisions / outcomes
                       v
             FEEDBACK / OUTCOME STORE
                       |
                       +-------------------->
                         ADAPTIVE LEARNING
```

The forward path carries **validated intelligence**.

The return path carries **observations and outcomes**.

------------------------------------------------------------------------

## 23. Trigger Engine

A Trigger Engine provides an inexpensive first-pass scan across the
market universe.

A trigger means:

> A market condition has changed enough to justify deeper evaluation.

A trigger is **not** automatically a BUY or SELL signal.

Possible triggers include:

-   Volatility expansion or contraction
-   Unusual volume
-   Rapid price displacement
-   Price velocity change
-   Price acceleration
-   Spread or liquidity change
-   Correlated-market movement
-   Scheduled market events
-   Unscheduled external perturbations

Example:

``` text
VOLATILITY EXPANSION
        |
        v
TRIGGER = YES
        |
        v
STATE / REGIME ANALYSIS
        |
        v
OPPORTUNITY ANALYSIS
        |
        +----> TRADE CANDIDATE
        |
        +----> NO TRADE
```

This allows a large universe of instruments to be monitored cheaply
while deeper adaptive inference is concentrated on instruments
experiencing potentially meaningful perturbations.

------------------------------------------------------------------------

## 24. Volatility as State, Trigger, and Trade Geometry

Volatility has three distinct architectural roles.

### State / Regime Input

Volatility helps describe the current market condition.

Examples:

-   Quiet
-   Normal
-   Expanding
-   Contracting
-   Directional high volatility
-   Chaotic high volatility

### Trigger

A meaningful volatility change can cause immediate re-evaluation of an
instrument.

Volatility alone does not determine trade direction.

### Opportunity Geometry

Volatility affects whether a proposed stop distance, reward target, and
time horizon are realistic for the current market state.

A stop that is appropriate in a quiet regime may sit inside ordinary
market noise during a volatile regime.

Therefore volatility contributes to the Opportunity Engine rather than
being treated only as a directional feature.

------------------------------------------------------------------------

## 25. Opportunity Engine

The Opportunity Engine sits between adaptive inference and the trading
Decision Engine.

Updated flow:

``` text
Market Universe
      |
      v
Trigger Engine
      |
      v
State / Regime Engine
      |
      v
Adaptive Parametric Inference
      |
      v
Opportunity Engine
      |
      v
Decision Engine
      |
      v
Risk Engine
      |
      v
Execution Engine
```

The Opportunity Engine evaluates whether the current state offers a
sufficiently attractive trade structure.

It considers jointly:

-   Direction
-   Risk boundary
-   Reward multiple
-   Time horizon
-   Model confidence
-   Current regime
-   Liquidity and spread
-   Estimated transaction costs
-   Signal age

It should not assume a fixed reward/risk ratio.

------------------------------------------------------------------------

## 26. Variable Reward-to-Risk

A 5:1 reward-to-risk requirement can be useful in some conditions, but
it should not be a permanent architectural constant.

The appropriate reward multiple can vary with market state.

The system can evaluate candidate opportunities such as:

``` text
2R opportunity
3R opportunity
4R opportunity
5R opportunity
```

and determine which, if any, is supported by the current state.

For example:

``` text
Current regime: VOLATILE_DIRECTIONAL

2R eligibility: HIGH
3R eligibility: HIGH
4R eligibility: MODERATE
5R eligibility: LOW

Selected opportunity: 3R
```

The objective is therefore not:

> Always find a 5:1 trade.

It is:

> Find the best sufficiently supported reward/risk opportunity for the
> current market state and available time horizon.

Risk boundary, reward multiple, and time horizon should all be treated
as configurable or state-dependent quantities.

------------------------------------------------------------------------

## 27. Target-Before-Stop Event Model

For short-horizon trading, the real-time system can frame an opportunity
as a boundary event.

For a proposed direction, risk boundary, reward target, and horizon, the
system evaluates three possible outcomes:

``` text
TARGET FIRST
STOP FIRST
NEITHER WITHIN HORIZON
```

This is more useful to the execution architecture than a simple UP/DOWN
forecast.

The Opportunity Engine can evaluate several candidate reward multiples
and horizons using the same current market state.

Example:

``` text
Horizon     Candidate
---------------------
3 min       2R
5 min       2R / 3R
10 min      3R / 4R
15 min      3R / 4R / 5R
```

The exact values are model and strategy configuration, not architectural
constants.

------------------------------------------------------------------------

## 28. Nonlinear and N-Degree Parametric Responses

The architecture must not assume one parameter per observed signal or a
permanently linear relationship.

A signal can have:

-   A linear response
-   A nonlinear response
-   Multiple fitted coefficients
-   A polynomial response of selected degree
-   Interactions with other signals

Examples of candidate signal families include:

-   Volatility
-   Momentum
-   Price velocity
-   Acceleration
-   Volume behavior
-   Liquidity
-   Spread
-   Distance from reference state

The Adaptive Learning System is responsible for determining whether
additional model complexity produces stable forward improvement.

The Real-Time Decision System simply evaluates the currently approved
model structure.

Model complexity must not be increased solely because it improves
historical fit.

------------------------------------------------------------------------

## 29. Stability Rather Than Aggregate Profit Selection

Time windows and market regimes should not be selected merely because
they produced the largest historical aggregate profit.

The framework should instead emphasize whether a behavior remains useful
across multiple rolling or forward windows.

Examples of questions for the Adaptive Learning System include:

-   Does a particular opportunity type remain effective across many
    periods?
-   Is the observed result dominated by one unusual market event?
-   Does the same parameter structure remain useful in different months?
-   Does the relationship survive untouched forward evaluation?
-   Is the behavior specific to a time-of-day regime?
-   Is the apparent time effect actually explained by volatility,
    volume, liquidity, or another state variable?

Time-of-day can therefore begin as a regime descriptor and later be
decomposed into the underlying market conditions that make that period
distinctive.

------------------------------------------------------------------------

## 30. Three Adaptation Timescales

The framework should distinguish at least three timescales.

### Fast --- Seconds

The Real-Time Decision System updates current observations and state.

Examples:

-   Volatility changed
-   Volume changed
-   Price velocity changed
-   Spread changed
-   Trigger fired

No large model refit occurs.

### Medium --- Minutes to Hours

The system can identify a regime change and select among already
validated model/parameter states.

Example:

``` text
NORMAL
   ->
VOLATILE_DIRECTIONAL
```

A validated parameter configuration appropriate to that regime can
become active without running a full optimization.

### Slow --- Hours to Days or Longer

The Adaptive Learning System can determine whether the underlying
relationships themselves have changed.

Activities may include:

-   Parameter re-estimation
-   Interaction testing
-   Polynomial-degree testing
-   Stability analysis
-   Walk-forward validation
-   Candidate-model promotion

This prevents expensive research computations from becoming part of the
real-time execution path.

------------------------------------------------------------------------

## 31. Real-Time Feedback

The Real-Time Decision System continuously generates new evidence for
the Adaptive Learning System.

Feedback must contain more than trade profit or loss.

For every evaluated opportunity, record the subsequent market trajectory
where practical.

Examples include:

-   Target reached
-   Stop reached
-   Which boundary occurred first
-   Time to target
-   Time to stop
-   Maximum favorable excursion
-   Maximum adverse excursion
-   Volatility after decision
-   Directional persistence after decision
-   Actual spread
-   Actual slippage
-   Execution latency
-   Exit reason

This provides information about whether the original state assessment
was useful and whether a different reward/risk or horizon would have
been preferable.

------------------------------------------------------------------------

## 32. Learn From No-Trade Decisions

The feedback system must also follow opportunities that were rejected.

The learning dataset should distinguish:

``` text
TRADED + SUCCESS
TRADED + FAILURE

REJECTED + WOULD HAVE SUCCEEDED
REJECTED + CORRECTLY REJECTED
```

Without rejected-opportunity outcomes, the learning system would observe
only situations that the existing decision policy already chose to
trade.

That would make it difficult to identify missed opportunities or overly
restrictive eligibility rules.

------------------------------------------------------------------------

## 33. Counterfactual Reward/Risk Observation

When a trade uses one reward target, the system should continue
observing the subsequent market trajectory so that alternative
reward/risk outcomes can be evaluated.

For example:

``` text
1R reached: YES
2R reached: YES
3R reached: YES
4R reached: YES
5R reached: NO

Maximum favorable excursion: 4.3R
Maximum adverse excursion:   0.4R
```

The Adaptive Learning System can use this information to determine
whether different market states support different reward multiples.

The production system should not need to place five separate trades to
learn the outcomes of five candidate reward targets.

------------------------------------------------------------------------

## 34. Controlled Model Promotion

Real-time feedback should not immediately and silently modify the
production model.

The initial promotion path should be controlled:

``` text
Live observations
       |
       v
Outcome Store
       |
       v
Accumulated evidence
       |
       v
Adaptive estimation
       |
       v
Forward / stability validation
       |
       v
Candidate model snapshot
       |
       v
Promotion criteria
       |
       v
Production model
```

This provides a feedback loop without allowing a single unusual
observation to destabilize live trading behavior.

Future versions may permit selected parameters to adapt more rapidly
after their stability and safety have been demonstrated.

------------------------------------------------------------------------

## 35. Updated Production Architecture

The resulting v2 production architecture is:

``` text
                       LEARNING / VALIDATION PLANE

Historical Data -------------------------------+
                                               |
Accumulated Live Observations -----------------+
                                               |
Executed Trade Outcomes -----------------------+
                                               |
Rejected Opportunity Outcomes ----------------+
                                               |
                                               v
                                  +---------------------------+
                                  | Adaptive Learning System  |
                                  |                           |
                                  | Parameters                |
                                  | Nonlinear structure       |
                                  | Interactions              |
                                  | Regimes                   |
                                  | Stability                 |
                                  | R:R / horizon behavior    |
                                  +-------------+-------------+
                                                |
                                      validated snapshots
                                                |
                                                v

                         REAL-TIME PLANE

Market Universe
      |
      v
+------------------+
| Market Data      |
| Gateway          |
+--------+---------+
         |
         v
+------------------+
| Trigger Engine   |
+--------+---------+
         |
         v
+------------------+
| State / Regime   |
| Engine           |
+--------+---------+
         |
         v
+---------------------------+
| Adaptive Parametric       |
| Inference                 |
+-------------+-------------+
              |
              v
+---------------------------+
| Opportunity Engine        |
| R:R x Horizon             |
+-------------+-------------+
              |
              v
+---------------------------+
| Decision Engine           |
+-------------+-------------+
              |
              v
+---------------------------+
| Independent Risk Engine   |
+-------------+-------------+
              |
              v
+---------------------------+
| Execution Engine          |
+-------------+-------------+
              |
              v
+---------------------------+
| Broker / Venue            |
+-------------+-------------+
              |
              v
       Orders / Fills /
       Positions / Outcomes
              |
              v
+---------------------------+
| Outcome / Feedback Store  |
+-------------+-------------+
              |
              +------------------------------>
                         Learning Plane
```

------------------------------------------------------------------------

## 36. v2 Architectural Principle

The v2 framework separates **discovery**, **real-time interpretation**,
**opportunity construction**, **risk authorization**, and **execution**.

The Adaptive Learning System asks:

> What relationships and parameter structures have demonstrated stable
> forward value?

The Real-Time Decision System asks:

> What state is the market in now?

The Opportunity Engine asks:

> Given that state, what direction, reward/risk structure, and time
> horizon are sufficiently supported?

The Decision Engine asks:

> Should the strategy propose action?

The Risk Engine asks:

> Is the proposed exposure permitted?

The Execution Engine asks:

> How should the authorized action be transmitted and managed?

The feedback path asks:

> What actually happened, including what happened to opportunities we
> did not trade?

The resulting closed-loop architecture is:

``` text
OBSERVE
   |
   v
TRIGGER
   |
   v
ESTIMATE CURRENT STATE
   |
   v
APPLY VALIDATED ADAPTIVE MODEL
   |
   v
CONSTRUCT R:R x TIME OPPORTUNITY
   |
   v
DECIDE
   |
   v
AUTHORIZE RISK
   |
   v
EXECUTE
   |
   v
OBSERVE OUTCOME
   |
   v
LEARN / VALIDATE
   |
   +---------------------> future validated model state
```

The core production safety boundary remains:

**No adaptive model output becomes a market order without an explicit
trading decision and independent risk authorization.**
