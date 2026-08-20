# Test 013B External Validation Decision V0.1

Classification: **CONDITIONALLY_EXTERNALLY_VALIDATED_CONTINUOUS_CANDIDATE**.

## Generalization result

The frozen adaptive method generalized from SPY to QQQ. No SPY coefficient, center, or scale was transferred. QQQ causally estimated every local field from its own history.

Relative to QQQ F0_W15, F4_L1_W30 reduced P2 MAE by 96.01%, P2 RMSE by 99.97%, P2 Q99 by 82.67%, P2 Q99.9 by 94.69%, maximum P2 error by 99.997%, perturbation Q99 by 94.70%, local-domain exits by 42.06%, and Jacobian max-real Q99 by 84.52%. P2 sign and derivative-state accuracy each improved by about 9.0 percentage points. F4 had zero RK failures versus one F0 failure.

This reproduces every central SPY stabilization direction on QQQ and supports generalization of the adaptive method rather than an SPY-specific coefficient fit.

## Remaining concerns

F4 upper/lower recall is only 11.45%/10.26%, below F0. Local-domain exits remain 45.07%. The max-real eigenvalue is positive for 99.999% of local F4 fields even though its Q99 magnitude falls from 4.946 to 0.765. Price-movement sign remains below 50%. These concerns prevent unconditional validation or Runtime/Control promotion.

W30 is not highly fragile. On exact 97,712-row sensitivity cover, all windows remain bounded with zero RK failures. W30 leads P2 MAE/RMSE; W15 leads direction/state/perturbation slightly; W60 leads domain retention and conditioning. W30 remains primary.

RK45 continuous Price propagation now has conditional support on two ETFs, not universal validation.
