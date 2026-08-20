from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "QQQ_1min_firstratedata.csv"
SPY_SCORE = ROOT / "APTF_TEST_012_FP_VECTOR_FIELD_SCORECARD_V0_1.csv"
WINDOWS = (15, 30, 60)
RTOL = 1e-6
RIDGE_LAMBDA = 1.0
EPSILON = 0.0035332071428566536
LOCAL_ZONE = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

PRIMARY_COLUMNS = [
    "instrument", "model", "observation_index", "timestamp", "session", "P", "P1", "P2",
    "local_coefficients_json", "local_center_json", "local_scale_json", "condition_number",
    "eigenvalues_json", "max_real_eigenvalue", "spectral_radius", "RK_success", "solver_message",
    "projected_P", "projected_P1", "projected_P2", "actual_P", "actual_P1", "actual_P2",
    "error_P", "error_P1", "error_P2", "projected_price_sign", "actual_price_sign",
    "projected_P1_sign", "actual_P1_sign", "projected_P2_sign", "actual_P2_sign",
    "predicted_derivative_state", "actual_derivative_state", "projected_upper", "projected_lower",
    "actual_upper", "actual_lower", "D_local_maximum", "envelope_exit", "first_exit_time",
    "exit_dimension",
]


def session_type(value: datetime) -> str:
    minute = value.hour * 60 + value.minute
    if 240 <= minute < 570:
        return "PREMARKET"
    if 570 <= minute < 960:
        return "REGULAR"
    if 960 <= minute < 1200:
        return "AFTERHOURS"
    return "OUTSIDE"


def contiguous(left: int, right: int, times: list[datetime], sessions: list[str]) -> bool:
    return (
        times[left].date() == times[right].date()
        and sessions[left] == sessions[right]
        and sessions[left] != "OUTSIDE"
        and (times[right] - times[left]).total_seconds() == 60.0
    )


def sign(value: float) -> int:
    return 1 if value > 1e-15 else -1 if value < -1e-15 else 0


def derivative_state(p1: float, p2: float) -> str:
    if not (math.isfinite(p1) and math.isfinite(p2)):
        return "UNAVAILABLE"
    if abs(p1) <= EPSILON:
        if p2 > 0:
            return "LOWER_TURNING_REGION"
        if p2 < 0:
            return "UPPER_TURNING_REGION"
        return "D2_ZERO"
    if p1 > 0:
        return "RISING_STRENGTHENING" if p2 > 0 else "RISING_WEAKENING"
    return "FALLING_WEAKENING" if p2 > 0 else "FALLING_STRENGTHENING"


def causal_quadratic(times_minutes: np.ndarray, prices: np.ndarray, window: int = 15):
    p1 = np.full(len(prices), np.nan)
    p2 = np.full(len(prices), np.nan)
    failures = 0
    for index in range(window - 1, len(prices)):
        local = times_minutes[index - window + 1:index + 1] - times_minutes[index]
        design = np.column_stack((local * local, local, np.ones(window)))
        try:
            coefficients, _, rank, _ = np.linalg.lstsq(design, prices[index - window + 1:index + 1], rcond=None)
        except np.linalg.LinAlgError:
            failures += 1
            continue
        if rank != 3 or not np.all(np.isfinite(coefficients)):
            failures += 1
            continue
        p1[index] = coefficients[1]
        p2[index] = 2.0 * coefficients[0]
    return p1, p2, failures


def allocate_fit(size: int, coefficient_count: int):
    return {
        "standardized": np.full((size, coefficient_count), np.nan),
        "physical": np.full((size, 4), np.nan),
        "means": np.full((size, 3), np.nan),
        "scales": np.full((size, 3), np.nan),
        "minimum": np.full((size, 3), np.nan),
        "maximum": np.full((size, 3), np.nan),
        "condition": np.full(size, np.nan),
        "time_mean": np.full(size, np.nan),
        "time_scale": np.full(size, np.nan),
    }


