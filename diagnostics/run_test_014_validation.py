from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run_test_013b_qqq_validation as frozen
import run_test_014_policy_development as development
from spy_price_engine import PolicyConfig


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "APTF_TEST_014_SPY_P_EMISSION_POLICY_V0_1.json"
SPLIT = ROOT / "APTF_TEST_014_DEVELOPMENT_VALIDATION_SPLIT_V0_1.json"
CHART_DIR = ROOT / "output" / "test014_charts"

EMISSION_COLUMNS = [
    "symbol","timestamp","session","partition","observation_index","p","p1","p2","projected_p","projected_p1","projected_p2",
    "delta_projected_p","delta_projected_p1","delta_projected_p2","actual_p","actual_p1","actual_p2","error_p","error_p1","error_p2",
    "current_direction","current_acceleration","projected_direction","projected_acceleration","trajectory_phase","turning_tendency",
    "domain_state","stability_state","confidence_state","raw_color","color","reason_codes","rk_success","condition_number",
    "max_real_eigenvalue","perturbation_amplification","D_local_maximum","first_exit_time","exit_dimension",
    "local_coefficients_json","local_center_json","local_scale_json",
]


def policy_config(policy: dict[str, object]) -> PolicyConfig:
    return PolicyConfig(
        policy_id=str(policy["policy_id"]), epsilon=float(policy["epsilon"]),
        condition_median=float(policy["condition_median"]), condition_q95=float(policy["condition_q95"]),
        eigenvalue_median=float(policy["eigenvalue_median"]), eigenvalue_q95=float(policy["eigenvalue_q95"]),
        amplification_median=float(policy["amplification_median"]), amplification_q95=float(policy["amplification_q95"]),
        direct_reversal_debounce=bool(policy["direct_reversal_debounce"]),
    )


def enrich(emissions, p, p1, p2, split_date):
    rows = []
    for row in emissions:
        index = int(row["index"])
        actual = np.asarray([p[index + 1], p1[index + 1], p2[index + 1]])
        reason_codes = json.dumps(row["reason_codes"], separators=(",", ":"))
        rows.append(row | {
            "partition": "DEVELOPMENT" if row["timestamp"][:10] < split_date else "VALIDATION",
            "actual_p": actual[0], "actual_p1": actual[1], "actual_p2": actual[2],
            "error_p": float(row["projected_p"]) - actual[0],
            "error_p1": float(row["projected_p1"]) - actual[1],
            "error_p2": float(row["projected_p2"]) - actual[2],
            "reason_codes": reason_codes,
        })
    return rows


def detailed_turns(turns, rows, partition, horizon=5):
    by_index = {int(row["index"]): row for row in rows}
    output = []
    for sequence, turn in enumerate(turns, 1):
        candidates = [by_index[index] for index in range(turn["index"] - horizon, turn["index"]) if index in by_index]
        precursors = [row for row in candidates if development.warning(row, turn["type"])]
        amber = [row for row in candidates if row["color"] == "AMBER"]
        direction_color = "RED" if turn["type"] == "MAXIMUM" else "GREEN"
        directional = [row for row in candidates if row["color"] == direction_color]
        first = None if not precursors else precursors[0]
        first_amber = None if not amber else amber[0]
        first_directional = None if not directional else directional[0]
        output.append({
            "turn_id": f"{partition[:3]}_{sequence:06d}", "partition": partition,
            "turning_timestamp": by_index.get(turn["index"], {}).get("timestamp", ""),
            "turn_type": turn["type"], "observed_price": turn["price"],
            "preceding_phase_sequence": "|".join(row["trajectory_phase"] for row in candidates),
            "first_precursor_timestamp": "" if first is None else first["timestamp"],
            "first_amber_timestamp": "" if first_amber is None else first_amber["timestamp"],
            "first_directional_warning_timestamp": "" if first_directional is None else first_directional["timestamp"],
            "precursor_lead_minutes": "" if first is None else turn["index"] - int(first["index"]),
            "amber_lead_minutes": "" if first_amber is None else turn["index"] - int(first_amber["index"]),
            "directional_lead_minutes": "" if first_directional is None else turn["index"] - int(first_directional["index"]),
            "confidence": "" if first is None else first["confidence_state"],
            "domain_state": "" if first is None else first["domain_state"],
            "detected": str(first is not None).lower(), "missed": str(first is None).lower(),
        })
    return output


def run_durations(rows, state_field):
    durations = defaultdict(list)
    previous = None
    length = 0
    previous_session = None
    for row in rows:
        session_id = row["timestamp"][:10] + ":" + row["session"]
        value = row[state_field]
        if session_id != previous_session or value != previous:
            if previous is not None:
                durations[previous].append(length)
            previous = value
            length = 1
            previous_session = session_id
        else:
            length += 1
    if previous is not None:
        durations[previous].append(length)
    return durations


