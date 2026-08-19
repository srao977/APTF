from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Callable


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    rank = (len(ordered) - 1) * probability
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def describe(values: list[float], probabilities: tuple[float, ...]) -> dict[str, Any]:
    result = {
        "count": len(values),
        "minimum": min(values),
        "maximum": max(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "population_standard_deviation": statistics.pstdev(values),
    }
    result.update({f"P{int(p * 100):02d}": percentile(values, p) for p in probabilities})
    return result


def pearson(left: list[float], right: list[float]) -> float | None:
    mean_left, mean_right = statistics.fmean(left), statistics.fmean(right)
    numerator = sum((x - mean_left) * (y - mean_right) for x, y in zip(left, right))
    denominator = math.sqrt(sum((x - mean_left) ** 2 for x in left) * sum((y - mean_right) ** 2 for y in right))
    return None if denominator == 0.0 else numerator / denominator


def longest_predicate_run(records: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
    best: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for record in records:
        if predicate(record):
            current.append(record)
            if len(current) > len(best):
                best = list(current)
        else:
            current = []
    if not best:
        return {"length": 0, "start_cycle": None, "end_cycle": None, "start_row": None, "end_row": None}
    return {"length": len(best), "start_cycle": best[0]["cycle"], "end_cycle": best[-1]["cycle"], "start_row": best[0]["physical_row"], "end_row": best[-1]["physical_row"], "starting_C": best[0]["C"], "ending_C": best[-1]["C"]}


def monotonic_run(records: list[dict[str, Any]], rising: bool) -> dict[str, Any]:
    best_start = best_end = 0
    start = 0
    for index in range(1, len(records)):
        qualifies = records[index]["C"] > records[index - 1]["C"] if rising else records[index]["C"] < records[index - 1]["C"]
        if not qualifies:
            start = index
        if index - start > best_end - best_start:
            best_start, best_end = start, index
    first, last = records[best_start], records[best_end]
    return {"start_cycle": first["cycle"], "end_cycle": last["cycle"], "start_row": first["physical_row"], "end_row": last["physical_row"], "duration_observations": best_end - best_start + 1, "duration_minutes_between_endpoints": best_end - best_start, "starting_C": first["C"], "ending_C": last["C"], "total_C_change": last["C"] - first["C"]}


def compact(record: dict[str, Any], rank: int | None = None) -> dict[str, Any]:
    result = {"cycle": record["cycle"], "physical_row": record["physical_row"], "source_timestamp": record["source_timestamp"], **record["source"], "H": record["H"], "Q_G": record["Q_G"], "Q_S": record["Q_S"], "Q_R": record["Q_R"], "C": record["C"], "shortfall_from_0_75": record["open_shortfall"], "D04_state": record["D04_new_state"], "D03_state": record["D03_state"], "position_controller_decision": record["position_controller_decision"]}
    if rank is not None:
        result = {"rank": rank, **result}
    return result


def metadata(trace: dict[str, Any]) -> dict[str, Any]:
    return {name: trace[name] for name in ("run_id", "freeze_id", "freeze_manifest_sha256", "source_data_sha256", "execution_timestamp_utc")}


def write(root: Path, name: str, trace: dict[str, Any], body: dict[str, Any]) -> None:
    (root / name).write_text(json.dumps({**metadata(trace), **body}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def derive(trace_path: Path, root: Path) -> None:
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    records = trace["records"]
    if len(records) != 100:
        raise RuntimeError("trace does not contain exactly 100 records")
    c_values = [record["C"] for record in records]
    probabilities = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
    factor_probabilities = (0.10, 0.25, 0.50, 0.75, 0.90, 0.95)

    write(root, "APTF_TEST_005_FROZEN_INPUTS_V0_2.json", trace, {"source": trace["source"], "initialization": trace["initialization"], "inputs": [{"cycle": r["cycle"], "physical_row": r["physical_row"], "source_timestamp": r["source_timestamp"], "source": r["source"], "source_payload": r["source_payload"]} for r in records]})
    write(root, "APTF_TEST_005_FROZEN_D04_RECONSTRUCTION_V0_2.json", trace, {"equation": "C = H * Q_G * Q_S * Q_R", "rows": [{name: r[name] for name in ("cycle", "physical_row", "source_timestamp", "H", "Q_G", "Q_S", "Q_R", "C_reconstructed", "C", "reconstruction_delta")} for r in records], "maximum_reconstruction_error": max(r["reconstruction_delta"] for r in records), "all_pass": all(r["reconstruction_delta"] == 0.0 for r in records)})

    differences = [{"cycle": r["cycle"], "physical_row": r["physical_row"], "delta_C": r["C"] - records[index - 1]["C"]} for index, r in enumerate(records) if index]
    absolute_differences = [abs(item["delta_C"]) for item in differences]
    ordered_high = sorted(records, key=lambda r: (-r["C"], r["cycle"]))
    ordered_low = sorted(records, key=lambda r: (r["C"], r["cycle"]))
    bands = {
        "C_LT_0_25": sum(r["C"] < 0.25 for r in records),
        "C_GE_0_25_LT_0_40": sum(0.25 <= r["C"] < 0.40 for r in records),
        "C_GE_0_40_LT_0_50": sum(0.40 <= r["C"] < 0.50 for r in records),
        "C_GE_0_50_LT_0_55": sum(0.50 <= r["C"] < 0.55 for r in records),
        "C_GE_0_55_LT_0_65": sum(0.55 <= r["C"] < 0.65 for r in records),
        "C_GE_0_65_LT_0_70": sum(0.65 <= r["C"] < 0.70 for r in records),
        "C_GE_0_70_LT_0_75": sum(0.70 <= r["C"] < 0.75 for r in records),
        "C_GE_0_75": sum(r["C"] >= 0.75 for r in records)
    }
    c_distribution = {"percentile_convention": "linear interpolation at rank (n-1)*p", "distribution": describe(c_values, probabilities), "bands": bands, "top_10": [compact(r, i + 1) for i, r in enumerate(ordered_high[:10])], "bottom_10": [compact(r, i + 1) for i, r in enumerate(ordered_low[:10])], "maximum_actual_observation": compact(ordered_high[0]), "trajectory": [{"cycle": r["cycle"], "physical_row": r["physical_row"], "source_timestamp": r["source_timestamp"], "C": r["C"], "delta_C": None if i == 0 else r["C"] - records[i - 1]["C"]} for i, r in enumerate(records)], "first_difference_summary": {"maximum_positive_delta": max(item["delta_C"] for item in differences), "maximum_negative_delta": min(item["delta_C"] for item in differences), "mean_absolute_delta": statistics.fmean(absolute_differences), "median_absolute_delta": statistics.median(absolute_differences)}, "longest_increasing_run": monotonic_run(records, True), "longest_decreasing_run": monotonic_run(records, False)}
    write(root, "APTF_TEST_005_FROZEN_C_DISTRIBUTION_V0_2.json", trace, c_distribution)

    factors = {}
    maxima = {}
    lowest_counts = Counter()
    tie_patterns = Counter()
    for factor in ("Q_G", "Q_S", "Q_R"):
        values = [r[factor] for r in records]
        factors[factor] = describe(values, factor_probabilities)
        maximum = max(values)
        maxima[factor] = [compact(r) for r in records if r[factor] == maximum]
    for record in records:
        names = record["lowest_current_multiplicative_factors"]
        for name in names:
            lowest_counts[name] += 1
        if len(names) > 1:
            tie_patterns["+".join(names)] += 1
    write(root, "APTF_TEST_005_FROZEN_FACTOR_DISTRIBUTIONS_V0_2.json", trace, {"H_counts": dict(Counter(str(r["H"]) for r in records)), "distributions": factors, "factor_maximum_observations": maxima, "lowest_current_multiplicative_factor_counts_including_ties": dict(lowest_counts), "tie_patterns": dict(tie_patterns), "association_with_C": {factor: pearson([r[factor] for r in records], c_values) for factor in ("Q_G", "Q_S", "Q_R")}, "association_classification": "STRUCTURALLY RELATED BY PRODUCT EQUATION; NOT INDEPENDENT CAUSAL DISCOVERY", "cross_row_independent_max_product_calculated": False})

    thresholds = (0.50, 0.55, 0.60, 0.65, 0.70, 0.725, 0.74, 0.75)
    write(root, "APTF_TEST_005_FROZEN_THRESHOLD_PROXIMITY_V0_2.json", trace, {"open_threshold": 0.75, "counts": {str(value): sum(r["C"] >= value for r in records) for value in thresholds}, "longest_runs": {str(value): longest_predicate_run(records, lambda r, threshold=value: r["C"] >= threshold) for value in thresholds}, "first_events": trace["first_events"], "analysis_only_not_new_thresholds": True})

    state_counts = Counter(r["D04_new_state"] for r in records)
    opening_1 = sum(r["D04_new_state"] == "OPENING" and r["opening_counter"] == 1 for r in records)
    opening_2 = sum(r["D04_new_state"] == "OPENING" and r["opening_counter"] == 2 for r in records)
    transitions = [{"cycle": r["cycle"], "physical_row": r["physical_row"], "source_timestamp": r["source_timestamp"], "C": r["C"], "previous_state": r["D04_previous_state"], "resulting_state": r["D04_new_state"], "opening_counter": r["opening_counter"], "closing_counter": r["closing_counter"], "transition_event_id": r["D04_transition_event_id"]} for r in records if r["D04_previous_state"] != r["D04_new_state"]]
    write(root, "APTF_TEST_005_FROZEN_D04_STATE_ANALYSIS_V0_2.json", trace, {"state_counts": dict(state_counts), "derived_persistence_positions": {"OPENING_1": opening_1, "OPENING_2": opening_2, "note": "Current enum uses OPENING plus persistence counter."}, "transitions": transitions, "transition_count": len(transitions), "any_opening": state_counts["OPENING"] > 0, "any_open": state_counts["OPEN"] > 0})
    d03_counts = Counter(r["D03_state"] for r in records)
    write(root, "APTF_TEST_005_FROZEN_D03_STATE_ANALYSIS_V0_2.json", trace, {"state_counts": {name: d03_counts[name] for name in ("FLAT", "LONG", "SHORT")}, "other_states": {k: v for k, v in d03_counts.items() if k not in {"FLAT", "LONG", "SHORT"}}, "non_flat_count": sum(r["D03_state"] != "FLAT" for r in records), "first_non_flat": next((compact(r) for r in records if r["D03_state"] != "FLAT"), None)})
    verbs = Counter(verb for r in records for verb in r["position_controller_decision"])
    vocabulary = ("BUY", "SELL", "HOLD", "SELL_SHORT", "BUY_TO_COVER", "NO_ACTION")
    write(root, "APTF_TEST_005_FROZEN_POSITION_CONTROLLER_ANALYSIS_V0_2.json", trace, {"decision_counts": {name: verbs[name] for name in vocabulary}, "other_decisions": {k: v for k, v in verbs.items() if k not in vocabulary}, "non_no_action_count": sum(r["position_controller_decision"] != ["NO_ACTION"] for r in records), "first_non_no_action": next((compact(r) for r in records if r["position_controller_decision"] != ["NO_ACTION"]), None)})

    source_rows = []
    for index, record in enumerate(records):
        prior = records[index - 1] if index else None
        volume = record["source"]["volume"]
        close = record["source"]["close"]
        delta_volume = None if prior is None else volume - prior["source"]["volume"]
        delta_close = None if prior is None else close - prior["source"]["close"]
        source_rows.append({"cycle": record["cycle"], "physical_row": record["physical_row"], "source_timestamp": record["source_timestamp"], "volume": volume, "delta_volume": delta_volume, "absolute_delta_volume": None if delta_volume is None else abs(delta_volume), "percent_delta_volume": None if prior is None or prior["source"]["volume"] == 0 else delta_volume / prior["source"]["volume"] * 100.0, "close": close, "delta_close": delta_close, "absolute_delta_close": None if delta_close is None else abs(delta_close), "percent_delta_close": None if prior is None or prior["source"]["close"] == 0 else delta_close / prior["source"]["close"] * 100.0, "high_low_range": record["source"]["high"] - record["source"]["low"], "Q_G": record["Q_G"], "Q_S": record["Q_S"], "Q_R": record["Q_R"], "C": record["C"], "D04": record["D04_new_state"], "D03": record["D03_state"], "position_controller_decision": record["position_controller_decision"]})
    comparable = source_rows[1:]
    largest_abs_volume = max(comparable, key=lambda r: r["absolute_delta_volume"])
    largest_abs_close = max(comparable, key=lambda r: r["absolute_delta_close"])
    largest_range = max(source_rows, key=lambda r: r["high_low_range"])
    write(root, "APTF_TEST_005_FROZEN_SOURCE_VARIATION_ANALYSIS_V0_2.json", trace, {"rows": source_rows, "volume": {"minimum": min(r["volume"] for r in source_rows), "maximum": max(r["volume"] for r in source_rows), "median": statistics.median(r["volume"] for r in source_rows), "largest_positive_change": max(r["delta_volume"] for r in comparable), "largest_negative_change": min(r["delta_volume"] for r in comparable), "largest_absolute_change_observation": largest_abs_volume, "largest_valid_percentage_change_observation": max(comparable, key=lambda r: abs(r["percent_delta_volume"]))}, "price": {"minimum_close": min(r["close"] for r in source_rows), "maximum_close": max(r["close"] for r in source_rows), "largest_positive_close_change": max(r["delta_close"] for r in comparable), "largest_negative_close_change": min(r["delta_close"] for r in comparable), "largest_high_low_range_observation": largest_range}, "large_source_perturbations": {"largest_absolute_volume_change": largest_abs_volume, "largest_absolute_close_change": largest_abs_close, "largest_high_low_range": largest_range}, "descriptive_association_not_causal_proof": {"C_vs_volume": pearson(c_values, [r["volume"] for r in source_rows]), "C_vs_absolute_volume_change_cycles_2_100": pearson(c_values[1:], [r["absolute_delta_volume"] for r in comparable]), "C_vs_close": pearson(c_values, [r["close"] for r in source_rows]), "C_vs_absolute_close_change_cycles_2_100": pearson(c_values[1:], [r["absolute_delta_close"] for r in comparable]), "C_vs_high_low_range": pearson(c_values, [r["high_low_range"] for r in source_rows])}})

    temporal_rows = [{"cycle": r["cycle"], "physical_row": r["physical_row"], "source_timestamp": r["source_timestamp"], "timing": r["timing"], "checks": r["checks"], "temporal_lineage": r["temporal_lineage"]} for r in records]
    write(root, "APTF_TEST_005_FROZEN_TEMPORAL_ANALYSIS_V0_2.json", trace, {"rows": temporal_rows, "valid_lifecycles": sum(all(r["checks"].values()) and len(r["temporal_lineage"]) == 6 for r in records), "nanosecond_timing_pass": all(all(isinstance(value, int) and value >= 0 for value in r["timing"]["stage_duration_ns"].values()) and isinstance(r["timing"]["direct_end_to_end_ns"], int) for r in records), "direct_measurements": len(records), "component_measurements": len(records), "direct_component_comparisons": len(records), "difference_ns_distribution": describe([r["timing"]["difference_ns"] for r in records], (0.10, 0.50, 0.90)), "continuity": trace["continuity"], "continuity_links_passed": sum(all(link[name] for name in ("D01", "D04", "controller")) for link in trace["continuity"])})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    derive(args.trace, args.root)
    print("TEST005_FROZEN_ANALYSIS=COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())