# APTF Position Action Consumer Equivalence v0.1

## Invariant

A canonical plan has one meaning across human, simulator, and broker-adapter consumers. Consumers may differ in mechanics but cannot reinterpret state effects.

| Verb | Human meaning | Simulator effect | Future broker-adapter requirement |
|---|---|---|---|
| BUY | establish LONG | FLAT -> LONG on success | map to positive-exposure acquisition |
| SELL | close LONG | LONG -> FLAT on success | map to long-closing sale |
| SELL_SHORT | establish SHORT | FLAT -> SHORT on success | map to short-opening sale |
| BUY_TO_COVER | close SHORT | SHORT -> FLAT on success | map to short-closing purchase |
| HOLD | retain open exposure | no state change | submit no order |
| NO_ACTION | remain FLAT | no state change | submit no order |

Entity is a parameter; no instrument is hard-coded. Quantity, price, order type, time-in-force, account, permissions, and fills belong to consumer-specific contracts. An adapter must reject unsupported mechanics rather than alter verb meaning.

Human readability: PASS. Backtest-simulator translatability: PASS. Broker-adapter translatability: PASS. Semantic equivalence: PASS.
