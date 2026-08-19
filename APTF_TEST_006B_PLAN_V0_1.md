# APTF Test 006B One-Way Reserve Validation Plan V0.1

Status: AUTHORIZED / PRE-EXECUTION  
Emitter freeze: `ADAPTIVE_EMITTER_PRE_RESERVE_FREEZE_V0_1`.

This prompt is explicit human authorization for one one-way reserve run. The frozen Test 006A implementation, rules, context length, adaptation, feedback, and semantics are immutable. Reserve observations are streamed once in literal source order through `next_observation()`; the first 15 initialize state and the remaining 101,206 emit exactly one BUY/SELL/HOLD decision.

The reserve range is derived from governance metadata only: source data rows 106,604-207,824, corresponding to physical CSV rows 106,605-207,825 inclusive. No reserve value was read before authorization. Original source columns are projected unchanged into the required CSV with appended emitter fields. No outcome/profit fields are added.

Because the reserve contains 101,221 rows, immutable emissions, adaptation events, and feedback events are persisted incrementally to JSON artifacts. The frozen Emitter remains unchanged; its append-only audit collections are replaced at construction time with append-only disk sinks that preserve every record without retaining the entire reserve in RAM. These sinks are evidence plumbing only and are not read by the decision path.

No rewind, second pass, parameter search, broker, or post-hoc rule change is authorized.