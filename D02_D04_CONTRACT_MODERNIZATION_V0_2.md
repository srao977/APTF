# D02/D04 Contract Modernization v0.2

## 1. Status and purpose

**Status:** HUMAN-APPROVED DESIGN; FREEZE CANDIDATE; NOT IMPLEMENTED

This document reconciles the completed frozen D01 Q_t/FMO architecture with the earlier D04 physical prototype. The objective is the correct D02 scientific representation and the smallest controlled D04 input-boundary revision, not backward coverage of all legacy fields.

## 2. Why modernization is required

The D04 `ReturnShape` prototype predates frozen D01 v0.2. It accepted synthetic normalized meta-scores and candidate/lifecycle fields because no canonical FMO boundary existed. D01 now emits a complete causal projected path, current state coordinates, an elastic projection interval, and a forward half-life.

Therefore the implemented D04 model is evidence about prototype behavior, not authority requiring D02 to manufacture every legacy name. The v0.1 D02 reconciliation correctly stopped instead of inventing formulas, but it overclassified representation, naming, lifecycle, and protocol questions as eight scientific gaps.

## 3. Governing frozen authority

The following were reverified before modernization:

- all seven governing freeze-file SHA256 values: PASS;
- pre-Stage-3 freeze SHA256: `B6ED942E41EC1C72350CF9247597E5819A942DBE9D04770C23E243204165B235`;
- 29/29 protected Stage 1 model/configuration/design artifacts: PASS;
- 14/14 Stage 2 protected implementation artifacts: PASS;
- 6/6 pre-Stage-3 companion artifacts: PASS.

D01 remains unchanged and the sole market-state inference authority.

## 4. D04 prototype status

D04 provides valuable implemented behavior:

- capturability separation from market inference;
- feasibility gating from operational context;
- aperture smoothing;
- hysteresis and envelope state;
- safety/lifecycle checks;
- transition, opportunity, and continuation events.

Its physical design calls the shape scoring, weights, thresholds, and dimensions placeholder/experimental scaffolding. The current `_shape_values()` function consumes seven scalar values, but that does not make those values canonical D02 science.

## 5. Old versus proposed boundary

### Legacy boundary

```text
Synthetic/prototype ReturnShape
  = identity + candidate context + scalar shape opinions + lifecycle flag
  -> D04 placeholder weighted shape component
```

### Modernized boundary

```text
Frozen Q_t / FMO
  -> D02 loss-minimizing deterministic representation
     = identity + complete forward samples + natural D01 coordinates
       + four reversible geometry views
  -> D04 capturability under separate EnvelopeContext
```

The proposed canonical D02 contract has 17 fields and is defined in `D02_RETURNSHAPE_CANONICAL_SCHEMA_V0_2.json`.

## 6. Canonical representation summary

Identity/provenance:

- `model_time`, `entity_id`, `source_model_version`.

Forward path and temporal geometry:

- `current_level`, `projection_interval`, `forward_half_life`, `forward_samples`.

Deterministic geometry views:

- `terminal_displacement`, `maximum_absolute_displacement`, `path_direction`, `terminal_decay_factor`.

D01-aligned shape-state coordinates:

- `strength`, `coherence`, `persistence`, `uncertainty`, `reversal_propensity`, `state_support_ratio`.

The full samples remain authoritative; derived views do not replace or compress them.

## 7. Legacy field disposition

| Disposition | Count | Fields |
|---|---:|---|
| Unchanged | 1 | `uncertainty` |
| Renamed / semantically aligned | 7 | `timestamp`, `direction`, `forward_support`, `expected_lifetime_seconds`, `persistence_score`, `decay_score`, `reversal_risk` |
| Removed | 4 | `shape_quality`, `candidate_rr`, `magnitude_score`, `metadata` |
| Moved to protocol/lifecycle/downstream context | 4 | `return_shape_id`, `candidate_id`, `version`, `active` |

The exact migration and implementation impact are in `D02_D04_FIELD_MIGRATION_V0_2.md`.

## 8. Responsibility changes

- D02 owns deterministic representation of Q_t/FMO only.
- D04 owns shape capturability, scalarization needed for capturability, operational feasibility, aperture, hysteresis, lifecycle, and events.
- D04 owns candidate formation and candidate identity; it passes candidate/envelope information downstream to D03.
- D03 owns decisions and any future reward/risk decision construct.
- Canonical ReturnShape identity is `(entity_id, model_time)`; D02 emits no separate shape ID/version/sequence.

## 9. D04 core impact

| D04 subsystem | Impact | Classification |
|---|---|---|
| Feasibility gate and `EnvelopeContext` | No conceptual change | NONE |
| Aperture update | No conceptual change | NONE |
| Hysteresis/state transitions | No conceptual change | NONE |
| Event architecture | Identity payload alignment only | TYPE/PROTOCOL ALIGNMENT |
| Shape component weighted sum | Inputs must be redesigned around natural fields | D04_CORE_MATHEMATICS_CHANGE |
| Lifetime component | Rename/reinterpret as projection interval or revise | SEMANTIC_ALIGNMENT |
| Expiry/active safety | Move to D04 causal lifecycle policy | RESPONSIBILITY_MOVE |
| Shape ID/version guard | Move to explicit interface protocol | RESPONSIBILITY_MOVE |

The current placeholder weights must not be silently relabeled. Any modernized D04 shape-component formula requires its own design review before implementation.

## 10. Information-loss policy

D02 preserves the complete FMO path. It does not emit generic `shape_quality`, `magnitude_score`, or `decay_score` values. D04 can inspect explicit coordinates or approved geometry views. This keeps alternative legitimate path interpretations available without adding market inference.

## 11. Evidence lineage

Stage 2 labels remain attached to every direct or derived coordinate. They constrain claims, not mathematical availability. No unsupported/inconclusive coordinate is removed, zeroed, weighted down, or recalibrated because of its label.

## 12. Whole-system validation

The eventual sealed backtest validates:

```text
causal observations -> D01 -> D02 -> D04 -> D03
  -> committed decisions -> later realized outcomes
```

It does not select D02 formulas. The first six months are consumed development evidence; the second six months remain sealed. This task used neither.

## 13. Modernization decision

The canonical D02 data structure and six boundary decisions are human-approved. The D02 design may be frozen after final mechanical and consistency validation. No implementation is authorized. D04 source modernization follows only through a separate D04 capturability/lifecycle design task.
