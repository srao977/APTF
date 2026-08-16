from __future__ import annotations

import argparse
from pathlib import Path
import platform

import yaml
from rich.console import Console

from aptf_d01.runtime.experiment_runner import run_experiment_matrix
from aptf_d01.runtime.report_writer import write_markdown


console = Console()


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def list_scenarios(root: Path) -> int:
    data = yaml.safe_load((root / "config" / "synthetic_scenarios.yaml").read_text(encoding="utf-8"))
    for s in data["scenarios"]:
        console.print(s)
    return 0


def run_scenario(root: Path, name: str) -> int:
    from aptf_d01.providers.synthetic_provider import SyntheticProvider
    from aptf_d01.runtime.experiment_runner import _build_model_cfg, _load_yaml
    from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel

    cfg_default = _load_yaml(root / "config" / "default.yaml")
    first_exp = _load_yaml(root / "config" / "experiment_matrix.yaml")["experiments"][0]
    model = AdaptiveParametricModel(_build_model_cfg(cfg_default, first_exp))
    provider = SyntheticProvider(root / "synthetic" / f"{name}.yaml", entity_id=cfg_default["entity_id"])

    for i, obs in enumerate(provider.stream()):
        dmo, fmo, _ = model.step(obs, obs.model_available_timestamp)
        if i % 10 == 0:
            console.print(
                f"[{obs.model_available_timestamp:05.1f}] {obs.entity_id} "
                f"variant={first_exp['variant']} n={first_exp['polynomial_order']} "
                f"price={obs.price:.4f} RV={dmo.volume_state.relative_volume:.3f} "
                f"Vlog={dmo.volume_state.volume_log:.3f} perturb={dmo.perturbation_state:.2f} "
                f"strength={dmo.strength:.2f} Hobs={dmo.observation_half_life:.1f}s Hfwd={dmo.forward_half_life:.1f}s "
                f"reinforce={dmo.reinforcement:+.2f} uncertainty={dmo.uncertainty:.2f} "
                f"direction={dmo.direction_state:+.2f} magnitude={dmo.magnitude_state:.4f} reversal={dmo.reversal_tendency:.2f}"
            )
    return 0


