# APTF Test 012 Plan V0.1

Phase 1 diagnoses frozen Test 011 without fitting alternatives: error tails, dense severe traces, matched controls, Jacobians/eigenvalues, coefficient/condition relationships, local fitted-domain exits, and target alignment. Phase 2 begins only after those artifacts pass, freezes F0-F5 and all evaluation rules, then compares candidates on identical common cover under frozen RK45 tolerance/horizon.

Structural state remains `[P,P1,P2]`; only dP2/dt is investigated. Volume, trading, P&L, colors, AutoPilot, broker, Runtime, and all prior tests remain frozen.

Primary continuous training pairs are only `INTRASESSION_CONTINUOUS`, exactly one-minute transitions whose target endpoint is available at model time. No gap/session target is admitted. No trajectory clipping/winsorization is permitted.
