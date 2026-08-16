# D01 Experiment Plan v0.1

Hypotheses:

- Adaptive half-life improves temporal relevance handling versus fixed half-life.
- Volume channels improve directional/magnitude quality versus no-volume runs.
- Polynomial order n>1 may improve fit but may increase drift/instability.

Matrix:

- Variants A-E
- Orders n=1,2,3
- 15 total runs

Controls:

- Chronological processing only
- Point-in-time enforcement on every observation
- Deterministic seeds and scenario definitions

Falsification criteria:

- No directional/magnitude improvement for adaptive half-life over fixed.
- No measurable gain from volume-enabled variants.
- n>1 adds drift without useful metric improvement.
