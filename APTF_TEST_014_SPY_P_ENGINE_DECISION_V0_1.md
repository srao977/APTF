# Test 014 SPY P-Engine Decision V0.1

Classification: **SPY_P_ENGINE_EMISSION_CONDITIONAL**.

The numerical emission is causal, deterministic, serializable, explainable, and production-interface compatible. It preserves current/projected `[P,P1,P2]`, phase, turning tendency, domain, stability, confidence, raw/cockpit color, and reason codes. The lamp is not a trade action.

Untouched policy validation is not strong enough for READY. Maximum/minimum precursor recall is 22.30%/23.61%, false deterioration/recovery rates are 53.99%/53.57%, and in-session color chatter is 134.49 changes per session. Median detected lead is four minutes. Debounce nearly eliminates direct GREEN/RED reversal, but does not reduce total chatter.

Domain exits are retained and downgrade confidence without forcing RED. OUT_OF_DOMAIN and LOW confidence have worse P2 magnitude error, but unexpectedly higher P2 sign/state accuracy; confidence is therefore a deterministic caution category, not calibrated probability.

The P Engine emission may be reviewed as an experimental cockpit lamp, but it is not ready for active cockpit reliance, Runtime Core promotion, Execution Controller use, paper trading, or live integration. The next missing component is **P-emission policy refinement under a new predeclared SPY policy-validation design**, focused on chatter and turn precision/recall without P&L.
