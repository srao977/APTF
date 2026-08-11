# Adaptive Parametric Trading Framework --- v2

## Document Organization

The framework is organized conceptually into two major systems:

**Section A — Adaptive Learning System** covers research, learning, parameter estimation, nonlinear structure, state-transition learning, stability, validation, and controlled model promotion.

**Section B — Real-Time Trading System** covers live market data, triggers, current state, predictive look-ahead, opportunity construction, decision, risk, execution, broker integration, and feedback.

The existing numbered sections remain detailed component specifications. The consolidated sections at the end capture the current system boundaries and implementation decisions.

---

# Part I — Conceptual Framework

This part defines the system ontology, operating principles, terminology, and architectural boundaries. It answers **what the system means and what its major entities are** before committing to implementation.

The conceptual artifacts include:

- Adaptive Learning System
- Real-Time Trading System
- Perturbation and Trigger
- Current State and Regime
- Adaptive Parameters and State Transitions
- Forward State and predictive look-ahead
- Return Shape
- Return Field
- Trading Envelope
- Capturability
- Opportunity and Opportunity Lifetime
- Reward/Risk and horizon
- Decision
- Independent Risk Authorization
- Execution Policy
- Position Lifecycle
- Outcome / Feedback
- Model Snapshot and controlled promotion
- Performance Envelope
- Learning States: Discovery, Maintenance, Re-adaptation

The existing numbered framework sections below remain the detailed conceptual record.



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

---

## 37. Current-State and Predictive Look-Ahead

The real-time system should answer two separate questions at every decision point:

1. **What conditions are present now?**
2. **Given those conditions and all information available now, how are those conditions likely to evolve over the relevant future horizon?**

The second question is a predictive look-ahead. It must not be confused with prohibited backtest look-ahead, where future information is accidentally used to reconstruct a past decision.

### Point-in-Time Rule

For any decision at time `t`, every observation, parameter state, model snapshot, and derived feature used by the system must have been available at or before `t`.

Historical replay must enforce the same rule.

Predictive look-ahead is therefore:

```text
information available at t
        |
        v
estimate possible states at t + h
```

and never:

```text
future information
        |
        v
retroactively improve decision at t
```

---

## 38. Forward State Engine

Add a Forward State Engine between Adaptive Parametric Inference and the Opportunity Engine.

Updated real-time path:

```text
Market Universe
      |
      v
Trigger Engine
      |
      v
Current State / Regime Engine
      |
      v
Adaptive Parametric Inference
      |
      v
Forward State Engine
      |
      v
Opportunity Engine
R:R x Time
      |
      v
Decision Engine
      |
      v
Risk Engine
      |
      v
Execution Policy Engine
      |
      v
Broker Adapter
```

### Responsibility

The Forward State Engine estimates how the current market state may evolve over one or more future horizons.

It should not be limited to predicting an exact future price.

It can estimate forward behavior such as:

- Directional continuation
- Directional weakening
- Reversal
- Sideways/indeterminate behavior
- Volatility expansion
- Volatility contraction
- Volume persistence or decay
- Liquidity deterioration or improvement
- Signal persistence or decay
- Probability of reaching candidate reward boundaries
- Probability of reaching the risk boundary first

The output should represent uncertainty rather than assume one deterministic future.

---

## 39. State and State Transition

The architecture should distinguish between two related forms of intelligence.

### Current-State Intelligence

Describes what the market looks like now.

Examples:

```text
Volatility: EXPANDING
Volume: ACCELERATING
Price velocity: POSITIVE
Acceleration: POSITIVE
Liquidity: GOOD
Spread: NORMAL
Regime: DIRECTIONAL
```

### Transition Intelligence

Describes how a state with these characteristics has demonstrated a tendency to evolve.

Conceptually:

```text
CURRENT STATE
      |
      v
STATE TRANSITION MODEL
      |
      v
POSSIBLE FUTURE STATES
```

The Adaptive Learning System should therefore be capable of learning both:

- Parameters that characterize the present state.
- Parameters that characterize transitions from one state to another.

The Real-Time Decision System evaluates the approved state and transition structures against live observations.

---

## 40. Forward State Distribution

The Forward State Engine should support multiple possible future states rather than emit only a single prediction.

Example:

```text
CURRENT STATE
     |
     +----> directional continuation
     |
     +----> weak continuation
     |
     +----> sideways / signal decay
     |
     +----> reversal
```

Each branch can carry a model-derived likelihood or confidence assessment.

The Opportunity Engine can then determine whether the distribution of possible future states supports a trade.

This allows the system to distinguish between:

```text
Current state looks favorable
```

and:

```text
Current state looks favorable
AND
its likely forward evolution supports a tradable opportunity
```

---

## 41. Multiple Forward Horizons

The Forward State Engine should be capable of evaluating several future horizons.

Illustrative horizons could include:

```text
+1 minute
+3 minutes
+5 minutes
+10 minutes
+15 minutes
```

These are not fixed architectural constants.

The relevant horizon can depend on:

- Trigger type
- Current volatility
- Signal strength
- Market regime
- Instrument behavior
- Expected signal lifetime
- Candidate reward/risk structure

A single current state can therefore produce different forward assessments at different horizons.

Example:

```text
+1m   continuation: HIGH
+3m   continuation: HIGH
+5m   continuation: MODERATE
+10m  continuation: LOW
+15m  reversal risk: ELEVATED
```

---

## 42. Adaptive Opportunity Lifetime

The system should not assume every signal has the same useful lifetime.

The Forward State Engine can estimate the period over which the current perturbation or state remains sufficiently supportive.

Example:

```text
Signal detected: 10:31:42

Forward support:
+1m   HIGH
+2m   HIGH
+3m   HIGH
+4m   MODERATE
+5m   MODERATE
+6m   LOW
+7m   VERY LOW
```

The Opportunity Engine can interpret this as an approximately four- to five-minute opportunity rather than forcing a predetermined holding period.

This connects forward-state estimation directly to:

- Entry timing
- Reward target
- Risk boundary
- Holding horizon
- Exit timing

---

## 43. Forward Volatility

Volatility should be evaluated in both present-state and forward-state terms.

The Trigger Engine may observe:

```text
VOLATILITY EXPANSION
```

The Forward State Engine then asks whether that expansion is likely to:

- Continue
- Stabilize
- Contract
- Become chaotic

A current volatility trigger can therefore be rejected if the forward state indicates rapid decay or unfavorable microstructure.

Conversely, a moderate current volatility state may become more interesting if forward-state intelligence indicates an emerging expansion.

This reinforces the distinction:

```text
TRIGGER
   !=
ENTRY
```

---

## 44. Look-Ahead and Reward/Risk Selection

The Opportunity Engine should use forward-state information when selecting reward/risk and time geometry.

Conceptually:

```text
CURRENT STATE
      |
      v
FORWARD STATE DISTRIBUTION
      |
      v
EXPECTED OPPORTUNITY LIFETIME
      |
      v
CANDIDATE R:R x HORIZON
      |
      v
SELECT / REJECT
```

A shorter predicted state lifetime may support a smaller reward target.

A stronger and more persistent forward state may support a larger reward multiple.

The system should therefore avoid selecting reward/risk independently of the expected future state.

---

## 45. Prediction Feedback

Every forward-state assessment creates a measurable prediction that can be returned to the Adaptive Learning System.

For a decision at time `t`, store:

```text
STATE AT t
      |
      v
PREDICTED STATE AT t+h
      |
      v
ACTUAL STATE AT t+h
      |
      v
PREDICTION ERROR / OUTCOME
      |
      v
ADAPTIVE LEARNING SYSTEM
```

Feedback should include both trading outcomes and state-prediction outcomes.

Examples:

- Was directional continuation predicted correctly?
- Did volatility remain elevated?
- Did the signal decay when expected?
- Did reversal occur earlier than expected?
- Was the predicted opportunity lifetime accurate?
- Which reward boundary was actually achievable?
- Did the stop boundary occur first?

This allows the learning system to improve the transition model independently of whether a trade was executed.

---

## 46. Moment-in-Time Decision Objective

At any given moment, the production system should progressively answer the following questions:

```text
1. Has something changed enough to require attention?
                |
                v
2. What is the current market state?
                |
                v
3. What does the validated adaptive model infer from that state?
                |
                v
4. How is that state likely to evolve?
                |
                v
5. For how long is the opportunity likely to remain valid?
                |
                v
6. What direction, R:R, and horizon are supported?
                |
                v
7. Is the opportunity eligible under the trading policy?
                |
                v
8. Is the exposure permitted by independent risk controls?
                |
                v
9. Can the trade be executed acceptably under current microstructure?
                |
                v
10. Execute, wait, reprice, or reject.
```

