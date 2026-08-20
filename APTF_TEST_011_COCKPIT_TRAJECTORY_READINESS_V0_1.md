# APTF Test 011 Cockpit Trajectory Readiness V0.1

## Price Engine

Future Price condition should represent trajectory stability and transition proximity, not BUY/HOLD/SELL. Candidate continuous inputs:

- projected P1 and distance from zero;
- projected P2 and derivative-state label;
- J_P at projection start and projected deltas P/P1/P2;
- projected within-minute crossing flag/time;
- F_P condition number and historical P2 error context;
- solver success, nfev/steps, and perturbation amplification;
- gap/ineligibility state.

Readiness: **NO for color-envelope construction from the current RK trajectory**. Although tolerances converge, F_P-driven RK is worse than Test 010, has six numerical instabilities, low transition recall, and high P2 perturbation amplification. Thresholding these projections would quantize an unstable local law.

## Volume Engine

Future Volume condition should represent participation state, not direction or causation. Candidate continuous inputs:

- V_N and discrete G_V update error;
- interval-15 mean/dispersion/max-median ratio;
- elevated/extreme counts and persistence above baseline;
- V1/V2 signs, persistence, and observer-event frequency;
- burst state.

Readiness: **CONDITIONAL for descriptive participation envelopes only**. Volume state is complete and causal but noisy and weakly turn-specific. No threshold may imply BUY/SELL.

## Prohibited mappings

- GREEN != BUY.
- AMBER != HOLD.
- RED != SELL.
- High Volume != BUY or SELL.

Final thresholds created: **NO**  
Execution Window implemented: **NO**  
AutoPilot implemented: **NO**
