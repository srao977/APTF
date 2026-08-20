# APTF Test 010 Dual-Engine Local Dynamics Plan V0.1

## Purpose

Identify transparent causal local dynamics for two mathematically separate engines: frozen Price `[P,P1,P2]` and frozen Volume/participation evidence. Produce diagnostic engine emissions, one-step walk-forward validation, lead/lag evidence, session-gap rules, and a Test 011 interface. Do not execute Runge-Kutta, fit trading actions, optimize P&L, modify Runtime/Emitter/Position semantics, implement AutoPilot, or connect a broker.

## Ordered procedure

1. Verify and pre-hash Runtime Core, Test 009, Test 009V, Test 007, and Test 008.
2. Freeze Price target/model families/windows/conditioning/selection and Volume interval/model candidates before fitting.
3. Phase P: load only frozen price/time/session fields, identify J_P locally, freeze one Price model from numerical walk-forward metrics.
4. Phase V: load frozen Volume fields, construct intervals 3/5/8/15, compare four independent Volume representations, and freeze one Volume engine representation.
5. Only after both engines are frozen, open frozen crossings and trading labels for descriptive lead/lag and Control observations.
6. Produce session boundary evidence, cockpit architecture, and Test 011 interface without performing integration.
7. Recompute all pretest hashes and stop.

## Architectural invariants

- Price and Volume never collapse into a scalar mixture.
- Price identities `dP/dt=P1` and `dP1/dt=P2` are structural, not fitted.
- Volume is an observed participation/result channel; no causal claim toward Price.
- Control observes both emissions independently and may be `INCONCLUSIVE`; it emits no trading action.
- Session close changes execution eligibility but resets no engine state.
