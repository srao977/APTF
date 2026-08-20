# APTF Test 009V Causal Volume Derivative Method V0.1

Given frozen V_N and actual UTC elapsed-minute coordinates relative to current observation, fit for each $w\in\{3,5,8,15\}$:

$$V_N(\tau)=a_v\tau^2+b_v\tau+c_v.$$

At current observation:

$$V1=b_v,\qquad V2=2a_v.$$

Units are normalized-volume units/minute and normalized-volume units/minute². No centered derivative, centered smoother, future observation, interpolation, or assumed fixed spacing is used.

Raw backward Volume change is retained only as reference:

$$raw\_V1_n=(V_{RAW,n}-V_{RAW,n-1})/\Delta t_{minutes}.$$

The primary Volume derivative window is selected without crossings, decisions, episodes, or P&L using the Test 009 stability ordering: maximum valid actionable fits, minimum single-observation V1 reversal-run rate, minimum V2 sign-change rate, maximum median V1 persistence, then smaller-window responsiveness only as an exact tie-break.