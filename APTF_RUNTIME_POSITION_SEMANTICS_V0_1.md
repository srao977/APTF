# APTF Runtime Position Semantics V0.1

## HOLD IS STATE-RELATIVE

`LONG + HOLD -> LONG` means maintain the existing long Position State.

`FLAT + HOLD -> FLAT` means remain out of the market.

HOLD does not intrinsically mean that shares exist. It means preserve the current Position State.

## Exact long-only truth table

| State before | Emitter decision | State after | Structural meaning | Execution intent |
|---|---|---|---|---|
| FLAT | BUY | LONG | EPISODE_OPEN | BUY |
| FLAT | HOLD | FLAT | FLAT_HOLD | NONE |
| FLAT | SELL | FLAT | UNMATCHED_SELL_WHILE_FLAT | NONE |
| LONG | BUY | LONG | REPEATED_BUY_WHILE_LONG | NONE |
| LONG | HOLD | LONG | EPISODE_HOLD | NONE |
| LONG | SELL | FLAT | EPISODE_CLOSE | SELL |

## Why Emitter decisions are not broker actions

Test 007 records 14,249 BUY emissions but only 2,051 FLAT->LONG openings; 12,198 BUYs occurred while already LONG. It records 9,779 SELL emissions but only 2,051 LONG->FLAT closes; 7,728 SELLs occurred while FLAT. Therefore raw BUY/SELL cannot flow directly to execution.

Only state-changing transitions create non-NONE Execution Intent. Repeated BUY cannot create another BUY intent. SELL while FLAT cannot create SELL intent and cannot create SHORT.

## Vocabulary separation

- EmitterDecision: BUY, SELL, HOLD.
- PositionState: FLAT, LONG.
- ExecutionIntent: BUY, SELL, NONE.

Historical D03/controller and frozen Emitter internal-state names remain documented in their evidence. Production normalization does not rewrite that history.