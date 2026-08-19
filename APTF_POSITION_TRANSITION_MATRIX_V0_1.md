# APTF Position Transition Matrix v0.1

The matrix is the base state-to-action mapping after input reconciliation. It contains all nine pairs exactly once.

| Current | Desired | Transition class | Ordered verbs | Successful result |
|---|---|---|---|---|
| FLAT | FLAT | NO_CHANGE_FLAT | `[NO_ACTION]` | FLAT |
| FLAT | LONG | OPEN_LONG | `[BUY]` | LONG |
| FLAT | SHORT | OPEN_SHORT | `[SELL_SHORT]` | SHORT |
| LONG | FLAT | CLOSE_LONG | `[SELL]` | FLAT |
| LONG | LONG | HOLD_LONG | `[HOLD]` | LONG |
| LONG | SHORT | REVERSE_LONG_TO_SHORT | `[SELL, SELL_SHORT]` | SHORT |
| SHORT | FLAT | CLOSE_SHORT | `[BUY_TO_COVER]` | FLAT |
| SHORT | LONG | REVERSE_SHORT_TO_LONG | `[BUY_TO_COVER, BUY]` | LONG |
| SHORT | SHORT | HOLD_SHORT | `[HOLD]` | SHORT |

D03 authorization remains controlling. Base verbs describe the required semantic transition, but only a `READY` plan with `action_authorized=true` may be submitted. A D03 `BLOCKED` record retains the base required verbs for audit but produces plan status `BLOCKED`; consumers must not execute it. `TRANSITION_ALREADY_PENDING` produces `PENDING_ALREADY` with an empty verb list to prevent duplicate intent.

Human renderings are direct and entity-parameterized: `BUY <entity>`, `SELL <entity>`, `SELL SHORT <entity>`, `BUY TO COVER <entity>`, `HOLD <entity>`, and `NO ACTION <entity>`.
