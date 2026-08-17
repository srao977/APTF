# APTF Integrated System Design Authority --- Replay-Core Foundation

**Version:** 0.1 --- Design Draft\
**Purpose:** Establish the complete integrated architecture before
further component-level design, so D01, D02, D04, and D03 cannot evolve
independently and create integration conflicts.

------------------------------------------------------------------------

## 1. Opening Architecture --- Design the System as One Continuous Chain

APTF is a **continuous signal-to-decision-and-action system**. Its
permanent architecture is not organized around an offline backtest, a
fixed decision window, or independent models that are later connected.

The canonical operating chain is:

``` text
Continuous Signals
        |
        v
       D01
        |
        v
       D02
        |
        v
       D04
        |
        v
       D03
        |
        v
Decision / Trigger / Action
```

Or:

``` text
Continuous Signals -> D01 -> D02 -> D04 -> D03 -> Decision / Trigger / Action
```

The responsibilities are:

-   **D01 --- Adaptive Parametric Model:** state intelligence and
    inference.
-   **D02 --- Forward / Return Shape:** expresses the forward geometry
    required downstream.
-   **D04 --- Trading Envelope:** determines whether the evolving
    opportunity is capturable/actionable.
-   **D03 --- Decision and Control System:** integrates the chain with
    position/execution state and commits decisions, triggers, and
    actions.

A D-number defines a **responsibility and contract**. It does not
automatically require a separately deployed process or service.

The architecture must be treated holistically. Component-level designs
may not redefine neighboring interfaces, timing assumptions, signal
semantics, trigger semantics, causal boundaries, or replay behavior
independently.

------------------------------------------------------------------------

## 2. Fundamental Signal Assumption

### 2.1 Signals are continuous

The system shall assume that signal producers are continuous unless they
are:

-   explicitly disabled;
-   manually disconnected;
-   administratively stopped; or
-   unavailable because the producer/source itself is unavailable.

There is **no artificial scientific decision cadence** imposed by the
architecture.

The 15-minute interval used during Stage 2 historical state-validity
work was a validation/evaluation horizon. It is **not** the operating
clock of the production system.

An admissible signal may arrive at any time.

Every admissible signal event may cause D01 to update the current state
`Q_t`.

A new `Q_t` may cause D02, D04, and D03 to reevaluate immediately.

One decision does not exhaust or close a nominal horizon.

Multiple decisions/actions may occur within a previous forward horizon,
and decisions may span or cross horizons.

Therefore, **intra-window and inter-window are observer descriptions,
not architectural states**.

The operating system sees only an evolving state at time `t`.

------------------------------------------------------------------------

## 3. Event-Driven, Not Window-Driven

The production model is:

``` text
Signal Event_t
    -> D01 update
    -> Q_t
    -> D02 evaluation
    -> D04 evaluation
    -> D03 evaluation
    -> possible Decision / Trigger / Action
```

The next admissible signal can begin another cycle immediately.

There is no rule such as:

``` text
start 15-minute window
-> collect observations
-> calculate
-> decide
-> wait for next window
```

Instead:

``` text
signal
-> evaluate
-> signal
-> evaluate
-> signal
-> evaluate
-> ...
```

for the lifetime of the feed.

Engineering controls such as coalescing, backpressure, debouncing, or
materiality filtering may later be used to avoid redundant computation.
Such controls are implementation optimizations and must not silently
create a new scientific decision horizon.

------------------------------------------------------------------------

## 4. Three Different Meanings of Time

The architecture must keep three concepts separate.

### 4.1 Observation / Event Time

When an authorized producer emits an admissible signal.

This may cause D01 state to advance immediately.

### 4.2 Computation Latency

The physical time required to evaluate the mathematics/control logic in:

``` text
D01 -> D02 -> D04 -> D03
```

Conceptually:

``` text
t_decision
≈ t_observation
+ T_D01
+ T_D02
+ T_D04
+ T_D03
```

These terms represent **execution latency**, not scientific horizons.

### 4.3 Forward Horizon

The mathematical extent over which the current inferred/forward state
remains meaningful.

A forward horizon does **not** instruct the system to wait before
accepting another signal or making another decision.

Therefore:

``` text
model time != wall-clock decision interval
```

and:

``` text
forward horizon != decision cadence
```

