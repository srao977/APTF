# D01 Feature Scaling Model v0.1.1

For each feature x(t), use prior state S(t-) to transform then update:

S(t-) -> z(t) = clip((x(t)-mu(t-))/max(sigma(t-), epsilon), [L,U]) -> model -> update S with x(t).

Warmup: deterministic zero model value before minimum observations; updates disabled during warmup.