This is the sharpened real-time objective of the framework.

The system is therefore not merely a current-condition classifier and not merely a price predictor.

It is a continuously operating system for:

**detecting change, estimating present state, estimating future state, constructing a bounded opportunity, controlling risk, executing, and learning from what subsequently occurred.**

---

# Section A — Adaptive Learning System

## 47. Consolidated Adaptive Learning Architecture

The Adaptive Learning System is the slower intelligence-development side of the framework. It is separate from the real-time trading path but continuously receives evidence produced by that path.

Its central question is:

> What parameter structures, nonlinear relationships, state transitions, regimes, reward/risk structures, and time horizons demonstrate stable forward value?

### Inputs

It should consume historical observations together with accumulated live evidence, including:

- Historical and live market observations
- Current-state histories
- Forward-state predictions and actual subsequent states
- Executed trade outcomes
- Rejected/no-trade outcomes
- Counterfactual reward/risk outcomes
- Fill, spread, slippage, and latency observations
- Prediction errors

### Responsibilities

The learning system can perform:

- Parameter estimation and self-adaptive parameter analysis
- Parameter interaction analysis
- Linear and nonlinear response testing
- Candidate polynomial-degree testing
- State-transition estimation
- Regime discovery
- Time-window and opportunity-lifetime analysis
- Reward/risk and horizon analysis
- Rolling-window stability analysis
- Point-in-time / no-lookahead validation
- Walk-forward validation
- Candidate-model comparison
- Controlled model promotion

### Output to Real Time

The learning system publishes controlled, versioned production artifacts rather than raw experiments:

```text
Model definition
Feature definition
Validated parameter snapshot
Validated transition model
Validated regime definitions
Eligibility configuration
R:R / horizon behavior
Model confidence / health metadata
```

### Feedback From Real Time

Feedback must be richer than P&L. For each evaluated opportunity the learning side should eventually be able to reconstruct what was observed, what state was inferred, what future state was predicted, what opportunity was proposed, whether it was traded, what happened afterward, which R boundaries were reached, how long the opportunity persisted, and what execution actually cost.

Rejected opportunities are retained as learning observations so the model can distinguish missed opportunities from correctly rejected situations.

### Controlled Adaptation

Real-time feedback should initially accumulate evidence rather than instantly rewrite production parameters:

```text
Observations / outcomes
        ↓
Learning dataset
        ↓
Adaptive estimation
        ↓
Forward and stability validation
        ↓
Candidate model snapshot
        ↓
Promotion criteria
        ↓
Approved production snapshot
        ↓
Real-Time Trading System
```

This remains the principal safety boundary between self-adaptation and live execution.

---

# Section B — Real-Time Trading System

## 48. Consolidated Real-Time Architecture

The Real-Time Trading System is the continuously operating side of the framework.

At any moment it asks:

> Has something changed, what is the market state now, where is that state likely to go next, is there a bounded reward/risk opportunity, and can that opportunity be safely and acceptably executed?

```text
Live Market Data
       ↓
Market Data Gateway
       ↓
Trigger Engine
       ↓
Current State / Regime Engine
       ↓
Adaptive Parametric Inference
       ↓
Forward State Engine
       ↓
Opportunity Engine
   (R:R × Time)
       ↓
Trading Eligibility
       ↓
Decision Engine
       ↓
Independent Risk Engine
       ↓
Execution Policy Engine
       ↓
Broker Adapter
       ↓
REPLAY / PAPER / LIVE
       ↓
Orders / Fills / Positions / Outcomes
       ↓
Outcome & Feedback Store
       ↓
Adaptive Learning System
```

### Trigger Is Not Entry

Volatility, unusual volume, rapid displacement, acceleration, liquidity change, or another perturbation can trigger deeper analysis. A trigger means **evaluate this instrument now**, not **buy or sell now**.

### Present State Plus Predictive Look-Ahead

The system evaluates both what is true now and, using only information available now, how that state is likely to evolve. The Forward State Engine can evaluate several horizons and estimate opportunity lifetime.

### Variable Reward/Risk

Reward/risk is not fixed at 5:1. The Opportunity Engine can evaluate candidate structures such as 2R, 3R, 4R, and 5R. A volatile period may support a 2R or 3R opportunity even when 5R is not credible.

Reward multiple, risk boundary, and time horizon are therefore state-dependent decision variables.

### Execution Is Separate From Prediction

The model never issues broker orders directly. Opportunity construction is followed by a Decision Engine and independent Risk Engine. The Execution Policy Engine then determines how an authorized exposure should be acquired under current microstructure.

Possible actions include:

```text
MARKET
LIMIT
MARKETABLE LIMIT
WAIT
REPRICE
CANCEL
ABANDON
```

---

## 49. Broker Simulation and Execution Layer

The architecture should expose one internal broker interface with multiple destinations:

```text
                         ┌── Our Internal Replay / Paper Broker
Execution Policy ────────┼── Third-Party Paper Broker
                         └── Third-Party Live Broker
```

The adaptive model, Opportunity Engine, Decision Engine, and Risk Engine should not need to know which destination is active.

### REPLAY — Our Own Paper Broker

We should build our own **Paper Broker / Replay Broker** for deterministic experimentation against recorded market data.

It should mimic the broker-facing behavior needed by the rest of the system:

- Submit, acknowledge, cancel, and replace orders
- Simulate fills and configurable partial fills
- Maintain positions and account state
- Support stops and targets
- Model rejection rules
- Model configurable latency and slippage
- Use spread-aware execution
- Apply transaction-cost assumptions

This gives us a repeatable environment in which a complete historical trading session can pass through the same logical real-time pipeline. It is useful for fast experiments, regression testing, walk-forward replay, failure reproduction, and comparing model versions against the exact same market sequence.

### PAPER — Third-Party Broker

A third-party paper account tests the system against live market conditions without intentionally committing live capital.

It adds operational realities that our internal replay cannot fully reproduce:

- Live API connectivity and authentication
- Broker acknowledgements and order states
- Real-time timing
- Network latency
- Broker-side validation
- Paper positions and account state

For the first implementation, the selected external paper environment is **Alpaca Paper Trading**.

### LIVE

The same Broker Adapter boundary can later support live execution without rewriting the adaptive model or Decision Engine.

A later adapter can support **Interactive Brokers** if broader instruments, futures, or other capabilities make it desirable.

---

## 50. Current Conservative Starting Point

Given where the design is now, the selected first implementation is:

**SPY + our own Replay/Paper Broker + Alpaca paper account + Python real-time prototype.**

SPY is a controlled first market instrument, not a permanent limitation of the system.

```text
                 PYTHON REAL-TIME PROTOTYPE

SPY live market observations
                 ↓
            Trigger Engine
                 ↓
        Current State / Regime
                 ↓
     Adaptive Parametric Inference
                 ↓
          Forward State Engine
                 ↓
       Opportunity Engine
          R:R × Horizon
                 ↓
          Decision Engine
                 ↓
            Risk Engine
                 ↓
      Execution Policy Engine
                 ↓
           Broker Adapter
          ↙             ↘
Our Replay Broker     Alpaca Paper
          \             /
           Outcomes / Fills
                 ↓
       Outcome / Feedback Store
                 ↓
       Adaptive Learning System
```

Starting with one highly liquid instrument lets us validate live data ingestion, trigger behavior, state updates, fast inference, predictive look-ahead, R:R/horizon selection, BUY/SELL/HOLD/EXIT decisions, independent risk authorization, broker API integration, order lifecycle, position tracking, outcome measurement, and feedback capture without simultaneously solving a 15,000-instrument scanning problem.

---

## 51. Python Is Not the Offline Boundary

Python is not inherently an offline platform. Our current experiments are offline because they load historical datasets, estimate parameters, produce results, and terminate.

The first real-time prototype can also be Python and operate continuously:

```text
receive observation
      ↓
update state
      ↓
evaluate trigger
      ↓
run fast inference
      ↓
estimate forward state
      ↓
evaluate opportunity
      ↓
decide
      ↓
risk check
      ↓
submit paper order if authorized
      ↓
observe outcome
      ↓
continue
```

The expensive learning and parameter-estimation work remains separate.

A simple first physical implementation can therefore be:

