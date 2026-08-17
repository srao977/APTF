# D04 to Frozen D02 Interface Mapping v0.2

## 1. Old-to-new map

| Old D04 input | Frozen D02 input | Existing consumer | Modernization action |
|---|---|---|---|
| `return_shape_id` | identity `(entity_id, model_time)` | Version/audit/events | Remove synthetic ID/version; D04 tracks latest model time per entity |
| `candidate_id` | None | Opportunity/events | D04 creates candidate identity after qualification |
| `version` | `model_time` ordering | Monotonic guard | Validate strictly newer model time per entity for new-shape events |
| `timestamp` | `model_time` | Events/audit | Rename; context reevaluation has separate evaluation time |
| `direction` | `path_direction` | No operational consumer | Semantic rename; retain as geometry metadata |
| `shape_quality` | None; `coherence` and FMO remain separate | Shape sum/reason/output | Remove term and echo; do not create replacement meta-score |
| `forward_support` | `state_support_ratio`, projected sample coordinates | Shape sum/reason | Define D04-specific use only after human decision |
| `uncertainty` | `uncertainty`, projected uncertainty path | Inverse term/reason | Preserve current inverse penalty as candidate D04 semantics |
| `expected_lifetime_seconds` | `projection_interval` | Lifetime/safety | Use interval only for validity boundary; temporal capture factor unresolved |
| `candidate_rr` | None | None | Remove |
| `magnitude_score` | terminal/max displacement and full path | Shape sum | Define D04 geometric capturability transform; no D02 normalization |
| `persistence_score` | `persistence`, projected path | Shape sum | Rename; current direct bounded contribution may be preserved subject to final aggregation |
| `decay_score` | `terminal_decay_factor`, half-life, full path | Inverse term | Correct to remaining-influence semantics; do not preserve old inversion blindly |
| `reversal_risk` | `reversal_propensity`, projected path | Inverse term/reason | Rename; inverse propensity remains a transparent D04 penalty candidate |
| `active` | D04 rule over `model_time`, `projection_interval`, entity supersession | Safety/eligibility | Derive in D04; endpoint inclusive |
| `metadata` | None | Serialization only | Remove |

## 2. Canonical 17-field coverage

| Frozen D02 field | Existing equivalent/consumer | Modernized D04 relevance |
|---|---|---|
| `model_time` | Legacy timestamp/version ordering | Identity, events, staleness |
| `entity_id` | Part of synthetic shape ID only | Entity key, latest-shape state |
| `source_model_version` | None | Audit/provenance only |
| `current_level` | None | Geometry reference; full path validation |
| `projection_interval` | Mislabeled lifetime | Staleness boundary; possible temporal component pending design |
| `forward_half_life` | None | Decay provenance/path interpretation |
| `forward_samples` | None | Rich path available; no immediate scalar collapse |
| `terminal_displacement` | Hidden behind magnitude score | Magnitude design input |
| `maximum_absolute_displacement` | Hidden behind magnitude score | Excursion design input |
| `path_direction` | Legacy direction, unused | Geometry/event metadata |
| `terminal_decay_factor` | Inverted degradation proxy | Remaining influence input |
| `strength` | Indirectly buried in quality/support | Explicit capturability dimension candidate |
| `coherence` | Indirectly buried in quality | Explicit regularity dimension candidate |
| `persistence` | Legacy persistence score | Direct bounded input candidate |
| `uncertainty` | Exact equivalent | Existing inverse penalty candidate |
| `reversal_propensity` | Legacy risk name | Existing inverse penalty candidate |
| `state_support_ratio` | Legacy bounded support proxy | Natural unbounded input; transform unresolved |

## 3. Full-FMO policy

D04 receives and validates the entire ordered path. Scalar contributions may be added only when mathematically justified by D04 capturability semantics. D04 must not mutate FMO geometry or treat it as realized future data.