def _write_docs(root: Path, artifacts) -> None:
    best_dir = artifacts.best_directional
    best_mag = artifacts.best_magnitude
    low_drift = artifacts.lowest_drift
    best_stability = artifacts.best_stability

    exp_results = f"""# D01 Experiment Results v0.1

## Executive Summary

All 15 matrix configurations were executed across 10 deterministic synthetic scenarios.

- Best directional accuracy: {best_dir['experiment_id']} ({best_dir['directional_accuracy']:.4f})
- Best magnitude MAE: {best_mag['experiment_id']} ({best_mag['magnitude_mae']:.6f})
- Lowest parameter drift: {low_drift['experiment_id']} ({low_drift['parameter_drift_total']:.6f})
- Best DMO stability: {best_stability['experiment_id']} ({best_stability['dmo_stability']:.6f})

## Experiment Matrix

Variants A-E with polynomial orders n=1,2,3 (15 total).

## Data Used

Synthetic scenarios from `synthetic/*.yaml`; no live market access.

## Synthetic Scenarios

01 quiet market
02 volume shock
03 price + volume confirmation
04 price + volume divergence
05 perturbation memory reset
06 reinforcement extends half-life
07 reversal after persistent state
08 high volume low displacement
09 low volume high displacement
10 irregular event-time sampling

## Metric Definitions

Directional accuracy, magnitude MAE/RMSE, excursion MAE, persistence error,
half-life error, state flips, perturbation-associated flips, parameter drift.

## Results Table

See `output/metrics/experiment_metrics.csv`.

## Comparisons

- No-volume vs volume: compare A_* against B/C/D/E_* rows.
- Fixed vs adaptive half-life: compare B_* against C_*.
- Adaptive vs perturbation-responsive half-life: compare D_* against E_*.
- n=1 vs n=2 vs n=3: compare *_n1, *_n2, *_n3 within each variant.

## Findings Notes

- High-volume/low-displacement does not force maximum strength due to explicit guardrail.
- Low-volume/high-displacement can still trigger perturbation through displacement channels.
- Ambiguous metrics should be treated as inconclusive, not as production proof.

## Open Questions

- Whether richer microstructure directionality should replace sign(delta_price)*log(1+RV).
- Whether polynomial order >1 consistently improves calibration after real-data replay.
"""
    write_markdown(root / "docs" / "D01_EXPERIMENT_RESULTS_V0_1.md", exp_results)

    model_math = """# D01 Model Mathematics v0.1

Implemented mathematics:

- Relative volume: RV(t)=V(t)/V_baseline(t)
- Log volume: V_log(t)=log(1+RV(t))
- Volume density: rho_V=sum(V in I)/elapsed_seconds
- Directional volume: D_V=sign(delta_price)*V_log
- Volume interactions: I_VM_abs=V_log*abs(delta_price), I_VM_signed=V_log*delta_price
- Half-life decay: w(delta_t)=2^(-delta_t/H)
- Adaptive half-life: bounded deterministic update in [H_min,H_max]
- Perturbation-responsive half-life: shortening proportional to perturbation magnitude
- Parametric basis: bounded polynomial order n in {1,2,3}
- Multi-output mapping: one model instance emits multiple DMO channels
- Parameter update: bounded online gradient with L2 regularization
- Uncertainty proxy: bounded function of strength and perturbation
- FMO mapping: directional_support, expected_magnitude, persistence, decay, reversal, excursions

Design-only / future mathematics:

- Learned non-exponential temporal relevance
- Rich microstructure direction classification
- State-conditional mass/density models
"""
    write_markdown(root / "docs" / "D01_MODEL_MATHEMATICS_V0_1.md", model_math)

    temporal_doc = """# D01 Temporal Model v0.1

T(t)={I_o,H_o(t),t_m,I_f,H_f(t)}

Implemented V0 behavior:

- I_o is rolling bounded observation interval.
- I_f is fixed forward interval per run.
- H_o and H_f are bounded adaptive half-lives.
- Non-uniform observation spacing is supported using real elapsed seconds.
- Perturbation can shorten half-life.
- Reinforcement can lengthen half-life.
- Bounds are always enforced.
"""
    write_markdown(root / "docs" / "D01_TEMPORAL_MODEL_V0_1.md", temporal_doc)

    volume_doc = """# D01 Volume Model v0.1

Implemented channels:

- raw volume
- relative volume baseline normalization
- log transform
- time density
- directional volume proxy
- volume x movement interactions
- volume half-life input
- effective mass candidates M0 and M1

Scenario emphasis:

- high volume + low displacement does not auto-max strength
- lower volume + higher displacement can still produce perturbation
"""
    write_markdown(root / "docs" / "D01_VOLUME_MODEL_V0_1.md", volume_doc)

    schema_doc = """# D01 DMO/FMO Schema v0.1

DMO fields include identity/versioning, intervals, input snapshots,
Adaptive Signal snapshot, current state fan-out, half-lives,
perturbation state, volume state, parameter summary, and health metadata.

FMO fields include forward interval, directional support,
expected magnitude/persistence/decay, reversal tendency, uncertainty,
favorable/adverse excursion estimates, confidence, and metadata.

All fields are emitted as machine-readable JSONL and summarized in CSV files.
"""
    write_markdown(root / "docs" / "D01_DMO_FMO_SCHEMA_V0_1.md", schema_doc)

    physical_doc = """# D01 Physical Design v0.1

Purpose: implement D01 design v0.3 boundaries as a deterministic prototype.

Key subsystems:

- provider-neutral input contract
- temporal model with adaptive half-life
- adaptive signal and perturbation subsystem
- volume subsystem with explicit mathematics
- bounded polynomial parametric subsystem
- MIMO DMO fan-out and FMO generation
- FMO capture and realized-outcome evaluation
- JSONL/CSV audit outputs
- deterministic replay and benchmark path

Explicit exclusions:

- no D02 integration in this build
- no D04 integration in this build
- no broker integration
- no live/paper trading
"""
    write_markdown(root / "docs" / "D01_PHYSICAL_DESIGN_V0_1.md", physical_doc)

    limitations_doc = """# D01 Limitations and Open Questions v0.1

- Synthetic data limitations.
- Placeholder mathematics in uncertainty and excursion projections.
- Online gradient parameter update limitations.
- Polynomial basis limitations and potential instability risk.
- Directional volume proxy limitations.
- Effective mass remains an initial hypothesis.
- No true microstructure trade classification.
- No real market data in v0.1 experiments.
- No D02 integration in this build.
- No D04 integration in this build.
- No broker execution.
- No live trading.
"""
    write_markdown(root / "docs" / "D01_LIMITATIONS_AND_OPEN_QUESTIONS_V0_1.md", limitations_doc)

    exp_plan_doc = """# D01 Experiment Plan v0.1

Hypotheses:

- Adaptive half-life improves temporal relevance handling versus fixed half-life.
- Volume channels improve directional/magnitude quality versus no-volume runs.
- Polynomial order n>1 may improve fit but may increase drift/instability.

Matrix:

- Variants A-E
- Orders n=1,2,3
- 15 total runs

Controls:

- Chronological processing only
- Point-in-time enforcement on every observation
- Deterministic seeds and scenario definitions

Falsification criteria:

- No directional/magnitude improvement for adaptive half-life over fixed.
- No measurable gain from volume-enabled variants.
- n>1 adds drift without useful metric improvement.
"""
    write_markdown(root / "docs" / "D01_EXPERIMENT_PLAN_V0_1.md", exp_plan_doc)


