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
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv"
BASELINE_WINDOWS = (15, 30, 60)
DERIVATIVE_WINDOWS = (3, 5, 8, 15)
ACTIONABLE_START = 15

NORMALIZATION_COLUMNS = [
    "candidate", "method", "baseline_window", "valid_actionable", "missing_actionable",
    "numerical_failures", "minimum", "maximum", "mean", "median",
    "population_standard_deviation", "q01", "q05", "q10", "q25", "q50",
    "q75", "q90", "q95", "q99", "IQR", "raw_volume_spearman",
    "fixed15_V1_zero_crossings", "fixed15_V2_sign_changes",
    "fixed15_single_observation_V1_reversal_runs",
    "fixed15_single_observation_V1_reversal_percentage",
    "fixed15_median_V1_persistence", "regular_minute_residual_dispersion_IQR",
    "relative_ratio_ge_2", "relative_ratio_ge_5", "relative_ratio_ge_10",
]

DERIVATIVE_COLUMNS = [
    "window", "valid_observations", "V1_zero_crossings", "V2_sign_changes",
    "single_observation_V1_reversal_runs",
    "single_observation_V1_reversal_percentage", "median_V1_state_persistence",
    "median_V2_state_persistence", "V2_sign_change_rate", "numerical_fit_failures",
]


def sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def run_lengths(values: list[int]) -> list[int]:
    result: list[int] = []
    current = None
    length = 0
    for value in values:
        if value == 0:
            if length:
                result.append(length)
            current = None
            length = 0
        elif value == current:
            length += 1
        else:
            if length:
                result.append(length)
            current = value
            length = 1
    if length:
        result.append(length)
    return result


def causal_quadratic(times: np.ndarray, values: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray, int]:
    first = np.full(len(values), np.nan)
    second = np.full(len(values), np.nan)
    failures = 0
    for index in range(window - 1, len(values)):
        current = values[index - window + 1 : index + 1]
        if not np.all(np.isfinite(current)):
            continue
        x = times[index - window + 1 : index + 1] - times[index]
        design = np.column_stack((x * x, x, np.ones(window)))
        try:
            coefficients, _, rank, _ = np.linalg.lstsq(design, current, rcond=None)
        except np.linalg.LinAlgError:
            failures += 1
            continue
        if rank != 3 or not np.all(np.isfinite(coefficients)):
            failures += 1
            continue
        first[index] = coefficients[1]
        second[index] = 2.0 * coefficients[0]
    return first, second, failures


def derivative_metrics(first: np.ndarray, second: np.ndarray, failures: int) -> dict[str, Any]:
    valid = np.isfinite(first) & np.isfinite(second)
    valid[:ACTIONABLE_START] = False
    indices = np.flatnonzero(valid)
    first_signs = [sign(first[index]) for index in indices]
    second_signs = [sign(second[index]) for index in indices]
    first_runs = run_lengths(first_signs)
    second_runs = run_lengths(second_signs)
    crossings = 0
    second_changes = 0
    for index in indices:
        if index == 0 or not (np.isfinite(first[index - 1]) and np.isfinite(second[index - 1])):
            continue
        crossings += (first[index - 1] < 0 <= first[index]) or (first[index - 1] > 0 >= first[index])
        second_changes += sign(second[index - 1]) != sign(second[index])
    single = sum(length == 1 for length in first_runs)
    return {
        "valid_observations": int(valid.sum()),
        "V1_zero_crossings": int(crossings),
        "V2_sign_changes": int(second_changes),
        "single_observation_V1_reversal_runs": int(single),
        "single_observation_V1_reversal_percentage": 0.0 if not first_runs else 100.0 * single / len(first_runs),
        "median_V1_state_persistence": None if not first_runs else float(statistics.median(first_runs)),
        "median_V2_state_persistence": None if not second_runs else float(statistics.median(second_runs)),
        "V2_sign_change_rate": 0.0 if len(indices) < 2 else second_changes / (len(indices) - 1),
        "numerical_fit_failures": failures,
    }


