# D02 Repository and Contract Inventory v0.1

## 1. Status and scope

**Status:** DESIGN RECONCILIATION; NOT FROZEN  
**System authority:** `APTF_INTEGRATED_SYSTEM_DESIGN_AUTHORITY_REPLAY_CORE_V0_2.md`  
**Inventory boundary:** repository source, configuration, tests, and design documents only. No historical replay, reserve access, future-outcome inspection, or outcome-decision-column inspection occurred.

The system authority was read in full before this inventory. Its filename is v0.2 and it governs this task. Its internal header still says `Version: 0.1 --- Design Draft`; this is a metadata inconsistency. The authority was not modified. No file named `APTF_HOLISTIC_SYSTEM_ARCHITECTURE_AND_STAGE3_DESIGN_V0_1.md` is present in the repository; if recovered later, it is superseded by the v0.2 authority under the task governance.

## 2. Status vocabulary

- **CONCEPT EXISTS:** a responsibility or term is described.
- **CONTRACT EXISTS:** an input/output structure is specified.
- **DESIGN EXISTS:** behavior and mathematics are sufficiently defined for implementation.
- **IMPLEMENTATION EXISTS:** executable source exists.
- **TESTS EXIST:** automated or deterministic scenario tests exist.
- **EXECUTED:** repository evidence records execution.
- **VALIDATED:** stated acceptance checks passed for the stated scope.
- **FROZEN:** a freeze authority or immutable hash chain exists.
- **SUPERSEDED:** a later authority explicitly controls conflicts.

These statuses are independent. In particular, implemented or executed does not imply scientifically validated or frozen.

## 3. Frozen D01 authority verification

The D01 authority chain passed byte-level SHA256 verification before D02 inspection:

| Authority | Repository status | Actual verification |
|---|---|---|
| `D01_V0_2_STAGE_1_SYNTHETIC_ACCEPTANCE_FREEZE.json` | FROZEN | SHA256 `57F800A510FC68A60928B5FCA36A2E58C3E9F7B6FD2A39E7EC3A709831573C94` PASS |
| `D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2_FREEZE.json` | FROZEN | SHA256 `094AF0595575F93B045AEEC6E993128CF3D6EBEC31565602D9394AB52694AABF` PASS |
| Scoring clarification v0.2.1 freeze | FROZEN | SHA256 `E273F07AC7237FF5F6D653B07A90AC32C11175A18FACA7888A8BFE1DCB2C709F` PASS |
| Scoring clarification v0.2.2 freeze | FROZEN | SHA256 `1D508B86C85D1156679DB3F0E5BE85ABFE89FF8F4F0B8C6C0E92877F88922139` PASS |
| `D01_STAGE_2_IMPLEMENTATION_V0_2_2_FREEZE.json` | FROZEN PRE-EXECUTION | SHA256 `281A50D5B3D615EE258EBA0C3A8691B9574C92CF0C59BBAE1DA7951D03CD69E7` PASS |
| Stage 2 closeout / Stage 3 boundary freeze | FROZEN | SHA256 `2CBDD76F97036E5546132DEE171ADFA2B0DD376F7DDF9E5D6E3C8E87F09208EE` PASS |
| Pre-Stage-3 architecture freeze | FROZEN | Known SHA256 `B6ED942E41EC1C72350CF9247597E5819A942DBE9D04770C23E243204165B235` PASS |

The canonical primary replay seal is consistently recorded as `6CF2BE31F8815ADB3B5B2E70916A4CD5CDAF427783DA9098E5167313EB70F981`. Hash checks also passed for 29/29 Stage 1 protected model/configuration/design artifacts, 14/14 Stage 2 protected implementation artifacts, and 6/6 pre-Stage-3 frozen companion artifacts. D01 was not modified.

## 4. D02 artifact inventory

No standalone pre-existing D02 design, source package, test suite, execution artifact, validation record, or freeze manifest was found. Filename search found no pre-existing artifact containing `D02` before this task.