def run_matrix(root: Path) -> int:
    artifacts = run_experiment_matrix(root)
    _write_docs(root, artifacts)

    completion = f"""# D01 v0.1 Completion Report

## Implementation summary

D01 physical prototype implemented under `d01_adaptive_parametric_model/` with provider-neutral replay,
adaptive temporal model, volume mathematics, perturbation response, MIMO DMO/FMO output,
capture/evaluation, deterministic matrix execution, and benchmark.

## Tests

Run `pytest -q`.

## Experiment matrix

15/15 configurations executed.

## Key numerical results

- Best directional config: {artifacts.best_directional['experiment_id']} ({artifacts.best_directional['directional_accuracy']:.4f})
- Best magnitude config: {artifacts.best_magnitude['experiment_id']} ({artifacts.best_magnitude['magnitude_mae']:.6f})
- Lowest parameter drift: {artifacts.lowest_drift['experiment_id']} ({artifacts.lowest_drift['parameter_drift_total']:.6f})
- Best DMO stability: {artifacts.best_stability['experiment_id']} ({artifacts.best_stability['dmo_stability']:.6f})

## Determinism

{'PASS' if artifacts.deterministic_pass else 'FAIL'}

## Benchmark

100000 observations
Runtime: {artifacts.benchmark_runtime:.4f} s
Observations/sec: {artifacts.benchmark_ops:.2f}

## Recommended next step

Run the same matrix on chronologically split historical SPY normalized replay data and compare stability/calibration drift against synthetic results before designing D02 mappings.
"""
    write_markdown(root / "output" / "reports" / "D01_V0_1_COMPLETION_REPORT.md", completion)
    write_markdown(root / "output" / "reports" / "determinism_report.md", f"# Determinism\n\nResult: {'PASS' if artifacts.deterministic_pass else 'FAIL'}\n")

    console.print("run-matrix complete")
    return 0


def benchmark(root: Path) -> int:
    artifacts = run_experiment_matrix(root)
    console.print(f"100000 observations in {artifacts.benchmark_runtime:.4f}s ({artifacts.benchmark_ops:.2f} obs/s)")
    return 0


def summarize(root: Path) -> int:
    import csv

    metrics = list(csv.DictReader((root / "output" / "metrics" / "experiment_metrics.csv").open("r", encoding="utf-8")))
    if not metrics:
        console.print("No metrics found. Run run-matrix first.")
        return 1
    best_dir = max(metrics, key=lambda r: float(r["directional_accuracy"]))
    best_mag = min(metrics, key=lambda r: float(r["magnitude_mae"]))
    low_drift = min(metrics, key=lambda r: float(r["parameter_drift_total"]))
    best_stability = min(metrics, key=lambda r: float(r["state_flip_count"]) / max(1.0, float(r["observation_count"])))

    console.print(f"Best directional: {best_dir['experiment_id']} ({best_dir['directional_accuracy']})")
    console.print(f"Best magnitude: {best_mag['experiment_id']} ({best_mag['magnitude_mae']})")
    console.print(f"Lowest drift: {low_drift['experiment_id']} ({low_drift['parameter_drift_total']})")
    console.print(f"Best stability: {best_stability['experiment_id']}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="APTF D01 Adaptive Parametric Model CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-scenarios")

    p_run = sub.add_parser("run-scenario")
    p_run.add_argument("name")

    p_exp = sub.add_parser("run-experiment")
    p_exp.add_argument("experiment_id")

    sub.add_parser("run-matrix")
    sub.add_parser("benchmark")
    sub.add_parser("summarize")
    return parser.parse_args()


def main() -> int:
    root = project_root()
    args = parse_args()

    if args.command == "list-scenarios":
        return list_scenarios(root)
    if args.command == "run-scenario":
        return run_scenario(root, args.name)
    if args.command == "run-experiment":
        # v0.1 executes full matrix for consistent output artifacts.
        return run_matrix(root)
    if args.command == "run-matrix":
        return run_matrix(root)
    if args.command == "benchmark":
        return benchmark(root)
    if args.command == "summarize":
        return summarize(root)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
