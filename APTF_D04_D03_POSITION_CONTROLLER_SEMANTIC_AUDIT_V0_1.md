# APTF D04 / D03 / Position Controller Semantic Audit V0.1

Status: READ-ONLY DIAGNOSTIC ARCHITECTURAL / SEMANTIC AUDIT. NOT FROZEN AUTHORITY.

No implementation, model, threshold, replay, backtest, mock-context, or freeze change was made.

## Authority verification

| Component | Version | Authority artifact | SHA256 | Verification |
|---|---|---|---|---|
| D01 | v0.2 runtime / pre-Stage-3 freeze v0.1 | `D01_PRE_STAGE_3_ARCHITECTURE_FREEZE_V0_1.json` | `b6ed942e41ec1c72350cf9247597e5819a942dbe9d04770c23e243204165b235` | VERIFIED |
| D02 | v0.2 | `D02_RETURNSHAPE_IMPLEMENTATION_V0_2_FREEZE.json` | `c8029c4b9608547bbf7960f05e4f8613480c4fb2bf8594d94482516b954f7e72` | VERIFIED; 13/13 frozen files match |
| D04 | v0.2.1 | `D04_TRADING_ENVELOPE_IMPLEMENTATION_V0_2_1_FREEZE.json` | `f72a86b3085bd11d8626f06f1fe3faedde60570365488176011239382a46f1af` | VERIFIED; manifest seal matches |
| D03 | v0.1 | `D03_DECISION_CONTROL_IMPLEMENTATION_V0_1_FREEZE.json` | `6a93291ffe555a3fff1239a9a4f88c0a1546b6c46a02b60586614b60a3c91ad6` | VERIFIED; 13/13 frozen files match |
| Position/action design | v0.1 | `APTF_POSITION_ACTION_DESIGN_V0_1_FREEZE.json` | `ecb4f1749c5c70e1405513ad8f50dab9bed5f53ffa1ebb3569935f1b2f45db20` | VERIFIED |
| Position Transition Controller | v0.1 | `position_transition_controller/APTF_POSITION_TRANSITION_CONTROLLER_IMPLEMENTATION_V0_1_FREEZE.json` | `7c4f7ddc616a28090d3698634d67e4a6d71d4ef58744e9dee6c9cc5b06714bc2` | VERIFIED |
| Controller implementation manifest | v0.1 | `position_transition_controller/APTF_POSITION_TRANSITION_CONTROLLER_IMPLEMENTATION_V0_1_MANIFEST.json` | `7d543120d7ff7ddb03c4ba5e6bfdeca98ac83aadea3f13a325df370cbcd07ac0` | VERIFIED; 5/5 protected files match |

## Original component intent

| Component | Stated responsibility | Explicitly outside responsibility | Inputs | Outputs | Knows current position? | Knows desired position? | Knows verbs? | Knows execution feasibility/broker state? | Determines direction? |
|---|---|---|---|---|---|---|---|---|---|
| D02 | Represent D01 forward geometry without material loss | Capturability, candidate, execution, portfolio, position, orders, decisions | D01 `DMOOutput` + `FMOOutput` | 17-field `ReturnShape` | NO | NO | NO | NO | YES: descriptive path orientation from terminal displacement |
| D04 | Capturability, feasibility, aperture, hysteresis, envelope lifecycle, candidate formation/events | Alternate market inference, trades, BUY/SELL/HOLD, position commitment | `ReturnShape` + 13-field `EnvelopeContext` | 23-field `EnvelopeEvaluation`, optional candidate | NO actual position; only `position_capacity` scalar | NO | NO | YES, as pre-candidate context | NO; copies D02 direction verbatim |
| D03 | Convert factual D04 state plus causal control context into desired control state and authorization | Market prediction, ReturnShape construction, capturability, candidate creation, orders, sizing, routing | `EnvelopeEvaluation` + 12-field `DecisionContext` | 21-field `DecisionRecord` | YES, externally supplied | YES, it determines it | NO primitive verbs; knows transition intent | Knows `execution_available`, not raw broker/capital dimensions | NO; consumes candidate direction |
| Position Transition Controller | Validate lineage/state, translate actual + desired into transition class and primitive sequence, preserve D03 authorization | Market interpretation, sizing, routing, fills, profitability | committed D03 record/hash + actual-position snapshot | `PositionTransitionPlan` | YES | YES | YES | NO direct raw context | NO |

Brief authority phrases:

- D02: “path orientation, not LONG/SHORT advice” in [D02_RETURNSHAPE_CANONICAL_DESIGN_V0_2.md](D02_RETURNSHAPE_CANONICAL_DESIGN_V0_2.md), section 7.
- D04: “does not infer an alternate market state or commit trades” in [D04_TRADING_ENVELOPE_MODERNIZATION_DESIGN_V0_2.md](D04_TRADING_ENVELOPE_MODERNIZATION_DESIGN_V0_2.md), section 4.
- D03: “desired-state centric with a derived transition intent” in [D03_DECISION_CONTROL_ARCHITECTURE_TRACE_V0_1.md](D03_DECISION_CONTROL_ARCHITECTURE_TRACE_V0_1.md), section 6.
- Controller: “performs no market interpretation, sizing, routing, fill assumption, or profitability evaluation” in [APTF_POSITION_TRANSITION_CONTROLLER_DESIGN_V0_1.md](APTF_POSITION_TRANSITION_CONTROLLER_DESIGN_V0_1.md), Responsibility.

## Answers to the five architectural questions

