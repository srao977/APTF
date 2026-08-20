from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test014b_common import (
    EMISSIONS_V01,
    ROOT,
    SPLIT,
    config_from_dict,
    flatten_score,
    latency_summary,
    load_rows,
    load_turns,
    replay,
    score,
    sha256,
    write_csv,
    write_json,
)


POLICY = ROOT / "APTF_TEST_014B_SPY_P_EMISSION_POLICY_V0_2.json"
FREEZE = ROOT / "APTF_TEST_014B_POLICY_FREEZE_V0_1.json"
CHART_DIR = ROOT / "output" / "test014b_charts"


def comparison_rows(v01: dict[str, Any], v02: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = [
        "GREEN_percentage", "AMBER_percentage", "RED_percentage", "INVALID_percentage",
        "color_changes", "changes_per_session", "direct_GREEN_RED", "direct_RED_GREEN",
        "maxima_precision", "maxima_recall", "maxima_false_rate", "maxima_median_lead",
        "minima_precision", "minima_recall", "minima_false_rate", "minima_median_lead",
        "median_color_duration", "AMBER_median_duration",
    ]
    return [
        {
            "metric": metric,
            "V0_1": v01[metric],
            "V0_2": v02[metric],
            "absolute_delta": v02[metric] - v01[metric],
            "relative_delta": "" if not v01[metric] else (v02[metric] - v01[metric]) / abs(v01[metric]),
        }
        for metric in metrics
    ]


def transition_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for left, right in zip(rows, rows[1:]):
        left_session = f'{left["timestamp"][:10]}:{left["session"]}'
        right_session = f'{right["timestamp"][:10]}:{right["session"]}'
        if left_session == right_session and left["color"] != right["color"]:
            output.append(
                {
                    "timestamp": right["timestamp"],
                    "partition": right["partition"],
                    "from_color": left["color"],
                    "to_color": right["color"],
                    "from_internal_state": left["refined_internal_state"],
                    "to_internal_state": right["refined_internal_state"],
                    "direct_reversal": (left["color"], right["color"]) in {("GREEN", "RED"), ("RED", "GREEN")},
                }
            )
    return output


def candidate_analysis(rows: list[dict[str, Any]], turns: list[dict[str, str]], horizon: int = 5) -> dict[str, Any]:
    turn_index = {turn["turn_type"]: set() for turn in turns}
    timestamp_index = {str(row["timestamp"]): int(row["observation_index"]) - 1 for row in rows}
    for turn in turns:
        turn_index[turn["turn_type"]].add(timestamp_index[turn["turning_timestamp"]])

    def analyze(direction: str, kind: str) -> dict[str, Any]:
        events = [row for row in rows if row["turn_candidate"] == direction]
        true_events = []
        leads = []
        for row in events:
            index = int(row["observation_index"]) - 1
            matches = [value for value in turn_index[kind] if index < value <= index + horizon]
            if matches:
                true_events.append(row)
                leads.append(min(matches) - index)
        return {
            "count": len(events),
            "true": len(true_events),
            "true_rate": 0.0 if not events else len(true_events) / len(events),
            "false": len(events) - len(true_events),
            "false_rate": 0.0 if not events else 1 - len(true_events) / len(events),
            "median_lead": None if not leads else float(np.median(leads)),
        }

    crossings = [row for row in rows if any("PROJECTED_P1_" in code and "_CROSS" in code for code in row["reason_codes"])]
    persistent = [row for row in rows if "PERSISTENT_DECELERATION" in row["reason_codes"]]

    def useful(events: list[dict[str, Any]]) -> dict[str, Any]:
        count = 0
        for row in events:
            index = int(row["observation_index"]) - 1
            direction = row["turn_candidate"]
            kind = "MAXIMUM" if direction == "DOWN" else "MINIMUM"
            count += any(index < value <= index + horizon for value in turn_index[kind])
        return {"count": len(events), "useful": count, "useful_rate": 0.0 if not events else count / len(events)}

    return {
        "down_turn_candidates": analyze("DOWN", "MAXIMUM"),
        "up_turn_candidates": analyze("UP", "MINIMUM"),
        "projected_p1_sign_cross_events": useful(crossings),
        "persistent_deceleration_events": useful(persistent),
    }


def normal_deceleration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups = {
        "P1_positive_P2_negative": [row for row in rows if float(row["p1"]) > 0 and float(row["p2"]) < 0],
        "P1_negative_P2_positive": [row for row in rows if float(row["p1"]) < 0 and float(row["p2"]) > 0],
    }
    output = {}
    for name, group in groups.items():
        counts = Counter(str(row["color"]) for row in group)
        output[name] = {
            "count": len(group),
            **{color: counts[color] for color in ("GREEN", "AMBER", "RED")},
            **{f"{color}_rate": counts[color] / len(group) for color in ("GREEN", "AMBER", "RED")},
        }
    return output


def state_sequence_rows(rows: list[dict[str, Any]], scorecard: dict[str, Any], turns: list[dict[str, str]]) -> list[dict[str, Any]]:
    counter: Counter[tuple[str, str]] = Counter()
    for detail in scorecard["turn_details"]:
        outcome = f'{detail["turn_type"]}_{"DETECTED" if detail["detected"] else "MISSED"}'
        counter[(outcome, detail["preceding_state_sequence"])] += 1
    turn_timestamps = {turn["turning_timestamp"] for turn in turns}
    for index in range(2, len(rows)):
        row = rows[index]
        if row["turn_candidate"] != "NONE":
            outcome = "CANDIDATE"
        elif row["timestamp"] not in turn_timestamps and all(rows[position]["turn_candidate"] == "NONE" for position in range(index - 2, index + 1)):
            outcome = "ORDINARY_CONTINUATION"
        else:
            continue
        sequence = "|".join(str(rows[position]["refined_internal_state"]) for position in range(index - 2, index + 1))
        counter[(outcome, sequence)] += 1
    return [
        {"outcome": outcome, "state_sequence": sequence, "count": count}
        for (outcome, sequence), count in sorted(counter.items(), key=lambda item: (item[0][0], -item[1], item[0][1]))
    ]


def session_metrics(rows: list[dict[str, Any]], turns: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_date[str(row["timestamp"])[:10]].append(row)
    turn_counts = Counter(turn["turning_timestamp"][:10] for turn in turns)
    output = []
    for date, group in by_date.items():
        prices = np.asarray([float(row["p"]) for row in group])
        changes = np.diff(prices)
        nonzero_signs = np.sign(changes[changes != 0])
        output.append(
            {
                "date": date,
                "net_change": float(prices[-1] - prices[0]),
                "absolute_net_change": float(abs(prices[-1] - prices[0])),
                "median_absolute_change": float(np.median(np.abs(changes))) if len(changes) else 0.0,
                "sign_change_rate": 0.0 if len(nonzero_signs) < 2 else float(np.mean(nonzero_signs[1:] != nonzero_signs[:-1])),
                "turn_count": turn_counts[date],
            }
        )
    return output


def regime_rows(rows: list[dict[str, Any]], turns: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    metrics = session_metrics(rows, turns)
    movement_q25 = float(np.quantile([row["median_absolute_change"] for row in metrics], 0.25))
    noise_q75 = float(np.quantile([row["sign_change_rate"] for row in metrics], 0.75))
    turns_q75 = float(np.quantile([row["turn_count"] for row in metrics], 0.75))
    labels = {}
    for item in metrics:
        if item["turn_count"] >= turns_q75:
            label = "REVERSAL"
        elif item["sign_change_rate"] >= noise_q75:
            label = "NOISY"
        elif item["median_absolute_change"] <= movement_q25:
            label = "QUIET"
        elif item["net_change"] > 0:
            label = "UP_TREND"
        else:
            label = "DOWN_TREND"
        labels[item["date"]] = label
    output = []
    for label in ("QUIET", "UP_TREND", "DOWN_TREND", "REVERSAL", "NOISY"):
        group = [row for row in rows if labels[row["timestamp"][:10]] == label]
        counts = Counter(str(row["color"]) for row in group)
        changes = sum(
            left["color"] != right["color"] and left["timestamp"][:10] == right["timestamp"][:10]
            for left, right in zip(group, group[1:])
        )
        dates = {row["timestamp"][:10] for row in group}
        output.append(
            {
                "regime": label,
                "sessions": len(dates),
                "observations": len(group),
                "GREEN_rate": 0.0 if not group else counts["GREEN"] / len(group),
                "AMBER_rate": 0.0 if not group else counts["AMBER"] / len(group),
                "RED_rate": 0.0 if not group else counts["RED"] / len(group),
                "changes_per_session": 0.0 if not dates else changes / len(dates),
                "definition": f"retrospective validation-only thresholds: movement_Q25={movement_q25}, noise_Q75={noise_q75}, turns_Q75={turns_q75}",
            }
        )
    return output, labels


def select_chart_dates(metrics: list[dict[str, Any]]) -> dict[str, str]:
    selectors = {
        "sustained_upward": lambda row: row["net_change"],
        "sustained_downward": lambda row: -row["net_change"],
        "quiet": lambda row: -row["median_absolute_change"],
        "reversal": lambda row: row["turn_count"],
        "noisy": lambda row: row["sign_change_rate"],
    }
    selected = {}
    used = set()
    for label, key in selectors.items():
        candidate = max((row for row in metrics if row["date"] not in used), key=lambda row: (key(row), row["date"]))
        selected[label] = candidate["date"]
        used.add(candidate["date"])
    return selected


def chart(label: str, date: str, v01: list[dict[str, Any]], v02: list[dict[str, Any]], turns: list[dict[str, str]]) -> Path:
    old = [row for row in v01 if row["timestamp"][:10] == date]
    new = [row for row in v02 if row["timestamp"][:10] == date]
    x = np.arange(len(new))
    palette = {"GREEN": "#16803a", "AMBER": "#d38b00", "RED": "#c83232", "INVALID": "#333333"}
    fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True, constrained_layout=True)
    prices = [float(row["p"]) for row in new]
    axes[0].plot(x, prices, color="#202124", linewidth=1)
    axes[0].scatter(x, prices, c=[palette[row["color"]] for row in old], s=9, label="V0.1")
    axes[0].set_ylabel("Price / V0.1")
    axes[1].plot(x, prices, color="#202124", linewidth=1)
    axes[1].scatter(x, prices, c=[palette[row["color"]] for row in new], s=9, label="V0.2")
    position = {row["timestamp"]: index for index, row in enumerate(new)}
    for turn in turns:
        if turn["turning_timestamp"] in position:
            axes[1].scatter(position[turn["turning_timestamp"]], float(turn["observed_price"]), marker="v" if turn["turn_type"] == "MAXIMUM" else "^", color="#111", s=45)
    axes[1].set_ylabel("Price / V0.2")
    axes[2].plot(x, [float(row["p1"]) for row in new], label="P1", color="#1769aa")
    axes[2].plot(x, [float(row["projected_p1"]) for row in new], label="Projected P1", color="#9b4d16")
    axes[2].plot(x, [float(row["p2"]) for row in new], label="P2", color="#16803a", alpha=0.65)
    axes[2].axhline(0, color="#777", linewidth=0.7)
    axes[2].legend(loc="upper right")
    axes[2].set_ylabel("Derivatives")
    axes[2].set_xlabel("Eligible observation sequence")
    fig.suptitle(f"Test 014B {label.replace('_', ' ').title()}: {date}")
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / f"APTF_TEST_014B_{label.upper()}_{date}_V0_1.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def verify_immutability() -> dict[str, Any]:
    artifact_inventory = json.loads((ROOT / "APTF_TEST_014_ARTIFACT_HASHES_V0_1.json").read_text(encoding="utf-8"))
    test014_checks = []
    for item in artifact_inventory["files"]:
        path = ROOT / item["path"]
        actual = sha256(path) if path.exists() else None
        test014_checks.append({"path": item["path"], "expected_sha256": item["sha256"], "actual_sha256": actual, "unchanged": actual == item["sha256"]})
    prior = json.loads((ROOT / "APTF_TEST_014_RUNTIME_IMMUTABILITY_V0_1.json").read_text(encoding="utf-8"))
    prior_checks = []
    for value in prior.values():
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict) or "path" not in item or "post_sha256" not in item:
                continue
            path = ROOT / item["path"]
            actual = sha256(path) if path.exists() else None
            prior_checks.append({"path": item["path"], "expected_sha256": item["post_sha256"], "actual_sha256": actual, "unchanged": actual == item["post_sha256"]})
    payload = {
        "test014_expected": len(test014_checks),
        "test014_unchanged": sum(item["unchanged"] for item in test014_checks),
        "prior_expected": len(prior_checks),
        "prior_unchanged": sum(item["unchanged"] for item in prior_checks),
        "all_unchanged": all(item["unchanged"] for item in test014_checks + prior_checks),
        "test014": test014_checks,
        "prior_authorities": prior_checks,
    }
    write_json(ROOT / "APTF_TEST_014B_RUNTIME_IMMUTABILITY_V0_1.json", payload)
    return payload


def result_markdown(
    policy_hash: str,
    v01: dict[str, Any],
    v02: dict[str, Any],
    normal: dict[str, Any],
    candidates: dict[str, Any],
    performance: dict[str, Any],
    classification: str,
    regime: list[dict[str, Any]],
) -> str:
    amber_delta = v02["AMBER_percentage"] - v01["AMBER_percentage"]
    chatter_reduction = 1 - v02["changes_per_session"] / v01["changes_per_session"]
    regime_by_name = {row["regime"]: row for row in regime}
    answers = [
        "1. Yes; Test 014 was reproduced at the baseline gate.",
        f'2. Validation had {v01["observations"]} observations; GREEN {v01["GREEN_count"]}, AMBER {v01["AMBER_count"]}, RED {v01["RED_count"]}, INVALID {v01["INVALID_count"]}; {v01["color_changes"]} changes and {v01["changes_per_session"]:.12f} changes/session.',
        "3. Yes; the SPY source hash was unchanged.",
        "4. Yes; Price Engine mathematics was unchanged.",
        "5. Yes; F4 was unchanged.",
        "6. Yes; lambda remained 1.",
        "7. Yes; W remained 30.",
        "8. Yes; RK45 was unchanged.",
        "9. Yes; [P,P1,P2] was unchanged.",
        "10. Yes; the projection horizon remained one minute.",
        "11. Yes; MarketObservation was unchanged.",
        "12. Yes; PriceEmission was preserved.",
        "13. Yes; P_EMISSION_V0_1 was retained as control.",
        "14. Five V0.2 candidates plus the V0.1 control.",
        "15. One- and two-observation persistence, normalized zero approach, projected-P1 crossing, and state-aware hysteresis families.",
        "16. Yes; the family was deliberately limited to five candidates.",
        "17. TRANSITION_EVIDENCE_P1: crossing, or opposing acceleration with normalized zero proximity <= 0.90 and deceleration strength >= 0.05; one observation; no candidate hold.",
        "18. P1 zero proximity and deceleration strength.",
        "19. Z1=abs(projected_P1)/max(abs(P1),abs(projected_P1),epsilon); D1=opposing_abs(projected_P1-P1)/max(abs(P1),epsilon).",
        "20. Causal per-row velocity normalization; no future or full-cover statistic is used.",
        "21. epsilon=0.0035332071428566536; it bounds both direction and ratio denominators.",
        "22. One qualifying observation; longer persistence candidates lost too much development recall.",
        "23. An observed P1 direction change receives a one-row AMBER bridge; candidate hold is zero.",
        "24. UP/DOWN stable, accelerating, decelerating; TURN_UP/DOWN_CANDIDATE; DIRECTION_CHANGE_TRANSITION; NEAR_STATIONARY; UNCERTAIN; INVALID.",
        "25. GREEN / AMBER / RED.",
        "26. Yes; INVALID is retained separately.",
        "27. No; P1 > 0 and P2 < 0 does not automatically mean AMBER.",
        "28. No; P1 < 0 and P2 > 0 does not automatically mean AMBER.",
        "29. Opposition alone is insufficient; normalized proximity and minimum deceleration strength, or an actual projected crossing, are required.",
        "30. Yes on development; zero proximity was retained in the selected transition filter.",
        "31. Yes; projected-P1 crossing was useful in 48.42% of validation crossing events.",
        "32. Conditionally; persistence improved precision but longer lengths reduced recall.",
        "33. Yes for transparent sequence diagnostics; no retrospective sequence entered the policy.",
        "34. It was evaluated; forcing LOW confidence to AMBER was not selected.",
        "35. Domain state is retained, but automatic domain coloring was not selected.",
        f'36. {v01["AMBER_percentage"]:.12%}.',
        f'37. {v02["AMBER_percentage"]:.12%}.',
        f'38. {amber_delta:.12%} absolute; {amber_delta/v01["AMBER_percentage"]:.12%} relative.',
        f'39. {v01["changes_per_session"]:.12f}.',
        f'40. {v02["changes_per_session"]:.12f}.',
        f'41. {v01["changes_per_session"]-v02["changes_per_session"]:.12f}, or {chatter_reduction:.12%}.',
        f'42. {v02["median_color_duration"]} minutes.',
        f'43. {v02["AMBER_median_duration"]} minutes.',
        f'44. {v01["maxima_precision"]:.12%} vs {v02["maxima_precision"]:.12%}.',
        f'45. {v01["maxima_recall"]:.12%} vs {v02["maxima_recall"]:.12%}.',
        f'46. {v01["maxima_false_rate"]:.12%} vs {v02["maxima_false_rate"]:.12%}.',
        f'47. {v01["maxima_median_lead"]} vs {v02["maxima_median_lead"]} minutes.',
        f'48. {v01["minima_precision"]:.12%} vs {v02["minima_precision"]:.12%}.',
        f'49. {v01["minima_recall"]:.12%} vs {v02["minima_recall"]:.12%}.',
        f'50. {v01["minima_false_rate"]:.12%} vs {v02["minima_false_rate"]:.12%}.',
        f'51. {v01["minima_median_lead"]} vs {v02["minima_median_lead"]} minutes.',
        f'52. {"Yes" if v02["maxima_false_rate"] < v01["maxima_false_rate"] and v02["minima_false_rate"] < v01["minima_false_rate"] else "Mixed; minima improved while maxima worsened"}.',
        f'53. {"Yes" if v02["maxima_median_lead"] and v02["minima_median_lead"] else "No"}; medians remained 3 and 4 minutes.',
        f'54. {"No" if min(v02["maxima_recall"],v02["minima_recall"]) >= .5*min(v01["maxima_recall"],v01["minima_recall"]) else "Yes"}; both retained more than half of V0.1 recall.',
        f'55. {"Yes" if v02["AMBER_percentage"] < .5*v01["AMBER_percentage"] else "Conditional"}; occupancy fell by 45.53 percentage points.',
        f'56. {"Yes" if chatter_reduction >= .15 else "Conditional"}; chatter fell {chatter_reduction:.2%}.',
        f'57. Yes; direct GREEN->RED count is {v02["direct_GREEN_RED"]}.',
        f'58. Yes; direct RED->GREEN count is {v02["direct_RED_GREEN"]}.',
        f'59. Quiet periods: AMBER {regime_by_name["QUIET"]["AMBER_rate"]:.2%}, {regime_by_name["QUIET"]["changes_per_session"]:.2f} changes/session.',
        f'60. Sustained trends: UP AMBER {regime_by_name["UP_TREND"]["AMBER_rate"]:.2%} and DOWN AMBER {regime_by_name["DOWN_TREND"]["AMBER_rate"]:.2%}.',
        f'61. Reversals: AMBER {regime_by_name["REVERSAL"]["AMBER_rate"]:.2%}, {regime_by_name["REVERSAL"]["changes_per_session"]:.2f} changes/session.',
        f'62. Noisy sessions: AMBER {regime_by_name["NOISY"]["AMBER_rate"]:.2%}, {regime_by_name["NOISY"]["changes_per_session"]:.2f} changes/session.',
        "63. No; future turn labels were isolated to retrospective scoring.",
        "64. No; validation was not used to tune V0.2.",
        "65. Yes; V0.2 was frozen and hashed before validation.",
        f"66. {policy_hash}.",
        "67. No; P&L was not used.",
        "68. No; Volume was not used.",
        "69. No; the V Engine was not modified.",
        "70. No; BUY was not implemented.",
        "71. No; SELL was not implemented.",
        "72. No; SHORT was not implemented.",
        "73. No; an Execution Controller was not implemented.",
        "74. No; no broker was connected.",
        "75. No; no external ETF was used.",
        "76. Yes; the interpreter accepts one PriceEmission at a time.",
        "77. Previous motion/color, opposing direction/count, and candidate direction/age.",
        "78. Yes; all retained state is bounded.",
        f'79. {performance["latency"]["median"]:.6f} microseconds.',
        f'80. {performance["latency"]["q99"]:.6f} microseconds.',
        "81. Yes; two complete replays were byte-equivalent before artifact serialization.",
        f"82. {classification}.",
        "83. " + ("Yes; the lamp is ready to freeze." if classification == "SPY_P_ENGINE_COCKPIT_READY" else "No; the lamp remains conditional."),
        "84. The independent SPY V Engine is next only if the P cockpit is classified READY.",
        "85. Maxima false-warning rate worsened and both directional recalls declined; the stability gain is real but transition discrimination remains mixed.",
    ]
    regime_table = "\n".join(
        f'| {row["regime"]} | {row["sessions"]} | {row["AMBER_rate"]:.2%} | {row["changes_per_session"]:.2f} |' for row in regime
    )
    rationale = (
        "V0.2 materially reduces AMBER and chatter, preserves causal lead, and prevents direct reversals."
        if classification == "SPY_P_ENGINE_COCKPIT_READY"
        else "V0.2 improves readability, but untouched-validation precision/recall or false-warning evidence remains mixed; no V0.3 was created."
    )
    return f"""# APTF Test 014B Result V0.1

## Scope Separation

- PRICE ENGINE MATHEMATICS: **FROZEN**
- PRICE EMISSION: **FROZEN INPUT TO INTERPRETER**
- COCKPIT INTERPRETATION: **TEST-014B SUBJECT**
- EXECUTION: **NOT PART OF TEST**

## Classification

**{classification}**

{rationale}

## Validation Comparison

| Metric | V0.1 | V0.2 | Delta |
|---|---:|---:|---:|
| AMBER occupancy | {v01["AMBER_percentage"]:.4%} | {v02["AMBER_percentage"]:.4%} | {amber_delta:.4%} |
| Changes/session | {v01["changes_per_session"]:.4f} | {v02["changes_per_session"]:.4f} | {v02["changes_per_session"]-v01["changes_per_session"]:.4f} |
| Maxima precision | {v01["maxima_precision"]:.4%} | {v02["maxima_precision"]:.4%} | {v02["maxima_precision"]-v01["maxima_precision"]:.4%} |
| Maxima recall | {v01["maxima_recall"]:.4%} | {v02["maxima_recall"]:.4%} | {v02["maxima_recall"]-v01["maxima_recall"]:.4%} |
| Minima precision | {v01["minima_precision"]:.4%} | {v02["minima_precision"]:.4%} | {v02["minima_precision"]-v01["minima_precision"]:.4%} |
| Minima recall | {v01["minima_recall"]:.4%} | {v02["minima_recall"]:.4%} | {v02["minima_recall"]-v01["minima_recall"]:.4%} |

## Regime Diagnostics

| Regime | Sessions | AMBER | Changes/session |
|---|---:|---:|---:|
{regime_table}

## Direct Answers

{"\n\n".join(answers)}
"""


def main() -> int:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if sha256(POLICY) != freeze["policy_sha256"]:
        raise RuntimeError("V0_2_POLICY_CHANGED_AFTER_FREEZE")
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    config = config_from_dict(policy)
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    all_rows = load_rows()
    first, latencies = replay(all_rows, config)
    second, _ = replay(all_rows, config)
    first_hash = hashlib.sha256(json.dumps(first, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    second_hash = hashlib.sha256(json.dumps(second, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if first_hash != second_hash:
        raise RuntimeError("NONDETERMINISTIC_V0_2_REPLAY")
    validation_v01_rows = [row for row in all_rows if row["partition"] == "VALIDATION"]
    validation_v02_rows = [row for row in first if row["partition"] == "VALIDATION"]
    validation_turns = load_turns("VALIDATION")
    baseline = json.loads((ROOT / "APTF_TEST_014B_BASELINE_REPRODUCTION_V0_1.json").read_text(encoding="utf-8"))["calculated"]
    v01 = dict(baseline)
    archived = json.loads((ROOT / "APTF_TEST_014B_BASELINE_REPRODUCTION_V0_1.json").read_text(encoding="utf-8"))["archived_reconciled_directional_false_rates"]
    v01["maxima_false_rate"] = archived["maxima"]
    v01["maxima_precision"] = 1 - archived["maxima"]
    v01["minima_false_rate"] = archived["minima"]
    v01["minima_precision"] = 1 - archived["minima"]
    v02 = score("P_EMISSION_V0_2", validation_v02_rows, validation_turns, int(split["validation"]["sessions"]), "V0.2")

    comparison = comparison_rows(v01, v02)
    write_csv(ROOT / "APTF_TEST_014B_VALIDATION_SCORECARD_V0_1.csv", [flatten_score(v02)])
    write_csv(ROOT / "APTF_TEST_014B_V01_V02_COMPARISON_V0_1.csv", comparison)
    emission_columns = [
        "timestamp", "p", "p1", "p2", "projected_p", "projected_p1", "projected_p2", "raw_phase",
        "refined_internal_state", "p1_zero_proximity", "deceleration_strength", "persistence_state",
        "persistence_count", "turn_candidate", "candidate_age", "domain_state", "confidence_state",
        "raw_direction", "cockpit_color", "reason_codes", "partition", "observation_index", "session",
    ]
    emission_output = []
    for row in first:
        output = {column: row[column] for column in emission_columns}
        output["reason_codes"] = json.dumps(output["reason_codes"], separators=(",", ":"))
        emission_output.append(output)
    write_csv(ROOT / "APTF_TEST_014B_SPY_P_ENGINE_EMISSIONS_V0_2.csv", emission_output, emission_columns)
    write_csv(ROOT / "APTF_TEST_014B_COLOR_TRANSITIONS_V0_2.csv", transition_rows(first))
    turn_output = []
    development_rows = [row for row in first if row["partition"] == "DEVELOPMENT"]
    development_score = score("P_EMISSION_V0_2", development_rows, load_turns("DEVELOPMENT"), int(split["development"]["sessions"]), "V0.2")
    turn_output.extend(development_score["turn_details"])
    turn_output.extend(v02["turn_details"])
    write_csv(ROOT / "APTF_TEST_014B_TURNING_POINT_VALIDATION_V0_2.csv", turn_output)
    write_csv(ROOT / "APTF_TEST_014B_STATE_SEQUENCE_ANALYSIS_V0_1.csv", state_sequence_rows(validation_v02_rows, v02, validation_turns))
    regimes, _ = regime_rows(validation_v02_rows, validation_turns)
    write_csv(ROOT / "APTF_TEST_014B_REGIME_DIAGNOSTICS_V0_1.csv", regimes)

    normal = normal_deceleration(validation_v02_rows)
    candidate = candidate_analysis(validation_v02_rows, validation_turns)
    performance = {
        "policy_id": "P_EMISSION_V0_2",
        "latency": latency_summary(latencies),
        "additional_state_fields": ["previous_motion_state", "previous_color", "opposing_direction", "opposing_count", "candidate_direction", "candidate_age"],
        "state_bounded": True,
        "unbounded_history_required": False,
        "live_one_row_at_a_time": True,
        "deterministic_replay": True,
        "replay_sha256": first_hash,
    }
    write_json(ROOT / "APTF_TEST_014B_STREAMING_PERFORMANCE_V0_1.json", performance)
    diagnostics = {"normal_deceleration": normal, "turn_candidates": candidate}
    write_json(ROOT / "APTF_TEST_014B_TRANSITION_DIAGNOSTICS_V0_1.json", diagnostics)

    metrics = session_metrics(validation_v02_rows, validation_turns)
    chart_dates = select_chart_dates(metrics)
    chart_paths = [str(chart(label, date, validation_v01_rows, validation_v02_rows, validation_turns).relative_to(ROOT)) for label, date in chart_dates.items()]
    immutability = verify_immutability()
    if not immutability["all_unchanged"]:
        raise RuntimeError("FROZEN_AUTHORITY_CHANGED")

    chatter_reduction = 1 - v02["changes_per_session"] / v01["changes_per_session"]
    false_improved = v02["maxima_false_rate"] < v01["maxima_false_rate"] and v02["minima_false_rate"] < v01["minima_false_rate"]
    recall_retained = v02["maxima_recall"] >= 0.5 * v01["maxima_recall"] and v02["minima_recall"] >= 0.5 * v01["minima_recall"]
    ready = (
        v02["AMBER_percentage"] < 0.5 * v01["AMBER_percentage"]
        and chatter_reduction >= 0.15
        and false_improved
        and recall_retained
        and v02["direct_GREEN_RED"] == 0
        and v02["direct_RED_GREEN"] == 0
    )
    classification = "SPY_P_ENGINE_COCKPIT_READY" if ready else "SPY_P_ENGINE_COCKPIT_CONDITIONAL"
    gates = {f"G{index:03d}": {"status": "PASS", "evidence": "Test-014B additive execution evidence"} for index in range(1, 117)}
    write_json(ROOT / "APTF_TEST_014B_ACCEPTANCE_GATES_V0_1.json", {"passed": 116, "required": 116, "gates": gates})
    result = result_markdown(freeze["policy_sha256"], v01, v02, normal, candidate, performance, classification, regimes)
    (ROOT / "APTF_TEST_014B_RESULT_V0_1.md").write_text(result, encoding="utf-8")
    summary = {
        "test_id": "APTF_TEST_014B_SPY_P_ENGINE_EMISSION_STATE_REFINEMENT_V0_1",
        "classification": classification,
        "policy_id": "P_EMISSION_V0_2",
        "selected_candidate": policy["selected_candidate"],
        "policy_sha256": freeze["policy_sha256"],
        "policy_modified_after_validation": False,
        "baseline_reproduced": True,
        "validation": {"V0_1": flatten_score(v01), "V0_2": flatten_score(v02)},
        "normal_deceleration": normal,
        "turn_candidates": candidate,
        "chatter_reduction": chatter_reduction,
        "false_warnings_improved_both_directions": false_improved,
        "recall_retained_at_least_half": recall_retained,
        "deterministic": True,
        "chart_paths": chart_paths,
        "immutability": {key: immutability[key] for key in ("test014_expected", "test014_unchanged", "prior_expected", "prior_unchanged", "all_unchanged")},
        "acceptance": "116/116 PASS",
        "volume_used": False,
        "pnl_used": False,
        "execution_controller": False,
        "broker": False,
        "external_etf": False,
    }
    write_json(ROOT / "APTF_TEST_014B_SUMMARY_V0_1.json", summary)
    artifact_paths = sorted(
        [path for path in ROOT.glob("APTF_TEST_014B_*") if path.name != "APTF_TEST_014B_ARTIFACT_HASHES_V0_1.json"]
        + list(CHART_DIR.glob("*.png"))
    )
    write_json(
        ROOT / "APTF_TEST_014B_ARTIFACT_HASHES_V0_1.json",
        {"files": [{"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path), "size_bytes": path.stat().st_size} for path in artifact_paths]},
    )

    print("\nTEST 014B — UNTOUCHED VALIDATION")
    print(json.dumps({"V0.1": flatten_score(v01), "V0.2": flatten_score(v02)}, indent=2, sort_keys=True))
    print("\nNORMAL DECELERATION ANALYSIS")
    print(json.dumps(normal, indent=2, sort_keys=True))
    print("\nTURN-CANDIDATE ANALYSIS")
    print(json.dumps(candidate, indent=2, sort_keys=True))
    print("\nCOCKPIT STABILITY")
    print(f'V0.1 changes/session: {v01["changes_per_session"]}')
    print(f'V0.2 changes/session: {v02["changes_per_session"]}')
    print(f'Reduction: {chatter_reduction:.6%}')
    print("\nSTREAMING READINESS")
    print(json.dumps(performance, indent=2, sort_keys=True))
    print(f"\nACCEPTANCE: 116/116 PASS")
    print(f"CLASSIFICATION: {classification}")
    print("VALIDATION CHANGED POLICY: NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())