------------------------------------------------------------------------

## 5. Observation Continuity and Execution Availability Are Separate

The architecture must distinguish:

``` text
Can observe? != Can execute?
```

Signals may continue when a particular instrument or venue is not
executable.

For example, authorized signals may continue during periods when WING
itself cannot be traded.

D01 may continue evolving `Q_t`.

D02 may continue evolving forward geometry.

D04 may continue evolving its Trading Envelope.

D03 constrains **actions** according to current execution availability.

Execution availability must not automatically stop state inference.

A trigger generated while execution is unavailable must not simply be
queued and blindly executed later. When execution becomes available, D03
must evaluate the **then-current** system state and execution context.

------------------------------------------------------------------------

## 6. Signal Terminology

The architecture should not assume every input is a market-price tick.

Use the broader term:

**Signal Event** or **Observation Event**

because future authorized producers may include heterogeneous signals
with different cadences, for example:

-   price;
-   volume;
-   options-derived observations;
-   correlated instruments;
-   macro signals;
-   news/event signals;
-   other authorized external observations.

Each signal must retain causal event/source identity appropriate to its
contract.

------------------------------------------------------------------------

## 7. Canonical Component Responsibilities

### 7.1 D01 --- Adaptive Parametric Model

**Responsibility:** market/system state inference.

D01 is the sole market-state intelligence authority.

It consumes authorized causal observations and emits the frozen `Q_t`
state.

Stage 3 must not create a competing independent market predictor.

### 7.2 D02 --- Forward / Return Shape

**Responsibility:** express the D01 forward state in the forward/Return
Shape representation required by the Trading Envelope.

D01 v0.2 now emits substantially richer forward information than existed
when the original D02 concept was created.

Therefore D02 must be reconciled before further implementation.

The design must determine whether D02:

1.  performs independent required mathematics; or
2.  is now primarily a deterministic projection/representation of the
    frozen D01 FMO.

If D02 is only a deterministic transformation, it need not become a
large standalone model or separately deployed module.

### 7.3 D04 --- Trading Envelope

**Responsibility:** determine dynamic capturability/actionability.

D04 remains the adaptive gate between forward opportunity and actionable
opportunity.

It may maintain dynamic envelope state and transitions/triggers.

D04 must not become the broker/execution system.

### 7.4 D03 --- Decision and Control System

Retire the earlier name **Real-Time Decision System**.

The preferred name is:

**D03 --- Decision and Control System**

The architecture is continuous and responsive but does not claim hard
real-time behavior.

D03 integrates:

-   current causal state;
-   D02 forward representation;
-   D04 Trading Envelope state/triggers;
-   current position;
-   pending execution state;
-   execution availability;
-   other explicitly authorized non-predictive operational context.

D03 commits decisions, triggers, and actions.

------------------------------------------------------------------------

## 8. Frozen D01 -\> Q_t Boundary

The frozen pre-Stage-3 architecture established `Q_t` as the canonical
causal D01 output.

Its top-level structure is:

``` text
Q_t = {
  identity: {
    model_time,
    entity_id,
    model_version
  },

  current_state: {
    state_level,
    state_velocity,
    state_acceleration,
    state_curvature,
    strength,
    coherence,
    persistence,
    perturbation_magnitude,
    perturbation_class,
    uncertainty,
    reversal_propensity,
    state_support_ratio,
    observation_half_life,
    forward_half_life
  },

  forward_state: {
    forward_interval,
    forward_samples
  }
}
```

The frozen contract contains 19 canonical top-level fields.

Diagnostic/internal DMO fields are not automatically Stage 3 inputs.

Stage 2 realized observer values are not `Q_t`.

Future observations are not `Q_t`.

Future outcome labels are not `Q_t`.

The sealed reserve is not `Q_t`.

------------------------------------------------------------------------

## 9. Integrated Operating Chain

The canonical permanent chain is:

``` text
Signals -> D01 -> D02 -> D04 -> D03 -> Decision / Trigger / Action
```

D03 is downstream in the logical chain because it consumes the
integrated intelligence/control state and commits action.

This does **not** mean D03 is passive.

D03 is the controller and operating integration responsibility around
the evolving system.

Events capable of causing reevaluation may include:

