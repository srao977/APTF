# APTF Test 009 Derivative Window Selection V0.1

Primary window: **15 observations**.

Selection was performed before opening Test 008 P&L and without Emitter labels. The predeclared lexicographic rule maximized valid fits, minimized single-observation D1 reversal-run percentage, minimized D2 sign-change rate, maximized median D1 persistence, and used smaller-window responsiveness only as a final tie-break.

- Window 3: valid=101206, D1 crossings=62435, single-reversal=59.72451349403379%, D2 change rate=0.6712217775801591, median D1 persistence=1.0.
- Window 5: valid=101206, D1 crossings=37925, single-reversal=23.282794990112063%, D2 change rate=0.41245985870263324, median D1 persistence=2.0.
- Window 8: valid=101206, D1 crossings=24141, single-reversal=13.789246955513214%, D2 change rate=0.2610740576058495, median D1 persistence=4.0.
- Window 15: valid=101206, D1 crossings=13212, single-reversal=8.688412926663135%, D2 change rate=0.1422261745961168, median D1 persistence=7.0.

Primary near-zero threshold: empirical Q10(|D1|) = `0.0035332071428566536`. Sensitivity values: Q05 `0.0017320854030486998`, Q15 `0.005440976485674653`.

P&L used for selection: **NO**.
