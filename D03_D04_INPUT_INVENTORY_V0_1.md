# D03 D04 Input Inventory v0.1

## Status and authority

**Status:** DESIGN INVENTORY; NOT A FREEZE; NO IMPLEMENTATION AUTHORIZED.

The live `aptf_d04.models.envelope_state.EnvelopeEvaluation` retains exactly 23 top-level fields. Under the v0.2.1 amendment, `CandidateEnvelope` has exactly six nested fields. The current executable authority is `D04_TRADING_ENVELOPE_IMPLEMENTATION_V0_2_1_FREEZE.json`, SHA256 `F72A86B3085BD11D8626F06F1FE3FAEDDE60570365488176011239382A46F1AF`; v0.2 remains historical authority.

All fields are causal at D04 evaluation time, D04-owned factual output, required at the top level, and consumed by D03 as one immutable `D04Evaluation`; `candidate_envelope` is required as a field but nullable.

## Exact top-level inventory

| # | Field | Type/range | Meaning | Classification | Decision-active? |
|---:|---|---|---|---|---|
| 1 | `evaluation_time` | finite float seconds | Causal D04 evaluation time | identity, factual | Yes: timing/commitment |
| 2 | `entity_id` | non-empty string | Evaluated entity | identity, factual | Yes: join/identity |
| 3 | `return_shape_model_time` | finite float seconds | Source D02 model time | identity/provenance | Yes: candidate lineage |
| 4 | `source_model_version` | string | Source D01/D02 model version | provenance | Audit only |
| 5 | `hard_eligibility` | integer `0|1` | D04 hard capturability eligibility | capturability fact | Validation only; never rescored |
| 6 | `geometry_quality` | float `[0,1]` | Endpoint efficiency | capturability diagnostic | No |
| 7 | `structural_quality` | float `[0,1]` | Structural geometric mean | capturability diagnostic | No |
| 8 | `risk_quality` | float `[0,1]` | Uncertainty/reversal quality | capturability diagnostic | No |
| 9 | `base_capturability_score` | float `[0,1]` | D04 base capturability | capturability diagnostic | No |
| 10 | `feasibility_gate_score` | float `[0,1]` | Minimum D04 feasibility gate | capturability diagnostic | No |
| 11 | `capturability_score` | float `[0,1]` | Final factual D04 capturability | capturability fact | Audit only; D03 must not threshold it |
| 12 | `previous_envelope_state` | enum `CLOSED|OPENING|OPEN|CLOSING` | State before this evaluation | lifecycle fact | Transition audit only |
| 13 | `new_envelope_state` | same enum | Current post-evaluation state | lifecycle fact | Yes: authorization rule |
| 14 | `aperture_before` | float `[0,1]` | Aperture before update | lifecycle diagnostic | No |
| 15 | `aperture_after` | float `[0,1]` | Current aperture | lifecycle fact | Audit only; D03 must not rescore it |
| 16 | `projection_valid` | bool | Inclusive projection validity | lifecycle/safety fact | Yes: consistency guard |
| 17 | `stale` | bool | Projection is strictly stale | lifecycle/safety fact | Yes: flat-target reason |
| 18 | `safety_state` | enum `CLEAR|SAFETY_CLOSED` | D04 safety condition | lifecycle/safety fact | Yes: flat-target rule |
| 19 | `safety_reason` | nullable enum | `SHAPE_STALE|MARKET_INELIGIBLE|DATA_INVALID|INVALID_RETURNSHAPE|NO_VALID_RETURNSHAPE` | lifecycle/safety fact | Yes: reason lineage |
| 20 | `candidate_envelope` | `CandidateEnvelope|null` | Current qualified or invalidated D04 candidate | candidate fact | Yes: directional authorization and lineage |
| 21 | `gate_dimension_values` | object of ten `[0,1]` floats | D04 gate diagnostics | diagnostic | No; must not duplicate D04 policy |
| 22 | `reason_codes` | array of strings | D04 factual explanations | diagnostic | Audit/supporting reasons only |
| 23 | `events` | array of factual `EventType` | Ordered D04 events | lifecycle/candidate diagnostic | Audit and supersession explanation only |

## Exact nested candidate inventory

| # | Field | Type/range | Meaning | D03 use |
|---:|---|---|---|
| 1 | `candidate_id` | string | D04 deterministic candidate identity | Preserve unchanged in decisions |
| 2 | `entity_id` | string | Candidate entity | Must equal top-level entity |
| 3 | `source_return_shape_model_time` | finite float seconds | Candidate's source D02 identity component | Preserve unchanged |
| 4 | `qualified_at` | finite float seconds | Causal qualification time | Audit/commitment ordering |
| 5 | `status` | `QUALIFIED|INVALIDATED` | Current candidate disposition | Only `QUALIFIED` can authorize directional target |
| 6 | `path_direction` | `PathDirection`: `UPWARD|DOWNWARD|FLAT` | Verbatim immutable source D02 orientation | UPWARD -> LONG; DOWNWARD -> SHORT; FLAT -> FLAT |

## Factual and diagnostic separation

D03 consumes the complete immutable object for auditability but its first-pass control rule uses only identity/time, current envelope state, projection/safety facts, and candidate identity/status. Capturability components, aperture magnitude, gates, reason codes, and events cannot be recombined into a D03 score or used to bypass candidate qualification.

## Directional authority

D03 consumes only `candidate_envelope.path_direction`. D04 copies it verbatim from the candidate's source `ReturnShape.path_direction`; D03 neither queries D02 nor infers orientation from unsigned scores, prices, D01 velocity, or raw FMO. Directional authority is resolved.
