# APTF Test 006A Adaptive Emitter Plan V0.1

Status: PRE-EXECUTION DESIGN  
Development range fixed before value inspection: physical rows 115-1114.  
Initialization: rows 115-129 (O1-O15). Actionable: rows 130-1114 (O16-O1000), 985 emissions.

The sealed reserve begins at `2023-03-30T08:00:00Z` and remains inaccessible. A streaming reader skips only to physical row 115, yields one row at a time, stops at row 1114, and rejects any timestamp at or beyond reserve start. The Emitter receives only the current row, an immutable prior-15 context, and inherited state.

Design and rules are frozen before O16. Development validation is one pass with no search, profitability criterion, broker, synthetic input, future statistic, rewind, or reserve access. Eligibility for pre-reserve freeze requires causal integrity plus a non-degenerate BUY/SELL/HOLD stream; otherwise human review is required.