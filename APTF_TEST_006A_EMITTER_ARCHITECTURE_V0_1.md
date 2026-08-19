# Test 006A Emitter Architecture V0.1

`emit(current, prior_context_15, prior_state) -> (immutable_emission, next_state)` is one synchronous logical lifecycle. Internal operators are source admission, D01, D02, four-factor H/Q_G/Q_S/Q_R/C, rolling-context derivation, deterministic decision, feedback declaration, and state persistence.

The harness owns a forward-only `next_observation()` stream; the Emitter cannot access the iterator or full dataset. The stream hard-stops at physical row 1114 and rejects timestamps at/after the reserve boundary. Current input is not appended to context until after its emission is committed. Next source row is requested only afterward.

Recursive state contains internal Position State, previous decision, emission sequence, and rolling completed records. There is no broker state. Feedback from n becomes active at n+1. Source time and `perf_counter_ns` lifecycle time remain separate.