-   a new authorized observation;
-   a material D01 state change;
-   a D02 forward-shape change;
-   a D04 envelope transition;
-   a position change;
-   an order/fill/cancellation/rejection event;
-   a change in execution availability;
-   an administrative feed enable/disable event.

------------------------------------------------------------------------

## 10. D03 Input Boundary --- Design Direction

The exact contract remains to be designed, but the conceptual boundary
is:

``` text
D03Input_t = (
    Q_t,
    D02_t,
    D04_t,
    ExecutionContext_t
)
```

This may later be simplified if D02/D04 reconciliation shows that some
information is redundant.

`ExecutionContext_t` must be causal and non-predictive.

Potential operational fields may include:

``` text
current_position
pending_order_state
execution_available
venue/session_state
already_realized_fills
```

No future outcome belongs in the contemporaneous decision path.

------------------------------------------------------------------------

## 11. Decision, Trigger, and Action

Stage 3 must be tightly integrated with committed decisions and
actions/triggers.

D04 state transitions and other material system changes may generate
triggers consumed by D03.

D03 converts the integrated causal state into a committed
decision/action request.

The precise trading semantics remain a Stage 3 design task.

Candidate position-oriented semantics include:

``` text
TARGET_LONG
TARGET_SHORT
TARGET_FLAT
```

from which operational actions could later be derived, such as:

``` text
ENTER
EXIT
HOLD
REVERSE
```

This document deliberately does **not** select trading thresholds or
trading rules.

------------------------------------------------------------------------

## 12. Live Operation and Backtest Replay Are the Same System

Backtest replay must not become a separate trading architecture.

The final backtest validates the **ENTIRE integrated system**.

### 12.1 Normal operation

``` text
Live/Continuous Signals
    -> Normalization
    -> D01
    -> D02
    -> D04
    -> D03
    -> Decision / Trigger / Action
    -> Execution
```

### 12.2 Historical replay

``` text
Historical Signal Replay
    -> SAME Normalization
    -> SAME D01
    -> SAME D02
    -> SAME D04
    -> SAME D03
    -> Decision / Trigger / Action
    -> Replay Execution / Outcome Evaluation
```

The historical replay adapter replaces the source of time/signals.

It does **not** replace the decision architecture.

------------------------------------------------------------------------

## 13. Replay Equivalence Invariant

Given:

-   the same causal observation sequence;
-   the same initial model state;
-   the same initial control/position state; and
-   the same causal execution context,

the integrated:

``` text
D01 -> D02 -> D04 -> D03
```

chain must emit the same decisions regardless of whether observations
arrive from:

-   a live/continuous feed; or
-   deterministic historical replay.

The production decision chain must not know that future observations
happen to exist on disk during replay.

------------------------------------------------------------------------

## 14. Backtest as Validation of the Entire System

The reserved final backtest is not another isolated D01 experiment.

It is an **end-to-end validation of the complete signal-to-action
architecture**.

It should validate, without tuning against the reserve:

1.  causal signal ingestion;
2.  point-in-time normalization;
3.  D01 state evolution;
4.  `Q_t` emission;
5.  D02 forward/Return Shape behavior;
6.  D04 Trading Envelope behavior;
7.  D04 state transitions/triggers;
8.  D03 decision/control behavior;
9.  committed decision timing;
10. action/position transitions;
11. replay execution assumptions;
12. causal integrity of the complete chain;
13. realized outcomes after decision commitment;
14. benchmark comparison after commitment;
15. final P&L/performance and other agreed system metrics.

The second six months remain sealed until:

-   integrated architecture is frozen;
-   Stage 3/D03 decision behavior is frozen;
-   D02/D04 reconciliation is complete;
-   execution assumptions are frozen; and
-   final backtest scoring is frozen.

The reserve must not be consumed to iteratively design or tune the
decision system.

------------------------------------------------------------------------

## 15. Outcome Evaluation

The architecture does not need to invent D05 or a permanent Stage 4
merely to evaluate outcomes.

A decision must first be irrevocably committed.

Later realized observations may then be associated with that earlier
decision.

Therefore:

``` text
Q_t
-> D02
-> D04
-> D03
-> committed Decision_t
```

must occur before:

``` text
future realized outcome
benchmark outcome/decision
future price
P&L
performance metrics
```

