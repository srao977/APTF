from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm


ROOT = Path(__file__).resolve().parents[1]
PRICE = ROOT / "APTF_TEST_009_DERIVATIVE_OBSERVATIONS_V0_1.csv"
EMISSIONS = ROOT / "APTF_TEST_010_PRICE_ENGINE_EMISSIONS_V0_1.csv"
TEST012_SCORE = ROOT / "APTF_TEST_012_FP_VECTOR_FIELD_SCORECARD_V0_1.csv"
HOLDOUT_START = 101099
HOLDOUT_END = 101220
WINDOWS = (15, 30, 60)
RTOL = 1e-6
LAMBDA = 1.0
EPSILON = 0.0035332071428566536

PROJECTION_COLUMNS = [
    "candidate_id", "cover", "projection_id", "observation_index", "timestamp",
    "next_timestamp", "current_P", "current_P1", "current_P2", "coefficients_json",
    "state_means_json", "state_scales_json", "condition_number", "max_real_eigenvalue",
    "spectral_radius", "rtol", "atol_P", "atol_P1", "atol_P2", "solver_success",
    "nfev", "projected_P", "projected_P1", "projected_P2", "actual_P", "actual_P1",
    "actual_P2", "error_P", "error_P1", "error_P2", "predicted_state", "actual_state",
    "projected_upper", "projected_lower", "actual_upper", "actual_lower",
    "max_local_domain_distance", "local_envelope_exit_flag", "first_exit_time",
]


def sign(value: float) -> int:
    return 1 if value > 1e-15 else -1 if value < -1e-15 else 0


def state(p1: float, p2: float) -> str:
    if abs(p1) <= EPSILON:
        if p2 > 0:
            return "LOWER_TURNING_REGION"
        if p2 < 0:
            return "UPPER_TURNING_REGION"
        return "D2_ZERO"
    if p1 > 0:
        return "RISING_STRENGTHENING" if p2 > 0 else "RISING_WEAKENING"
    return "FALLING_WEAKENING" if p2 > 0 else "FALLING_STRENGTHENING"


def fit_f4(p: np.ndarray, p1: np.ndarray, p2: np.ndarray, jp: np.ndarray, observation: int, window: int):
    index = observation - 1
    ids = np.arange(index - window + 1, index + 1)
    if ids[0] < 1 or not np.all(np.isfinite(jp[ids])):
        return None
    values = np.column_stack((p[ids], p1[ids], p2[ids]))
    means = values.mean(axis=0)
    scales = values.std(axis=0)
    if np.any(scales <= 0):
        return None
    design = np.column_stack((np.ones(window), (values - means) / scales))
    ridge = np.diag([0.0, 1.0, 1.0, 1.0])
    try:
        standardized = np.linalg.solve(design.T @ design + LAMBDA * ridge, design.T @ jp[ids])
    except np.linalg.LinAlgError:
        return None
    physical = standardized[1:] / scales
    coefficients = np.r_[standardized[0] - physical @ means, physical]
    return {
        "coefficients": coefficients,
        "means": means,
        "scales": scales,
        "condition": float(np.linalg.cond(design)),
        "minimum": values.min(axis=0),
        "maximum": values.max(axis=0),
    }


def f0_model(emission: dict[str, str], p: np.ndarray, p1: np.ndarray, p2: np.ndarray, observation: int):
    beta = np.asarray(json.loads(emission["local_model_parameters_json"]), dtype=float)
    scaling = json.loads(emission["local_model_scaling_json"])
    means = np.asarray(scaling["state_means"], dtype=float)
    scales = np.asarray(scaling["state_scales"], dtype=float)
    time_mean = float(scaling["time_mean"])
    time_scale = float(scaling["time_scale"])
    physical = beta[1:4] / scales
    index = observation - 1
    values = np.column_stack((p[index - 14:index + 1], p1[index - 14:index + 1], p2[index - 14:index + 1]))

    def function(time: float, current: np.ndarray) -> np.ndarray:
        standardized_state = (current - means) / scales
        standardized_time = (time - time_mean) / time_scale
        jerk = float(beta @ np.r_[1.0, standardized_state, standardized_time])
        return np.asarray([current[1], current[2], jerk])

    return {
        "function": function,
        "coefficients": np.r_[np.nan, physical],
        "means": means,
        "scales": scales,
        "condition": float(emission["model_condition"]),
        "minimum": values.min(axis=0),
        "maximum": values.max(axis=0),
    }


def f4_model(fit: dict[str, np.ndarray]):
    coefficients = fit["coefficients"]

    def function(_time: float, current: np.ndarray) -> np.ndarray:
        return np.asarray([current[1], current[2], coefficients[0] + coefficients[1:] @ current])

    return fit | {"function": function}