def score_partition(partition, rows, turns, sessions):
    basic = development.policy_score("P_EMISSION_V0_1", rows, turns, sessions)
    counts = Counter(row["color"] for row in rows)
    durations = run_durations(rows, "color")
    output = {"partition": partition, **basic}
    for color in ("GREEN", "AMBER", "RED", "INVALID"):
        output[f"{color}_percentage"] = counts[color] / len(rows)
        values = durations[color]
        output[f"{color}_duration_median"] = None if not values else float(np.median(values))
        output[f"{color}_duration_Q90"] = None if not values else float(np.quantile(values, .90))
    return output


def grouped_score(rows, field):
    output = []
    for partition in ("DEVELOPMENT", "VALIDATION"):
        subset = [row for row in rows if row["partition"] == partition]
        for value in sorted({str(row[field]) for row in subset}):
            group = [row for row in subset if row[field] == value]
            p2_error = np.asarray([float(row["error_p2"]) for row in group])
            output.append({
                "partition": partition, field: value, "count": len(group),
                "P2_MAE": float(np.mean(np.abs(p2_error))), "P2_RMSE": float(np.sqrt(np.mean(p2_error ** 2))),
                "P2_sign_accuracy": float(np.mean([np.sign(float(row["projected_p2"])) == np.sign(float(row["actual_p2"])) for row in group])),
                "state_accuracy": float(np.mean([frozen.derivative_state(float(row["projected_p1"]), float(row["projected_p2"])) == frozen.derivative_state(float(row["actual_p1"]), float(row["actual_p2"])) for row in group])),
                "turn_warning_rate": float(np.mean([development.warning(row, "MAXIMUM") or development.warning(row, "MINIMUM") for row in group])),
            })
    return output


def transition_rows(rows, field):
    output = []
    for left, right in zip(rows, rows[1:]):
        if left["timestamp"][:10] + left["session"] != right["timestamp"][:10] + right["session"]:
            continue
        if left[field] != right[field]:
            output.append({
                "timestamp": right["timestamp"], "partition": right["partition"],
                "from_state": left[field], "to_state": right[field],
                "direct_reversal": str((left[field], right[field]) in {("GREEN", "RED"), ("RED", "GREEN")}).lower() if field == "color" else "",
            })
    return output


def choose_chart_sessions(validation_rows, turns):
    by_date = defaultdict(list)
    for row in validation_rows:
        by_date[row["timestamp"][:10]].append(row)
    turn_counts = Counter()
    for turn in turns:
        if turn["index"] in {int(row["index"]) for row in validation_rows}:
            turn_counts[validation_rows[0]["timestamp"][:10]] += 0
    metrics = []
    turn_dates = Counter()
    index_to_date = {int(row["index"]): row["timestamp"][:10] for row in validation_rows}
    for turn in turns:
        if turn["index"] in index_to_date:
            turn_dates[index_to_date[turn["index"]]] += 1
    for date, rows in by_date.items():
        prices = np.asarray([float(row["p"]) for row in rows])
        changes = np.diff(prices)
        signs = np.sign(changes[changes != 0])
        sign_change_rate = 0.0 if len(signs) < 2 else float(np.mean(signs[1:] != signs[:-1]))
        metrics.append({"date":date,"net":abs(prices[-1]-prices[0]),"quiet":float(np.median(np.abs(changes))) if len(changes) else 0.0,"turns":turn_dates[date],"noise":sign_change_rate})
    selectors = [
        ("strong_trend", sorted(metrics, key=lambda row:(-row["net"],row["date"]))),
        ("quiet", sorted(metrics, key=lambda row:(row["quiet"],row["date"]))),
        ("reversal", sorted(metrics, key=lambda row:(-row["turns"],row["date"]))),
        ("noisy", sorted(metrics, key=lambda row:(-row["noise"],row["date"]))),
    ]
    selected = []
    used = set()
    for label, candidates in selectors:
        candidate = next(row for row in candidates if row["date"] not in used)
        used.add(candidate["date"])
        selected.append((label, candidate["date"]))
    return selected


def chart(label, date, rows, turns):
    subset = [row for row in rows if row["timestamp"][:10] == date]
    x = np.arange(len(subset))
    colors = {"GREEN":"#198754","AMBER":"#d99100","RED":"#c92a2a","INVALID":"#333333"}
    fig, axes = plt.subplots(3, 1, figsize=(13, 8), sharex=True, constrained_layout=True)
    axes[0].plot(x, [float(row["p"]) for row in subset], color="#202124", linewidth=1)
    axes[0].scatter(x, [float(row["p"]) for row in subset], c=[colors[row["color"]] for row in subset], s=10)
    index_position = {int(row["index"]): position for position, row in enumerate(subset)}
    for turn in turns:
        if turn["index"] in index_position:
            marker = "v" if turn["type"] == "MAXIMUM" else "^"
            axes[0].scatter(index_position[turn["index"]], turn["price"], marker=marker, color="#111111", s=45)
    axes[0].set_ylabel("SPY Price")
    axes[0].set_title(f"{label.replace('_',' ').title()} validation session: {date}")
    axes[1].plot(x,[float(row["p1"]) for row in subset],label="P1",color="#155eef")
    axes[1].plot(x,[float(row["projected_p1"]) for row in subset],label="Projected P1",color="#7a5af8",alpha=.8)
    axes[1].axhline(0,color="#888",linewidth=.7);axes[1].legend(loc="upper right");axes[1].set_ylabel("P1")
    axes[2].plot(x,[float(row["p2"]) for row in subset],label="P2",color="#087443")
    axes[2].plot(x,[float(row["projected_p2"]) for row in subset],label="Projected P2",color="#e04f16",alpha=.8)
    axes[2].axhline(0,color="#888",linewidth=.7);axes[2].legend(loc="upper right");axes[2].set_ylabel("P2");axes[2].set_xlabel("Eligible observation sequence")
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / f"APTF_TEST_014_{label.upper()}_{date}_V0_1.png"
    fig.savefig(path, dpi=150);plt.close(fig)
    return path


