# D02 Return Shape Design v0.1

## 1. Purpose

D02 expresses frozen D01 causal state and FMO projections in the `ReturnShape` representation consumed by D04. This document reconciles the boundary; it does not implement or freeze D02.

**Decision:** D02 DESIGN NOT FREEZE-READY.

## 2. Position in the Integrated System Design Authority

The governing chain is:

```text
Signals -> D01 -> D02 -> D04 -> D03 -> Decision / Trigger / Action
```

`APTF_INTEGRATED_SYSTEM_DESIGN_AUTHORITY_REPLAY_CORE_V0_2.md` governs conflicts. D01 remains the sole market-state inference authority. D02 cannot redefine D01, capturability, execution context, or decision semantics.

## 3. D02 responsibility

D02 is responsible for constructing a causal, versioned ReturnShape representation from Q_t/FMO using reviewed deterministic mathematics. Its target architectural form is a **deterministic ReturnShape constructor**, not an independent model. The current design classification remains **DESIGN AMBIGUITY** because eight required semantics lack authorized mathematics.

## 4. Explicit non-responsibilities

D02 does not:

- infer new market state, learn parameters, adapt, or predict independently;
- modify D01 or reinterpret unsupported fields as validated predictors;
- evaluate capturability, aperture, hysteresis, envelope state, or feasibility;
- create candidates, positions, orders, execution availability, or portfolio state;
- emit BUY/SELL/HOLD, targets, triggers, actions, or trading rules;
- inspect outcomes, observer fields, future records, or reserve data.

## 5. D01 input authority

The only market-state input authority is the frozen pair:

- `D01_QT_OUTPUT_CONTRACT_V0_1.md`;
- `D01_QT_OUTPUT_SCHEMA_V0_1.json`.

The pre-Stage-3 freeze SHA256 `B6ED942E41EC1C72350CF9247597E5819A942DBE9D04770C23E243204165B235` and all linked frozen artifacts were verified before this design.

## 6. Q_t/FMO input contract

Q_t contains exactly 19 canonical top-level fields: 3 identity, 14 current state, and 2 forward state. `forward_samples` contains seven coordinates per sample: `tau`, `level`, `velocity`, `uncertainty`, `strength`, `persistence`, and `reversal_propensity`. The accepted default sample count is eight; consumers must honor the actual list and `tau` values rather than assume fixed spacing or count.

Nine DMO diagnostic/internal fields and all observer/future/reserve concepts are prohibited.

## 7. D04 ReturnShape output contract

The current D04 target is the 16-field Pydantic model in `d04_trading_envelope/src/aptf_d04/models/return_shape.py`. Fourteen fields are mandatory; `active` and `metadata` have defaults. Exact field metadata and consumers are inventoried in `D02_REPOSITORY_AND_CONTRACT_INVENTORY_V0_1.md` and mapped in the JSON companion.

The current target contract is a prototype interface, not validated production mathematics. `candidate_id` belongs outside D02, and `candidate_rr` has no authorized Q_t source and no current D04 core consumer.

## 8. Field-by-field mapping

The normative reconciliation artifact is `D02_D01_TO_D04_RETURNSHAPE_MAPPING_V0_1.json`.

- DIRECT: 3.
- DETERMINISTIC_TRANSFORMATION: 2.
- FMO_GEOMETRY_DERIVATION: 0 complete definitions.
- CONSTANT_OR_CONFIGURATION: 1.
- CONTEXT_NOT_D02: 1.
- GENUINE_D02_MATHEMATICAL_GAP: 8.
- OBSOLETE_OR_DUPLICATIVE: 1.

Current mandatory field coverage is 5/14.

## 9. Return Shape geometry

D01 already provides a causal projected path:

$$
\hat L_t(\tau)=L_t+V_t\tau+\frac{1}{2}A_t\tau^2,
$$

with coordinate-wise half-life decay/expansion. D02 may eventually represent signed displacement, slopes between FMO coordinates, path extent, and projected support/decay only after the scalar definitions, horizon selection, and normalization are reviewed.

