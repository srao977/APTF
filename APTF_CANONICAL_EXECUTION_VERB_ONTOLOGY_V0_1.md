# APTF Canonical Execution Verb Ontology v0.1

## Status and boundary

Design freeze candidate. This consumer-independent language translates an authoritative position-state transition; it does not select a desired position, quantity, price, order type, broker, venue, or timing policy.

## Position states

- `FLAT`: no directional exposure in the entity.
- `LONG`: positive directional exposure.
- `SHORT`: negative directional exposure.

States contain no quantity. `LONG` never means buy more and `SHORT` never means sell more.

## Primitive verbs

| Verb | Exact meaning | Valid source | Result after success |
|---|---|---|---|
| `BUY` | Establish LONG exposure | FLAT | LONG |
| `SELL` | Close existing LONG exposure | LONG | FLAT |
| `SELL_SHORT` | Establish SHORT exposure | FLAT | SHORT |
| `BUY_TO_COVER` | Close existing SHORT exposure | SHORT | FLAT |
| `HOLD` | Preserve already-open directional exposure | LONG or SHORT | unchanged |
| `NO_ACTION` | Preserve absence of directional exposure | FLAT | FLAT |

`HOLD` and `NO_ACTION` are separate. HOLD communicates deliberate preservation of non-FLAT exposure; NO_ACTION communicates continued FLAT state. Neither changes exposure or constitutes a broker order.

Reversal names are not verbs. A reversal is an ordered sequence of close then open primitives.

## Exclusions

Verbs do not encode quantity, price, order type, time-in-force, account, broker, venue, leverage, margin, profitability, benchmark result, or execution success. Execution confirmation is external factual evidence.
