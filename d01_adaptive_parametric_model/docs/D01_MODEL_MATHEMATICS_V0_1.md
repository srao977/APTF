# D01 Model Mathematics v0.1

Implemented mathematics:

- Relative volume: RV(t)=V(t)/V_baseline(t)
- Log volume: V_log(t)=log(1+RV(t))
- Volume density: rho_V=sum(V in I)/elapsed_seconds
- Directional volume: D_V=sign(delta_price)*V_log
- Volume interactions: I_VM_abs=V_log*abs(delta_price), I_VM_signed=V_log*delta_price
- Half-life decay: w(delta_t)=2^(-delta_t/H)
- Adaptive half-life: bounded deterministic update in [H_min,H_max]
- Perturbation-responsive half-life: shortening proportional to perturbation magnitude
- Parametric basis: bounded polynomial order n in {1,2,3}
- Multi-output mapping: one model instance emits multiple DMO channels
- Parameter update: bounded online gradient with L2 regularization
- Uncertainty proxy: bounded function of strength and perturbation
- FMO mapping: directional_support, expected_magnitude, persistence, decay, reversal, excursions

Design-only / future mathematics:

- Learned non-exponential temporal relevance
- Rich microstructure direction classification
- State-conditional mass/density models
