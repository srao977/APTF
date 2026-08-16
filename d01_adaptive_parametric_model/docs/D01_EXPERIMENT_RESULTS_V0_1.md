# D01 Experiment Results v0.1

## Executive Summary

All 15 matrix configurations were executed across 10 deterministic synthetic scenarios.

- Best directional accuracy: A_n2 (0.8000)
- Best magnitude MAE: A_n1 (1271909391.206709)
- Lowest parameter drift: A_n1 (5130.521075)
- Best DMO stability: A_n2 (0.068108)

## Experiment Matrix

Variants A-E with polynomial orders n=1,2,3 (15 total).

## Data Used

Synthetic scenarios from `synthetic/*.yaml`; no live market access.

## Synthetic Scenarios

01 quiet market
02 volume shock
03 price + volume confirmation
04 price + volume divergence
05 perturbation memory reset
06 reinforcement extends half-life
07 reversal after persistent state
08 high volume low displacement
09 low volume high displacement
10 irregular event-time sampling

## Metric Definitions

Directional accuracy, magnitude MAE/RMSE, excursion MAE, persistence error,
half-life error, state flips, perturbation-associated flips, parameter drift.

## Results Table

See `output/metrics/experiment_metrics.csv`.

## Comparisons

- No-volume vs volume: compare A_* against B/C/D/E_* rows.
- Fixed vs adaptive half-life: compare B_* against C_*.
- Adaptive vs perturbation-responsive half-life: compare D_* against E_*.
- n=1 vs n=2 vs n=3: compare *_n1, *_n2, *_n3 within each variant.

## Findings Notes

- High-volume/low-displacement does not force maximum strength due to explicit guardrail.
- Low-volume/high-displacement can still trigger perturbation through displacement channels.
- Ambiguous metrics should be treated as inconclusive, not as production proof.

## Open Questions

- Whether richer microstructure directionality should replace sign(delta_price)*log(1+RV).
- Whether polynomial order >1 consistently improves calibration after real-data replay.
