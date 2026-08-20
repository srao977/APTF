# Test 012 Price Vector-Field Decision V0.1

Decision: **CONDITIONAL continuous field found; not control-ready without independent validation.**

Strongest overall candidate: `F4_L1_W30`, centered/scaled affine ridge with lambda=1 and 30 contiguous targets.

It materially reduces F0 common-cover P2 MAE 0.01019 -> 0.00309, Q99.9 0.31005 -> 0.02333, max 8.0565 -> 0.06057, perturbation Q99 95.52 -> 2.73, and median max-real eigenvalue 1.836 -> 0.419. No RK failures/nonfinite endpoints occurred.

Tradeoffs remain: P/P1 MAE is slightly worse, transition recall falls, and 45.97% of endpoints leave the strict local historical min/max envelope. W60 improves envelope exits/max tail/conditioning but weakens directional behavior; W15 improves direction/state/perturbation but has more exits.

Recommended F_P for a separate validation experiment: `F4_L1_W30`, lambda 1, W30, one-minute RK45 only. It is not authorized to replace frozen F0 or enter cockpit/Runtime.

Current architecture: discrete Test010 propagation remains safer until the ridge field passes chronological independent validation. RK45 remains conditionally justified as an experimental integrator, not a current control propagator.