are available to the evaluator for that decision.

In live operation, these outcomes become available naturally as time
advances.

In historical replay, the replay harness must enforce the same causal
ordering even though future data already exists on disk.

------------------------------------------------------------------------

## 16. Integration Invariants

The following should govern all further component design.

### 16.1 Holistic Architecture Invariant

Component designs may not independently redefine neighboring interfaces
or system semantics.

### 16.2 Continuous Signal Invariant

The operating chain has no artificial scientific decision cadence.

### 16.3 Event Evaluation Invariant

Every admissible material observation may cause a new integrated
evaluation.

### 16.4 Observation / Execution Separation

Inability to execute does not automatically stop state inference.

### 16.5 D01 Authority Invariant

D01 remains the sole market-state inference authority.

### 16.6 No Future Leakage Invariant

Future observations, outcome labels, benchmark decisions, future P&L,
and reserve values cannot enter the contemporaneous decision path.

### 16.7 Replay Equivalence Invariant

Live operation and historical replay use the same production decision
chain.

### 16.8 Decision Commitment Invariant

Outcome evaluation occurs only after the corresponding decision is
fixed.

### 16.9 Reserve Governance Invariant

Final reserve data is not used for iterative Stage 3 design or tuning.

### 16.10 Logical, Not Necessarily Physical, Modularity

D01, D02, D04, and D03 are architectural responsibilities. They do not
automatically require four independently deployed services.

------------------------------------------------------------------------

## 17. System-Level Authority and Controlled Component Evolution

This document is the **system-level design authority** above the
individual D01, D02, D04, and D03 component specifications.

Its purpose is not to freeze every implementation detail permanently.
Its purpose is to preserve the integrated system invariants while
allowing evidence-driven changes inside one or more components.

The authority hierarchy is:

``` text
Integrated System Design Authority
              |
     +--------+--------+--------+
     |        |        |        |
    D01      D02      D04      D03
```

A component may be modified when evidence justifies the change, provided
that either:

1.  the change remains compliant with this system-level authority; or
2.  the change genuinely requires a system invariant to change, in which
    case this architecture must be explicitly revised rather than being
    silently changed from inside a component.

This gives the project a stable basis for both:

-   **component validation** --- whether a changed component still
    satisfies the integrated architecture; and
-   **whole-system validation** --- whether the complete frozen core
    turns causal signals into useful decisions.

The architecture therefore supports controlled iteration without
allowing local component changes to create system-level drift.

------------------------------------------------------------------------

## 18. Immediate Experimental Target --- The Replay Core

The immediate target is **not** a production trading integration.

The immediate target is the complete decision-producing core:

``` text
Historical Observation Stream
        |
        v
       D01
        |
        v
       D02
        |
        v
       D04
        |
        v
       D03
        |
        v
Committed Decision
```

This integrated core becomes the **APTF Replay System** when driven by
chronologically replayed historical observations.

The development sequence is:

``` text
D01 frozen
   ->
D02 mapping / Return Shape completion
   ->
D04 integration using the already implemented physical prototype
   ->
D03 Decision and Control completion
   ->
Integrated Core Freeze
   ->
Final Backtest Contract Freeze
   ->
Sealed Six-Month Replay / Backtest
```

No production market-feed adapter, broker adapter, or trading-platform
output adapter is required to determine whether the core decision
architecture is empirically worthwhile.

------------------------------------------------------------------------

## 19. Historical Data Governance

The available historical dataset is deliberately divided into two roles.

### 19.1 First Six Months --- Development Evidence

The first six months have already been consumed for D01 historical
state-validity work.

They remain the only historical period available for development
activities before final backtest, including:

-   D02 mapping and integration development;
-   D04 integration verification;
-   D03 design and implementation;
-   integrated replay plumbing;
-   deterministic/causal tests;
-   debugging;
-   architecture consistency testing; and
-   pre-reserve system verification.

Repeated analysis of this period must remain bounded. The purpose is to
complete and verify the architecture, not to recursively search the same
data until favorable trading behavior is obtained.

### 19.2 Second Six Months --- Sealed Final-Backtest Reserve

The second six months remain sealed until all of the following are
frozen:

-   D01;
-   D02;
-   D04 integration;
-   D03;
-   the integrated replay core;
-   execution/replay assumptions; and
-   the final backtest scoring/benchmark contract.

