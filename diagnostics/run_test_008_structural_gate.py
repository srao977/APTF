from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for path in (
    ROOT / "aptf_runtime" / "src",
    ROOT / "d01_adaptive_parametric_model" / "src",
    ROOT / "d02_return_shape" / "src",
    ROOT / "d04_trading_envelope" / "src",
):
    sys.path.insert(0, str(path))

from aptf_runtime.models import EmitterDecision, ExecutionIntent, PositionState  # noqa: E402
from aptf_runtime.position import apply_position_decision  # noqa: E402


MAP_PATH = ROOT / "APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv"
EPISODE_PATH = ROOT / "APTF_TEST_007_POSITION_EPISODES_V0_1.csv"
FREEZE_HASHES_PATH = ROOT / "APTF_RUNTIME_CORE_FREEZE_HASHES_V0_1.json"


def verify_runtime() -> dict[str, object]:
    frozen = json.loads(FREEZE_HASHES_PATH.read_text(encoding="utf-8"))
    mismatches = []
    for item in frozen["files"]:
        actual = hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest()
        if actual != item["sha256"]:
            mismatches.append({"path": item["path"], "expected": item["sha256"], "actual": actual})
    return {
        "expected_files": len(frozen["files"]),
        "matched_files": len(frozen["files"]) - len(mismatches),
        "mismatches": mismatches,
        "status": "PASS" if not mismatches else "FAIL",
    }


def main() -> int:
    runtime = verify_runtime()
    episodes = list(csv.DictReader(EPISODE_PATH.open(newline="", encoding="utf-8")))
    episode_ids = {item["episode_id"] for item in episodes}
    rows = 0
    initializing = 0
    actionable = 0
    initialization_violations = []
    replay_violations = []
    classifications: Counter[str] = Counter()
    generated_intents: Counter[str] = Counter()
    filled_intents: Counter[str] = Counter()
    missing_open = []
    collisions = []
    pending: dict[str, str] | None = None
    execution_sequence = 0

    with MAP_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows += 1

            if pending is not None:
                if not row["open"]:
                    missing_open.append({
                        "execution_id": pending["execution_id"],
                        "execution_source_observation_index": row["test006b_observation_index"],
                    })
                else:
                    filled_intents[pending["intent"]] += 1
                    pending = None

            decision = row["position_decision"]
            if decision == "INITIALIZING":
                initializing += 1
                if rows > 15 or any((
                    row["test007_position_state_before"] != "FLAT",
                    row["test007_position_state_after"] != "FLAT",
                    row["test007_episode_id"] != "",
                    row["test007_structural_classification"] != "INITIALIZING",
                )):
                    initialization_violations.append(rows)
                continue

            actionable += 1
            transition = apply_position_decision(
                PositionState(row["test007_position_state_before"]),
                EmitterDecision(decision),
            )
            if (
                transition.state_after.value != row["test007_position_state_after"]
                or transition.structural_classification
                != row["test007_structural_classification"]
            ):
                replay_violations.append(row["test006b_observation_index"])
            classifications[transition.structural_classification] += 1

            if transition.execution_intent is not ExecutionIntent.NONE:
                if pending is not None:
                    collisions.append({
                        "existing": pending["execution_id"],
                        "new_signal_observation_index": row["test006b_observation_index"],
                    })
                    continue
                execution_sequence += 1
                execution_id = f"EX{execution_sequence:06d}"
                pending = {
                    "execution_id": execution_id,
                    "intent": transition.execution_intent.value,
                    "signal_observation_index": row["test006b_observation_index"],
                }
                generated_intents[transition.execution_intent.value] += 1

    unresolved = [] if pending is None else [pending]
    expected_classifications = {
        "EPISODE_OPEN": 2051,
        "REPEATED_BUY_WHILE_LONG": 12198,
        "EPISODE_CLOSE": 2051,
        "UNMATCHED_SELL_WHILE_FLAT": 7728,
        "EPISODE_HOLD": 39787,
        "FLAT_HOLD": 37391,
    }
    expected_episode_ids = {f"EP{index:06d}" for index in range(1, 2052)}
    initialization_pass = (
        rows == 101221
        and initializing == 15
        and actionable == 101206
        and not initialization_violations
    )
    structural_pass = (
        runtime["status"] == "PASS"
        and initialization_pass
        and not replay_violations
        and dict(classifications) == expected_classifications
        and len(episodes) == 2051
        and episode_ids == expected_episode_ids
        and generated_intents == {"BUY": 2051, "SELL": 2051}
        and filled_intents == generated_intents
        and not missing_open
        and not unresolved
        and not collisions
    )

    initialization_audit = {
        "test_id": "APTF_TEST_008_INITIALIZATION_EXCLUSION_AUDIT_V0_2",
        "total_source_rows": rows,
        "initializing_rows_found": initializing,
        "initializing_rows_leading": initializing == 15 and not initialization_violations,
        "initializing_rows_marked_excluded": initializing,
        "initializing_buy_executions": 0,
        "initializing_sell_executions": 0,
        "initializing_pending_executions": 0,
        "initializing_trades": 0,
        "initializing_realized_gross_pnl": "0",
        "initializing_trade_statistics_contribution": 0,
        "actionable_rows": actionable,
        "violations": initialization_violations,
        "status": "PASS" if initialization_pass else "FAIL",
    }
    structural_gate = {
        "test_id": "APTF_TEST_008_PRE_PNL_STRUCTURAL_GATE_V0_2",
        "runtime_core": runtime,
        "reserve_emitter_reruns": 0,
        "source_rows": rows,
        "initializing_excluded": initializing,
        "actionable_expected": 101206,
        "actionable_replayed": actionable,
        "position_replay_matches": actionable - len(replay_violations),
        "position_replay_violations": replay_violations,
        "test007_episode_count": len(episodes),
        "episode_ids_reconciled": episode_ids == expected_episode_ids,
        "structural_counts": dict(classifications),
        "generated_execution_intents": dict(generated_intents),
        "filled_execution_intents": dict(filled_intents),
        "next_observation_open_available_for_all_entries": not any(
            item.get("intent") == "BUY" for item in unresolved
        ) and not missing_open,
        "next_observation_open_available_for_all_exits": not any(
            item.get("intent") == "SELL" for item in unresolved
        ) and not missing_open,
        "no_next_observation_executions": unresolved,
        "missing_open_executions": missing_open,
        "pending_execution_collisions": collisions,
        "same_observation_execution_used": False,
        "pnl_calculated": False,
        "status": "PASS" if structural_pass else "FAIL",
    }
    (ROOT / "APTF_TEST_008_INITIALIZATION_EXCLUSION_AUDIT_V0_2.json").write_text(
        json.dumps(initialization_audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / "APTF_TEST_008_PRE_PNL_STRUCTURAL_GATE_V0_2.json").write_text(
        json.dumps(structural_gate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "initialization": initialization_audit["status"],
        "structural_gate": structural_gate["status"],
        "actionable_replay": actionable,
        "position_matches": structural_gate["position_replay_matches"],
        "execution_intents": dict(generated_intents),
        "pending_collisions": len(collisions),
        "pnl_calculated": False,
    }, indent=2, sort_keys=True))
    return 0 if structural_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())