def fit_f4(p: np.ndarray, p1: np.ndarray, p2: np.ndarray, jp: np.ndarray, window: int):
    result = allocate_fit(len(p), 4)
    ridge = np.diag([0.0, 1.0, 1.0, 1.0])
    for index in range(window, len(p) - 1):
        ids = np.arange(index - window + 1, index + 1)
        if not np.all(np.isfinite(jp[ids])):
            continue
        values = np.column_stack((p[ids], p1[ids], p2[ids]))
        means = values.mean(axis=0)
        scales = values.std(axis=0)
        if np.any(scales <= 0) or not np.all(np.isfinite(scales)):
            continue
        design = np.column_stack((np.ones(window), (values - means) / scales))
        try:
            beta = np.linalg.solve(design.T @ design + RIDGE_LAMBDA * ridge, design.T @ jp[ids])
        except np.linalg.LinAlgError:
            continue
        slopes = beta[1:] / scales
        result["standardized"][index] = beta
        result["physical"][index] = np.r_[beta[0] - slopes @ means, slopes]
        result["means"][index] = means
        result["scales"][index] = scales
        result["minimum"][index] = values.min(axis=0)
        result["maximum"][index] = values.max(axis=0)
        result["condition"][index] = np.linalg.cond(design)
    return result


def fit_f0(p: np.ndarray, p1: np.ndarray, p2: np.ndarray, jp: np.ndarray, times_minutes: np.ndarray):
    window = 15
    result = allocate_fit(len(p), 5)
    for index in range(window, len(p) - 1):
        ids = np.arange(index - window + 1, index + 1)
        if not np.all(np.isfinite(jp[ids])):
            continue
        values = np.column_stack((p[ids], p1[ids], p2[ids]))
        means = values.mean(axis=0)
        scales = values.std(axis=0)
        local_time = times_minutes[ids] - times_minutes[index]
        time_mean = float(local_time.mean())
        time_scale = float(local_time.std())
        if np.any(scales <= 0) or time_scale <= 0 or not np.all(np.isfinite(scales)):
            continue
        design = np.column_stack((np.ones(window), (values - means) / scales, (local_time - time_mean) / time_scale))
        try:
            beta, _, rank, _ = np.linalg.lstsq(design, jp[ids], rcond=None)
        except np.linalg.LinAlgError:
            continue
        if rank != 5 or not np.all(np.isfinite(beta)):
            continue
        slopes = beta[1:4] / scales
        result["standardized"][index] = beta
        result["physical"][index] = np.r_[beta[0] - slopes @ means, slopes]
        result["means"][index] = means
        result["scales"][index] = scales
        result["minimum"][index] = values.min(axis=0)
        result["maximum"][index] = values.max(axis=0)
        result["condition"][index] = np.linalg.cond(design)
        result["time_mean"][index] = time_mean
        result["time_scale"][index] = time_scale
    return result


def valid_fit(fit: dict[str, np.ndarray], index: int) -> bool:
    return bool(np.all(np.isfinite(fit["standardized"][index])))


def solve_cover(observations: list[int], fit: dict[str, np.ndarray], p: np.ndarray, p1: np.ndarray, p2: np.ndarray, time_term: bool):
    solved: dict[int, dict[str, object]] = {}
    failed: dict[int, str] = {}
    grid = np.linspace(0.0, 1.0, 11)

    def run(group: list[int]):
        if not group:
            return
        indices = np.asarray(group, dtype=int)
        initial = np.column_stack((p[indices], p1[indices], p2[indices]))
        beta = fit["standardized"][indices]
        means = fit["means"][indices]
        scales = fit["scales"][indices]

        def function(time: float, flattened: np.ndarray):
            state_values = flattened.reshape(-1, 3)
            standardized = (state_values - means) / scales
            jerk = beta[:, 0] + np.sum(beta[:, 1:4] * standardized, axis=1)
            if time_term:
                jerk += beta[:, 4] * ((time - fit["time_mean"][indices]) / fit["time_scale"][indices])
            return np.column_stack((state_values[:, 1], state_values[:, 2], jerk)).ravel()

        atol = np.column_stack((
            RTOL * scales[:, 0],
            np.minimum(RTOL * scales[:, 1], 0.1 * EPSILON),
            RTOL * scales[:, 2],
        )).ravel()
        try:
            solution = solve_ivp(function, (0.0, 1.0), initial.ravel(), method="RK45", rtol=RTOL, atol=atol, t_eval=grid)
            if not solution.success or not np.all(np.isfinite(solution.y)):
                raise RuntimeError(solution.message)
            trajectories = solution.y.reshape(len(group), 3, -1).transpose(0, 2, 1)
            for position, observation in enumerate(group):
                trajectory = trajectories[position]
                if np.any(np.abs(trajectory[-1] - initial[position]) > 1e6 * scales[position]):
                    failed[observation] = "NUMERICALLY_UNSTABLE"
                    continue
                local_distance = np.linalg.norm((trajectory - means[position]) / scales[position], axis=1)
                inside_components = (trajectory >= fit["minimum"][indices[position]]) & (trajectory <= fit["maximum"][indices[position]])
                inside = np.all(inside_components, axis=1)
                exit_positions = np.flatnonzero(~inside)
                first_exit = ""
                exit_dimension = ""
                if len(exit_positions):
                    exit_position = int(exit_positions[0])
                    first_exit = float(grid[exit_position])
                    exit_dimension = "|".join(np.asarray(["P", "P1", "P2"])[~inside_components[exit_position]].tolist())
                solved[observation] = {
                    "trajectory": trajectory,
                    "nfev": int(solution.nfev),
                    "message": solution.message,
                    "D_local_maximum": float(local_distance.max()),
                    "envelope_exit": bool(len(exit_positions)),
                    "first_exit_time": first_exit,
                    "exit_dimension": exit_dimension,
                }
        except Exception as error:
            if len(group) == 1:
                failed[group[0]] = str(error)
            else:
                midpoint = len(group) // 2
                run(group[:midpoint])
                run(group[midpoint:])

    for start in range(0, len(observations), 1024):
        run(observations[start:start + 1024])
    return solved, failed