| Question | Answer |
|---|---|
| A. What direction/state does the analytical model indicate? | D01 owns inference; D02 creates the descriptive `path_direction` view over D01's projected endpoint. |
| B. What position does APTF desire to hold? | D03 owns `desired_position_state`, conditional on control overrides and D04 state/candidate qualification. |
| C. What transition is required? | D03 derives semantic intent; the Position Transition Controller validates and derives the exact state-pair transition class. |
| D. What human/broker-understandable verb represents it? | Position Transition Controller, using the frozen six-primitive matrix. |
| E. Is it permitted/feasible/safe now? | D04 applies pre-desire capturability/safety/operational feasibility; D03 applies post-desire `execution_available`; controller enforces the committed authorization. A downstream independent risk/broker layer is architectural but not part of this frozen four-component decision chain. |

## D02 meaning

`path_direction` domain: `UPWARD`, `DOWNWARD`, `FLAT`.

It is descriptive, not prescriptive. It means the D01 projected terminal level is above, below, or exactly equal to the current level. It does not mean LONG, SHORT, BUY, SELL, or any broker action. D02 has no current position, capital, broker health, execution feasibility, or verb field.

## D04 meaning

D04 receives D02 direction but never computes an alternative. Candidate construction performs:

```python
CandidateEnvelope(path_direction=return_shape.path_direction)
```

The v0.2.1 freeze states `propagation=VERBATIM`, `d04_recomputes=false`, and `d04_reinterprets=false`.

D04 can:

- suppress candidate creation through $H$, $B$, $G$, $C$, hysteresis, safety, and lifecycle;
- invalidate an existing candidate;
- preserve the candidate's original direction when present.

D04 cannot:

- rewrite UPWARD to DOWNWARD or FLAT;
- choose LONG/SHORT directly;
- choose BUY/SELL/etc.;
- separately authorize a verb already selected downstream.

## D03 meaning

The directional mapping is conditional:

- OPEN + QUALIFIED + UPWARD -> LONG.
- OPEN + QUALIFIED + DOWNWARD -> SHORT.
- OPEN + QUALIFIED + FLAT -> FLAT.
- Every non-OPEN, safety, absent-candidate, or invalidated-candidate case -> FLAT, except disabled controls preserve actual position and emergency flatten has priority.

After desired state is resolved, D03 derives NO_CHANGE/OPEN/CLOSE/REVERSE/RETARGET. If `execution_available=false`, an actionable transition becomes `BLOCKED` while desired position remains unchanged.

## Position Transition Controller meaning

The controller is a pure position-transition translator with validation and authorization preservation. It does not consume D04 context, broker health, capital availability, or direction. Its verb identity is a pure function of current and desired position. Reversals use two ordered primitives.

### Static design-to-code non-conformance

The matrix/verb output is exact, but three promised validation behaviors are incomplete:

- Same-target pending: frozen D03 emits `NO_CHANGE` plus T10/`TRANSITION_ALREADY_PENDING`; the frozen controller design requires `PENDING_ALREADY` and empty verbs. The implementation instead rejects a changing base pair in its `NO_CHANGE` branch. Its `PENDING_ALREADY` intent branch cannot be reached through its own validator and is not a D03 intent.
- Intent consistency: the design requires OPEN/CLOSE/REVERSE to match the actual-to-desired matrix class. The implementation accepts any of those actionable intent labels with any changing base pair when `action_authorized=true`.
- Authority reconciliation: design-required complete-record/hash/entity/identity checks are only partially implemented; the supplied hash is bound into output identity but not verified against record content.

The protected files match their frozen manifest. This is semantic implementation non-conformance, not hash drift. It does not alter the responsibility conclusion or six-verb matrix. No code was executed or repaired.

## Do D04 properties determine the six verbs?

**PARTIALLY, and only indirectly.**

- They do not directly select any verb.
- Twelve score-active fields can alter candidate existence and therefore D03 desired position.
- Current position plus that desired position determines verb identity in the controller.
- They cannot block an already-selected verb as a distinct post-desire permission decision.
- D03 `execution_available` can block the transition while preserving desired position and base verbs for audit.

## Model A versus Model B

The frozen architecture implements **Model A**:

```text
D01 -> D02 -> D04 (analytical + operational capturability)
    -> D03 desired position/authorization
    -> Position Transition Controller verbs
```

It does not implement Model B's relocation of capital, broker, liquidity, latency, portfolio, and risk gates after verb translation. Moving those fields would change D04 candidate/capturability semantics, alter D03 target outcomes, and violate current D04/D03 frozen authority. It would not be a mere wiring change.

## All-FLAT output reassessment

Classification: **C, with D as the consequence for historical interpretation.**

The output used synthetic perfect operational context, so it is not a genuine point-in-time historical context stream. It is deterministic evidence for that synthetic scenario. It cannot establish that D01/D02 were flat: D02 direction existed and changed independently. It also cannot be treated as a faithful live execution-gated stream because account/broker/execution conditions were not historically observed.

## Final resolution

**RESOLUTION A: CURRENT ARCHITECTURE IS SEMANTICALLY CORRECT AS FROZEN. D04 CONTEXT LEGITIMATELY PARTICIPATES BEFORE DESIRED POSITION.**

This is the resolution encoded by frozen authority, not an endorsement that perfect constants are valid historical evidence. A desired-position-only historical experiment that intentionally removes operational context is not defined by the frozen architecture and remains a separate human design decision.

Resolution A concerns component responsibility and D04/D03 ordering. It does not waive the controller implementation non-conformance identified above.
