# D04 Preservation Classification v0.2

## 1. Classification summary

The 36 major elements below receive exactly one primary classification.

| Classification | Count |
|---|---:|
| PRESERVE_UNCHANGED | 10 |
| PRESERVE_WITH_INTERFACE_ADAPTER | 6 |
| SEMANTIC_RENAME_ONLY | 3 |
| MODERNIZATION_REQUIRED | 5 |
| OBSOLETE | 4 |
| RESPONSIBILITY_MOVED | 3 |
| NEW_INTEGRATION_REQUIRED | 2 |
| UNCERTAIN_REQUIRES_REVIEW | 3 |

## 2. Element classification

| Element | Classification | Reason |
|---|---|---|
| `CapturabilityModel` abstract plug-in boundary | PRESERVE_UNCHANGED | Correct D04-owned extension point |
| `ApertureModel` and `ApertureModelV0` | PRESERVE_UNCHANGED | Depend only on final capturability score |
| `HysteresisConfig` and `HysteresisController` | PRESERVE_UNCHANGED | Score-driven control, independent of shape schema |
| `EnvelopeState` four-state model | PRESERVE_UNCHANGED | Correct envelope-control ontology |
| `map_transition_event` | PRESERVE_UNCHANGED | Pure state transition mapping |
| minimum feasibility-gate algorithm | PRESERVE_UNCHANGED | Uses only causal D04 context and enforces bottleneck intent |
| gate dimension reason-code mapping | PRESERVE_UNCHANGED | Operational diagnostics remain valid |
| `EventBus` | PRESERVE_UNCHANGED | Input-schema independent publication mechanism |
| `MARKET_INELIGIBLE` safety principle | PRESERVE_UNCHANGED | Causal D04 operational safety |
| `DATA_INVALID` safety principle | PRESERVE_UNCHANGED | Causal D04 context safety |
| `TradingEnvelope.process` orchestration order | PRESERVE_WITH_INTERFACE_ADAPTER | Safety/capture/state/aperture/events order remains valid |
| `EnvelopeContext` operational fields | PRESERVE_WITH_INTERFACE_ADAPTER | Existing causal qualities remain useful; time/metadata need alignment |
| `RealtimeLoop` ordered processing | PRESERVE_WITH_INTERFACE_ADAPTER | Event-driven loop is valid; field access/output adapts |
| `AuditLogger` mechanism | PRESERVE_WITH_INTERFACE_ADAPTER | Audit sequence/records preserve; schema identity changes |
| `SyntheticGenerator` concept | PRESERVE_WITH_INTERFACE_ADAPTER | Deterministic fixture adapter survives with new ReturnShape |
| CLI assembly/scenario runner | PRESERVE_WITH_INTERFACE_ADAPTER | Component construction survives with modern config/models |
| `timestamp` -> `model_time` | SEMANTIC_RENAME_ONLY | Frozen identity naming |
| `persistence_score` -> `persistence` | SEMANTIC_RENAME_ONLY | Exact D01 semantic alignment |
| `reversal_risk` -> `reversal_propensity` | SEMANTIC_RENAME_ONLY | Avoid probability/risk overclaim |
| legacy `ReturnShape` Pydantic model | MODERNIZATION_REQUIRED | Must accept frozen 17-field D02 contract |
| shape-component weighted formula | MODERNIZATION_REQUIRED | Six retired/changed scalar inputs |
| lifetime component formula | MODERNIZATION_REQUIRED | Expected lifetime retired; projection extent is not attractiveness |
| `EnvelopeEvaluation` public output | MODERNIZATION_REQUIRED | Legacy IDs, shape quality, position fields, component semantics |
| stale-shape safety path | MODERNIZATION_REQUIRED | `active` retired; inclusive event-time rule approved |
| `candidate_rr` | OBSOLETE | Unused and prohibited upstream |
| `shape_quality` meta-score | OBSOLETE | Redundant compression without distinct ontology |
| untyped ReturnShape metadata | OBSOLETE | Unused hidden-input channel |
| untyped EnvelopeContext metadata | OBSOLETE | Unused hidden-input channel |
| `active` input ownership | RESPONSIBILITY_MOVED | D04 lifecycle derives validity |
| logical `position_open` ownership | RESPONSIBILITY_MOVED | Position lifecycle belongs to D03 |
| HOLD/REDUCE/EXIT commitment semantics | RESPONSIBILITY_MOVED | D03 decides; D04 may report envelope state only |
| frozen D02 ReturnShape ingestion/validation | NEW_INTEGRATION_REQUIRED | Existing source has no canonical D02 adapter/model |
| D04 candidate identity formation | NEW_INTEGRATION_REQUIRED | Human-approved D04 ownership needs explicit mechanism |
| magnitude-to-capturability transform | UNCERTAIN_REQUIRES_REVIEW | Natural geometry exists; bounded D04 math is unresolved |
| support-to-capturability transform | UNCERTAIN_REQUIRES_REVIEW | Natural ratio/path exists; bounded D04 math is unresolved |
| modern base shape aggregation | UNCERTAIN_REQUIRES_REVIEW | Contributions/normalization/aggregation require design |

## 3. Preservation conclusion

Twenty-two of 36 elements are directly preserved, adapter-preserved, or semantic renames. Only five require internal modernization, four are obsolete, three move to the correct owner, two integrations are new, and three mathematical choices remain for review. This is an interface-focused evolution, not a rewrite.