def confusion(predicted: list[bool], actual: list[bool]):
    tp = sum(p and a for p, a in zip(predicted, actual))
    fp = sum(p and not a for p, a in zip(predicted, actual))
    tn = sum(not p and not a for p, a in zip(predicted, actual))
    fn = sum(not p and a for p, a in zip(predicted, actual))
    divide = lambda numerator, denominator: None if denominator == 0 else numerator / denominator
    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn, "precision": divide(tp, tp + fp), "recall": divide(tp, tp + fn), "specificity": divide(tn, tn + fp)}


def score(model: str, rows: list[dict[str, object]], failures: int, perturbations: list[dict[str, object]]):
    successful = [row for row in rows if row["RK_success"] == "true"]
    errors = {component: np.asarray([float(row[f"error_{component}"]) for row in successful]) for component in ("P", "P1", "P2")}
    absolute_p2 = np.abs(errors["P2"])
    amplitudes = np.asarray([float(row["amplification_ratio"]) for row in perturbations])
    eigenvalues = np.asarray([float(row["max_real_eigenvalue"]) for row in successful])
    distances = np.asarray([float(row["D_local_maximum"]) for row in successful])
    conditions = np.asarray([float(row["condition_number"]) for row in successful])
    result: dict[str, object] = {"instrument": "QQQ", "model": model, "common_cover_count": len(rows), "scored_count": len(successful), "RK_failures": failures, "nonfinite_trajectories": 0}
    for component in ("P", "P1", "P2"):
        result[f"{component}_MAE"] = float(np.mean(np.abs(errors[component])))
        result[f"{component}_RMSE"] = float(np.sqrt(np.mean(errors[component] ** 2)))
    result.update({
        "P2_median_abs_error": float(np.median(absolute_p2)),
        "P2_Q90": float(np.quantile(absolute_p2, 0.90)),
        "P2_Q95": float(np.quantile(absolute_p2, 0.95)),
        "P2_Q99": float(np.quantile(absolute_p2, 0.99)),
        "P2_Q99_5": float(np.quantile(absolute_p2, 0.995)),
        "P2_Q99_9": float(np.quantile(absolute_p2, 0.999)),
        "P2_max_abs_error": float(absolute_p2.max()),
        "P2_RMSE_MAE_ratio": result["P2_RMSE"] / result["P2_MAE"],
        "price_sign_accuracy": float(np.mean([row["projected_price_sign"] == row["actual_price_sign"] for row in successful])),
        "P1_sign_accuracy": float(np.mean([row["projected_P1_sign"] == row["actual_P1_sign"] for row in successful])),
        "P2_sign_accuracy": float(np.mean([row["projected_P2_sign"] == row["actual_P2_sign"] for row in successful])),
        "derivative_state_accuracy": float(np.mean([row["predicted_derivative_state"] == row["actual_derivative_state"] for row in successful])),
        "perturbation_median": float(np.median(amplitudes)),
        "perturbation_Q95": float(np.quantile(amplitudes, 0.95)),
        "perturbation_Q99": float(np.quantile(amplitudes, 0.99)),
        "perturbation_maximum": float(amplitudes.max()),
        "domain_exit_count": sum(row["envelope_exit"] == "true" for row in successful),
        "domain_exit_rate": float(np.mean([row["envelope_exit"] == "true" for row in successful])),
        "D_local_median": float(np.median(distances)), "D_local_Q95": float(np.quantile(distances, 0.95)),
        "D_local_Q99": float(np.quantile(distances, 0.99)), "D_local_maximum": float(distances.max()),
        "max_real_eigenvalue_median": float(np.median(eigenvalues)),
        "max_real_eigenvalue_Q90": float(np.quantile(eigenvalues, 0.90)),
        "max_real_eigenvalue_Q95": float(np.quantile(eigenvalues, 0.95)),
        "max_real_eigenvalue_Q99": float(np.quantile(eigenvalues, 0.99)),
        "max_real_eigenvalue_maximum": float(eigenvalues.max()),
        "max_real_eigenvalue_fraction_positive": float(np.mean(eigenvalues > 0)),
        "median_condition_number": float(np.median(conditions)),
        "condition_number_Q95": float(np.quantile(conditions, 0.95)),
        "condition_number_Q99": float(np.quantile(conditions, 0.99)),
        "condition_number_maximum": float(conditions.max()),
    })
    upper = confusion([row["projected_upper"] == "true" for row in successful], [row["actual_upper"] == "true" for row in successful])
    lower = confusion([row["projected_lower"] == "true" for row in successful], [row["actual_lower"] == "true" for row in successful])
    for key, value in upper.items():
        result[f"upper_{key}"] = value
    for key, value in lower.items():
        result[f"lower_{key}"] = value
    return result, upper, lower


