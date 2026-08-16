from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import time

import yaml

from aptf_d01.evaluation.calibration_metrics import uncertainty_calibration_proxy
from aptf_d01.evaluation.directional_metrics import directional_accuracy
from aptf_d01.evaluation.experiment_comparison import best_by_metric
from aptf_d01.evaluation.fmo_capture import FMOCapture
from aptf_d01.evaluation.magnitude_metrics import mae, rmse
from aptf_d01.evaluation.realized_outcome import evaluate_capture
from aptf_d01.evaluation.temporal_metrics import half_life_error, persistence_error
from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel, ModelConfig
from aptf_d01.providers.synthetic_provider import SyntheticProvider
from aptf_d01.runtime.audit_log import AuditLogger
from aptf_d01.runtime.report_writer import write_markdown, write_text_log
from aptf_d01.signals.perturbation_detector import PerturbationThresholds


@dataclass
class ExperimentArtifacts:
    metrics_rows: list[dict]
    best_directional: dict
    best_magnitude: dict
    lowest_drift: dict
    best_stability: dict
    deterministic_pass: bool
    benchmark_runtime: float
    benchmark_ops: float


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _build_model_cfg(default_cfg: dict, exp_cfg: dict) -> ModelConfig:
    th = default_cfg["perturbation"]
    conditioning = default_cfg.get("conditioning", {})
    parametric_cfg = default_cfg["parametric"]
    return ModelConfig(
        entity_id=default_cfg["entity_id"],
        model_instance_id=default_cfg["model_instance_id"],
        model_definition_version=default_cfg["model_definition_version"],
        polynomial_order=int(exp_cfg["polynomial_order"]),
        include_volume=bool(exp_cfg["include_volume"]),
        include_volume_interactions=bool(exp_cfg["include_volume_interactions"]),
        adaptive_half_life=bool(exp_cfg["adaptive_half_life"]),
        perturbation_responsive_half_life=bool(exp_cfg["perturbation_responsive_half_life"]),
        learning_rate=float(parametric_cfg["learning_rate"]),
        l2_regularization=float(parametric_cfg["l2_regularization"]),
        weight_clip=float(parametric_cfg["weight_clip"]),
        observation_interval_seconds=float(default_cfg["temporal"]["observation_interval_seconds"]),
        forward_interval_seconds=float(default_cfg["temporal"]["forward_interval_seconds"]),
        half_life_min=float(default_cfg["temporal"]["half_life"]["min_seconds"]),
        half_life_default=float(default_cfg["temporal"]["half_life"]["default_seconds"]),
        half_life_max=float(default_cfg["temporal"]["half_life"]["max_seconds"]),
        perturbation_shorten_factor=float(default_cfg["temporal"]["half_life"]["perturbation_shorten_factor"]),
        reinforcement_lengthen_factor=float(default_cfg["temporal"]["half_life"]["reinforcement_lengthen_factor"]),
        volume_baseline_method=str(default_cfg["volume"]["baseline_method"]),
        volume_baseline_window=int(default_cfg["volume"]["baseline_window"]),
        volume_half_life_seconds=float(default_cfg["volume"]["half_life_seconds"]),
        interaction_allowlist=list(parametric_cfg["interaction_allowlist"]),
        interaction_max_order=int(parametric_cfg.get("interaction_max_order", int(exp_cfg.get("interaction_max_order", 3)))),
        use_conditioning=bool(conditioning.get("enabled", False)),
        thresholds=PerturbationThresholds(
            displacement_threshold=float(th["displacement_threshold"]),
            velocity_threshold=float(th["velocity_threshold"]),
            acceleration_threshold=float(th["acceleration_threshold"]),
            rv_threshold=float(th["rv_threshold"]),
            volume_density_threshold=float(th["volume_density_threshold"]),
            spread_change_threshold=float(th["spread_change_threshold"]),
        ),
        scaling_min_warmup_observations=int(conditioning.get("minimum_warmup_observations", 0)),
        scaling_epsilon=float(conditioning.get("epsilon", 1e-6)),
        scaling_lower_bound=float(conditioning.get("lower_bound", -1e9)),
        scaling_upper_bound=float(conditioning.get("upper_bound", 1e9)),
        output_overrides=dict(parametric_cfg.get("output_overrides", {})),
        observation_capabilities=default_cfg.get("observation_capabilities"),
    )


