# APTF D03 Desired-Position Boundary Decision Point V0.1

Status: DIAGNOSTIC. NOT FROZEN AUTHORITY.

## Finding

**FINDING D: D03 ITSELF USES D04 INFORMATION, ACTUAL POSITION AND/OR CONTROL STATE TO DERIVE LONG/SHORT/FLAT IN A WAY THAT CANNOT BE REDUCED TO D02 DIRECTION PLUS D04 PERMISSION.**

## Why

For the ordinary fully enabled branch, the reduced statement is true:

```text
qualified D02/D04 UPWARD -> LONG
qualified D02/D04 DOWNWARD -> SHORT
qualified D02/D04 FLAT -> FLAT
```

D04 analytical/external/control properties permit or suppress candidate transport but do not select sign.

The complete frozen D03 policy has higher-precedence branches:

- emergency control forces FLAT;
- system/trading disabled preserves actual position, which may be FLAT, LONG, or SHORT regardless of D04;
- invalid control yields no decision.

Therefore identical D04 input can produce different desired states solely from actual position under disabled controls. The full causal boundary is not reducible to direction plus D04 permission.

## Minimal-input comparison

### Current frozen schema minimum

A complete 23-field `EnvelopeEvaluation` and complete 12-field `DecisionContext` are required for any committed record.

### Target-active minimum

- control precedence: emergency, system enabled, trading enabled, actual state for disabled preservation;
- D04 safety, stale, projection validity, envelope state;
- candidate existence/status/path direction;
- valid control state.

Pending and execution availability are required schema/control inputs but act after desired target selection.

### Analytical desire information already present

- D02 `path_direction` supplies sign;
- D04 state/candidate supplies qualification;
- no independent pre-D04/pre-gate desired-position field exists.

## Threshold answer

With current state CLOSED, $C<0.75$ cannot produce an ordinary LONG or SHORT. It yields CLOSED, no candidate, then D03 R31 FLAT. Semantically this is no qualified candidate/envelope, not a new analytical FLAT direction.

## Non-change declaration

No implementation, configuration, threshold, D04, D03, controller, broker, replay, tuning, or freeze change was made. Human review is required.
