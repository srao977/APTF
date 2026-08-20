from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spy_price_engine.cockpit import CockpitPolicyConfig
from test014b_common import (
    EMISSIONS_V01,
    ROOT,
    SPLIT,
    TURNS_V01,
    V01_SCORECARD,
    flatten_score,
    load_rows,
    load_turns,
    replay,
    score,
    sha256,
    write_csv,
    write_json,
)


POLICY_PATH = ROOT / "APTF_TEST_014B_SPY_P_EMISSION_POLICY_V0_2.json"


def initial_output() -> None:
    print("""APTF TEST 014B —
SPY P-ENGINE EMISSION STATE REFINEMENT

==================================================
OBJECTIVE:
FINISH THE SPY P-ENGINE COCKPIT LAMP.

PRICE ENGINE MATHEMATICS: FROZEN.
F4: FROZEN.
LAMBDA: FROZEN.
WINDOW: FROZEN.
RK45: FROZEN.
MARKET OBSERVATION INTERFACE: FROZEN.
PRICE EMISSION INTERFACE: FROZEN.

==================================================
TEST 014 PROBLEM:
AMBER TOO BROAD.
COCKPIT CHATTER TOO HIGH.
FALSE PRECURSOR RATE TOO HIGH.

TEST 014B MAY MODIFY: EMISSION INTERPRETATION ONLY.
TEST 014B MAY NOT MODIFY: PRICE DYNAMICS.

NO VOLUME. NO V ENGINE. NO EXECUTION CONTROLLER.
NO P&L OPTIMIZATION. NO BUY. NO SELL. NO SHORT.
NO BROKER. NO EXTERNAL ETF.

BEGIN TEST-014 BASELINE REPRODUCTION.""")


def baseline_reproduction(split: dict[str, Any]) -> dict[str, Any]:
    rows = load_rows("VALIDATION")
    turns = load_turns("VALIDATION")
    calculated = score("P_EMISSION_V0_1", rows, turns, int(split["validation"]["sessions"]), "V0.1")
    with V01_SCORECARD.open(newline="", encoding="utf-8") as handle:
        authority = next(csv.DictReader(handle))
    comparisons = {
        "eligible_observations": len(rows) == int(authority["observations"]),
        "GREEN": calculated["GREEN_count"] == int(authority["GREEN_count"]),
        "AMBER": calculated["AMBER_count"] == int(authority["AMBER_count"]),
        "RED": calculated["RED_count"] == int(authority["RED_count"]),
        "INVALID": calculated["INVALID_count"] == int(authority["INVALID_count"]),
        "color_changes": calculated["color_changes"] == int(authority["in_session_color_changes"]),
        "changes_per_session": abs(calculated["changes_per_session"] - float(authority["changes_per_session"])) < 1e-12,
        "direct_GREEN_RED": calculated["direct_GREEN_RED"] == int(authority["direct_GREEN_RED"]),
        "direct_RED_GREEN": calculated["direct_RED_GREEN"] == int(authority["direct_RED_GREEN"]),
        "maxima_recall": abs(calculated["maxima_recall"] - float(authority["maxima_recall"])) < 1e-12,
        "minima_recall": abs(calculated["minima_recall"] - float(authority["minima_recall"])) < 1e-12,
        "maxima_median_lead": calculated["maxima_median_lead"] == float(authority["maxima_median_lead"]),
        "minima_median_lead": calculated["minima_median_lead"] == float(authority["minima_median_lead"]),
        "combined_false_rate": abs(
            (calculated["maxima_false_warnings"] + calculated["minima_false_warnings"])
            / (calculated["maxima_warnings"] + calculated["minima_warnings"])
            - float(authority["false_precursor_rate"])
        ) < 1e-12,
    }
    reproduced = all(comparisons.values())
    payload = {
        "test_id": "APTF_TEST_014B_BASELINE_REPRODUCTION_V0_1",
        "reproduced": reproduced,
        "comparisons": comparisons,
        "calculated": flatten_score(calculated),
        "authoritative_scorecard_sha256": sha256(V01_SCORECARD),
        "emissions_v01_sha256": sha256(EMISSIONS_V01),
        "turns_v01_sha256": sha256(TURNS_V01),
        "archived_reconciled_directional_false_rates": {
            "maxima": float(authority["false_deterioration_rate"]),
            "minima": float(authority["false_recovery_rate"]),
            "note": "Test-014 archived directional reconciliation; combined replay authority is scored independently",
        },
    }
    write_json(ROOT / "APTF_TEST_014B_BASELINE_REPRODUCTION_V0_1.json", payload)
    if not reproduced:
        raise RuntimeError("TEST_014B_BLOCKED_BASELINE_REPRODUCTION")
    return payload


def candidates(epsilon: float) -> list[tuple[str, str, CockpitPolicyConfig]]:
    definitions = [
        ("TRANSITION_EVIDENCE_P1", "one-observation opposition with normalized zero approach and minimum deceleration strength", 0.90, 0.05, 1, 0, False),
        ("PERSISTENCE_2", "phase + two-observation opposing persistence", 1.0, 0.0, 2, 0, False),
        ("ZERO_APPROACH_P2", "phase + persistence + normalized projected-P1 zero approach", 0.35, 0.25, 2, 0, False),
        ("CROSS_PERSIST_P3", "phase + persistence + zero approach + projected-P1 crossing", 0.50, 0.20, 3, 1, False),
        ("STATE_HYSTERESIS_P3", "cross/persistent transition with two-row candidate hysteresis", 0.50, 0.20, 3, 2, False),
    ]
    return [
        (
            policy_id,
            description,
            CockpitPolicyConfig(
                policy_id=policy_id,
                epsilon=epsilon,
                zero_proximity_threshold=zero_threshold,
                deceleration_strength_threshold=strength_threshold,
                persistence_observations=persistence,
                candidate_hold_observations=hold,
                low_confidence_requires_amber=confidence,
                domain_exit_requires_amber=False,
            ),
        )
        for policy_id, description, zero_threshold, strength_threshold, persistence, hold, confidence in definitions
    ]