```text
learning.py
    ↓
validated_model_snapshot
    ↓
realtime.py
    ↓
broker_adapter.py
    ↓
Replay Broker / Alpaca Paper
```

The design principle is:

**Logical components first; physical service separation later when scale, resilience, deployment, or latency requires it.**

---

## 52. Development Progression

The current progression is:

```text
1. Historical research / parameter experiments
                ↓
2. Internal Replay / Paper Broker
                ↓
3. SPY Python real-time prototype
                ↓
4. Alpaca Paper integration
                ↓
5. Shadow-live operation
                ↓
6. Limited live deployment
                ↓
7. Broader instrument universe
                ↓
8. Additional broker adapters where useful
```

The internal Replay Broker tests our model and execution assumptions deterministically. The external paper broker tests the live operational path. Shadow live runs the complete production decision process while preventing live order transmission. Limited live exposure comes only after predefined model, risk, operational, and execution criteria are satisfied.

---

## 53. Current Two-System Boundary

```text
+==========================================================+
|                ADAPTIVE LEARNING SYSTEM                  |
|                                                          |
| Historical + Live Evidence                               |
| Parameters / Nonlinear Structure / State Transitions     |
| Regimes / Stability / R:R / Horizons                     |
| Forward Validation / Controlled Promotion                |
+===========================+==============================+
                            |
                  validated intelligence
                            |
                            v
+==========================================================+
|                REAL-TIME TRADING SYSTEM                  |
|                                                          |
| Market Data → Trigger → Current State → Forward State     |
| → Opportunity → Decision → Risk → Execution Policy       |
| → Broker Adapter → Replay/Paper/Live                     |
+===========================+==============================+
                            |
                     outcomes / errors
                            |
                            +------------------------------>
                                      Learning System
```

The Adaptive Learning System determines **what has demonstrated stable forward value**.

The Real-Time Trading System determines **what should be done now, given current and predicted near-future conditions**.

The broker layer determines **how an authorized action is represented and executed in the selected test or live environment**.

The immediate implementation choice remains deliberately conservative:

**SPY + our own Replay/Paper Broker + Alpaca Paper + a modular Python real-time prototype.**


---

## 54. Trading Envelope — Common Near-Field Boundary

The high-level design should not treat Market Universe, Market Clock/Event Context, Data Quality/Timing, Capital/Portfolio Allocation, and Position/Trade Lifecycle as unrelated downstream boxes. Together they define a common **near-field boundary** around a trading opportunity.

We call this boundary the **Trading Envelope**.

### Definition

> **Trading Envelope:** the dynamic set of market, temporal, data-integrity, capital, exposure, position, and execution constraints within which the intelligence system may construct, enter, maintain, modify, or exit a trading opportunity at a specific moment in time.

The Trading Envelope is therefore not itself a predictive model and is not simply another sequential pipeline stage. It is the contextual and constraint boundary within which the real-time intelligence operates.

At time `t`, a first logical representation is:

```text
TE(t) = {
    U(t),   market/instrument eligibility
    C(t),   market clock and event context
    D(t),   data quality and timing integrity
    A(t),   available capital / portfolio allocation state
    P(t),   current position and trade-lifecycle state
    X(t)    execution / market-microstructure feasibility
}
```

This is deliberately a logical definition rather than a final mathematical equation. Each term can later be formalized independently and the envelope can then be expressed as a constraint set, eligibility function, state vector, or feasible region.

### Why It Is an Envelope

The intelligence system may identify an attractive market state while the Trading Envelope makes the opportunity unavailable. Examples include:

- Instrument is outside the eligible universe.
- Market/session context prohibits entry.
- A scheduled event creates an excluded interval.
- Market data is stale or incomplete.
- Capital is already committed elsewhere.
- Existing portfolio exposure conflicts with the candidate.
- An open position changes what actions are valid.
- Spread, liquidity, or execution conditions make the theoretical opportunity unrealizable.

The envelope is dynamic. A trade can move into or out of feasibility without the underlying directional model changing.

---

## 55. Trading Envelope Terms

The following terms form the initial vocabulary for later mathematical definitions and logical maps.

### Market Universe — `U(t)`

The set of instruments that are eligible for consideration at time `t`.

It answers:

> **What may the system consider trading now?**

The Market Universe can later incorporate instrument type, liquidity requirements, exchange status, strategy eligibility, trading permissions, and scanner promotion rules.

### Market Clock / Event Context — `C(t)`

The temporal and external-event context surrounding the opportunity.

It answers:

> **When and under what event context is the system operating?**

Examples include pre-market, regular session, close, overnight session, shortened session, scheduled economic event, earnings event, halt, or another defined event window.

### Data Quality / Timing Integrity — `D(t)`

The validity, freshness, completeness, sequencing, and synchronization state of the observations used for a decision.

It answers:

> **Can the system trust the observations available at this instant?**

Candidate measures include source timestamp, receive timestamp, observation age, missing sequence detection, duplicate detection, feed gaps, clock drift, and cross-feed synchronization.

### Capital / Portfolio Allocation State — `A(t)`

The capital and portfolio resources currently available to an otherwise eligible opportunity.

It answers:

> **Given all competing opportunities and existing commitments, what capital may be allocated here?**

This is distinct from the Risk Engine. Allocation chooses among eligible uses of capital; Risk determines whether the proposed exposure is permitted.

### Position / Trade Lifecycle State — `P(t)`

The current strategic state of any open or pending position associated with the instrument or portfolio.

It answers:

> **What commitment already exists, and what actions remain valid?**

Possible state includes pending entry, open position, partial fill, active target, active stop, time expiry, partial exit, signal decay, model invalidation, trailing behavior, and forced exit.

### Execution Feasibility / Microstructure — `X(t)`

The current ability to realize a theoretical opportunity in the market at an acceptable execution cost.

It answers:

> **Can the authorized opportunity actually be acquired or exited acceptably now?**

Candidate inputs include spread, displayed/estimated liquidity, expected slippage, urgency, order latency, signal decay, and permitted order policy.

---

## 56. Entry Boundary and Exit Boundary

The Trading Envelope has two useful logical faces.

### Entry Boundary

The Entry Boundary asks whether a newly constructed opportunity can become a position.

```text
ENTRY BOUNDARY
--------------
Instrument eligible?
Session/event context acceptable?
Data valid and timely?
Capital available?
Portfolio exposure compatible?
Risk authorization available?
Execution feasible?
```

### Exit / Continuation Boundary

Once a position exists, the same envelope continues to operate. It asks whether the position should remain open, be modified, or be exited.

```text
EXIT / CONTINUATION BOUNDARY
----------------------------
Opportunity still valid?
Forward state still supportive?
Expected opportunity lifetime expired?
Target/stop state changed?
Position state changed?
Capital/risk constraints changed?
Execution conditions changed?
```

This makes the Trading Envelope continuous rather than an entry-only gate.

---

## 57. Opportunity Versus Trading Envelope

The **Opportunity Engine** and **Trading Envelope** answer different questions.

The Opportunity Engine asks:

> **What bounded direction, reward/risk structure, and time horizon are supported by the current and predicted future state?**

The Trading Envelope asks:

> **Is that opportunity feasible and permissible in the surrounding market, temporal, data, capital, position, and execution context?**

A useful logical form is:

```text
Candidate Opportunity O(t)
        +
Trading Envelope TE(t)
        ↓
Feasible Opportunity F(t)
```

A future mathematical formulation could treat `TE(t)` as a feasible set and require:

```text
O(t) ∈ TE(t)
```

before an opportunity can proceed to an authorized trading action. This notation is intentionally provisional; detailed design should determine whether the envelope is best represented as a state vector, set of constraints, gating function, or combination of these.

---

## 58. Defined Core Terms for Mathematical and Logical Refinement

The following vocabulary should remain stable enough to support later mathematical definition.

**Perturbation** — A measurable change in one or more observed market variables sufficient to alter system attention or state assessment.

**Trigger** — A rule or learned condition that promotes an instrument/state for deeper real-time evaluation. A Trigger is not an Entry Signal.

**Current State** — The system's point-in-time representation of relevant market conditions using only information available at or before that instant.

**Regime** — A recognizable class or region of market state in which relationships or parameter behavior are sufficiently similar to justify common treatment.

**Adaptive Parameter** — A model coefficient or structural quantity whose validated value can change as accumulated evidence indicates that the underlying relationship has changed.

**State Transition** — The modeled evolution from a current state to one or more possible future states over a specified horizon.

