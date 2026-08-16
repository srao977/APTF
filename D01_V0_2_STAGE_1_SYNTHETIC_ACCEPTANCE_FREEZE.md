# D01 v0.2 Stage 1 Synthetic Acceptance Freeze

## Freeze Identity

- **Freeze ID:** `D01_V0_2_STAGE1_ACCEPTED_20260815T161928Z`
- **Freeze timestamp UTC:** `2026-08-15T16:19:28.0670468Z`
- **D01 version:** v0.2
- **Stage:** Stage 1 - Synthetic Semantic Validity
- **Status:** **ACCEPTED / FROZEN**
- **JSON freeze manifest:** `D01_V0_2_STAGE_1_SYNTHETIC_ACCEPTANCE_FREEZE.json`
- **JSON manifest SHA256:** `57F800A510FC68A60928B5FCA36A2E58C3E9F7B6FD2A39E7EC3A709831573C94`
- **JSON manifest size:** 9,763 bytes

## Final Stage 1 Result

| Gate | Result |
|---|---:|
| Required semantic assertions | 81 / 81 PASS |
| Cross-scenario assertions | 9 / 9 PASS |
| Ablation assertions | 43 / 43 PASS |
| Numerical health | PASS |
| Determinism | PASS |
| Source hash guard | PASS |
| Full matrix | 27 / 27 tasks completed |
| Worker failures | 0 |
| Final decision | READY FOR HISTORICAL STATE-VALIDITY DESIGN |

Carried diagnostic warning:

```text
FORWARD_INTERVAL_RANGE_WARNING
```

This warning does not authorize a model change. Stage 2 will monitor whether the emitted forward interval has empirical historical discrimination and validity.

## Frozen Model Authority

The JSON freeze manifest records SHA256, size, and role for:

- every file in `d01_adaptive_parametric_model/src/d01/v02/`;
- executable defaults and bounds in `config.py`;
- the resolved accepted `v02_default_config.json`;
- DMO/FMO implementation and resolved output schema;
- package/build authority.

The manifest is the machine-readable authority. D01 v0.2 is not to be modified in place.

## Frozen Design Authority

| Document | SHA256 |
|---|---|
| `D01_ADAPTIVE_PARAMETRIC_MODEL_V0_2_IMPLEMENTATION_DESIGN.md` | `8D081E85A6FC86F93AC2B515CE9E93DB2F23A4D06C1A81A2F750BE3E843165A2` |
| `D01_ADAPTIVE_PARAMETRIC_MODEL_DESIGN_V0_3_ADDENDUM_PERTURBATION_SEMANTICS.md` | `AF00CB7B22C7B29CC28B3EC9C9CFFC10AF01D7DB564525594490CA248B780BCB` |

The required perturbation-semantics hash was verified before freeze creation.

## Frozen Acceptance Evidence

The JSON freeze manifest links the accepted source and configuration to the final evidence under `output/d01_v02_semantic_acceptance/`, including:

- final acceptance manifest;
- 81 required semantic assertions;
- 9 cross-scenario assertions;
- 43 ablation assertions;
- numerical-health evidence;
- determinism evidence;
- 27-task worker/PID evidence;
- final acceptance review;
- final user-owned run log.

## Stage 2 Integrity Contract

> D01 v0.2 SHALL NOT BE RETRAINED, RETUNED, RECALIBRATED, OR MODIFIED BEFORE OR DURING THE PRIMARY STAGE 2 EVALUATION.

Every future Stage 2 runner must load the JSON freeze manifest and verify all frozen source, configuration, schema, and design hashes before reading historical observations into D01.

Any mismatch must abort before replay with:

```text
STAGE_1_BASELINE_INTEGRITY_FAILURE
```

Frozen online adaptation already present in D01 v0.2 remains model execution. It is not authorization for fitting or calibration against Stage 2 outcomes.

## Immutability and Versioning

Stage 2 is allowed to find unsupported semantics. Such evidence must not alter this baseline. Any future model change becomes a new candidate version, returns through Stage 1 synthetic semantic validity, and receives a new freeze identity before historical evaluation.

## Execution Boundary

- Stage 2 implemented: **NO**
- Historical D01 replay started: **NO**
- Reserve unsealed: **NO**
- Historical data used for model fitting: **NO**
- Trading/backtest/P&L performed: **NO**