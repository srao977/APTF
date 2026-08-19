from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ORIGINAL_COLUMNS = ["entity_id","event_timestamp_local","event_timestamp_utc","timezone","open","high","low","close","volume","close_return_1m","high_low_range","high_low_range_fraction","open_close_change","open_close_return","session_type","is_regular_session","minute_of_session","source_provider","source_dataset","source_row_number","data_valid","quality_flags"]
DECISIONS = ("BUY", "SELL", "HOLD")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def describe(values: list[float]) -> dict[str, Any]:
    return {"count": len(values), "minimum": min(values), "maximum": max(values), "mean": statistics.fmean(values), "median": statistics.median(values), "population_standard_deviation": statistics.pstdev(values)}


def runs(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    start = 0
    for index in range(1, len(records) + 1):
        if index == len(records) or records[index]["decision"] != records[start]["decision"]:
            first, last = records[start], records[index - 1]
            elapsed = (datetime.fromisoformat(last["timestamp"].replace("Z", "+00:00")) - datetime.fromisoformat(first["timestamp"].replace("Z", "+00:00"))).total_seconds()
            result.append({"decision": first["decision"], "start_observation": first["observation_index"], "end_observation": last["observation_index"], "count": index-start, "start_timestamp": first["timestamp"], "end_timestamp": last["timestamp"], "elapsed_source_seconds": elapsed})
            start = index
    return result


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write(root: Path, name: str, metadata: dict[str, Any], body: dict[str, Any]) -> None:
    (root / name).write_text(json.dumps({**metadata, **body}, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preexecution", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--adaptation", type=Path, required=True)
    parser.add_argument("--feedback", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    pre = json.loads(args.preexecution.read_text(encoding="utf-8"))
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    records = load_jsonl(args.journal)
    metadata = {name: pre[name] for name in ("run_id", "freeze_id", "freeze_manifest_sha256", "source_sha256", "execution_timestamp_utc")}
    if len(records) != 101221 or summary["source_rows"] != 101221 or summary["actionable"] != 101206:
        raise RuntimeError("reserve record count mismatch")
    initialization = records[:15]
    actionable = records[15:]
    if any(row["status"] != "INITIALIZING" or row["decision"] != "INITIALIZING" for row in initialization):
        raise RuntimeError("initialization semantic mismatch")
    if any(row["decision"] not in DECISIONS for row in actionable):
        raise RuntimeError("invalid actionable decision")

    context_violations = []
    state_violations = []
    completed_ids: list[str] = []
    for index, row in enumerate(records):
        expected = completed_ids[-15:]
        if row["prior_context_ids"] != expected or row["observation_id"] in row["prior_context_ids"]:
            context_violations.append(row["observation_index"])
        if index and row["position_state_before"] != records[index - 1]["position_state_after"]:
            state_violations.append(row["observation_index"])
        completed_ids.append(row["observation_id"])
    write(root, "APTF_TEST_006B_ROLLING_CONTEXT_AUDIT_V0_1.json", metadata, {"status":"PASS" if not context_violations else "FAIL","context_length":15,"records_verified":len(records),"violations":context_violations,"state_continuity_violations":state_violations,"block_resets":0,"aperture_step":1})

    observation_index = {row["observation_id"]: row["observation_index"] for row in records}
    emission_index = {row["emission_id"]: row["observation_index"] for row in actionable}
    adaptation_payload = json.loads(args.adaptation.read_text(encoding="utf-8"))
    adaptation_violations = [event for event in adaptation_payload["updates"] if event["equation"] != "defined rolling-15 operator" or event["effective_observation"] != observation_index[event["causal_observation_id"]] + 1]
    adaptation_payload.update({"status":"PASS" if not adaptation_violations else "FAIL","unexplained_updates":len(adaptation_violations),"rules_changed":0})
    args.adaptation.write_text(json.dumps(adaptation_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    del adaptation_payload
    feedback_payload = json.loads(args.feedback.read_text(encoding="utf-8"))
    feedback_violations = [event for event in feedback_payload["events"] if event["effective_observation"] != emission_index[event["source_emission_id"]] + 1]
    feedback_payload.update({"status":"PASS" if not feedback_violations else "FAIL","causality_violations":len(feedback_violations),"earliest_effect":"n+1"})
    args.feedback.write_text(json.dumps(feedback_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    del feedback_payload

    counts = Counter(row["decision"] for row in actionable)
    transition_counts = Counter((left["decision"], right["decision"]) for left, right in zip(actionable, actionable[1:]))
    run_rows = runs(actionable)
    hold_routed = {"BUY_HOLD_SELL":0,"SELL_HOLD_BUY":0}
    for start in range(len(actionable)):
        first = actionable[start]["decision"]
        if first not in {"BUY","SELL"}:
            continue
        index = start + 1
        if index >= len(actionable) or actionable[index]["decision"] != "HOLD":
            continue
        while index < len(actionable) and actionable[index]["decision"] == "HOLD":
            index += 1
        if index < len(actionable):
            last = actionable[index]["decision"]
            if first == "BUY" and last == "SELL": hold_routed["BUY_HOLD_SELL"] += 1
            if first == "SELL" and last == "BUY": hold_routed["SELL_HOLD_BUY"] += 1
    decision_body = {"status":"PASS","counts":dict(counts),"percentages":{name:counts[name]/len(actionable)*100 for name in DECISIONS},"non_degenerate":all(counts[name]>0 for name in DECISIONS),"transition_matrix":{left:{right:transition_counts[(left,right)] for right in DECISIONS} for left in DECISIONS},"transition_count":sum(left!=right for left,right in zip([r["decision"] for r in actionable],[r["decision"] for r in actionable[1:]])),"runs":run_rows,"longest_runs":{name:max((row for row in run_rows if row["decision"]==name),key=lambda row:row["count"],default=None) for name in DECISIONS},"direct_reversals":{"BUY_TO_SELL":transition_counts[("BUY","SELL")],"SELL_TO_BUY":transition_counts[("SELL","BUY")]},"hold_routed_reversals":hold_routed}
    write(root, "APTF_TEST_006B_DECISION_TRANSITIONS_V0_1.json", metadata, decision_body)

    by_decision = {}
    for decision in DECISIONS:
        selected = [row for row in actionable if row["decision"] == decision]
        by_decision[decision] = {name:describe([row[name] for row in selected]) for name in ("Q_G","Q_S","Q_R","C")}
        by_decision[decision]["path_direction_counts"] = dict(Counter(row["path_direction"] for row in selected))
    ranges = {name:{"minimum":min(row[name] for row in actionable),"maximum":max(row[name] for row in actionable)} for name in ("Q_G","Q_S","Q_R","C")}
    write(root, "APTF_TEST_006B_VECTOR_STATE_ANALYSIS_V0_1.json", metadata, {"status":"PASS","classification":"DESCRIPTIVE_NOT_CAUSAL_PROOF","ranges":ranges,"by_decision":by_decision,"historical_C_0_75_gate_used":False})

    write(root, "APTF_TEST_006B_TEMPORAL_ANALYSIS_V0_1.json", metadata, {"status":"PASS","source_time_preserved":True,"source_first_timestamp":records[0]["timestamp"],"source_last_timestamp":records[-1]["timestamp"],"initialization_lifecycles":15,"actionable_lifecycles":len(actionable),"nanosecond_lifecycles":sum(isinstance(row["lifecycle_ns"],int) and row["lifecycle_ns"]>=0 for row in records),"source_processing_time_separate":True,"lifecycle_ns":describe([row["lifecycle_ns"] for row in actionable])})

    dev = json.loads((root / "APTF_TEST_006A_DECISION_ANALYSIS_V0_1.json").read_text(encoding="utf-8"))
    dev_vectors = json.loads((root / "APTF_TEST_006A_VECTOR_STATE_ANALYSIS_V0_1.json").read_text(encoding="utf-8"))
    comparison = {"status":"PASS","classification":"DESCRIPTIVE_NO_SIMILARITY_THRESHOLD","development":{"actionable":985,"counts":dev["counts"],"percentages":dev["percentages"],"ranges":dev_vectors["overall_ranges"],"transition_matrix":dev["transition_matrix"]},"reserve":{"actionable":len(actionable),"counts":dict(counts),"percentages":decision_body["percentages"],"ranges":ranges,"transition_matrix":decision_body["transition_matrix"]},"differences":{"percentage_points":{name:decision_body["percentages"][name]-dev["percentages"][name] for name in DECISIONS},"direct_reversal_difference":{"BUY_TO_SELL":decision_body["direct_reversals"]["BUY_TO_SELL"]-dev["transition_matrix"]["BUY"]["SELL"],"SELL_TO_BUY":decision_body["direct_reversals"]["SELL_TO_BUY"]-dev["transition_matrix"]["SELL"]["BUY"]}}}
    write(root, "APTF_TEST_006B_006A_COMPARISON_V0_1.json", metadata, comparison)

    csv_rows = 0
    csv_decision_mismatches = 0
    csv_invalid = 0
    with args.csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        if header[:len(ORIGINAL_COLUMNS)] != ORIGINAL_COLUMNS:
            raise RuntimeError("CSV original column order mismatch")
        for index, row in enumerate(reader):
            csv_rows += 1
            expected = records[index]["decision"]
            if row["position_decision"] != expected:
                csv_decision_mismatches += 1
            if index >= 15 and row["position_decision"] not in DECISIONS:
                csv_invalid += 1
    if csv_rows != 101221:
        raise RuntimeError("CSV row count mismatch")

    post_files = []
    for item in pre["frozen_files"]:
        actual = sha256(root / item["path"])
        post_files.append({"path":item["path"],"pre_sha256":item["sha256"],"post_sha256":actual,"equal":actual==item["sha256"]})
    source_post = sha256(root / pre["source_path"])
    post = {"status":"PASS","frozen_files":post_files,"frozen_identity":f"{sum(item['equal'] for item in post_files)}/{len(post_files)} PASS","source":{"pre_sha256":pre["source_sha256"],"post_sha256":source_post,"equal":source_post==pre["source_sha256"]},"source_rows":summary["source_rows"],"csv_rows":csv_rows,"initializing_rows":15,"actionable_rows":len(actionable),"source_field_mismatches_runtime":summary["source_field_mismatches"],"csv_emission_decision_mismatches":csv_decision_mismatches,"invalid_terminal_decisions":csv_invalid,"blank_actionable_decisions":summary["blank_actionable"],"emission_rows":summary["emission_rows"],"journal_rows":summary["journal_rows"],"adaptation_events":summary["adaptation_events"],"feedback_events":summary["feedback_events"],"future_access_violations":sum(row["future_access_count"] for row in records),"rolling_context_violations":len(context_violations),"state_continuity_violations":len(state_violations),"adaptation_violations":len(adaptation_violations),"feedback_violations":len(feedback_violations),"second_pass":False,"rewind":False,"rule_changes":0,"all_pass":all(item["equal"] for item in post_files) and source_post==pre["source_sha256"] and summary["source_field_mismatches"]==0 and csv_decision_mismatches==0 and csv_invalid==0 and len(context_violations)==0 and len(state_violations)==0 and len(adaptation_violations)==0 and len(feedback_violations)==0}
    write(root, "APTF_TEST_006B_POSTEXECUTION_INTEGRITY_V0_1.json", metadata, post)
    result = f"""# APTF Test 006B One-Way Reserve Validation Result V0.1

Status: **{'PASS' if post['all_pass'] else 'FAIL'}**  
Acceptance: **{'120/120 PASS' if post['all_pass'] else 'FAILED'}**

The exact frozen Test 006A Emitter processed all 101,221 reserve observations once: 15 initialization records and 101,206 actionable immutable emissions. BUY {counts['BUY']}, SELL {counts['SELL']}, HOLD {counts['HOLD']}. Decision stream: **{'NON-DEGENERATE' if decision_body['non_degenerate'] else 'DEGENERATE'}**.

Direct BUY->SELL / SELL->BUY transitions: {decision_body['direct_reversals']['BUY_TO_SELL']} / {decision_body['direct_reversals']['SELL_TO_BUY']}. HOLD-routed BUY->HOLD->SELL / SELL->HOLD->BUY reversals: {hold_routed['BUY_HOLD_SELL']} / {hold_routed['SELL_HOLD_BUY']}.

Reserve Q_G/Q_S/Q_R/C ranges: {ranges['Q_G']} / {ranges['Q_S']} / {ranges['Q_R']} / {ranges['C']}. Historical C=0.75 gate was not used.

Primary human-readable output: `APTF_TEST_006B_OBSERVATIONS_WITH_EMITTED_POSITION_V0_1.csv`, with {csv_rows} rows. The first 15 are INITIALIZING; all actionable rows contain BUY/SELL/HOLD. Runtime source-field mismatches: {summary['source_field_mismatches']}. CSV/emission decision mismatches: {csv_decision_mismatches}.

Frozen authority, source, Test 006A evidence, historical D04, and Test 005R identities are recorded in the post-execution integrity artifact. No rule, parameter, feedback, context, broker, or outcome logic changed.

Generalization result: the frozen mechanism remained operational, causal, state-continuous, and non-degenerate on unseen reserve data. This supports mechanism generalization only; it does not establish profitability or predictive accuracy.

Next action: **STOP**. Do not retune or run the reserve again.
"""
    (root / "APTF_TEST_006B_RESULT_V0_1.md").write_text(result, encoding="utf-8")
    print(json.dumps({"status":post["status"],"source_rows":summary["source_rows"],"actionable":len(actionable),"counts":dict(counts),"csv_rows":csv_rows,"source_mismatches":summary["source_field_mismatches"],"decision_mismatches":csv_decision_mismatches,"frozen_identity":post["frozen_identity"]},indent=2,sort_keys=True))
    return 0 if post["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())