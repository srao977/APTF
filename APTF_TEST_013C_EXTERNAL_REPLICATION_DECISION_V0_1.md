# Test 013C External Replication Decision V0.1

Classification: **SECOND_EXTERNAL_REPLICATION_CONDITIONAL**.

## Replication

DIA materially reproduced the frozen F4 stabilization signature relative to DIA F0. F4 reduced P2 MAE 74.09%, RMSE 98.49%, Q99 81.99%, Q99.9 91.92%, maximum error 99.90%, perturbation Q99 96.01%, domain exits 40.82%, and Jacobian max-real Q99 84.96%. P2 sign improved 9.113 percentage points and derivative-state accuracy improved 8.989 points. F4 had zero RK failures.

This is the same qualitative signature observed on SPY and QQQ. DIA fitted every local coefficient, center, and scale from DIA causal history; no fitted state was transferred.

## Quietness

The visual impression that DIA is quieter is **mixed and not materially supported**. DIA, SPY, and QQQ all have median absolute one-minute movement of 0.06. DIA has lower Q95/Q99 raw movement (0.26/0.45 versus roughly 0.28/0.51), but fewer unchanged rows (3.43% versus 5.64% SPY and 5.13% QQQ). Median relative movement is above SPY and close to QQQ. All sources have four-decimal precision and minimum observed increment 0.0001. Precision does not explain a material quietness difference.

F4 stabilizes exact-zero rows and every predeclared movement band, including Q0-Q25 and Q99-Q100. Its benefit is not dependent on high-motion observations.

## Remaining concerns

Upper/lower transition recall remains 10.90%/10.54%, local-domain exits remain 45.92%, and local maximum-real eigenvalues remain positive despite strong magnitude reduction. Window sensitivity is acceptable, but W15 leads direction and W60 leads domain retention. These concerns prevent unconditional confirmation and cockpit/Runtime promotion.

Evidence conditionally supports the same adaptive method across SPY, QQQ, and DIA. Universality is not claimed.