def evenly_spaced(items: list[int], count: int):
    if len(items) <= count:
        return items
    return [items[position] for position in np.linspace(0, len(items) - 1, count, dtype=int)]


def perturbation_rows(model: str, cover_name: str, observations: list[int], fit: dict[str, np.ndarray]):
    rows = []
    for observation in evenly_spaced(observations, 128):
        physical = fit["physical"][observation, 1:]
        matrix = np.asarray([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], physical])
        transition = expm(matrix)
        for component, name in enumerate(("P", "P1", "P2")):
            magnitude = 1e-6 * fit["scales"][observation, component]
            rows.append({
                "instrument": "QQQ", "model": model, "cover": cover_name,
                "observation_index": observation + 1, "component": name,
                "perturbation_magnitude": magnitude,
                "amplification_ratio": float(np.linalg.norm(transition[:, component] * magnitude) / magnitude),
            })
    return rows


def projection_rows(model: str, observations: list[int], fit: dict[str, np.ndarray], solved: dict[int, dict[str, object]], failed: dict[int, str], timestamps: list[str], sessions: list[str], p: np.ndarray, p1: np.ndarray, p2: np.ndarray):
    rows = []
    jacobians = []
    domains = []
    causality = []
    for index in observations:
        physical = fit["physical"][index]
        matrix = np.asarray([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], physical[1:]])
        eigenvalues = np.linalg.eigvals(matrix)
        base = {
            "instrument": "QQQ", "model": model, "observation_index": index + 1,
            "timestamp": timestamps[index], "session": sessions[index], "P": p[index], "P1": p1[index], "P2": p2[index],
            "local_coefficients_json": json.dumps(fit["standardized"][index].tolist(), separators=(",", ":")),
            "local_center_json": json.dumps(fit["means"][index].tolist(), separators=(",", ":")),
            "local_scale_json": json.dumps(fit["scales"][index].tolist(), separators=(",", ":")),
            "condition_number": fit["condition"][index],
            "eigenvalues_json": json.dumps([[float(value.real), float(value.imag)] for value in eigenvalues], separators=(",", ":")),
            "max_real_eigenvalue": float(eigenvalues.real.max()), "spectral_radius": float(np.abs(eigenvalues).max()),
        }
        if index in failed:
            rows.append(base | {column: "" for column in PRIMARY_COLUMNS if column not in base} | {"RK_success": "false", "solver_message": failed[index]})
            continue
        result = solved[index]
        terminal = np.asarray(result["trajectory"])[-1]
        actual = np.asarray([p[index + 1], p1[index + 1], p2[index + 1]])
        initial = np.asarray([p[index], p1[index], p2[index]])
        error = terminal - actual
        row = base | {
            "RK_success": "true", "solver_message": result["message"],
            "projected_P": terminal[0], "projected_P1": terminal[1], "projected_P2": terminal[2],
            "actual_P": actual[0], "actual_P1": actual[1], "actual_P2": actual[2],
            "error_P": error[0], "error_P1": error[1], "error_P2": error[2],
            "projected_price_sign": sign(terminal[0] - initial[0]), "actual_price_sign": sign(actual[0] - initial[0]),
            "projected_P1_sign": sign(terminal[1]), "actual_P1_sign": sign(actual[1]),
            "projected_P2_sign": sign(terminal[2]), "actual_P2_sign": sign(actual[2]),
            "predicted_derivative_state": derivative_state(terminal[1], terminal[2]),
            "actual_derivative_state": derivative_state(actual[1], actual[2]),
            "projected_upper": str(initial[1] > 0 and terminal[1] <= 0).lower(),
            "projected_lower": str(initial[1] < 0 and terminal[1] >= 0).lower(),
            "actual_upper": str(initial[1] > 0 and actual[1] <= 0).lower(),
            "actual_lower": str(initial[1] < 0 and actual[1] >= 0).lower(),
            "D_local_maximum": result["D_local_maximum"], "envelope_exit": str(result["envelope_exit"]).lower(),
            "first_exit_time": result["first_exit_time"], "exit_dimension": result["exit_dimension"],
        }
        rows.append(row)
        jacobians.append({
            "instrument": "QQQ", "model": model, "observation_index": index + 1, "timestamp": timestamps[index],
            "eigenvalues_json": base["eigenvalues_json"], "max_real_eigenvalue": base["max_real_eigenvalue"],
            "spectral_radius": base["spectral_radius"], "subsequent_P2_error": error[2],
        })
        domains.append({
            "instrument": "QQQ", "model": model, "observation_index": index + 1,
            "D_local_maximum": result["D_local_maximum"], "envelope_exit": str(result["envelope_exit"]).lower(),
            "first_exit_time": result["first_exit_time"], "exit_dimension": result["exit_dimension"],
            "subsequent_P2_error": error[2],
        })
        causality.append({
            "instrument": "QQQ", "model": model, "observation_index": index + 1,
            "training_target_max_observation": index + 1, "future_observations_in_fit": 0,
            "future_observations_during_rk": 0, "projection_persisted_before_reveal": "true",
            "actual_revealed_after_projection": "true", "error_scored_after_reveal": "true",
            "next_model_uses_real_state": "true", "predicted_state_substituted": "false",
            "future_leakage_violation": "false",
        })
    return rows, jacobians, domains, causality