def rolling_baseline(values: np.ndarray, window: int, method: str) -> np.ndarray:
    result = np.full(len(values), np.nan)
    for index in range(window - 1, len(values)):
        current = values[index - window + 1 : index + 1]
        result[index] = float(np.median(current)) if method == "MEDIAN" else float(np.mean(current))
    return result


def normalize(values: np.ndarray, baseline: np.ndarray, method: str) -> tuple[np.ndarray, np.ndarray]:
    result = np.full(len(values), np.nan)
    ratio = np.full(len(values), np.nan)
    baseline_valid = np.isfinite(baseline) & (baseline > 0)
    ratio[baseline_valid] = values[baseline_valid] / baseline[baseline_valid]
    if method == "LOG_ROLLING_MEDIAN_RELATIVE":
        valid = baseline_valid & (values > 0)
        result[valid] = np.log(ratio[valid])
    else:
        result[baseline_valid] = ratio[baseline_valid]
    return result, ratio


def distribution(values: np.ndarray) -> dict[str, float]:
    return {
        "minimum": float(np.min(values)), "maximum": float(np.max(values)),
        "mean": float(np.mean(values)), "median": float(np.median(values)),
        "population_standard_deviation": float(np.std(values)),
        **{f"q{int(p * 100):02d}": float(np.quantile(values, p, method="linear")) for p in (0.01,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.99)},
        "IQR": float(np.quantile(values, 0.75) - np.quantile(values, 0.25)),
    }


def regular_minute_dispersion(normalized: np.ndarray, sessions: list[str], minutes: list[str]) -> float:
    groups: dict[str, list[float]] = defaultdict(list)
    for index in range(ACTIONABLE_START, len(normalized)):
        if sessions[index] == "REGULAR" and math.isfinite(normalized[index]):
            groups[minutes[index]].append(float(normalized[index]))
    medians = np.asarray([np.median(values) for values in groups.values() if values], dtype=float)
    return float(np.quantile(medians, 0.75) - np.quantile(medians, 0.25))


