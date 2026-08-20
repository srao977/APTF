# APTF Runtime DO_NOT_REINTRODUCE Registry V0.1

The following rejected or superseded behaviors are prohibited in APTF Runtime Core V0.1.

1. Arbitrary market, quality, capacity, threshold, or context values introduced merely to satisfy a type.
2. Unexplained 1.0 dimensions standing in for unavailable evidence.
3. Non-observational context dimensions participating as measured D04 inputs.
4. `data_integrity` as a D04 scoring factor; quality belongs at admission.
5. Executable G in current capturability; current C is `H * Q_G * Q_S * Q_R`.
6. Absolute `C >= 0.75` as an Adaptive Emitter BUY/SELL gate.
7. Threshold retuning from Test 004A, Test 005R, development, or reserve outcomes.
8. Claims that C=0.75 is mathematically impossible based on bounded evidence.
9. `FLAT` as an Emitter terminal decision.
10. `NO_ACTION` as an Emitter terminal decision.
11. Raw Emitter BUY sent directly to a broker or repeated BUY execution while already LONG.
12. Raw Emitter SELL sent directly to a broker while FLAT.
13. SELL while FLAT opening SHORT.
14. A production PositionState.SHORT without a future authorizing test.
15. Independent 15-row blocks or resets at observations 15, 30, 45, session boundaries, or file boundaries without authority.
16. Current observation inserted into its own prior context.
17. Full-dataset/index APIs that expose future observations to the core.
18. Feedback from emission n modifying emission n.
19. Runtime rule adaptation; values may adapt but frozen predicates do not.
20. State reset between observations without explicit authority.
21. Reserve-driven retuning or Test 006B Emitter re-execution.
22. P&L, returns, execution price, shares, capital, slippage, commission, spread, fills, or account state inside the Emitter.
23. Broker, paper-order, or live-order adapters in Runtime Core V0.1.
24. The failed Test 006 close/volume mock heuristic, mock D03 hash, blank terminal vocabulary, or reserve-crossing replay route.
25. Treating incomplete Test 005 checkpoints as a serialized empirical trace.
26. Requiring uniform 60-second source intervals when timestamps are strictly increasing.
27. Replacing literal source gaps with synthetic market time.
28. Treating processing duration as source elapsed time or source spacing as CPU latency.
29. Substituting the full historical D04 envelope/hysteresis path for the frozen Test 006A Emitter's direct four-factor evaluation.
30. Collapsing Emitter Decision, legacy Emitter recursive state, production Position State, Position Transition, and Execution Intent into one generic state/action field.
31. Reinterpreting HOLD as intrinsically holding shares; HOLD preserves FLAT or LONG relative to current state.
32. Silent terminology normalization that hides historical D03/Position Controller semantic corrections.
33. Global mutable runtime state shared across symbols or channels.
34. Concurrent mutation of one runtime instance; O_n must complete before O_(n+1).
35. Historical evidence rewrites to make a production extraction pass.

Any future removal or relaxation of an item requires additive versioned authority and regression evidence; V0.1 must not be silently modified.