| Path | Type and purpose | Concept | Contract | Design | Implementation | Tests | Executed | Validated | Frozen | Superseded | Current authority |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `APTF_INTEGRATED_SYSTEM_DESIGN_AUTHORITY_REPLAY_CORE_V0_2.md` | Integrated architecture; defines D02 responsibility and reconciliation | YES | PARTIAL | NO D02 math | NO | NO | N/A | N/A | NO manifest | NO | YES, system-level |
| `D01_QT_OUTPUT_CONTRACT_V0_1.md` | Canonical causal D01 input available to D02 | YES | YES | D01 only | D01 source | D01 tests | YES | D01 scope | YES via pre-Stage-3 freeze | NO | YES, D02 input |
| `D01_QT_OUTPUT_SCHEMA_V0_1.json` | Machine-readable 19-field Q_t contract | YES | YES | D01 only | Documentation | N/A | N/A | Hash verified | YES via pre-Stage-3 freeze | NO | YES, D02 input |
| `D01_ADAPTIVE_PARAMETRIC_MODEL_V0_2_IMPLEMENTATION_DESIGN.md` | D01-to-D02 separation and FMO mathematics | YES | PARTIAL | D01/FMO only | D01 implemented | YES | YES | D01 scope | Protected by Stage 1 | NO | YES where consistent with frozen Q_t |
| `D01_ADAPTIVE_PARAMETRIC_MODEL_DESIGN_V0_3.md` | Historical DMO-to-D02 topology and candidate fields | YES | HISTORICAL/PARTIAL | NO final D02 schema | NO D02 | NO D02 | NO D02 | NO D02 | NO D02 freeze | Limited by later frozen Q_t | Supporting only |
| `adaptive_parametric_trading_framework_reference1.1.md` | Historical holistic ReturnShape concept | YES | NO committed formula | NO | NO | NO | NO | NO | NO | SUPERSEDED for integration | Historical only |

### D02 status conclusion

| Status | Finding |
|---|---|
| CONCEPT EXISTS | YES |
| CONTRACT EXISTS | PARTIAL: frozen D01 input and implemented D04 target exist |
| DESIGN EXISTS | NO complete scientific construction |
| IMPLEMENTATION EXISTS | NO |
| TESTS EXIST | NO D02 tests |
| EXECUTED | NO |
| VALIDATED | NO |
| FROZEN | NO |
| SUPERSEDED | Historical concepts are constrained by frozen Q_t and system authority v0.2 |

## 5. Actual frozen D01 output trace

The source trace is:

```text
NormalizedObservation
  -> D01V02Model.step(...)
  -> DMOOutput + FMOOutput
  -> canonical Q_t
```

`Q_t` has exactly 19 top-level canonical fields:

- Identity: `model_time`, `entity_id`, `model_version`.
- Current state: `state_level`, `state_velocity`, `state_acceleration`, `state_curvature`, `strength`, `coherence`, `persistence`, `perturbation_magnitude`, `perturbation_class`, `uncertainty`, `reversal_propensity`, `state_support_ratio`, `observation_half_life`, `forward_half_life`.
- Forward state: `forward_interval`, `forward_samples`.

Each `FMOSample` has exactly seven coordinates: `tau`, `level`, `velocity`, `uncertainty`, `strength`, `persistence`, and `reversal_propensity`. The accepted default emits eight samples. D01 computes projected level, velocity decay, strength decay, persistence decay, uncertainty expansion, and reversal-propensity expansion before D02.

Nine DMO diagnostic/internal fields, twelve Stage 2 observer concepts, future observations, labels/decisions, and reserve data are explicitly outside Q_t.

## 6. D04 artifact inventory

