from __future__ import annotations

import bisect
from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any, Iterable

from .authority import canonical_json, logical_seal
from .constants import ADAPTIVE_MULTIPLIERS, BLOCK_MINUTES, FIXED_HORIZONS_MINUTES
from .observer import Duration, ambiguity_index, compatibility, direction_claim, observe_geometry, transition_magnitude


def _epoch(record: dict[str, Any]) -> float:
    return datetime.fromisoformat(str(record["event_time"])).timestamp()


def _duration(anchor_index: int, times: list[float], closes: list[float], directions: list[int], strata: list[str]) -> Duration:
    direction = directions[anchor_index]
    if direction == 0:
        return Duration("INCONCLUSIVE", 0.0, None)
    anchor_time = times[anchor_index]
    anchor_close = closes[anchor_index]
    sum_xy = 0.0
    sum_x2 = 0.0
    last_compatible = 0.0
    for endpoint in range(anchor_index + 1, len(times)):
        minutes = (times[endpoint] - anchor_time) / 60.0
        displacement = math.log(closes[endpoint] / anchor_close)
        sum_xy += minutes * displacement
        sum_x2 += minutes * minutes
        slope = sum_xy / sum_x2
        if compatibility(direction, displacement, slope) == "REVERSAL":
            if strata[endpoint] != "INTRASESSION_CONTINUOUS":
                return Duration("INTERVAL", last_compatible, minutes)
            return Duration("EXACT", minutes, minutes)
        last_compatible = minutes
    return Duration("RIGHT", last_compatible, None)


def _coordinate(
    anchor_index: int,
    requested_minutes: float,
    times: list[float],
    closes: list[float],
    direction: int,
) -> tuple[dict[str, object] | None, str | None]:
    target = times[anchor_index] + requested_minutes * 60.0
    endpoint = bisect.bisect_left(times, target, lo=anchor_index + 1)
    if endpoint >= len(times):
        return None, "BOUNDARY_CENSORED"
    future_times = [(value - times[anchor_index]) / 60.0 for value in times[anchor_index + 1:endpoint + 1]]
    try:
        geometry = observe_geometry(closes[anchor_index], future_times, closes[anchor_index + 1:endpoint + 1], direction, requested_minutes)
    except (ValueError, FloatingPointError):
        return None, "COORDINATE_UNAVAILABLE"
    return geometry.to_dict(), None


def _adaptive_requests(record: dict[str, Any]) -> dict[str, float]:
    dmo = record["dmo"]
    fmo = record["fmo"]
    bases = {
        "observation_half_life": float(dmo["observation_half_life"]),
        "forward_half_life": float(dmo["forward_half_life"]),
        "forward_interval": float(fmo["interval_length"]),
    }
    return {
        f"{name}_{multiplier:g}x": base * multiplier
        for name, base in bases.items()
        for multiplier in ADAPTIVE_MULTIPLIERS
        if math.isfinite(base) and base > 0.0
    }


def build_anchor_records(replay_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    times = [_epoch(record) for record in replay_records]
    closes = [float(record["close"]) for record in replay_records]
    strata = [str(record["transition_stratum"]) for record in replay_records]
    directions = [
        direction_claim(
            float(record["dmo"]["state_velocity"]),
            float(record["dmo"]["state_acceleration"]),
            float(record["dmo"]["state_level"]),
        )
        for record in replay_records
    ]
    first_time = times[0] if times else 0.0
    anchors: list[dict[str, Any]] = []
    for index, replay in enumerate(replay_records):
        dmo = replay["dmo"]
        eligible = bool(replay["score_eligible"])
        anchor: dict[str, Any] = {
            "anchor_id": replay["source_row_id"],
            "accepted_index": replay["accepted_index"],
            "event_time": replay["event_time"],
            "score_eligible": eligible,
            "block_id": int((times[index] - first_time) // (BLOCK_MINUTES * 60.0)),
            "transition_stratum": replay["transition_stratum"],
            "direction": directions[index],
            "strength": dmo["strength"],
            "coherence": dmo["coherence"],
            "persistence": dmo["persistence"],
            "uncertainty": dmo["uncertainty"],
            "reversal_propensity": dmo["reversal_propensity"],
            "perturbation_magnitude": dmo["perturbation_magnitude"],
            "perturbation_class": dmo["perturbation_class"],
            "observation_half_life": dmo["observation_half_life"],
            "forward_half_life": dmo["forward_half_life"],
            "forward_interval": replay["fmo"]["interval_length"],
        }
        if not eligible:
            anchors.append(anchor)
            continue
        fixed: dict[str, object] = {}
        fixed_reasons: dict[str, str] = {}
        for horizon in FIXED_HORIZONS_MINUTES:
            geometry, reason = _coordinate(index, horizon, times, closes, directions[index])
            key = f"{horizon:g}m"
            if geometry is None:
                fixed_reasons[key] = str(reason)
            else:
                fixed[key] = geometry
        adaptive: dict[str, object] = {}
        adaptive_reasons: dict[str, str] = {}
        for key, requested in _adaptive_requests(replay).items():
            geometry, reason = _coordinate(index, requested, times, closes, directions[index])
            if geometry is None:
                adaptive_reasons[key] = str(reason)
            else:
                adaptive[key] = geometry
        anchor["fixed"] = fixed
        anchor["fixed_exclusions"] = fixed_reasons
        anchor["adaptive"] = adaptive
        anchor["adaptive_exclusions"] = adaptive_reasons
        anchor["duration"] = _duration(index, times, closes, directions, strata).__dict__
        primary = fixed.get("15m")
        if primary is None:
            reason = fixed_reasons.get("15m", "COORDINATE_UNAVAILABLE")
            for dimension in ("state_kinematics", "strength", "coherence", "uncertainty", "perturbation_magnitude", "perturbation_class"):
                anchor[f"{dimension}_exclusion_reason"] = reason
        else:
            geometry = primary
            efficiency = float(geometry["efficiency"])
            slope = float(geometry["slope"])
            ambiguity = ambiguity_index(efficiency, float(geometry["normalized_deviation"]), str(geometry["category"]))
            anchor.update({
                "slope_15": slope,
                "state_concordant_15": None if directions[index] == 0 or slope == 0 else bool(directions[index] * slope > 0),
                "strength_expression": abs(slope) * efficiency,
                "efficiency": efficiency,
                "ambiguity_index": ambiguity,
                "transition_magnitude": transition_magnitude(float(geometry["displacement"]), slope, 15.0),
                "realized_category_15": geometry["category"],
            })
            if ambiguity is None:
                anchor["uncertainty_exclusion_reason"] = "AMBIGUITY_COMPONENT_UNAVAILABLE"
        anchors.append(anchor)
    return anchors


def write_anchor_jsonl(path: Path, records: Iterable[dict[str, Any]], authority: dict[str, Any]) -> str:
    materialized = list(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in materialized:
            handle.write(canonical_json(record) + "\n")
    return logical_seal(materialized, authority)


def read_anchor_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
