# Test 012 J_P Target Audit V0.1

For a contiguous pair O_k -> O_(k+1):

$$J_{P,k+1}=(P2_{k+1}-P2_k)/\Delta t_{minutes}.$$

Units: price/minute^3. At model time O_n, training targets may use only pairs ending at or before O_n. Test 012 excludes SESSION_TRANSITION, OVERNIGHT_GAP, WEEKEND/HOLIDAY_GAP, and same-session missing-row gaps. Delta-t must equal exactly one minute and both frozen P2 values must be finite. Future leakage is prohibited.

Test 010's historical target used any positive elapsed interval; Test 012 explicitly corrects this for continuous intrasection identification without modifying Test 010 evidence.