# Test 013 Frozen Validation Method V0.1

State `[P,P1,P2]`; structural derivatives unchanged. Primary F4 is exact Test012 centered/scaled affine ridge with lambda 1, W30: local means/population std, standardized design `[1,zP,zP1,zP2]`, unpenalized intercept, ridge matrix diag(0,1,1,1), solve `(D.T D + lambda R)b=D.T J`. Physical affine field is reconstructed exactly and propagated by Test011 RK45 rtol 1e-6 with emission-local vector atol.

J targets use only exactly-one-minute INTRASESSION_CONTINUOUS pairs ending no later than current observation. Fits adapt walk-forward using earlier holdout outcomes only after each projection is persisted/scored.

F0 is frozen Test010 `PRICE_AFFINE_TIME_W15` per-observation field, evaluated by Test011 RK45. W15/W60 use the same F4 lambda=1 implementation as sensitivity only.

Primary cover is F0∩F4W30 valid one-minute rows within observations 101099-101220. Sensitivity cover is W15∩W30∩W60. No metric threshold or model choice changes after scoring.

Perturbation uses Test012 scale rule and affine matrix exponential. Local domain uses training-window min/max plus standardized D_local; dense 0.1-minute RK diagnostics determine first exit.