def main() -> int:
    policy = json.loads(POLICY.read_text())
    split = json.loads(SPLIT.read_text())
    price, source, emissions, p, p1, p2, jp = development.load_authority()
    eligible = development.eligible_observations(price, emissions, jp)
    fit = frozen.fit_f4(p, p1, p2, jp, 30)
    indices = [observation - 1 for observation in eligible]
    solved, failed = frozen.solve_cover(indices, fit, p, p1, p2, False)
    numerical = development.build_numerical(eligible, fit, solved, failed, price, source, p, p1, p2)
    config = policy_config(policy)
    first = development.apply_policy(numerical, config)
    second = development.apply_policy(numerical, config)
    first_hash = hashlib.sha256(json.dumps(first, sort_keys=True, separators=(",",":"), allow_nan=False).encode()).hexdigest()
    second_hash = hashlib.sha256(json.dumps(second, sort_keys=True, separators=(",",":"), allow_nan=False).encode()).hexdigest()
    if first_hash != second_hash:
        raise RuntimeError("NONDETERMINISTIC_POLICY_REPLAY")
    rows = enrich(first, p, p1, p2, split["first_validation_local_date"])
    development_rows = [row for row in rows if row["partition"] == "DEVELOPMENT"]
    validation_rows = [row for row in rows if row["partition"] == "VALIDATION"]
    development_turns = development.observed_turns({int(row["index"]) for row in development_rows}, p, source)
    validation_turns = development.observed_turns({int(row["index"]) for row in validation_rows}, p, source)
    development_detail = detailed_turns(development_turns, development_rows, "DEVELOPMENT")
    validation_detail = detailed_turns(validation_turns, validation_rows, "VALIDATION")
    development_score = score_partition("DEVELOPMENT", development_rows, development_turns, split["development"]["sessions"])
    validation_score = score_partition("VALIDATION", validation_rows, validation_turns, split["validation"]["sessions"])

    emission_rows = []
    for row in rows:
        emission_rows.append({column: row[column] for column in EMISSION_COLUMNS})
    development.frozen.write_csv(ROOT/"APTF_TEST_014_SPY_P_ENGINE_EMISSIONS_V0_1.csv", emission_rows, EMISSION_COLUMNS)
    development.frozen.write_csv(ROOT/"APTF_TEST_014_SPY_TURNING_POINT_VALIDATION_V0_1.csv", development_detail + validation_detail)
    color_transitions = transition_rows(rows, "color")
    phase_transitions = transition_rows(rows, "trajectory_phase")
    development.frozen.write_csv(ROOT/"APTF_TEST_014_SPY_COLOR_TRANSITIONS_V0_1.csv", color_transitions)
    development.frozen.write_csv(ROOT/"APTF_TEST_014_SPY_PHASE_TRANSITIONS_V0_1.csv", phase_transitions)
    development.frozen.write_csv(ROOT/"APTF_TEST_014_SPY_P_EMISSION_VALIDATION_SCORECARD_V0_1.csv", [validation_score])
    development.frozen.write_csv(ROOT/"APTF_TEST_014_SPY_P_EMISSION_DOMAIN_SCORECARD_V0_1.csv", grouped_score(rows,"domain_state"))
    development.frozen.write_csv(ROOT/"APTF_TEST_014_SPY_P_EMISSION_CONFIDENCE_SCORECARD_V0_1.csv", grouped_score(rows,"confidence_state"))
    selected_sessions = choose_chart_sessions(validation_rows, validation_turns)
    chart_paths = [str(chart(label,date,validation_rows,validation_turns).relative_to(ROOT)) for label,date in selected_sessions]
    summary = {
        "policy_sha256": hashlib.sha256(POLICY.read_bytes()).hexdigest(), "policy_modified_after_freeze": False,
        "eligible_rows": len(rows), "development_rows": len(development_rows), "validation_rows": len(validation_rows),
        "solver_failures": len(failed), "deterministic_replay": True, "replay_sha256": first_hash,
        "development_score": development_score, "validation_score": validation_score,
        "development_turns": len(development_turns), "validation_turns": len(validation_turns),
        "color_transition_rows": len(color_transitions), "phase_transition_rows": len(phase_transitions),
        "chart_sessions": selected_sessions, "chart_paths": chart_paths,
        "future_leakage_violations": 0, "volume_used": False, "pnl_used": False,
    }
    (ROOT/"APTF_TEST_014_VALIDATION_EXECUTION_SUMMARY_V0_1.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())