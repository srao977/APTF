# APTF Benchmark Decision Model Exclusion Attestation v0.1

## Scope

This attestation verifies that benchmark/outcome information is excluded from the frozen causal system. It does not claim that a benchmark dataset has been identified.

## Evidence

- The raw FirstRateData source manifest lists only timestamp and OHLCV fields.
- The normalized dataset manifest lists 22 fields and no decision-like field.
- The frozen D01 mapping positively selects only `event_timestamp_utc`, `data_valid`, `close`, `volume`, and `session_type`, then constructs identity and availability fields.
- The Stage 2 input-isolation audit reports zero decision/target columns passed to D01 and proves synthetic poison fields cannot affect D01 state or observer evidence.
- Frozen D01 Q_t explicitly prohibits outcome/benchmark labels and vendor decisions.
- Frozen D02 has no benchmark field or benchmark input path.
- Frozen D04 has no benchmark field or benchmark input path.
- Frozen D03 DecisionContext has 12 fields and no benchmark field; its runtime source governance scan has zero benchmark access.

## Boundary matrix

| Boundary | Benchmark allowed? | Result |
|---|---:|---|
| D01 input/state | NO | PASS |
| D02 input/output | NO | PASS |
| D04 input/output | NO | PASS |
| D03 DecisionContext/policy | NO | PASS |
| D03 DecisionRecord before commitment | NO | PASS |
| Post-commit evaluator | YES, after a future contract freeze | NOT YET AUTHORIZED |

No benchmark value was used to fit, tune, select, or validate D01, D02, D04, or D03.

## Reserve governance

Final six-month reserve accessed: NO. Reserved benchmark values inspected: NO. Replay executed: NO. Backtest executed: NO.

## Verdict

**BENCHMARK MODEL EXCLUSION: PASS**
