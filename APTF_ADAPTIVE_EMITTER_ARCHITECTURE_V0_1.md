# APTF Adaptive Emitter Architecture Authority V0.1

Status: PRODUCTION CANDIDATE / PRE-RESERVE  
Validated implementation: `experimental_adaptive_emitter/emitter.py` SHA-256 `e8b736dfba03b454633831585222d5270c18b7f8eae510b34ee19dc1f5c58410`.

The Emitter is one synchronous logical stateful function consuming current observation, exactly 15 prior completed immutable records, and inherited state. D01, D02, and four-factor H/Q_G/Q_S/Q_R/C are internal operators. One actionable observation yields one immutable emission, one BUY/SELL/HOLD decision, and next state before another source row is exposed.

Initialization consumes 15 observations with status INITIALIZING and no terminal decision. The rolling aperture advances by one observation with no block reset. State contains internal experimental Position State, prior decision, completed count, D01 recursive state, and prior-15 records. It is not broker state.

The forward-only source stream exposes only `next_observation()`, hard-stops at the development bound, and rejects reserve timestamps. Feedback from emission n updates prior decision and internal Position State effective at n+1. Adaptive rolling values evolve; rules do not. Source timestamps and nanosecond lifecycle time are separate.

This authority incorporates the complete validated architecture in `APTF_TEST_006A_EMITTER_ARCHITECTURE_V0_1.md` and causal cover in `APTF_TEST_006A_CAUSAL_COVER_PROOF_V0_1.md` without changing either.