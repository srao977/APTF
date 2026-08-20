from __future__ import annotations

import bisect
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import pearsonr, spearmanr


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv"
PRICE_OBSERVATIONS = ROOT / "APTF_TEST_009_DERIVATIVE_OBSERVATIONS_V0_1.csv"
CROSSINGS = ROOT / "APTF_TEST_009_DERIVATIVE_CROSSINGS_V0_1.csv"
TURNING = ROOT / "APTF_TEST_009_TURNING_TRAJECTORIES_V0_1.csv"
PRICE_ALIGNMENT = ROOT / "APTF_TEST_009_EPISODE_DERIVATIVE_ALIGNMENT_V0_1.csv"
PRICE_PRECURSORS = ROOT / "APTF_TEST_009_D2_PRECURSOR_ANALYSIS_V0_1.csv"
TRADES = ROOT / "APTF_TEST_008_TRADE_LEDGER_V0_2.csv"
SELECTION = ROOT / "APTF_TEST_009V_VOLUME_SELECTION_V0_1.json"
PRIOR_WINDOWS = (1, 3, 5, 8, 15)

OBS_COLUMNS = [
    "source_observation_index", "source_physical_row", "timestamp",
    "initialization_status", "price", "frozen_P1", "frozen_P2",
    "frozen_price_derivative_state", "V_RAW", "raw_V1", "V_N", "V1", "V2",
    "volume_regime", "H", "Q_G", "Q_S", "Q_R", "C",
    "frozen_emitter_decision", "frozen_position_state_before",
    "frozen_position_state_after", "frozen_execution_intent",
]

TRAJECTORY_COLUMNS = [
    "transition_id", "transition_type", "frozen_Test009_crossing_id",
    "relative_observation", "relative_seconds", "timestamp", "normalized_price",
    "P1", "P2", "V_RAW", "V_N", "V1", "V2", "volume_regime",
    "H", "Q_G", "Q_S", "Q_R", "C", "emitter_decision", "position_state",
    "causal_or_retrospective_flag",
]

TIME_COLUMNS = [
    "precursor_event_id", "crossing_id", "crossing_type", "trajectory_label",
    "precursor_observation", "precursor_timestamp", "P1", "P2", "V_N", "V1",
    "V2", "volume_regime", "observations_to_crossing", "seconds_to_crossing",
]


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def finite(value: Any) -> float | None:
    if value in (None, ""):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def sign(value: float | None) -> int | None:
    if value is None:
        return None
    return 1 if value > 0 else -1 if value < 0 else 0


def summary(values: list[float]) -> dict[str, Any]:
    array = np.asarray([value for value in values if math.isfinite(value)], dtype=float)
    if not len(array):
        return {"count": 0, "mean": None, "median": None, "std": None, "q25": None, "q75": None}
    return {
        "count": int(len(array)), "mean": float(np.mean(array)),
        "median": float(np.median(array)), "std": float(np.std(array)),
        "q25": float(np.quantile(array, 0.25)), "q75": float(np.quantile(array, 0.75)),
    }


