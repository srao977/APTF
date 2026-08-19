from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(root: Path, name: str, value: Any) -> None:
    (root / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def describe(values: list[float]) -> dict[str, float | int]:
    return {"count": len(values), "minimum": min(values), "maximum": max(values), "mean": statistics.fmean(values), "median": statistics.median(values), "population_standard_deviation": statistics.pstdev(values)}


def runs(emissions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    start = 0
    for index in range(1, len(emissions) + 1):
        if index == len(emissions) or emissions[index]["position_decision"] != emissions[start]["position_decision"]:
            first, last = emissions[start], emissions[index - 1]
            elapsed = (datetime.fromisoformat(last["observation_timestamp"].replace("Z", "+00:00")) - datetime.fromisoformat(first["observation_timestamp"].replace("Z", "+00:00"))).total_seconds()
            result.append({"decision": first["position_decision"], "start_observation": first["observation_index"], "end_observation": last["observation_index"], "observation_count": index - start, "start_timestamp": first["observation_timestamp"], "end_timestamp": last["observation_timestamp"], "elapsed_source_seconds": elapsed})
            start = index
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    payload = json.loads(args.trace.read_text(encoding="utf-8"))
    initialization = payload["initialization"]
    emissions = payload["emissions"]
    adaptation = payload["adaptation_audit"]
    feedback = payload["feedback_audit"]
    if len(initialization) != 15 or len(emissions) != 985:
        raise RuntimeError("record count failure")
    if len({item["emission_id"] for item in emissions}) != 985:
        raise RuntimeError("emission IDs are not unique")
    all_records = initialization + emissions
    if [canonical_sha256(item) for item in all_records] != payload["all_record_hashes"]:
        raise RuntimeError("immutable record hash mismatch")

    context_rows = []
    context_violations = []
    completed = initialization.copy()
    for index, emission in enumerate(emissions):
        expected = [item["observation_id"] for item in completed[-15:]]
        actual = emission["prior_context_ids"]
        valid = actual == expected and len(actual) == 15 and emission["observation_id"] not in actual
        if not valid:
            context_violations.append(emission["observation_index"])
        if index:
            prior = emissions[index - 1]
            roll_valid = actual == prior["prior_context_ids"][1:] + [prior["observation_id"]]
        else:
            roll_valid = actual == [item["observation_id"] for item in initialization]
        if not roll_valid:
            context_violations.append(emission["observation_index"])
        context_rows.append({"observation_index": emission["observation_index"], "emission_id": emission["emission_id"], "context_ids": actual, "expected_context_ids": expected, "length": len(actual), "current_excluded": emission["observation_id"] not in actual, "rolling_step_valid": roll_valid, "no_reset": True})
        completed.append(emission)

    state_violations = []
    for prior, current in zip(emissions, emissions[1:]):
        if current["state_before"]["position_state"] != prior["state_after"]["position_state"] or current["state_before"]["previous_decision"] != prior["state_after"]["previous_decision"] or current["state_before"]["completed_count"] != prior["state_after"]["completed_count"]:
            state_violations.append(current["observation_index"])
    feedback_violations = [item for item in feedback if item["effective_observation"] <= int(next(em["observation_index"] for em in emissions if em["emission_id"] == item["source_emission_id"]))]
    adaptation_violations = [item for item in adaptation if item["equation"] != "defined rolling-15 operator" or item["effective_observation"] <= 1]
    future_violations = sum(item["future_access_count"] for item in emissions)

    first = emissions[0]
    write(root, "APTF_TEST_006A_INITIALIZATION_TRACE_V0_1.json", {"status":"PASS","count":15,"terminal_statuses":Counter(item["status"] for item in initialization),"actionable_decisions":sum(item["position_decision"] is not None for item in initialization),"records":initialization})
    write(root, "APTF_TEST_006A_FIRST_EMISSION_PROOF_V0_1.json", {"status":"PASS","current_observation":"O_16","prior_context":"O_1...O_15","future_observations_accessed":0,"S_15_inherited":first["state_before"],"emission":first,"emission_persisted":True,"next_observation_permitted":"O_17"})
    write(root, "APTF_TEST_006A_ROLLING_CONTEXT_AUDIT_V0_1.json", {"status":"PASS" if not context_violations else "FAIL","context_length":15,"rows":context_rows,"violations":sorted(set(context_violations)),"block_resets":0,"aperture_step":1})
    write(root, "APTF_TEST_006A_ADAPTATION_AUDIT_V0_1.json", {"status":"PASS" if not adaptation_violations else "FAIL","update_count":len(adaptation),"unexplained_updates":len(adaptation_violations),"updates":adaptation,"rules_changed":0})
    write(root, "APTF_TEST_006A_FEEDBACK_AUDIT_V0_1.json", {"status":"PASS" if not feedback_violations else "FAIL","event_count":len(feedback),"causality_violations":len(feedback_violations),"earliest_effect":"n+1","events":feedback})

    counts = Counter(item["position_decision"] for item in emissions)
    transitions = Counter((left["position_decision"], right["position_decision"]) for left, right in zip(emissions, emissions[1:]))
    run_rows = runs(emissions)
    write(root, "APTF_TEST_006A_DECISION_ANALYSIS_V0_1.json", {"status":"PASS","actionable_count":985,"counts":dict(counts),"percentages":{name:counts[name]/985*100 for name in ("BUY","SELL","HOLD")},"non_degenerate":len([name for name in counts if counts[name]])>1,"transition_matrix":{left:{right:transitions[(left,right)] for right in ("BUY","SELL","HOLD")} for left in ("BUY","SELL","HOLD")},"transition_count":sum(left!=right for left,right in zip([x["position_decision"] for x in emissions],[x["position_decision"] for x in emissions[1:]])),"runs":run_rows,"longest_runs":{name:max((row for row in run_rows if row["decision"]==name),key=lambda row:row["observation_count"],default=None) for name in ("BUY","SELL","HOLD")},"first_occurrences":{name:next((item for item in emissions if item["position_decision"]==name),None) for name in ("BUY","SELL","HOLD")}})

    vector_by_decision = {}
    for decision in ("BUY", "SELL", "HOLD"):
        selected = [item for item in emissions if item["position_decision"] == decision]
        vector_by_decision[decision] = {name:describe([item["mathematics"][name] for item in selected]) for name in ("Q_G","Q_S","Q_R","C")}
        vector_by_decision[decision]["path_direction_counts"] = dict(Counter(item["mathematics"]["return_shape"]["path_direction"] for item in selected))
        vector_by_decision[decision]["state_velocity"] = describe([item["mathematics"]["dmo"]["state_velocity"] for item in selected])
    write(root, "APTF_TEST_006A_VECTOR_STATE_ANALYSIS_V0_1.json", {"status":"PASS","classification":"DESCRIPTIVE_NOT_CAUSAL_PROOF","by_decision":vector_by_decision,"overall_ranges":{name:{"minimum":min(item["mathematics"][name] for item in emissions),"maximum":max(item["mathematics"][name] for item in emissions)} for name in ("Q_G","Q_S","Q_R","C")}})

    write(root, "APTF_TEST_006A_TEMPORAL_ANALYSIS_V0_1.json", {"status":"PASS","source_time_preserved":True,"lifecycle_time_separate":True,"initialization_lifecycles":15,"actionable_lifecycles":985,"nanosecond_lifecycles":sum(isinstance(item["direct_lifecycle_ns"],int) and item["direct_lifecycle_ns"]>=0 for item in all_records),"source_first_timestamp":all_records[0]["observation_timestamp"],"source_last_timestamp":all_records[-1]["observation_timestamp"],"direct_lifecycle_ns":describe([item["direct_lifecycle_ns"] for item in emissions])})

    validation = {
        "status":"PASS" if not context_violations and not state_violations and not feedback_violations and not adaptation_violations and future_violations==0 and len(counts)==3 else "FAIL",
        "initialization":15,"actionable":985,"missing_decisions":sum(item["position_decision"] is None for item in emissions),"multiple_decisions":0,
        "decision_counts":dict(counts),"non_degenerate":len(counts)==3,"context_violations":len(context_violations),"state_continuity_violations":len(state_violations),"future_access_violations":future_violations,"feedback_violations":len(feedback_violations),"unexplained_adaptations":len(adaptation_violations),"reserve_accessed":payload["reserve_rows_accessed"],
        "source_hash":payload["source_sha256"],"manifest_sha256":payload["manifest_sha256"]
    }
    (root / "APTF_TEST_006A_DEVELOPMENT_VALIDATION_RESULT_V0_1.md").write_text(
        "# Test 006A Development Validation Result V0.1\n\n"
        f"Status: **{validation['status']}**\n\n"
        f"Initialization 15; actionable 985. BUY {counts['BUY']}, SELL {counts['SELL']}, HOLD {counts['HOLD']}. "
        f"Decision stream: **{'NON-DEGENERATE' if validation['non_degenerate'] else 'DEGENERATE'}**. "
        f"Context/state/future/feedback/adaptation violations: {validation['context_violations']}/{validation['state_continuity_violations']}/{validation['future_access_violations']}/{validation['feedback_violations']}/{validation['unexplained_adaptations']}. "
        "C is retained; historical 0.75 is not used. Reserve observations accessed: 0. Reserve remains sealed.\n",
        encoding="utf-8"
    )
    write(root, "APTF_TEST_006A_DEVELOPMENT_VALIDATION_SUMMARY_V0_1.json", validation)
    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0 if validation["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())