**Forward State** — A probability-weighted or confidence-weighted representation of possible future market states derived exclusively from information available at the current decision time.

**Opportunity Lifetime** — The estimated future interval over which the current state and its predicted evolution continue to support a candidate opportunity.

**Opportunity** — A bounded candidate trading proposition containing at minimum direction, risk boundary, reward objective or reward multiple, and time horizon, supported by current and forward-state intelligence.

**Reward/Risk (`R:R`)** — The relationship between the candidate reward boundary and defined unit of risk. It is a state-dependent decision variable rather than a fixed 5:1 constant.

**Trading Envelope (`TE(t)`)** — The dynamic feasible boundary around an opportunity, defined by market eligibility, temporal/event context, data integrity, capital/portfolio state, position lifecycle, and execution feasibility.

**Decision** — The strategy-level determination to propose action, wait, maintain, modify, exit, or reject after considering intelligence and the Trading Envelope.

**Risk Authorization** — An independent determination that the proposed exposure is permitted under risk policy. Risk authorization is separate from opportunity quality.

**Execution Policy** — The determination of how an authorized action should be represented in orders under current microstructure, including market, limit, marketable-limit, wait, reprice, cancel, or abandon behavior.

**Position Lifecycle** — The evolving strategic state of an accepted trade from pending entry through fill, management, modification, and final exit.

**Outcome** — The observed market, position, execution, and prediction result following an evaluated opportunity, including outcomes for opportunities that were rejected.

**Model Snapshot** — An immutable, versioned collection of validated model structure, parameters, state-transition behavior, and associated metadata approved for real-time inference.

---

## 59. Final High-Level Picture Before Detailed Design

The current architecture can now be represented with the Trading Envelope as the common near-field boundary rather than as a row of unrelated control components.

```text
                         ADAPTIVE LEARNING SYSTEM
                                  |
                         validated intelligence
                                  |
                                  v

+-------------------------------------------------------------------+
|                         TRADING ENVELOPE                          |
|                                                                   |
|   Market Universe             Market Clock / Event Context        |
|   Data Quality / Timing       Capital / Portfolio State           |
|   Position Lifecycle          Execution / Microstructure          |
|                                                                   |
|                 +--------------------------------+                |
| Market Data --->|       REAL-TIME INTELLIGENCE   |                |
|                 |                                |                |
|                 | Trigger                        |                |
|                 | Current State / Regime         |                |
|                 | Adaptive Inference             |                |
|                 | Forward State / Look-Ahead     |                |
|                 | Opportunity R:R x Time         |                |
|                 +---------------+----------------+                |
|                                 |                                 |
|                    feasible candidate opportunity                 |
|                                 |                                 |
+---------------------------------+---------------------------------+
                                  |
                                  v
                           DECISION ENGINE
                                  |
                                  v
                       INDEPENDENT RISK ENGINE
                                  |
                                  v
                       EXECUTION POLICY ENGINE
                                  |
                                  v
                           BROKER ADAPTER
                         /       |        \
                    REPLAY     PAPER      LIVE
                         \       |        /
                                  v
                       ORDERS / FILLS / POSITIONS
                                  |
                                  v
                        OUTCOME / FEEDBACK STORE
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
          TRADING ENVELOPE UPDATE       ADAPTIVE LEARNING
```

### Interpretation

The Adaptive Learning System determines **what relationships have demonstrated stable forward value** and publishes validated intelligence.

The Real-Time Intelligence core determines **what is happening now and what is likely to happen next**.

The Trading Envelope determines **the feasible contextual boundary within which that intelligence can become and remain a trading opportunity**.

The Decision Engine determines **what strategic action is proposed**.

The Risk Engine determines **whether the exposure is permitted**.

The Execution Policy Engine and Broker Adapter determine **how the authorized action is realized**.

The Outcome / Feedback Store closes both loops: it updates the immediate Trading Envelope as positions and market conditions change, and it supplies evidence back to the Adaptive Learning System for slower validated adaptation.

This picture is the current high-level design boundary. Detailed design should refine the internal mathematics and interfaces without collapsing the separation between **learning**, **real-time intelligence**, **the Trading Envelope**, **decision**, **risk**, and **execution**.

---

## 54. Primary Entity Within the Trading Envelope: Return Shape

A key conceptual refinement is that the primary entity of interest inside the Trading Envelope is **not the instrument, stock, tick, or raw signal**.

The instrument is the carrier of observable market behavior.

The entity the system is attempting to identify and capture is the **Return Shape**.

### Return Shape — Working Definition

A **Return Shape** is the model's time-varying representation of the possible return behavior associated with an instrument or opportunity from the present moment across one or more forward horizons.

A Return Shape can encode more than one expected-return number. Its eventual mathematical representation may include:

- Direction
- Potential return magnitude
- Probability or confidence distribution
- Time-to-return
- Reward boundaries
- Adverse excursion
- Volatility
- Expected persistence
- Expected decay
- Reversal probability
- Uncertainty
- Dependence on current market state
- Dependence on the evolving Trading Envelope

A useful initial notation is:

\[
\mathcal{R}_i(t,h)
\]

where:

- \(i\) identifies the instrument or candidate opportunity,
- \(t\) is the present decision time,
- \(h\) is a forward horizon.

The notation is deliberately abstract. It does **not** yet prescribe a particular mathematical model.

Conceptually:

\[
\mathcal{R}_i(t,h)
=
f(
\text{return},
\text{probability},
\text{time},
\text{risk},
\text{state},
\text{transition},
\text{uncertainty}
)
\]

The purpose of later mathematical work is to determine which representation is useful and empirically defensible.

---

## 55. Elasticity of a Return Shape

The word **shape** is intentional.

A Return Shape is not assumed to remain fixed after it is first detected.

As new market observations arrive, the estimated future return structure can:

- Expand
- Contract
- Strengthen
- Weaken
- Shift in time
- Change direction
- Become more uncertain
- Become less uncertain
- Develop greater adverse risk
- Decay entirely

Therefore:

\[
\mathcal{R}_i(t,h)
\rightarrow
\mathcal{R}'_i(t+\Delta t,h)
\]

The system should treat Return Shapes as **elastic, continuously re-estimated entities**.

This is a major distinction from a conventional fixed signal such as:

```text
BUY = TRUE
```

A BUY flag is a discrete decision artifact.

A Return Shape is the richer evolving object from which an opportunity and later a decision may be derived.

---

## 56. Return Field

At any point in time there can be many Return Shapes present simultaneously.

The collection of Return Shapes observable or under consideration at time \(t\) is called the **Return Field**.

A working notation is:

\[
\boxed{
\mathcal{F}(t)=
\{
\mathcal{R}_1(t),
\mathcal{R}_2(t),
\ldots,
\mathcal{R}_n(t)
\}
}
\]

The Return Field is therefore a time-varying population rather than a static list of stocks.

The instruments remain important because they produce the market observations from which Return Shapes are estimated, but the trading intelligence is ultimately interested in the **shapes**, not merely the instrument names.

For example:

```text
AAPL ──────→ Return Shape A
SPY  ──────→ Return Shape B
MSFT ──────→ Return Shape C
NVDA ──────→ Return Shape D
```

At time \(t\), those shapes form part of:

```text
RETURN FIELD F(t)
```

SPY in the first prototype is therefore best understood as the **first controlled carrier of a Return Shape**, not as the conceptual center of the architecture.

---

## 57. The Net Analogy

The Trading Envelope can be understood as a dynamic net operating over a dynamic Return Field.

At any point in time, multiple elastic Return Shapes may move into, through, deform within, and leave the region in which they can potentially be acted upon.

```text
                         MARKET

              thousands of instruments
                        |
                        v
              perturbations / movement
                        |
                        v
               evolving RETURN SHAPES

                  ~       /\       __
               /    \    /  \    /   \
                  \      \       ~

          +================================+
          |        TRADING ENVELOPE        |
          |                                |
          |       ~    /\    ∩    ~        |
          |                                |
          |          RETURN FIELD          |
          |        R1 R2 R3 ... Rn         |
          |                                |
          |   Which shapes are             |
          |   CAPTURABLE at time t?        |
          +===============+================+
                          |
                          v
                     OPPORTUNITY
                          |
                          v
                       DECISION
                          |
                          v
                         RISK
                          |
                          v
                      EXECUTION
```

The analogy is useful because the Trading Envelope does not merely contain static candidates.

The entities within it are moving and changing.

A Return Shape may:

```text
ENTER ENVELOPE
      ↓
DEFORM / STRENGTHEN
      ↓
BECOME CAPTURABLE
      ↓
BECOME AN OPPORTUNITY
      ↓
DETERIORATE OR PERSIST
      ↓
EXIT ENVELOPE
```

The plural object being captured at any instant is therefore the **Return Field**, analogous to multiple fish being present within a net.

---

## 58. Capturability

A predicted Return Shape is not necessarily realizable as a trade.

Introduce the working term **Capturability**.

### Capturability — Working Definition

**Capturability** is the degree to which a Return Shape can realistically be converted into realized return under the Trading Envelope that exists at a particular moment.

Represent it initially as:

\[
C(\mathcal{R}_i,t)
\]

or more explicitly:

\[
C(\mathcal{R}_i,TE(t))
\]

Capturability can depend on:

- Available capital
- Existing positions
- Portfolio exposure
- Liquidity
- Bid/ask spread
- Expected slippage
- Execution latency
- Signal/opportunity lifetime
- Market session
- Event context
- Data integrity
- Risk constraints
- Broker availability
- Order feasibility

A theoretically attractive Return Shape can therefore have low capturability.

Example:

```text
Predicted shape:
    strong +4R potential

But:

    spread        excessive
    liquidity     poor
    expected life 12 seconds
    latency       high
    capital       unavailable

Result:
    shape quality may be high
    capturability may be near zero
```

This distinction prevents the system from confusing **theoretical opportunity** with **realizable opportunity**.

---

## 59. Opportunity as Return Shape Plus Capturability

The Opportunity Engine should therefore not be described simply as finding attractive stocks.

Its conceptual task is:

> Identify Return Shapes within the current Trading Envelope whose predicted behavior and capturability jointly satisfy the system's opportunity criteria.

A useful working relationship is:

\[
O_i(t)
=
g(
\text{ReturnShapeQuality}_i(t),
\text{Capturability}_i(t)
)
\]

An illustrative simplification is:

\[
O_i(t)
\sim
Q(\mathcal{R}_i(t))
\times
C(\mathcal{R}_i,TE(t))
\]

where:

- \(Q\) represents the quality of the predicted Return Shape,
- \(C\) represents its capturability,
- \(O\) represents opportunity quality.

The multiplication is **not yet a committed mathematical formula**. It records the logical relationship to be tested later.

A high-quality Return Shape with negligible capturability should not become an executable opportunity.

Likewise, something easy to execute but with a poor Return Shape should not become an opportunity merely because it is liquid.

---

## 60. Revised Trading Envelope Definition

The Return Shape concept makes the Trading Envelope definition more concrete.

### Trading Envelope — Revised Working Definition

> **The Trading Envelope is the dynamic boundary within which Return Shapes are observable, eligible, manageable, and potentially capturable at a particular moment in time.**

The Trading Envelope is not merely a risk filter.

It combines the contextual and operational conditions surrounding a Return Shape.

Its logical components currently include:

\[
TE(t)
=
\{
U(t),
C_t(t),
D(t),
A(t),
P(t),
X(t)
\}
\]

where, as a working logical map:

- \(U(t)\) = Market Universe / instrument eligibility
- \(C_t(t)\) = Market Clock and Event Context
- \(D(t)\) = Data Quality and Time Integrity
- \(A(t)\) = Capital / Portfolio Allocation state
- \(P(t)\) = Position / Trade Lifecycle state
- \(X(t)\) = Execution feasibility / market microstructure

This is intentionally a **logical definition first**.

Later mathematical work can determine whether the Trading Envelope is best represented as:

- A state vector
- A multidimensional constraint set
- A feasible region
- A gating function
- A probability surface
- A combination of these representations

---

## 61. Entry and Continuation Faces of the Trading Envelope

The Trading Envelope has two related faces.

### Entry Boundary

Before a Return Shape becomes a position, the envelope asks:

```text
Is the instrument eligible?
Is the market/session context acceptable?
Is the data valid?
Is capital available?
Is portfolio exposure acceptable?
Is the Return Shape sufficiently attractive?
Is it sufficiently capturable?
Can execution occur acceptably?
```

### Continuation / Exit Boundary

Once a position exists, the same envelope continues to evolve and asks:

```text
Does the Return Shape still exist?
How has the shape deformed?
Is the Forward State still supportive?
Is the opportunity lifetime expiring?
Has capturability changed?
Has volatility changed?
Has liquidity deteriorated?
Has portfolio/risk state changed?
Has target or stop geometry changed?
Should the position remain, change, or exit?
```

The Trading Envelope therefore surrounds the **entire life of an opportunity**, not only its entry.

---

## 62. Entity and Decision Hierarchy

The current conceptual hierarchy is:

```text
RAW MARKET OBSERVATIONS
          |
          v
     PERTURBATIONS
          |
          v
       TRIGGERS
          |
          v
     CURRENT STATE
          |
          v
     FORWARD STATE
          |
          v
      RETURN SHAPE
          |
          v
+===================================+
|         TRADING ENVELOPE          |
|                                   |
|           RETURN FIELD            |
|        R1 R2 R3 ... Rn            |
|                                   |
|     Shape Quality +               |
|       Capturability               |
+================+==================+
                 |
                 v
            OPPORTUNITY
                 |
                 v
              DECISION
                 |
                 v
                RISK
                 |
                 v
         EXECUTION POLICY
                 |
                 v
              BROKER
                 |
                 v
         REALIZED RETURN
                 |
                 v
              OUTCOME
                 |
                 +------------------->
                      ADAPTIVE LEARNING
```

This hierarchy distinguishes several terms that might otherwise be conflated:

- A **perturbation** is a change in observable conditions.
- A **trigger** causes deeper evaluation.
- **Current State** describes the market now.
- **Forward State** estimates how that state may evolve.
- A **Return Shape** describes the resulting possible return behavior.
- The **Return Field** is the population of Return Shapes at time \(t\).
- The **Trading Envelope** defines the dynamic region in which those shapes can be considered and managed.
- **Capturability** measures whether a Return Shape can realistically be converted into realized return.
- An **Opportunity** is a Return Shape that satisfies the relevant quality and capturability criteria.
- A **Decision** proposes action.
- **Risk Authorization** determines whether exposure is permitted.
- **Execution Policy** determines how authorized exposure should be acquired or managed.
- **Realized Return / Outcome** provides evidence back to the Adaptive Learning System.

---

## 63. Dynamic Return-Field View of the System

The conceptual system should no longer be described merely as:

```text
scan stocks
    ↓
find signals
    ↓
trade
```

The stronger model is:

> **Continuously observe a dynamic field of elastic Return Shapes, determine which shapes fall within the current Trading Envelope, estimate which are capturable, act on qualified opportunities, and learn from how those shapes subsequently evolved.**

At time \(t_0\):

\[
\mathcal{F}(t_0)
=
\{\mathcal{R}_1,\mathcal{R}_2,\ldots,\mathcal{R}_n\}
\]

At the next observation:

\[
\mathcal{F}(t_1)
\neq
\mathcal{F}(t_0)
\]

because:

- Existing Return Shapes may deform.
- New shapes may appear.
- Existing shapes may disappear.
- Their probabilities may change.
- Their opportunity lifetimes may change.
- Their capturability may change.
- The Trading Envelope itself may change.

The system is therefore operating on **two simultaneously changing objects**:

\[
\boxed{\text{Dynamic Return Field}}
\qquad\text{and}\qquad
\boxed{\text{Dynamic Trading Envelope}}
\]

Their interaction determines the opportunity set available at each moment.

---

## 64. Consolidated High-Level Picture

```text
                 ADAPTIVE LEARNING SYSTEM
                          |
              validated intelligence
                          |
                          v

                         MARKET
                           |
                           v
                 RAW OBSERVATIONS
                           |
                           v
                    PERTURBATIONS
                           |
                           v
                       TRIGGERS
                           |
                           v
                  CURRENT STATE
                           |
                           v
                  FORWARD STATE
                           |
                           v
                  RETURN SHAPES
                           |
             R1(t) R2(t) ... Rn(t)
                           |
                           v
        +======================================+
        |           TRADING ENVELOPE           |
        |                                      |
        |             RETURN FIELD             |
        |                                      |
        |  Universe / Market Context           |
        |  Data Integrity / Timing             |
        |  Capital / Portfolio State           |
        |  Position Lifecycle                  |
        |  Execution Feasibility               |
        |                                      |
        |       RETURN SHAPE QUALITY            |
        |                 +                    |
        |           CAPTURABILITY              |
        |                 |                    |
        |                 v                    |
        |            OPPORTUNITY               |
        +=================+====================+
                          |
                          v
                       DECISION
                          |
                          v
                 INDEPENDENT RISK
                          |
                          v
                 EXECUTION POLICY
                          |
                          v
                    BROKER ADAPTER
                 /        |        \
             REPLAY      PAPER      LIVE
                          |
                          v
                POSITION / OUTCOME
                          |
             +------------+-------------+
             |                          |
             v                          v
   TRADING ENVELOPE              OUTCOME STORE
    re-evaluates                     |
    open position                    v
                            ADAPTIVE LEARNING
```