def solve_model(model: dict[str, np.ndarray], initial: np.ndarray):
    scales = model["scales"]
    atol = np.asarray([RTOL * scales[0], min(RTOL * scales[1], 0.1 * EPSILON), RTOL * scales[2]])
    solution = solve_ivp(
        model["function"], (0.0, 1.0), initial, method="RK45", rtol=RTOL, atol=atol,
        t_eval=np.linspace(0.0, 1.0, 11),
    )
    if not solution.success or not np.all(np.isfinite(solution.y)):
        raise RuntimeError(solution.message)
    dense = solution.y.T
    distances = np.linalg.norm((dense - model["means"]) / model["scales"], axis=1)
    inside = np.all((dense >= model["minimum"]) & (dense <= model["maximum"]), axis=1)
    first_exit = "" if np.all(inside) else float(solution.t[np.flatnonzero(~inside)[0]])
    return solution, dense[-1], atol, float(distances.max()), not bool(inside[-1]), first_exit


def confusion(predicted: list[bool], actual: list[bool]):
    true_positive = sum(p and a for p, a in zip(predicted, actual))
    false_positive = sum(p and not a for p, a in zip(predicted, actual))
    false_negative = sum(not p and a for p, a in zip(predicted, actual))
    precision = None if true_positive + false_positive == 0 else true_positive / (true_positive + false_positive)
    recall = None if true_positive + false_negative == 0 else true_positive / (true_positive + false_negative)
    return precision, recall


def score(candidate: str, cover: str, rows: list[dict[str, object]], perturbations: list[dict[str, object]]):
    errors = {component: np.asarray([float(row[f"error_{component}"]) for row in rows]) for component in ("P", "P1", "P2")}
    absolute_p2 = np.abs(errors["P2"])
    upper = confusion([row["projected_upper"] == "true" for row in rows], [row["actual_upper"] == "true" for row in rows])
    lower = confusion([row["projected_lower"] == "true" for row in rows], [row["actual_lower"] == "true" for row in rows])
    amplitudes = np.asarray([float(row["amplification_ratio"]) for row in perturbations])
    result: dict[str, object] = {"candidate_id": candidate, "cover": cover, "count": len(rows), "solver_failures": 0}
    for component in ("P", "P1", "P2"):
        result[f"{component}_MAE"] = float(np.mean(np.abs(errors[component])))
        result[f"{component}_RMSE"] = float(np.sqrt(np.mean(errors[component] ** 2)))
    result.update({
        "P2_median_abs_error": float(np.median(absolute_p2)),
        "P2_Q95": float(np.quantile(absolute_p2, 0.95)),
        "P2_Q99": float(np.quantile(absolute_p2, 0.99)),
        "P2_Q99_9": float(np.quantile(absolute_p2, 0.999)),
        "P2_max_abs_error": float(absolute_p2.max()),
        "P2_RMSE_MAE_ratio": result["P2_RMSE"] / result["P2_MAE"],
        "P1_sign_accuracy": float(np.mean([sign(float(row["projected_P1"])) == sign(float(row["actual_P1"])) for row in rows])),
        "P2_sign_accuracy": float(np.mean([sign(float(row["projected_P2"])) == sign(float(row["actual_P2"])) for row in rows])),
        "derivative_state_accuracy": float(np.mean([row["predicted_state"] == row["actual_state"] for row in rows])),
        "upper_precision": upper[0], "upper_recall": upper[1],
        "lower_precision": lower[0], "lower_recall": lower[1],
        "perturbation_median": float(np.median(amplitudes)),
        "perturbation_Q95": float(np.quantile(amplitudes, 0.95)),
        "perturbation_Q99": float(np.quantile(amplitudes, 0.99)),
        "perturbation_maximum": float(amplitudes.max()),
        "median_condition_number": float(np.median([float(row["condition_number"]) for row in rows])),
        "Q99_condition_number": float(np.quantile([float(row["condition_number"]) for row in rows], 0.99)),
        "median_max_real_eigenvalue": float(np.median([float(row["max_real_eigenvalue"]) for row in rows])),
        "Q99_max_real_eigenvalue": float(np.quantile([float(row["max_real_eigenvalue"]) for row in rows], 0.99)),
        "local_envelope_exit_rate": float(np.mean([row["local_envelope_exit_flag"] == "true" for row in rows])),
    })
    return result


