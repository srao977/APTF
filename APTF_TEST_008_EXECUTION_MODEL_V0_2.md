# APTF Test 008 Execution Model V0.2

## Fixed authority

- Instrument: **SPY**
- Source rows: **101,221**
- Initialization rows: **15**
- Initialization handling: **excluded from all execution and P&L**
- Actionable rows: **101,206**
- Position model: **LONG ONLY**
- Quantity: **100 shares**
- Entry trigger: FLAT -> LONG / ExecutionIntent BUY
- Exit trigger: LONG -> FLAT / ExecutionIntent SELL
- Entry execution: provider `open` of next chronological source observation
- Exit execution: provider `open` of next chronological source observation
- Repeated BUY while LONG: no transaction
- SELL while FLAT: no transaction and no SHORT
- HOLD while LONG: maintain 100 executed shares, subject only to the one-row pending-fill boundary
- HOLD while FLAT: maintain zero executed shares, subject only to the one-row pending-fill boundary
- SHORT: disabled
- Compounding: disabled
- Slippage: zero
- Transaction costs/fees/spread cost: zero
- Dividends/distributions/taxes: excluded
- Financing/cash yield/opportunity cost: excluded
- Capital constraint: not modeled; sufficient capital assumed

## Causal rule

A completed signal at O_n may create a pending ExecutionIntent. It cannot execute from O_n's OPEN, HIGH, LOW, or CLOSE. When the immediately following chronological source row O_(n+1) arrives, the pending event fills first at the exact provider `open` string from O_(n+1). Actual timestamp gaps, sessions, overnight periods, weekends, and missing minutes remain unchanged.

## State separation

Runtime desired Position State (`FLAT`/`LONG`) is immutable Test 007 structure. Simulated quantity (`0`/`100`) changes only on the later execution row. They may differ for one observation. Test 008 never modifies Runtime State to hide that delay.

## Economic definitions

For each completed long trade:

- gross P&L per share = exit price - entry price
- gross P&L = 100 * gross P&L per share
- trade return = gross P&L per share / entry price
- entry/exit notional = 100 * corresponding price

Results are **GROSS P&L UNDER TEST 008 V0.2 ASSUMPTIONS**, not account equity, net executable profit, or evidence of future profitability.