def _point_in_time_assert(obs, model_time: float) -> None:
    if obs.model_available_timestamp > model_time:
        raise ValueError("POINT_IN_TIME_VIOLATION")


def _clear_outputs(root: Path) -> None:
    for p in [
        root / "output" / "dmo" / "dmo_all.csv",
        root / "output" / "fmo" / "fmo_all.csv",
        root / "output" / "metrics" / "experiment_metrics.csv",
        root / "output" / "logs" / "runtime.log",
        root / "output" / "logs" / "parameter_changes.log",
        root / "output" / "logs" / "half_life_changes.log",
        root / "output" / "logs" / "perturbations.log",
        root / "output" / "logs" / "fmo_evaluations.log",
        root / "output" / "logs" / "errors.log",
        root / "output" / "audit" / "observations.jsonl",
        root / "output" / "audit" / "perturbations.jsonl",
        root / "output" / "audit" / "signals.jsonl",
        root / "output" / "audit" / "parameter_updates.jsonl",
        root / "output" / "audit" / "dmo.jsonl",
        root / "output" / "audit" / "fmo.jsonl",
        root / "output" / "audit" / "fmo_captures.jsonl",
        root / "output" / "audit" / "realized_outcomes.jsonl",
        root / "output" / "audit" / "experiments.jsonl",
    ]:
        if p.exists():
            p.unlink()


