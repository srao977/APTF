# APTF D01 Adaptive Parametric Model v0.1

This package implements D01 as an entity-centric, provider-neutral, adaptive, point-in-time-causal model that emits Dynamic Model Outputs (DMO) and Forward Model Outputs (FMO).

## Scope

- Does: normalized observations, adaptive temporal model, volume math, perturbation handling, parametric multi-output mapping, FMO capture/evaluation, experiment matrix, deterministic synthetic replay.
- Does not: trading decisions, capturability, broker connectivity, R:R selection, live/paper trading.

## Quick Start

```bash
python -m aptf_d01.cli.main list-scenarios
python -m aptf_d01.cli.main run-matrix
python -m aptf_d01.cli.main benchmark
python -m aptf_d01.cli.main summarize
```
