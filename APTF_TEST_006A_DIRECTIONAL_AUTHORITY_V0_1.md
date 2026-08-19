# Test 006A Directional Authority V0.1

Directional authority is **D02 `path_direction`**, mechanically derived from the sign of `terminal_displacement`, where terminal displacement is the terminal D01 forward-sample level minus current D01 state level. `UPWARD` maps to positive sign, `DOWNWARD` to negative sign, and `FLAT` to zero. D01 signed `state_velocity` and `state_acceleration` remain provenance/context but do not replace canonical D02 direction.

This authority is causal, producer-backed, deterministic, and available at the current observation. BUY and SELL are never inferred from positive scalar C alone. No fabricated directional variable exists.