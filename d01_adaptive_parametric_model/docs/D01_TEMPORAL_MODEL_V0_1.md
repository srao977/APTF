# D01 Temporal Model v0.1

T(t)={I_o,H_o(t),t_m,I_f,H_f(t)}

Implemented V0 behavior:

- I_o is rolling bounded observation interval.
- I_f is fixed forward interval per run.
- H_o and H_f are bounded adaptive half-lives.
- Non-uniform observation spacing is supported using real elapsed seconds.
- Perturbation can shorten half-life.
- Reinforcement can lengthen half-life.
- Bounds are always enforced.
