from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.linalg import expm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run_test_013b_qqq_validation as frozen
from spy_price_engine import EmissionPolicy, MarketObservation, PolicyConfig, PolicyState, PriceEngine


ROOT = Path(__file__).resolve().parents[1]
PRICE = ROOT / "APTF_TEST_009_DERIVATIVE_OBSERVATIONS_V0_1.csv"
SOURCE = ROOT / "APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv"
EMISSIONS = ROOT / "APTF_TEST_010_PRICE_ENGINE_EMISSIONS_V0_1.csv"
SPLIT = ROOT / "APTF_TEST_014_DEVELOPMENT_VALIDATION_SPLIT_V0_1.json"
DEVELOPMENT_FREEZE = ROOT / "APTF_TEST_014_POLICY_DEVELOPMENT_FREEZE_V0_1.json"


def load_authority():
    price = list(csv.DictReader(PRICE.open(newline="", encoding="utf-8")))
    source = list(csv.DictReader(SOURCE.open(newline="", encoding="utf-8")))
    emissions = {int(row["observation_index"]): row for row in csv.DictReader(EMISSIONS.open(newline="", encoding="utf-8"))}
    p = np.asarray([float(row["price"]) for row in price])
    p1 = np.asarray([np.nan if row["primary_D1"] == "" else float(row["primary_D1"]) for row in price])
    p2 = np.asarray([np.nan if row["primary_D2"] == "" else float(row["primary_D2"]) for row in price])
    jp = np.full(len(p), np.nan)
    for observation, row in emissions.items():
        index = observation - 1
        if row["transition_stratum"] == "INTRASESSION_CONTINUOUS" and index > 0:
            jp[index] = p2[index] - p2[index - 1]
    return price, source, emissions, p, p1, p2, jp


def eligible_observations(price, emissions, jp):
    eligible = []
    for observation, row in emissions.items():
        index = observation - 1
        if (
            observation >= 30
            and observation < len(price)
            and row["transition_stratum"] == "INTRASESSION_CONTINUOUS"
            and float(row["next_elapsed_minutes"]) == 1.0
            and np.all(np.isfinite(jp[index - 29:index + 1]))
        ):
            eligible.append(observation)
    return sorted(eligible)


def contiguous(left: int, right: int, source: list[dict[str, str]]) -> bool:
    left_time = datetime.fromisoformat(source[left]["event_timestamp_utc"].replace("Z", "+00:00"))
    right_time = datetime.fromisoformat(source[right]["event_timestamp_utc"].replace("Z", "+00:00"))
    return source[left]["session_type"] == source[right]["session_type"] and (right_time - left_time).total_seconds() == 60.0


def observed_turns(indices: set[int], p: np.ndarray, source: list[dict[str, str]], radius: int = 3):
    turns = []
    for index in sorted(indices):
        if index < radius or index + radius >= len(p):
            continue
        if not all(contiguous(position, position + 1, source) for position in range(index - radius, index + radius)):
            continue
        neighbors = np.r_[p[index - radius:index], p[index + 1:index + radius + 1]]
        if p[index] > np.max(neighbors):
            turns.append({"index": index, "type": "MAXIMUM", "price": p[index]})
        elif p[index] < np.min(neighbors):
            turns.append({"index": index, "type": "MINIMUM", "price": p[index]})
    return turns


def build_numerical(observations, fit, solved, failed, price, source, p, p1, p2):
    rows = []
    for observation in observations:
        index = observation - 1
        physical = fit["physical"][index]
        matrix = np.asarray([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], physical[1:]])
        eigenvalues = np.linalg.eigvals(matrix)
        amplification = float(max(np.linalg.norm(expm(matrix)[:, component]) for component in range(3)))
        if index in failed:
            projected = np.asarray([p[index], p1[index], p2[index]])
            success = False
            domain_exit = False
        else:
            projected = np.asarray(solved[index]["trajectory"])[-1]
            success = True
            domain_exit = bool(solved[index]["envelope_exit"])
        rows.append({
            "index": index, "observation_index": observation, "symbol": "SPY",
            "timestamp": price[index]["timestamp"], "session": source[index]["session_type"],
            "open": float(source[index]["open"]), "high": float(source[index]["high"]),
            "low": float(source[index]["low"]), "close": float(source[index]["close"]),
            "volume": float(source[index]["volume"]), "source_provider": source[index]["source_provider"],
            "p": p[index], "p1": p1[index], "p2": p2[index],
            "projected_p": projected[0], "projected_p1": projected[1], "projected_p2": projected[2],
            "rk_success": success, "domain_exit": domain_exit,
            "condition_number": fit["condition"][index],
            "max_real_eigenvalue": float(eigenvalues.real.max()),
            "perturbation_amplification": amplification,
            "local_coefficients_json": json.dumps(fit["standardized"][index].tolist(), separators=(",", ":")),
            "local_center_json": json.dumps(fit["means"][index].tolist(), separators=(",", ":")),
            "local_scale_json": json.dumps(fit["scales"][index].tolist(), separators=(",", ":")),
            "D_local_maximum": "" if index in failed else solved[index]["D_local_maximum"],
            "first_exit_time": "" if index in failed else solved[index]["first_exit_time"],
            "exit_dimension": "" if index in failed else solved[index]["exit_dimension"],
        })
    return rows


