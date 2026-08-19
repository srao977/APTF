# APTF D04 / D03 Semantic Decision Point V0.1

Status: DIAGNOSTIC / DESIGN REVIEW ONLY. NOT FROZEN AUTHORITY.

## Evidence-based resolution

**RESOLUTION A: CURRENT ARCHITECTURE IS SEMANTICALLY CORRECT AS FROZEN. D04 CONTEXT LEGITIMATELY PARTICIPATES BEFORE DESIRED POSITION.**

## Why Resolution A follows from authority

The frozen D04 modernization design explicitly states:

- all 13 context fields are required and causal;
- liquidity, spread, latency, execution feasibility, broker health, capital, portfolio, position, risk, and data integrity enter the minimum feasibility gate $G$;
- $C=HBG$ drives envelope state and candidate qualification;
- no typed context field moves to D03 because each constrains present capturability.

The frozen D03 design then states that only an OPEN envelope with a current QUALIFIED directional candidate may target LONG or SHORT. Therefore D04 operational context intentionally participates before desired position.

The frozen controller design independently states that verb identity is derived only after desired position exists, from actual/desired state. This confirms that D04 fields do not belong to the six-verb translator itself.

## Why this is not Resolution B

The replay is not merely misusing an already-separated desire/permission contract. D03 does have a separate `execution_available` overlay, but D04 deliberately embeds operational feasibility in candidate qualification before desire. The frozen contract is only partially separated.

## Why this audit does not choose Resolution C

The frozen semantics themselves are resolved: they intentionally couple present capturability context to candidate/desire. What is unresolved is a different experiment specification: how to produce an analytical desired-position history when causal operational/account/broker context is unavailable. That does not make the current frozen architecture ambiguous; it means the proposed reduced historical experiment is outside its contract.

## Human design decision still required

Before another historical desired-position replay, choose one of these future design paths through a separate authority process:

1. Supply genuine causal historical D04 context from additional market, account, portfolio, risk, and broker-state records.
2. Freeze an explicit historical scenario policy and label its output as scenario-conditioned rather than observed history.
3. Define a new analytical-only output before operational feasibility, distinct from frozen D03 `desired_position_state`.
4. Redesign D04/D03 into Model B, knowingly changing frozen semantics.

This audit recommends none of these and implements none.

## Separate controller implementation decision

Human review must also disposition a static conformance defect in the frozen controller implementation: T10 same-target pending cannot produce the designed `PENDING_ALREADY` plan, transition-intent/base-class consistency is not enforced, and several promised authority checks are incomplete. This does not change Resolution A for D04/D03 semantic ownership, but it prevents claiming complete controller conformance without a separate authorized repair and re-freeze process.

## Consequence for the existing output

The 106,603-row all-FLAT file is scenario-conditioned by synthetic perfect context. It is not evidence that the analytical model was flat and is not a faithful point-in-time historical desired-position stream.

## Stop boundary

No implementation, model, threshold, replay, backtest, context synthesis, or freeze modification is authorized. Human review is required.
