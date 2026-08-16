from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .authority import bootstrap_seed
from .constants import BOOTSTRAP_REPLICATES, DIMENSIONS, FIXED_HORIZONS_MINUTES
from .observer import Duration


PRIMARY_SPEARMAN_FIELDS = {
    "strength": ("strength", "strength_expression"),
    "coherence": ("coherence", "efficiency"),
    "uncertainty": ("uncertainty", "ambiguity_index"),
}


def _ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + end - 1) / 2.0 + 1.0
        start = end
    return ranks


def spearman(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2:
        return None
    rx, ry = _ranks(np.asarray(x, dtype=float)), _ranks(np.asarray(y, dtype=float))
    if np.ptp(rx) == 0 or np.ptp(ry) == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def primary_spearman_score(dimension: str, anchor_records: list[dict[str, object]]) -> dict[str, object]:
    if dimension not in PRIMARY_SPEARMAN_FIELDS:
        raise ValueError(f"UNSUPPORTED_PRIMARY_SPEARMAN_DIMENSION:{dimension}")
    predictor_field, outcome_field = PRIMARY_SPEARMAN_FIELDS[dimension]
    predictors: list[float] = []
    outcomes: list[float] = []
    exclusions: dict[str, int] = {}
    seen: set[object] = set()
    eligible = 0
    for record in anchor_records:
        if not bool(record.get("score_eligible")):
            continue
        eligible += 1
        anchor_id = record.get("anchor_id")
        if anchor_id in seen:
            raise ValueError(f"DUPLICATE_ANCHOR_RECORD:{anchor_id}")
        seen.add(anchor_id)
        reason = record.get(f"{dimension}_exclusion_reason")
        if reason:
            exclusions[str(reason)] = exclusions.get(str(reason), 0) + 1
            continue
        predictor = record.get(predictor_field)
        outcome = record.get(outcome_field)
        if predictor is None or not np.isfinite(float(predictor)):
            exclusions["NONFINITE_PREDICTOR"] = exclusions.get("NONFINITE_PREDICTOR", 0) + 1
            continue
        if outcome is None or not np.isfinite(float(outcome)):
            reason = "AMBIGUITY_COMPONENT_UNAVAILABLE" if dimension == "uncertainty" else "COORDINATE_UNAVAILABLE"
            exclusions[reason] = exclusions.get(reason, 0) + 1
            continue
        predictors.append(float(predictor))
        outcomes.append(float(outcome))
    effect = spearman(predictors, outcomes)
    return {
        "dimension": dimension,
        "primary_coordinate": "fixed_15m",
        "statistic": "spearman",
        "effect": effect,
        "null": 0.0,
        "expected_direction": "positive",
        "eligible_anchors": eligible,
        "available_records": len(predictors),
        "excluded_records": eligible - len(predictors),
        "exclusion_counts": dict(sorted(exclusions.items())),
        "record_weighting": "one_valid_anchor_one_record_equal_weight",
        "pooled_horizons": False,
        "best_horizon_selection": False,
    }


def state_c15(direction: list[int], slopes: list[float]) -> dict[str, float | int | None]:
    valid = [(d, b) for d, b in zip(direction, slopes, strict=True) if d != 0 and b != 0]
    if not valid:
        return {"concordance": None, "effect": None, "valid_anchors": 0}
    concordance = sum(d * b > 0 for d, b in valid) / len(valid)
    return {"concordance": concordance, "effect": concordance - 0.5, "valid_anchors": len(valid)}


def class_contrasts(classes: list[str], categories: list[str]) -> dict[str, float | None]:
    def incidence(class_name: str, outcome: str) -> float | None:
        selected = [category == outcome for cls, category in zip(classes, categories, strict=True) if cls == class_name]
        return None if not selected else sum(selected) / len(selected)
    reinforcing_weak = incidence("REINFORCING", "WEAKENING")
    contradicting_weak = incidence("CONTRADICTING", "WEAKENING")
    reinforcing_rev = incidence("REINFORCING", "REVERSAL")
    reversing_rev = incidence("REVERSING", "REVERSAL")
    return {
        "delta_rc": None if reinforcing_weak is None or contradicting_weak is None else contradicting_weak - reinforcing_weak,
        "delta_rv": None if reinforcing_rev is None or reversing_rev is None else reversing_rev - reinforcing_rev,
    }


def _certain_order(left: Duration, right: Duration) -> int | None:
    if left.censor_type == "RIGHT" and right.censor_type == "RIGHT":
        return None
    if left.censor_type == "EXACT" and right.censor_type == "EXACT" and left.lower == right.lower:
        return 0
    if left.censor_type == "EXACT" and left.lower < right.lower:
        return -1
    if right.censor_type == "EXACT" and right.lower < left.lower:
        return 1
    if left.censor_type == "INTERVAL" and left.upper is not None and left.upper < right.lower:
        return -1
    if right.censor_type == "INTERVAL" and right.upper is not None and right.upper < left.lower:
        return 1
    return None


def censor_aware_concordance(predictors: list[float], durations: list[Duration], reverse_orientation: bool = False) -> dict[str, float | int | None]:
    if len(predictors) != len(durations):
        raise ValueError("PREDICTOR_DURATION_LENGTH_MISMATCH")
    oriented = [-value if reverse_orientation else value for value in predictors]
    unique_predictors = sorted(set(oriented))
    ranks = {value: index + 1 for index, value in enumerate(unique_predictors)}
    tree = [0] * (len(unique_predictors) + 1)

    def update(position: int) -> None:
        while position < len(tree):
            tree[position] += 1
            position += position & -position

    def prefix(position: int) -> int:
        total = 0
        while position:
            total += tree[position]
            position -= position & -position
        return total

    later = sorted(range(len(durations)), key=lambda index: durations[index].lower, reverse=True)
    events = sorted(
        (index for index, duration in enumerate(durations) if duration.censor_type in {"EXACT", "INTERVAL"}),
        key=lambda index: durations[index].lower if durations[index].censor_type == "EXACT" else float(durations[index].upper),
        reverse=True,
    )
    inserted = 0
    comparable = 0
    score_sum = 0.0
    for event_index in events:
        duration = durations[event_index]
        event_end = duration.lower if duration.censor_type == "EXACT" else float(duration.upper)
        while inserted < len(later) and durations[later[inserted]].lower > event_end:
            update(ranks[oriented[later[inserted]]])
            inserted += 1
        rank = ranks[oriented[event_index]]
        lower_count = prefix(rank - 1)
        equal_count = prefix(rank) - lower_count
        greater_count = inserted - prefix(rank)
        comparable += inserted
        score_sum += greater_count + 0.5 * equal_count

    exact_groups: dict[float, int] = {}
    for duration in durations:
        if duration.censor_type == "EXACT":
            exact_groups[duration.lower] = exact_groups.get(duration.lower, 0) + 1
    exact_ties = sum(count * (count - 1) // 2 for count in exact_groups.values())
    comparable += exact_ties
    score_sum += 0.5 * exact_ties
    total_pairs = len(durations) * (len(durations) - 1) // 2
    concordance = None if comparable == 0 else score_sum / comparable
    return {
        "concordance": concordance, "effect": None if concordance is None else concordance - 0.5,
        "comparable_pairs": comparable, "noncomparable_pairs": total_pairs - comparable,
        "exact_events": sum(item.censor_type == "EXACT" for item in durations),
        "interval_events": sum(item.censor_type == "INTERVAL" for item in durations),
        "right_censored": sum(item.censor_type == "RIGHT" for item in durations),
    }


def support_label(block_count: int) -> str:
    return "ADEQUATE" if block_count >= 30 else "LIMITED" if block_count >= 10 else "INSUFFICIENT"


def classify(effect: float | None, interval: tuple[float, float] | None, support: str, expected_positive: bool = True) -> str:
    if effect is None or interval is None or support == "INSUFFICIENT":
        return "INCONCLUSIVE"
    oriented_effect = effect if expected_positive else -effect
    oriented_interval = interval if expected_positive else (-interval[1], -interval[0])
    if support == "ADEQUATE" and oriented_interval[1] < 0:
        return "UNSUPPORTED"
    if support == "ADEQUATE" and oriented_effect > 0 and oriented_interval[0] > 0:
        return "EMPIRICALLY_SUPPORTED"
    if oriented_effect > 0 or support == "LIMITED":
        return "PARTIALLY_SUPPORTED"
    return "INCONCLUSIVE"


def moving_block_bootstrap(records: list[dict[str, object]], statistic: Callable[[list[dict[str, object]]], float | None], replicates: int = BOOTSTRAP_REPLICATES, seed: int | None = None) -> dict[str, object]:
    blocks: dict[int, list[dict[str, object]]] = {}
    for record in records:
        blocks.setdefault(int(record["block_id"]), []).append(record)
    ordered = [blocks[key] for key in sorted(blocks)]
    if not ordered:
        return {"interval": None, "failures": replicates, "replicates": replicates, "block_count": 0}
    rng = np.random.default_rng(bootstrap_seed() if seed is None else seed)
    estimates: list[float] = []
    failures = 0
    for _ in range(replicates):
        sample = [row for index in rng.integers(0, len(ordered), len(ordered)) for row in ordered[int(index)]]
        estimate = statistic(sample)
        if estimate is None or not np.isfinite(estimate):
            failures += 1
        else:
            estimates.append(float(estimate))
    interval = None if not estimates else tuple(float(value) for value in np.percentile(estimates, [2.5, 97.5]))
    return {"interval": interval, "failures": failures, "replicates": replicates, "block_count": len(ordered), "interval_type": "two-sided 95% percentile"}


def _duration_from_record(record: dict[str, object]) -> Duration | None:
    payload = record.get("duration")
    if not isinstance(payload, dict) or payload.get("censor_type") == "INCONCLUSIVE":
        return None
    return Duration(str(payload["censor_type"]), float(payload["lower"]), None if payload.get("upper") is None else float(payload["upper"]))


def _available(records: list[dict[str, object]], required: tuple[str, ...]) -> list[dict[str, object]]:
    return [
        record for record in records
        if bool(record.get("score_eligible")) and all(record.get(field) is not None for field in required)
    ]


def _bootstrap_result(records: list[dict[str, object]], statistic: Callable[[list[dict[str, object]]], float | None], replicates: int) -> tuple[dict[str, object], str]:
    bootstrap = moving_block_bootstrap(records, statistic, replicates=replicates)
    return bootstrap, support_label(int(bootstrap["block_count"]))


def _secondary_fixed(records: list[dict[str, object]], kind: str) -> dict[str, object]:
    diagnostics: dict[str, object] = {}
    for horizon in FIXED_HORIZONS_MINUTES:
        key = f"{horizon:g}m"
        available = [record for record in records if bool(record.get("score_eligible")) and key in record.get("fixed", {})]
        if kind == "state":
            result = state_c15(
                [int(record["direction"]) for record in available],
                [float(record["fixed"][key]["slope"]) for record in available],
            )
        else:
            predictor_field, outcome_name = PRIMARY_SPEARMAN_FIELDS[kind]
            predictors = [float(record[predictor_field]) for record in available]
            if outcome_name == "strength_expression":
                outcomes = [abs(float(record["fixed"][key]["slope"])) * float(record["fixed"][key]["efficiency"]) for record in available]
            elif outcome_name == "ambiguity_index":
                outcomes = [
                    ambiguity for record in available
                    if (ambiguity := (1.0 - float(record["fixed"][key]["efficiency"]) + float(record["fixed"][key]["normalized_deviation"]) / (1.0 + float(record["fixed"][key]["normalized_deviation"])) + (1.0 if record["fixed"][key]["category"] == "AMBIGUOUS/INCONCLUSIVE" else 0.0)) / 3.0) is not None
                ]
            else:
                outcomes = [float(record["fixed"][key]["efficiency"]) for record in available]
            result = {"effect": spearman(predictors[:len(outcomes)], outcomes), "available_records": len(outcomes)}
        diagnostics[key] = result
    return diagnostics


def score_dimension(dimension: str, records: list[dict[str, object]], replicates: int = BOOTSTRAP_REPLICATES) -> dict[str, object]:
    if dimension not in DIMENSIONS:
        raise ValueError(f"UNKNOWN_DIMENSION:{dimension}")
    eligible_count = sum(bool(record.get("score_eligible")) for record in records)
    if dimension in PRIMARY_SPEARMAN_FIELDS:
        result = primary_spearman_score(dimension, records)
        available = _available(records, PRIMARY_SPEARMAN_FIELDS[dimension])
        predictor, outcome = PRIMARY_SPEARMAN_FIELDS[dimension]
        statistic = lambda sample: spearman([float(row[predictor]) for row in sample], [float(row[outcome]) for row in sample])
        bootstrap, support = _bootstrap_result(available, statistic, replicates)
        result.update({"bootstrap": bootstrap, "support": support, "classification": classify(result["effect"], bootstrap["interval"], support), "secondary_fixed": _secondary_fixed(records, dimension), "secondary_changes_primary": False})
        return result
    if dimension == "state_kinematics":
        available = _available(records, ("direction", "slope_15", "state_concordant_15"))
        statistic = lambda sample: state_c15([int(row["direction"]) for row in sample], [float(row["slope_15"]) for row in sample])["effect"]
        point = statistic(available)
        bootstrap, support = _bootstrap_result(available, statistic, replicates)
        return {"dimension": dimension, "effect": point, "null": 0.0, "primary_coordinate": "fixed_15m", "available_records": len(available), "eligible_anchors": eligible_count, "bootstrap": bootstrap, "support": support, "classification": classify(point, bootstrap["interval"], support), "secondary_fixed": _secondary_fixed(records, "state")}
    if dimension == "perturbation_magnitude":
        available = _available(records, ("perturbation_magnitude", "transition_magnitude"))
        statistic = lambda sample: spearman([float(row["perturbation_magnitude"]) for row in sample], [float(row["transition_magnitude"]) for row in sample])
        point = statistic(available)
        bootstrap, support = _bootstrap_result(available, statistic, replicates)
        return {"dimension": dimension, "effect": point, "null": 0.0, "primary_coordinate": "fixed_15m", "available_records": len(available), "eligible_anchors": eligible_count, "bootstrap": bootstrap, "support": support, "classification": classify(point, bootstrap["interval"], support)}
    if dimension == "perturbation_class":
        available = _available(records, ("perturbation_class", "realized_category_15"))
        contrast = class_contrasts([str(row["perturbation_class"]) for row in available], [str(row["realized_category_15"]) for row in available])
        outputs: dict[str, object] = {}
        classifications: list[str] = []
        for key in ("delta_rc", "delta_rv"):
            statistic = lambda sample, contrast_key=key: class_contrasts([str(row["perturbation_class"]) for row in sample], [str(row["realized_category_15"]) for row in sample])[contrast_key]
            bootstrap, support = _bootstrap_result(available, statistic, replicates)
            classification = classify(contrast[key], bootstrap["interval"], support)
            classifications.append(classification)
            outputs[key] = {"effect": contrast[key], "null": 0.0, "bootstrap": bootstrap, "support": support, "classification": classification}
        if "INCONCLUSIVE" in classifications:
            overall = "INCONCLUSIVE"
        elif "UNSUPPORTED" in classifications:
            overall = "UNSUPPORTED"
        elif classifications == ["EMPIRICALLY_SUPPORTED", "EMPIRICALLY_SUPPORTED"]:
            overall = "EMPIRICALLY_SUPPORTED"
        else:
            overall = "PARTIALLY_SUPPORTED"
        return {"dimension": dimension, "primary_coordinate": "fixed_15m", "eligible_anchors": eligible_count, "available_records": len(available), "co_primary": outputs, "classification": overall, "composite_effect": None}

    predictor_field = {
        "persistence": "persistence",
        "reversal_propensity": "reversal_propensity",
        "observation_half_life": "observation_half_life",
        "forward_half_life": "forward_half_life",
        "forward_interval": "forward_interval",
    }[dimension]
    available = [record for record in records if bool(record.get("score_eligible")) and record.get(predictor_field) is not None and _duration_from_record(record) is not None]
    reverse = dimension == "reversal_propensity"
    def statistic(sample: list[dict[str, object]]) -> float | None:
        durations = [_duration_from_record(row) for row in sample]
        return censor_aware_concordance([float(row[predictor_field]) for row in sample], [duration for duration in durations if duration is not None], reverse)["effect"]
    point_details = censor_aware_concordance([float(row[predictor_field]) for row in available], [_duration_from_record(row) for row in available], reverse)
    bootstrap, support = _bootstrap_result(available, statistic, replicates)
    return {"dimension": dimension, "effect": point_details["effect"], "null": 0.0, "primary_coordinate": "full_survival", "orientation": "shorter_duration" if reverse else "longer_duration", "eligible_anchors": eligible_count, "available_records": len(available), "pair_counts": point_details, "bootstrap": bootstrap, "support": support, "classification": classify(point_details["effect"], bootstrap["interval"], support), "secondary_adaptive": {"multipliers": [0.5, 1.0, 2.0], "diagnostic_only": True}}