This diagram is the current consolidated conceptual picture before detailed mathematical and physical system design.

The principal entity inside the Trading Envelope is the **Return Shape**.

The plural, moment-in-time population is the **Return Field**.

The envelope and the field both vary through time.

The objective of the real-time system is to identify which Return Shapes are sufficiently **capturable** to become qualified opportunities while continuously re-evaluating any shape associated with an open position.

---

## 65. Trading Envelope as an Elastic Adaptive Gate

The Trading Envelope should be understood as more than a static boundary or a collection of constraints.

Both the **Return Shape** and the **Trading Envelope** are elastic.

They interact continuously:

\[
\boxed{
\mathcal{R}_i(t)
\longleftrightarrow
TE_i(t)
}
\]

A trade opportunity exists when the interaction between the evolving Return Shape and the evolving Trading Envelope produces sufficient **Capturability**.

### The Tap / Valve Analogy

The Trading Envelope can be viewed as an adaptive tap or valve operating on each candidate Return Shape.

```text
               RETURN FIELD

          R1   R2   R3   R4
           |    |    |    |
           v    v    v    v

      +=======================+
      |    TRADING ENVELOPE   |
      |                       |
      |     ADAPTIVE TAP      |
      +===========+===========+
                  |
            CLOSED / OPENING
                  |
                  v
             OPPORTUNITY
```

Most Return Shapes do not automatically become opportunities.

The tap can remain effectively closed when one or more required conditions are inadequate, including:

- Return Shape quality
- Forward-state support
- Capturability
- Capital availability
- Portfolio state
- Position state
- Data integrity
- Market/session/event context
- Liquidity
- Spread
- Execution feasibility
- Risk capacity

As those conditions change, the Trading Envelope can open or close dynamically.

### Aperture Rather Than Only Binary State

The Trading Envelope need not ultimately be represented as only:

\[
TE \in \{0,1\}
\]

A useful mathematical direction is to consider an **aperture** or gating value:

\[
0 \leq A_i(t) \leq 1
\]

where the value represents the degree to which Return Shape \(i\) is presently eligible and capturable.

Illustratively:

```text
0.00   closed
0.20   weak eligibility
0.50   partially open
0.80   strongly eligible
1.00   fully open
```

These values are conceptual only. The actual representation and thresholds must be derived and validated experimentally.

The important design property is that the aperture can change continuously as both the Return Shape and surrounding Trading Envelope conditions change.

### Opportunity Formation

The logical interaction becomes:

```text
RETURN SHAPE
     |
     | quality / forward behavior
     v
TRADING ENVELOPE
     |
     | market + capital + position
     | data + execution conditions
     v
CAPTURABILITY
     |
     v
SUFFICIENT?
   /     \
 NO       YES
 |         |
 v         v
CLOSED   QUALIFIED
          OPPORTUNITY
```

Therefore:

> **The trade opportunity exists when the relationship between the Return Shape and Trading Envelope creates sufficient Capturability.**

An attractive Return Shape does not by itself create an actionable opportunity.

### The Envelope Remains Active After Entry

Passing through the Trading Envelope does not terminate its role.

Once a trade becomes an open position, the Trading Envelope continues to regulate that position.

```text
RETURN SHAPE
     ↓
ENVELOPE OPENS
     ↓
OPPORTUNITY
     ↓
DECISION / RISK
     ↓
EXECUTION
     ↓
OPEN POSITION
     |
     +----------------------+
                            |
                            v
                  TRADING ENVELOPE
                  CONTINUES WATCHING
                            |
              +-------------+-------------+
              |             |             |
           shape          shape         shape
          persists      weakens      invalidates
              |             |             |
              v             v             v
            HOLD        REDUCE /       EXIT
                         MODIFY
```

If the Return Shape continues to develop favorably, the aperture can remain sufficiently open to support continuation.

If the Return Shape deteriorates, opportunity lifetime shortens, execution conditions worsen, portfolio conditions change, or other envelope conditions deteriorate, the aperture can begin closing.

That change contributes to a:

- Hold decision
- Position reduction
- Target modification where permitted
- Protective adjustment
- Exit decision

The Trading Envelope therefore participates in both **entry qualification** and **position continuation/exit qualification**.

### Sharpened Definition

The working definition is now:

> **The Trading Envelope is a dynamic control boundary whose aperture continuously responds to the quality and Capturability of Return Shapes and the surrounding market, capital, position, data, and execution conditions.**

Operationally:

> **The Trading Envelope is the real-time adaptive gate between predicted return and actionable opportunity.**

This definition supersedes any interpretation of the Trading Envelope as merely a passive boundary.

---

## 66. Elastic Interaction Model

The real-time system can now be viewed as the interaction of two evolving objects:

```text
        ELASTIC RETURN SHAPE
                 |
                 | continuously changes
                 v
        +--------------------+
        |                    |
        |  ELASTIC TRADING   |
        |      ENVELOPE      |
        |                    |
        | adaptive aperture  |
        +---------+----------+
                  |
            Capturability
                  |
                  v
             Opportunity
```

Both sides can change independently.

A Return Shape can improve while the Trading Envelope becomes less favorable.

For example:

```text
Return Shape quality        increasing
Forward-state confidence    increasing

BUT

spread                       widening
available capital            decreasing
portfolio exposure           increasing
```

Conversely, the Trading Envelope can become more favorable while the Return Shape itself deteriorates.

An opportunity therefore exists only through their **joint state at time \(t\)**.

A useful logical representation is:

\[
O_i(t)
=
g\left(
\mathcal{R}_i(t),
TE_i(t),
C_i(t)
\right)
\]

where:

- \(\mathcal{R}_i(t)\) = elastic Return Shape,
- \(TE_i(t)\) = elastic Trading Envelope state,
- \(C_i(t)\) = Capturability,
- \(O_i(t)\) = resulting opportunity state.

The exact mathematical form of \(g\) remains an experimental question.

This interaction is central to the real-time architecture because the system is not simply predicting return and then applying a static filter. It is continuously evaluating whether an evolving predicted return remains actionable inside an evolving control environment.

---

# Part II — Design

## Design Artifact Index

The Design section translates the conceptual framework into logical artifacts. It deliberately stops short of committing to physical services, databases, programming-language classes, or final mathematics until experiments justify those choices.

Artifact status values:

- **CONCEPT** — named and bounded, but logical behavior is still being explored.
- **LOGICAL DESIGN** — responsibilities, inputs, outputs, states, and interactions are defined.
- **EXPERIMENTAL** — logical design exists and mathematical/behavioral alternatives are being tested.
- **VALIDATED** — experimental evidence supports the selected behavior.
- **IMPLEMENTATION READY** — interfaces and behavior are sufficiently stable for detailed implementation design.

Current artifact map:

| ID | Artifact | Current Status |
|---|---|---|
| D01 | Overall System Logical Design | CONCEPT |
| D02 | Adaptive Learning System | CONCEPT |
| D03 | Real-Time Trading System | CONCEPT |
| D04 | Trading Envelope | LOGICAL DESIGN |
| D05 | Return Shape / Forward State Model | CONCEPT |
| D06 | Opportunity Engine | CONCEPT |
| D07 | Decision Engine | CONCEPT |
| D08 | Independent Risk Engine | CONCEPT |
| D09 | Position / Trade Lifecycle Manager | CONCEPT |
| D10 | Execution Policy Engine | CONCEPT |
| D11 | Broker Adapter | CONCEPT |
| D12 | Internal Replay / Paper Broker | CONCEPT |
| D13 | Alpaca Paper Integration | CONCEPT |
| D14 | Outcome / Feedback System | CONCEPT |
| D15 | Model Registry / Promotion Controller | CONCEPT |
| D16 | Capital / Portfolio Allocation | CONCEPT |
| D17 | Market Universe / Candidate Scanner | CONCEPT |
| D18 | Market Clock / Event Context | CONCEPT |
| D19 | Data Quality / Time Synchronization | CONCEPT |
| D20 | Observability / Control / Recovery | CONCEPT |

