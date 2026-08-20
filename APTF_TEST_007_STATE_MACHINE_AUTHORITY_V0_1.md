# APTF Test 007 Long-Only State-Machine Authority V0.1

Operational states are exactly `FLAT` and `LONG`; initial state is `FLAT`; SHORT does not exist.

| State before | Immutable decision | State after | Classification | Episode effect |
|---|---|---|---|---|
| FLAT | BUY | LONG | EPISODE_OPEN | Create next deterministic episode ID |
| LONG | HOLD | LONG | EPISODE_HOLD | Maintain active episode |
| LONG | SELL | FLAT | EPISODE_CLOSE | Close active episode on this row |
| FLAT | HOLD | FLAT | FLAT_HOLD | No episode |
| FLAT | SELL | FLAT | UNMATCHED_SELL_WHILE_FLAT | No episode; never SHORT |
| LONG | BUY | LONG | REPEATED_BUY_WHILE_LONG | Keep same episode and quantity-unspecified state |

INITIALIZING rows preserve decision text, remain FLAT, and have no episode. A final active episode is `OPEN_AT_END`; no SELL is synthesized. Episode construction uses only state before and immutable current decision in one forward pass. C/Q/OHLCV never control boundaries. No P&L or execution-price semantics exist.