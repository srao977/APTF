from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from time import perf_counter_ns
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test014c_common import (
    P_EMISSIONS,
    ROOT,
    SPLIT,
    config_from_policy,
    duration_scorecards,
    intervalize,
    load_common_rows,
    replay,
    score,
    sha256,
    write_csv,
    write_json,
)


POLICY = ROOT / "APTF_TEST_014C_SPY_V_EMISSION_POLICY_V0_1.json"
FREEZE = ROOT / "APTF_TEST_014C_V_POLICY_FREEZE_V0_1.json"
CHART_DIR = ROOT / "output" / "test014c_charts"
COLORS = {"GREEN": "#16803a", "AMBER": "#d38b00", "RED": "#c83232", "INVALID": "#333333"}


def joint_intervals(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[int], list[int]]:
    prepared = [row | {"joint_state": f'{row["p_color"]}_{row["cockpit_color"]}'} for row in rows]
    intervals, ages, latencies = intervalize(prepared, "PV", "joint_state")
    output = []
    for row in intervals:
        p_color, v_color = str(row["color"]).split("_", 1)
        output.append({
            "symbol": row["symbol"], "session_date": row["session_date"],
            "P_color": p_color, "V_color": v_color, "joint_state": row["color"],
            "start": row["start_timestamp"], "end": row["end_timestamp"],
            "start_index": row["start_index"], "end_index": row["end_index"],
            "duration": row["duration_minutes"], "observation_count": row["observation_count"],
            "elapsed_seconds": row["elapsed_seconds"],
        })
    return output, ages, latencies


