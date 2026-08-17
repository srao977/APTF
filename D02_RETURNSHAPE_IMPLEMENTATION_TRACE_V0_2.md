# D02 ReturnShape Implementation Trace v0.2

## 1. Frozen authority

- System authority: `APTF_INTEGRATED_SYSTEM_DESIGN_AUTHORITY_REPLAY_CORE_V0_2.md`.
- Frozen D01 Q_t authority: `D01_PRE_STAGE_3_ARCHITECTURE_FREEZE_V0_1.json`, SHA256 `B6ED942E41EC1C72350CF9247597E5819A942DBE9D04770C23E243204165B235`.
- Frozen D02 design: `D02_RETURNSHAPE_DESIGN_V0_2_FREEZE.json`, SHA256 `6FC2D51FDA74284B7866B67DE2B6EA7025F9F3599606E2A9945FCF53D07A7CE6`.
- Frozen downstream D04 design: `D04_TRADING_ENVELOPE_MODERNIZATION_V0_2_FREEZE.json`, SHA256 `B5C489D060629A91DDED5B2C6EAA4076F6273AF05AED3480659CE649A1050E51`.

All authority and referenced-artifact hashes passed before implementation.

## 2. Implementation paths

- Package root: `d02_return_shape`.
- Models: `d02_return_shape/src/d02/v02/models.py`.
- Transformation: `d02_return_shape/src/d02/v02/builder.py`.
- Public exports: `d02_return_shape/src/d02/__init__.py` and `src/d02/v02/__init__.py`.
- Tests: `d02_return_shape/tests`.

No D01, D04, or D03 source file is part of the implementation.

## 3. Public entry point

```python
build_return_shape(dmo: DMOOutput, fmo: FMOOutput) -> ReturnShape
```

The function is pure and has no mutable/global state, clock, randomness, environment branch, cache, I/O, or D04 dependency.

## 4. D01 input types

The boundary imports actual frozen types from `d01.v02.outputs`: `DMOOutput`, `FMOOutput`, and their nested `FMOSample` values. No undocumented pseudo-Q adapter is used. Input validation requires matching model time/entity identity, D01 model version `0.2`, finite/ranged canonical coordinates, nonempty strictly increasing samples, and terminal tau equal to the FMO interval.

## 5. D02 output type

`ReturnShape` and nested `ForwardSample` are frozen dataclasses. `PathDirection` is the exact `UPWARD | DOWNWARD | FLAT` string enum. `ReturnShape.to_dict()` provides stable structured serialization with all 17 fields, a list of seven-field samples, and enum value serialization.

## 6. Top-level lineage — 17/17

| D02 field | D01 source | Object | Transformation | Mode | Type / units | Deterministic |
|---|---|---|---|---|---|---:|
| `model_time` | `model_time` | DMO/FMO | Match then copy DMO | COPIED | float UTC seconds | YES |
| `entity_id` | `entity_id` | DMO/FMO | Match then copy DMO | COPIED | string ID | YES |
| `source_model_version` | `model_version` | DMO | Copy | COPIED | string version | YES |
| `current_level` | `state_level` | DMO | Copy | COPIED | normalized displacement | YES |
| `projection_interval` | `interval_length` | FMO | Copy | COPIED | seconds `[10,600]` | YES |
| `forward_half_life` | `forward_half_life` | DMO | Copy | COPIED | seconds `[15,900]` | YES |
| `forward_samples` | `samples` | FMO | Ordered immutable field-for-field copy | COPIED | tuple of ForwardSample | YES |
| `terminal_displacement` | terminal sample `level`, `state_level` | FMO/DMO | terminal level minus current level | DERIVED | normalized displacement | YES |
| `maximum_absolute_displacement` | all sample `level`, `state_level` | FMO/DMO | maximum absolute level difference | DERIVED | nonnegative normalized displacement | YES |
| `path_direction` | `terminal_displacement` | D02 derived | exact sign; zero is FLAT | DERIVED | enum | YES |
| `terminal_decay_factor` | interval, forward half-life | FMO/DMO | $2^{-I/H}$ | DERIVED | dimensionless `(0,1)` | YES |
| `strength` | `strength` | DMO | Copy | COPIED | `[0,1]` | YES |
| `coherence` | `coherence` | DMO | Copy | COPIED | `[0,1]` | YES |
| `persistence` | `persistence` | DMO | Copy | COPIED | `[0,1]` | YES |
| `uncertainty` | `uncertainty` | DMO | Copy | COPIED | `[0,1]` | YES |
| `reversal_propensity` | `reversal_propensity` | DMO | Copy | COPIED | `[0,1]` | YES |
| `state_support_ratio` | `state_support_ratio` | DMO | Copy | COPIED | finite ratio `>=0` | YES |

Traced: **17**. Untraced: **0**.

## 7. Nested FMO lineage — 7/7

Each source `FMOSample` is copied in original order into immutable `ForwardSample`: `tau`, `level`, `velocity`, `uncertainty`, `strength`, `persistence`, and `reversal_propensity`. No interpolation, reconstruction, sorting, resampling, or rounding occurs.

## 8. Geometry implementation

The final source sample is authoritative because validation requires strictly increasing tau and terminal tau equal to `projection_interval`. Geometry exactly implements the frozen formulas. No epsilon or threshold affects direction. Natural displacement is not normalized or clamped.

## 9. Validation behavior

Invalid authoritative input raises deterministic `TypeError` or `ValueError`; it is never repaired, imputed, reordered, clipped, or defaulted. Both input objects and immutable output models enforce finite/range/path invariants.

## 10. Serialization

`to_dict()` follows D01's dataclass/asdict convention, normalizes tuple samples to a JSON-compatible list, and emits the string enum value. It introduces no canonical wire protocol or timestamp.

## 11. Deterministic behavior

Ten repeated same-process calls matched exactly. Two fresh Python processes produced byte-identical canonical JSON for the same synthetic actual D01 replay. No random/clock/global/environment dependency exists in runtime source.

## 12. Prohibited fields

Runtime source contains none of the frozen legacy scores, candidate/execution fields, D03 decisions, learned/fitted parameters, or adaptive state. A static source scan found zero prohibited runtime matches.

## 13. D04 compatibility

The implementation field set exactly equals the frozen 17-field D02 schema referenced by `D04_MODERNIZED_INTERFACE_SCHEMA_V0_2.json`. Missing fields: 0. Extra adapter requirements: 0. D04 was not imported or modified.

## 14. Tests

D02: 26/26 passed. D01 v0.2-focused regression: 50/50 passed. Existing D04 regression: 23/23 passed. Frozen D02 contains no separate deterministic vector artifact, so frozen-vector count is 0/0; all frozen formulas and invariants are executable tests.

## 15. No-data attestation

No historical dataset, development period, Stage 2 observer, reserve value, outcome label, benchmark decision, or P&L was read or used. Governance metadata confirms reserve sealed/uninspected.
