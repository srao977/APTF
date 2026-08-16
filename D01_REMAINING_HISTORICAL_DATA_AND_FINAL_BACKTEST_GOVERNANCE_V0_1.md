# D01 Remaining Historical Data and Final Backtest Governance v0.1

## 1. Data Status

### First Six Months

```text
[2022-09-30T04:00:00-04:00, 2023-03-30T04:00:00-04:00)
```

Status: **CONSUMED / DEVELOPMENT EVIDENCE**

This period produced the accepted Stage 2 empirical characterization. It is no longer blind evidence. It may support bounded Stage 3 design, but it may not become an unlimited strategy-search space.

### Second Six Months

```text
[2023-03-30T04:00:00-04:00, 2023-09-30T04:00:00-04:00)
```

Status: **SEALED FINAL-BACKTEST RESERVE**

Reserve access remains prohibited until the complete executable trading system, including all decision, position, execution, cost, benchmark, and scoring rules, has been frozen.

## 2. Development Governance

**DEVELOPMENT IS PERMITTED. UNBOUNDED HISTORICAL OPTIMIZATION IS NOT.**

Stage 3 must be derived from explicit design rationale. The consumed first period must not be used to search hundreds of strategies, thresholds, horizons, state combinations, features, policies, or transaction assumptions and select the historical winner.

No recursive Stage 2 investigation is authorized. Existing questions raised by Stage 2 remain observations, not invitations to mine the consumed corpus.

## 3. Reserve Prohibitions

Before the complete executable system is frozen, the second period shall not be used for:

- D01 diagnosis, tuning, redesign, or confirmation;
- Stage 2 reruns or alternate hypotheses;
- horizon, threshold, feature, state, or rule selection;
- Stage 3 development or trading-rule selection;
- position, execution, or cost calibration against outcomes;
- profitability inspection or preliminary backtesting;
- exploratory charts, statistics, labels, correlations, or outcomes.

Reserve metadata may remain known only as already frozen identity and boundary information.

## 4. Outcome Isolation

Historical decision, annotation, target, recommendation, and outcome fields may be used only after a future Stage 3 decision is committed, and only as explicitly frozen evaluator evidence.

They must never enter D01 inputs, Stage 3 causal inputs, decision construction, threshold selection, feature/state selection, or parameter selection.

Required causal order:

```text
authorized observations at or before t
    -> D01 state
    -> frozen Stage 3 decision mechanism
    -> commit decision_t
    -> reveal future/outcome benchmark
    -> score decision_t
```

Outcomes are evaluators, not inputs.

## 5. Final Backtest Purpose

The final reserve backtest asks:

> If the complete frozen system had been operating live during this previously unseen six-month period, what decisions would it have made, and how would those decisions have compared with what actually happened?

At every timestamp, only information available at or before that timestamp may be consumed. The decision is committed before future outcomes are exposed.

## 6. Freeze Requirement

Before reserve access, freeze at minimum:

- exact D01 inputs used by Stage 3;
- evidence-status treatment for supported, unresolved, and unsupported coordinates;
- decision states and deterministic algorithm;
- entry/exit and horizon rules;
- position and exposure assumptions;
- transaction-cost and execution assumptions;
- decision timing and causal order;
- evaluation outcomes and benchmark definitions;
- scoring metrics and report schema;
- implementation source, dependencies, tests, and launcher.

Any unresolved executable choice blocks reserve access.

## 7. One-Way Reserve Backtest

Once reserve execution begins:

- no model, rule, threshold, horizon, weight, feature, scoring, cost, or execution change;
- no restart after poor results;
- no fallback strategy;
- no reserve-driven debugging of scientific behavior;
- no second attempt against the same reserve.

The result may be successful, mixed, weak, or unsuccessful. All are valid final outcomes.

## 8. Failure Governance

**FAILURE TO ACHIEVE SATISFACTORY TRADING PERFORMANCE DOES NOT AUTHORIZE POST-HOC MODIFICATION AND RE-EXECUTION AGAINST THE SAME RESERVE PERIOD.**

A future model/system may be developed afterward, but the used reserve can no longer support an untouched out-of-sample claim for that successor.

## 9. Current Attestation

- First six months consumed: YES
- Reserve sealed: YES
- Reserve accessed: NO
- Reserve outcomes inspected: NO
- Stage 2 repeated: NO
- Stage 3 implemented: NO
- Backtest executed: NO
