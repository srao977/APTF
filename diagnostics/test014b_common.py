from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from time import perf_counter_ns
from typing import Any, Iterable

import numpy as np

from spy_price_engine.cockpit import (
    CockpitPolicyConfig,
    CockpitState,
    PriceCockpitInterpreter,
)
from spy_price_engine.contracts import PriceEmission


ROOT = Path(__file__).resolve().parents[1]
EMISSIONS_V01 = ROOT / "APTF_TEST_014_SPY_P_ENGINE_EMISSIONS_V0_1.csv"
TURNS_V01 = ROOT / "APTF_TEST_014_SPY_TURNING_POINT_VALIDATION_V0_1.csv"
SPLIT = ROOT / "APTF_TEST_014_DEVELOPMENT_VALIDATION_SPLIT_V0_1.json"
V01_SCORECARD = ROOT / "APTF_TEST_014_SPY_P_EMISSION_VALIDATION_SCORECARD_V0_1.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if not rows and fieldnames is None:
        raise ValueError(f"fieldnames required for empty CSV: {path.name}")
    columns = fieldnames or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_rows(partition: str | None = None) -> list[dict[str, str]]:
    with EMISSIONS_V01.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if partition is None:
        return rows
    return [row for row in rows if row["partition"] == partition]


def load_turns(partition: str) -> list[dict[str, str]]:
    with TURNS_V01.open(newline="", encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle) if row["partition"] == partition]


def price_emission(row: dict[str, str]) -> PriceEmission:
    return PriceEmission(
        symbol=row["symbol"],
        timestamp=row["timestamp"],
        engine="P",
        p=float(row["p"]),
        p1=float(row["p1"]),
        p2=float(row["p2"]),
        projected_p=float(row["projected_p"]),
        projected_p1=float(row["projected_p1"]),
        projected_p2=float(row["projected_p2"]),
        delta_projected_p=float(row["delta_projected_p"]),
        delta_projected_p1=float(row["delta_projected_p1"]),
        delta_projected_p2=float(row["delta_projected_p2"]),
        current_direction=row["current_direction"],
        current_acceleration=row["current_acceleration"],
        projected_direction=row["projected_direction"],
        projected_acceleration=row["projected_acceleration"],
        trajectory_phase=row["trajectory_phase"],
        turning_tendency=row["turning_tendency"],
        domain_state=row["domain_state"],
        stability_state=row["stability_state"],
        confidence_state=row["confidence_state"],
        raw_color=row["raw_color"],
        color=row["color"],
        reason_codes=tuple(json.loads(row["reason_codes"])),
        rk_success=row["rk_success"].lower() == "true",
        condition_number=float(row["condition_number"]),
        max_real_eigenvalue=float(row["max_real_eigenvalue"]),
        perturbation_amplification=float(row["perturbation_amplification"]),
    )


def replay(rows: list[dict[str, str]], config: CockpitPolicyConfig) -> tuple[list[dict[str, Any]], list[int]]:
    interpreter = PriceCockpitInterpreter(config)
    state = CockpitState()
    previous_session = None
    output = []
    latencies = []
    for row in rows:
        session_id = f'{row["timestamp"][:10]}:{row["session"]}'
        if session_id != previous_session:
            state = CockpitState()
            previous_session = session_id
        emission = price_emission(row)
        started = perf_counter_ns()
        cockpit, state = interpreter.observe(emission, state)
        latencies.append(perf_counter_ns() - started)
        output.append(row | cockpit.as_dict() | {"color": cockpit.cockpit_color})
    return output, latencies


def _session_id(row: dict[str, Any]) -> str:
    return f'{str(row["timestamp"])[:10]}:{row["session"]}'


def _warning(row: dict[str, Any], turn_type: str, version: str) -> bool:
    if version == "V0.1":
        if turn_type == "MAXIMUM":
            return row["trajectory_phase"] in {"UP_DECELERATING", "TURNING_DOWN"} or row["turning_tendency"] in {
                "DETERIORATING_TOWARD_TURN", "TURNING_DOWN"
            }
        return row["trajectory_phase"] in {"DOWN_DECELERATING", "TURNING_UP"} or row["turning_tendency"] in {
            "RECOVERING_TOWARD_TURN", "TURNING_UP"
        }
    return row["turn_candidate"] == ("DOWN" if turn_type == "MAXIMUM" else "UP")


def run_durations(rows: list[dict[str, Any]], field: str = "color") -> dict[str, list[int]]:
    durations: dict[str, list[int]] = defaultdict(list)
    previous_value = None
    previous_session = None
    length = 0
    for row in rows:
        value = str(row[field])
        session = _session_id(row)
        if session != previous_session or value != previous_value:
            if previous_value is not None:
                durations[previous_value].append(length)
            previous_value = value
            previous_session = session
            length = 1
        else:
            length += 1
    if previous_value is not None:
        durations[previous_value].append(length)
    return durations


