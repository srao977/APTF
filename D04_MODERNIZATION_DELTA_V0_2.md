# D04 Modernization Delta v0.2

## What does not change

- D04 remains capturability/envelope authority.
- D01/D02 remain sole market inference/representation authorities.
- Capturability plug-in boundary, minimum feasibility gate, aperture smoothing, hysteresis state machine, envelope states, event bus, ordered event processing, scenario-loader concept, audit mechanism, and market/data safety principles remain.

## Exact module delta

| Existing path/module | Existing responsibility | Classification | Required change | Reason/upstream dependency | Downstream/test impact |
|---|---|---|---|---|---|
| `models/return_shape.py` | Legacy input | REQUIRED | Replace with/consume frozen 17-field contract exactly | Frozen D02 | Replace interface tests/fixtures |
| `models/envelope_context.py` | Context | REQUIRED | Rename `timestamp` to `evaluation_time`; remove metadata; retain 12 bounded/bool fields | Final I1 | Adapt fixtures |
| `models/capturability.py` | Score result | REQUIRED | Emit Q_G/Q_S/Q_R/B/G/C, eligibility, gate values, reasons | Approved formula | Audit/tests adapt |
| `models/aperture.py` | Aperture result | PRESERVE_UNCHANGED | None | Score remains bounded | Existing test unchanged |
| `models/envelope_state.py` | Evaluation output | REQUIRED | Implement final 23-field factual D04Evaluation | Final I2 | Output/audit tests adapt |
| `models/events.py` | Generic events | REQUIRED | Entity/model-time/candidate payload alignment | Final event contract | Event tests needed |
| `models/opportunity.py` | Qualified opportunity | REQUIRED | Evolve existing type into five-field CandidateEnvelope | D04 candidate ownership | Candidate tests |
| `models/enums.py` | Enums | REQUIRED | Preserve envelope states; add factual events/safety/candidate status; remove canonical decision commitments | D02/D03 boundary | Enum fixture changes |
| `envelope/capturability_model.py` | Capture math | REQUIRED | Add deterministic successor behind existing plug-in; preserve V0 historical class and gate | Approved formula | Formula/vector tests |
| `envelope/aperture_model.py` | Aperture | PRESERVE_UNCHANGED | None | Score-agnostic | Test unchanged |
| `envelope/hysteresis.py` | State control | PRESERVE_UNCHANGED | No formula change; reassess configured numbers analytically | New score scale | Four tests unchanged plus integration |
| `envelope/lifecycle.py` | Transition/continuation mapping | REQUIRED | Preserve state transitions; remove position-decision mapping; add stale/supersession factual mapping | Final L1/D03 ownership | Lifecycle tests adapt |
| `envelope/trading_envelope.py` | Orchestration | REQUIRED | Entity/model-time state, context-only reevaluation, safety staleness, candidate/output; preserve validated order | Final boundaries | Scenario/state tests adapt |
| `configuration.py` | Typed config | REQUIRED | Retire shape weights/target lifetime; retain gate/safety/aperture/hysteresis settings | Approved formula | Config tests needed |
| `config/default.yaml` | Values | REQUIRED | Remove old shape weights/target lifetime; no new formula weights | Approved formula | Numeric scenario expectations change |
| `runtime/event_bus.py` | Pub/sub | PRESERVE_UNCHANGED | None | Event mechanism independent | Preserve |
| `runtime/audit_log.py` | Audit | REQUIRED | Serialize final input/output/candidate/events; wall clock diagnostic only | Boundary changes | Audit test adapts |
| `runtime/realtime_loop.py` | Ordered loop | REQUIRED | Support ReturnShape and context-only events; keep speed outside science | Event-driven design | Scenario tests adapt |
| `inputs/scenario_loader.py` | YAML loader | PRESERVE_UNCHANGED | None | Format loader generic | Preserve |
| `inputs/synthetic_generator.py` | Fixture adapter | ADAPT FIXTURE | Generate canonical ReturnShape/context events | Frozen D02 | Fixtures adapt |
| `cli/main.py` | Assembly/runner | REQUIRED | Build modern models/config and factual summaries | All deltas | CLI/scenario tests adapt |
| `tests/` | Regression | ADD TEST | Keep all historical tests; 6 unchanged, adapt 15, replace 2 interface assertions, add final boundary/formula tests | Modern contract | Baseline plan |
| `scenarios/` | Behavior fixtures | ADAPT FIXTURE | Express canonical geometry/context while retaining intent | Modern input | Acceptance values reviewed |

## Implementation guardrail

Implementation should be incremental: add canonical boundary and tests, preserve gate/aperture/hysteresis modules, then install the already-approved formula behind the existing plug-in. No broad package rewrite or parallel package is justified.