The index is a map, not an instruction to design every artifact immediately. D04 is the first artifact developed to logical-design depth because it provides the near-field control boundary around Return Shapes and positions.

---

# D04 — Trading Envelope Logical Design

**Status:** LOGICAL DESIGN

## D04.1 Purpose

The Trading Envelope is the real-time adaptive gate between **predicted return** and **actionable opportunity**.

Its purpose is not to predict the Return Shape. That responsibility belongs to the state, adaptive inference, and Forward State logic.

Its purpose is to continuously determine whether an elastic Return Shape is sufficiently **observable, eligible, manageable, and capturable** under the conditions that exist at time \(t\).

The Trading Envelope remains active after entry. It therefore participates in both:

- qualification of a new opportunity; and
- continuation, reduction, modification, or exit assessment of an existing position.

---

## D04.2 Primary Entity

The primary entity presented to the Trading Envelope is:

\[
\mathcal{R}_i(t,h)
\]

the **Return Shape** for candidate \(i\), evaluated at current time \(t\) across forward horizon \(h\).

The Trading Envelope does not fundamentally process a stock symbol as its object of interest. The symbol identifies the carrier of the observations from which the Return Shape is formed.

For the first experiment:

```text
SPY
  |
  v
market observations
  |
  v
current + forward state
  |
  v
Return Shape R_SPY(t,h)
  |
  v
Trading Envelope
```

At scale, many Return Shapes can be present simultaneously. Their time-\(t\) population is the **Return Field**:

\[
\mathcal{F}(t)=
\{\mathcal{R}_1(t),\mathcal{R}_2(t),...,\mathcal{R}_n(t)\}
\]

---

## D04.3 Elastic Interaction

The Return Shape and Trading Envelope are both elastic.

\[
\boxed{
\mathcal{R}_i(t)
\longleftrightarrow
TE_i(t)
}
\]

The Return Shape can strengthen, weaken, expand, contract, shift horizon, change uncertainty, or reverse.

At the same time, the Trading Envelope can become more or less permissive because market, capital, portfolio, position, data, event, liquidity, spread, latency, or execution conditions have changed.

An opportunity therefore cannot be determined from either object alone.

A working logical relationship is:

\[
O_i(t)=
g(
\mathcal{R}_i(t),
TE_i(t),
C_i(t)
)
\]

where \(C_i(t)\) is Capturability and \(O_i(t)\) is the resulting opportunity state.

The exact form of \(g\) is an experimental question.

---

## D04.4 Trading Envelope Logical Map

The current logical map is:

\[
TE(t)=
\{
U(t),
C_t(t),
D(t),
A(t),
P(t),
X(t)
\}
\]

where:

- \(U(t)\) — Market Universe / instrument eligibility
- \(C_t(t)\) — Market Clock and Event Context
- \(D(t)\) — Data Quality and Time Integrity
- \(A(t)\) — Capital / Portfolio Allocation state
- \(P(t)\) — Position / Trade Lifecycle state
- \(X(t)\) — Execution feasibility / market microstructure

This is not yet a committed mathematical state vector. It is a logical decomposition of the conditions defining the envelope.

Later experiments can determine whether the best formal representation is a state vector, feasible region, constraint set, gating function, probability surface, or hybrid.

---

## D04.5 Logical Inputs

The Trading Envelope receives two broad classes of input.

### Return-Shape Inputs

Examples include:

- Direction
- Potential magnitude
- Target-before-stop estimates
- Forward-state distribution
- Expected opportunity lifetime
- Persistence / decay
- Volatility behavior
- Adverse excursion expectation
- Uncertainty / confidence
- Candidate R:R and horizon structures

### Envelope-State Inputs

Examples include:

- Instrument eligibility
- Market/session state
- Scheduled-event context
- Data freshness and integrity
- Timestamp/sequence integrity
- Available capital
- Existing portfolio exposure
- Existing position state
- Risk capacity
- Liquidity
- Bid/ask spread
- Expected slippage
- Execution latency
- Broker availability / health
- Order feasibility

---

## D04.6 Capturability

**Capturability** is the degree to which a Return Shape can realistically be converted into realized return under the Trading Envelope existing at that moment.

Working notation:

\[
C_i(t)=C(\mathcal{R}_i(t),TE_i(t))
\]

Capturability is deliberately separate from Return Shape quality.

A high-quality predicted shape can be poorly capturable because the surrounding envelope is unfavorable.

Likewise, excellent execution conditions do not create an opportunity when the Return Shape itself is poor.

The Opportunity Engine therefore eventually evaluates the joint condition:

```text
RETURN SHAPE QUALITY
          +
    CAPTURABILITY
          |
          v
 QUALIFIED OPPORTUNITY
```

---

## D04.7 Adaptive Aperture

The Trading Envelope can be modeled conceptually as an adaptive tap or valve.

A Return Shape does not automatically pass through the envelope.

```text
              RETURN FIELD

         R1   R2   R3   R4
          |    |    |    |
          v    v    v    v

     +=======================+
     |    TRADING ENVELOPE   |
     |                       |
     |     ADAPTIVE TAP      |
     +===========+===========+
                 |
          adaptive aperture
                 |
                 v
            OPPORTUNITY
```

A useful future mathematical direction is:

\[
0 \leq A_i(t) \leq 1
\]

where \(A_i(t)\) represents the envelope aperture for Return Shape \(i\).

Illustratively only:

```text
0.00   closed
0.20   weak eligibility
0.50   partially open
0.80   strongly eligible
1.00   fully open
```

The design does not yet prescribe whether the production representation will be continuous, discrete, probabilistic, or hybrid.

---

## D04.8 Aperture State Model

For logical design, the envelope can initially be described with the following states:

```text
CLOSED
   |
   | sufficient evidence accumulating
   v
OPENING
   |
   | qualification + persistence satisfied
   v
OPEN
   |
   | deterioration / invalidation
   v
CLOSING
   |
   +----> CLOSED
```

For an existing position, OPEN/CLOSING does not directly mean HOLD/EXIT. It supplies the current envelope state to the Decision and Risk layers.

Possible downstream outcomes include:

```text
HOLD
REDUCE
MODIFY
EXIT
```

---

## D04.9 Hysteresis and Persistence

The envelope should not oscillate rapidly around one threshold.

A naive implementation such as:

```text
0.79 -> CLOSED
0.81 -> OPEN
0.79 -> CLOSED
0.81 -> OPEN
```

could create unstable trade behavior.

The logical design therefore includes **hysteresis and persistence**.

Potential mechanisms include:

- Opening threshold greater than closing threshold
- Minimum persistence before opening
- Minimum persistence before closing
- Rate-of-change constraints
- Confidence persistence
- State-transition confirmation

Conceptually:

\[
A_{\text{open}} > A_{\text{close}}
\]

This allows a Return Shape to establish itself before becoming actionable while preventing tiny fluctuations from immediately invalidating an open position.

The actual thresholds and persistence periods must be determined experimentally.

---

## D04.10 Entry Face

Before a Return Shape becomes a position, the Trading Envelope evaluates questions such as:

```text
Is the instrument eligible?
Is the market/session context acceptable?
Is the data valid and current?
Is the Return Shape sufficiently strong?
Is its forward state sufficiently supportive?
Is its opportunity lifetime sufficient?
Is capital available?
Is portfolio exposure acceptable?
Is risk capacity available?
Is liquidity adequate?
Is spread acceptable?
Is expected slippage acceptable?
Can the trade be executed within the shape lifetime?
```

If the combined state produces sufficient Capturability and the aperture reaches the qualified state, the Return Shape becomes an **Opportunity Candidate**.

The envelope itself does not execute the trade.

```text
Trading Envelope
       |
       v
Qualified Opportunity
       |
       v
Decision Engine
       |
       v
Independent Risk
       |
       v
Execution Policy
```

---

## D04.11 Continuation / Exit Face

The Trading Envelope remains active after entry.

The Return Shape associated with the position continues to evolve:

\[
\mathcal{R}_i(t)
\rightarrow
\mathcal{R}_i(t+\Delta t)
\]

The envelope continuously asks:

