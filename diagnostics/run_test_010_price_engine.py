from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PRICE = ROOT / "APTF_TEST_009_DERIVATIVE_OBSERVATIONS_V0_1.csv"
SOURCE = ROOT / "APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv"
FAMILIES = ("PRICE_LINEAR", "PRICE_AFFINE_TIME", "PRICE_QUADRATIC_DIAGONAL")
WINDOWS = (15, 30, 60)
CONDITION_LIMIT = 1e8

COMPARISON_COLUMNS = [
    "model_id", "model_family", "lookback", "parameter_count", "valid_fits",
    "failed_fits", "unstable_fits", "singular_fits", "median_condition_number",
    "p95_condition_number", "coefficient_stability_median_step",
    "one_step_P2_MAE", "one_step_P2_RMSE", "one_step_P2_median_absolute_error",
    "one_step_P2_signed_bias", "one_step_P1_MAE", "one_step_P_MAE",
    "P2_evolution_sign_accuracy", "curvature_state_transition_accuracy",
    "intraday_P2_MAE", "session_gap_P2_MAE",
]

EMISSION_COLUMNS = [
    "price_emission_id", "observation_index", "timestamp", "session_id",
    "session_boundary_flag", "transition_stratum", "P", "P1", "P2", "J_P",
    "local_model_id", "local_model_window", "model_condition", "model_stability",
    "predicted_next_P", "predicted_next_P1", "predicted_next_P2",
    "actual_next_P", "actual_next_P1", "actual_next_P2", "prediction_error_P",
    "prediction_error_P1", "prediction_error_P2", "P2_sign_prediction_correct",
    "curvature_state_transition_correct", "next_elapsed_minutes",
    "local_model_parameters_json", "local_model_scaling_json",
    "prediction_error_estimate_P2_MAE", "valid_local_horizon_minutes",
]


def parse_local(value: str) -> datetime:
    return datetime.fromisoformat(value)


def sign(value: float, tolerance: float = 1e-15) -> int:
    return 1 if value > tolerance else -1 if value < -tolerance else 0


def transition_stratum(previous: dict[str, str], current: dict[str, str]) -> str:
    prior_local = parse_local(previous["event_timestamp_local"])
    current_local = parse_local(current["event_timestamp_local"])
    date_delta = (current_local.date() - prior_local.date()).days
    elapsed = (datetime.fromisoformat(current["event_timestamp_utc"].replace("Z", "+00:00")) - datetime.fromisoformat(previous["event_timestamp_utc"].replace("Z", "+00:00"))).total_seconds()
    if date_delta >= 2:
        return "WEEKEND_OR_HOLIDAY_GAP"
    if date_delta == 1:
        return "OVERNIGHT_GAP"
    if previous["session_type"] != current["session_type"]:
        return "SESSION_TRANSITION"
    if elapsed > 60:
        return "DATA_GAP_IRREGULAR_INTERVAL"
    return "INTRASESSION_CONTINUOUS"


def design_matrix(
    family: str,
    p: np.ndarray,
    p1: np.ndarray,
    p2: np.ndarray,
    times: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]] | None:
    state = np.column_stack((p, p1, p2))
    means = np.mean(state, axis=0)
    scales = np.std(state, axis=0)
    if np.any(~np.isfinite(scales)) or np.any(scales <= 0):
        return None
    z = (state - means) / scales
    columns = [np.ones(len(p)), z[:, 0], z[:, 1], z[:, 2]]
    prediction = [1.0, *(state[-1] - means) / scales]
    metadata: dict[str, Any] = {"state_means": means.tolist(), "state_scales": scales.tolist()}
    if family == "PRICE_AFFINE_TIME":
        local = times - times[-1]
        local_mean = float(np.mean(local))
        local_scale = float(np.std(local))
        if local_scale <= 0:
            return None
        columns.append((local - local_mean) / local_scale)
        prediction.append((0.0 - local_mean) / local_scale)
        metadata.update({"time_mean": local_mean, "time_scale": local_scale, "time_origin": "FIT_ENDPOINT"})
    elif family == "PRICE_QUADRATIC_DIAGONAL":
        columns.extend((z[:, 0] ** 2, z[:, 1] ** 2, z[:, 2] ** 2))
        prediction.extend((((state[-1] - means) / scales) ** 2).tolist())
    return np.column_stack(columns), np.asarray(prediction), metadata