Stage 2 realized-observer path statistics are evaluation-side concepts and cannot be copied into D02 as inputs or labels. Their existence does not define D02 geometry.

## 10. Deterministic transformations

Currently determined transformations are:

```text
timestamp         = Q_t.model_time
uncertainty       = Q_t.uncertainty
persistence_score = Q_t.persistence
metadata          = {}
```

Stable `return_shape_id` and monotonic `version` are deterministic protocol transformations, but their exact serialization and persistence contract require an engineering clarification before implementation. They introduce no market inference.

## 11. Genuine mathematical gaps

The unresolved fields are `direction`, `shape_quality`, `forward_support`, `expected_lifetime_seconds`, `magnitude_score`, `decay_score`, `reversal_risk`, and `active`. Each requires a scientific definition that is not supplied by frozen D01 or current D04 source. `D02_DESIGN_AMBIGUITIES_V0_1.md` is controlling for these gaps.

## 12. Stage 2 evidence lineage

| Upstream dimension | Frozen empirical status | D02 rule |
|---|---|---|
| Strength | SUPPORTED | Preserve narrow association claim only |
| Perturbation Magnitude | SUPPORTED | Never treat as expected-return magnitude |
| Coherence | PARTIALLY_SUPPORTED | Preserve unresolved qualification |
| Uncertainty | INCONCLUSIVE | Directly available, not validated risk information |
| Reversal Propensity | INCONCLUSIVE | Not a validated probability or timing signal |
| Perturbation Class | INCONCLUSIVE | Not validated decision evidence |
| Observation/Forward Half-Life | INCONCLUSIVE | Not validated useful-state duration |
| Forward Interval | INCONCLUSIVE | Range warning retained; not a validated horizon |
| State/Kinematics | UNSUPPORTED | Mathematically defined, not validated directional prediction |
| Persistence | UNSUPPORTED | Mathematically defined, not validated realized persistence |

Composite outputs have MIXED lineage. Evidence labels are metadata, not weights or gates. No dimension is zeroed, deleted, tuned, or confidence-weighted.

## 13. Causality rules

D02 may consume only Q_t and fixed reviewed configuration. It must reject unknown fields and must never consume future observations, realized observer fields, outcome labels, benchmark decisions, future P&L, reserve information, or D01 diagnostics. `D02_CAUSALITY_AND_INFORMATION_BOUNDARY_V0_1.md` is normative.

## 14. Initialization behavior

The scientific transformation must operate on the first valid Q_t without warm-up, imputation, or future lookahead. Protocol version state, if adopted, initializes to version 1 for a newly derived stable shape ID. Missing or invalid Q_t prevents ReturnShape emission. Scientific gap fields have no authorized initialization value; placeholder zeros or constants are prohibited.

## 15. Statefulness/statelessness

Target scientific behavior: **stateless** with respect to market inference; each shape value must be a function of current Q_t and fixed configuration.  
Permitted protocol behavior: **minimally stateful** only for monotonic `version` and deterministic identity continuity.  
Current final status: unresolved `active` expiration under context-only reevaluation prevents a fully closed lifecycle contract.

## 16. Adaptation policy

D02 is **non-adaptive**. It may not update parameters, learn from outcomes, retain error history, calibrate on replay, or respond to Stage 2 evidence by altering mappings. D01 owns adaptation.

## 17. Configuration policy

Future D02 configuration must be:

- explicit, typed, versioned, and immutable for a run;
- limited to reviewed representation choices;
- identical in replay and future live use;
- excluded from performance-driven reserve tuning;
- unable to inject observer, outcome, diagnostic, or execution values.

No unresolved scientific formula may be hidden as a configuration default.

## 18. Numerical bounds

Outputs must satisfy the actual D04 contract:

- normalized scores in `[0,1]`;
- `version >= 1` and strictly increasing per stable shape ID;
- finite `timestamp` preserving causal order;
- positive `expected_lifetime_seconds` whenever `active=true`;
- a valid `Direction` enum;
- finite scalar values only.

Input Q_t bounds remain those in the frozen schema. Unbounded `state_level` and `state_support_ratio` cannot be clamped or normalized without explicit mathematics.