| Path | Type and purpose | Contract | Implementation | Tests | Executed | Validated | Frozen | Current authority |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `d04_trading_envelope/D04_PHYSICAL_DESIGN_V0_1.md` | Physical prototype design | YES | Describes prototype | N/A | Repository records execution | Prototype scope | Claims frozen domain contracts, but no hash freeze manifest found | D04 design, subordinate to system authority |
| `d04_trading_envelope/src/aptf_d04/models/return_shape.py` | Concrete Pydantic `ReturnShape` | YES | YES | YES | YES | Structural ranges only | NO independent freeze manifest | Actual current input type |
| `.../models/envelope_context.py` | Operational/context input model | YES | YES | YES | YES | Structural ranges only | NO | Actual context type |
| `.../envelope/capturability_model.py` | Placeholder deterministic capturability V0/V0.2 | YES | YES | YES | YES | Synthetic prototype behavior | NO; explicitly experimental | Actual prototype consumer |
| `.../envelope/trading_envelope.py` | Process orchestration, safety, transitions, events | YES | YES | YES | YES | Synthetic prototype behavior | NO independent freeze manifest | Actual prototype orchestration |
| `.../envelope/aperture_model.py` | Smoothed aperture | YES | YES | YES | YES | Synthetic prototype behavior | NO | Actual prototype |
| `.../envelope/hysteresis.py` | Persistent asymmetric state transitions | YES | YES | YES | YES | Synthetic prototype behavior | NO | Actual prototype |
| `.../envelope/lifecycle.py` and `.../models/events.py` | Transition and continuation/event semantics | YES | YES | YES | YES | Synthetic prototype behavior | NO | Actual prototype |
| `d04_trading_envelope/scenarios/*.yaml` | Seven deterministic synthetic scenarios | Scenario contract | Fixture implementation | YES | YES | Scenario expectations | NO | Test evidence only |

D04 is an implemented and exercised physical prototype. Its design explicitly calls capturability scoring, thresholds, dimensions, and weights placeholder/experimental scaffolding. That status must not be promoted to validated production mathematics.

## 7. D04 ReturnShape contract

The concrete model has 16 fields, of which 14 are Pydantic-mandatory; `active` defaults to `true` and `metadata` defaults to `{}`.

| Field | Type / range | Meaning and actual D04 role |
|---|---|---|
| `return_shape_id` | string | Stable shape identity; version continuity, events, audit |
| `candidate_id` | string | Candidate identity; opportunity/event identity |
| `version` | integer >= 1 | Must increase for repeated shape ID |
| `timestamp` | float | Event/evaluation time |
| `direction` | `LONG|SHORT|NEUTRAL` | Stored; not used by current capturability math |
| `shape_quality` | float [0,1] | Weighted shape component, reason code, evaluation output |
| `forward_support` | float [0,1] | Weighted shape component and reason code |
| `uncertainty` | float [0,1] | Inverted weighted shape component and reason code |
| `expected_lifetime_seconds` | float; operationally > 0 | Safety expiration and normalized lifetime component |
| `candidate_rr` | float | No current D04 core consumer |
| `magnitude_score` | float [0,1] | Weighted shape component |
| `persistence_score` | float [0,1] | Weighted shape component |
| `decay_score` | float [0,1] | Inverted weighted shape component |
| `reversal_risk` | float [0,1] | Inverted weighted shape component and reason code |
| `active` | bool, default true | Safety expiration and entry eligibility |
| `metadata` | mapping, default empty | Core ignores it |

## 8. D04 context separation

`EnvelopeContext` is a separate model consumed alongside `ReturnShape`. Its fields are `timestamp`, `market_eligible`, `data_integrity`, `clock_event_quality`, `capital_available`, `portfolio_capacity`, `position_capacity`, `liquidity_quality`, `spread_quality`, `latency_quality`, `execution_feasibility`, `risk_capacity`, `broker_health`, and `metadata`.

These are execution, portfolio, infrastructure, or eligibility conditions. D02 must not manufacture them. The models use `extra="forbid"`, and `CapturabilityModelV0` extracts shape and envelope values through separate functions.

## 9. Inventory decision

D01 already owns adaptive market-state inference and causal FMO propagation. D04 owns capturability, aperture, hysteresis, safety, and envelope lifecycle. D02 has no existing independent implementation and must not duplicate either side. The remaining D02 responsibility is a deterministic ReturnShape construction boundary, but its mandatory scalar geometry and validity semantics are not fully defined. The detailed gaps are controlled by `D02_DESIGN_AMBIGUITIES_V0_1.md`.
