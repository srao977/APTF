# Test 006A Emitter Definition V0.1

The Emitter is one logical stateful function. It atomically consumes the current observation, the immutable immediately prior 15 completed observation records, and inherited recursive state. It emits one immutable Emission, exactly one terminal Position Decision (`BUY`, `SELL`, or `HOLD`) after initialization, and next recursive state.

Existing D01, D02, and four-factor D04 mathematics are synchronous internal operators. There is no asynchronous messaging, broker, order router, fill, portfolio, telemetry decision, or batch boundary.

The first 15 observations are `INITIALIZING` and emit no Position Decision. O16 is first actionable. Context advances by one completed observation and never resets. Values adapt causally; equations, context length, semantics, conflict resolution, adaptation, and feedback rules do not change after O16 becomes accessible.

Feedback consists only of the persisted prior decision and internal Position State (`FLAT`, `LONG`, `SHORT`), effective from n+1. It cannot alter Emission n. Invalid input is `INVALID`, never HOLD.