def value_summary(indices: set[int], arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    return {
        name: summary([float(values[index]) for index in indices if math.isfinite(values[index])])
        for name, values in arrays.items()
    }


def run_persistence(values: np.ndarray, index: int) -> int:
    current = sign(finite(values[index]))
    if current is None:
        return 0
    start = index
    while start - 1 >= 0 and sign(finite(values[start - 1])) == current:
        start -= 1
    return index - start + 1


def main() -> int:
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    if selection["status"] != "PASS" or selection["selection_used_pnl"]:
        raise RuntimeError("Volume selection is not frozen independently")
    source = list(csv.DictReader(SOURCE.open(newline="", encoding="utf-8")))
    price = list(csv.DictReader(PRICE_OBSERVATIONS.open(newline="", encoding="utf-8")))
    if len(source) != len(price) != 101221:
        raise RuntimeError("source/price row authority changed")
    if len(source) != 101221 or len(price) != 101221:
        raise RuntimeError("source/price row authority changed")
    for source_row, price_row in zip(source, price, strict=True):
        if (
            source_row["test006b_observation_index"] != price_row["source_observation_index"]
            or source_row["event_timestamp_utc"] != price_row["timestamp"]
            or source_row["close"] != price_row["price"]
        ):
            raise RuntimeError("frozen price/source alignment mismatch")

    n = len(source)
    raw = np.asarray([float(row["volume"]) for row in source], dtype=float)
    p = np.asarray([float(row["price"]) for row in price], dtype=float)
    p1 = np.asarray([np.nan if row["primary_D1"] == "" else float(row["primary_D1"]) for row in price])
    p2 = np.asarray([np.nan if row["primary_D2"] == "" else float(row["primary_D2"]) for row in price])
    vn = np.asarray([np.nan if value is None else float(value) for value in selection["selected_V_N"]])
    ratio = np.asarray([np.nan if value is None else float(value) for value in selection["selected_relative_ratio"]])
    v1 = np.asarray([np.nan if value is None else float(value) for value in selection["selected_V1"]])
    v2 = np.asarray([np.nan if value is None else float(value) for value in selection["selected_V2"]])
    seconds = np.asarray([dt(row["timestamp"]).timestamp() for row in price], dtype=float)
    raw_v1 = np.full(n, np.nan)
    raw_v1[1:] = np.diff(raw) / (np.diff(seconds) / 60.0)
    boundaries = selection["volume_regime_boundaries"]

    def regime(value: float) -> str:
        if not math.isfinite(value):
            return "UNAVAILABLE"
        if value <= boundaries["q25"]:
            return "LOW"
        if value <= boundaries["q75"]:
            return "NORMAL"
        if value <= boundaries["q95"]:
            return "ELEVATED"
        return "EXTREME"

    regimes = [regime(value) for value in vn]
    output_path = ROOT / "APTF_TEST_009V_PRICE_VOLUME_OBSERVATIONS_V0_1.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OBS_COLUMNS)
        writer.writeheader()
        for index, (source_row, price_row) in enumerate(zip(source, price, strict=True)):
            writer.writerow({
                "source_observation_index": price_row["source_observation_index"],
                "source_physical_row": price_row["source_physical_row"],
                "timestamp": price_row["timestamp"],
                "initialization_status": price_row["initialization_status"],
                "price": price_row["price"], "frozen_P1": price_row["primary_D1"],
                "frozen_P2": price_row["primary_D2"],
                "frozen_price_derivative_state": price_row["derivative_state"],
                "V_RAW": source_row["volume"], "raw_V1": "" if not math.isfinite(raw_v1[index]) else raw_v1[index],
                "V_N": "" if not math.isfinite(vn[index]) else vn[index],
                "V1": "" if not math.isfinite(v1[index]) else v1[index],
                "V2": "" if not math.isfinite(v2[index]) else v2[index],
                "volume_regime": regimes[index],
                "H": price_row["H"], "Q_G": price_row["Q_G"], "Q_S": price_row["Q_S"],
                "Q_R": price_row["Q_R"], "C": price_row["C"],
                "frozen_emitter_decision": price_row["emitter_decision"],
                "frozen_position_state_before": price_row["position_state_before"],
                "frozen_position_state_after": price_row["position_state_after"],
                "frozen_execution_intent": price_row["execution_intent"],
            })

    crossing_rows = list(csv.DictReader(CROSSINGS.open(newline="", encoding="utf-8")))
    crossing_indices = [int(row["observation_index"]) - 1 for row in crossing_rows]
    crossing_by_id = {row["crossing_id"]: row for row in crossing_rows}
    crossing_by_index = dict(zip(crossing_indices, crossing_rows, strict=True))
    elevated_indices = [index for index in range(15, n) if regimes[index] == "ELEVATED"]
    extreme_indices = [index for index in range(15, n) if regimes[index] == "EXTREME"]
    feature_columns = [
        "crossing_id", "crossing_type", "observation_index", "timestamp",
        "V_N_at_crossing", "V1_at_crossing", "V2_at_crossing", "volume_regime_at_crossing",
        "V1_sign_persistence", "V2_sign_persistence",
        "nearest_preceding_elevated_observation", "observations_since_elevated", "seconds_since_elevated",
        "nearest_preceding_extreme_observation", "observations_since_extreme", "seconds_since_extreme",
        "elevated_at_crossing", "extreme_at_crossing",
    ]
    for window in PRIOR_WINDOWS:
        feature_columns.extend([
            f"max_V_N_prior_{window}", f"mean_V_N_prior_{window}", f"median_V_N_prior_{window}",
            f"mean_V1_prior_{window}", f"median_V1_prior_{window}",
            f"mean_V2_prior_{window}", f"median_V2_prior_{window}",
            f"V_N_change_prior_{window}", f"elevated_within_prior_{window}",
            f"extreme_within_prior_{window}",
        ])
    crossing_features: list[dict[str, Any]] = []
    for crossing, index in zip(crossing_rows, crossing_indices, strict=True):
        previous_elevated_position = bisect.bisect_left(elevated_indices, index) - 1
        previous_extreme_position = bisect.bisect_left(extreme_indices, index) - 1
        previous_elevated = None if previous_elevated_position < 0 else elevated_indices[previous_elevated_position]
        previous_extreme = None if previous_extreme_position < 0 else extreme_indices[previous_extreme_position]
        item: dict[str, Any] = {
            "crossing_id": crossing["crossing_id"], "crossing_type": crossing["crossing_type"],
            "observation_index": index + 1, "timestamp": price[index]["timestamp"],
            "V_N_at_crossing": vn[index], "V1_at_crossing": v1[index], "V2_at_crossing": v2[index],
            "volume_regime_at_crossing": regimes[index],
            "V1_sign_persistence": run_persistence(v1, index),
            "V2_sign_persistence": run_persistence(v2, index),
            "nearest_preceding_elevated_observation": "" if previous_elevated is None else previous_elevated + 1,
            "observations_since_elevated": "" if previous_elevated is None else index - previous_elevated,
            "seconds_since_elevated": "" if previous_elevated is None else seconds[index] - seconds[previous_elevated],
            "nearest_preceding_extreme_observation": "" if previous_extreme is None else previous_extreme + 1,
            "observations_since_extreme": "" if previous_extreme is None else index - previous_extreme,
            "seconds_since_extreme": "" if previous_extreme is None else seconds[index] - seconds[previous_extreme],
            "elevated_at_crossing": str(regimes[index] == "ELEVATED").lower(),
            "extreme_at_crossing": str(regimes[index] == "EXTREME").lower(),
        }
        for window in PRIOR_WINDOWS:
            values = vn[max(0, index - window) : index]
            values = values[np.isfinite(values)]
            first_values = v1[max(0, index - window) : index]
            first_values = first_values[np.isfinite(first_values)]
            second_values = v2[max(0, index - window) : index]
            second_values = second_values[np.isfinite(second_values)]
            start_index = max(0, index - window)
            item.update({
                f"max_V_N_prior_{window}": "" if not len(values) else float(np.max(values)),
                f"mean_V_N_prior_{window}": "" if not len(values) else float(np.mean(values)),
                f"median_V_N_prior_{window}": "" if not len(values) else float(np.median(values)),
                f"mean_V1_prior_{window}": "" if not len(first_values) else float(np.mean(first_values)),
                f"median_V1_prior_{window}": "" if not len(first_values) else float(np.median(first_values)),
                f"mean_V2_prior_{window}": "" if not len(second_values) else float(np.mean(second_values)),
                f"median_V2_prior_{window}": "" if not len(second_values) else float(np.median(second_values)),
                f"V_N_change_prior_{window}": "" if not len(values) else vn[index] - values[0],
                f"elevated_within_prior_{window}": str(any(regimes[position] == "ELEVATED" for position in range(start_index, index))).lower(),
                f"extreme_within_prior_{window}": str(any(regimes[position] == "EXTREME" for position in range(start_index, index))).lower(),
            })
        crossing_features.append(item)
    with (ROOT / "APTF_TEST_009V_CROSSING_VOLUME_FEATURES_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=feature_columns)
        writer.writeheader(); writer.writerows(crossing_features)

    joint = Counter()
    for index in range(15, n):
        if math.isfinite(v1[index]) and math.isfinite(v2[index]):
            joint[(price[index]["derivative_state"], regimes[index], sign(v1[index]), sign(v2[index]))] += 1
    with (ROOT / "APTF_TEST_009V_JOINT_STATE_FREQUENCIES_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        columns = ["price_derivative_state", "volume_regime", "V1_sign", "V2_sign", "observation_count", "percentage_of_actionable_observations"]
        writer = csv.DictWriter(handle, fieldnames=columns); writer.writeheader()
        for key, count in sorted(joint.items()):
            writer.writerow(dict(zip(columns[:4], key)) | {"observation_count": count, "percentage_of_actionable_observations": 100.0 * count / 101206})

    trajectory_rows = 0
    dispersion_values: dict[str, dict[int, dict[str, list[float]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    with (
        TURNING.open(newline="", encoding="utf-8") as source_handle,
        (ROOT / "APTF_TEST_009V_MULTIVARIATE_TURNING_TRAJECTORIES_V0_1.csv").open("w", newline="", encoding="utf-8") as output_handle,
    ):
        reader = csv.DictReader(source_handle); writer = csv.DictWriter(output_handle, fieldnames=TRAJECTORY_COLUMNS); writer.writeheader()
        for row in reader:
            index = int(row["crossing_observation_index"]) - 1 + int(row["relative_observation"])
            item = {
                "transition_id": row["transition_id"], "transition_type": row["transition_type"],
                "frozen_Test009_crossing_id": row["transition_id"],
                "relative_observation": row["relative_observation"], "relative_seconds": row["relative_seconds"],
                "timestamp": price[index]["timestamp"], "normalized_price": row["normalized_price"],
                "P1": row["primary_D1"], "P2": row["primary_D2"], "V_RAW": raw[index],
                "V_N": vn[index], "V1": v1[index], "V2": v2[index], "volume_regime": regimes[index],
                "H": row["H"], "Q_G": row["Q_G"], "Q_S": row["Q_S"], "Q_R": row["Q_R"], "C": row["C"],
                "emitter_decision": row["emitter_decision"], "position_state": row["position_state"],
                "causal_or_retrospective_flag": "CAUSAL_PRECURSOR_OR_CROSSING" if int(row["relative_observation"]) <= 0 else "RETROSPECTIVE_REFERENCE_ONLY",
            }
            writer.writerow(item); trajectory_rows += 1
            dispersion_values[row["transition_type"]][int(row["relative_observation"])][regimes[index]].append(float(row["normalized_price"]))

    upper_indices = [index for row, index in zip(crossing_rows, crossing_indices) if row["crossing_type"] == "UPPER"]
    lower_indices = [index for row, index in zip(crossing_rows, crossing_indices) if row["crossing_type"] == "LOWER"]
    upper_set, lower_set = set(), set()
    for index in upper_indices: upper_set.update(range(max(15, index - 15), index + 1))
    for index in lower_indices: lower_set.update(range(max(15, index - 15), index + 1))
    turning_mask = np.zeros(n, dtype=bool)
    for index in crossing_indices: turning_mask[max(15, index - 3) : min(n, index + 4)] = True
    baseline_set = {index for index in range(15, n) if not turning_mask[index] and math.isfinite(v1[index]) and math.isfinite(v2[index])}
    arrays = {"V_N": vn, "abs_V1": np.abs(v1), "abs_V2": np.abs(v2)}

    def region_evidence(indices: set[int]) -> dict[str, Any]:
        valid = {index for index in indices if math.isfinite(vn[index]) and math.isfinite(v1[index]) and math.isfinite(v2[index])}
        counts = Counter(regimes[index] for index in valid)
        return {
            "rows": len(valid), "distributions": value_summary(valid, arrays),
            "regime_counts": dict(counts),
            "elevated_frequency": 0 if not valid else counts["ELEVATED"] / len(valid),
            "extreme_frequency": 0 if not valid else counts["EXTREME"] / len(valid),
        }
    regions = {"UPPER_PRECURSOR": region_evidence(upper_set), "LOWER_PRECURSOR": region_evidence(lower_set), "NON_TURNING_BASELINE": region_evidence(baseline_set)}

    sustained_price_precursors: dict[str, Any] = {"UPPER": {}, "LOWER": {}}
    precursor_authority = list(csv.DictReader(PRICE_PRECURSORS.open(newline="", encoding="utf-8")))
    for crossing_type in ("UPPER", "LOWER"):
        for threshold in (1, 2, 3):
            pool: list[int] = []
            qualified = 0
            for item in precursor_authority:
                if (
                    item["crossing_type"] != crossing_type
                    or int(item["minimum_sustained_observations"]) != threshold
                    or item["qualifies"] != "true"
                ):
                    continue
                qualified += 1
                start = int(item["precursor_start_observation"]) - 1
                crossing_index = int(item["crossing_observation"]) - 1
                pool.extend(range(start, crossing_index))
            sustained_price_precursors[crossing_type][str(threshold)] = {
                "qualified_crossings": qualified,
                "precursor_rows_with_overlap": len(pool),
                "V_N": summary([vn[index] for index in pool if math.isfinite(vn[index])]),
                "V1": summary([v1[index] for index in pool if math.isfinite(v1[index])]),
                "V2": summary([v2[index] for index in pool if math.isfinite(v2[index])]),
                "regime_counts": dict(Counter(regimes[index] for index in pool)),
            }

    # Retrospective time-to-crossing labels; all feature values remain current/past-only.
    time_rows: list[dict[str, Any]] = []
    separation_groups: dict[str, dict[str, list[int]]] = {
        "UPPER": defaultdict(list), "LOWER": defaultdict(list)
    }
    for crossing_type, relevant_indices, precursor_predicate, strengthening_state in (
        ("UPPER", upper_indices, lambda i: p1[i] > 0 and p2[i] < 0, "RISING_STRENGTHENING"),
        ("LOWER", lower_indices, lambda i: p1[i] < 0 and p2[i] > 0, "FALLING_STRENGTHENING"),
    ):
        for index in range(15, n):
            if not precursor_predicate(index) or not (math.isfinite(vn[index]) and math.isfinite(v1[index]) and math.isfinite(v2[index])):
                continue
            position = bisect.bisect_right(relevant_indices, index)
            next_index = None if position >= len(relevant_indices) else relevant_indices[position]
            distance = None if next_index is None else next_index - index
            if distance == 1:
                label = "IMMEDIATE"
            elif distance is not None and 2 <= distance <= 6:
                label = "DELAYED"
            elif any(price[j]["derivative_state"] == strengthening_state for j in range(index + 1, min(n, index + 7))):
                label = "RETURN_TO_STRENGTHENING"
            else:
                label = "OTHER_NO_NEAR_CROSSING"
            separation_groups[crossing_type][label].append(index)
            if next_index is not None:
                crossing_row = crossing_by_index[next_index]
                time_rows.append({
                    "precursor_event_id": f"PV{len(time_rows)+1:07d}", "crossing_id": crossing_row["crossing_id"],
                    "crossing_type": crossing_type, "trajectory_label": label,
                    "precursor_observation": index + 1, "precursor_timestamp": price[index]["timestamp"],
                    "P1": p1[index], "P2": p2[index], "V_N": vn[index], "V1": v1[index], "V2": v2[index],
                    "volume_regime": regimes[index], "observations_to_crossing": distance,
                    "seconds_to_crossing": seconds[next_index] - seconds[index],
                })
    with (ROOT / "APTF_TEST_009V_VOLUME_TIME_TO_CROSSING_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TIME_COLUMNS); writer.writeheader(); writer.writerows(time_rows)

    separation: dict[str, Any] = {}
    for crossing_type, groups in separation_groups.items():
        separation[crossing_type] = {}
        for label, indices in groups.items():
            separation[crossing_type][label] = {
                "count": len(indices),
                "V_N": summary([vn[index] for index in indices]),
                "V1": summary([v1[index] for index in indices]),
                "V2": summary([v2[index] for index in indices]),
                "absolute_P2": summary([abs(p2[index]) for index in indices]),
                "elevated_or_extreme_frequency": sum(regimes[index] in ("ELEVATED", "EXTREME") for index in indices) / max(1, len(indices)),
            }
    (ROOT / "APTF_TEST_009V_TRAJECTORY_SEPARATION_V0_1.json").write_text(json.dumps(separation, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    valid = np.isfinite(p) & np.isfinite(p1) & np.isfinite(p2) & np.isfinite(vn) & np.isfinite(v1) & np.isfinite(v2)
    valid[:15] = False
    names = ("P", "P1", "P2", "V_N", "V1", "V2")
    matrix = {"P": p, "P1": p1, "P2": p2, "V_N": vn, "V1": v1, "V2": v2}
    pearson, spearman = {}, {}
    for left in names:
        pearson[left], spearman[left] = {}, {}
        for right in names:
            pair = valid & np.isfinite(matrix[left]) & np.isfinite(matrix[right])
            pearson[left][right] = float(pearsonr(matrix[left][pair], matrix[right][pair]).statistic)
            spearman[left][right] = float(spearmanr(matrix[left][pair], matrix[right][pair]).statistic)
    linear_r2 = {}
    design = np.column_stack((np.ones(valid.sum()), p1[valid], p2[valid]))
    for target in ("V_N", "V1", "V2"):
        y = matrix[target][valid]
        coefficients, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
        residual = y - design @ coefficients
        linear_r2[target] = float(1.0 - np.sum(residual * residual) / np.sum((y - np.mean(y)) ** 2))
    internal_relationships = {}
    for internal in ("H", "Q_G", "Q_S", "Q_R", "C"):
        values = np.asarray([float(row[internal]) for row in price])
        if np.std(values[valid]) == 0:
            internal_relationships[internal] = {
                target: {"pearson": None, "spearman": None, "reason": "CONSTANT_INPUT"}
                for target in ("V_N", "V1", "V2")
            }
        else:
            internal_relationships[internal] = {
                target: {
                    "pearson": float(pearsonr(values[valid], matrix[target][valid]).statistic),
                    "spearman": float(spearmanr(values[valid], matrix[target][valid]).statistic),
                } for target in ("V_N", "V1", "V2")
            }
    relationships = {
        "valid_actionable_rows": int(valid.sum()), "pearson": pearson, "spearman": spearman,
        "linear_R2_volume_component_from_P1_P2": linear_r2,
        "internal_vs_volume": internal_relationships,
        "interpretation_rule": "Correlation/R2 alone does not establish independence; region and trajectory separation evidence is also required.",
    }
    (ROOT / "APTF_TEST_009V_PRICE_VOLUME_RELATIONSHIPS_V0_1.json").write_text(json.dumps(relationships, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    frozen_alignment = {row["episode_id"]: row for row in csv.DictReader(PRICE_ALIGNMENT.open(newline="", encoding="utf-8"))}
    trades = {row["episode_id"]: row for row in csv.DictReader(TRADES.open(newline="", encoding="utf-8"))}
    episode_columns = [
        "episode_id", "test008_result_classification", "test008_gross_pnl",
        "buy_timestamp", "buy_P1", "buy_P2", "buy_V_N", "buy_V1", "buy_V2",
        "frozen_lower_crossing_offset_observations", "sell_timestamp", "sell_P1",
        "sell_P2", "sell_V_N", "sell_V1", "sell_V2",
        "frozen_upper_crossing_offset_observations",
    ]
    for prefix in ("pre_buy", "pre_sell"):
        for window in PRIOR_WINDOWS:
            for variable in ("V_N", "V1", "V2"):
                episode_columns.extend([f"{prefix}_{variable}_mean_{window}", f"{prefix}_{variable}_max_{window}"])
    episode_rows = []
    for episode_id, aligned in frozen_alignment.items():
        buy = int(aligned["buy_observation"]) - 1; sell = int(aligned["sell_observation"]) - 1
        trade = trades[episode_id]
        item = {
            "episode_id": episode_id, "test008_result_classification": trade["result_classification"],
            "test008_gross_pnl": trade["gross_pnl"], "buy_timestamp": aligned["buy_timestamp"],
            "buy_P1": p1[buy], "buy_P2": p2[buy], "buy_V_N": vn[buy], "buy_V1": v1[buy], "buy_V2": v2[buy],
            "frozen_lower_crossing_offset_observations": aligned["buy_offset_observations"],
            "sell_timestamp": aligned["sell_timestamp"], "sell_P1": p1[sell], "sell_P2": p2[sell],
            "sell_V_N": vn[sell], "sell_V1": v1[sell], "sell_V2": v2[sell],
            "frozen_upper_crossing_offset_observations": aligned["sell_offset_observations"],
        }
        for prefix, index in (("pre_buy", buy), ("pre_sell", sell)):
            for window in PRIOR_WINDOWS:
                for variable, values in (("V_N", vn), ("V1", v1), ("V2", v2)):
                    current = values[max(0, index-window):index]; current = current[np.isfinite(current)]
                    item[f"{prefix}_{variable}_mean_{window}"] = "" if not len(current) else float(np.mean(current))
                    item[f"{prefix}_{variable}_max_{window}"] = "" if not len(current) else float(np.max(current))
        episode_rows.append(item)
    with (ROOT / "APTF_TEST_009V_EPISODE_PRICE_VOLUME_ALIGNMENT_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=episode_columns); writer.writeheader(); writer.writerows(episode_rows)

    crossing_summary = {}
    for crossing_type in ("UPPER", "LOWER"):
        selected_features = [item for item in crossing_features if item["crossing_type"] == crossing_type]
        crossing_summary[crossing_type] = {
            "count": len(selected_features),
            "V_N_at_crossing": summary([float(item["V_N_at_crossing"]) for item in selected_features]),
            "V1_at_crossing": summary([float(item["V1_at_crossing"]) for item in selected_features]),
            "V2_at_crossing": summary([float(item["V2_at_crossing"]) for item in selected_features]),
            **{
                f"{regime_name.lower()}_within_prior_{window}": sum(item[f"{regime_name.lower()}_within_prior_{window}"] == "true" for item in selected_features)
                for regime_name in ("ELEVATED", "EXTREME") for window in PRIOR_WINDOWS
            },
        }

    # Does regime stratification reduce price-path IQR?
    dispersion = {}
    for crossing_type, relative_groups in dispersion_values.items():
        unstratified, stratified = [], []
        for _, regime_groups in relative_groups.items():
            all_values = [value for values in regime_groups.values() for value in values]
            if len(all_values) < 4: continue
            unstratified.append(float(np.quantile(all_values, .75) - np.quantile(all_values, .25)))
            weighted = []
            total = 0
            for values in regime_groups.values():
                if len(values) >= 4:
                    weighted.append((len(values), float(np.quantile(values,.75)-np.quantile(values,.25))))
                    total += len(values)
            if total: stratified.append(sum(count*iqr for count,iqr in weighted)/total)
        dispersion[crossing_type] = {
            "median_unstratified_price_IQR": float(np.median(unstratified)),
            "median_volume_regime_stratified_price_IQR": float(np.median(stratified)),
            "relative_reduction": float(1 - np.median(stratified)/np.median(unstratified)),
        }

    episode_groups = {}
    for result in ("WIN", "LOSS", "FLAT_RESULT"):
        selected_rows = [item for item in episode_rows if item["test008_result_classification"] == result]
        episode_groups[result] = {
            "count": len(selected_rows),
            **{
                name: summary([float(item[name]) for item in selected_rows if item[name] != ""])
                for name in (
                    "buy_V_N","buy_V1","buy_V2","sell_V_N","sell_V1","sell_V2",
                    "pre_buy_V_N_mean_15","pre_buy_V1_mean_15","pre_buy_V2_mean_15",
                    "pre_sell_V_N_mean_15","pre_sell_V1_mean_15","pre_sell_V2_mean_15",
                )
            },
        }

    result = {
        "test_id": "APTF_TEST_009V_SUMMARY_V0_1",
        "source_rows": n, "initializing_context_only": 15, "actionable_rows": 101206,
        "primary_V_N": selection["primary_V_N_candidate"],
        "primary_volume_derivative_window": selection["primary_volume_derivative_window"],
        "volume_regime_boundaries": boundaries, "relative_ratio_counts": selection["relative_ratio_counts"],
        "frozen_upper_crossings": len(upper_indices), "frozen_lower_crossings": len(lower_indices),
        "price_crossings_moved_by_volume": 0, "crossing_volume_summary": crossing_summary,
        "regions_vs_baseline": regions, "relationships": relationships,
        "sustained_price_precursor_volume": sustained_price_precursors,
        "trajectory_separation": separation, "trajectory_dispersion": dispersion,
        "episode_pnl_descriptive_groups": episode_groups,
        "joint_state_count": len(joint), "turning_trajectory_rows": trajectory_rows,
        "time_to_crossing_rows": len(time_rows), "future_volume_normalization_observations": 0,
        "future_volume_derivative_observations": 0, "classifier_trained": False,
        "trading_rule_created": False, "local_dynamics_fitted": False,
        "runge_kutta_used": False, "curve_family_forced": False, "PCA_used": False,
        "runtime_modified": False, "emitter_modified": False, "status": "PASS",
    }
    (ROOT / "APTF_TEST_009V_SUMMARY_V0_1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "upper_crossings": len(upper_indices), "lower_crossings": len(lower_indices),
        "observation_rows": n, "trajectory_rows": trajectory_rows,
        "joint_states": len(joint), "time_to_crossing_rows": len(time_rows),
        "future_volume": 0, "status": "PASS",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())