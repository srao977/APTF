# APTF Test 007 Long-Only Position Episode Reconstruction Plan V0.1

Status: PRE-RECONSTRUCTION  
Mode: downstream structural analysis only.

Source decision authority is the immutable `APTF_TEST_006B_OBSERVATIONS_WITH_EMITTED_POSITION_V0_1.csv`, SHA-256 `f4c4bcf3e03e37f99ff04444035915d8f28cc24dec6d16a22e32089ad83dbfd4`. No Emitter, D01, D02, D03, D04, Position Controller, reserve replay, decision calculation, P&L, capital, quantity, execution-price, spread, slippage, commission, or outcome process is authorized.

One deterministic pass processes all 101,221 rows in CSV order. The first 15 INITIALIZING rows remain FLAT and have no episode. Actionable BUY/SELL/HOLD values drive only the frozen Test 007 FLAT/LONG state machine. Episode IDs are sequential `EP000001...`. Outputs preserve every Test 006B column unchanged and append structural interpretation. Episode boundary rows retain OHLCV and H/Q_G/Q_S/Q_R/C without choosing execution prices.

After the pass, statistics may inspect completed episodes and structural exceptions. No later observation may alter an earlier row classification or episode boundary.