def main() -> int:
    initial_output()
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    baseline = baseline_reproduction(split)
    policy_v01 = json.loads((ROOT / "APTF_TEST_014_SPY_P_EMISSION_POLICY_V0_1.json").read_text(encoding="utf-8"))
    development_rows = load_rows("DEVELOPMENT")
    if len(development_rows) != int(split["development"]["rows"]):
        raise RuntimeError("TEST_014_DEVELOPMENT_SPLIT_CHANGED")
    development_turns = load_turns("DEVELOPMENT")
    baseline_development = score(
        "P_EMISSION_V0_1", development_rows, development_turns, int(split["development"]["sessions"]), "V0.1"
    )

    candidate_rows = []
    candidate_scores = []
    configurations = {}
    descriptions = {}
    for policy_id, description, config in candidates(float(policy_v01["epsilon"])):
        interpreted, _ = replay(development_rows, config)
        candidate_score = score(policy_id, interpreted, development_turns, int(split["development"]["sessions"]), "V0.2")
        candidate_scores.append(candidate_score)
        configurations[policy_id] = config
        descriptions[policy_id] = description
        candidate_rows.append(
            {
                "candidate_id": policy_id,
                "rule_summary": description,
                "parameters": json.dumps(config.__dict__, sort_keys=True, separators=(",", ":")),
                **flatten_score(candidate_score),
            }
        )

    minimum_average_recall = (baseline_development["maxima_recall"] + baseline_development["minima_recall"]) / 4
    eligible = [
        item
        for item in candidate_scores
        if (item["maxima_recall"] + item["minima_recall"]) / 2 >= minimum_average_recall
        and item["maxima_false_rate"] + item["minima_false_rate"]
        <= baseline_development["maxima_false_rate"] + baseline_development["minima_false_rate"]
    ]
    if not eligible:
        raise RuntimeError("NO_DEVELOPMENT_CANDIDATE_PRESERVED_MINIMUM_INFORMATION")
    selected_score = min(
        eligible,
        key=lambda item: (
            item["changes_per_session"],
            item["maxima_false_rate"] + item["minima_false_rate"],
            -(item["maxima_recall"] + item["minima_recall"]),
            item["policy_id"],
        ),
    )
    selected_id = str(selected_score["policy_id"])
    selected_config = configurations[selected_id]
    policy = {
        "policy_id": "P_EMISSION_V0_2",
        "selected_candidate": selected_id,
        "description": descriptions[selected_id],
        "created_from_partition": "TEST_014_DEVELOPMENT_ONLY",
        "validation_outcomes_read": False,
        "status": "FROZEN_BEFORE_VALIDATION",
        "parameters": selected_config.__dict__,
        "normalization": {
            "P1_zero_proximity": "abs(projected_P1) / max(abs(P1), abs(projected_P1), epsilon)",
            "deceleration_strength": "opposing_abs(projected_P1 - P1) / max(abs(P1), epsilon)",
        },
        "candidate_rule": "crossing OR (opposition persistent AND zero proximity threshold met AND deceleration strength threshold met)",
        "hysteresis": "candidate retained for candidate_hold_observations after evidence disappears",
        "confidence_handling": "LOW causes AMBER only when low_confidence_requires_amber=true",
        "domain_handling": "OUT_OF_DOMAIN is retained but does not automatically determine color",
        "invalid_handling": "RK failure or nonfinite trajectory remains INVALID",
        "visible_colors": ["GREEN", "AMBER", "RED"],
        "color_is_trade_action": False,
        "selection_rule": "minimum development changes/session subject to >=50% of V0.1 average recall and no worse combined directional false-warning rate",
    }
    write_json(POLICY_PATH, policy)
    policy_hash = sha256(POLICY_PATH)

    write_csv(ROOT / "APTF_TEST_014B_POLICY_CANDIDATES_V0_1.csv", candidate_rows)
    development_scorecards = [
        {"candidate_id": "P_EMISSION_V0_1", "selected": False, **flatten_score(baseline_development)}
    ] + [
        {"candidate_id": item["policy_id"], "selected": item["policy_id"] == selected_id, **flatten_score(item)}
        for item in candidate_scores
    ]
    write_csv(ROOT / "APTF_TEST_014B_DEVELOPMENT_SCORECARD_V0_1.csv", development_scorecards)
    freeze = {
        "policy_path": POLICY_PATH.name,
        "policy_sha256": policy_hash,
        "selected_candidate": selected_id,
        "candidate_count_excluding_control": len(candidate_scores),
        "baseline_reproduced": baseline["reproduced"],
        "validation_read_during_selection": False,
        "policy_frozen_before_validation": True,
    }
    write_json(ROOT / "APTF_TEST_014B_POLICY_FREEZE_V0_1.json", freeze)
    print("\nTEST 014 BASELINE REPRODUCTION")
    print(json.dumps(flatten_score(baseline["calculated"]), indent=2, sort_keys=True))
    print("\nBASELINE REPRODUCED: YES")
    print("\nTEST 014B — DEVELOPMENT POLICY SELECTION")
    print(f"Candidate policies tested: {len(candidate_scores)} plus V0.1 control")
    print(f"Selected V0.2: {selected_id}")
    print(json.dumps(flatten_score(selected_score), indent=2, sort_keys=True))
    print(f"POLICY HASH: {policy_hash}")
    print("POLICY FROZEN BEFORE VALIDATION: YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())