def apply_policy(numerical, config):
    policy = EmissionPolicy(config)
    engine = PriceEngine(policy)
    output = []
    state = PolicyState()
    previous_session = None
    for row in numerical:
        session_id = row["timestamp"][:10] + ":" + row["session"]
        if session_id != previous_session:
            state = PolicyState()
            previous_session = session_id
        observation = MarketObservation(
            symbol="SPY", timestamp=row["timestamp"], open=row["open"], high=row["high"],
            low=row["low"], close=row["close"], volume=row["volume"], session=row["session"],
            source=row["source_provider"],
        )
        emission, state = engine.observe(observation, row, state)
        output.append(row | emission.as_dict())
    return output


def warning(row, turn_type):
    if turn_type == "MAXIMUM":
        return row["trajectory_phase"] in {"UP_DECELERATING", "TURNING_DOWN"} or row["turning_tendency"] in {"DETERIORATING_TOWARD_TURN", "TURNING_DOWN"}
    return row["trajectory_phase"] in {"DOWN_DECELERATING", "TURNING_UP"} or row["turning_tendency"] in {"RECOVERING_TOWARD_TURN", "TURNING_UP"}


def policy_score(policy_id, rows, turns, sessions, horizon=5):
    by_index = {int(row["index"]): row for row in rows}
    colors = [row["color"] for row in rows]
    changes = sum(left != right for left, right in zip(colors, colors[1:]))
    direct_green_red = sum(left == "GREEN" and right == "RED" for left, right in zip(colors, colors[1:]))
    direct_red_green = sum(left == "RED" and right == "GREEN" for left, right in zip(colors, colors[1:]))
    turn_results = []
    for turn in turns:
        candidates = [by_index[index] for index in range(turn["index"] - horizon, turn["index"]) if index in by_index]
        precursors = [row for row in candidates if warning(row, turn["type"])]
        amber = [row for row in candidates if row["color"] == "AMBER"]
        directional = [row for row in candidates if row["color"] == ("RED" if turn["type"] == "MAXIMUM" else "GREEN")]
        first = None if not precursors else precursors[0]
        turn_results.append({
            "type": turn["type"], "detected": first is not None,
            "lead": None if first is None else turn["index"] - int(first["index"]),
            "prior_amber": bool(amber), "prior_directional": bool(directional),
        })
    maxima = [row for row in turn_results if row["type"] == "MAXIMUM"]
    minima = [row for row in turn_results if row["type"] == "MINIMUM"]
    turn_lookup = {kind: {turn["index"] for turn in turns if turn["type"] == kind} for kind in ("MAXIMUM", "MINIMUM")}
    warning_count = false_count = 0
    for row in rows:
        for kind in ("MAXIMUM", "MINIMUM"):
            if warning(row, kind):
                warning_count += 1
                if not any(int(row["index"]) < turn_index <= int(row["index"]) + horizon for turn_index in turn_lookup[kind]):
                    false_count += 1
    leads_max = [row["lead"] for row in maxima if row["lead"] is not None]
    leads_min = [row["lead"] for row in minima if row["lead"] is not None]
    counts = Counter(colors)
    return {
        "policy_id": policy_id, "observations": len(rows), "sessions": sessions,
        "GREEN_count": counts["GREEN"], "AMBER_count": counts["AMBER"], "RED_count": counts["RED"], "INVALID_count": counts["INVALID"],
        "color_changes": changes, "changes_per_session": changes / sessions,
        "direct_GREEN_RED": direct_green_red, "direct_RED_GREEN": direct_red_green,
        "maxima": len(maxima), "maxima_detected": sum(row["detected"] for row in maxima),
        "maxima_recall": 0.0 if not maxima else sum(row["detected"] for row in maxima) / len(maxima),
        "maxima_median_lead": None if not leads_max else float(np.median(leads_max)),
        "minima": len(minima), "minima_detected": sum(row["detected"] for row in minima),
        "minima_recall": 0.0 if not minima else sum(row["detected"] for row in minima) / len(minima),
        "minima_median_lead": None if not leads_min else float(np.median(leads_min)),
        "warning_count": warning_count, "false_warning_count": false_count,
        "false_precursor_rate": 0.0 if not warning_count else false_count / warning_count,
    }