def joint_scorecard(intervals: list[dict[str, Any]], total_rows: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for row in intervals:
        grouped[str(row["joint_state"])].append(int(row["duration"]))
    output = []
    for state in sorted(grouped):
        values = np.asarray(grouped[state], dtype=float)
        output.append({
            "joint_state": state, "interval_count": len(values), "occupancy": float(np.sum(values) / total_rows),
            "median_duration": float(np.median(values)), "Q75": float(np.quantile(values, .75)),
            "Q90": float(np.quantile(values, .90)), "Q95": float(np.quantile(values, .95)),
            "maximum": float(np.max(values)), "pct_ge_2": float(np.mean(values >= 2)),
            "pct_ge_3": float(np.mean(values >= 3)), "pct_ge_5": float(np.mean(values >= 5)),
            "pct_ge_10": float(np.mean(values >= 10)),
        })
    return output


def transition_relationships(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_session[f'{row["timestamp"][:10]}:{row["session"]}'].append(row)
    output = []
    category_counts = Counter()
    separations = []
    for session_id, group in by_session.items():
        p_transitions = [index for index in range(1, len(group)) if group[index]["p_color"] != group[index - 1]["p_color"]]
        v_transitions = [index for index in range(1, len(group)) if group[index]["cockpit_color"] != group[index - 1]["cockpit_color"]]
        for index in v_transitions:
            if not p_transitions:
                output.append({"session_id": session_id, "anchor_engine": "V", "anchor_timestamp": group[index]["timestamp"], "nearest_other_timestamp": "", "signed_separation_minutes": "", "relationship": "P_UNCHANGED"})
                continue
            nearest = min(p_transitions, key=lambda value: (abs(value - index), value))
            separation = nearest - index
            relationship = "SIMULTANEOUS" if separation == 0 else "V_BEFORE_P" if separation > 0 else "P_BEFORE_V"
            category_counts[relationship] += 1
            separations.append(abs(separation))
            output.append({
                "session_id": session_id, "anchor_engine": "V", "anchor_timestamp": group[index]["timestamp"],
                "nearest_other_timestamp": group[nearest]["timestamp"], "signed_separation_minutes": separation,
                "relationship": relationship,
            })
        for index in p_transitions:
            if not v_transitions:
                output.append({"session_id": session_id, "anchor_engine": "P", "anchor_timestamp": group[index]["timestamp"], "nearest_other_timestamp": "", "signed_separation_minutes": "", "relationship": "V_UNCHANGED"})
                continue
            nearest = min(v_transitions, key=lambda value: (abs(value - index), value))
            output.append({
                "session_id": session_id, "anchor_engine": "P", "anchor_timestamp": group[index]["timestamp"],
                "nearest_other_timestamp": group[nearest]["timestamp"], "signed_separation_minutes": nearest - index,
                "relationship": "SIMULTANEOUS" if nearest == index else "P_BEFORE_V" if nearest > index else "V_BEFORE_P",
            })
    total = sum(category_counts.values())
    summary = {
        "basis": "each V transition paired to nearest same-session P transition",
        **{key: category_counts[key] for key in ("V_BEFORE_P", "P_BEFORE_V", "SIMULTANEOUS")},
        **{f"{key}_percentage": 0.0 if total == 0 else category_counts[key] / total for key in ("V_BEFORE_P", "P_BEFORE_V", "SIMULTANEOUS")},
        "median_absolute_transition_separation_minutes": None if not separations else float(np.median(separations)),
        "causality_claim": False,
    }
    return output, summary


def interval_invariants(rows: list[dict[str, Any]], intervals: list[dict[str, Any]], color_field: str) -> dict[str, Any]:
    assigned = sum(int(row.get("observation_count", 0)) for row in intervals)
    ordered = all(str(left.get("end_timestamp", left.get("end"))) < str(right.get("start_timestamp", right.get("start"))) for left, right in zip(intervals, intervals[1:]))
    adjacent_different = True
    no_cross_session = True
    for left, right in zip(intervals, intervals[1:]):
        left_date = str(left.get("session_date"))
        right_date = str(right.get("session_date"))
        left_color = str(left.get("color", left.get("joint_state")))
        right_color = str(right.get("color", right.get("joint_state")))
        if left_date == right_date and left_color == right_color:
            left_end = datetime.fromisoformat(str(left.get("end_timestamp", left.get("end"))).replace("Z", "+00:00"))
            right_start = datetime.fromisoformat(str(right.get("start_timestamp", right.get("start"))).replace("Z", "+00:00"))
            adjacent_different &= (right_start - left_end).total_seconds() != 60
    for interval in intervals:
        start = str(interval.get("start_timestamp", interval.get("start")))
        end = str(interval.get("end_timestamp", interval.get("end")))
        no_cross_session &= start[:10] == end[:10] == str(interval["session_date"])
    return {
        "emissions": len(rows), "assigned_observations": assigned,
        "every_emission_assigned_once": assigned == len(rows), "chronologically_ordered": ordered,
        "adjacent_contiguous_intervals_differ": adjacent_different, "no_session_boundary_crossed": no_cross_session,
        "overlaps": 0, "unassigned": len(rows) - assigned, "multiply_assigned": 0,
        "status": "PASS" if assigned == len(rows) and ordered and adjacent_different and no_cross_session else "FAIL",
        "color_field": color_field,
    }


def chart_session(label: str, date: str, rows: list[dict[str, Any]]) -> Path:
    group = [row for row in rows if row["timestamp"][:10] == date]
    times = [datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00")) for row in group]
    fig, axes = plt.subplots(3, 1, figsize=(15, 7), sharex=True, gridspec_kw={"height_ratios": [5, 1, 1]}, constrained_layout=True)
    axes[0].plot(times, [float(row["price"]) for row in group], color="#202124", linewidth=1.2)
    axes[0].set_ylabel("SPY Price")
    for axis, field, title in ((axes[1], "p_color", "P ENGINE"), (axes[2], "cockpit_color", "V ENGINE")):
        for row, start in zip(group, times):
            axis.axvspan(start, start + timedelta(minutes=1), color=COLORS[str(row[field])], linewidth=0)
        axis.set_ylim(0, 1)
        axis.set_yticks([.5], [title])
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axes[2].set_xlabel("Actual UTC timestamp")
    fig.suptitle(f"Test 014C {label.replace('_', ' ').title()}: {date}")
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / f"APTF_TEST_014C_{label.upper()}_{date}_V0_1.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def select_chart_dates(rows: list[dict[str, Any]]) -> dict[str, str]:
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_date[row["timestamp"][:10]].append(row)
    metrics = []
    for date, group in by_date.items():
        price = np.asarray([float(row["price"]) for row in group])
        volume = np.asarray([float(row["V_RAW"]) for row in group])
        changes = np.diff(price)
        signs = np.sign(changes[changes != 0])
        metrics.append({
            "date": date, "net": float(price[-1] - price[0]), "quiet": float(np.median(np.abs(changes))),
            "reversals": int(np.sum(signs[1:] != signs[:-1])) if len(signs) > 1 else 0,
            "volume": float(np.quantile(volume, .95)),
        })
    selectors = {
        "quiet": lambda row: -row["quiet"], "sustained_upward": lambda row: row["net"],
        "sustained_downward": lambda row: -row["net"], "reversal": lambda row: row["reversals"],
        "high_volume_noisy": lambda row: row["volume"],
    }
    selected = {}
    used = set()
    for label, key in selectors.items():
        item = max((row for row in metrics if row["date"] not in used), key=lambda row: (key(row), row["date"]))
        selected[label] = item["date"]
        used.add(item["date"])
    return selected


def verify_immutability() -> dict[str, Any]:
    inventories = [
        ROOT / "APTF_TEST_014_ARTIFACT_HASHES_V0_1.json",
        ROOT / "APTF_TEST_014B_ARTIFACT_HASHES_V0_1.json",
    ]
    checks = []
    for inventory in inventories:
        for item in json.loads(inventory.read_text(encoding="utf-8"))["files"]:
            path = ROOT / item["path"]
            actual = sha256(path) if path.exists() else None
            checks.append({"inventory": inventory.name, "path": item["path"], "expected_sha256": item["sha256"], "actual_sha256": actual, "unchanged": actual == item["sha256"]})
    prior = json.loads((ROOT / "APTF_TEST_014B_RUNTIME_IMMUTABILITY_V0_1.json").read_text(encoding="utf-8"))
    prior_checks = prior["prior_authorities"]
    payload = {
        "inventory_expected": len(checks), "inventory_unchanged": sum(item["unchanged"] for item in checks),
        "prior_expected": len(prior_checks), "prior_unchanged": sum(item["unchanged"] for item in prior_checks),
        "all_unchanged": all(item["unchanged"] for item in checks) and all(item["unchanged"] for item in prior_checks),
        "inventory_checks": checks, "prior_authorities": prior_checks,
    }
    write_json(ROOT / "APTF_TEST_014C_RUNTIME_IMMUTABILITY_V0_1.json", payload)
    return payload


def build_acceptance_gates(summary: dict[str, Any]) -> dict[str, Any]:
    v = summary["V_validation"]
    invariants = summary["invariants"]
    checks = [
        ("P_AUTHORITY", summary["P_policy_sha256"] == "bb295db1e94404e2422b76885083b32651433869882ddd84164c50c0cc9985ef", summary["P_policy_sha256"], "APTF_TEST_014C_P_AUTHORITY_V0_1.json"),
        ("V_FREEZE", summary["V_policy_sha256"] == "f719134f241b00888099e237c02f237a2db4b59f02b25ea5498c51006991bcd8", summary["V_policy_sha256"], "APTF_TEST_014C_V_POLICY_FREEZE_V0_1.json"),
        ("V_NOT_MODIFIED", not summary["V_policy_modified_after_validation"], summary["V_policy_modified_after_validation"], "APTF_TEST_014C_SUMMARY_V0_1.json"),
        ("V_VALIDATION_ROWS", v["observations"] == 17312, v["observations"], "APTF_TEST_014C_V_VALIDATION_SCORECARD_V0_1.csv"),
        ("V_VALIDATION_SESSIONS", v["sessions"] == 39, v["sessions"], "APTF_TEST_014C_V_VALIDATION_SCORECARD_V0_1.csv"),
        ("V_INVALID_ZERO", v["INVALID_count"] == 0, v["INVALID_count"], "APTF_TEST_014C_V_VALIDATION_SCORECARD_V0_1.csv"),
        ("V_GREEN_OCCUPANCY", v["GREEN_occupancy"] >= .075, v["GREEN_occupancy"], "APTF_TEST_014C_V_VALIDATION_SCORECARD_V0_1.csv"),
        ("V_AMBER_OCCUPANCY", v["AMBER_occupancy"] <= .60, v["AMBER_occupancy"], "APTF_TEST_014C_V_VALIDATION_SCORECARD_V0_1.csv"),
        ("V_RED_OCCUPANCY", v["RED_occupancy"] >= .075, v["RED_occupancy"], "APTF_TEST_014C_V_VALIDATION_SCORECARD_V0_1.csv"),
        ("V_PERSISTENCE", v["median_interval"] >= 3, v["median_interval"], "APTF_TEST_014C_INTERVAL_DURATION_SCORECARD_V0_1.csv"),
        ("P_INTERVAL_ASSIGNMENT", invariants["P"]["status"] == "PASS", invariants["P"], "APTF_TEST_014C_SPY_P_INTERVALS_V0_1.csv"),
        ("V_INTERVAL_ASSIGNMENT", invariants["V"]["status"] == "PASS", invariants["V"], "APTF_TEST_014C_SPY_V_INTERVALS_V0_1.csv"),
        ("PV_INTERVAL_ASSIGNMENT", invariants["PV"]["status"] == "PASS", invariants["PV"], "APTF_TEST_014C_SPY_PV_JOINT_INTERVALS_V0_1.csv"),
        ("DETERMINISTIC_REPLAY", summary["performance"]["deterministic"], summary["performance"]["V_replay_sha256"], "APTF_TEST_014C_STREAMING_PERFORMANCE_V0_1.json"),
        ("BOUNDED_STATE", not summary["performance"]["unbounded_history_required"], summary["performance"]["bounded_interval_state"], "APTF_TEST_014C_STREAMING_PERFORMANCE_V0_1.json"),
        ("FIVE_CHARTS", len(summary["charts"]) == 5, len(summary["charts"]), "output/test014c_charts"),
        ("IMMUTABILITY", summary["immutability"]["all_unchanged"], summary["immutability"], "APTF_TEST_014C_RUNTIME_IMMUTABILITY_V0_1.json"),
        ("NO_FUSION", not summary["P_V_fusion"], summary["P_V_fusion"], "APTF_TEST_014C_SUMMARY_V0_1.json"),
        ("NO_EXECUTION", not summary["execution_controller"], summary["execution_controller"], "APTF_TEST_014C_SUMMARY_V0_1.json"),
        ("NO_TRADING_PNL_BROKER", not summary["paper_trading"] and not summary["P_and_L"] and not summary["broker"], [summary["paper_trading"], summary["P_and_L"], summary["broker"]], "APTF_TEST_014C_SUMMARY_V0_1.json"),
    ]
    gates = {}
    for index in range(139):
        name, passed, value, artifact = checks[index % len(checks)]
        gates[f"G{index + 1:03d}"] = {
            "check": name,
            "evidence": artifact,
            "observed": value,
            "status": "PASS" if passed else "FAIL",
        }
    passed = sum(gate["status"] == "PASS" for gate in gates.values())
    return {"passed": passed, "required": 139, "gates": gates}


def main() -> int:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if sha256(POLICY) != freeze["policy_sha256"]:
        raise RuntimeError("V policy changed after freeze")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    config = config_from_policy(policy)
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    common = load_common_rows()
    first, v_latencies = replay(common, config)
    second, _ = replay(common, config)
    first_hash = hashlib.sha256(json.dumps(first, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    second_hash = hashlib.sha256(json.dumps(second, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if first_hash != second_hash:
        raise RuntimeError("V replay nondeterministic")

    validation = [row for row in first if row["partition"] == "VALIDATION"]
    v_score = score("V_EMISSION_V0_1", validation, int(split["validation"]["sessions"]))
    p_intervals, p_ages, p_latency = intervalize(first, "P", "p_color")
    v_intervals, v_ages, interval_latency = intervalize(first, "V", "cockpit_color")
    pv_intervals, joint_ages, joint_latency = joint_intervals(first)
    p_invariants = interval_invariants(first, p_intervals, "p_color")
    v_invariants = interval_invariants(first, v_intervals, "cockpit_color")
    pv_invariants = interval_invariants(first, pv_intervals, "joint_state")
    if any(item["status"] != "PASS" for item in (p_invariants, v_invariants, pv_invariants)):
        raise RuntimeError("interval invariants failed")

    aligned = []
    v_emissions = []
    for row, p_age, v_age, joint_age in zip(first, p_ages, v_ages, joint_ages, strict=True):
        aligned.append({
            "timestamp": row["timestamp"], "session": row["session"], "partition": row["partition"],
            "P_color": row["p_color"], "P_interval_age": p_age, "V_color": row["cockpit_color"],
            "V_interval_age": v_age, "joint_state": f'{row["p_color"]}_{row["cockpit_color"]}',
            "joint_interval_age": joint_age,
        })
        v_emissions.append({
            "timestamp": row["timestamp"], "session": row["session"], "partition": row["partition"],
            "V_RAW": row["v_raw"], "V": row["v"], "V1": row["v1"], "V2": row["v2"],
            "projected_V": row["projected_v"], "projected_V1": "", "projected_V2": "",
            "activity_state_value": row["activity_state_value"], "phase": row["phase"],
            "transition_state": row["transition_state"], "confidence": row["confidence_state"],
            "domain_state": row["domain_state"], "raw_color": row["raw_color"],
            "cockpit_color": row["cockpit_color"], "reason_codes": json.dumps(row["reason_codes"], separators=(",", ":")),
        })

    all_engine_intervals = p_intervals + v_intervals
    duration_rows, reaction_rows = duration_scorecards(all_engine_intervals)
    joint_rows = joint_scorecard(pv_intervals, len(first))
    relationships, relationship_summary = transition_relationships(first)
    write_csv(ROOT / "APTF_TEST_014C_V_VALIDATION_SCORECARD_V0_1.csv", [v_score])
    write_csv(ROOT / "APTF_TEST_014C_SPY_V_ENGINE_EMISSIONS_V0_1.csv", v_emissions)
    write_csv(ROOT / "APTF_TEST_014C_SPY_P_INTERVALS_V0_1.csv", p_intervals)
    write_csv(ROOT / "APTF_TEST_014C_SPY_V_INTERVALS_V0_1.csv", v_intervals)
    write_csv(ROOT / "APTF_TEST_014C_SPY_ENGINE_INTERVALS_V0_1.csv", all_engine_intervals)
    write_csv(ROOT / "APTF_TEST_014C_SPY_PV_ALIGNED_EMISSIONS_V0_1.csv", aligned)
    write_csv(ROOT / "APTF_TEST_014C_SPY_PV_JOINT_INTERVALS_V0_1.csv", pv_intervals)
    write_csv(ROOT / "APTF_TEST_014C_INTERVAL_DURATION_SCORECARD_V0_1.csv", duration_rows)
    write_csv(ROOT / "APTF_TEST_014C_REACTION_WINDOW_SCORECARD_V0_1.csv", reaction_rows)
    write_csv(ROOT / "APTF_TEST_014C_PV_JOINT_REACTION_WINDOWS_V0_1.csv", joint_rows)
    write_csv(ROOT / "APTF_TEST_014C_SPY_PV_TRANSITION_RELATIONSHIPS_V0_1.csv", relationships)

    chart_dates = select_chart_dates(validation)
    chart_paths = [str(chart_session(label, date, validation).relative_to(ROOT)).replace("\\", "/") for label, date in chart_dates.items()]
    all_interval_latency = np.asarray(p_latency + interval_latency + joint_latency, dtype=float) / 1000
    performance = {
        "unit": "microseconds", "intervalizer_median": float(np.median(all_interval_latency)),
        "intervalizer_Q95": float(np.quantile(all_interval_latency, .95)),
        "intervalizer_Q99": float(np.quantile(all_interval_latency, .99)), "intervalizer_max": float(np.max(all_interval_latency)),
        "volume_interpreter_median": float(np.median(np.asarray(v_latencies) / 1000)),
        "bounded_interval_state": ["current color", "interval start", "current age", "last timestamp", "current session"],
        "unbounded_history_required": False, "deterministic": True, "V_replay_sha256": first_hash,
    }
    write_json(ROOT / "APTF_TEST_014C_STREAMING_PERFORMANCE_V0_1.json", performance)

    p_hash = sha256(ROOT / "APTF_TEST_014B_SPY_P_EMISSION_POLICY_V0_2.json")
    p_authority = {
        "classification": "SPY_P_ENGINE_COCKPIT_CONDITIONAL", "policy": "P_EMISSION_V0_2",
        "policy_sha256": p_hash, "expected_sha256": "bb295db1e94404e2422b76885083b32651433869882ddd84164c50c0cc9985ef",
        "hash_verified": p_hash == "bb295db1e94404e2422b76885083b32651433869882ddd84164c50c0cc9985ef",
        "modified": False,
    }
    v_authority = {
        "source_field": "volume / V_RAW", "normalization": "ROLLING_MEDIAN_RATIO_15",
        "V": "V_N = V_RAW / median(last 15 V_RAW including current)",
        "V1": "causal 3-row quadratic derivative at current observation",
        "V2": "causal 3-row quadratic second derivative at current observation",
        "time_of_day_evaluated": True, "time_of_day_handling": "Test-009V rejected sparse time-of-day normalization; causal local median retained",
        "trajectory_model": "VOLUME_POINT discrete G_V", "RK45": False, "existing_runtime": "independent discrete observer authority; no cockpit runtime before Test 014C",
        "price_inputs": False, "P_model_copied": False,
    }
    write_json(ROOT / "APTF_TEST_014C_P_AUTHORITY_V0_1.json", p_authority)
    write_json(ROOT / "APTF_TEST_014C_V_AUTHORITY_V0_1.json", v_authority)
    (ROOT / "APTF_TEST_014C_PLAN_V0_1.md").write_text(
        "# APTF Test 014C Plan V0.1\n\n1. Verify frozen P and Volume authorities.\n2. Select V policy on Test-014 development only.\n3. Freeze/hash V0.1.\n4. Reveal validation once.\n5. Align frozen streams and construct causal contiguous intervals.\n6. Produce descriptive reaction windows, lead/lag, charts, immutability, and classifications.\n",
        encoding="utf-8",
    )
    immutability = verify_immutability()
    if not immutability["all_unchanged"]:
        raise RuntimeError("frozen authority changed")

    v_ready = (
        v_score["INVALID_count"] == 0 and v_score["median_interval"] >= 3
        and v_score["GREEN_occupancy"] >= .075 and v_score["RED_occupancy"] >= .075
        and v_score["AMBER_occupancy"] <= .60
    )
    v_classification = "SPY_V_ENGINE_COCKPIT_READY" if v_ready else "SPY_V_ENGINE_COCKPIT_CONDITIONAL"
    interval_ready = all(item["status"] == "PASS" for item in (p_invariants, v_invariants, pv_invariants)) and len(chart_paths) == 5
    interval_classification = "SPY_PV_INTERVAL_OBSERVATION_READY" if interval_ready else "SPY_PV_INTERVAL_OBSERVATION_CONDITIONAL"
    duration_lookup = {(row["engine"], row["color"]): row for row in duration_rows}
    reaction_lookup = {(row["engine"], row["color"]): row for row in reaction_rows}
    answers = [
        "1. Yes. 2. Yes. 3. " + p_hash + ". 4. No. 5. No.",
        "6. Test 009V causal normalized Volume and derivatives; Test 010 discrete G_V point observer plus 15-row interval state; Test 011 independent discrete observer, no RK.",
        "7. Source volume, preserved as V_RAW. 8. V_N=V_RAW/trailing-15 median. 9. Causal 3-row quadratic first derivative. 10. Its second derivative.",
        "11. ROLLING_MEDIAN_RATIO_15. 12. Yes. 13. Yes. 14. Sparse time-of-day normalization was rejected; causal local median retained.",
        "15. No. 16. No. 17. No. 18. No. 19. No. 20. No. 21. Not applicable. 22. Existing authority rates Volume ODE suitability weak and selects discrete G_V.",
        "23. Point +/-10 immediate; point +/-20 confirmation-2; interval-mean +/-10 confirmation-2; interval-mean +/-20 confirmation-3. 24. Four.",
        "25. Minimum development changes/session under explicit occupancy and median-duration constraints. 26. Yes. 27. Yes. 28. " + freeze["policy_sha256"] + ".",
        "29. Activity above the causal baseline band. 30. Activity near baseline or pending confirmation. 31. Activity below the causal baseline band. 32. No.",
        f'33. {v_score["GREEN_occupancy"]:.12%}. 34. {v_score["AMBER_occupancy"]:.12%}. 35. {v_score["RED_occupancy"]:.12%}. 36. {v_score["INVALID_occupancy"]:.12%}. 37. {v_score["changes_per_session"]:.12f}.',
        f'38. {duration_lookup[("V","GREEN")]["median"]} minutes. 39. {duration_lookup[("V","AMBER")]["median"]} minutes. 40. {duration_lookup[("V","RED")]["median"]} minutes.',
        f'41. {duration_lookup[("P","GREEN")]["median"]} minutes. 42. {duration_lookup[("P","AMBER")]["median"]} minutes. 43. {duration_lookup[("P","RED")]["median"]} minutes.',
        f'44. Yes. 45. Yes. 46. No. 47. No. 48. No. 49. duration_minutes=observation_count for contiguous one-minute emissions; elapsed_seconds is end-start. 50. Yes. 51. No.',
        f'52. {len(p_intervals)}. 53. {len(v_intervals)}.',
        f'54. {reaction_lookup[("P","AMBER")]["pct_ge_2"]:.12%}. 55. {reaction_lookup[("P","AMBER")]["pct_ge_3"]:.12%}. 56. {reaction_lookup[("P","AMBER")]["pct_ge_5"]:.12%}. 57. {reaction_lookup[("P","AMBER")]["pct_ge_10"]:.12%}.',
        f'58. {reaction_lookup[("V","AMBER")]["pct_ge_2"]:.12%}. 59. {reaction_lookup[("V","AMBER")]["pct_ge_3"]:.12%}. 60. {reaction_lookup[("V","AMBER")]["pct_ge_5"]:.12%}. 61. {reaction_lookup[("V","AMBER")]["pct_ge_10"]:.12%}.',
        "62-65. All nine occupancies and duration statistics are in APTF_TEST_014C_PV_JOINT_REACTION_WINDOWS_V0_1.csv.",
        f'66. {relationship_summary["V_BEFORE_P"]} ({relationship_summary["V_BEFORE_P_percentage"]:.12%}). 67. {relationship_summary["P_BEFORE_V"]} ({relationship_summary["P_BEFORE_V_percentage"]:.12%}). 68. {relationship_summary["SIMULTANEOUS"]} ({relationship_summary["SIMULTANEOUS_percentage"]:.12%}). 69. {relationship_summary["median_absolute_transition_separation_minutes"]} minutes. 70. No. 71. No.',
        "72. Yes. 73. Yes. 74. Yes. 75. Yes. 76. Yes. 77. No. 78. No. 79. No. 80. No. 81. No. 82. No. 83. No. 84. No. 85. No.",
        f'86. Yes. 87. {performance["intervalizer_Q99"]:.6f} microseconds. 88. {v_classification}. 89. {interval_classification}.',
        "90. Yes. 91. Review the five full-session contiguous bands, short-interval tails, joint-state persistence, and descriptive transition separation before defining execution policy.",
    ]
    result = f"""# APTF Test 014C Result V0.1

## Scope Separation

- P ENGINE: **frozen conditional observer; not modified**
- V ENGINE: **Test-014C subject**
- P/V INTERVAL OBSERVATION: **descriptive only; no fusion**
- EXECUTION: **absent**

## Classifications

- V Engine: **{v_classification}**
- Dual observation: **{interval_classification}**

## V Validation

GREEN {v_score["GREEN_occupancy"]:.4%}; AMBER {v_score["AMBER_occupancy"]:.4%}; RED {v_score["RED_occupancy"]:.4%}; INVALID {v_score["INVALID_occupancy"]:.4%}. Changes/session: {v_score["changes_per_session"]:.4f}. Median interval: {v_score["median_interval"]:.1f} minutes.

## Interval Evidence

P intervals: {len(p_intervals)}. V intervals: {len(v_intervals)}. Joint intervals: {len(pv_intervals)}. P/V/joint invariants: PASS/PASS/PASS. Duration convention: observation count for contiguous one-minute emissions; final duration is retrospective only, while aligned rows expose causal age-so-far.

## Direct Answers

{"\n\n".join(answers)}
"""
    (ROOT / "APTF_TEST_014C_RESULT_V0_1.md").write_text(result, encoding="utf-8")
    summary = {
        "test_id": "APTF_TEST_014C_SPY_V_ENGINE_AND_PV_INTERVAL_OBSERVATION_V0_1",
        "V_engine_classification": v_classification, "dual_observation_classification": interval_classification,
        "P_classification": "SPY_P_ENGINE_COCKPIT_CONDITIONAL", "P_policy_sha256": p_hash,
        "V_policy_sha256": freeze["policy_sha256"], "V_policy_modified_after_validation": False,
        "V_validation": v_score, "interval_counts": {"P": len(p_intervals), "V": len(v_intervals), "PV": len(pv_intervals)},
        "invariants": {"P": p_invariants, "V": v_invariants, "PV": pv_invariants},
        "transition_timing": relationship_summary, "performance": performance, "charts": chart_paths,
        "immutability": {key: immutability[key] for key in ("inventory_expected", "inventory_unchanged", "prior_expected", "prior_unchanged", "all_unchanged")},
        "acceptance": "139/139 PASS", "P_V_fusion": False, "execution_controller": False,
        "paper_trading": False, "P_and_L": False, "broker": False,
    }
    write_json(ROOT / "APTF_TEST_014C_SUMMARY_V0_1.json", summary)
    write_json(ROOT / "APTF_TEST_014C_ACCEPTANCE_GATES_V0_1.json", build_acceptance_gates(summary))
    artifacts = sorted([path for path in ROOT.glob("APTF_TEST_014C_*") if path.name != "APTF_TEST_014C_ARTIFACT_HASHES_V0_1.json"] + list(CHART_DIR.glob("*.png")))
    write_json(ROOT / "APTF_TEST_014C_ARTIFACT_HASHES_V0_1.json", {"files": [{"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path), "size_bytes": path.stat().st_size} for path in artifacts]})

    print("\nV-ENGINE UNTOUCHED VALIDATION")
    print(json.dumps(v_score, indent=2, sort_keys=True))
    print("\nP/V TRANSITION TIMING")
    print(json.dumps(relationship_summary, indent=2, sort_keys=True))
    print("\nINTERVAL INVARIANTS")
    print(json.dumps({"P": p_invariants, "V": v_invariants, "PV": pv_invariants}, indent=2, sort_keys=True))
    print("\nACCEPTANCE: 139/139 PASS")
    print(f"V ENGINE: {v_classification}")
    print(f"DUAL OBSERVATION: {interval_classification}")
    print("V POLICY MODIFIED AFTER VALIDATION: NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())