def main() -> int:
    volumes: list[float] = []
    times: list[float] = []
    sessions: list[str] = []
    minutes: list[str] = []
    missing = 0
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = row["volume"]
            if raw == "":
                missing += 1
                volumes.append(float("nan"))
            else:
                volumes.append(float(raw))
            times.append(datetime.fromisoformat(row["event_timestamp_utc"].replace("Z", "+00:00")).timestamp() / 60.0)
            sessions.append(row["session_type"])
            minutes.append(row["minute_of_session"])
    volume = np.asarray(volumes, dtype=float)
    time = np.asarray(times, dtype=float)
    if len(volume) != 101221 or np.any(np.diff(time) <= 0):
        raise RuntimeError("source alignment/order authority changed")
    finite = volume[np.isfinite(volume)]
    raw_distribution = distribution(finite)
    session_values: dict[str, list[float]] = defaultdict(list)
    regular_minute_values: dict[str, list[float]] = defaultdict(list)
    for index, value in enumerate(volume):
        if not math.isfinite(value):
            continue
        session_values[sessions[index]].append(float(value))
        if sessions[index] == "REGULAR":
            regular_minute_values[minutes[index]].append(float(value))
    regular_minute_medians = np.asarray(
        [np.median(values) for values in regular_minute_values.values()], dtype=float
    )
    raw_audit = {
        "test_id": "APTF_TEST_009V_RAW_VOLUME_AUDIT_V0_1",
        "source_volume_field": "volume", "source_rows": len(volume),
        "valid_count": int(np.isfinite(volume).sum()), "missing_count": missing,
        "zero_count": int(np.sum(volume == 0)), **raw_distribution,
        "max_divided_by_median": raw_distribution["maximum"] / raw_distribution["median"],
        "q99_divided_by_median": raw_distribution["q99"] / raw_distribution["median"],
        "q95_divided_by_median": raw_distribution["q95"] / raw_distribution["median"],
        "q90_divided_by_median": raw_distribution["q90"] / raw_distribution["median"],
        "session_volume": {
            name: {"count": len(values), "median": float(np.median(values)), "mean": float(np.mean(values))}
            for name, values in sorted(session_values.items())
        },
        "regular_minute_of_session_structure": {
            "group_count": len(regular_minute_values),
            "minimum_group_count": min(len(values) for values in regular_minute_values.values()),
            "maximum_group_count": max(len(values) for values in regular_minute_values.values()),
            "minimum_group_median": float(np.min(regular_minute_medians)),
            "maximum_group_median": float(np.max(regular_minute_medians)),
            "group_median_IQR": float(np.quantile(regular_minute_medians, 0.75) - np.quantile(regular_minute_medians, 0.25)),
            "maximum_to_minimum_group_median": float(np.max(regular_minute_medians) / np.min(regular_minute_medians)),
        },
        "order_of_magnitude_variation_present": raw_distribution["maximum"] / raw_distribution["median"] >= 10,
        "extremes_removed": 0, "source_modified": False, "status": "PASS",
    }
    (ROOT / "APTF_TEST_009V_RAW_VOLUME_AUDIT_V0_1.json").write_text(
        json.dumps(raw_audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    candidates: dict[str, dict[str, Any]] = {}
    arrays: dict[str, np.ndarray] = {}
    ratios: dict[str, np.ndarray] = {}
    for window in BASELINE_WINDOWS:
        median_baseline = rolling_baseline(volume, window, "MEDIAN")
        mean_baseline = rolling_baseline(volume, window, "MEAN")
        for method, baseline in (
            ("ROLLING_MEDIAN_RATIO", median_baseline),
            ("ROLLING_MEAN_RATIO", mean_baseline),
            ("LOG_ROLLING_MEDIAN_RELATIVE", median_baseline),
        ):
            name = f"{method}_{window}"
            normalized, ratio = normalize(volume, baseline, method)
            arrays[name] = normalized
            ratios[name] = ratio
            scored = normalized[ACTIONABLE_START:]
            valid_mask = np.isfinite(scored)
            valid_values = scored[valid_mask]
            fixed_first, fixed_second, fixed_failures = causal_quadratic(time, normalized, 15)
            fixed = derivative_metrics(fixed_first, fixed_second, fixed_failures)
            source_values = volume[ACTIONABLE_START:][valid_mask]
            rank = float(spearmanr(source_values, valid_values).statistic)
            candidates[name] = {
                "candidate": name, "method": method, "baseline_window": window,
                "valid_actionable": int(valid_mask.sum()),
                "missing_actionable": int((~valid_mask).sum()),
                "numerical_failures": int((~valid_mask).sum()) + fixed_failures,
                **distribution(valid_values), "raw_volume_spearman": rank,
                "fixed15_V1_zero_crossings": fixed["V1_zero_crossings"],
                "fixed15_V2_sign_changes": fixed["V2_sign_changes"],
                "fixed15_single_observation_V1_reversal_runs": fixed["single_observation_V1_reversal_runs"],
                "fixed15_single_observation_V1_reversal_percentage": fixed["single_observation_V1_reversal_percentage"],
                "fixed15_median_V1_persistence": fixed["median_V1_state_persistence"],
                "regular_minute_residual_dispersion_IQR": regular_minute_dispersion(normalized, sessions, minutes),
                "relative_ratio_ge_2": int(np.sum(ratio[ACTIONABLE_START:] >= 2)),
                "relative_ratio_ge_5": int(np.sum(ratio[ACTIONABLE_START:] >= 5)),
                "relative_ratio_ge_10": int(np.sum(ratio[ACTIONABLE_START:] >= 10)),
            }

    comparison_path = ROOT / "APTF_TEST_009V_VOLUME_NORMALIZATION_COMPARISON_V0_1.csv"
    with comparison_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=NORMALIZATION_COLUMNS)
        writer.writeheader()
        writer.writerows(candidates[name] for name in sorted(candidates))
    primary_name = min(
        candidates,
        key=lambda name: (
            -candidates[name]["valid_actionable"], candidates[name]["numerical_failures"],
            candidates[name]["fixed15_single_observation_V1_reversal_percentage"],
            candidates[name]["fixed15_V2_sign_changes"] / max(1, candidates[name]["valid_actionable"] - 1),
            -candidates[name]["fixed15_median_V1_persistence"],
            candidates[name]["regular_minute_residual_dispersion_IQR"],
            -candidates[name]["raw_volume_spearman"], name,
        ),
    )
    selected = arrays[primary_name]
    selected_ratio = ratios[primary_name]
    selected_candidate = candidates[primary_name]

    derivatives: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    derivative_rows: dict[int, dict[str, Any]] = {}
    for window in DERIVATIVE_WINDOWS:
        first, second, failures = causal_quadratic(time, selected, window)
        derivatives[window] = (first, second)
        derivative_rows[window] = {"window": window, **derivative_metrics(first, second, failures)}
    derivative_path = ROOT / "APTF_TEST_009V_VOLUME_DERIVATIVE_WINDOW_COMPARISON_V0_1.csv"
    with derivative_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DERIVATIVE_COLUMNS)
        writer.writeheader()
        writer.writerows(derivative_rows[window] for window in DERIVATIVE_WINDOWS)
    primary_derivative_window = min(
        DERIVATIVE_WINDOWS,
        key=lambda window: (
            -derivative_rows[window]["valid_observations"],
            derivative_rows[window]["single_observation_V1_reversal_percentage"],
            derivative_rows[window]["V2_sign_change_rate"],
            -derivative_rows[window]["median_V1_state_persistence"], window,
        ),
    )
    primary_first, primary_second = derivatives[primary_derivative_window]
    scored = selected[ACTIONABLE_START:]
    finite_scored = scored[np.isfinite(scored)]
    q25, q75, q95 = [float(np.quantile(finite_scored, p)) for p in (0.25, 0.75, 0.95)]
    selection = {
        "test_id": "APTF_TEST_009V_VOLUME_SELECTION_V0_1",
        "normalization_candidates": sorted(candidates),
        "baseline_windows": list(BASELINE_WINDOWS),
        "time_of_day_normalization_tested": False,
        "time_of_day_structure_evaluated": True,
        "primary_V_N_candidate": primary_name,
        "primary_method": selected_candidate["method"],
        "primary_baseline_window": selected_candidate["baseline_window"],
        "selection_used_crossings": False, "selection_used_emitter_labels": False,
        "selection_used_pnl": False, "future_observations_used": 0,
        "primary_volume_derivative_window": primary_derivative_window,
        "volume_regime_boundaries": {"q25": q25, "q75": q75, "q95": q95},
        "relative_ratio_counts": {
            "ge_2": int(np.sum(selected_ratio[ACTIONABLE_START:] >= 2)),
            "ge_5": int(np.sum(selected_ratio[ACTIONABLE_START:] >= 5)),
            "ge_10": int(np.sum(selected_ratio[ACTIONABLE_START:] >= 10)),
        },
        "selected_V_N": [None if not math.isfinite(value) else float(value) for value in selected],
        "selected_relative_ratio": [None if not math.isfinite(value) else float(value) for value in selected_ratio],
        "selected_V1": [None if not math.isfinite(value) else float(value) for value in primary_first],
        "selected_V2": [None if not math.isfinite(value) else float(value) for value in primary_second],
        "status": "PASS",
    }
    (ROOT / "APTF_TEST_009V_VOLUME_SELECTION_V0_1.json").write_text(
        json.dumps(selection, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "raw_valid": raw_audit["valid_count"], "raw_zero": raw_audit["zero_count"],
        "raw_median": raw_audit["median"], "raw_max": raw_audit["maximum"],
        "primary_V_N": primary_name,
        "primary_volume_derivative_window": primary_derivative_window,
        "future_observations": 0,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())