def main() -> int:
    split = json.loads(SPLIT.read_text())
    development_freeze = json.loads(DEVELOPMENT_FREEZE.read_text())
    price, source, emissions, p, p1, p2, jp = load_authority()
    all_eligible = eligible_observations(price, emissions, jp)
    split_date = split["first_validation_local_date"]
    development = [observation for observation in all_eligible if price[observation - 1]["timestamp"][:10] < split_date]
    if len(development) != split["development"]["rows"]:
        raise RuntimeError("DEVELOPMENT_SPLIT_CHANGED")
    fit = frozen.fit_f4(p, p1, p2, jp, 30)
    indices = [observation - 1 for observation in development]
    solved, failed = frozen.solve_cover(indices, fit, p, p1, p2, False)
    numerical = build_numerical(development, fit, solved, failed, price, source, p, p1, p2)
    valid = [row for row in numerical if row["rk_success"]]
    condition = np.asarray([row["condition_number"] for row in valid])
    eigenvalue = np.asarray([row["max_real_eigenvalue"] for row in valid])
    amplification = np.asarray([row["perturbation_amplification"] for row in valid])
    thresholds = {
        "condition_median": float(np.median(condition)), "condition_q95": float(np.quantile(condition, .95)),
        "eigenvalue_median": float(np.median(eigenvalue)), "eigenvalue_q95": float(np.quantile(eigenvalue, .95)),
        "amplification_median": float(np.median(amplification)), "amplification_q95": float(np.quantile(amplification, .95)),
    }
    candidates = []
    emissions_by_candidate = {}
    development_indices = set(indices)
    turns = observed_turns(development_indices, p, source)
    for candidate in development_freeze["candidates"]:
        config = PolicyConfig(candidate["policy_id"], frozen.EPSILON, **thresholds, direct_reversal_debounce=candidate["direct_reversal_debounce"])
        candidate_emissions = apply_policy(numerical, config)
        emissions_by_candidate[candidate["policy_id"]] = candidate_emissions
        candidates.append(policy_score(candidate["policy_id"], candidate_emissions, turns, split["development"]["sessions"]))
    raw = next(row for row in candidates if row["policy_id"] == "PHASE_RULES_RAW")
    debounce = next(row for row in candidates if row["policy_id"] == "PHASE_RULES_DEBOUNCE_1")
    change_reduction = 0.0 if raw["color_changes"] == 0 else 1 - debounce["color_changes"] / raw["color_changes"]
    raw_direct = raw["direct_GREEN_RED"] + raw["direct_RED_GREEN"]
    debounce_direct = debounce["direct_GREEN_RED"] + debounce["direct_RED_GREEN"]
    direct_reduction = 0.0 if raw_direct == 0 else 1 - debounce_direct / raw_direct
    recall_preserved = debounce["maxima_recall"] >= raw["maxima_recall"] - .02 and debounce["minima_recall"] >= raw["minima_recall"] - .02
    selected = "PHASE_RULES_DEBOUNCE_1" if max(change_reduction, direct_reduction) >= .20 and recall_preserved else "PHASE_RULES_RAW"
    selected_candidate = next(candidate for candidate in development_freeze["candidates"] if candidate["policy_id"] == selected)
    policy = {
        "policy_id": "P_EMISSION_V0_1",
        "selected_candidate": selected,
        "created_from_partition": "DEVELOPMENT_ONLY",
        "validation_outcomes_read": False,
        "epsilon": frozen.EPSILON,
        **thresholds,
        "direct_reversal_debounce": selected_candidate["direct_reversal_debounce"],
        "confirmation_observations": 1 if selected_candidate["direct_reversal_debounce"] else 0,
        "phase_rules": "spy_price_engine.policy._phase",
        "turning_rules": "spy_price_engine.policy._turning_tendency",
        "color_rules": "GREEN confident UP_ACCELERATING/TURNING_UP; RED confident DOWN_ACCELERATING/TURNING_DOWN; AMBER transitional/near-stationary/LOW; INVALID solver/nonfinite",
        "domain_exit_effect": "confidence LOW; not automatic RED",
        "confidence_rules": "development Q50/Q95 thresholds over condition, max-real eigenvalue, perturbation amplification",
        "reason_codes_required": True,
        "color_is_trade_action": False,
        "selection_evidence": {"color_change_reduction": change_reduction, "direct_reversal_reduction": direct_reduction, "recall_preserved": recall_preserved},
        "status": "FROZEN_BEFORE_VALIDATION"
    }
    policy_path = ROOT / "APTF_TEST_014_SPY_P_EMISSION_POLICY_V0_1.json"
    policy_path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (ROOT / "APTF_TEST_014_SPY_P_EMISSION_DEVELOPMENT_SCORECARD_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(candidates[0])); writer.writeheader(); writer.writerows(candidates)
    summary = {"selected": selected, "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(), "thresholds": thresholds, "candidate_scorecards": candidates, "development_turns": len(turns), "development_solver_failures": len(failed)}
    (ROOT / "APTF_TEST_014_POLICY_DEVELOPMENT_SUMMARY_V0_1.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())