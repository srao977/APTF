# APTF Test 013B Plan V0.1

Validate the SPY-developed adaptive Price method on unseen QQQ data without transferring SPY coefficients, centers, or scales. Freeze source identity, derivative construction, F0/F4 methods, lambda, windows, RK45 settings, covers, metrics, and classifications before constructing QQQ state or scoring outcomes.

QQQ supplies its own causal local history at every observation. Primary evaluation compares F0_W15 and F4_L1_W30 on exact common cover. W15/W30/W60 sensitivity uses a separate common cover and cannot replace W30. Volume, P&L, trading rules, colors, AutoPilot, broker, Runtime, Emitter, Position State, and prior tests remain untouched.
