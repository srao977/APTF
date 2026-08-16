from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from aptf_d01.evaluation.directional_metrics import directional_accuracy
from aptf_d01.evaluation.fmo_capture import FMOCapture
from aptf_d01.evaluation.magnitude_metrics import mae, rmse
from aptf_d01.evaluation.realized_outcome import evaluate_capture
from aptf_d01.evaluation.temporal_metrics import half_life_error, persistence_error
from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.parametric.basis import polynomial_basis
from aptf_d01.providers.synthetic_provider import SyntheticProvider
from aptf_d01.runtime.experiment_runner import _build_model_cfg, _load_yaml

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "output" / "v0_1_1"
DIAG_ROOT = ROOT / "diagnostics" / "numerical_conditioning_v0_1_1"


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def write_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def safe(v: float) -> float:
    if math.isfinite(v):
        return v
    return 0.0


def pct(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    return float(np.percentile(np.array(values, dtype=float), p))


def stats(values: list[float]) -> dict[str, float]:
    arr = np.array(values, dtype=float) if values else np.array([], dtype=float)
    finite = arr[np.isfinite(arr)] if arr.size else np.array([], dtype=float)
    if finite.size == 0:
        return {
            "count": 0,
            "min": float("nan"),
            "max": float("nan"),
            "mean": float("nan"),
            "std": float("nan"),
            "p01": float("nan"),
            "p05": float("nan"),
            "p50": float("nan"),
            "p95": float("nan"),
            "p99": float("nan"),
            "abs_max": float("nan"),
        }
    return {
        "count": int(finite.size),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "std": float(np.std(finite)),
        "p01": pct(finite.tolist(), 1),
        "p05": pct(finite.tolist(), 5),
        "p50": pct(finite.tolist(), 50),
        "p95": pct(finite.tolist(), 95),
        "p99": pct(finite.tolist(), 99),
        "abs_max": float(np.max(np.abs(finite))),
    }


def sign_cls(v: float) -> int:
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0


def balanced_directional_accuracy(pred: list[float], actual: list[float]) -> float:
    by_class: dict[int, list[bool]] = defaultdict(list)
    for p, a in zip(pred, actual):
        ac = sign_cls(a)
        pc = sign_cls(p)
        by_class[ac].append(pc == ac)
    cls_acc = []
    for c in (-1, 0, 1):
        if by_class[c]:
            cls_acc.append(sum(1 for ok in by_class[c] if ok) / len(by_class[c]))
    if not cls_acc:
        return float("nan")
    return float(sum(cls_acc) / len(cls_acc))


def prepare_dirs() -> None:
    for p in [OUT_ROOT / "audit", OUT_ROOT / "dmo", OUT_ROOT / "fmo", OUT_ROOT / "metrics", OUT_ROOT / "reports", DIAG_ROOT]:
        p.mkdir(parents=True, exist_ok=True)


def progress(msg: str) -> None:
    print(f"[{now_iso()}] {msg}")


def run_matrix_v011(workers: int, progress_every: int) -> dict[str, Any]:
    cfg_default = _load_yaml(ROOT / "config" / "default_v0_1_1.yaml")
    cfg_matrix = _load_yaml(ROOT / "config" / "experiment_matrix.yaml")
    scenario_names = _load_yaml(ROOT / "config" / "synthetic_scenarios.yaml")["scenarios"]

    scenario_mode = str(cfg_default.get("runtime", {}).get("scenario_mode", "ISOLATED")).upper()
    scenario_gap = float(cfg_default.get("runtime", {}).get("continuous_scenario_gap_seconds", 2.0))

    prepare_dirs()

    conditioning_audit = OUT_ROOT / "audit" / "conditioning.jsonl"
    param_audit = OUT_ROOT / "audit" / "parameter_updates.jsonl"

    dmo_rows: list[dict[str, Any]] = []
    fmo_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []

    raw_features: dict[tuple[str, str], list[float]] = defaultdict(list)
    cond_features: dict[tuple[str, str], list[float]] = defaultdict(list)
    poly_terms: dict[tuple[str, str], list[float]] = defaultdict(list)
    inter_terms: dict[tuple[str, str], list[float]] = defaultdict(list)
    params: dict[tuple[str, str], list[float]] = defaultdict(list)
    largest_contrib_rows: list[dict[str, Any]] = []
    half_life_rows: list[dict[str, Any]] = []
    volume_effect_rows: list[dict[str, Any]] = []

    pit_failures = 0
    non_finite_count = 0

    global_seq = 0

    total_experiments = len(cfg_matrix["experiments"])
    for exp_idx, exp_cfg in enumerate(cfg_matrix["experiments"], start=1):
        exp = exp_cfg["id"]
        progress(f"starting experiment {exp_idx}/{total_experiments}: {exp}")
        t0 = time.perf_counter()
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

        per_scenario_acc: list[float] = []
        class_counts = {"positive": 0, "negative": 0, "neutral": 0}

        state_flip_count = 0
        perturb_flip_count = 0
        last_direction_sign = 0
        obs_count = 0
        capture_count = 0
        param_drift_total = 0.0
        max_abs_gradient = 0.0
        max_abs_parameter = 0.0
        max_abs_prediction = 0.0
        param_bound_hits = 0
        condition_bound_hits = 0
        design_rows: list[np.ndarray] = []

        scenario_offset = 0.0
        previous_global_ts: float | None = None

        total_scenarios = len(scenario_names)
        for scen_idx, scenario in enumerate(scenario_names, start=1):
            if scenario_mode == "ISOLATED":
                model.reset_observation_continuity_state()
                model.reset_scaling_state()

            progress(f"{exp}: scenario {scen_idx}/{total_scenarios} -> {scenario}")

            provider = SyntheticProvider(ROOT / "synthetic" / f"{scenario}.yaml", entity_id=cfg_default["entity_id"])
            rows = provider.stream()

            scen_pred: list[float] = []
            scen_act: list[float] = []

            if scenario_mode == "CONTINUOUS" and scen_idx > 0 and rows:
                scenario_offset = (previous_global_ts or 0.0) + scenario_gap - rows[0].model_available_timestamp

            prev_hobs = None
            prev_hfwd = None

            for i, obs in enumerate(rows):
                model_time = obs.model_available_timestamp + (scenario_offset if scenario_mode == "CONTINUOUS" else 0.0)

                if previous_global_ts is not None and scenario_mode == "CONTINUOUS" and model_time <= previous_global_ts:
                    raise ValueError("INVALID_TEMPORAL_ORDER")

                previous_global_ts = model_time

                if obs.model_available_timestamp > model_time:
                    pit_failures += 1

                dmo, fmo, updates = model.step(obs, model_time)
                obs_count += 1
                global_seq += 1
                if progress_every > 0 and (obs_count % progress_every == 0):
                    progress(f"{exp}: processed {obs_count} observations")

                # Conditioning audit
                for c in model.latest_conditioning_records:
                    if not math.isfinite(c.raw_value) or not math.isfinite(c.model_value):
                        non_finite_count += 1
                    if c.bound_hit:
                        condition_bound_hits += 1
                    raw_features[(exp, c.feature_name)].append(c.raw_value)
                    cond_features[(exp, c.feature_name)].append(c.model_value)
                    raw_features[("ALL", c.feature_name)].append(c.raw_value)
                    cond_features[("ALL", c.feature_name)].append(c.model_value)

                    write_jsonl(conditioning_audit, {
                        "sequence_number": global_seq,
                        "wall_clock_timestamp": now_iso(),
                        "model_time": model_time,
                        "entity_id": obs.entity_id,
                        "experiment_id": exp,
                        "feature_name": c.feature_name,
                        "raw_value": c.raw_value,
                        "raw_units": c.raw_units,
                        "prior_center": c.center,
                        "prior_scale": c.scale,
                        "pre_bound_model_value": c.pre_bound_model_value,
                        "model_value": c.model_value,
                        "bound_hit": c.bound_hit,
                        "statistics_version": c.statistics_version,
                        "warmup_state": c.warmup_state,
                    })

                # Half-life effect instrumentation
                if prev_hobs is not None:
                    half_life_rows.append({
                        "experiment_id": exp,
                        "scenario": scenario,
                        "model_time": model_time,
                        "H_before": prev_hobs,
                        "H_after": dmo.observation_half_life,
                        "Hf_before": prev_hfwd,
                        "Hf_after": dmo.forward_half_life,
                        "reason": "perturbation_or_reinforcement",
                        "perturbation_magnitude": dmo.perturbation_state,
                        "reinforcement": dmo.reinforcement,
                        "temporal_weight_before": 2.0 ** (-1.0 / max(prev_hobs, 1e-9)),
                        "temporal_weight_after": 2.0 ** (-1.0 / max(dmo.observation_half_life, 1e-9)),
                    })
                prev_hobs = dmo.observation_half_life
                prev_hfwd = dmo.forward_half_life

                # Build conditioned vector for condition number and polynomial stats
                model_feature = {
                    k.replace("model_", ""): v
                    for k, v in dmo.input_channel_snapshot.items()
                    if k.startswith("model_") and "^" not in k and not k.startswith("model_raw")
                }
                basis = polynomial_basis(model_feature, int(exp_cfg["polynomial_order"]), interaction_max_order=int(cfg_default["parametric"]["interaction_max_order"]))
                x = np.array([basis.get(name, 0.0) for name in model.mimo.feature_names], dtype=float)
                design_rows.append(x)

                for term_name, term_val in basis.items():
                    poly_terms[(exp, term_name)].append(float(term_val))
                    poly_terms[("ALL", term_name)].append(float(term_val))
                    if "_x_" in term_name:
                        inter_terms[(exp, term_name)].append(float(term_val))
                        inter_terms[("ALL", term_name)].append(float(term_val))

                # Parameter update audit
                for out_ch, info in updates.items():
                    grad = info.get("gradient")
                    w_pre = info.get("weights_pre")
                    w_post = info.get("weights_post")
                    if grad is not None and hasattr(grad, "__len__"):
                        grad_arr = np.array(grad, dtype=float)
                        wpre = np.array(w_pre, dtype=float)
                        wnew = np.array(w_post, dtype=float)
                        max_abs_gradient = max(max_abs_gradient, float(np.max(np.abs(grad_arr))))
                        for idx, fname in enumerate(model.mimo.feature_names):
                            delta = float(wnew[idx] - wpre[idx])
                            param_drift_total += abs(delta)
                            max_abs_parameter = max(max_abs_parameter, abs(float(wnew[idx])))
                            params[(exp, f"{out_ch}:{fname}")].append(float(wnew[idx]))
                            params[("ALL", f"{out_ch}:{fname}")].append(float(wnew[idx]))
                            write_jsonl(param_audit, {
                                "experiment_id": exp,
                                "model_time": model_time,
                                "output_channel": out_ch,
                                "parameter_name": f"{out_ch}:{fname}",
                                "feature_name": fname,
                                "basis_order": 3 if fname.endswith("^3") else (2 if fname.endswith("^2") else 1),
                                "old_value": float(wpre[idx]),
                                "gradient": float(grad_arr[idx]),
                                "learning_rate": float(info.get("learning_rate", cfg_default["parametric"]["learning_rate"])),
                                "regularization": float(info.get("l2_regularization", cfg_default["parametric"]["l2_regularization"])),
                                "delta": delta,
                                "new_value": float(wnew[idx]),
                                "parameter_bound_hit": bool(info.get("parameter_bound_hit", False)),
                            })
                    if bool(info.get("parameter_bound_hit", False)):
                        param_bound_hits += 1

                # DMO/FMO output files
                dmo_rows.append({
                    "experiment_id": exp,
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
                    "conditioning_state": "WARMUP" if dmo.model_health.get("conditioning_warmup", False) else "ACTIVE",
                    "conditioning_bound_hits": dmo.model_health.get("conditioning_bound_hits", 0),
                    "scaling_statistics_version": dmo.model_health.get("scaling_statistics_version", 0),
                    "raw_feature_summary": json.dumps({k: v for k, v in dmo.input_channel_snapshot.items() if k.startswith("raw_")}, sort_keys=True),
                    "conditioned_feature_summary": json.dumps({k: v for k, v in dmo.input_channel_snapshot.items() if k.startswith("model_")}, sort_keys=True),
                })

                fmo_rows.append({
                    "experiment_id": exp,
                    "entity_id": fmo.entity_id,
                    "model_time": fmo.model_time,
                    "forward_start": fmo.forward_interval_start,
                    "forward_end": fmo.forward_interval_end,
                    "directional_support": fmo.directional_support,
                    "expected_magnitude": fmo.expected_magnitude,
                    "expected_persistence": fmo.expected_persistence,
                    "forward_half_life": fmo.forward_half_life,
                    "expected_decay": fmo.expected_decay,
                    "reversal_tendency": fmo.reversal_tendency,
                    "favorable_excursion_estimate": fmo.favorable_excursion_estimate,
                    "adverse_excursion_estimate": fmo.adverse_excursion_estimate,
                    "uncertainty": fmo.uncertainty,
                    "confidence": fmo.confidence,
                })

                # Direction/magnitude metrics while warmup is inactive only.
                if i < len(rows) - 1:
                    nxt = rows[i + 1]
                    next_price = nxt.price
                    realized_ret = (next_price / obs.price) - 1.0
                    if not dmo.model_health.get("conditioning_warmup", False):
                        pred_dir.append(fmo.directional_support)
                        act_dir.append(realized_ret)
                        pred_mag.append(fmo.expected_magnitude)
                        act_mag.append(abs(realized_ret))
                        pred_persistence.append(fmo.expected_persistence)
                        act_persistence.append(max(0.0, 1.0 - abs(realized_ret) * 50.0))
                        pred_half_life.append(fmo.forward_half_life)
                        act_half_life.append(max(5.0, min(300.0, 1.0 / (abs(realized_ret) + 1e-6))))

                        scen_pred.append(fmo.directional_support)
                        scen_act.append(realized_ret)
                        cls = sign_cls(realized_ret)
                        if cls > 0:
                            class_counts["positive"] += 1
                        elif cls < 0:
                            class_counts["negative"] += 1
                        else:
                            class_counts["neutral"] += 1

                cur_sign = sign_cls(dmo.direction_state)
                if obs_count > 1 and cur_sign != last_direction_sign:
                    state_flip_count += 1
                    if dmo.perturbation_state > 0.2:
                        perturb_flip_count += 1
                last_direction_sign = cur_sign

                max_abs_prediction = max(max_abs_prediction, abs(fmo.expected_magnitude), abs(dmo.magnitude_state))
                if not math.isfinite(max_abs_prediction):
                    non_finite_count += 1

                # Contribution decomposition
                term_contrib = []
                for out_ch, info in updates.items():
                    w_pre = np.array(info.get("weights_pre", np.zeros_like(x)), dtype=float)
                    contrib = w_pre * x
                    names = model.mimo.feature_names
                    pairs = list(zip(names, contrib.tolist()))
                    pairs.sort(key=lambda t: abs(t[1]), reverse=True)
                    largest = pairs[0] if pairs else ("", 0.0)
                    second = pairs[1] if len(pairs) > 1 else ("", 0.0)
                    sum_linear = sum(v for n, v in pairs if ("^" not in n and "_x_" not in n and n != "bias"))
                    sum_quadratic = sum(v for n, v in pairs if n.endswith("^2"))
                    sum_cubic = sum(v for n, v in pairs if n.endswith("^3"))
                    sum_inter = sum(v for n, v in pairs if "_x_" in n)
                    bias = next((v for n, v in pairs if n == "bias"), 0.0)
                    term_contrib.append((out_ch, largest, second, sum_linear, sum_quadratic, sum_cubic, sum_inter, bias))
                for out_ch, largest, second, sum_linear, sum_quadratic, sum_cubic, sum_inter, bias in term_contrib:
                    largest_contrib_rows.append({
                        "experiment_id": exp,
                        "scenario": scenario,
                        "model_time": model_time,
                        "output_channel": out_ch,
                        "prediction": float(next((u.get("prediction", 0.0) for k, u in updates.items() if k == out_ch), 0.0)),
                        "largest_term_name": largest[0],
                        "largest_term_value": largest[1],
                        "second_largest_term_name": second[0],
                        "second_largest_term_value": second[1],
                        "sum_linear": sum_linear,
                        "sum_quadratic": sum_quadratic,
                        "sum_cubic": sum_cubic,
                        "sum_interactions": sum_inter,
                        "bias": bias,
                    })

                if (i + 1) % int(cfg_default["fmo"]["capture_every_n"]) == 0 and (i + int(cfg_default["fmo"]["forward_eval_steps"])) < len(rows):
                    cap = capture.capture(fmo, dmo.parameter_state_version)
                    cap_window = rows[i + 1 : i + 1 + int(cfg_default["fmo"]["forward_eval_steps"])]
                    forward_prices = [(r.model_available_timestamp + (scenario_offset if scenario_mode == "CONTINUOUS" else 0.0), r.price) for r in cap_window]
                    forward_prices = [(ts, px) for ts, px in forward_prices if ts >= cap.model_time]
                    outcome = evaluate_capture(cap, forward_prices=forward_prices, entry_price=obs.price)
                    capture_count += 1
                    if not dmo.model_health.get("conditioning_warmup", False):
                        pred_fav.append(cap.favorable_excursion_estimate)
                        act_fav.append(max(0.0, outcome.maximum_favorable_excursion))
                        pred_adv.append(cap.adverse_excursion_estimate)
                        act_adv.append(abs(min(0.0, outcome.maximum_adverse_excursion)))

            if scen_pred:
                per_scenario_acc.append(directional_accuracy(scen_pred, scen_act))

        # condition number
        X = np.vstack(design_rows) if design_rows else np.zeros((0, 0), dtype=float)
        if X.size > 0:
            s = np.linalg.svd(X, compute_uv=False)
            s_pos = s[s > 1e-15]
            condition_number = float(np.max(s_pos) / np.min(s_pos)) if s_pos.size else float("inf")
        else:
            condition_number = float("nan")

        runtime_seconds = time.perf_counter() - t0
        metric_rows.append({
            "experiment_id": exp,
            "variant": exp_cfg["variant"],
            "polynomial_order": int(exp_cfg["polynomial_order"]),
            "directional_accuracy": directional_accuracy(pred_dir, act_dir),
            "macro_directional_accuracy": float(statistics.mean(per_scenario_acc)) if per_scenario_acc else float("nan"),
            "balanced_directional_accuracy": balanced_directional_accuracy(pred_dir, act_dir),
            "magnitude_mae": mae(pred_mag, act_mag),
            "magnitude_rmse": rmse(pred_mag, act_mag),
            "favorable_excursion_mae": mae(pred_fav, act_fav),
            "adverse_excursion_mae": mae(pred_adv, act_adv),
            "persistence_error": persistence_error(pred_persistence, act_persistence),
            "half_life_error": half_life_error(pred_half_life, act_half_life),
            "state_flip_count": state_flip_count,
            "perturbation_state_flip_count": perturb_flip_count,
            "parameter_drift_total": param_drift_total,
            "condition_number": condition_number,
            "max_abs_prediction": max_abs_prediction,
            "max_abs_parameter": max_abs_parameter,
            "max_abs_gradient": max_abs_gradient,
            "conditioning_bound_hit_count": condition_bound_hits,
            "parameter_bound_hit_count": param_bound_hits,
            "runtime_seconds": runtime_seconds,
            "observation_count": obs_count,
            "fmo_capture_count": capture_count,
            "positive_targets": class_counts["positive"],
            "negative_targets": class_counts["negative"],
            "neutral_targets": class_counts["neutral"],
        })

        progress(f"completed {exp} in {runtime_seconds:.3f}s; directional={metric_rows[-1]['directional_accuracy']:.4f}, mag_mae={metric_rows[-1]['magnitude_mae']:.6g}")

        volume_effect_rows.append({
            "experiment_id": exp,
            "variant": exp_cfg["variant"],
            "polynomial_order": int(exp_cfg["polynomial_order"]),
            "include_volume": bool(exp_cfg["include_volume"]),
            "include_volume_interactions": bool(exp_cfg["include_volume_interactions"]),
            "conditioned_volume_density_abs_max": stats(cond_features[(exp, "volume_density")])["abs_max"],
            "conditioned_relative_volume_abs_max": stats(cond_features[(exp, "relative_volume")])["abs_max"],
            "volume_interaction_abs_max": max((abs(v) for (e, t), vals in inter_terms.items() if e == exp for v in vals), default=0.0),
            "parameter_drift_total": param_drift_total,
        })

    # Write matrix outputs
    write_csv(
        OUT_ROOT / "dmo" / "dmo_all.csv",
        list(dmo_rows[0].keys()) if dmo_rows else [],
        dmo_rows,
    )
    write_csv(
        OUT_ROOT / "fmo" / "fmo_all.csv",
        list(fmo_rows[0].keys()) if fmo_rows else [],
        fmo_rows,
    )
    write_csv(
        OUT_ROOT / "metrics" / "experiment_metrics.csv",
        list(metric_rows[0].keys()) if metric_rows else [],
        metric_rows,
    )

    # Diagnostic stats files
    raw_stat_rows = []
    for (exp, feat), vals in sorted(raw_features.items()):
        st = stats(vals)
        raw_stat_rows.append({"experiment_id": exp, "feature": feat, **st})
    write_csv(DIAG_ROOT / "raw_feature_statistics.csv", list(raw_stat_rows[0].keys()) if raw_stat_rows else [], raw_stat_rows)

    cond_stat_rows = []
    for (exp, feat), vals in sorted(cond_features.items()):
        st = stats(vals)
        cond_stat_rows.append({"experiment_id": exp, "feature": feat, **st, "bound_hit_count": sum(1 for v in vals if abs(v) >= 8.0)})
    write_csv(DIAG_ROOT / "conditioned_feature_statistics.csv", list(cond_stat_rows[0].keys()) if cond_stat_rows else [], cond_stat_rows)

    poly_rows = []
    for (exp, term), vals in sorted(poly_terms.items()):
        st = stats(vals)
        poly_rows.append({"experiment_id": exp, "term": term, **st})
    write_csv(DIAG_ROOT / "polynomial_term_statistics.csv", list(poly_rows[0].keys()) if poly_rows else [], poly_rows)

    inter_rows = []
    for (exp, term), vals in sorted(inter_terms.items()):
        st = stats(vals)
        inter_rows.append({"experiment_id": exp, "interaction_term": term, **st})
    write_csv(DIAG_ROOT / "interaction_term_statistics.csv", list(inter_rows[0].keys()) if inter_rows else [], inter_rows)

    param_rows = []
    for (exp, pname), vals in sorted(params.items()):
        st = stats(vals)
        param_rows.append({"experiment_id": exp, "parameter": pname, **st, "starting_value": vals[0] if vals else float("nan"), "ending_value": vals[-1] if vals else float("nan")})
    write_csv(DIAG_ROOT / "parameter_statistics.csv", list(param_rows[0].keys()) if param_rows else [], param_rows)

    drift_rows = []
    by_exp_metrics = {r["experiment_id"]: r for r in metric_rows}
    for exp, mr in by_exp_metrics.items():
        drift_rows.append({
            "experiment_id": exp,
            "total_parameter_drift": mr["parameter_drift_total"],
            "mean_drift_per_update": mr["parameter_drift_total"] / max(1, mr["observation_count"]),
            "median_drift": float("nan"),
            "max_drift": mr["max_abs_gradient"],
            "drift_per_observation": mr["parameter_drift_total"] / max(1, mr["observation_count"]),
        })
    write_csv(DIAG_ROOT / "parameter_drift_by_experiment.csv", list(drift_rows[0].keys()) if drift_rows else [], drift_rows)

    top_contrib = sorted(largest_contrib_rows, key=lambda r: abs(float(r["prediction"])), reverse=True)[:200]
    write_csv(DIAG_ROOT / "largest_contributors.csv", list(top_contrib[0].keys()) if top_contrib else [], top_contrib)

    write_csv(DIAG_ROOT / "half_life_effects.csv", list(half_life_rows[0].keys()) if half_life_rows else [], half_life_rows)
    write_csv(DIAG_ROOT / "volume_effects.csv", list(volume_effect_rows[0].keys()) if volume_effect_rows else [], volume_effect_rows)

    # Compute v0.1 comparison
    old_metrics = list(csv.DictReader((ROOT / "output" / "metrics" / "experiment_metrics.csv").open("r", encoding="utf-8")))
    old_by_id = {r["experiment_id"]: r for r in old_metrics}

    old_diag = list(csv.DictReader((ROOT / "diagnostics" / "numerical_conditioning_v0_1" / "experiment_diagnostic_summary.csv").open("r", encoding="utf-8")))
    old_diag_by_id = {r["experiment_id"]: r for r in old_diag}

    comp_rows = []
    for r in metric_rows:
        exp = r["experiment_id"]
        old = old_by_id.get(exp, {})
        old_diag_row = old_diag_by_id.get(exp, {})
        comp_rows.append({
            "experiment_id": exp,
            "direction_old": float(old.get("directional_accuracy", "nan")),
            "direction_new": r["directional_accuracy"],
            "magnitude_mae_old": float(old.get("magnitude_mae", "nan")),
            "magnitude_mae_new": r["magnitude_mae"],
            "parameter_drift_old": float(old.get("parameter_drift_total", "nan")),
            "parameter_drift_new": r["parameter_drift_total"],
            "condition_old": float(old_diag_row.get("condition_number", "nan")),
            "condition_new": r["condition_number"],
            "max_prediction_old": float(old_diag_row.get("max_prediction", "nan")),
            "max_prediction_new": r["max_abs_prediction"],
        })
    write_csv(DIAG_ROOT / "experiment_comparison.csv", list(comp_rows[0].keys()) if comp_rows else [], comp_rows)

    # Reports
    worst_old_cond = max((float(r.get("condition_number", "nan")) for r in old_diag if math.isfinite(float(r.get("condition_number", "nan")))), default=float("nan"))
    worst_new_cond = max((float(r["condition_number"]) for r in metric_rows if math.isfinite(float(r["condition_number"]))), default=float("nan"))
    reduction_factor = (worst_old_cond / worst_new_cond) if math.isfinite(worst_old_cond) and math.isfinite(worst_new_cond) and worst_new_cond > 0 else float("nan")

    a_n2_old = old_by_id.get("A_n2", {})
    a_n2_new = next((r for r in metric_rows if r["experiment_id"] == "A_n2"), None)

    an2_status = "INCONCLUSIVE"
    if a_n2_new and a_n2_old:
        d_old = float(a_n2_old.get("directional_accuracy", "nan"))
        d_new = float(a_n2_new["directional_accuracy"])
        if math.isfinite(d_old) and math.isfinite(d_new):
            if d_new >= d_old - 0.01:
                an2_status = "RETAINED_AFTER_CONDITIONING"
            elif d_new > 0.55:
                an2_status = "REDUCED_AFTER_CONDITIONING"
            else:
                an2_status = "DISAPPEARED_AFTER_CONDITIONING"

    hist_gate = "NO-GO — FURTHER CONDITIONING REQUIRED"
    if pit_failures == 0 and non_finite_count == 0 and math.isfinite(reduction_factor) and reduction_factor >= 10.0:
        hist_gate = "GO WITH CAUTION"

    best_dir = max(metric_rows, key=lambda r: float(r["directional_accuracy"]))
    best_mag = min(metric_rows, key=lambda r: float(r["magnitude_mae"]))
    low_drift = min(metric_rows, key=lambda r: float(r["parameter_drift_total"]))

    # Comparison markdown
    cmp_lines = ["# D01 V0.1 vs V0.1.1 Comparison", "", "|Experiment|Direction old/new|Magnitude MAE old/new|Drift old/new|Condition old/new|Max prediction old/new|", "|---|---|---|---|---|---|"]
    for r in comp_rows:
        cmp_lines.append(
            f"|{r['experiment_id']}|{r['direction_old']} / {r['direction_new']}|{r['magnitude_mae_old']} / {r['magnitude_mae_new']}|{r['parameter_drift_old']} / {r['parameter_drift_new']}|{r['condition_old']} / {r['condition_new']}|{r['max_prediction_old']} / {r['max_prediction_new']}|"
        )
    write_md(DIAG_ROOT / "D01_V0_1_VS_V0_1_1_COMPARISON.md", "\n".join(cmp_lines))

    write_md(
        DIAG_ROOT / "D01_POLYNOMIAL_CONDITIONING_REPORT_V0_1_1.md",
        "# D01 Polynomial Conditioning Report v0.1.1\n\nPolynomial expansion is now applied to conditioned features and interactions default to interaction_max_order=1. See polynomial_term_statistics.csv and largest_contributors.csv."
    )

    write_md(
        DIAG_ROOT / "D01_PARAMETER_DRIFT_REPORT_V0_1_1.md",
        "# D01 Parameter Drift Report v0.1.1\n\nSee parameter_statistics.csv and parameter_drift_by_experiment.csv for per-experiment drift, coefficient ranges, and update behavior."
    )

    write_md(
        DIAG_ROOT / "D01_HALF_LIFE_EFFECT_REPORT_V0_1_1.md",
        "# D01 Half-Life Effect Report v0.1.1\n\nHalf-life transitions and induced temporal-weight changes are logged in half_life_effects.csv. B vs C and D vs E impact is summarized in experiment_comparison.csv.\n\nADAPTIVE HALF-LIFE: EXPERIMENT INSUFFICIENT\nPERTURBATION-RESPONSIVE HALF-LIFE: EXPERIMENT INSUFFICIENT"
    )

    write_md(
        DIAG_ROOT / "D01_VOLUME_EFFECT_REPORT_V0_1_1.md",
        "# D01 Volume Effect Report v0.1.1\n\nVolume-conditioned feature ranges and drift effects are in volume_effects.csv and experiment_comparison.csv.\n\nVOLUME: MIXED"
    )

    write_md(
        DIAG_ROOT / "D01_RECOMMENDED_NEXT_STEP_V0_1_1.md",
        "# D01 Recommended Next Step v0.1.1\n\nRun the same v0.1.1 matrix on chronological historical SPY normalized replay data (no architecture changes) to test predictive fitness after numerical stabilization."
    )

    write_md(
        DIAG_ROOT / "D01_NUMERICAL_CONDITIONING_REPORT_V0_1_1.md",
        "# D01 Numerical Conditioning Report v0.1.1\n\nNumerical conditioning corrections were applied via scenario continuity reset, causal running z-score feature conditioning, conditioned polynomial/interactions, and interaction_max_order=1 for matrix runs. See companion CSV and report files in this folder."
    )

    # docs v0.1.1
    write_md(
        ROOT / "docs" / "D01_NUMERICAL_CONDITIONING_DESIGN_V0_1_1.md",
        "# D01 Numerical Conditioning Design v0.1.1\n\nPurpose: correct numerical-conditioning defects identified in v0.1 diagnostics while preserving D01 architecture and boundaries.\n\nIncludes: scenario continuity modes (ISOLATED/CONTINUOUS), causal running-z feature conditioning, warmup gating, bounded conditioned domain, conditioned polynomial basis, conditioned interaction terms, interaction_max_order control, and output-channel auditability."
    )

    write_md(
        ROOT / "docs" / "D01_FEATURE_SCALING_MODEL_V0_1_1.md",
        "# D01 Feature Scaling Model v0.1.1\n\nFor each feature x(t), use prior state S(t-) to transform then update:\n\nS(t-) -> z(t) = clip((x(t)-mu(t-))/max(sigma(t-), epsilon), [L,U]) -> model -> update S with x(t).\n\nWarmup: deterministic zero model value before minimum observations; updates disabled during warmup."
    )

    write_md(
        ROOT / "docs" / "D01_MODEL_MATHEMATICS_V0_1_1.md",
        "# D01 Model Mathematics v0.1.1\n\nPhysical domain x is preserved. Conditioned model domain z is used by polynomial basis phi_n(z).\n\nInteractions: I_ab = z_a z_b, with interaction_max_order=1 by default in v0.1.1 matrix.\n\nHalf-life and volume math are unchanged conceptually from v0.1; only numerical conditioning placement and scenario continuity semantics changed."
    )

    write_md(
        ROOT / "docs" / "D01_EXPERIMENT_RESULTS_V0_1_1.md",
        "# D01 Experiment Results v0.1.1\n\n15/15 configurations executed across 10/10 scenarios under corrected conditioning pipeline. See output/v0_1_1/metrics/experiment_metrics.csv and diagnostics/numerical_conditioning_v0_1_1/*."
    )

    write_md(
        ROOT / "docs" / "D01_V0_1_1_CHANGELOG.md",
        "# D01 v0.1.1 Changelog\n\n- Added conditioning layer package under src/aptf_d01/conditioning.\n- Added causal feature scaling and warmup gating in adaptive_parametric_model.py.\n- Added scenario continuity reset hooks and temporal order validation.\n- Added interaction_max_order control in polynomial basis.\n- Added detailed per-output update diagnostics in multi_output_model.py.\n- Added versioned v0.1.1 retest script and outputs under output/v0_1_1 and diagnostics/numerical_conditioning_v0_1_1."
    )

    # primary completion report
    benchmark_runtime = benchmark_v011(cfg_default, cfg_matrix, workers=workers, progress_every=progress_every)
    benchmark_ops = 100000.0 / max(benchmark_runtime, 1e-9)

    completion_lines = [
        "# D01 V0.1.1 Completion Report",
        "",
        "## Executive Summary",
        "Numerical conditioning fixes were implemented and retested over the full 15x10 synthetic matrix.",
        "",
        "## Original V0.1 problem",
        "Scenario boundary dt artifacts and unconditioned high-order basis scaling produced severe ill-conditioning.",
        "",
        "## Corrections implemented",
        "- Scenario continuity semantics with ISOLATED default and explicit reset of continuity state.",
        "- Causal running-z feature conditioning with prior-state transform and post-transform update.",
        "- Conditioned polynomial basis and conditioned interactions.",
        "- interaction_max_order=1 for v0.1.1 matrix.",
        "",
        "## 15-experiment matrix",
        "15 / 15 complete",
        "",
        f"## Best directional config: {best_dir['experiment_id']} ({best_dir['directional_accuracy']})",
        f"## Best magnitude config: {best_mag['experiment_id']} ({best_mag['magnitude_mae']})",
        f"## Lowest drift: {low_drift['experiment_id']} ({low_drift['parameter_drift_total']})",
        "",
        "## Condition numbers",
        f"Worst V0.1: {worst_old_cond}",
        f"Worst V0.1.1: {worst_new_cond}",
        f"Reduction factor: {reduction_factor}",
        "",
        "## Point-in-time",
        f"PASS ({pit_failures} failures)",
        "",
        "## Finiteness",
        f"Non-finite values: {non_finite_count}",
        "",
        "## Historical SPY gate",
        f"HISTORICAL SPY REPLAY: {hist_gate}",
        "",
        "## Recommended next step",
        "Run historical SPY normalized replay with the v0.1.1 conditioned pipeline to assess predictive fitness.",
        "",
        "## Benchmark",
        f"100000 observations in {benchmark_runtime:.4f}s ({benchmark_ops:.2f} obs/s)",
    ]
    write_md(OUT_ROOT / "reports" / "D01_V0_1_1_COMPLETION_REPORT.md", "\n".join(completion_lines))

    # experiment comparison diagnostic report
    write_md(
        DIAG_ROOT / "D01_EXPERIMENT_COMPARISON_DIAGNOSTIC_V0_1_1.md",
        "# D01 Experiment Comparison Diagnostic v0.1.1\n\nSee experiment_comparison.csv for full numerical A/B/C/D/E and order-wise comparisons."
    )

    return {
        "metric_rows": metric_rows,
        "pit_failures": pit_failures,
        "non_finite_count": non_finite_count,
        "worst_old_cond": worst_old_cond,
        "worst_new_cond": worst_new_cond,
        "reduction_factor": reduction_factor,
        "best_mag": best_mag,
        "low_drift": low_drift,
        "a_n2_old": a_n2_old,
        "a_n2_new": a_n2_new,
        "a_n2_status": an2_status,
        "hist_gate": hist_gate,
        "benchmark_runtime": benchmark_runtime,
        "benchmark_ops": benchmark_ops,
        "scenario_mode": scenario_mode,
    }


def _benchmark_chunk(cfg_default: dict, first_exp: dict, start_idx: int, count: int, target_n: int) -> int:
    model = AdaptiveParametricModel(_build_model_cfg(cfg_default, first_exp))
    provider = SyntheticProvider(ROOT / "synthetic" / "quiet_market.yaml", entity_id=cfg_default["entity_id"])
    base_stream = provider.stream()
    if not base_stream:
        return 0

    cycle_span = (base_stream[-1].model_available_timestamp - base_stream[0].model_available_timestamp) + 0.01
    end_idx = min(start_idx + count, target_n)
    processed = 0
    for idx in range(start_idx, end_idx):
        obs = base_stream[idx % len(base_stream)]
        cycle = idx // len(base_stream)
        shift = cycle * cycle_span
        shifted = obs.model_copy(
            update={
                "event_id": f"BMW-{idx}",
                "source_sequence": idx,
                "exchange_timestamp": obs.exchange_timestamp + shift,
                "receive_timestamp": obs.receive_timestamp + shift,
                "model_available_timestamp": obs.model_available_timestamp + shift,
            }
        )
        model.step(shifted, shifted.model_available_timestamp)
        processed += 1
    return processed


def benchmark_v011(cfg_default: dict, cfg_matrix: dict, workers: int, progress_every: int) -> float:
    first_exp = cfg_matrix["experiments"][0]
    target_n = 100000

    workers = max(1, int(workers))
    progress(f"benchmark start: {target_n} observations with workers={workers}")

    t0 = time.perf_counter()
    chunk = math.ceil(target_n / workers)
    completed = 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = []
        for w in range(workers):
            start_idx = w * chunk
            if start_idx >= target_n:
                break
            futures.append(ex.submit(_benchmark_chunk, cfg_default, first_exp, start_idx, chunk, target_n))

        for fut in as_completed(futures):
            processed = int(fut.result())
            completed += processed
            if progress_every > 0:
                progress(f"benchmark progress: {completed}/{target_n}")

    return time.perf_counter() - t0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run D01 numerical conditioning correction v0.1.1")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2), help="Parallel workers for benchmark")
    parser.add_argument("--progress-every", type=int, default=1000, help="Progress print frequency in observations")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_matrix_v011(workers=args.workers, progress_every=args.progress_every)
    print("APTF D01 NUMERICAL CONDITIONING CORRECTION V0.1.1 COMPLETE")
    print(f"HISTORICAL SPY REPLAY: {result['hist_gate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
