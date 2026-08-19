# APTF Temporal Telemetry Non-Drift Plan V0.1

Status: DESIGN / DIAGNOSTIC. NOT FROZEN IMPLEMENTATION AUTHORITY.

## Protected behavior

Telemetry must not alter:

- input payload values or types supplied to frozen calls;
- D01 state evolution, cadence, elapsed-time math, trace/state hashes;
- D02 ReturnShape values/identity;
- D04 scoring, context semantics, hysteresis, aperture, lifecycle, candidate identity;
- D03 policy, fingerprints, reason/rule identities;
- controller state-pair algebra, verbs, transition identity, authorization;
- exception/fail-closed behavior or call order.

## Isolation rules

1. Frozen packages never import `aptf_runtime`.
2. Wrappers invoke public frozen entry points only.
3. Telemetry clocks/IDs are not arguments to frozen mathematical methods.
4. Payload serialization occurs after output production and is side-effect free.
5. Event/observation IDs never enter scientific/control identity preimages.
6. Telemetry failure cannot manufacture a payload or convert a mathematical failure to success.
7. No network/database write occurs inside a frozen method call.
8. Historical event time remains historical; replay processing UTC is separate.

## Future verification matrix

| Check | Required evidence |
|---|---|
| Protected hashes | Exact pre/post SHA256 equality for all frozen files |
| Payload equality | Canonical serialized unwrapped output equals wrapped payload at E1-E5 |
| State equality | D01/D04 snapshots and controller outputs identical |
| Exception equality | Same frozen exception type/code before wrapper error conversion |
| Ordering equality | One call per stage, same E0-E5 order |
| Identity isolation | Scientific IDs identical; envelope IDs absent from payloads |
| Time isolation | Frozen event/model/control fields unchanged |
| Regression | Existing D01/D02/D04/D03/controller suites pass unchanged |
| Dependency direction | Frozen sources do not import wrapper package |

## Error handling

The wrapper catches at the external boundary only after sampling receive time. On failure it samples emit time and creates an ERROR envelope. The original exception remains available to local control policy; the event carries a stable error code/type and sanitized message. No partial scientific object is labeled successful.

## Overhead goal

$O(1)$ local metadata operations per event, no external timestamp service, no synchronous publisher dependency, and no benchmark claim until a separately authorized performance task.

## Freeze governance

The design artifacts are not implementation authority. A future implementation must receive its own approval and may freeze only the new runtime package after proving all frozen cores byte-identical.
