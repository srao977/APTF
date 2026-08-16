# D01 v0.2 Determinism

Determinism strategy:
- no stochastic sampling in state updates
- pure causal update order
- explicit snapshot export with configuration hash
- repeated replay over identical normalized sequence must match semantic outputs

Determinism checks are included in unit tests and manifest artifacts.