def score(
    policy_id: str,
    rows: list[dict[str, Any]],
    turns: list[dict[str, str]],
    sessions: int,
    version: str,
    horizon: int = 5,
) -> dict[str, Any]:
    by_index = {int(row["observation_index"]) - 1: row for row in rows}
    index_by_timestamp = {str(row["timestamp"]): int(row["observation_index"]) - 1 for row in rows}
    turn_indices = {
        kind: {index_by_timestamp[turn["turning_timestamp"]] for turn in turns if turn["turn_type"] == kind}
        for kind in ("MAXIMUM", "MINIMUM")
    }
    turn_details = []
    for turn in turns:
        turn_index = index_by_timestamp[turn["turning_timestamp"]]
        turn_row = by_index[turn_index]
        candidates = [
            by_index[index]
            for index in range(turn_index - horizon, turn_index)
            if index in by_index and _session_id(by_index[index]) == _session_id(turn_row)
        ]
        warnings = [row for row in candidates if _warning(row, turn["turn_type"], version)]
        first = warnings[0] if warnings else None
        turn_details.append(
            {
                "turn_id": turn["turn_id"],
                "partition": turn["partition"],
                "turning_timestamp": turn["turning_timestamp"],
                "turn_type": turn["turn_type"],
                "observed_price": turn["observed_price"],
                "detected": first is not None,
                "first_precursor_timestamp": "" if first is None else first["timestamp"],
                "precursor_lead_minutes": "" if first is None else turn_index - (int(first["observation_index"]) - 1),
                "preceding_state_sequence": "|".join(str(row.get("refined_internal_state", row["trajectory_phase"])) for row in candidates),
            }
        )

    warnings_by_kind: dict[str, list[dict[str, Any]]] = {"MAXIMUM": [], "MINIMUM": []}
    false_by_kind = Counter()
    for row in rows:
        row_index = int(row["observation_index"]) - 1
        for kind in ("MAXIMUM", "MINIMUM"):
            if _warning(row, kind, version):
                warnings_by_kind[kind].append(row)
                if not any(row_index < turn_index <= row_index + horizon for turn_index in turn_indices[kind]):
                    false_by_kind[kind] += 1

    counts = Counter(str(row["color"]) for row in rows)
    changes = direct_green_red = direct_red_green = 0
    for left, right in zip(rows, rows[1:]):
        if _session_id(left) != _session_id(right):
            continue
        if left["color"] != right["color"]:
            changes += 1
        direct_green_red += left["color"] == "GREEN" and right["color"] == "RED"
        direct_red_green += left["color"] == "RED" and right["color"] == "GREEN"
    durations = run_durations(rows)
    maxima = [item for item in turn_details if item["turn_type"] == "MAXIMUM"]
    minima = [item for item in turn_details if item["turn_type"] == "MINIMUM"]

    def turn_metrics(kind: str, details: list[dict[str, Any]]) -> dict[str, Any]:
        warning_count = len(warnings_by_kind[kind])
        false_count = false_by_kind[kind]
        leads = [int(item["precursor_lead_minutes"]) for item in details if item["detected"]]
        return {
            "count": len(details),
            "detected": sum(bool(item["detected"]) for item in details),
            "precision": 0.0 if warning_count == 0 else (warning_count - false_count) / warning_count,
            "recall": 0.0 if not details else sum(bool(item["detected"]) for item in details) / len(details),
            "false_rate": 0.0 if warning_count == 0 else false_count / warning_count,
            "median_lead": None if not leads else float(np.median(leads)),
            "q25_lead": None if not leads else float(np.quantile(leads, 0.25)),
            "q75_lead": None if not leads else float(np.quantile(leads, 0.75)),
            "warnings": warning_count,
            "false_warnings": false_count,
        }

    maxima_metrics = turn_metrics("MAXIMUM", maxima)
    minima_metrics = turn_metrics("MINIMUM", minima)
    all_durations = [value for values in durations.values() for value in values]
    return {
        "policy_id": policy_id,
        "observations": len(rows),
        "sessions": sessions,
        "GREEN_count": counts["GREEN"],
        "GREEN_percentage": counts["GREEN"] / len(rows),
        "AMBER_count": counts["AMBER"],
        "AMBER_percentage": counts["AMBER"] / len(rows),
        "RED_count": counts["RED"],
        "RED_percentage": counts["RED"] / len(rows),
        "INVALID_count": counts["INVALID"],
        "INVALID_percentage": counts["INVALID"] / len(rows),
        "color_changes": changes,
        "changes_per_session": changes / sessions,
        "median_color_duration": None if not all_durations else float(median(all_durations)),
        "AMBER_median_duration": None if not durations["AMBER"] else float(median(durations["AMBER"])),
        "direct_GREEN_RED": direct_green_red,
        "direct_RED_GREEN": direct_red_green,
        **{f"maxima_{key}": value for key, value in maxima_metrics.items()},
        **{f"minima_{key}": value for key, value in minima_metrics.items()},
        "turn_details": turn_details,
    }


def flatten_score(scorecard: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in scorecard.items() if key != "turn_details"}


def config_from_dict(payload: dict[str, Any]) -> CockpitPolicyConfig:
    parameters = payload["parameters"] if "parameters" in payload else payload
    return CockpitPolicyConfig(
        policy_id=str(payload.get("policy_id", parameters.get("policy_id", "P_EMISSION_V0_2"))),
        epsilon=float(parameters["epsilon"]),
        zero_proximity_threshold=float(parameters["zero_proximity_threshold"]),
        deceleration_strength_threshold=float(parameters["deceleration_strength_threshold"]),
        persistence_observations=int(parameters["persistence_observations"]),
        candidate_hold_observations=int(parameters["candidate_hold_observations"]),
        low_confidence_requires_amber=bool(parameters["low_confidence_requires_amber"]),
        domain_exit_requires_amber=bool(parameters["domain_exit_requires_amber"]),
    )


def latency_summary(latencies_ns: Iterable[int]) -> dict[str, float]:
    values = np.asarray(list(latencies_ns), dtype=float) / 1000.0
    return {
        "unit": "microseconds",
        "median": float(np.median(values)),
        "q95": float(np.quantile(values, 0.95)),
        "q99": float(np.quantile(values, 0.99)),
        "max": float(np.max(values)),
    }