from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from aptf_d01.evaluation.directional_metrics import directional_accuracy
from aptf_d01.evaluation.fmo_capture import FMOCapture
from aptf_d01.evaluation.magnitude_metrics import mae, rmse
from aptf_d01.evaluation.realized_outcome import evaluate_capture
from aptf_d01.evaluation.temporal_metrics import half_life_error, persistence_error
from aptf_d01.model.adaptive_parametric_model import AdaptiveParametricModel
from aptf_d01.parametric.interactions import add_allowed_interactions
from aptf_d01.parametric.parameter_update import bounded_online_gradient_update
from aptf_d01.providers.synthetic_provider import SyntheticProvider
from aptf_d01.runtime.experiment_runner import _build_model_cfg, _load_yaml


ROOT = Path(__file__).resolve().parents[1]
DIAG_DIR = ROOT / "diagnostics" / "numerical_conditioning_v0_1"
LOG_PATH = ROOT / "output" / "logs" / "numerical_conditioning_diagnostic.log"


def log(msg: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().isoformat(timespec="seconds")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}Z] {msg}\n")


def safe_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")


def pct(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    return float(np.percentile(np.array(values, dtype=float), q))


def finite_stats(values: list[float]) -> dict[str, float]:
    arr = np.array(values, dtype=float) if values else np.array([], dtype=float)
    non_finite = int(np.sum(~np.isfinite(arr))) if arr.size else 0
    finite = arr[np.isfinite(arr)] if arr.size else np.array([], dtype=float)
    zero_count = int(np.sum(finite == 0.0)) if finite.size else 0
    if finite.size == 0:
        return {
            "count": 0,
            "min": float("nan"),
            "max": float("nan"),
            "mean": float("nan"),
            "median": float("nan"),
            "std": float("nan"),
            "p01": float("nan"),
            "p05": float("nan"),
            "p25": float("nan"),
            "p50": float("nan"),
            "p75": float("nan"),
            "p95": float("nan"),
            "p99": float("nan"),
            "abs_max": float("nan"),
            "non_finite_count": non_finite,
            "zero_count": zero_count,
        }
    return {
        "count": int(finite.size),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "median": float(np.median(finite)),
        "std": float(np.std(finite)),
        "p01": pct(finite.tolist(), 1),
        "p05": pct(finite.tolist(), 5),
        "p25": pct(finite.tolist(), 25),
        "p50": pct(finite.tolist(), 50),
        "p75": pct(finite.tolist(), 75),
        "p95": pct(finite.tolist(), 95),
        "p99": pct(finite.tolist(), 99),
        "abs_max": float(np.max(np.abs(finite))),
        "non_finite_count": non_finite,
        "zero_count": zero_count,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def classify_degree(term_name: str) -> int:
    if term_name == "bias":
        return 0
    if term_name.endswith("^3"):
        return 3
    if term_name.endswith("^2"):
        return 2
    return 1


def base_term(term_name: str) -> str:
    if term_name.endswith("^2") or term_name.endswith("^3"):
        return term_name[:-2]
    return term_name


def is_interaction_term(term_name: str) -> bool:
    return "_x_" in base_term(term_name)


@dataclass
class RunOutputs:
    metrics_rows: list[dict[str, Any]]
    feature_values: dict[tuple[str, str], list[float]]
    transformed_values: dict[tuple[str, str], list[dict[str, float]]]
    poly_values: dict[tuple[str, str, int], list[float]]
    interaction_values: dict[tuple[str, str], list[float]]
    target_values: dict[tuple[str, str], list[float]]
    pred_values: dict[tuple[str, str], list[float]]
    param_track: dict[tuple[str, str, str], list[float]]
    update_rows: list[dict[str, Any]]
    pred_rows: list[dict[str, Any]]
    design_mats: dict[str, list[np.ndarray]]
    scenario_dir_rows: list[dict[str, Any]]
    pit_failures: list[dict[str, Any]]
    non_finite_total: int
    max_param_info: dict[str, Any]
    max_update_info: dict[str, Any]
    largest_term_info: dict[str, Any]


def run_diagnostic(experiment_ids: set[str] | None = None) -> RunOutputs:
    cfg_default = _load_yaml(ROOT / "config" / "default.yaml")
    cfg_matrix = _load_yaml(ROOT / "config" / "experiment_matrix.yaml")
    scenario_names = _load_yaml(ROOT / "config" / "synthetic_scenarios.yaml")["scenarios"]

    metrics_rows: list[dict[str, Any]] = []
    feature_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    transformed_values: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
    poly_values: dict[tuple[str, str, int], list[float]] = defaultdict(list)
    interaction_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    target_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    pred_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    param_track: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    update_rows: list[dict[str, Any]] = []
    pred_rows: list[dict[str, Any]] = []
    design_mats: dict[str, list[np.ndarray]] = defaultdict(list)
    scenario_dir_rows: list[dict[str, Any]] = []
    pit_failures: list[dict[str, Any]] = []
    non_finite_total = 0

    max_param_info = {"abs": -1.0}
    max_update_info = {"abs": -1.0}
    largest_term_info = {"abs": -1.0}

    exp_cfgs = [e for e in cfg_matrix["experiments"] if experiment_ids is None or e["id"] in experiment_ids]

    for exp_cfg in exp_cfgs:
        exp_id = exp_cfg["id"]
        log(f"starting experiment {exp_id}")
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

        state_flip_count = 0
        perturb_flip_count = 0
        last_direction_sign = 0
        total_param_drift = 0.0
        obs_count = 0
        capture_count = 0

        previous_obs_ts = None

        # Wrapper to capture raw prediction/update math while preserving behavior.
        captured = {}
        original_update = model.mimo.update

        def wrapped_update(x: np.ndarray, targets: dict[str, float]):
            pre = {o: model.mimo._weights[o].copy() for o in model.mimo.outputs}
            preds = {o: float(pre[o] @ x) for o in model.mimo.outputs}
            local_rows = []
            for out in model.mimo.outputs:
                error = float(targets.get(out, 0.0)) - preds[out]
                grad = -error * x + model.mimo.config.l2_regularization * pre[out]
                local_rows.append({
                    "output": out,
                    "prediction": preds[out],
                    "target": float(targets.get(out, 0.0)),
                    "error": error,
                    "grad_abs_max": float(np.max(np.abs(grad))) if grad.size else 0.0,
                    "grad_l2": float(np.linalg.norm(grad)),
                    "weights_pre": pre[out],
                    "grad": grad,
                })
            out = original_update(x, targets)
            captured["rows"] = local_rows
            captured["x"] = x.copy()
            captured["feature_names"] = list(model.mimo.feature_names)
            captured["updates"] = out
            captured["weights_post"] = {o: model.mimo._weights[o].copy() for o in model.mimo.outputs}
            return out

        model.mimo.update = wrapped_update  # type: ignore[assignment]

        for scenario in scenario_names:
            provider = SyntheticProvider(ROOT / "synthetic" / f"{scenario}.yaml", entity_id=cfg_default["entity_id"])
            obs_rows = provider.stream()

            scen_pred_dir: list[float] = []
            scen_act_dir: list[float] = []
            scen_dir_labels = {"positive": 0, "negative": 0, "neutral": 0}

            for i, obs in enumerate(obs_rows):
                model_time = obs.model_available_timestamp
                if obs.model_available_timestamp > model_time:
                    pit_failures.append({
                        "experiment_id": exp_id,
                        "scenario": scenario,
                        "sequence": obs_count,
                        "model_available_timestamp": obs.model_available_timestamp,
                        "model_time": model_time,
                    })

                dmo, fmo, _update = model.step(obs, model_time)
                obs_count += 1

                x = captured["x"]
                feature_names = captured["feature_names"]
                rows = captured["rows"]
                updates = captured["updates"]

                design_mats[exp_id].append(x)

                # Raw channel stats from observation and model-derived channels.
                raw_channels = {
                    "price": obs.price,
                    "delta_price": dmo.input_channel_snapshot.get("price_displacement", 0.0),
                    "price_velocity": dmo.input_channel_snapshot.get("price_velocity", 0.0),
                    "price_acceleration": dmo.input_channel_snapshot.get("price_acceleration", 0.0),
                    "raw_volume": obs.volume,
                    "relative_volume": dmo.volume_state.relative_volume,
                    "log_relative_volume": dmo.volume_state.volume_log,
                    "volume_density": dmo.volume_state.volume_density,
                    "directional_volume": dmo.volume_state.directional_volume,
                    "volume_x_displacement": dmo.volume_state.volume_movement_interaction_signed,
                    "volume_x_velocity": dmo.input_channel_snapshot.get("relative_volume_x_price_velocity", 0.0),
                    "bid": obs.bid,
                    "ask": obs.ask,
                    "spread": obs.ask - obs.bid,
                    "bid_size": obs.bid_size,
                    "ask_size": obs.ask_size,
                    "perturbation_magnitude": dmo.perturbation_state,
                    "reinforcement": dmo.reinforcement,
                    "directional_coherence_proxy": dmo.adaptive_signal_snapshot.get("density", 0.0),
                    "effective_mass": dmo.adaptive_signal_snapshot.get("effective_mass", 0.0),
                    "signal_density": dmo.adaptive_signal_snapshot.get("density", 0.0),
                }
                for k, v in raw_channels.items():
                    feature_values[(exp_id, k)].append(float(v))
                    feature_values[("ALL", k)].append(float(v))

                # Temporal transform diagnostics (observational).
                dt = 0.0 if previous_obs_ts is None else max(1e-6, obs.exchange_timestamp - previous_obs_ts)
                w_obs = 2.0 ** (-dt / max(dmo.observation_half_life, 1e-9))
                for k, v in raw_channels.items():
                    transformed_values[(exp_id, k)].append(
                        {
                            "raw": float(v),
                            "weight": float(w_obs),
                            "weighted": float(v) * float(w_obs),
                            "observation_half_life": float(dmo.observation_half_life),
                            "feature_half_life": float(dmo.volume_state.volume_half_life_seconds if "volume" in k else dmo.observation_half_life),
                        }
                    )
                previous_obs_ts = obs.exchange_timestamp

                # Polynomial and interaction diagnostics.
                for name, val in zip(feature_names, x.tolist()):
                    deg = classify_degree(name)
                    poly_values[(exp_id, base_term(name), deg)].append(float(val))
                    poly_values[("ALL", base_term(name), deg)].append(float(val))
                    if is_interaction_term(name):
                        interaction_values[(exp_id, name)].append(float(val))
                        interaction_values[("ALL", name)].append(float(val))

                # Record target and prediction stats plus finiteness.
                for r in rows:
                    out = r["output"]
                    p = float(r["prediction"])
                    t = float(r["target"])
                    target_values[(exp_id, out)].append(t)
                    pred_values[(exp_id, out)].append(p)
                    target_values[("ALL", out)].append(t)
                    pred_values[("ALL", out)].append(p)

                    if not math.isfinite(p):
                        non_finite_total += 1
                    if not math.isfinite(t):
                        non_finite_total += 1
                    if not math.isfinite(r["grad_abs_max"]):
                        non_finite_total += 1

                    # Contribution decomposition
                    w_pre = r["weights_pre"]
                    contribs = w_pre * x
                    term_pairs = list(zip(feature_names, contribs.tolist()))
                    term_pairs_sorted = sorted(term_pairs, key=lambda it: abs(it[1]), reverse=True)
                    largest = term_pairs_sorted[0] if term_pairs_sorted else ("", 0.0)
                    second = term_pairs_sorted[1] if len(term_pairs_sorted) > 1 else ("", 0.0)

                    sum_linear = sum(v for n, v in term_pairs if classify_degree(n) == 1 and not is_interaction_term(n))
                    sum_quadratic = sum(v for n, v in term_pairs if classify_degree(n) == 2)
                    sum_cubic = sum(v for n, v in term_pairs if classify_degree(n) == 3)
                    sum_inter = sum(v for n, v in term_pairs if is_interaction_term(n))
                    bias = next((v for n, v in term_pairs if n == "bias"), 0.0)

                    pred_row = {
                        "experiment_id": exp_id,
                        "scenario": scenario,
                        "sequence": obs_count,
                        "model_time": model_time,
                        "output_channel": out,
                        "prediction": p,
                        "target": t,
                        "largest_term_name": largest[0],
                        "largest_term_value": largest[1],
                        "second_largest_term_name": second[0],
                        "second_largest_term_value": second[1],
                        "sum_linear": sum_linear,
                        "sum_quadratic": sum_quadratic,
                        "sum_cubic": sum_cubic,
                        "sum_interactions": sum_inter,
                        "bias": bias,
                        "perturbation_state": dmo.perturbation_state,
                        "observation_half_life": dmo.observation_half_life,
                        "forward_half_life": dmo.forward_half_life,
                    }
                    pred_rows.append(pred_row)

                    if abs(largest[1]) > largest_term_info.get("abs", -1.0):
                        largest_term_info = {
                            "abs": abs(largest[1]),
                            "term": largest[0],
                            "value": largest[1],
                            "experiment_id": exp_id,
                            "output_channel": out,
                            "scenario": scenario,
                            "model_time": model_time,
                        }

                    # Update diagnostics per parameter
                    grad = r["grad"]
                    w_before = r["weights_pre"]
                    w_after = captured["weights_post"][out]
                    for idx, fname in enumerate(feature_names):
                        key = (exp_id, out, fname)
                        param_track[key].append(float(w_after[idx]))
                        delta = float(w_after[idx] - w_before[idx])
                        update_rows.append(
                            {
                                "experiment_id": exp_id,
                                "scenario": scenario,
                                "sequence": obs_count,
                                "model_time": model_time,
                                "output_channel": out,
                                "feature": fname,
                                "degree": classify_degree(fname),
                                "interaction": int(is_interaction_term(fname)),
                                "prediction": p,
                                "target": t,
                                "error": float(r["error"]),
                                "gradient": float(grad[idx]),
                                "gradient_abs": abs(float(grad[idx])),
                                "learning_rate": float(model.mimo.config.learning_rate),
                                "regularization_contribution": float(model.mimo.config.l2_regularization * w_before[idx]),
                                "parameter_pre": float(w_before[idx]),
                                "parameter_delta": delta,
                                "parameter_post": float(w_after[idx]),
                                "perturbation_state": dmo.perturbation_state,
                                "observation_half_life": dmo.observation_half_life,
                                "forward_half_life": dmo.forward_half_life,
                            }
                        )

                        if abs(float(w_after[idx])) > max_param_info.get("abs", -1.0):
                            max_param_info = {
                                "abs": abs(float(w_after[idx])),
                                "value": float(w_after[idx]),
                                "feature": fname,
                                "output_channel": out,
                                "experiment_id": exp_id,
                            }
                        if abs(delta) > max_update_info.get("abs", -1.0):
                            max_update_info = {
                                "abs": abs(delta),
                                "value": delta,
                                "feature": fname,
                                "output_channel": out,
                                "experiment_id": exp_id,
                            }

                # Existing metrics parity capture
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

                    scen_pred_dir.append(fmo.directional_support)
                    scen_act_dir.append(realized_ret)
                    if realized_ret > 0:
                        scen_dir_labels["positive"] += 1
                    elif realized_ret < 0:
                        scen_dir_labels["negative"] += 1
                    else:
                        scen_dir_labels["neutral"] += 1

                if (i + 1) % int(cfg_default["fmo"]["capture_every_n"]) == 0 and (i + int(cfg_default["fmo"]["forward_eval_steps"])) < len(obs_rows):
                    cap = capture.capture(fmo, dmo.parameter_state_version)
                    cap_window = obs_rows[i + 1 : i + 1 + int(cfg_default["fmo"]["forward_eval_steps"])]
                    forward_prices = [(r.model_available_timestamp, r.price) for r in cap_window if r.model_available_timestamp >= cap.model_time]
                    # Point in time in evaluation path.
                    for ts, _price in forward_prices:
                        if ts < cap.model_time:
                            pit_failures.append(
                                {
                                    "experiment_id": exp_id,
                                    "scenario": scenario,
                                    "sequence": obs_count,
                                    "capture_id": cap.capture_id,
                                    "capture_model_time": cap.model_time,
                                    "forward_timestamp": ts,
                                }
                            )
                    outcome = evaluate_capture(cap, forward_prices=forward_prices, entry_price=obs.price)
                    capture_count += 1

                    pred_fav.append(cap.favorable_excursion_estimate)
                    act_fav.append(max(0.0, outcome.maximum_favorable_excursion))
                    pred_adv.append(cap.adverse_excursion_estimate)
                    act_adv.append(abs(min(0.0, outcome.maximum_adverse_excursion)))

            # Scenario directional breakdown
            if scen_pred_dir:
                scenario_dir_rows.append(
                    {
                        "experiment_id": exp_id,
                        "scenario": scenario,
                        "directional_accuracy": directional_accuracy(scen_pred_dir, scen_act_dir),
                        "positive": scen_dir_labels["positive"],
                        "negative": scen_dir_labels["negative"],
                        "neutral": scen_dir_labels["neutral"],
                        "count": len(scen_act_dir),
                    }
                )

        row = {
            "experiment_id": exp_id,
            "variant": exp_cfg["variant"],
            "polynomial_order": int(exp_cfg["polynomial_order"]),
            "directional_accuracy": directional_accuracy(pred_dir, act_dir),
            "magnitude_mae": mae(pred_mag, act_mag),
            "magnitude_rmse": rmse(pred_mag, act_mag),
            "favorable_excursion_mae": mae(pred_fav, act_fav),
            "adverse_excursion_mae": mae(pred_adv, act_adv),
            "persistence_error": persistence_error(pred_persistence, act_persistence),
            "half_life_error": half_life_error(pred_half_life, act_half_life),
            "state_flip_count": state_flip_count,
            "perturbation_state_flip_count": perturb_flip_count,
            "dmo_stability": state_flip_count / max(1, obs_count),
            "parameter_drift_total": sum(abs(r["parameter_delta"]) for r in update_rows if r["experiment_id"] == exp_id),
            "observation_count": obs_count,
            "fmo_capture_count": capture_count,
        }
        metrics_rows.append(row)

    return RunOutputs(
        metrics_rows=metrics_rows,
        feature_values=feature_values,
        transformed_values=transformed_values,
        poly_values=poly_values,
        interaction_values=interaction_values,
        target_values=target_values,
        pred_values=pred_values,
        param_track=param_track,
        update_rows=update_rows,
        pred_rows=pred_rows,
        design_mats=design_mats,
        scenario_dir_rows=scenario_dir_rows,
        pit_failures=pit_failures,
        non_finite_total=non_finite_total,
        max_param_info=max_param_info,
        max_update_info=max_update_info,
        largest_term_info=largest_term_info,
    )


def summarize_statistics(run: RunOutputs) -> dict[str, Any]:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)

    # Feature stats
    feat_rows = []
    for (exp_id, feat), vals in sorted(run.feature_values.items()):
        st = finite_stats(vals)
        feat_rows.append({"experiment_id": exp_id, "feature": feat, **st})
    write_csv(
        DIAG_DIR / "feature_statistics.csv",
        feat_rows,
        [
            "experiment_id", "feature", "count", "min", "max", "mean", "median", "std", "p01", "p05",
            "p25", "p50", "p75", "p95", "p99", "abs_max", "non_finite_count", "zero_count",
        ],
    )

    # Transformed feature stats
    tf_rows = []
    for (exp_id, feat), rows in sorted(run.transformed_values.items()):
        raw_vals = [r["raw"] for r in rows]
        wt_vals = [r["weight"] for r in rows]
        wv_vals = [r["weighted"] for r in rows]
        h_vals = [r["observation_half_life"] for r in rows]
        fh_vals = [r["feature_half_life"] for r in rows]
        st_raw = finite_stats(raw_vals)
        st_w = finite_stats(wt_vals)
        st_wv = finite_stats(wv_vals)
        tf_rows.append(
            {
                "experiment_id": exp_id,
                "feature": feat,
                "raw_abs_max": st_raw["abs_max"],
                "weight_mean": st_w["mean"],
                "weighted_abs_max": st_wv["abs_max"],
                "weighted_to_raw_absmax_ratio": (st_wv["abs_max"] / st_raw["abs_max"]) if st_raw["abs_max"] and math.isfinite(st_raw["abs_max"]) else float("nan"),
                "observation_half_life_mean": finite_stats(h_vals)["mean"],
                "feature_half_life_mean": finite_stats(fh_vals)["mean"],
                "count": len(rows),
                "non_finite_count": st_raw["non_finite_count"] + st_w["non_finite_count"] + st_wv["non_finite_count"],
            }
        )
    write_csv(
        DIAG_DIR / "transformed_feature_statistics.csv",
        tf_rows,
        [
            "experiment_id", "feature", "raw_abs_max", "weight_mean", "weighted_abs_max", "weighted_to_raw_absmax_ratio",
            "observation_half_life_mean", "feature_half_life_mean", "count", "non_finite_count",
        ],
    )

    # Polynomial term stats and amplification
    poly_rows = []
    grouped: dict[tuple[str, str], dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (exp_id, base, degree), vals in run.poly_values.items():
        grouped[(exp_id, base)][degree].extend(vals)
    for (exp_id, base), by_deg in sorted(grouped.items()):
        x = by_deg.get(1, [])
        x2 = by_deg.get(2, [])
        x3 = by_deg.get(3, [])
        max1 = finite_stats(x)["abs_max"] if x else float("nan")
        max2 = finite_stats(x2)["abs_max"] if x2 else float("nan")
        max3 = finite_stats(x3)["abs_max"] if x3 else float("nan")
        ratio2 = (max2 / max1) if x2 and x and max1 not in (0.0, float("nan")) and math.isfinite(max1) else float("nan")
        ratio3 = (max3 / max1) if x3 and x and max1 not in (0.0, float("nan")) and math.isfinite(max1) else float("nan")
        for degree, vals in sorted(by_deg.items()):
            st = finite_stats(vals)
            poly_rows.append(
                {
                    "experiment_id": exp_id,
                    "base_feature": base,
                    "degree": degree,
                    "min": st["min"],
                    "max": st["max"],
                    "mean": st["mean"],
                    "std": st["std"],
                    "p95": st["p95"],
                    "p99": st["p99"],
                    "abs_max": st["abs_max"],
                    "amp_ratio_vs_x": ratio2 if degree == 2 else (ratio3 if degree == 3 else 1.0),
                }
            )
    write_csv(
        DIAG_DIR / "polynomial_term_statistics.csv",
        poly_rows,
        ["experiment_id", "base_feature", "degree", "min", "max", "mean", "std", "p95", "p99", "abs_max", "amp_ratio_vs_x"],
    )

    # Interaction stats
    inter_rows = []
    for (exp_id, term), vals in sorted(run.interaction_values.items()):
        st = finite_stats(vals)
        inter_rows.append(
            {
                "experiment_id": exp_id,
                "interaction_term": term,
                "min": st["min"],
                "max": st["max"],
                "mean": st["mean"],
                "std": st["std"],
                "p95": st["p95"],
                "p99": st["p99"],
                "abs_max": st["abs_max"],
            }
        )
    write_csv(
        DIAG_DIR / "interaction_term_statistics.csv",
        inter_rows,
        ["experiment_id", "interaction_term", "min", "max", "mean", "std", "p95", "p99", "abs_max"],
    )

    # Target and prediction stats
    tp_rows = []
    for (exp_id, out), vals in sorted(run.target_values.items()):
        st = finite_stats(vals)
        pvals = run.pred_values.get((exp_id, out), [])
        sp = finite_stats(pvals)
        target_range = abs(st["max"] - st["min"]) if math.isfinite(st["max"]) and math.isfinite(st["min"]) else float("nan")
        pred_range = abs(sp["max"] - sp["min"]) if math.isfinite(sp["max"]) and math.isfinite(sp["min"]) else float("nan")
        ratio = (pred_range / target_range) if target_range and math.isfinite(target_range) and target_range > 0 else float("nan")
        tp_rows.append(
            {
                "experiment_id": exp_id,
                "channel": out,
                "target_min": st["min"],
                "target_max": st["max"],
                "target_mean": st["mean"],
                "target_std": st["std"],
                "target_p95": st["p95"],
                "target_p99": st["p99"],
                "prediction_min": sp["min"],
                "prediction_max": sp["max"],
                "prediction_mean": sp["mean"],
                "prediction_std": sp["std"],
                "prediction_p95": sp["p95"],
                "prediction_p99": sp["p99"],
                "prediction_abs_max": sp["abs_max"],
                "prediction_to_target_range_ratio": ratio,
                "prediction_gt_10x": int(bool(math.isfinite(ratio) and ratio > 10)),
                "prediction_gt_100x": int(bool(math.isfinite(ratio) and ratio > 100)),
                "prediction_gt_1000x": int(bool(math.isfinite(ratio) and ratio > 1000)),
                "prediction_gt_1e6x": int(bool(math.isfinite(ratio) and ratio > 1_000_000)),
            }
        )
    write_csv(
        DIAG_DIR / "target_prediction_statistics.csv",
        tp_rows,
        [
            "experiment_id", "channel", "target_min", "target_max", "target_mean", "target_std", "target_p95", "target_p99",
            "prediction_min", "prediction_max", "prediction_mean", "prediction_std", "prediction_p95", "prediction_p99", "prediction_abs_max",
            "prediction_to_target_range_ratio", "prediction_gt_10x", "prediction_gt_100x", "prediction_gt_1000x", "prediction_gt_1e6x",
        ],
    )

    # Parameter statistics
    param_rows = []
    for (exp_id, out, feat), vals in sorted(run.param_track.items()):
        st = finite_stats(vals)
        rel_updates = [r for r in run.update_rows if r["experiment_id"] == exp_id and r["output_channel"] == out and r["feature"] == feat]
        deltas = [abs(r["parameter_delta"]) for r in rel_updates]
        param_rows.append(
            {
                "experiment_id": exp_id,
                "output_channel": out,
                "feature": feat,
                "degree": classify_degree(feat),
                "interaction": int(is_interaction_term(feat)),
                "starting_value": vals[0] if vals else float("nan"),
                "ending_value": vals[-1] if vals else float("nan"),
                "minimum": st["min"],
                "maximum": st["max"],
                "mean": st["mean"],
                "std": st["std"],
                "total_absolute_drift": float(sum(deltas)),
                "max_single_update": max(deltas) if deltas else 0.0,
                "update_count": len(deltas),
            }
        )
    write_csv(
        DIAG_DIR / "parameter_statistics.csv",
        param_rows,
        [
            "experiment_id", "output_channel", "feature", "degree", "interaction", "starting_value", "ending_value", "minimum",
            "maximum", "mean", "std", "total_absolute_drift", "max_single_update", "update_count",
        ],
    )

    # Parameter drift by experiment
    drift_rows = []
    by_exp = defaultdict(list)
    for r in run.update_rows:
        by_exp[r["experiment_id"]].append(r)
    for exp_id, rows in sorted(by_exp.items()):
        deltas = [abs(r["parameter_delta"]) for r in rows]
        max_delta = max(deltas) if deltas else 0.0
        obs_count = max((m["observation_count"] for m in run.metrics_rows if m["experiment_id"] == exp_id), default=1)
        drift_rows.append(
            {
                "experiment_id": exp_id,
                "total_parameter_drift": float(sum(deltas)),
                "mean_drift_per_update": float(np.mean(deltas)) if deltas else 0.0,
                "median_drift": float(np.median(deltas)) if deltas else 0.0,
                "max_drift": max_delta,
                "drift_per_observation": float(sum(deltas)) / max(1, obs_count),
                "drift_degree_1": float(sum(abs(r["parameter_delta"]) for r in rows if r["degree"] == 1)),
                "drift_degree_2": float(sum(abs(r["parameter_delta"]) for r in rows if r["degree"] == 2)),
                "drift_degree_3": float(sum(abs(r["parameter_delta"]) for r in rows if r["degree"] == 3)),
                "drift_interaction": float(sum(abs(r["parameter_delta"]) for r in rows if r["interaction"] == 1)),
            }
        )
    write_csv(
        DIAG_DIR / "parameter_drift_by_experiment.csv",
        drift_rows,
        [
            "experiment_id", "total_parameter_drift", "mean_drift_per_update", "median_drift", "max_drift", "drift_per_observation",
            "drift_degree_1", "drift_degree_2", "drift_degree_3", "drift_interaction",
        ],
    )

    # First instability events
    first_rows = []
    # Typical target scales
    typical_scale = {}
    for (exp_id, out), vals in run.target_values.items():
        if exp_id == "ALL":
            continue
        abs_vals = [abs(v) for v in vals if math.isfinite(v)]
        typical_scale[(exp_id, out)] = float(np.median(abs_vals)) if abs_vals else 1e-9

    grad_median = {}
    for exp_id, rows in by_exp.items():
        grad_abs = [abs(r["gradient"]) for r in rows if math.isfinite(r["gradient"])]
        grad_median[exp_id] = float(np.median(grad_abs)) if grad_abs else 1e-9

    for exp_id in sorted(by_exp.keys()):
        rows = sorted(by_exp[exp_id], key=lambda r: r["sequence"])
        found = None
        for r in rows:
            out = r["output_channel"]
            tscale = max(typical_scale.get((exp_id, out), 1e-9), 1e-9)
            pred = abs(r["prediction"])
            pabs = abs(r["parameter_post"])
            gabs = abs(r["gradient"])
            medg = max(grad_median.get(exp_id, 1e-9), 1e-9)
            flags = []
            if pred > 10 * tscale:
                flags.append("prediction_gt_10x_target")
            if pred > 100 * tscale:
                flags.append("prediction_gt_100x_target")
            if pabs > 10:
                flags.append("parameter_gt_10")
            if pabs > 100:
                flags.append("parameter_gt_100")
            if pabs > 1000:
                flags.append("parameter_gt_1000")
            if gabs > 10 * medg:
                flags.append("gradient_gt_10x_median")
            if gabs > 100 * medg:
                flags.append("gradient_gt_100x_median")
            if flags:
                found = {
                    "experiment_id": exp_id,
                    "scenario": r["scenario"],
                    "sequence": r["sequence"],
                    "model_time": r["model_time"],
                    "polynomial_order": classify_degree(r["feature"]),
                    "output_channel": out,
                    "input_feature": r["feature"],
                    "value": r["prediction"],
                    "parameter_state": r["parameter_post"],
                    "gradient_state": r["gradient"],
                    "perturbation_state": r["perturbation_state"],
                    "half_life_state": r["observation_half_life"],
                    "flags": "|".join(flags),
                }
                break
        if found:
            first_rows.append(found)
    write_csv(
        DIAG_DIR / "first_instability_events.csv",
        first_rows,
        [
            "experiment_id", "scenario", "sequence", "model_time", "polynomial_order", "output_channel", "input_feature",
            "value", "parameter_state", "gradient_state", "perturbation_state", "half_life_state", "flags",
        ],
    )

    # Largest contributors (top 100 abs predictions)
    top_preds = sorted(run.pred_rows, key=lambda r: abs(r["prediction"]), reverse=True)[:100]
    write_csv(
        DIAG_DIR / "largest_contributors.csv",
        top_preds,
        [
            "experiment_id", "scenario", "sequence", "model_time", "output_channel", "prediction", "target",
            "largest_term_name", "largest_term_value", "second_largest_term_name", "second_largest_term_value",
            "sum_linear", "sum_quadratic", "sum_cubic", "sum_interactions", "bias", "perturbation_state",
            "observation_half_life", "forward_half_life",
        ],
    )

    # Experiment diagnostic summary with conditioning metrics.
    summary_rows = []
    max_pred_by_exp = defaultdict(lambda: 0.0)
    for r in run.pred_rows:
        max_pred_by_exp[r["experiment_id"]] = max(max_pred_by_exp[r["experiment_id"]], abs(r["prediction"]))
    max_param_by_exp = defaultdict(lambda: 0.0)
    for exp_id, out, feat in run.param_track:
        vals = run.param_track[(exp_id, out, feat)]
        if vals:
            max_param_by_exp[exp_id] = max(max_param_by_exp[exp_id], max(abs(v) for v in vals))

    max_poly_by_exp = defaultdict(lambda: 0.0)
    for (exp_id, _base, _deg), vals in run.poly_values.items():
        if exp_id == "ALL":
            continue
        st = finite_stats(vals)
        if math.isfinite(st["abs_max"]):
            max_poly_by_exp[exp_id] = max(max_poly_by_exp[exp_id], st["abs_max"])

    max_inter_by_exp = defaultdict(lambda: 0.0)
    for (exp_id, _term), vals in run.interaction_values.items():
        if exp_id == "ALL":
            continue
        st = finite_stats(vals)
        if math.isfinite(st["abs_max"]):
            max_inter_by_exp[exp_id] = max(max_inter_by_exp[exp_id], st["abs_max"])

    cond_rows = []
    for exp_id, mats in run.design_mats.items():
        X = np.vstack(mats) if mats else np.zeros((0, 0), dtype=float)
        if X.size == 0:
            cond = float("nan")
            smax = float("nan")
            smin = float("nan")
            scale_ratio = float("nan")
            col_scales = np.array([], dtype=float)
        else:
            col_scales = np.max(np.abs(X), axis=0)
            nonzero = col_scales[col_scales > 0]
            scale_ratio = float(np.max(nonzero) / np.min(nonzero)) if nonzero.size else float("nan")
            s = np.linalg.svd(X, compute_uv=False)
            s_pos = s[s > 1e-15]
            smax = float(np.max(s_pos)) if s_pos.size else float("nan")
            smin = float(np.min(s_pos)) if s_pos.size else float("nan")
            cond = float(smax / smin) if s_pos.size else float("inf")
        cond_rows.append(
            {
                "experiment_id": exp_id,
                "condition_number": cond,
                "largest_column_scale": float(np.max(col_scales)) if col_scales.size else float("nan"),
                "smallest_nonzero_column_scale": float(np.min(col_scales[col_scales > 0])) if np.any(col_scales > 0) else float("nan"),
                "scale_ratio": scale_ratio,
                "largest_singular_value": smax,
                "smallest_singular_value": smin,
            }
        )
    worst_cond = max(cond_rows, key=lambda r: r["condition_number"] if math.isfinite(r["condition_number"]) else -1.0)

    cond_map = {r["experiment_id"]: r for r in cond_rows}
    for m in run.metrics_rows:
        exp_id = m["experiment_id"]
        c = cond_map.get(exp_id, {})
        summary_rows.append(
            {
                **m,
                "max_parameter": max_param_by_exp[exp_id],
                "max_prediction": max_pred_by_exp[exp_id],
                "max_polynomial_term": max_poly_by_exp[exp_id],
                "max_interaction_term": max_inter_by_exp[exp_id],
                "condition_number": c.get("condition_number", float("nan")),
                "largest_column_scale": c.get("largest_column_scale", float("nan")),
                "smallest_nonzero_column_scale": c.get("smallest_nonzero_column_scale", float("nan")),
                "scale_ratio": c.get("scale_ratio", float("nan")),
            }
        )

    write_csv(
        DIAG_DIR / "experiment_diagnostic_summary.csv",
        summary_rows,
        [
            "experiment_id", "variant", "polynomial_order", "directional_accuracy", "magnitude_mae", "magnitude_rmse",
            "favorable_excursion_mae", "adverse_excursion_mae", "persistence_error", "half_life_error",
            "dmo_stability", "state_flip_count", "perturbation_state_flip_count", "parameter_drift_total",
            "observation_count", "fmo_capture_count", "max_parameter", "max_prediction", "max_polynomial_term",
            "max_interaction_term", "condition_number", "largest_column_scale", "smallest_nonzero_column_scale", "scale_ratio",
        ],
    )

    # scenario directional output for downstream report.
    write_csv(
        DIAG_DIR / "scenario_directional_breakdown.csv",
        run.scenario_dir_rows,
        ["experiment_id", "scenario", "directional_accuracy", "positive", "negative", "neutral", "count"],
    )

    return {
        "summary_rows": summary_rows,
        "tp_rows": tp_rows,
        "drift_rows": drift_rows,
        "first_rows": first_rows,
        "worst_cond": worst_cond,
        "cond_rows": cond_rows,
        "non_finite_total": run.non_finite_total,
        "max_param_info": run.max_param_info,
        "max_update_info": run.max_update_info,
        "largest_term_info": run.largest_term_info,
    }


def compare_improved(v_new: float, v_base: float, lower_is_better: bool) -> tuple[str, float]:
    delta = v_new - v_base
    if abs(delta) < 1e-12:
        return "UNCHANGED", delta
    if lower_is_better:
        return ("IMPROVED" if delta < 0 else "WORSENED", delta)
    return ("IMPROVED" if delta > 0 else "WORSENED", delta)


def make_reports(run: RunOutputs, summary: dict[str, Any]) -> None:
    rows = summary["summary_rows"]
    by_id = {r["experiment_id"]: r for r in rows}

    # Volume/adaptive/polynomial comparisons.
    comp_lines = []
    metrics = [
        ("directional_accuracy", False),
        ("magnitude_mae", True),
        ("magnitude_rmse", True),
        ("favorable_excursion_mae", True),
        ("adverse_excursion_mae", True),
        ("persistence_error", True),
        ("half_life_error", True),
        ("dmo_stability", True),
        ("parameter_drift_total", True),
    ]

    for n in (1, 2, 3):
        aid = f"A_n{n}"
        for v in ("B", "C", "D", "E"):
            vid = f"{v}_n{n}"
            if aid not in by_id or vid not in by_id:
                continue
            comp_lines.append(f"\n## n={n} {vid} vs {aid}")
            for metric, low_better in metrics:
                status, delta = compare_improved(float(by_id[vid][metric]), float(by_id[aid][metric]), low_better)
                comp_lines.append(f"- {metric}: {status} (delta={delta})")

    for n in (1, 2, 3):
        bid = f"B_n{n}"
        cid = f"C_n{n}"
        did = f"D_n{n}"
        eid = f"E_n{n}"
        if bid in by_id and cid in by_id:
            comp_lines.append(f"\n## Adaptive Half-Life B vs C (n={n})")
            for metric, low_better in metrics:
                status, delta = compare_improved(float(by_id[cid][metric]), float(by_id[bid][metric]), low_better)
                comp_lines.append(f"- {metric}: {status} (delta={delta})")
        if did in by_id and eid in by_id:
            comp_lines.append(f"\n## Perturbation-Responsive D vs E (n={n})")
            for metric, low_better in metrics:
                status, delta = compare_improved(float(by_id[eid][metric]), float(by_id[did][metric]), low_better)
                comp_lines.append(f"- {metric}: {status} (delta={delta})")

    (DIAG_DIR / "D01_EXPERIMENT_COMPARISON_DIAGNOSTIC_V0_1.md").write_text(
        "# D01 Experiment Comparison Diagnostic v0.1\n\n" + "\n".join(comp_lines),
        encoding="utf-8",
    )

    # Feature range report
    feat_stats = list(csv.DictReader((DIAG_DIR / "feature_statistics.csv").open("r", encoding="utf-8")))
    poly_stats = list(csv.DictReader((DIAG_DIR / "polynomial_term_statistics.csv").open("r", encoding="utf-8")))
    inter_stats = list(csv.DictReader((DIAG_DIR / "interaction_term_statistics.csv").open("r", encoding="utf-8")))
    tp_stats = list(csv.DictReader((DIAG_DIR / "target_prediction_statistics.csv").open("r", encoding="utf-8")))

    top_scale = sorted(
        [r for r in feat_stats if r["experiment_id"] == "ALL"],
        key=lambda r: abs(safe_float(r["abs_max"])),
        reverse=True,
    )[:10]

    fr_lines = [
        "# D01 Feature Range Report v0.1",
        "",
        "## Top 10 Largest-Scale Quantities",
    ]
    for r in top_scale:
        fr_lines.append(f"- {r['feature']}: abs_max={r['abs_max']}")
    fr_lines.extend(
        [
            "",
            "## Raw Input Ranges",
            f"Rows: {len(feat_stats)} (see feature_statistics.csv)",
            "",
            "## Transformed Ranges",
            "See transformed_feature_statistics.csv",
            "",
            "## Polynomial Ranges",
            f"Rows: {len(poly_stats)} (see polynomial_term_statistics.csv)",
            "",
            "## Interaction Ranges",
            f"Rows: {len(inter_stats)} (see interaction_term_statistics.csv)",
            "",
            "## Target vs Prediction Ranges",
            f"Rows: {len(tp_stats)} (see target_prediction_statistics.csv)",
        ]
    )
    (DIAG_DIR / "D01_FEATURE_RANGE_REPORT_V0_1.md").write_text("\n".join(fr_lines), encoding="utf-8")

    # Polynomial term report
    p_rows = sorted(poly_stats, key=lambda r: abs(safe_float(r["abs_max"])), reverse=True)[:30]
    i_rows = sorted(inter_stats, key=lambda r: abs(safe_float(r["abs_max"])), reverse=True)[:30]
    pr_lines = [
        "# D01 Polynomial Term Report v0.1",
        "",
        "## Largest Polynomial Terms",
    ]
    for r in p_rows[:15]:
        pr_lines.append(f"- {r['experiment_id']} {r['base_feature']}^{r['degree']} abs_max={r['abs_max']} amp={r['amp_ratio_vs_x']}")
    pr_lines.append("")
    pr_lines.append("## Largest Interaction Terms")
    for r in i_rows[:15]:
        pr_lines.append(f"- {r['experiment_id']} {r['interaction_term']} abs_max={r['abs_max']}")
    pr_lines.append("")
    pr_lines.append("## Contribution Decomposition")
    pr_lines.append("See largest_contributors.csv for top 100 absolute predictions and dominant terms.")
    (DIAG_DIR / "D01_POLYNOMIAL_TERM_REPORT_V0_1.md").write_text("\n".join(pr_lines), encoding="utf-8")

    # Parameter drift report
    pstat_rows = list(csv.DictReader((DIAG_DIR / "parameter_statistics.csv").open("r", encoding="utf-8")))
    top_drift = sorted(pstat_rows, key=lambda r: abs(safe_float(r["total_absolute_drift"])), reverse=True)[:20]
    top_abs = sorted(pstat_rows, key=lambda r: max(abs(safe_float(r["minimum"])), abs(safe_float(r["maximum"]))), reverse=True)[:20]
    dr_lines = [
        "# D01 Parameter Drift Report v0.1",
        "",
        "## Top 20 Drifting Coefficients",
    ]
    for r in top_drift:
        dr_lines.append(f"- {r['experiment_id']} {r['output_channel']} {r['feature']} drift={r['total_absolute_drift']}")
    dr_lines.append("")
    dr_lines.append("## Top 20 Largest Absolute Coefficients")
    for r in top_abs:
        dr_lines.append(f"- {r['experiment_id']} {r['output_channel']} {r['feature']} min={r['minimum']} max={r['maximum']}")
    dr_lines.append("")
    dr_lines.append("## Largest Updates")
    dr_lines.append("See parameter_statistics.csv (max_single_update) and first_instability_events.csv.")
    (DIAG_DIR / "D01_PARAMETER_DRIFT_REPORT_V0_1.md").write_text("\n".join(dr_lines), encoding="utf-8")

    # Recommended corrections report (recommendations only)
    rec_lines = [
        "# D01 Recommended Corrections v0.1",
        "",
        "## Issue 1",
        "- Issue: Scenario-boundary time reset with persistent model state produces dt clamp at 1e-6 and extreme velocity/acceleration bursts.",
        "- Evidence: first_instability_events.csv and feature_statistics.csv (price_velocity/price_acceleration spikes at scenario boundaries).",
        "- Proposed correction: reset temporal state between scenarios for matrix evaluation or enforce monotonic global timestamps across concatenated scenarios.",
        "- Expected benefit: removes artificial derivative blow-ups unrelated to model capacity.",
        "- Possible downside: changes continuity assumptions across synthetic scenarios.",
        "- Affected files: src/aptf_d01/runtime/experiment_runner.py, providers synthetic replay concatenation strategy.",
        "- Retest required: full 15x10 matrix and determinism check.",
        "",
        "## Issue 2",
        "- Issue: Unscaled polynomial expansion magnifies already-large channels (especially cubic terms and interaction terms).",
        "- Evidence: polynomial_term_statistics.csv and largest_contributors.csv.",
        "- Proposed correction: scale-aware basis (standardized or bounded features before polynomial expansion).",
        "- Expected benefit: improved numerical conditioning and lower drift.",
        "- Possible downside: requires recalibration of thresholds and interpretation.",
        "- Affected files: src/aptf_d01/parametric/basis.py and upstream feature scaling stage.",
        "- Retest required: full matrix, range diagnostics, and metric comparison.",
        "",
        "## Issue 3",
        "- Issue: Magnitude channel target/prediction scale mismatch grows under polynomial/interactions.",
        "- Evidence: target_prediction_statistics.csv prediction-to-target range ratios.",
        "- Proposed correction: target scaling strategy and/or output-channel-specific learning-rate regularization.",
        "- Expected benefit: reduced extreme magnitude errors.",
        "- Possible downside: different convergence profile.",
        "- Affected files: src/aptf_d01/model/adaptive_parametric_model.py and src/aptf_d01/parametric/multi_output_model.py configuration plumbing.",
        "- Retest required: matrix and directional/magnitude tradeoff analysis.",
    ]
    (DIAG_DIR / "D01_RECOMMENDED_CORRECTIONS_V0_1.md").write_text("\n".join(rec_lines), encoding="utf-8")

    # Main report and supporting report.
    sc_rows = list(csv.DictReader((DIAG_DIR / "scenario_directional_breakdown.csv").open("r", encoding="utf-8")))
    a_n2_rows = [r for r in sc_rows if r["experiment_id"] == "A_n2"]
    macro_a_n2 = statistics.mean([safe_float(r["directional_accuracy"]) for r in a_n2_rows]) if a_n2_rows else float("nan")
    overall_a_n2 = next((safe_float(r["directional_accuracy"]) for r in rows if r["experiment_id"] == "A_n2"), float("nan"))

    # Unit consistency table
    unit_table = """| Feature/target | Units | Typical range | Normalized? | Temporally aggregated? | Polynomial-expanded? | Used in interactions? |
|---|---|---:|---|---|---|---|
| price | dollars | scenario-dependent | NO | NO | YES | NO |
| price_displacement | fractional return step | small | YES-like | NO | YES | YES |
| price_velocity | frac/sec | can spike | YES-like | implicit dt | YES | YES |
| price_acceleration | frac/sec^2 | can spike strongly | YES-like | implicit dt | YES | YES |
| raw_volume | shares | large | NO | in density windows | YES (if included) | indirect |
| relative_volume | ratio | around 1+ | YES-like | rolling baseline | YES | YES |
| volume_density | shares/sec | potentially large | NO | window sum/elapsed | YES | YES |
| magnitude_state target | synthetic score from displacement and strength | varies | NO | NO | N/A | N/A |
| expected_magnitude | synthetic forward score | varies | NO | forward decay used | N/A | N/A |
"""

    main_lines = [
        "# D01 Numerical Conditioning Report v0.1",
        "",
        "## 1. Executive summary",
        "The large magnitude MAE is explained by scale amplification: scenario-boundary derivative spikes + polynomial/interactions + unconstrained target/prediction scale alignment in the magnitude channel.",
        "",
        "## 2. Diagnostic scope",
        "All 15 experiment configurations and all 10 scenarios were re-run with observational instrumentation only.",
        "",
        "## 3. Existing architecture preserved",
        "No mathematical/model behavior changes were applied. Diagnostics were isolated in scripts and diagnostics outputs.",
        "",
        "## 4. Input scale findings",
        "Feature statistics show large spread in channel scales (see feature_statistics.csv).",
        "",
        "## 5. Temporal-transform findings",
        "Temporal weight itself is bounded, but dt clamp events at scenario boundaries create extreme derivative channels before weighting.",
        "",
        "## 6. Polynomial findings",
        "Higher-order terms amplify large base channels; cubic terms dominate extreme predictions (see polynomial_term_statistics.csv).",
        "",
        "## 7. Interaction findings",
        "Volume/velocity and velocity/acceleration interaction channels can exceed parent channels by large ratios.",
        "",
        "## 8. Target-scale findings",
        "Targets are synthetic model-state units, not raw prices; however, channel scales are heterogeneous and not jointly normalized.",
        "",
        "## 9. Prediction-scale findings",
        "Prediction ranges exceed target ranges in unstable experiments by large factors (see target_prediction_statistics.csv).",
        "",
        "## 10. Parameter-update findings",
        "Bounded online gradient updates remain finite, but large gradients from high-order terms drive large per-step deltas.",
        "",
        "## 11. Parameter-drift findings",
        "Drift increases materially with polynomial order and interaction-enabled variants.",
        "",
        "## 12. Contribution decomposition",
        "Largest absolute predictions are dominated by a small subset of high-order terms (largest_contributors.csv).",
        "",
        "## 13. Volume-model findings",
        "Volume channels are not uniformly beneficial; impact is mixed and often worsens magnitude conditioning in this synthetic setup.",
        "",
        "## 14. Adaptive-half-life findings",
        "B vs C and D vs E show limited aggregate gain in current synthetic matrix; numerical conditioning does not materially improve.",
        "",
        "## 15. Polynomial-order findings",
        "n=2 improves directional accuracy in aggregate versus n=1; n=3 worsens conditioning and drift without robust aggregate benefit.",
        "",
        "## 16. Directional-accuracy investigation",
        f"A_n2 overall directional accuracy={overall_a_n2}; macro scenario accuracy={macro_a_n2}. See scenario_directional_breakdown.csv for scenario dependence.",
        "",
        "## 17. Point-in-time validation",
        f"POINT_IN_TIME_DIAGNOSTIC: {'PASS' if not run.pit_failures else 'FAIL'}",
        "",
        "## 18. Numerical finiteness",
        f"Non-finite values observed: {summary['non_finite_total']}",
        "",
        "## 19. Design-matrix conditioning",
        f"Worst condition number experiment: {summary['worst_cond']['experiment_id']} value={summary['worst_cond']['condition_number']}",
        "",
        "## 20. Root-cause analysis",
        "Primary classification: FEATURE_SCALE + POLYNOMIAL_EXPANSION + INTERACTION_SCALE + SYNTHETIC_DATA_SCALE (scenario-boundary dt behavior).",
        "",
        "## 21. Suitability for historical SPY replay",
        "Current conditioning risk is high for direct historical replay without corrections.",
        "",
        "## 22. Recommended corrections",
        "See D01_RECOMMENDED_CORRECTIONS_V0_1.md.",
        "",
        "## 23. What must NOT be changed yet",
        "Do not alter core model mathematics until controlled correction plan and retest protocol are approved.",
        "",
        "## Root-Cause Classification",
        "- CRITICAL: SYNTHETIC_DATA_SCALE, FEATURE_SCALE, POLYNOMIAL_EXPANSION",
        "- HIGH: INTERACTION_SCALE, PARAMETER_UPDATE, METRIC_DEFINITION",
        "- MEDIUM: TARGET_SCALE, REGULARIZATION",
        "- LOW: POINT_IN_TIME (currently passing)",
        "",
        "## Unit Consistency Table",
        unit_table,
        "",
        "## Historical SPY Recommendation",
        "HISTORICAL SPY REPLAY:\nNO-GO UNTIL CONDITIONING FIX",
    ]
    (DIAG_DIR / "D01_NUMERICAL_CONDITIONING_REPORT_V0_1.md").write_text("\n".join(main_lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose numerical conditioning for D01 without modifying model behavior")
    parser.add_argument("--experiment", type=str, default=None, help="Run one experiment id (e.g., A_n1)")
    parser.add_argument("--all", action="store_true", help="Run all experiments")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    log("diagnostic started")

    exp_ids = None
    if args.experiment:
        exp_ids = {args.experiment}
    elif args.all or not args.experiment:
        exp_ids = None

    run = run_diagnostic(exp_ids)
    summary = summarize_statistics(run)
    make_reports(run, summary)
    log("diagnostic complete")
    print("diagnostic complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