def safe_metrics(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mae": None, "rmse": None, "median": None, "bias": None}
    array = np.asarray(values, dtype=float)
    return {
        "mae": float(np.mean(np.abs(array))),
        "rmse": float(np.sqrt(np.mean(array * array))),
        "median": float(np.median(np.abs(array))),
        "bias": float(np.mean(array)),
    }


def main() -> int:
    price_rows = list(csv.DictReader(PRICE.open(newline="", encoding="utf-8")))
    source_rows = list(csv.DictReader(SOURCE.open(newline="", encoding="utf-8")))
    if len(price_rows) != len(source_rows) or len(price_rows) != 101221:
        raise RuntimeError("price/source authority changed")
    p = np.asarray([float(row["price"]) for row in price_rows])
    p1 = np.asarray([np.nan if row["primary_D1"] == "" else float(row["primary_D1"]) for row in price_rows])
    p2 = np.asarray([np.nan if row["primary_D2"] == "" else float(row["primary_D2"]) for row in price_rows])
    times = np.asarray([datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).timestamp() / 60.0 for row in price_rows])
    jp = np.full(len(p), np.nan)
    valid_delta = np.diff(times) > 0
    jp[1:][valid_delta] = np.diff(p2)[valid_delta] / np.diff(times)[valid_delta]
    strata = ["START"] + [transition_stratum(source_rows[index - 1], source_rows[index]) for index in range(1, len(source_rows))]

    candidate_results: dict[str, dict[str, Any]] = {}
    candidate_predictions: dict[str, dict[str, np.ndarray]] = {}
    for family in FAMILIES:
        for window in WINDOWS:
            model_id = f"{family}_W{window}"
            predictions_j = np.full(len(p), np.nan)
            predictions_p = np.full(len(p), np.nan)
            predictions_p1 = np.full(len(p), np.nan)
            predictions_p2 = np.full(len(p), np.nan)
            prediction_condition = np.full(len(p), np.nan)
            conditions: list[float] = []
            coefficients: list[np.ndarray] = []
            failed = unstable = singular = 0
            start = max(15, window)
            for index in range(start, len(p) - 1):
                train = slice(index - window + 1, index + 1)
                if not (
                    np.all(np.isfinite(p[train]))
                    and np.all(np.isfinite(p1[train]))
                    and np.all(np.isfinite(p2[train]))
                    and np.all(np.isfinite(jp[train]))
                ):
                    failed += 1
                    continue
                built = design_matrix(family, p[train], p1[train], p2[train], times[train])
                if built is None:
                    singular += 1
                    continue
                design, prediction, _ = built
                try:
                    condition = float(np.linalg.cond(design))
                    coefficient, _, rank, _ = np.linalg.lstsq(design, jp[train], rcond=None)
                except np.linalg.LinAlgError:
                    failed += 1
                    continue
                if rank != design.shape[1]:
                    singular += 1
                    continue
                if not math.isfinite(condition) or condition > CONDITION_LIMIT:
                    unstable += 1
                    continue
                estimated_j = float(prediction @ coefficient)
                h = times[index + 1] - times[index]
                if not math.isfinite(estimated_j) or h <= 0:
                    failed += 1
                    continue
                predictions_j[index] = estimated_j
                prediction_condition[index] = condition
                predictions_p2[index] = p2[index] + estimated_j * h
                predictions_p1[index] = p1[index] + p2[index] * h + 0.5 * estimated_j * h * h
                predictions_p[index] = p[index] + p1[index] * h + 0.5 * p2[index] * h * h + estimated_j * h**3 / 6.0
                conditions.append(condition)
                coefficients.append(coefficient)
            valid = np.isfinite(predictions_p2) & np.isfinite(p2[np.minimum(np.arange(len(p)) + 1, len(p) - 1)])
            valid[-1] = False
            indices = np.flatnonzero(valid)
            errors_p2 = [predictions_p2[index] - p2[index + 1] for index in indices]
            errors_p1 = [predictions_p1[index] - p1[index + 1] for index in indices]
            errors_p = [predictions_p[index] - p[index + 1] for index in indices]
            p2_metrics = safe_metrics(errors_p2)
            p1_metrics = safe_metrics(errors_p1)
            p_metrics = safe_metrics(errors_p)
            evolution_correct = [sign(predictions_p2[index] - p2[index]) == sign(p2[index + 1] - p2[index]) for index in indices]
            state_correct = [sign(predictions_p2[index]) == sign(p2[index + 1]) for index in indices]
            steps = [float(np.median(np.abs(right - left))) for left, right in zip(coefficients, coefficients[1:])]
            intraday_errors = [abs(predictions_p2[index] - p2[index + 1]) for index in indices if strata[index + 1] == "INTRASESSION_CONTINUOUS"]
            gap_errors = [abs(predictions_p2[index] - p2[index + 1]) for index in indices if strata[index + 1] != "INTRASESSION_CONTINUOUS"]
            candidate_results[model_id] = {
                "model_id": model_id, "model_family": family, "lookback": window,
                "parameter_count": 4 if family == "PRICE_LINEAR" else 5 if family == "PRICE_AFFINE_TIME" else 7,
                "valid_fits": len(indices), "failed_fits": failed, "unstable_fits": unstable,
                "singular_fits": singular,
                "median_condition_number": None if not conditions else float(np.median(conditions)),
                "p95_condition_number": None if not conditions else float(np.quantile(conditions, .95)),
                "coefficient_stability_median_step": None if not steps else float(np.median(steps)),
                "one_step_P2_MAE": p2_metrics["mae"], "one_step_P2_RMSE": p2_metrics["rmse"],
                "one_step_P2_median_absolute_error": p2_metrics["median"],
                "one_step_P2_signed_bias": p2_metrics["bias"],
                "one_step_P1_MAE": p1_metrics["mae"], "one_step_P_MAE": p_metrics["mae"],
                "P2_evolution_sign_accuracy": None if not evolution_correct else sum(evolution_correct) / len(evolution_correct),
                "curvature_state_transition_accuracy": None if not state_correct else sum(state_correct) / len(state_correct),
                "intraday_P2_MAE": None if not intraday_errors else float(np.mean(intraday_errors)),
                "session_gap_P2_MAE": None if not gap_errors else float(np.mean(gap_errors)),
            }
            candidate_predictions[model_id] = {"J": predictions_j, "P": predictions_p, "P1": predictions_p1, "P2": predictions_p2, "condition": prediction_condition}

    family_order = {family: index for index, family in enumerate(FAMILIES)}
    primary_id = min(
        candidate_results,
        key=lambda model_id: (
            -candidate_results[model_id]["valid_fits"],
            candidate_results[model_id]["failed_fits"] + candidate_results[model_id]["unstable_fits"] + candidate_results[model_id]["singular_fits"],
            candidate_results[model_id]["one_step_P2_MAE"],
            candidate_results[model_id]["one_step_P2_RMSE"],
            -candidate_results[model_id]["P2_evolution_sign_accuracy"],
            family_order[candidate_results[model_id]["model_family"]],
            candidate_results[model_id]["lookback"],
        ),
    )
    with (ROOT / "APTF_TEST_010_PRICE_LOCAL_DYNAMICS_COMPARISON_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMPARISON_COLUMNS); writer.writeheader()
        writer.writerows(candidate_results[key] for key in sorted(candidate_results))

    selected = candidate_predictions[primary_id]
    primary = candidate_results[primary_id]
    with (ROOT / "APTF_TEST_010_PRICE_ENGINE_EMISSIONS_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EMISSION_COLUMNS); writer.writeheader()
        emission_count = 0
        for index in range(len(p) - 1):
            if not math.isfinite(selected["P2"][index]):
                continue
            train = slice(index - primary["lookback"] + 1, index + 1)
            built = design_matrix(primary["model_family"], p[train], p1[train], p2[train], times[train])
            if built is None:
                raise RuntimeError("selected model reconstruction failed")
            design, _, scaling = built
            local_coefficient, _, rank, _ = np.linalg.lstsq(design, jp[train], rcond=None)
            if rank != design.shape[1]:
                raise RuntimeError("selected model reconstruction became singular")
            emission_count += 1
            errors = (
                selected["P"][index] - p[index + 1],
                selected["P1"][index] - p1[index + 1],
                selected["P2"][index] - p2[index + 1],
            )
            writer.writerow({
                "price_emission_id": f"PE{emission_count:06d}",
                "observation_index": index + 1, "timestamp": price_rows[index]["timestamp"],
                "session_id": parse_local(source_rows[index]["event_timestamp_local"]).date().isoformat(),
                "session_boundary_flag": str(strata[index] in ("WEEKEND_OR_HOLIDAY_GAP","OVERNIGHT_GAP","SESSION_TRANSITION")).lower(),
                "transition_stratum": strata[index + 1], "P": p[index], "P1": p1[index], "P2": p2[index],
                "J_P": selected["J"][index], "local_model_id": primary_id,
                "local_model_window": primary["lookback"], "model_condition": selected["condition"][index],
                "model_stability": "STABLE" if primary["unstable_fits"] == 0 else "MIXED",
                "predicted_next_P": selected["P"][index], "predicted_next_P1": selected["P1"][index],
                "predicted_next_P2": selected["P2"][index], "actual_next_P": p[index + 1],
                "actual_next_P1": p1[index + 1], "actual_next_P2": p2[index + 1],
                "prediction_error_P": errors[0], "prediction_error_P1": errors[1], "prediction_error_P2": errors[2],
                "P2_sign_prediction_correct": str(sign(selected["P2"][index] - p2[index]) == sign(p2[index + 1] - p2[index])).lower(),
                "curvature_state_transition_correct": str(sign(selected["P2"][index]) == sign(p2[index + 1])).lower(),
                "next_elapsed_minutes": times[index + 1] - times[index],
                "local_model_parameters_json": json.dumps(local_coefficient.tolist(), separators=(",", ":")),
                "local_model_scaling_json": json.dumps(scaling, sort_keys=True, separators=(",", ":")),
                "prediction_error_estimate_P2_MAE": primary["one_step_P2_MAE"],
                "valid_local_horizon_minutes": 1.0,
            })
    output = {
        "test_id": "APTF_TEST_010_PRICE_ENGINE_SELECTION_V0_1",
        "models_tested": sorted(candidate_results), "windows": list(WINDOWS),
        "primary_model_id": primary_id, "primary": primary,
        "price_emissions": emission_count, "future_observations_used_in_fit": 0,
        "selection_used_pnl": False, "selection_used_trading_labels": False,
        "structural_dynamics": {"dP_dt": "P1", "dP1_dt": "P2", "dP2_dt": "F_P"},
        "runge_kutta_used": False, "status": "PASS",
    }
    (ROOT / "APTF_TEST_010_PRICE_ENGINE_SELECTION_V0_1.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"primary_model": primary_id, "valid_forecasts": primary["valid_fits"], "P2_MAE": primary["one_step_P2_MAE"], "P2_RMSE": primary["one_step_P2_RMSE"], "sign_accuracy": primary["P2_evolution_sign_accuracy"], "unstable": primary["unstable_fits"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())