The reserve must not be used to design, tune, select, or repair
D01/D02/D04/D03 behavior.

Once opened, it is the independent end-to-end test of the frozen
decision-producing system.

------------------------------------------------------------------------

## 20. Replay System Architecture

The replay system substitutes a historical causal source for a future
live signal source while preserving the same decision-producing core.

``` text
Historical Source
      |
      v
Causal Replay / Normalized Observation Boundary
      |
      v
D01 -> D02 -> D04 -> D03
                       |
                       v
                Committed Decision
                       |
                       v
                Replay Evaluator
                       |
                       v
          Realized Outcome / Benchmark
```

The replay source must reveal observations chronologically.

For each decision time `t`:

``` text
causal observations through t
        ->
D01 -> D02 -> D04 -> D03
        ->
Decision_t irrevocably committed
        ->
future outcome becomes evaluable later
```

Historical outcome/decision columns, future prices, future P&L,
benchmark labels, and other future-derived values are **evaluation-side
information only**.

They must never enter D01, D02, D04, or D03 before the corresponding
decision is committed.

------------------------------------------------------------------------

## 21. Final Backtest --- Validation of the Entire System

The final six-month replay is the hard benchmark for the **entire
integrated system**, not another D01 validation cycle.

It validates:

``` text
Observation
   -> D01 state inference
   -> D02 Return Shape
   -> D04 Trading Envelope / Capturability
   -> D03 Decision and Control
   -> committed decision/action
   -> realized outcome
```

The final backtest must answer whether the complete frozen system
converts unseen causal observations into decisions that outperform the
**pre-registered comparison benchmarks and performance criteria**.

The meaning of "better" must be frozen before the reserve is opened.

The project must not inspect the reserve and then choose whichever
metric makes APTF appear favorable.

The final backtest contract should therefore pre-register the agreed
measures, which may include appropriate combinations of:

-   decision correctness;
-   opportunity capture;
-   adverse-decision rate;
-   realized return;
-   drawdown;
-   turnover;
-   risk-adjusted performance;
-   benchmark-relative performance; and
-   other explicitly justified system metrics.

The exact metric set is a later design task, but it must be fixed before
reserve access.

------------------------------------------------------------------------

## 22. Productionization Is Conditional on Replay Evidence

Input and output adapters are intentionally **post-backtest concerns**.

If the sealed replay demonstrates that the integrated decision core
warrants continuation, the production architecture becomes:

``` text
Market / External Signal Sources
             |
             v
       Input Adapter
             |
             v
     D01 -> D02 -> D04 -> D03
                         |
                         v
                   Output Adapter
                         |
                         v
              Trading / Execution System
```

The adapters must not alter the scientific meaning of the core.

### 22.1 Future Input Adapter

The future input adapter will:

-   connect to one or more live/continuous signal providers;
-   convert provider-specific events into the same canonical causal
    observation contract used by replay;
-   preserve event/source identity and timing;
-   enforce data-quality/interface rules; and
-   contain no competing market-state inference.

D01 remains the state-intelligence authority.

### 22.2 Future Output Adapter

The future output adapter will:

-   receive committed D03 decisions/actions;
-   translate them into the contract required by the selected
    trading/execution platform;
-   report execution acknowledgements/fills/state back through the
    authorized operational boundary; and
-   contain no independent trading-intelligence logic.

The production adapters therefore surround the same core that was
validated in replay.

``` text
REPLAY:
Historical Source -> [ D01 -> D02 -> D04 -> D03 ] -> Replay Evaluator

PRODUCTION:
Input Adapter     -> [ D01 -> D02 -> D04 -> D03 ] -> Output Adapter
```

The bracketed core is intended to remain scientifically identical.

------------------------------------------------------------------------