```text
Does the Return Shape still exist?
Has its direction changed?
Has its magnitude changed?
Has uncertainty increased?
Is Forward State still supportive?
Is expected opportunity lifetime expiring?
Has Capturability changed?
Has volatility changed?
Has liquidity deteriorated?
Has spread widened?
Has capital/portfolio state changed?
Has execution feasibility changed?
Has event context changed?
```

The envelope can therefore contribute to:

```text
CONTINUE / HOLD
REDUCE
MODIFY
EXIT
```

while independent Risk controls remain able to force action regardless of the envelope's opportunity assessment.

---

## D04.12 Worked Scenario A — Strong Shape, Poor Capturability

```text
Predicted Return Shape:
    direction            LONG
    potential            +4R
    forward support      strong
    uncertainty          acceptable

Envelope:
    liquidity            poor
    spread               excessive
    expected lifetime    12 seconds
    execution latency    high

Result:
    Shape Quality        HIGH
    Capturability        LOW
    Aperture             CLOSED
    Opportunity          REJECTED
```

This scenario demonstrates why Return Shape quality and Trading Envelope state must remain separate.

The model may be correct about the future return and still have no realistically capturable trade.

---

## D04.13 Worked Scenario B — Shape Becomes Capturable

```text
At t0:
    Return Shape         weak/moderate
    forward support      uncertain
    aperture             CLOSED

At t1:
    Return Shape         strengthening
    forward support      improving
    liquidity            good
    spread               normal
    capital              available
    aperture             OPENING

At t2:
    persistence          confirmed
    predicted lifetime   ~5 minutes
    candidate R:R        3R
    Capturability        sufficient
    aperture             OPEN

Result:
    Qualified Opportunity -> Decision / Risk
```

This scenario represents the tap opening automatically as the joint Return Shape and Trading Envelope state becomes sufficiently favorable.

---

## D04.14 Worked Scenario C — Open Position, Shape Deteriorates

```text
Trade entered:
    LONG
    candidate            3R
    expected lifetime    5 minutes

Two minutes later:
    directional support  weakening
    volatility structure changing
    predicted lifetime   collapsing
    reversal probability increasing

Envelope response:
    aperture             OPEN -> CLOSING

Possible downstream action:
    HOLD / REDUCE / EXIT
```

The key design point is that the Trading Envelope does not disappear after entry.

It continuously regulates whether the predicted return remains actionable as a position.

---

## D04.15 Worked Scenario D — Shape Improves While Envelope Deteriorates

```text
Return Shape:
    quality              increasing
    forward confidence   increasing
    potential            3R -> 4R

At the same time:

Trading Envelope:
    spread               widening
    available capital    decreasing
    portfolio exposure   increasing
    execution latency    deteriorating

Result:
    Return Shape         BETTER
    Capturability        WORSE
    Aperture             may close
```

This is a central example because it proves that the Return Shape and Trading Envelope are two distinct elastic objects.

A better prediction does not necessarily imply a better trade.

---

## D04.16 Worked Scenario E — Envelope Improves While Shape Decays

The reverse condition is also possible:

```text
Trading Envelope:
    spread               improving
    liquidity            improving
    capital              available

But:

Return Shape:
    directional support  decaying
    target probability   falling
    expected lifetime    nearly expired

Result:
    execution conditions GOOD
    Return Shape         POOR
    Opportunity          REJECTED / EXIT
```

The envelope cannot manufacture an opportunity from favorable execution conditions alone.

---

## D04.17 Logical Outputs

The Trading Envelope should eventually expose a compact logical output rather than leak all internal calculations downstream.

A conceptual output could include:

```text
candidate_id
return_shape_id
timestamp

envelope_state:
    CLOSED | OPENING | OPEN | CLOSING

capturability:
    score / probability / state TBD

aperture:
    representation TBD

entry_eligible:
    true / false

continuation_state:
    HOLD_ELIGIBLE
    REDUCE_CANDIDATE
    MODIFY_CANDIDATE
    EXIT_CANDIDATE

reason_codes:
    shape_quality
    data_integrity
    capital
    portfolio
    event_context
    liquidity
    spread
    latency
    execution_feasibility
    opportunity_lifetime

valid_until / expected_lifetime
```

The exact schema remains a later implementation artifact.

---

## D04.18 Relationship to Other Design Artifacts

The Trading Envelope depends on, but does not replace, several other artifacts.

```text
D05 Return Shape / Forward State
              |
              v
       D04 Trading Envelope
              |
              v
       D06 Opportunity Engine
              |
              v
       D07 Decision Engine
              |
              v
       D08 Risk Engine
              |
              v
       D10 Execution Policy
```

It also consumes state from:

```text
D16 Capital / Portfolio Allocation
D17 Market Universe
D18 Market Clock / Event Context
D19 Data Quality / Time Synchronization
D09 Position Lifecycle
D20 Operational health where relevant
```

This is why those components were identified as nearby "goal posts": together they define the surrounding net in which Return Shapes become capturable.

---

## D04.19 Current Logical Diagram

```text
                   RETURN FIELD F(t)

        R1(t)     R2(t)     R3(t) ... Rn(t)
          |         |         |         |
          +---------+---------+---------+
                            |
                            v
       +=======================================+
       |          TRADING ENVELOPE             |
       |                                       |
       |  +---------------------------------+  |
       |  | RETURN SHAPE                    |  |
       |  | direction / magnitude           |  |
       |  | probability / uncertainty       |  |
       |  | forward horizon / persistence   |  |
       |  | R:R geometry / lifetime         |  |
       |  +---------------+-----------------+  |
       |                  |                    |
       |                  v                    |
       |  +---------------------------------+  |
       |  | ENVELOPE CONTEXT                |  |
       |  | universe / market clock         |  |
       |  | events / data integrity         |  |
       |  | capital / portfolio             |  |
       |  | position lifecycle              |  |
       |  | liquidity / spread / latency    |  |
       |  | execution feasibility           |  |
       |  +---------------+-----------------+  |
       |                  |                    |
       |                  v                    |
       |           CAPTURABILITY               |
       |                  |                    |
       |                  v                    |
       |        ADAPTIVE APERTURE / TAP         |
       |      CLOSED <-----------> OPEN         |
       |                  |                    |
       |                  v                    |
       |       QUALIFIED OPPORTUNITY            |
       +==================+====================+
                          |
                          v
                     DECISION
                          |
                          v
                 INDEPENDENT RISK
                          |
                          v
                  EXECUTION POLICY
                          |
                          v
                       BROKER
                          |
                          v
                    OPEN POSITION
                          |
                          +----------------------+
                                                 |
                                                 v
                                      TRADING ENVELOPE
                                       re-evaluates
                                      R_i(t + delta t)
                                                 |
                                  +--------------+-------------+
                                  |              |             |
                                  v              v             v
                                HOLD           REDUCE         EXIT
```

---

## D04.20 Open Mathematical Questions

The logical design intentionally leaves several mathematical questions unresolved for experimentation.

### Return Shape Representation

Should \(\mathcal{R}_i(t,h)\) be represented as:

- A parametric function
- A probability distribution
- A vector of horizon-specific distributions
- A surface
- A tensor
- A state-transition distribution
- A hybrid representation

### Trading Envelope Representation

Should \(TE_i(t)\) be:

- A state vector
- A multidimensional feasible region
- A constraint set
- A gating function
- A probability surface
- A hybrid

### Capturability

Should Capturability be:

- A probability of realizable capture
- A normalized score
- Feasible-region membership
- Expected realizable return after execution costs
- A multi-component vector rather than one scalar

### Aperture

Should \(A_i(t)\) be:

- Continuous
- Discrete
- State-machine based
- Probabilistic
- Hybrid

### Hysteresis

We must determine:

- Opening threshold
- Closing threshold
- Minimum opening persistence
- Minimum closing persistence
- Whether thresholds depend on regime
- Whether existing positions require different thresholds from new entries

These are experimental questions rather than assumptions to encode prematurely.

---

## D04.21 Design Principle

The current Trading Envelope design can be summarized as:

> **Continuously evaluate an elastic Return Shape against an elastic control environment; allow it to become an actionable opportunity only when their joint state produces sufficient Capturability; and continue re-evaluating that relationship for the entire life of any resulting position.**

Or, in compact form:

```text
Return Shape(t)
      <-->
Trading Envelope(t)
       |
       v
Capturability(t)
       |
       v
Adaptive Aperture
       |
       v
Opportunity / Continue / Reduce / Exit
```

This is the current D04 logical-design baseline. Subsequent experiments should sharpen its mathematics without changing the meaning of the entities unless evidence requires it.

