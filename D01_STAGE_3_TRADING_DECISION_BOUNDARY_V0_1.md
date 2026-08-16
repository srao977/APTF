# D01 Stage 3 Trading Decision Boundary v0.1

## 1. Status and Scope

**Status:** BOUNDARY ONLY - STAGE 3 DESIGN NOT STARTED

This document defines the boundary between accepted Stage 2 state-validity evidence and future Stage 3 trading-decision design. It does not define or implement BUY/SELL/HOLD rules.

## 2. System Boundary

```text
authorized causal market observations
    -> frozen D01 v0.2
    -> D01 state vector
    -> future Stage 3 Decision Processor
    -> committed decision
```

Stage 3 begins only after D01 emits its causal state. D01 remains unchanged.

## 3. Evidence Categories Presented to Stage 3

### Category A - Empirically Supported

- Strength
- Perturbation Magnitude

Stage 3 design may describe these as empirically supported D01 state information. It may not infer that they are profitable, directional, causal, or individually sufficient for a decision.

### Category B - Limited / Unresolved

- Coherence
- Uncertainty
- Reversal Propensity
- Perturbation Class
- Observation Half-Life
- Forward Half-Life
- Forward Interval

These must not be silently promoted to validated predictors. Any future use must preserve and disclose their limited/unresolved status.

### Category C - Empirically Unsupported Under Frozen Stage 2 Semantics

- State/Kinematics
- Persistence

Stage 3 must not claim that State/Kinematics is a historically validated directional predictor or that Persistence is a historically validated realized-persistence predictor. They may remain available as mathematically defined state coordinates only under an explicitly justified future design.

## 4. Causal Restrictions

Stage 3 causal inputs may include only information available at or before decision time and the frozen D01 state emitted from such information.

Future observations, outcomes, targets, recommendations, vendor decisions, human annotations, P&L, and reserve data may not enter decision construction, thresholds, parameters, state selection, or feature selection.

## 5. Outcome Isolation and Commitment

Required evaluation order:

```text
causal observations at or before t
    -> D01 state_t
    -> Stage 3 processor
    -> decision_t
    -> immutable decision commitment
    -> future/outcome reveal
    -> evaluator score
```

Historical outcome/decision columns, if scientifically appropriate, are evaluator evidence only. They are never causal model/decision inputs.

## 6. Difference From Stage 2

Stage 2 tested whether D01 state coordinates corresponded to independently realized future state geometry.

Stage 3 will test whether a complete frozen decision system makes useful decisions under explicit market, timing, position, cost, execution, benchmark, and scoring assumptions.

State validity is not trading validity. Stage 2 correlations do not establish Stage 3 performance.

## 7. Required Future Stage 3 Design Freeze

Before implementation and reserve access, a future Stage 3 design must freeze:

- exact D01 coordinates admitted to the decision processor;
- treatment of each Stage 2 evidence category;
- decision vocabulary and deterministic decision algorithm;
- entry and exit conditions;
- decision horizon and timing;
- position/exposure assumptions;
- transaction-cost assumptions;
- execution/availability assumptions;
- causal ordering and decision commitment mechanism;
- evaluator outcomes and benchmark definitions;
- scoring metrics and uncertainty/reporting rules;
- failure criteria and non-retry policy;
- implementation, tests, dependencies, and output schema.

This boundary document selects none of those values.

## 8. Reserve Role

The reserve is exclusively the final one-way out-of-sample backtest for the complete frozen executable system. It is not available during Stage 3 design, implementation, debugging, threshold selection, or preliminary evaluation.

## 9. Prohibitions

This document does not authorize:

- Stage 3 implementation;
- BUY/SELL/HOLD logic;
- trading rules;
- position sizing;
- portfolio construction;
- transaction-cost calibration;
- execution simulation;
- backtesting;
- P&L calculation;
- reserve access.

## 10. Current Status

- Boundary defined: YES
- Trading rules defined: NO
- Decision algorithm implemented: NO
- Backtest executed: NO
- Reserve sealed: YES
