# D01 v0.2 Synthetic Validation

Phase B runner covers deterministic synthetic scenarios S01-S10 and ablation smoke execution.

- Preflight mode: subset of scenarios and ablations for quick gate.
- Full mode: S01-S10 x all required ablations.
- Worker PID evidence persisted to diagnostics/worker_process_evidence.csv.

Manual full launch:
- `scripts/run_d01_v02_phase_b.ps1 -RunFull`
