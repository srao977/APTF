# APTF Causal Pipeline Event Cadence Audit v0.1

## Frozen natural cadence

| Stage | Trigger | Natural cadence | State dependency |
|---|---|---|---|
| Source | each admissible normalized observation | source event cadence, here one-minute records with gaps | none |
| D01 | `D01V02Model.step(NormalizedObservation)` | each accepted causally ordered observation | persistent adaptive RuntimeState |
| D02 | `build_return_shape(DMOOutput, FMOOutput)` | each valid D01 output pair | stateless |
| D04 | `TradingEnvelope.process(ReturnShape, EnvelopeContext)` | each new ReturnShape and causal context reevaluation | envelope, aperture, hysteresis, candidate state |
| D03 | `evaluate_decision(D03Input)` | each D04 evaluation and explicit DecisionContext event | stateless over explicit actual/pending/control facts |
| Position Transition Controller | each complete committed D03 record plus reconciled ActualPosition snapshot | D03 commitment order per entity | explicit actual-position version only |

The architecture has no artificial 15-minute decision scheduler. D01 emits DMO/FMO after each successful step; D02 can transform every valid pair; D04 evaluates every supplied shape/context event; D03 commits every valid invocation, including NO_CHANGE and BLOCKED.

## Stream distinction

A valid D03 invocation can provide current `desired_position_state` without authorizing a new execution. Aligned states produce NO_CHANGE with `action_authorized=false`. The frozen controller design still derives a non-executable HOLD or NO_ACTION plan, while adapters may submit only READY/authorized plans.

Therefore:

- one desired-position value per successful integrated observation cycle is structurally supported;
- one new executable action per minute is not supported;
- a CSV containing only authorized execution verbs is naturally sparse;
- the observed one-action result is not evidence of natural frozen cadence because the actual frozen chain never ran.

**EXPECTATION OF ONE TERMINAL VALUE PER MINUTE: PARTIALLY SUPPORTED.** It is supported for a desired-position/state stream after valid integration, not for a new execution-action event stream.
