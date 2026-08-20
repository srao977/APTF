from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spy_volume_engine import VolumePolicyConfig
from test014c_common import ROOT, SPLIT, load_common_rows, replay, score, sha256, write_csv, write_json


POLICY = ROOT / "APTF_TEST_014C_SPY_V_EMISSION_POLICY_V0_1.json"


def candidates() -> list[tuple[str, str, VolumePolicyConfig]]:
    return [
        ("V_POINT_B10_C1", "point V_N, +/-10% baseline band, immediate", VolumePolicyConfig("V_POINT_B10_C1", "V_N", .90, 1.10, 1, 1e-12)),
        ("V_POINT_B20_C2", "point V_N, +/-20% baseline band, two-observation confirmation", VolumePolicyConfig("V_POINT_B20_C2", "V_N", .80, 1.20, 2, 1e-12)),
        ("V_INTERVAL_B10_C2", "15-row mean V_N, +/-10% baseline band, two-observation confirmation", VolumePolicyConfig("V_INTERVAL_B10_C2", "INTERVAL_MEAN_V_N", .90, 1.10, 2, 1e-12)),
        ("V_INTERVAL_B20_C3", "15-row mean V_N, +/-20% baseline band, three-observation confirmation", VolumePolicyConfig("V_INTERVAL_B20_C3", "INTERVAL_MEAN_V_N", .80, 1.20, 3, 1e-12)),
    ]


def main() -> int:
    print("""APTF TEST 014C —
SPY V-ENGINE COCKPIT EMISSION
AND DUAL-ENGINE CONTIGUOUS INTERVAL OBSERVATION

OBJECTIVE: BUILD THE INDEPENDENT SPY V LAMP AND OBSERVE P/V STATE INTERVALS.
P ENGINE: FROZEN / NOT MODIFIED.
P V0.2 STATUS: CONDITIONAL EVIDENCE.
V ENGINE: CURRENT TEST SUBJECT.
P/V FUSION: NO.
EXECUTION CONTROLLER: NO.
PAPER TRADING: NO.
BROKER: NO.

HARD VISUAL REQUIREMENT: ALL ENGINE COLORS MUST BE CONTIGUOUS WITHIN EACH ELIGIBLE MARKET SESSION.
BEGIN AUTHORITY AUDIT.""")
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    rows = load_common_rows()
    development = [row for row in rows if row["partition"] == "DEVELOPMENT"]
    if len(development) != int(split["development"]["rows"]):
        raise RuntimeError("Test-014 development cover changed")
    results = []
    configs = {}
    descriptions = {}
    for policy_id, description, config in candidates():
        emissions, _ = replay(development, config)
        result = score(policy_id, emissions, int(split["development"]["sessions"]))
        results.append({"candidate_id": policy_id, "description": description, "parameters": json.dumps(asdict(config), sort_keys=True), **result})
        configs[policy_id] = config
        descriptions[policy_id] = description
    eligible = [
        row for row in results
        if row["GREEN_occupancy"] >= .075 and row["RED_occupancy"] >= .075
        and row["AMBER_occupancy"] <= .50 and row["median_interval"] >= 3
    ]
    if not eligible:
        raise RuntimeError("NO_INTERPRETABLE_V_POLICY")
    selected = min(eligible, key=lambda row: (row["changes_per_session"], -row["median_interval"], row["candidate_id"]))
    config = configs[selected["candidate_id"]]
    policy = {
        "policy_id": "V_EMISSION_V0_1", "selected_candidate": selected["candidate_id"],
        "description": descriptions[selected["candidate_id"]], "created_from_partition": "TEST_014_DEVELOPMENT_ONLY",
        "validation_outcomes_read": False, "status": "FROZEN_BEFORE_VALIDATION", "parameters": asdict(config),
        "V_definition": "V_N = raw Volume / trailing 15-observation raw-Volume median",
        "V1_definition": "current derivative of causal quadratic over 3 normalized-Volume observations",
        "V2_definition": "current second derivative of causal quadratic over 3 normalized-Volume observations",
        "trajectory_model": "G_V discrete point persistence: projected_V(t+1)=V_N(t)",
        "projected_V1_V2": "UNSUPPORTED_NOT_FABRICATED", "RK45": False,
        "GREEN_semantics": "normalized trading activity state above the causal baseline band",
        "AMBER_semantics": "normalized trading activity near baseline or pending a confirmed state change",
        "RED_semantics": "normalized trading activity state below the causal baseline band",
        "color_is_price_direction": False, "price_inputs_used": False,
        "selection_rule": "minimum development changes/session subject to >=7.5% GREEN and RED occupancy, <=50% AMBER occupancy, and median interval >=3 minutes",
    }
    write_json(POLICY, policy)
    policy_hash = sha256(POLICY)
    write_csv(ROOT / "APTF_TEST_014C_V_DEVELOPMENT_SCORECARD_V0_1.csv", results)
    write_json(ROOT / "APTF_TEST_014C_V_POLICY_FREEZE_V0_1.json", {
        "policy_sha256": policy_hash, "selected_candidate": selected["candidate_id"],
        "candidate_count": len(results), "frozen_before_validation": True, "validation_read": False,
    })
    print("\nV-ENGINE AUTHORITY")
    print("Volume field: volume / V_RAW")
    print("V: ROLLING_MEDIAN_RATIO_15; V1/V2: causal quadratic window 3")
    print("Trajectory model: discrete VOLUME_POINT; RK45 authority: NO")
    print("Was P model copied automatically? NO")
    print("\nV-ENGINE DEVELOPMENT")
    print(json.dumps({"development_rows": len(development), "candidate_policies": len(results), "selected": selected, "policy_sha256": policy_hash, "frozen_before_validation": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())