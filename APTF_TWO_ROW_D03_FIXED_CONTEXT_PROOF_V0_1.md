# APTF Two-Row D03 Fixed-Context Proof V0.1

Status: EXPERIMENTAL / DIAGNOSTIC. NOT FROZEN PRODUCTION AUTHORITY.

## Result

**TWO-ROW PROOF FAILED AT `D04 -> D03`.**

The real source, D01, D02, and D04 executed causally. D03 was not invoked because its required real position/pending/control context was unavailable and the experiment permits fixed artificial values only for D04.

## Causal setup

The source CSV was opened as a `csv.DictReader`. Rows were exposed one at a time. Genuine rows 0-15 established D01/D04 causal state. The loop read target rows 16 and 17 and broke immediately after `2022-09-30T08:17:00Z`; no later source row was read.

Frozen D04 was constructed through `aptf_d04.cli.main.build_envelope` using `d04_trading_envelope/config/default.yaml` unchanged.

## Row A

Timestamp: `2022-09-30T08:16:00Z`

- D01 output type: `tuple[d01.v02.outputs.DMOOutput, d01.v02.outputs.FMOOutput]`
- D01 trace ID: `SPY:17`
- D01 state hash: `FCCB692875A5CF82F914D2E27640C3A503998D00968F9A711E439589AD9BEC03`
- D02 output type: `d02.v02.models.ReturnShape`
- D02 identity: `(SPY, 1664525760.0)`
- D02 `path_direction`: `UPWARD`
- D04 output type: `aptf_d04.models.envelope_state.EnvelopeEvaluation`
- D04 state: `CLOSED -> CLOSED`
- D04 candidate exists: `NO`
- D04 candidate state: `null`
- D04 candidate path direction: `null`
- D04 actionable: `NO`
- $Q_G$: `1.0`
- $Q_S$: `0.8194388482618388`
- $Q_R$: `0.5875472468333434`
- $B$: `0.4814590392445292`
- $G$: `1.0`
- $H$: `1`
- $C$: `0.4814590392445292`
- Aperture before/after: `0.31165485069974536 / 0.3965569449721373`
- Frozen open threshold: `0.75`
- D04 reason codes: `REVERSAL_PROPENSITY_HIGH`
- Exact suppression mechanism: $C < 0.75$, so CLOSED does not enter OPENING; no candidate can exist.
- D03 DecisionRecord: `NOT PRODUCED`
- D03 desired position: `NOT PRODUCED`
- D03 primary reason: `NOT PRODUCED`

## Row B

Timestamp: `2022-09-30T08:17:00Z`

- D01 output type: `tuple[d01.v02.outputs.DMOOutput, d01.v02.outputs.FMOOutput]`
- D01 trace ID: `SPY:18`
- D01 state hash: `0237A5C4ABA304EB7C9D5B1BFC651A080250A381B0E655D402EFBC6790B95509`
- D02 output type: `d02.v02.models.ReturnShape`
- D02 identity: `(SPY, 1664525820.0)`
- D02 `path_direction`: `UPWARD`
- D04 state: `CLOSED -> CLOSED`
- D04 candidate exists: `NO`
- D04 candidate state: `null`
- D04 candidate path direction: `null`
- D04 actionable: `NO`
- $Q_G$: `1.0`
- $Q_S$: `0.8429381315925792`
- $Q_R$: `0.4276796988520893`
- $B$: `0.3605075262704571`
- $G$: `1.0`
- $H$: `1`
- $C$: `0.3605075262704571`
- Aperture before/after: `0.3965569449721373 / 0.37853223562129723`
- Frozen open threshold: `0.75`
- D04 reason codes: `REVERSAL_PROPENSITY_HIGH`
- Exact suppression mechanism: $C < 0.75$, so CLOSED remains CLOSED; no candidate exists.
- D03 DecisionRecord: `NOT PRODUCED`
- D03 desired position: `NOT PRODUCED`
- D03 primary reason: `NOT PRODUCED`

## Direction lineage

Both D02 shapes were UPWARD. D04 did not change either direction. Because no candidate was created, no candidate `path_direction` existed to cross the D04-D03 boundary.

Had a legitimate D03 context existed, frozen rule R31 would map `new_envelope_state=CLOSED` to desired FLAT with primary reason `ENVELOPE_CLOSED`. That statement is static contract analysis, not an executed D03 result.

## Gate assessment

- Real target rows: YES
- Real D01: YES
- Real D02: YES
- Real D04: YES
- Real D03: NO
- Only documented fixed D04 context artificial: YES
- Future market rows used: NO
- One D03 result per target: NO

First blocking boundary: **D04 -> D03**.
