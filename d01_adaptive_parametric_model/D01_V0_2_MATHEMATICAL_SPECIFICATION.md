# D01 v0.2 Mathematical Specification

## Core Equations
- Reference: `mu_t = mu_{t-1} + alpha * (p_t - mu_{t-1})`
- Scale: causal EW update with floor.
- Level: `L_t = (p_t - mu_t) / (s_t + eps)`
- Velocity: `V_t = (L_t - L_{t-1}) / (dt + eps)`
- Acceleration: `A_t = (V_t - V_{t-1}) / (dt + eps)`
- Curvature: `K_t = A_t / (1 + V_t^2)^(3/2)`

## Semantic Channels
- Coherence from weighted signed evidence alignment.
- Strength from bounded logistic combination of mass, kinematics, coherence, uncertainty.
- Persistence from causal agreement update.
- Uncertainty from innovation, incoherence, unknown perturbation, data quality degradation, instability.
- Reversal propensity from opposition, contradiction, low persistence, extremes, uncertainty.

## Temporal Geometry
- Adaptive half-life bounded by configured min/max.
- Elastic forward interval based on persistence, strength, uncertainty, perturbation.
- Non-linear sample schedule with exponent > 1 for near-term concentration.
