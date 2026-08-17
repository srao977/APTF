# D02/D04 Field Migration v0.2

## 1. Status

**Status:** HUMAN-APPROVED MIGRATION; FREEZE CANDIDATE; NOT IMPLEMENTED

This migration modernizes the D04 input boundary around frozen D01 Q_t/FMO. It does not modify D04 source or authorize capturability mathematics.

## 2. Disposition counts

| Old-field disposition | Count |
|---|---:|
| Unchanged | 1 |
| Renamed / semantically aligned | 7 |
| Removed | 4 |
| Moved to protocol, lifecycle, or downstream context | 4 |
| **Total old fields** | **16** |

The canonical D02 ReturnShape has 17 fields. Nine are natural D01/FMO-aligned additions not represented explicitly in the legacy model.

## 3. Exact migration table

| Old D04 field | Disposition | New canonical field(s) | Change classification | Reason | D04 core impact | Later implementation impact |
|---|---|---|---|---|---|---|
| `return_shape_id` | MOVED | Canonical identity `(entity_id, model_time)` | RESPONSIBILITY_MOVE | Synthetic shape identity is unnecessary; the canonical pair uniquely identifies the emitted shape | Version guard and event identity only | D04 aligns ordering/audit identity to the canonical pair |
| `candidate_id` | MOVED | None in D02; D04-owned candidate identity | RESPONSIBILITY_MOVE | D04 identifies the capturable candidate and passes it downstream to D03 | Opportunity-event identity only | D04 modernization defines candidate formation/identity; never derive it in D02 |
| `version` | REMOVED FROM D02 PROTOCOL | Monotonic `model_time` per `entity_id` | RESPONSIBILITY_MOVE | Human review found no separate sequence necessary | Current monotonic-version guard | D04 uses model-time ordering/supersession unless later concrete ambiguity is reviewed |
| `timestamp` | RENAMED | `model_time` | RENAME_ONLY | Align with frozen Q_t identity semantics | Events, audit, ordering | Mechanical rename |
| `direction` | SEMANTICALLY ALIGNED | `path_direction` | SEMANTIC_ALIGNMENT | Describes D01 projected-path orientation, not a market/trade prediction | Not used by current capturability core | Enum becomes `UPWARD|DOWNWARD|FLAT`; update serialization only |
| `shape_quality` | REMOVED | No one-to-one replacement; `coherence` and full FMO geometry are explicit | FIELD_REMOVAL + D04_CORE_MATHEMATICS_CHANGE | Legacy meta-score duplicates dimensions and has no independent ontology | Weighted shape component, reason code, evaluation echo | Remove weight/reason code or replace with explicitly reviewed D04 use of natural inputs |
| `forward_support` | SEMANTICALLY ALIGNED | `state_support_ratio` plus projected support coordinates in `forward_samples` | SEMANTIC_ALIGNMENT + TYPE_ALIGNMENT + D04_CORE_MATHEMATICS_CHANGE | D01 already defines support; legacy bounded score renamed and compressed it | Weighted shape component and reason code | D04 must decide direct ratio treatment or a documented bounded representation; no D02 meta-score |
| `uncertainty` | UNCHANGED | `uncertainty` | NONE | Exact frozen D01 coordinate and range | Weighted inverse and reason code | Field name/type remain compatible |
| `expected_lifetime_seconds` | SEMANTICALLY ALIGNED | `projection_interval` | SEMANTIC_ALIGNMENT + D04_CORE_MATHEMATICS_CHANGE | D01 defines projection extent, not statistical expected lifetime | Lifetime multiplier and expiry check | Rename lifetime component semantics; move staleness/expiry to D04 lifecycle policy |
| `candidate_rr` | REMOVED | None | FIELD_REMOVAL | Trade reward/risk has no Q_t source and no current D04 core consumer | None | Remove; any future reward/risk belongs to downstream decision/control design |
| `magnitude_score` | REMOVED | `terminal_displacement`, `maximum_absolute_displacement`, full `forward_samples` | FIELD_REMOVAL + FIELD_ADDITION + D04_CORE_MATHEMATICS_CHANGE | Preserve projected geometry rather than invent a normalized attractiveness score | Weighted shape component | D04 must explicitly select any scalarization needed for capturability |
| `persistence_score` | RENAMED | `persistence` | RENAME_ONLY | Exact frozen D01 name and bounded semantics | Weighted shape component | Mechanical rename; evidence lineage stays unsupported |
| `decay_score` | SEMANTICALLY ALIGNED | `forward_half_life`, `terminal_decay_factor`, projected sample paths | SEMANTIC_ALIGNMENT + FIELD_ADDITION + D04_CORE_MATHEMATICS_CHANGE | D01 already defines decay; legacy degradation score obscures remaining influence | Inverted weighted shape component | Consume remaining-influence semantics directly rather than double inversion |
| `reversal_risk` | SEMANTICALLY ALIGNED | `reversal_propensity` | SEMANTIC_ALIGNMENT | D01 emits propensity, not probability/risk | Weighted inverse and reason code | Rename and preserve non-probabilistic claim boundary |
| `active` | MOVED | None in D02; D04 lifecycle uses `model_time` and `projection_interval` | RESPONSIBILITY_MOVE | Active/expired is lifecycle state, not market inference | Safety override and entry eligibility | Newer same-entity shape supersedes; endpoint is inclusive; stale only after `model_time + projection_interval` |
| `metadata` | REMOVED | Explicit typed fields only | FIELD_REMOVAL | Untyped metadata can hide unauthorized inputs and is unused by core | None | Remove from canonical contract |

## 4. New D01/FMO-aligned fields

The following nine canonical fields have no direct legacy field counterpart:

1. `entity_id`;
2. `source_model_version`;
3. `current_level`;
4. `forward_half_life`;
5. `forward_samples`;
6. `terminal_displacement`;
7. `maximum_absolute_displacement`;
8. `strength`;
9. `coherence`.

`terminal_decay_factor` is counted as the semantic replacement for legacy `decay_score`; `state_support_ratio` replaces `forward_support`; the remaining aligned fields are identified in the migration table.

## 5. Core preservation boundary

Preserved D04 responsibilities:

- combine ReturnShape representation with `EnvelopeContext`;
- compute capturability and feasibility gating;
- update aperture;
- apply hysteresis and maintain envelope state;
- apply safety/lifecycle policy;
- emit transitions and events.

Controlled later revision is required only where placeholder D04 shape scoring consumes removed or semantically corrected fields. Aperture, hysteresis, feasibility-gate dimensions, envelope states, and event architecture do not need to move into D02.
