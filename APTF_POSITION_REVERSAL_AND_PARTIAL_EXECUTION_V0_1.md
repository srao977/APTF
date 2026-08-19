# APTF Position Reversal and Partial Execution v0.1

## Ordered reversal

LONG to SHORT is `[SELL, SELL_SHORT]`. SHORT to LONG is `[BUY_TO_COVER, BUY]`. Steps are sequential and conditional. Step 2 may be attempted only after confirmed success of step 1 and an authoritative FLAT intermediate state.

## Partial outcomes

| Transition | Step 1 | Step 2 | Actual result |
|---|---|---|---|
| LONG -> SHORT | SELL success | SELL_SHORT success | SHORT |
| LONG -> SHORT | SELL success | SELL_SHORT failure | FLAT |
| LONG -> SHORT | SELL failure | not attempted | LONG |
| SHORT -> LONG | BUY_TO_COVER success | BUY success | LONG |
| SHORT -> LONG | BUY_TO_COVER success | BUY failure | FLAT |
| SHORT -> LONG | BUY_TO_COVER failure | not attempted | SHORT |

Plans are not atomic execution guarantees. The controller does not retry, compensate, or assume fills. After any failure, the execution ledger records the confirmed actual state and a new D03 evaluation/reconciliation is required before further intent. The second step of a failed-first-step reversal is forbidden.