## 23. Updated Component Inventory

  -----------------------------------------------------------------------
  Component / Boundary    Current status          Immediate role
  ----------------------- ----------------------- -----------------------
  D01 --- Adaptive        Completed through Stage Sole market-state
  Parametric Model        1 and Stage 2; frozen   inference authority;
                                                  emits frozen `Q_t` /
                                                  FMO

  D02 --- Return Shape    Contract exists;        Deterministically
                          dedicated completed     translate D01 state/FMO
                          implementation not yet  into return-space
                          established             geometry required by
                                                  D04; add mathematics
                                                  only where genuinely
                                                  required

  D04 --- Trading         Physical prototype      Integrate existing D04
  Envelope                implemented and         with actual D02 Return
                          exercised               Shape and verify
                                                  end-to-end behavior

  D03 --- Decision and    Integrated completion   Convert the causal
  Control                 remains                 integrated state into
                                                  committed
                                                  decisions/actions

  Replay source/evaluator To complete before      Drive the frozen core
                          final backtest          causally and evaluate
                                                  decisions only after
                                                  commitment

  Live input adapter      Deferred until          Convert provider
                          successful final replay signals to the
                                                  canonical D01
                                                  observation boundary

  Production output       Deferred until          Convert D03 committed
  adapter                 successful final replay actions to the selected
                                                  trading/execution
                                                  system
  -----------------------------------------------------------------------

This inventory must be verified against the repository before any status
is treated as final authority. A concept mentioned inside another
document is not automatically a completed standalone design or
implementation.

------------------------------------------------------------------------

## 24. Updated Near-Term Work Sequence

The immediate work sequence is intentionally narrow:

### Step 1 --- Repository Inventory Verification

Establish the authoritative status of D01, D02, D04, D03, replay
artifacts, and governing design files from repository evidence.

### Step 2 --- D02 Mapping / Return Shape Completion

Create the field-by-field mapping:

``` text
D01 Q_t / FMO -> D02 -> D04 ReturnShape
```

Identify which D04-required fields are direct mappings, deterministic
transformations, or genuine mathematical gaps.

D02 must not become a second market-state inference engine.

### Step 3 --- D04 Integration

Connect the existing implemented D04 prototype to actual D02 output.

Do not redesign D04 merely because integration is occurring.

### Step 4 --- D03 Completion

Define and implement the Decision and Control contract, decision
semantics, trigger/action semantics, and causal execution-context
boundary.

### Step 5 --- Integrated Replay Core

Run the complete:

``` text
D01 -> D02 -> D04 -> D03
```

chain on development-period causal replay only to establish
deterministic operation and integration correctness.

### Step 6 --- Core Freeze

Freeze the complete decision-producing core.

### Step 7 --- Final Backtest Contract Freeze

Pre-register the independent reserve evaluation and benchmark criteria.

### Step 8 --- Open the Sealed Six-Month Reserve Once

Run the complete frozen replay system against the unseen reserve.

### Step 9 --- Productionization Decision

Only if the result warrants continuation should the project design and
implement live input and trading-system output adapters.

------------------------------------------------------------------------

## 25. Updated Governance Status

  -----------------------------------------------------------------------
  Item                                Status
  ----------------------------------- -----------------------------------
  Stage 1 / D01 synthetic-semantic    Complete and frozen
  work                                

  Stage 2 / D01 historical            Complete and frozen
  state-validity work                 

  D01 / `Q_t` contract                Frozen

  First six months                    Consumed development evidence

  D02                                 Next integration/mapping task

  D04 physical prototype              Implemented and exercised

  D04 connection to actual D02 output Required

  D03                                 Complete integrated
                                      decision/control design and
                                      implementation next

  Integrated replay core              Not yet complete

  Final backtest scoring contract     Must be frozen before reserve
                                      access

  Second six months                   Sealed final-backtest reserve

  Live input adapter                  Deferred until replay result
                                      warrants productionization

  Trading-system output adapter       Deferred until replay result
                                      warrants productionization
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 26. Revised Design Decision

The project shall first complete and freeze the **decision-producing
replay core**:

``` text
D01 -> D02 -> D04 -> D03
```

and then validate that entire core exactly once against the sealed
six-month reserve under a pre-registered backtest contract.

Production connectivity is deliberately outside the immediate
experiment.

Only after the replay evidence justifies continuation will live input
adapters and trading/execution output adapters be incorporated around
the validated core.

This sequencing protects the reserve, prevents production engineering
from obscuring the scientific question, and gives APTF a single hard
test:

> **Can the frozen integrated system convert previously unseen causal
> market observations into decisions whose realized performance exceeds
> the benchmarks and acceptance criteria fixed before the reserve is
> opened?**