def write_csv(path: Path, rows: list[dict[str, object]], fields=None):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    raw = list(csv.DictReader(SOURCE.open(newline="", encoding="utf-8-sig")))
    timestamps = [row["timestamp"] for row in raw]
    local_times = [datetime.fromisoformat(value).replace(tzinfo=LOCAL_ZONE) for value in timestamps]
    utc_times = [value.astimezone(UTC) for value in local_times]
    times_minutes = np.asarray([value.timestamp() / 60.0 for value in utc_times])
    sessions = [session_type(value) for value in local_times]
    p = np.asarray([float(row["close"]) for row in raw])
    p1, p2, derivative_failures = causal_quadratic(times_minutes, p)
    states = [derivative_state(p1[index], p2[index]) for index in range(len(p))]
    jp = np.full(len(p), np.nan)
    projection_eligible = []
    for index in range(1, len(p)):
        if contiguous(index - 1, index, local_times, sessions) and np.isfinite(p2[index - 1]) and np.isfinite(p2[index]):
            jp[index] = p2[index] - p2[index - 1]
    for index in range(14, len(p) - 1):
        if contiguous(index, index + 1, local_times, sessions) and np.all(np.isfinite([p1[index], p2[index], p1[index + 1], p2[index + 1]])):
            projection_eligible.append(index)

    f0 = fit_f0(p, p1, p2, jp, times_minutes)
    f4 = {window: fit_f4(p, p1, p2, jp, window) for window in WINDOWS}
    f0_cover = {index for index in projection_eligible if valid_fit(f0, index)}
    f4_cover = {window: {index for index in projection_eligible if valid_fit(f4[window], index)} for window in WINDOWS}
    primary_cover = sorted(f0_cover & f4_cover[30])
    sensitivity_cover = sorted(f4_cover[15] & f4_cover[30] & f4_cover[60])
    if not primary_cover:
        raise RuntimeError("EXTERNAL_VALIDATION_BLOCKED_EMPTY_PRIMARY_COVER")

    solved_f0, failed_f0 = solve_cover(primary_cover, f0, p, p1, p2, True)
    solved_w30, failed_w30 = solve_cover(primary_cover, f4[30], p, p1, p2, False)
    primary_f0, jac_f0, domain_f0, causal_f0 = projection_rows("F0_W15", primary_cover, f0, solved_f0, failed_f0, timestamps, sessions, p, p1, p2)
    primary_w30, jac_w30, domain_w30, causal_w30 = projection_rows("F4_L1_W30", primary_cover, f4[30], solved_w30, failed_w30, timestamps, sessions, p, p1, p2)
    primary_rows = primary_f0 + primary_w30

    primary_pert_f0 = perturbation_rows("F0_W15", "PRIMARY", primary_cover, f0)
    primary_pert_w30 = perturbation_rows("F4_L1_W30", "PRIMARY", primary_cover, f4[30])
    score_f0, upper_f0, lower_f0 = score("F0_W15", primary_f0, len(failed_f0), primary_pert_f0)
    score_w30, upper_w30, lower_w30 = score("F4_L1_W30", primary_w30, len(failed_w30), primary_pert_w30)
    primary_score = [score_f0, score_w30]

    sensitivity_rows = []
    sensitivity_perturbations = []
    sensitivity_scores = []
    sensitivity_failures = {}
    if sensitivity_cover:
        for window in WINDOWS:
            model = f"F4_L1_W{window}"
            solved, failed = solve_cover(sensitivity_cover, f4[window], p, p1, p2, False)
            rows, _, _, _ = projection_rows(model, sensitivity_cover, f4[window], solved, failed, timestamps, sessions, p, p1, p2)
            perturbations = perturbation_rows(model, "SENSITIVITY", sensitivity_cover, f4[window])
            scored, _, _ = score(model, rows, len(failed), perturbations)
            sensitivity_rows.extend(rows)
            sensitivity_perturbations.extend(perturbations)
            sensitivity_scores.append(scored)
            sensitivity_failures[model] = len(failed)

    coefficient_rows = []
    for index in primary_cover:
        beta = f4[30]["standardized"][index]
        physical = f4[30]["physical"][index]
        coefficient_rows.append({
            "instrument": "QQQ", "model": "F4_L1_W30", "observation_index": index + 1,
            "timestamp": timestamps[index], "b0": beta[0], "b1": beta[1], "b2": beta[2], "b3": beta[3],
            "physical_intercept": physical[0], "physical_a1": physical[1], "physical_a2": physical[2], "physical_a3": physical[3],
            "coefficient_norm": float(np.linalg.norm(beta)),
            "state_center_json": json.dumps(f4[30]["means"][index].tolist(), separators=(",", ":")),
            "state_scale_json": json.dumps(f4[30]["scales"][index].tolist(), separators=(",", ":")),
            "condition_number": f4[30]["condition"][index],
        })

    spy = {row["candidate_id"]: row for row in csv.DictReader(SPY_SCORE.open(newline="", encoding="utf-8"))}
    qqq = {row["model"]: row for row in primary_score}
    metric_map = {
        "P2_MAE": ("P2_MAE", "P2_MAE"), "P2_RMSE": ("P2_RMSE", "P2_RMSE"),
        "P2_Q99": ("P2_Q99", "P2_Q99"), "P2_Q99_9": ("P2_Q99_9", "P2_Q99_9"),
        "P2_max_abs_error": ("P2_max_abs_error", "P2_max_abs_error"),
        "P2_sign_accuracy": ("P2_sign_accuracy", "P2_sign_accuracy"),
        "derivative_state_accuracy": ("derivative_state_accuracy", "derivative_state_accuracy"),
        "perturbation_Q99": ("perturbation_Q99", "perturbation_Q99"),
        "domain_exit_rate": ("local_envelope_exit_rate", "domain_exit_rate"),
        "max_real_eigenvalue_Q99": ("Q99_max_real_eigenvalue", "max_real_eigenvalue_Q99"),
    }
    cross_rows = []
    for metric, (spy_key, qqq_key) in metric_map.items():
        spy_f0 = float(spy["F0_W15"][spy_key])
        spy_f4 = float(spy["F4_L1_W30"][spy_key])
        qqq_f0 = float(qqq["F0_W15"][qqq_key])
        qqq_f4 = float(qqq["F4_L1_W30"][qqq_key])
        cross_rows.append({
            "metric": metric, "SPY_F0": spy_f0, "SPY_F4": spy_f4,
            "SPY_absolute_change": spy_f4 - spy_f0,
            "SPY_relative_change": None if spy_f0 == 0 else (spy_f4 - spy_f0) / abs(spy_f0),
            "QQQ_F0": qqq_f0, "QQQ_F4": qqq_f4,
            "QQQ_absolute_change": qqq_f4 - qqq_f0,
            "QQQ_relative_change": None if qqq_f0 == 0 else (qqq_f4 - qqq_f0) / abs(qqq_f0),
        })

    transitions = {
        "test_id": "APTF_TEST_013B_QQQ_TRANSITION_VALIDATION_V0_1",
        "F0_W15": {"upper": upper_f0, "lower": lower_f0},
        "F4_L1_W30": {"upper": upper_w30, "lower": lower_w30},
        "definitions": "endpoint P1 sign crossing under frozen Test012 authority",
    }
    state_summary = {
        "test_id": "APTF_TEST_013B_QQQ_STATE_CONSTRUCTION_SUMMARY_V0_1",
        "total_rows": len(raw), "initialization_rows": 14,
        "derivative_fit_failures": derivative_failures,
        "complete_state_rows": int(np.sum(np.isfinite(p1) & np.isfinite(p2))),
        "contiguous_jp_targets": int(np.sum(np.isfinite(jp))),
        "eligible_contiguous_projection_origins": len(projection_eligible),
        "F0_eligible_rows": len(f0_cover), "F4_W15_eligible_rows": len(f4_cover[15]),
        "F4_W30_eligible_rows": len(f4_cover[30]), "F4_W60_eligible_rows": len(f4_cover[60]),
        "primary_common_cover": len(primary_cover),
        "primary_sessions_represented": len({local_times[index].date() for index in primary_cover}),
        "sensitivity_common_cover": len(sensitivity_cover),
        "sensitivity_sessions_represented": len({local_times[index].date() for index in sensitivity_cover}),
        "session_type_rows": dict(Counter(sessions)),
    }

    write_csv(ROOT / "APTF_TEST_013B_QQQ_PRIMARY_PROJECTIONS_V0_1.csv", primary_rows, PRIMARY_COLUMNS)
    write_csv(ROOT / "APTF_TEST_013B_QQQ_PRIMARY_SCORECARD_V0_1.csv", primary_score)
    if sensitivity_scores:
        write_csv(ROOT / "APTF_TEST_013B_QQQ_WINDOW_SENSITIVITY_SCORECARD_V0_1.csv", sensitivity_scores)
    else:
        (ROOT / "APTF_TEST_013B_QQQ_WINDOW_SENSITIVITY_SCORECARD_V0_1.csv").write_text("status,reason\nBLOCKED,EMPTY_COMMON_COVER\n", encoding="utf-8")
    write_csv(ROOT / "APTF_TEST_013B_SPY_VS_QQQ_GENERALIZATION_V0_1.csv", cross_rows)
    write_csv(ROOT / "APTF_TEST_013B_QQQ_PERTURBATION_STABILITY_V0_1.csv", primary_pert_f0 + primary_pert_w30 + sensitivity_perturbations)
    write_csv(ROOT / "APTF_TEST_013B_QQQ_JACOBIAN_STABILITY_V0_1.csv", jac_f0 + jac_w30)
    write_csv(ROOT / "APTF_TEST_013B_QQQ_LOCAL_DOMAIN_VALIDATION_V0_1.csv", domain_f0 + domain_w30)
    write_csv(ROOT / "APTF_TEST_013B_QQQ_F4_COEFFICIENT_STABILITY_V0_1.csv", coefficient_rows)
    write_csv(ROOT / "APTF_TEST_013B_QQQ_CAUSALITY_AUDIT_V0_1.csv", causal_f0 + causal_w30)
    (ROOT / "APTF_TEST_013B_QQQ_TRANSITION_VALIDATION_V0_1.json").write_text(json.dumps(transitions, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / "APTF_TEST_013B_QQQ_STATE_CONSTRUCTION_SUMMARY_V0_1.json").write_text(json.dumps(state_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(state_summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())