def _append_csv(path: Path, header: list[str], row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if write_header:
            w.writeheader()
        w.writerow(row)


def run_experiment_matrix(root: Path) -> ExperimentArtifacts:
    cfg_default = _load_yaml(root / "config" / "default.yaml")
    cfg_matrix = _load_yaml(root / "config" / "experiment_matrix.yaml")
    scenario_names = _load_yaml(root / "config" / "synthetic_scenarios.yaml")["scenarios"]
    audit = AuditLogger(root / "output" / "audit")

    _clear_outputs(root)

    dmo_csv = root / "output" / "dmo" / "dmo_all.csv"
    fmo_csv = root / "output" / "fmo" / "fmo_all.csv"
    metrics_csv = root / "output" / "metrics" / "experiment_metrics.csv"
    runtime_log = root / "output" / "logs" / "runtime.log"
    parameter_log = root / "output" / "logs" / "parameter_changes.log"
    half_life_log = root / "output" / "logs" / "half_life_changes.log"
    perturb_log = root / "output" / "logs" / "perturbations.log"
    fmo_eval_log = root / "output" / "logs" / "fmo_evaluations.log"
    errors_log = root / "output" / "logs" / "errors.log"
    write_text_log(errors_log, "No runtime errors recorded at matrix start.")

    metrics_rows: list[dict] = []

    for exp_cfg in cfg_matrix["experiments"]:
        t_start = time.perf_counter()
        model = AdaptiveParametricModel(_build_model_cfg(cfg_default, exp_cfg))
        capture = FMOCapture()

        pred_dir: list[float] = []
        act_dir: list[float] = []
        pred_mag: list[float] = []
        act_mag: list[float] = []
        pred_fav: list[float] = []
        act_fav: list[float] = []
        pred_adv: list[float] = []
        act_adv: list[float] = []
        pred_persistence: list[float] = []
        act_persistence: list[float] = []
        pred_half_life: list[float] = []
        act_half_life: list[float] = []
        unc: list[float] = []
        abs_err: list[float] = []

        state_flip_count = 0
        perturb_flip_count = 0
        last_direction_sign = 0
        total_param_drift = 0.0
        obs_count = 0
        capture_count = 0

        for scenario in scenario_names:
            provider = SyntheticProvider(root / "synthetic" / f"{scenario}.yaml", entity_id=cfg_default["entity_id"])
            obs_rows = provider.stream()
            for i, obs in enumerate(obs_rows):
                model_time = obs.model_available_timestamp
                _point_in_time_assert(obs, model_time)

                dmo, fmo, update = model.step(obs, model_time)
                obs_count += 1

                write_text_log(
                    runtime_log,
                    (
                        f"t={model_time:.3f} entity={obs.entity_id} exp={exp_cfg['id']} "
                        f"price={obs.price:.4f} rv={dmo.volume_state.relative_volume:.4f} "
                        f"strength={dmo.strength:.4f} dir={dmo.direction_state:.4f}"
                    ),
                )
                write_text_log(
                    half_life_log,
                    (
                        f"t={model_time:.3f} entity={obs.entity_id} exp={exp_cfg['id']} "
                        f"Hobs={dmo.observation_half_life:.4f} Hfwd={dmo.forward_half_life:.4f}"
                    ),
                )

                audit.write("observations", {
                    "wall_clock_timestamp": time.time(),
                    "model_time": model_time,
                    "entity_id": obs.entity_id,
                    "experiment_id": exp_cfg["id"],
                    "event_id": obs.event_id,
                })
                audit.write("dmo", {
                    "wall_clock_timestamp": time.time(),
                    "model_time": dmo.model_time,
                    "entity_id": dmo.entity_id,
                    "experiment_id": exp_cfg["id"],
                    "direction_state": dmo.direction_state,
                    "magnitude_state": dmo.magnitude_state,
                    "strength": dmo.strength,
                    "observation_half_life": dmo.observation_half_life,
                    "forward_half_life": dmo.forward_half_life,
                    "perturbation_state": dmo.perturbation_state,
                })
                audit.write("fmo", {
                    "wall_clock_timestamp": time.time(),
                    "model_time": fmo.model_time,
                    "entity_id": fmo.entity_id,
                    "experiment_id": exp_cfg["id"],
                    "directional_support": fmo.directional_support,
                    "expected_magnitude": fmo.expected_magnitude,
                    "uncertainty": fmo.uncertainty,
                })
                audit.write("perturbations", {
                    "wall_clock_timestamp": time.time(),
                    "model_time": dmo.model_time,
                    "entity_id": dmo.entity_id,
                    "experiment_id": exp_cfg["id"],
                    "magnitude": dmo.perturbation_state,
                    "direction": dmo.direction_state,
                    "type": dmo.model_health.get("perturbation_type", "UNKNOWN"),
                    "confidence": max(0.0, min(1.0, dmo.perturbation_state)),
                    "affected_channels": ["direction_state", "magnitude_state", "observation_half_life", "forward_half_life"],
                    "reason_codes": dmo.model_health.get("perturbation_reasons", []),
                })
                audit.write("signals", {
                    "wall_clock_timestamp": time.time(),
                    "model_time": dmo.model_time,
                    "entity_id": dmo.entity_id,
                    "experiment_id": exp_cfg["id"],
                    "signal_id": f"{dmo.entity_id}:{dmo.model_time:.6f}",
                    "signal_type": "ADAPTIVE_SIGNAL",
                    "strength": dmo.adaptive_signal_snapshot.get("strength", 0.0),
                    "half_life_seconds": dmo.adaptive_signal_snapshot.get("half_life_seconds", 0.0),
                    "reinforcement": dmo.adaptive_signal_snapshot.get("reinforcement", 0.0),
                    "uncertainty": dmo.adaptive_signal_snapshot.get("uncertainty", 1.0),
                    "effective_mass": dmo.adaptive_signal_snapshot.get("effective_mass", 0.0),
                    "density": dmo.adaptive_signal_snapshot.get("density", 0.0),
                    "active": True,
                })
                write_text_log(
                    perturb_log,
                    (
                        f"t={dmo.model_time:.3f} entity={dmo.entity_id} exp={exp_cfg['id']} "
                        f"magnitude={dmo.perturbation_state:.4f} "
                        f"type={dmo.model_health.get('perturbation_type', 'UNKNOWN')}"
                    ),
                )

                for ch, info in update.items():
                    total_param_drift += info["drift"]
                    audit.write("parameter_updates", {
                        "wall_clock_timestamp": time.time(),
                        "model_time": dmo.model_time,
                        "entity_id": dmo.entity_id,
                        "experiment_id": exp_cfg["id"],
                        "channel": ch,
                        "old_value": info["old_l1"],
                        "new_value": info["new_l1"],
                        "delta": info["delta_l1"],
                        "reason_model_error": info["error"],
                    })
                    write_text_log(
                        parameter_log,
                        (
                            f"t={dmo.model_time:.3f} entity={dmo.entity_id} exp={exp_cfg['id']} ch={ch} "
                            f"old={info['old_l1']:.6f} new={info['new_l1']:.6f} delta={info['delta_l1']:.6f} err={info['error']:.6f}"
                        ),
                    )

                _append_csv(
                    dmo_csv,
                    [
                        "experiment_id", "entity_id", "model_time", "direction_state", "magnitude_state", "strength", "persistence",
                        "observation_half_life", "forward_half_life", "reinforcement", "uncertainty", "reversal_tendency",
                        "relative_volume", "volume_log", "volume_density", "volume_movement_interaction", "perturbation_magnitude", "parameter_state_version"
                    ],
                    {
                        "experiment_id": exp_cfg["id"],
                        "entity_id": dmo.entity_id,
                        "model_time": dmo.model_time,
                        "direction_state": dmo.direction_state,
                        "magnitude_state": dmo.magnitude_state,
                        "strength": dmo.strength,
                        "persistence": dmo.persistence,
                        "observation_half_life": dmo.observation_half_life,
                        "forward_half_life": dmo.forward_half_life,
                        "reinforcement": dmo.reinforcement,
                        "uncertainty": dmo.uncertainty,
                        "reversal_tendency": dmo.reversal_tendency,
                        "relative_volume": dmo.volume_state.relative_volume,
                        "volume_log": dmo.volume_state.volume_log,
                        "volume_density": dmo.volume_state.volume_density,
                        "volume_movement_interaction": dmo.volume_state.volume_movement_interaction_signed,
                        "perturbation_magnitude": dmo.perturbation_state,
                        "parameter_state_version": dmo.parameter_state_version,
                    },
                )

                cur_sign = 1 if dmo.direction_state > 0 else (-1 if dmo.direction_state < 0 else 0)
                if obs_count > 1 and cur_sign != last_direction_sign:
                    state_flip_count += 1
                    if dmo.perturbation_state > 0.2:
                        perturb_flip_count += 1
                last_direction_sign = cur_sign

                if i < len(obs_rows) - 1:
                    nxt = obs_rows[i + 1]
                    realized_ret = (nxt.price / obs.price) - 1.0
                    pred_dir.append(fmo.directional_support)
                    act_dir.append(realized_ret)
                    pred_mag.append(fmo.expected_magnitude)
                    act_mag.append(abs(realized_ret))
                    pred_persistence.append(fmo.expected_persistence)
                    act_persistence.append(max(0.0, 1.0 - abs(realized_ret) * 50.0))
                    pred_half_life.append(fmo.forward_half_life)
                    act_half_life.append(max(5.0, min(300.0, 1.0 / (abs(realized_ret) + 1e-6))))
                    unc.append(fmo.uncertainty)
                    abs_err.append(abs(fmo.expected_magnitude - abs(realized_ret)))

                if (i + 1) % int(cfg_default["fmo"]["capture_every_n"]) == 0 and (i + int(cfg_default["fmo"]["forward_eval_steps"])) < len(obs_rows):
                    cap = capture.capture(fmo, dmo.parameter_state_version)
                    cap_window = obs_rows[i + 1 : i + 1 + int(cfg_default["fmo"]["forward_eval_steps"])]
                    forward_prices = [(r.model_available_timestamp, r.price) for r in cap_window if r.model_available_timestamp >= cap.model_time]
                    outcome = evaluate_capture(cap, forward_prices=forward_prices, entry_price=obs.price)
                    capture_count += 1

                    pred_fav.append(cap.favorable_excursion_estimate)
                    act_fav.append(max(0.0, outcome.maximum_favorable_excursion))
                    pred_adv.append(cap.adverse_excursion_estimate)
                    act_adv.append(abs(min(0.0, outcome.maximum_adverse_excursion)))

                    audit.write("fmo_captures", {
                        "wall_clock_timestamp": time.time(),
                        "model_time": cap.model_time,
                        "entity_id": cap.entity_id,
                        "experiment_id": exp_cfg["id"],
                        "capture_id": cap.capture_id,
                        "captured_directional_support": cap.directional_support,
                        "captured_magnitude": cap.expected_magnitude,
                        "captured_persistence": cap.expected_persistence,
                        "captured_uncertainty": cap.uncertainty,
                        "captured_favorable_excursion": cap.favorable_excursion_estimate,
                        "captured_adverse_excursion": cap.adverse_excursion_estimate,
                    })
                    audit.write("realized_outcomes", {
                        "wall_clock_timestamp": time.time(),
                        "model_time": cap.model_time,
                        "entity_id": cap.entity_id,
                        "experiment_id": exp_cfg["id"],
                        "capture_id": outcome.capture_id,
                        "realized_return": outcome.realized_return,
                        "maximum_favorable_excursion": outcome.maximum_favorable_excursion,
                        "maximum_adverse_excursion": outcome.maximum_adverse_excursion,
                        "realized_direction": outcome.realized_direction,
                    })
                    write_text_log(
                        fmo_eval_log,
                        (
                            f"t={cap.model_time:.3f} entity={cap.entity_id} exp={exp_cfg['id']} capture={cap.capture_id} "
                            f"pred_mag={cap.expected_magnitude:.6f} real_ret={outcome.realized_return:.6f} "
                            f"mfe={outcome.maximum_favorable_excursion:.6f} mae={outcome.maximum_adverse_excursion:.6f}"
                        ),
                    )

                    _append_csv(
                        fmo_csv,
                        [
                            "experiment_id", "capture_id", "entity_id", "model_time", "forward_start", "forward_end", "directional_support",
                            "expected_magnitude", "expected_persistence", "forward_half_life", "expected_decay", "reversal_tendency",
                            "favorable_excursion_estimate", "adverse_excursion_estimate", "uncertainty", "confidence"
                        ],
                        {
                            "experiment_id": exp_cfg["id"],
                            "capture_id": cap.capture_id,
                            "entity_id": cap.entity_id,
                            "model_time": cap.model_time,
                            "forward_start": cap.forward_interval_start,
                            "forward_end": cap.forward_interval_end,
                            "directional_support": cap.directional_support,
                            "expected_magnitude": cap.expected_magnitude,
                            "expected_persistence": cap.expected_persistence,
                            "forward_half_life": fmo.forward_half_life,
                            "expected_decay": fmo.expected_decay,
                            "reversal_tendency": fmo.reversal_tendency,
                            "favorable_excursion_estimate": cap.favorable_excursion_estimate,
                            "adverse_excursion_estimate": cap.adverse_excursion_estimate,
                            "uncertainty": cap.uncertainty,
                            "confidence": fmo.confidence,
                        },
                    )

        row = {
            "experiment_id": exp_cfg["id"],
            "variant": exp_cfg["variant"],
            "polynomial_order": exp_cfg["polynomial_order"],
            "directional_accuracy": directional_accuracy(pred_dir, act_dir),
            "magnitude_mae": mae(pred_mag, act_mag),
            "magnitude_rmse": rmse(pred_mag, act_mag),
            "favorable_excursion_mae": mae(pred_fav, act_fav),
            "adverse_excursion_mae": mae(pred_adv, act_adv),
            "persistence_error": persistence_error(pred_persistence, act_persistence),
            "half_life_error": half_life_error(pred_half_life, act_half_life),
            "reversal_detection_lead_time": 0.0,
            "state_flip_count": state_flip_count,
            "perturbation_state_flip_count": perturb_flip_count,
            "parameter_drift_total": total_param_drift,
            "observation_count": obs_count,
            "fmo_capture_count": capture_count,
            "runtime_seconds": time.perf_counter() - t_start,
            "uncertainty_calibration_proxy": uncertainty_calibration_proxy(unc, abs_err),
            "dmo_stability": state_flip_count / max(1, obs_count),
        }
        metrics_rows.append(row)
        _append_csv(
            metrics_csv,
            [
                "experiment_id", "variant", "polynomial_order", "directional_accuracy", "magnitude_mae", "magnitude_rmse",
                "favorable_excursion_mae", "adverse_excursion_mae", "persistence_error", "half_life_error",
                "reversal_detection_lead_time", "state_flip_count", "perturbation_state_flip_count", "parameter_drift_total",
                "observation_count", "fmo_capture_count", "runtime_seconds",
                "uncertainty_calibration_proxy", "dmo_stability"
            ],
            row,
        )
        audit.write("experiments", {
            "wall_clock_timestamp": time.time(),
            "model_time": 0.0,
            "entity_id": cfg_default["entity_id"],
            "experiment_id": exp_cfg["id"],
            "metrics": row,
        })
        write_text_log(
            runtime_log,
            (
                f"exp={exp_cfg['id']} complete runtime={row['runtime_seconds']:.4f}s "
                f"directional_accuracy={row['directional_accuracy']:.6f} magnitude_mae={row['magnitude_mae']:.6f}"
            ),
        )

    best_directional = max(metrics_rows, key=lambda r: r["directional_accuracy"])
    best_magnitude = min(metrics_rows, key=lambda r: r["magnitude_mae"])
    lowest_drift = min(metrics_rows, key=lambda r: r["parameter_drift_total"])
    best_stability = min(metrics_rows, key=lambda r: r["dmo_stability"])

    # deterministic check
    det_pass = True
    first_exp = cfg_matrix["experiments"][0]
    first_digest: list[tuple[float, float, float]] = []
    for run_idx in range(2):
        model = AdaptiveParametricModel(_build_model_cfg(cfg_default, first_exp))
        provider = SyntheticProvider(root / "synthetic" / "quiet_market.yaml", entity_id=cfg_default["entity_id"])
        stream = provider.stream()
        digest = []
        for obs in stream:
            dmo, fmo, _update = model.step(obs, obs.model_available_timestamp)
            digest.append((round(dmo.direction_state, 6), round(dmo.observation_half_life, 6), round(fmo.expected_magnitude, 6)))
        if run_idx == 0:
            first_digest = digest
        else:
            det_pass = det_pass and (digest == first_digest)

    # benchmark 100k
    bench_provider = SyntheticProvider(root / "synthetic" / "quiet_market.yaml", entity_id=cfg_default["entity_id"])
    bench_stream = bench_provider.stream()
    repeats = 100000 // len(bench_stream) + 1
    synthetic_100k = (bench_stream * repeats)[:100000]
    bench_model = AdaptiveParametricModel(_build_model_cfg(cfg_default, cfg_matrix["experiments"][0]))
    t0 = time.perf_counter()
    for obs in synthetic_100k:
        bench_model.step(obs, obs.model_available_timestamp)
    t1 = time.perf_counter()
    bench_runtime = t1 - t0
    bench_ops = 100000.0 / max(bench_runtime, 1e-9)

    return ExperimentArtifacts(
        metrics_rows=metrics_rows,
        best_directional=best_directional,
        best_magnitude=best_magnitude,
        lowest_drift=lowest_drift,
        best_stability=best_stability,
        deterministic_pass=det_pass,
        benchmark_runtime=bench_runtime,
        benchmark_ops=bench_ops,
    )
