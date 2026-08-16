# D01 Stage 2 Realized-State Observer Specification v0.2

**AUTHORITATIVE SOURCE:**  
`D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2.md`

**IN CASE OF CONFLICT, THE FROZEN DESIGN V0.2 CONTROLS.**

This document is a canonical implementation-facing extract of approved Design v0.2. It does not create independent scientific authority.

## 10. Independent Realized-State Observer

The measuring instrument uses only subsequent raw close observations and anchor close. It uses no D01 state, parameter, adaptive reference, or later D01 output to construct realized geometry.

For anchor $t$, later elapsed time $u$ in minutes, and raw close $C$:

$$
y_t(u)=\log\left(\frac{C(t+u)}{C(t)}\right),\qquad x(u)=u.
$$

At each horizon compute:

1. endpoint displacement $y_t(h)$;
2. through-origin slope
$$b_t(h)=\frac{\sum_jx_jy_j}{\sum_jx_j^2};$$
3. through-origin quadratic coefficients $y=bx+\frac12ax^2$ when at least two future points exist;
4. path length $A_t(h)=\sum_j|y_j-y_{j-1}|$;
5. path efficiency $E_t(h)=|y_t(h)|/A_t(h)$, defined as zero if $A=0$;
6. RMS line-path deviation normalized by path length, defined as zero for a zero-length path;
7. maximum and terminal signed progress relative to the DMO claim.

Continuous geometry is primary. Discrete labels are derived secondarily.

## 11. State Compatibility and Invalidation

The DMO's state-direction claim is:

$$
d_t=\operatorname{sign}(V_t),
$$

falling back in order to $\operatorname{sign}(A_t)$ and $\operatorname{sign}(L_t)$ only if the preceding value is exactly zero. If all are zero, directional scoring and survival are inconclusive; non-directional realized geometry remains available.

At horizon $h$:

- `CONTINUATION`: $d_ty_t(h)>0$ and $d_tb_t(h)>0$;
- `WEAKENING`: $d_ty_t(h)\ge0$ and $d_tb_t(h)\le0$;
- `REVERSAL`: $d_ty_t(h)<0$ and $d_tb_t(h)<0$;
- `AMBIGUOUS/INCONCLUSIVE`: all other cases or $d_t=0$.

State validity duration $T_{valid}(t)$ is elapsed time to the first future observation whose prefix geometry becomes `REVERSAL`. This zero-crossing/sign rule is dimensionless and fixed by geometry; no historically selected barrier is used.

If reversal appears across a gap, invalidation time is interval-censored in `(last compatible, first reversing]`. If no invalidation appears before the available scoring boundary, it is right-censored.

## 12. Sign/Mirror Invariance

**Invariant:** multiplying every directional quantity in an anchor/future geometry by `-1` must leave efficiency, path deviation, compatibility category, $T_{valid}$, and semantic evidence classification unchanged except for coordinate signs.

This must become a mandatory implementation test for continuation, weakening, reversal, perturbation-class geometry, and invalidation.