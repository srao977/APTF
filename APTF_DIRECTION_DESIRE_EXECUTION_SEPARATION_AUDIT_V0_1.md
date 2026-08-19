# APTF Direction, Desire, and Execution Separation Audit V0.1

Status: DIAGNOSTIC / DESIGN REVIEW ONLY. NOT FROZEN AUTHORITY.

## Executive answer

The frozen contracts distinguish three concepts, but not at every boundary:

1. Analytical direction is a D02 descriptive field.
2. Desired position is a D03 control target, conditional on D04 candidate qualification.
3. Execution permission is represented twice: operational feasibility is embedded in D04 before candidate/desire, while D03 `execution_available` can block a transition after desire is known.

Thus desire and permission are **partially separate**.

## Direction lineage

```text
D01 DMO/FMO
  -> D02 terminal_displacement
  -> D02 ReturnShape.path_direction
  -> D04 CandidateEnvelope.path_direction (verbatim, only if candidate exists)
  -> D03 desired_position_state
  -> Position Transition Controller verb sequence
```

D02 creates direction using:

$$
\operatorname{path\_direction}=
\begin{cases}
\text{UPWARD}, & \Delta_T>0\\
\text{DOWNWARD}, & \Delta_T<0\\
\text{FLAT}, & \Delta_T=0
\end{cases}
$$

D02 authority explicitly says this is path orientation, not LONG/SHORT advice. D04 v0.2.1 copies the enum verbatim, does not recompute it, cannot overwrite it, and cannot force it to FLAT. D04 instead may fail to create a candidate or may invalidate one. D03 sees direction only through a current `CandidateEnvelope`.

Authorities: [D02_RETURNSHAPE_CANONICAL_DESIGN_V0_2.md](D02_RETURNSHAPE_CANONICAL_DESIGN_V0_2.md), [D04_TRADING_ENVELOPE_IMPLEMENTATION_V0_2_1_FREEZE.json](D04_TRADING_ENVELOPE_IMPLEMENTATION_V0_2_1_FREEZE.json), and [D03_D04_INPUT_INVENTORY_V0_1.md](D03_D04_INPUT_INVENTORY_V0_1.md).

## D03 target policy

Target rules execute in priority order:

| Condition | Desired position | Semantics |
|---|---|---|
| `emergency_flatten=true` | FLAT | Highest-priority control override |
| `system_enabled=false` | actual position | Preserve current state; no deferred target |
| `trading_enabled=false` | actual position | Preserve current state; no deferred target |
| D04 safety closed, stale, or projection invalid | FLAT | Safety target |
| D04 state CLOSED | FLAT | Envelope unavailable |
| D04 state OPENING | FLAT | Not yet qualified |
| D04 state CLOSING | FLAT | Envelope closing |
| OPEN with no candidate | FLAT | No valid candidate |
| OPEN with INVALIDATED candidate | FLAT | Candidate unavailable |
| OPEN, QUALIFIED, `path_direction=FLAT` | FLAT | Non-directional candidate |
| OPEN, QUALIFIED, `path_direction=UPWARD` | LONG | Directional target |
| OPEN, QUALIFIED, `path_direction=DOWNWARD` | SHORT | Directional target |

The UPWARD/LONG and DOWNWARD/SHORT mappings are conditional, not unconditional.

## Desire versus D03 execution permission

The current D03 contract can represent:

```text
desired_position_state = LONG
transition_intent = BLOCKED
action_authorized = false
supporting_reason = EXECUTION_UNAVAILABLE
```

and the same structure with desired SHORT. This occurs when D04 has already supplied a qualified directional candidate, the actual-to-desired transition is actionable, and `DecisionContext.execution_available=false`.

The controller retains the required base verbs for audit, marks the plan `BLOCKED`, and does not permit execution. Therefore desired LONG/SHORT plus blocked execution is fully representable.

## Where desire and permission remain coupled

D04's $G$ includes liquidity, spread, latency, execution feasibility, capital, portfolio, position, risk, broker health, and data integrity. Since $C=HBG$ drives hysteresis and candidate creation, poor operational feasibility can prevent a candidate. D03 then receives CLOSED/OPENING/no candidate and chooses FLAT. At that earlier boundary, the contract does not preserve an independent directional desired position alongside a D04 feasibility block.

This produces a hybrid structure:

- D04 operational infeasibility can suppress desire before it exists.
- D03 execution unavailability can block a transition without changing an already-resolved desire.

## Semantic-collapse inventory

| Condition | Current representation | Distinct or collapsed? | Component | Consequence |
|---|---|---|---|---|
| D02 direction versus desired position | Direction retained in ReturnShape; only qualified candidate direction maps to desire | Distinct | D02/D04/D03 | Direction alone is not advice |
| Candidate direction versus candidate actionability | Direction exists upstream, but D03 receives it only if D04 creates/retains a candidate | Partially collapsed at candidate boundary | D04 | Unqualified direction cannot produce LONG/SHORT target |
| D04 execution infeasibility versus analytical desire | Low $G$ lowers $C$, can prevent OPEN/candidate, causing D03 FLAT | Collapsed before desire | D04/D03 | No separate “directional desire but D04 infeasible” record |
| D03 execution unavailable versus desired position | Desired retained; transition becomes BLOCKED | Distinct | D03 | LONG/SHORT plus blocked is representable |
| No candidate versus FLAT analytical direction | Both target FLAT, but different reason codes | State collapsed; reason preserved | D03 | Desired state alone loses cause |
| Safety closure versus analytical FLAT | Both target FLAT, but safety reason and rule ID differ | State collapsed; reason preserved | D03 | Audit record retains distinction |
| System/trading disabled | Desired equals actual and NO_CHANGE | Distinct control-preservation reason | D03 | Disabled does not imply market-flat opinion |
| Blocked transition versus FLAT | Blocked retains original desired state | Distinct | D03/controller | No accidental flattening |
| HOLD versus NO_ACTION | Separate primitives for non-FLAT and FLAT alignment | Distinct | Controller | Human semantics preserve exposure state |

## Direct answers

- Desired position and execution permission separate concepts: **PARTIALLY**.
- `desired=LONG`, execution blocked: **YES**.
- `desired=SHORT`, execution blocked: **YES**.
- D04 can force candidate suppression while preserving ReturnShape direction upstream: **YES**.
- D04 can rewrite `path_direction`: **NO**.
- Position Transition Controller can override D03 authorization: **NO**.