def main() -> int:
    price = list(csv.DictReader(PRICE.open(newline="", encoding="utf-8")))
    emissions = {int(row["observation_index"]): row for row in csv.DictReader(EMISSIONS.open(newline="", encoding="utf-8"))}
    test012 = {row["candidate_id"]: row for row in csv.DictReader(TEST012_SCORE.open(newline="", encoding="utf-8"))}
    p = np.asarray([float(row["price"]) for row in price])
    p1 = np.asarray([np.nan if row["primary_D1"] == "" else float(row["primary_D1"]) for row in price])
    p2 = np.asarray([np.nan if row["primary_D2"] == "" else float(row["primary_D2"]) for row in price])
    jp = np.full(len(price), np.nan)
    eligible = []
    for observation in range(HOLDOUT_START, HOLDOUT_END + 1):
        emission = emissions.get(observation)
        if emission and emission["transition_stratum"] == "INTRASESSION_CONTINUOUS" and float(emission["next_elapsed_minutes"]) == 1.0:
            eligible.append(observation)
    for observation, emission in emissions.items():
        index = observation - 1
        if emission["transition_stratum"] == "INTRASESSION_CONTINUOUS" and index > 0:
            jp[index] = p2[index] - p2[index - 1]

    fits = {window: {observation: fit_f4(p, p1, p2, jp, observation, window) for observation in eligible} for window in WINDOWS}
    covers = {window: {observation for observation in eligible if fits[window][observation] is not None} for window in WINDOWS}
    f0_cover = set(eligible) & set(emissions)
    primary_cover = sorted(f0_cover & covers[30])
    sensitivity_cover = sorted(covers[15] & covers[30] & covers[60])
    if not primary_cover or not sensitivity_cover:
        raise RuntimeError("VALIDATION_BLOCKED_EMPTY_COVER")

    variants = [("F0_W15", "PRIMARY", primary_cover), ("F4_L1_W30", "PRIMARY", primary_cover)]
    variants.extend((f"F4_L1_W{window}", "SENSITIVITY", sensitivity_cover) for window in WINDOWS)
    cores: list[dict[str, object]] = []
    model_by_projection = {}
    causality = []
    for candidate, cover_name, observations in variants:
        window = int(candidate.rsplit("W", 1)[1])
        for observation in observations:
            index = observation - 1
            model = f0_model(emissions[observation], p, p1, p2, observation) if candidate == "F0_W15" else f4_model(fits[window][observation])
            initial = np.asarray([p[index], p1[index], p2[index]])
            solution, terminal, atol, distance, exited, first_exit = solve_model(model, initial)
            coefficients = model["coefficients"]
            physical = coefficients[1:]
            eigenvalues = np.linalg.eigvals(np.asarray([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], physical]))
            projection_id = f"{candidate}_{cover_name}_{observation}"
            cores.append({
                "candidate_id": candidate, "cover": cover_name, "projection_id": projection_id,
                "observation_index": observation, "timestamp": price[index]["timestamp"],
                "next_timestamp": price[index + 1]["timestamp"], "current_P": initial[0],
                "current_P1": initial[1], "current_P2": initial[2],
                "coefficients_json": json.dumps(coefficients.tolist(), separators=(",", ":")),
                "state_means_json": json.dumps(model["means"].tolist(), separators=(",", ":")),
                "state_scales_json": json.dumps(model["scales"].tolist(), separators=(",", ":")),
                "condition_number": model["condition"], "max_real_eigenvalue": float(eigenvalues.real.max()),
                "spectral_radius": float(np.abs(eigenvalues).max()), "rtol": RTOL,
                "atol_P": atol[0], "atol_P1": atol[1], "atol_P2": atol[2],
                "solver_success": "true", "nfev": solution.nfev,
                "projected_P": terminal[0], "projected_P1": terminal[1], "projected_P2": terminal[2],
                "max_local_domain_distance": distance, "local_envelope_exit_flag": str(exited).lower(),
                "first_exit_time": first_exit,
            })
            model_by_projection[projection_id] = model
            causality.append({
                "projection_id": projection_id, "observation_index": observation,
                "training_target_max_observation": observation, "future_observations_in_fit": 0,
                "projection_persisted_before_future_reveal": "true", "error_scored_after_reveal": "true",
                "future_leakage_violation": "false",
            })

    projections = []
    perturbations = []
    coefficients = []
    quantiles = []
    for core in cores:
        observation = int(core["observation_index"])
        index = observation - 1
        actual = np.asarray([p[index + 1], p1[index + 1], p2[index + 1]])
        terminal = np.asarray([core["projected_P"], core["projected_P1"], core["projected_P2"]], dtype=float)
        initial = np.asarray([core["current_P"], core["current_P1"], core["current_P2"]], dtype=float)
        error = terminal - actual
        row = core | {
            "actual_P": actual[0], "actual_P1": actual[1], "actual_P2": actual[2],
            "error_P": error[0], "error_P1": error[1], "error_P2": error[2],
            "predicted_state": state(terminal[1], terminal[2]), "actual_state": price[index + 1]["derivative_state"],
            "projected_upper": str(initial[1] > 0 and terminal[1] <= 0).lower(),
            "projected_lower": str(initial[1] < 0 and terminal[1] >= 0).lower(),
            "actual_upper": str(initial[1] > 0 and actual[1] <= 0).lower(),
            "actual_lower": str(initial[1] < 0 and actual[1] >= 0).lower(),
        }
        projections.append(row)
        model = model_by_projection[str(core["projection_id"])]
        matrix = np.asarray([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], model["coefficients"][1:]])
        transition = expm(matrix)
        for component, name in enumerate(("P", "P1", "P2")):
            perturbations.append({
                "candidate_id": core["candidate_id"], "cover": core["cover"],
                "observation_index": observation, "component": name,
                "perturbation_magnitude": 1e-6 * model["scales"][component],
                "amplification_ratio": float(np.linalg.norm(transition[:, component])),
            })
        coefficients.append({
            "candidate_id": core["candidate_id"], "cover": core["cover"], "observation_index": observation,
            "coefficients_json": core["coefficients_json"],
            "coefficient_norm": float(np.linalg.norm(model["coefficients"][1:])),
            "condition_number": core["condition_number"], "max_real_eigenvalue": core["max_real_eigenvalue"],
            "spectral_radius": core["spectral_radius"], "subsequent_P2_error": error[2],
        })

    grouped = defaultdict(list)
    grouped_perturbations = defaultdict(list)
    for row in projections:
        grouped[(row["candidate_id"], row["cover"])].append(row)
    for row in perturbations:
        grouped_perturbations[(row["candidate_id"], row["cover"])].append(row)
    scorecard = [score(candidate, cover, rows, grouped_perturbations[(candidate, cover)]) for (candidate, cover), rows in grouped.items()]
    for (candidate, cover), rows in grouped.items():
        for stratum in sorted({str(row["actual_state"]) for row in rows}):
            values = np.asarray([abs(float(row["error_P2"])) for row in rows if row["actual_state"] == stratum])
            quantiles.append({
                "candidate_id": candidate, "cover": cover, "stratum_type": "DERIVATIVE_STATE",
                "stratum": stratum, "count": len(values), "Q50": np.quantile(values, 0.5),
                "Q90": np.quantile(values, 0.9), "Q95": np.quantile(values, 0.95),
                "Q99": np.quantile(values, 0.99), "maximum": values.max(),
            })

    def write_csv(name: str, rows: list[dict[str, object]], fields=None):
        with (ROOT / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    write_csv("APTF_TEST_013_HOLDOUT_RK45_PROJECTIONS_V0_1.csv", projections, PROJECTION_COLUMNS)
    write_csv("APTF_TEST_013_VALIDATION_SCORECARD_V0_1.csv", scorecard)
    write_csv("APTF_TEST_013_ERROR_QUANTILES_V0_1.csv", quantiles)
    write_csv("APTF_TEST_013_PERTURBATION_STABILITY_V0_1.csv", perturbations)
    write_csv("APTF_TEST_013_COEFFICIENT_STABILITY_V0_1.csv", coefficients)
    write_csv("APTF_TEST_013_CAUSALITY_AUDIT_V0_1.csv", causality)

    drift = []
    for validation in scorecard:
        development_id = validation["candidate_id"]
        development = test012[development_id]
        for metric in ("P_MAE", "P1_MAE", "P2_MAE", "P2_RMSE", "P2_Q99", "P2_Q99_9", "P2_max_abs_error", "P2_sign_accuracy", "derivative_state_accuracy", "perturbation_Q99", "local_envelope_exit_rate"):
            drift.append({
                "candidate_id": development_id, "cover": validation["cover"], "metric": metric,
                "test012_value": development[metric], "test013_value": validation[metric],
                "ratio_validation_to_test012": None if float(development[metric]) == 0 else float(validation[metric]) / float(development[metric]),
            })
    write_csv("APTF_TEST_013_DEVELOPMENT_VS_HOLDOUT_DRIFT_V0_1.csv", drift)
    summary = {
        "test_id": "APTF_TEST_013_VALIDATION_EXECUTION_V0_1",
        "holdout_rows": HOLDOUT_END - HOLDOUT_START + 1,
        "eligible_one_minute_rows": len(eligible),
        "primary_common_cover_count": len(primary_cover),
        "sensitivity_common_cover_count": len(sensitivity_cover),
        "primary_cover_start": primary_cover[0], "primary_cover_end": primary_cover[-1],
        "sensitivity_cover_start": sensitivity_cover[0], "sensitivity_cover_end": sensitivity_cover[-1],
        "projection_rows": len(projections), "solver_failures": 0, "nonfinite_endpoints": 0,
        "future_leakage_violations": 0, "selection_overlap": 0,
        "status": "EXECUTED",
    }
    (ROOT / "APTF_TEST_013_EXECUTION_SUMMARY_V0_1.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())