# D02/D04 Modernization Open Issues v0.2

## 1. Status

**Status:** ALL D02-BOUNDARY ISSUES RESOLVED BY HUMAN REVIEW; FREEZE CANDIDATE

No D02 scientific, representation, protocol, lifecycle-boundary, or ownership issue remains open. D04-specific consumption and stale-state response design is intentionally deferred and does not reopen D02.

## 2. Resolved representation decisions

### R1. Flat-path numerical convention — RESOLVED BY HUMAN REVIEW

`FLAT` applies if and only if terminal displacement equals exactly zero; otherwise sign determines orientation. D02 uses no epsilon or materiality tolerance. Economic significance belongs to D04.

### R2. Magnitude representation — D02 BOUNDARY RESOLVED; D04 CONSUMPTION DESIGN DEFERRED

D02 preserves signed terminal displacement, maximum absolute displacement, and the full path. It emits no normalized `magnitude_score`. D04 later decides which geometry affects capturability and owns any D04-specific normalization.

### R3. Support representation — D02 BOUNDARY RESOLVED; D04 CONSUMPTION DESIGN DEFERRED

D02 preserves direct unbounded `state_support_ratio` and complete projected support coordinates. It emits no bounded `forward_support`. D04 later decides whether and how support affects capturability.

## 3. Resolved engineering protocol

### P1. Interface identity and monotonicity — RESOLVED BY HUMAN REVIEW

Canonical ReturnShape identity is `(entity_id, model_time)`. D02 emits no `return_shape_id`, version, or synthetic sequence. D04 may use monotonic model time for same-entity ordering/supersession.

## 4. Resolved lifecycle boundary

### L1. Supersession and staleness — D02/D04 BOUNDARY RESOLVED; DETAILED D04 RESPONSE DEFERRED

A newer same-entity shape supersedes the older shape immediately. Without a newer shape, validity includes the endpoint `model_time + projection_interval`; staleness begins only after that endpoint. D04 owns detailed stale-state transitions/events.

## 5. Resolved responsibility ownership

### O1. Candidate identity boundary — RESOLVED BY HUMAN REVIEW

D04 owns candidate formation and candidate identity and passes candidate/envelope information to D03. `candidate_id` is not D02 output and cannot alter D02 geometry.

`candidate_rr` is not an open D02 issue: remove it from the ReturnShape contract. Any future reward/risk construct belongs to an explicitly designed downstream decision/control contract, not to D02 and not to `state_support_ratio`.

## 6. D04 core mathematics impact

The prototype `shape_component` weighted sum must be revised because it consumes obsolete scalar inputs. This is a controlled D04 design task. It must determine how, or whether, natural D01-aligned coordinates enter capturability. The feasibility gate, aperture update, hysteresis state machine, envelope states, and event architecture remain separable and reusable.

This issue does not create a D02 scientific gap and must not be resolved by fitting historical outcomes in this task.

## 7. Resolution counts

| Issue class | Open | Resolved/deferred at correct boundary |
|---|---:|---:|
| Genuine D02 scientific mathematics | 0 | 0 |
| D02 representation design | 0 | 3 |
| Engineering protocol | 0 | 1 |
| D02/D04 lifecycle boundary | 0 | 1 |
| Responsibility ownership | 0 | 1 |
