from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from time import perf_counter_ns
from typing import Any

import numpy as np

from emission_intervals import EmissionIntervalizer, IntervalState
from spy_volume_engine import VolumeEngine, VolumePolicyConfig, VolumePolicyState


ROOT = Path(__file__).resolve().parents[1]
P_EMISSIONS = ROOT / "APTF_TEST_014B_SPY_P_ENGINE_EMISSIONS_V0_2.csv"
V_AUTHORITY = ROOT / "APTF_TEST_010_VOLUME_ENGINE_EMISSIONS_V0_1.csv"
SPLIT = ROOT / "APTF_TEST_014_DEVELOPMENT_VALIDATION_SPLIT_V0_1.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    fields = columns or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_p_rows() -> list[dict[str, str]]:
    with P_EMISSIONS.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_common_rows() -> list[dict[str, Any]]:
    p_rows = load_p_rows()
    p_by_timestamp = {row["timestamp"]: row for row in p_rows}
    output = []
    with V_AUTHORITY.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            p_row = p_by_timestamp.get(row["timestamp"])
            if p_row is None:
                continue
            interval = json.loads(row["interval_state_json"])
            output.append(
                row | {
                    "interval_mean_vn": float(interval["mean_vn"]),
                    "interval_std_raw": float(interval["std"]),
                    "interval_max_median": float(interval["max_median"]),
                    "persistence_above_baseline": int(interval["persist_baseline"]),
                    "session": p_row["session"],
                    "partition": p_row["partition"],
                    "p_color": p_row["cockpit_color"],
                    "price": float(p_row["p"]),
                    "common_index": int(p_row["observation_index"]),
                }
            )
    if len(output) != len(p_rows):
        raise RuntimeError(f"P/V common timestamp mismatch: P={len(p_rows)} common={len(output)}")
    return output


def replay(rows: list[dict[str, Any]], config: VolumePolicyConfig) -> tuple[list[dict[str, Any]], list[int]]:
    engine = VolumeEngine(config)
    state = VolumePolicyState()
    previous_session = None
    output = []
    latencies = []
    for row in rows:
        session_id = f'{row["timestamp"][:10]}:{row["session"]}'
        if session_id != previous_session:
            state = VolumePolicyState()
            previous_session = session_id
        started = perf_counter_ns()
        emission, state = engine.observe(row, state)
        latencies.append(perf_counter_ns() - started)
        output.append(row | emission.as_dict())
    return output, latencies


def intervalize(rows: list[dict[str, Any]], engine: str, color_field: str) -> tuple[list[dict[str, Any]], list[int], list[int]]:
    intervalizer = EmissionIntervalizer()
    state: IntervalState | None = None
    intervals = []
    ages = []
    latencies = []
    for row in rows:
        session_id = f'{row["timestamp"][:10]}:{row["session"]}'
        started = perf_counter_ns()
        state, completed, age = intervalizer.observe(
            engine, "SPY", str(row["timestamp"]), str(row[color_field]), session_id,
            int(row["common_index"]), state,
        )
        latencies.append(perf_counter_ns() - started)
        ages.append(age)
        if completed is not None:
            intervals.append(completed.as_dict())
    if state is not None:
        intervals.append(intervalizer.complete(state).as_dict())
    return intervals, ages, latencies


def score(policy_id: str, rows: list[dict[str, Any]], sessions: int) -> dict[str, Any]:
    intervals, _, _ = intervalize(rows, "V", "cockpit_color")
    counts = Counter(str(row["cockpit_color"]) for row in rows)
    durations: dict[str, list[int]] = defaultdict(list)
    for row in intervals:
        durations[str(row["color"])].append(int(row["duration_minutes"]))
    changes = len(intervals) - sessions
    return {
        "policy_id": policy_id,
        "observations": len(rows),
        "sessions": sessions,
        **{f"{color}_count": counts[color] for color in ("GREEN", "AMBER", "RED", "INVALID")},
        **{f"{color}_occupancy": counts[color] / len(rows) for color in ("GREEN", "AMBER", "RED", "INVALID")},
        "intervals": len(intervals),
        "color_changes": changes,
        "changes_per_session": changes / sessions,
        **{f"{color}_median_interval": None if not durations[color] else float(median(durations[color])) for color in ("GREEN", "AMBER", "RED")},
        "median_interval": float(median([int(row["duration_minutes"]) for row in intervals])),
    }


def duration_scorecards(intervals: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in intervals:
        grouped[(str(row["engine"]), str(row["color"]))].append(int(row["duration_minutes"]))
    duration_rows = []
    reaction_rows = []
    for (engine, color), values in sorted(grouped.items()):
        array = np.asarray(values, dtype=float)
        base = {
            "engine": engine, "color": color, "interval_count": len(values),
            "minimum": float(np.min(array)), "Q25": float(np.quantile(array, .25)),
            "median": float(np.median(array)), "mean": float(np.mean(array)),
            "Q75": float(np.quantile(array, .75)), "Q90": float(np.quantile(array, .90)),
            "Q95": float(np.quantile(array, .95)), "maximum": float(np.max(array)),
        }
        duration_rows.append(base | {
            "pct_1_minute": float(np.mean(array == 1)), "pct_le_2": float(np.mean(array <= 2)),
            "pct_le_3": float(np.mean(array <= 3)), "pct_le_5": float(np.mean(array <= 5)),
            "pct_gt_5": float(np.mean(array > 5)), "pct_gt_10": float(np.mean(array > 10)),
        })
        reaction_rows.append({
            "engine": engine, "color": color, "intervals": len(values), "median_duration": base["median"],
            "Q75": base["Q75"], "Q90": base["Q90"], "Q95": base["Q95"],
            "pct_ge_2": float(np.mean(array >= 2)), "pct_ge_3": float(np.mean(array >= 3)),
            "pct_ge_5": float(np.mean(array >= 5)), "pct_ge_10": float(np.mean(array >= 10)),
        })
    return duration_rows, reaction_rows


def config_from_policy(policy: dict[str, Any]) -> VolumePolicyConfig:
    parameters = policy["parameters"]
    return VolumePolicyConfig(
        policy_id=str(policy["policy_id"]), state_source=str(parameters["state_source"]),
        lower_threshold=float(parameters["lower_threshold"]), upper_threshold=float(parameters["upper_threshold"]),
        confirmation_observations=int(parameters["confirmation_observations"]), epsilon=float(parameters["epsilon"]),
    )