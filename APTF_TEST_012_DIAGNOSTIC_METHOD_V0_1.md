# Test 012 Baseline Diagnostic Method V0.1

Use all 90,968 successful Test 011 projections; preserve six solver failures separately. Absolute P2 error groups are overlapping flags at empirical Q90/Q95/Q99/Q99.5/Q99.9 plus `TYPICAL_BELOW_MEDIAN`; headline rows assign the highest qualifying group.

For baseline affine standardized coefficients beta, physical Jacobian terms are `a1=beta_P/sigma_P`, `a2=beta_P1/sigma_P1`, `a3=beta_P2/sigma_P2`. Analyze eigenvalues of `[[0,1,0],[0,0,1],[a1,a2,a3]]`.

Local domain is the causal Test 010 fit-window min/max and standardized center/scales from each frozen emission. Dense diagnostic grid is tau=0.0...1.0 by 0.1 using frozen F_P and primary Test 011 RK45; it does not alter adaptive solver steps.

Severe set is top 0.1% absolute P2 error (ceil count, ties preserved). Matched stable controls are selected deterministically from below-median error rows by minimum standardized Euclidean distance in `[P,|P1|,|P2|,local hour,state scales]`, same derivative state preferred. Controls are diagnostic only.