## 19. Failure behavior

D02 must fail closed and emit no valid ReturnShape when:

- Q_t is missing, malformed, nonfinite, out of contract, or noncausal;
- FMO sample count/coordinates violate the Q_t contract;
- an unknown Q_t field is requested;
- identity/version continuity cannot be guaranteed;
- a required output formula is unresolved;
- output validation fails.

It must not replace failures with zeros, neutral direction, average scores, stale values, or future imputations.

## 20. Data-quality behavior

D01 `data_quality` is intentionally excluded from Q_t and cannot be promoted. If D01 cannot produce a valid Q_t, D02 emits nothing. D04 `EnvelopeContext.data_integrity` remains the operational data-quality/safety input and is not a D02 ReturnShape field.

## 21. Determinism requirements

For identical Q_t, configuration, and initial protocol state, D02 must produce identical semantic values, IDs, versions, errors, and serialized canonical output. No randomness, wall-clock dependence, process identity, unordered aggregation, or external service is allowed.

## 22. D04 integration contract

D04 receives `ReturnShape` and `EnvelopeContext` separately. D02 must not calculate capturability or anticipate D04 weights/thresholds. D04 must not be modified by this design. A future reviewed interface clarification must resolve `candidate_id`, obsolete `candidate_rr`, and all eight mathematical gaps before connection.

## 23. Replay behavior

D02 is invoked after each causal D01 Q_t emission. Context-only D04 reevaluation may reuse the most recent ReturnShape only under a defined causal expiry policy; that policy is currently a gap. No historical replay is authorized by this document.

## 24. Production/live equivalence

The identical D02 function and configuration must operate in replay and future live use. Only the causal source feeding D01 differs. D02 cannot branch on replay mode or inspect buffered future events.

## 25. Testing requirements

A future implementation requires, at minimum:

- schema completeness and type/range tests;
- exact 16-field D04 compatibility tests;
- unknown-field and prohibited-input rejection tests;
- first-Q_t initialization tests;
- identity/version monotonicity and restore tests;
- nonuniform FMO-coordinate tests;
- finite/boundary/property tests;
- deterministic repeat and process-isolation tests;
- causal prefix-invariance tests;
- observer/outcome/reserve leakage guards;
- replay/live source-equivalence tests using synthetic causal inputs only before any approved development replay.

## 26. Acceptance criteria

D02 can become implementation-ready only when:

1. all eight mathematical gaps have reviewed definitions;
2. all 14 mandatory D04 fields have an authorized producer or the D04 interface is separately revised;
3. types, units, bounds, semantics, initialization, and failures align;
4. no context field is placed in D02;
5. no diagnostic, observer, future, outcome, or reserve input enters D02;
6. D01 remains the sole inference authority;
7. the same deterministic function serves replay and live operation;
8. a machine-readable schema passes mechanical validation;
9. human review explicitly authorizes a freeze.

## 27. Prohibited behavior

Prohibited behavior includes independent prediction, adaptation, tuning, historical formula selection, reserve access, outcome-driven calibration, trading decisions, capturability duplication, silent default scores, hidden metadata inputs, and promotion of empirical status.

## 28. Open issues

The eight scientific gaps, candidate identity ownership, candidate reward/risk removal/relocation, protocol identity/version encoding, and context-only expiry invocation contract remain open. The system authority document also has a v0.2 filename with a v0.1 draft header; this metadata inconsistency should be resolved separately without altering its current governance role.

## 29. Implementation boundary

No D02 production package, runner, replay launcher, historical experiment, D04 adapter, or D03 integration may be created from this document. Implementation begins only after human clarification, reviewed updated design artifacts, a complete schema, and explicit authorization.

## 30. Freeze readiness decision

**D02 DESIGN NOT FREEZE-READY.**

Reason: eight required ReturnShape semantics are scientifically undefined, only 5/14 mandatory D04 fields are currently constructible within D02 responsibility, and two additional mandatory fields have ownership/interface conflicts. No freeze manifest is created.
