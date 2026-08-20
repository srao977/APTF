from __future__ import annotations

import bisect
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv"
EPISODES = ROOT / "APTF_TEST_007_POSITION_EPISODES_V0_1.csv"
TRADES = ROOT / "APTF_TEST_008_TRADE_LEDGER_V0_2.csv"
WINDOWS = (3, 5, 8, 15)
ACTIONABLE_START = 15

OBSERVATION_COLUMNS = [
    "source_observation_index", "source_physical_row", "timestamp",
    "initialization_status", "price_field", "price", "raw_D1",
    "D1_window_3", "D2_window_3", "D1_window_5", "D2_window_5",
    "D1_window_8", "D2_window_8", "D1_window_15", "D2_window_15",
    "primary_window", "primary_D1", "primary_D2", "D1_sign", "D2_sign",
    "derivative_state", "emitter_decision", "position_state_before",
    "position_state_after", "execution_intent", "episode_id", "H", "Q_G",
    "Q_S", "Q_R", "C",
]

CROSSING_COLUMNS = [
    "crossing_id", "crossing_type", "observation_index", "source_physical_row",
    "timestamp", "price", "D1_previous", "D1_current", "D2_current",
    "precursor_state", "precursor_length_observations", "precursor_elapsed_seconds",
    "nearest_emitter_decision", "nearest_position_transition",
]

PRECURSOR_COLUMNS = [
    "crossing_id", "crossing_type", "minimum_sustained_observations",
    "observed_contiguous_precursor_observations", "qualifies",
    "precursor_start_observation", "precursor_start_timestamp",
    "crossing_observation", "crossing_timestamp", "lead_observations",
    "lead_seconds", "D1_start", "D1_end_before_crossing", "D2_start",
    "D2_end_before_crossing",
]

TRAJECTORY_COLUMNS = [
    "transition_id", "transition_type", "crossing_observation_index",
    "crossing_timestamp", "relative_observation", "relative_seconds",
    "normalized_price", "primary_D1", "primary_D2", "H", "Q_G", "Q_S",
    "Q_R", "C", "emitter_decision", "position_state",
]

ALIGNMENT_COLUMNS = [
    "episode_id", "buy_observation", "buy_timestamp", "buy_price", "buy_D1",
    "buy_D2", "buy_derivative_state", "associated_lower_crossing",
    "buy_offset_observations", "buy_offset_seconds",
    "weakening_decline_precursor_start_observation",
    "weakening_decline_precursor_start_timestamp", "precursor_to_buy_observations",
    "precursor_to_buy_seconds", "hold_derivative_state_mode",
    "sell_observation", "sell_timestamp", "sell_price", "sell_D1", "sell_D2",
    "sell_derivative_state", "associated_upper_crossing",
    "sell_offset_observations", "sell_offset_seconds",
    "weakening_rise_precursor_start_observation",
    "weakening_rise_precursor_start_timestamp", "precursor_to_sell_observations",
    "precursor_to_sell_seconds", "retrospective_max_close_while_long",
    "retrospective_max_close_observation", "retrospective_min_close_next_15_after_sell",
    "retrospective_min_close_observation", "test008_gross_pnl",
    "test008_result_classification",
]

EMITTER_TRAJECTORY_COLUMNS = [
    "transition_id", "transition_type", "episode_id", "signal_observation_index",
    "signal_timestamp", "relative_observation", "relative_seconds", "timestamp",
    "price", "normalized_price", "primary_D1", "primary_D2", "H", "Q_G",
    "Q_S", "Q_R", "C", "emitter_decision", "position_state",
]


def timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def text(value: float | None) -> str:
    return "" if value is None or not math.isfinite(value) else repr(float(value))


def quantile(values: np.ndarray, probability: float) -> float:
    return float(np.quantile(values, probability, method="linear"))


def run_lengths(values: list[int]) -> list[int]:
    result: list[int] = []
    current: int | None = None
    length = 0
    for value in values:
        if value == 0:
            if length:
                result.append(length)
            current = None
            length = 0
        elif value == current:
            length += 1
        else:
            if length:
                result.append(length)
            current = value
            length = 1
    if length:
        result.append(length)
    return result


def causal_quadratic(
    times_minutes: np.ndarray, prices: np.ndarray, window: int
) -> tuple[np.ndarray, np.ndarray, int]:
    size = len(prices)
    d1 = np.full(size, np.nan)
    d2 = np.full(size, np.nan)
    failures = 0
    for index in range(window - 1, size):
        x = times_minutes[index - window + 1 : index + 1] - times_minutes[index]
        y = prices[index - window + 1 : index + 1]
        design = np.column_stack((x * x, x, np.ones(window)))
        try:
            coefficients, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
        except np.linalg.LinAlgError:
            failures += 1
            continue
        if rank != 3 or not np.all(np.isfinite(coefficients)):
            failures += 1
            continue
        d1[index] = coefficients[1]
        d2[index] = 2.0 * coefficients[0]
    return d1, d2, failures


def window_metrics(
    d1: np.ndarray, d2: np.ndarray, failures: int, actionable_start: int
) -> dict[str, Any]:
    valid = np.isfinite(d1) & np.isfinite(d2)
    scored = valid.copy()
    scored[:actionable_start] = False
    indices = np.flatnonzero(scored)
    d1_signs = [sign(d1[index]) for index in indices]
    d2_signs = [sign(d2[index]) for index in indices]
    d1_runs = run_lengths(d1_signs)
    d2_runs = run_lengths(d2_signs)
    crossings = 0
    d2_changes = 0
    for index in indices:
        if index == 0 or not valid[index - 1]:
            continue
        previous_d1 = d1[index - 1]
        current_d1 = d1[index]
        crossings += (previous_d1 < 0 <= current_d1) or (previous_d1 > 0 >= current_d1)
        d2_changes += sign(d2[index - 1]) != sign(d2[index])
    single = sum(length == 1 for length in d1_runs)
    return {
        "valid_observations": int(scored.sum()),
        "D1_zero_crossings": int(crossings),
        "D2_sign_changes": int(d2_changes),
        "single_observation_D1_reversal_runs": single,
        "single_observation_D1_reversal_percentage": (
            0.0 if not d1_runs else 100.0 * single / len(d1_runs)
        ),
        "median_D1_state_persistence": (
            None if not d1_runs else float(statistics.median(d1_runs))
        ),
        "median_D2_state_persistence": (
            None if not d2_runs else float(statistics.median(d2_runs))
        ),
        "D2_sign_change_rate": 0.0 if len(indices) < 2 else d2_changes / (len(indices) - 1),
        "numerical_fit_failures": failures,
    }


def select_primary(metrics: dict[int, dict[str, Any]]) -> int:
    return min(
        WINDOWS,
        key=lambda window: (
            -metrics[window]["valid_observations"],
            metrics[window]["single_observation_D1_reversal_percentage"],
            metrics[window]["D2_sign_change_rate"],
            -metrics[window]["median_D1_state_persistence"],
            window,
        ),
    )


def derivative_state(d1: float, d2: float, epsilon: float) -> str:
    if not math.isfinite(d1) or not math.isfinite(d2):
        return "UNAVAILABLE"
    if abs(d1) <= epsilon:
        return "LOWER_TURNING_REGION" if d2 > 0 else "UPPER_TURNING_REGION" if d2 < 0 else "D2_ZERO"
    if d1 > 0:
        return "RISING_STRENGTHENING" if d2 > 0 else "RISING_WEAKENING" if d2 < 0 else "D2_ZERO"
    return "FALLING_WEAKENING" if d2 > 0 else "FALLING_STRENGTHENING" if d2 < 0 else "D2_ZERO"


def execution_intent(classification: str) -> str:
    return "BUY" if classification == "EPISODE_OPEN" else "SELL" if classification == "EPISODE_CLOSE" else "NONE"


def contiguous_precursor(
    crossing_index: int,
    d1: np.ndarray,
    d2: np.ndarray,
    predicate: Callable[[float, float], bool],
) -> tuple[int | None, int]:
    end = crossing_index - 1
    if end < 0 or not predicate(d1[end], d2[end]):
        return None, 0
    start = end
    while start - 1 >= 0 and predicate(d1[start - 1], d2[start - 1]):
        start -= 1
    return start, end - start + 1


def latest_state_run(
    states: list[str], start: int, end: int, target: str
) -> int | None:
    latest_end = None
    for index in range(max(0, start), min(len(states) - 1, end) + 1):
        if states[index] == target:
            latest_end = index
    if latest_end is None:
        return None
    run_start = latest_end
    while run_start - 1 >= start and states[run_start - 1] == target:
        run_start -= 1
    return run_start


def numeric_summary(values: list[float]) -> dict[str, float | int | None]:
    finite = np.asarray([value for value in values if math.isfinite(value)], dtype=float)
    if not len(finite):
        return {"count": 0, "mean": None, "median": None, "minimum": None, "maximum": None}
    return {
        "count": int(len(finite)),
        "mean": float(np.mean(finite)),
        "median": float(np.median(finite)),
        "minimum": float(np.min(finite)),
        "maximum": float(np.max(finite)),
    }


def main() -> int:
    # Phase 1: derivatives and mathematical selection. Test 008 P&L is not opened here.
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 101221:
        raise RuntimeError("source row authority changed")
    if [row["position_decision"] for row in rows[:15]] != ["INITIALIZING"] * 15:
        raise RuntimeError("initialization authority changed")
    if any(row["position_decision"] == "INITIALIZING" for row in rows[15:]):
        raise RuntimeError("non-leading initialization row")

    datetimes = [timestamp(row["event_timestamp_utc"]) for row in rows]
    seconds = np.asarray([value.timestamp() for value in datetimes], dtype=float)
    if np.any(np.diff(seconds) <= 0):
        raise RuntimeError("source timestamps are not strictly increasing")
    times_minutes = seconds / 60.0
    prices = np.asarray([float(row["close"]) for row in rows], dtype=float)
    raw_d1 = np.full(len(rows), np.nan)
    raw_d1[1:] = np.diff(prices) / np.diff(times_minutes)

    derivatives: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    comparisons: dict[int, dict[str, Any]] = {}
    for window in WINDOWS:
        d1, d2, failures = causal_quadratic(times_minutes, prices, window)
        derivatives[window] = (d1, d2)
        comparisons[window] = window_metrics(d1, d2, failures, ACTIONABLE_START)
    primary_window = select_primary(comparisons)
    primary_d1, primary_d2 = derivatives[primary_window]
    actionable_d1 = primary_d1[ACTIONABLE_START:]
    actionable_d1 = actionable_d1[np.isfinite(actionable_d1)]
    absolute_d1 = np.abs(actionable_d1)
    epsilon_sensitivity = {
        "q05": quantile(absolute_d1, 0.05),
        "q10_primary": quantile(absolute_d1, 0.10),
        "q15": quantile(absolute_d1, 0.15),
    }
    epsilon = epsilon_sensitivity["q10_primary"]
    distribution_probabilities = (0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
    d1_distribution = {
        "count": int(len(actionable_d1)),
        "minimum": float(np.min(actionable_d1)),
        "maximum": float(np.max(actionable_d1)),
        "mean": float(np.mean(actionable_d1)),
        "median": float(np.median(actionable_d1)),
        "population_standard_deviation": float(np.std(actionable_d1)),
        "quantiles": {str(p): quantile(actionable_d1, p) for p in distribution_probabilities},
        "absolute_quantiles": {str(p): quantile(absolute_d1, p) for p in distribution_probabilities},
    }
    states = [derivative_state(primary_d1[index], primary_d2[index], epsilon) for index in range(len(rows))]

    comparison_path = ROOT / "APTF_TEST_009_DERIVATIVE_WINDOW_COMPARISON_V0_1.csv"
    with comparison_path.open("w", newline="", encoding="utf-8") as handle:
        columns = ["window", *next(iter(comparisons.values())).keys()]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for window in WINDOWS:
            writer.writerow({"window": window, **comparisons[window]})

    selection = ROOT / "APTF_TEST_009_DERIVATIVE_WINDOW_SELECTION_V0_1.md"
    selection.write_text(
        "# APTF Test 009 Derivative Window Selection V0.1\n\n"
        f"Primary window: **{primary_window} observations**.\n\n"
        "Selection was performed before opening Test 008 P&L and without Emitter labels. "
        "The predeclared lexicographic rule maximized valid fits, minimized single-observation "
        "D1 reversal-run percentage, minimized D2 sign-change rate, maximized median D1 "
        "persistence, and used smaller-window responsiveness only as a final tie-break.\n\n"
        + "\n".join(
            f"- Window {window}: valid={comparisons[window]['valid_observations']}, "
            f"D1 crossings={comparisons[window]['D1_zero_crossings']}, "
            f"single-reversal={comparisons[window]['single_observation_D1_reversal_percentage']}%, "
            f"D2 change rate={comparisons[window]['D2_sign_change_rate']}, "
            f"median D1 persistence={comparisons[window]['median_D1_state_persistence']}."
            for window in WINDOWS
        )
        + f"\n\nPrimary near-zero threshold: empirical Q10(|D1|) = `{epsilon}`. "
        f"Sensitivity values: Q05 `{epsilon_sensitivity['q05']}`, Q15 `{epsilon_sensitivity['q15']}`.\n\n"
        "P&L used for selection: **NO**.\n",
        encoding="utf-8",
    )

    observation_path = ROOT / "APTF_TEST_009_DERIVATIVE_OBSERVATIONS_V0_1.csv"
    with observation_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OBSERVATION_COLUMNS)
        writer.writeheader()
        for index, row in enumerate(rows):
            writer.writerow({
                "source_observation_index": row["test006b_observation_index"],
                "source_physical_row": row["source_physical_row"],
                "timestamp": row["event_timestamp_utc"],
                "initialization_status": "INITIALIZING_CONTEXT_ONLY" if index < 15 else "ACTIONABLE",
                "price_field": "close",
                "price": row["close"],
                "raw_D1": text(raw_d1[index]),
                **{
                    f"D{order}_window_{window}": text(derivatives[window][order - 1][index])
                    for window in WINDOWS for order in (1, 2)
                },
                "primary_window": primary_window,
                "primary_D1": text(primary_d1[index]),
                "primary_D2": text(primary_d2[index]),
                "D1_sign": "" if not math.isfinite(primary_d1[index]) else sign(primary_d1[index]),
                "D2_sign": "" if not math.isfinite(primary_d2[index]) else sign(primary_d2[index]),
                "derivative_state": states[index],
                "emitter_decision": row["position_decision"],
                "position_state_before": row["test007_position_state_before"],
                "position_state_after": row["test007_position_state_after"],
                "execution_intent": execution_intent(row["test007_structural_classification"]),
                "episode_id": row["test007_episode_id"],
                "H": row["H"], "Q_G": row["Q_G"], "Q_S": row["Q_S"],
                "Q_R": row["Q_R"], "C": row["C"],
            })

    crossings: list[dict[str, Any]] = []
    precursor_rows: list[dict[str, Any]] = []
    for index in range(ACTIONABLE_START, len(rows)):
        if not (math.isfinite(primary_d1[index - 1]) and math.isfinite(primary_d1[index])):
            continue
        crossing_type = None
        if primary_d1[index - 1] < 0 <= primary_d1[index]:
            crossing_type = "LOWER"
            predicate = lambda first, second: first < 0 and second > 0
            precursor_state = "FALLING_WEAKENING"
        elif primary_d1[index - 1] > 0 >= primary_d1[index]:
            crossing_type = "UPPER"
            predicate = lambda first, second: first > 0 and second < 0
            precursor_state = "RISING_WEAKENING"
        if crossing_type is None:
            continue
        crossing_id = f"CR{len(crossings) + 1:06d}"
        start, length = contiguous_precursor(index, primary_d1, primary_d2, predicate)
        elapsed = None if start is None else (seconds[index] - seconds[start])
        crossing = {
            "crossing_id": crossing_id,
            "crossing_type": crossing_type,
            "observation_index": int(rows[index]["test006b_observation_index"]),
            "source_physical_row": int(rows[index]["source_physical_row"]),
            "timestamp": rows[index]["event_timestamp_utc"],
            "price": rows[index]["close"],
            "D1_previous": primary_d1[index - 1],
            "D1_current": primary_d1[index],
            "D2_current": primary_d2[index],
            "precursor_state": precursor_state if length else "NONE",
            "precursor_length_observations": length,
            "precursor_elapsed_seconds": elapsed,
            "nearest_emitter_decision": rows[index]["position_decision"],
            "nearest_position_transition": rows[index]["test007_structural_classification"],
            "zero_based_index": index,
            "precursor_start_index": start,
        }
        crossings.append(crossing)
        for threshold in (1, 2, 3):
            qualifies = length >= threshold
            precursor_rows.append({
                "crossing_id": crossing_id,
                "crossing_type": crossing_type,
                "minimum_sustained_observations": threshold,
                "observed_contiguous_precursor_observations": length,
                "qualifies": str(qualifies).lower(),
                "precursor_start_observation": "" if start is None else rows[start]["test006b_observation_index"],
                "precursor_start_timestamp": "" if start is None else rows[start]["event_timestamp_utc"],
                "crossing_observation": rows[index]["test006b_observation_index"],
                "crossing_timestamp": rows[index]["event_timestamp_utc"],
                "lead_observations": "" if not qualifies else index - start,
                "lead_seconds": "" if not qualifies else seconds[index] - seconds[start],
                "D1_start": "" if start is None else primary_d1[start],
                "D1_end_before_crossing": "" if not length else primary_d1[index - 1],
                "D2_start": "" if start is None else primary_d2[start],
                "D2_end_before_crossing": "" if not length else primary_d2[index - 1],
            })

    with (ROOT / "APTF_TEST_009_DERIVATIVE_CROSSINGS_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CROSSING_COLUMNS)
        writer.writeheader()
        for crossing in crossings:
            writer.writerow({key: crossing[key] for key in CROSSING_COLUMNS})
    with (ROOT / "APTF_TEST_009_D2_PRECURSOR_ANALYSIS_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PRECURSOR_COLUMNS)
        writer.writeheader()
        writer.writerows(precursor_rows)

    with (ROOT / "APTF_TEST_009_TURNING_TRAJECTORIES_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRAJECTORY_COLUMNS)
        writer.writeheader()
        for crossing in crossings:
            center = crossing["zero_based_index"]
            center_price = prices[center]
            for relative in range(-15, 16):
                index = center + relative
                if not 0 <= index < len(rows):
                    continue
                row = rows[index]
                writer.writerow({
                    "transition_id": crossing["crossing_id"],
                    "transition_type": crossing["crossing_type"],
                    "crossing_observation_index": crossing["observation_index"],
                    "crossing_timestamp": crossing["timestamp"],
                    "relative_observation": relative,
                    "relative_seconds": seconds[index] - seconds[center],
                    "normalized_price": prices[index] / center_price - 1.0,
                    "primary_D1": text(primary_d1[index]),
                    "primary_D2": text(primary_d2[index]),
                    "H": row["H"], "Q_G": row["Q_G"], "Q_S": row["Q_S"],
                    "Q_R": row["Q_R"], "C": row["C"],
                    "emitter_decision": row["position_decision"],
                    "position_state": row["test007_position_state_after"],
                })

    # Phase 2: derivative definitions are fixed. Open immutable episode and P&L evidence descriptively.
    episode_rows = list(csv.DictReader(EPISODES.open(newline="", encoding="utf-8")))
    trade_by_episode = {
        row["episode_id"]: row for row in csv.DictReader(TRADES.open(newline="", encoding="utf-8"))
    }
    lower_crossings = [item for item in crossings if item["crossing_type"] == "LOWER"]
    upper_crossings = [item for item in crossings if item["crossing_type"] == "UPPER"]
    lower_indices = [item["zero_based_index"] for item in lower_crossings]
    upper_indices = [item["zero_based_index"] for item in upper_crossings]
    alignments: list[dict[str, Any]] = []
    for episode in episode_rows:
        buy = int(episode["buy_observation_index"]) - 1
        sell = int(episode["sell_observation_index"]) - 1
        lower_position = bisect.bisect_right(lower_indices, buy) - 1
        lower = None if lower_position < 0 else lower_crossings[lower_position]
        upper_position = bisect.bisect_left(upper_indices, sell)
        candidates = []
        if upper_position < len(upper_crossings):
            candidates.append(upper_crossings[upper_position])
        if upper_position > 0:
            candidates.append(upper_crossings[upper_position - 1])
        upper = None if not candidates else min(candidates, key=lambda item: (abs(item["zero_based_index"] - sell), item["zero_based_index"]))
        buy_precursor = None if lower is None else lower["precursor_start_index"]
        sell_precursor = latest_state_run(states, buy, sell, "RISING_WEAKENING")
        hold_states = [states[index] for index in range(buy + 1, sell) if rows[index]["position_decision"] == "HOLD"]
        hold_mode = "" if not hold_states else Counter(hold_states).most_common(1)[0][0]
        max_index = max(range(buy, sell + 1), key=lambda index: prices[index])
        post_indices = list(range(sell + 1, min(len(rows), sell + 16)))
        min_index = None if not post_indices else min(post_indices, key=lambda index: prices[index])
        trade = trade_by_episode[episode["episode_id"]]
        alignments.append({
            "episode_id": episode["episode_id"],
            "buy_observation": buy + 1,
            "buy_timestamp": rows[buy]["event_timestamp_utc"],
            "buy_price": rows[buy]["close"],
            "buy_D1": primary_d1[buy], "buy_D2": primary_d2[buy],
            "buy_derivative_state": states[buy],
            "associated_lower_crossing": "" if lower is None else lower["crossing_id"],
            "buy_offset_observations": "" if lower is None else buy - lower["zero_based_index"],
            "buy_offset_seconds": "" if lower is None else seconds[buy] - seconds[lower["zero_based_index"]],
            "weakening_decline_precursor_start_observation": "" if buy_precursor is None else buy_precursor + 1,
            "weakening_decline_precursor_start_timestamp": "" if buy_precursor is None else rows[buy_precursor]["event_timestamp_utc"],
            "precursor_to_buy_observations": "" if buy_precursor is None else buy - buy_precursor,
            "precursor_to_buy_seconds": "" if buy_precursor is None else seconds[buy] - seconds[buy_precursor],
            "hold_derivative_state_mode": hold_mode,
            "sell_observation": sell + 1,
            "sell_timestamp": rows[sell]["event_timestamp_utc"],
            "sell_price": rows[sell]["close"],
            "sell_D1": primary_d1[sell], "sell_D2": primary_d2[sell],
            "sell_derivative_state": states[sell],
            "associated_upper_crossing": "" if upper is None else upper["crossing_id"],
            "sell_offset_observations": "" if upper is None else sell - upper["zero_based_index"],
            "sell_offset_seconds": "" if upper is None else seconds[sell] - seconds[upper["zero_based_index"]],
            "weakening_rise_precursor_start_observation": "" if sell_precursor is None else sell_precursor + 1,
            "weakening_rise_precursor_start_timestamp": "" if sell_precursor is None else rows[sell_precursor]["event_timestamp_utc"],
            "precursor_to_sell_observations": "" if sell_precursor is None else sell - sell_precursor,
            "precursor_to_sell_seconds": "" if sell_precursor is None else seconds[sell] - seconds[sell_precursor],
            "retrospective_max_close_while_long": prices[max_index],
            "retrospective_max_close_observation": max_index + 1,
            "retrospective_min_close_next_15_after_sell": "" if min_index is None else prices[min_index],
            "retrospective_min_close_observation": "" if min_index is None else min_index + 1,
            "test008_gross_pnl": trade["gross_pnl"],
            "test008_result_classification": trade["result_classification"],
        })
    with (ROOT / "APTF_TEST_009_EPISODE_DERIVATIVE_ALIGNMENT_V0_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ALIGNMENT_COLUMNS)
        writer.writeheader()
        writer.writerows(alignments)

    with (ROOT / "APTF_TEST_009_EMITTER_TRANSITION_TRAJECTORIES_V0_1.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=EMITTER_TRAJECTORY_COLUMNS)
        writer.writeheader()
        for episode in episode_rows:
            for transition_type, signal in (
                ("BUY", int(episode["buy_observation_index"]) - 1),
                ("SELL", int(episode["sell_observation_index"]) - 1),
            ):
                signal_price = prices[signal]
                for relative in range(-15, 1):
                    index = signal + relative
                    if index < 0:
                        continue
                    row = rows[index]
                    writer.writerow({
                        "transition_id": f"{transition_type}_{episode['episode_id']}",
                        "transition_type": transition_type,
                        "episode_id": episode["episode_id"],
                        "signal_observation_index": signal + 1,
                        "signal_timestamp": rows[signal]["event_timestamp_utc"],
                        "relative_observation": relative,
                        "relative_seconds": seconds[index] - seconds[signal],
                        "timestamp": row["event_timestamp_utc"],
                        "price": row["close"],
                        "normalized_price": prices[index] / signal_price - 1.0,
                        "primary_D1": text(primary_d1[index]),
                        "primary_D2": text(primary_d2[index]),
                        "H": row["H"], "Q_G": row["Q_G"], "Q_S": row["Q_S"],
                        "Q_R": row["Q_R"], "C": row["C"],
                        "emitter_decision": row["position_decision"],
                        "position_state": row["test007_position_state_after"],
                    })

    crossing_types = [item["crossing_type"] for item in crossings]
    upward_cycles = sum(left == "LOWER" and right == "UPPER" for left, right in zip(crossing_types, crossing_types[1:]))
    downward_cycles = sum(left == "UPPER" and right == "LOWER" for left, right in zip(crossing_types, crossing_types[1:]))
    buy_offsets = [float(item["buy_offset_observations"]) for item in alignments if item["buy_offset_observations"] != ""]
    buy_seconds = [float(item["buy_offset_seconds"]) for item in alignments if item["buy_offset_seconds"] != ""]
    sell_offsets = [float(item["sell_offset_observations"]) for item in alignments if item["sell_offset_observations"] != ""]
    sell_seconds = [float(item["sell_offset_seconds"]) for item in alignments if item["sell_offset_seconds"] != ""]
    buy_precursors = [item for item in alignments if item["weakening_decline_precursor_start_observation"] != ""]
    sell_precursors = [item for item in alignments if item["weakening_rise_precursor_start_observation"] != ""]

    precursor_summary: dict[str, dict[str, Any]] = {}
    for crossing_type in ("UPPER", "LOWER"):
        precursor_summary[crossing_type] = {}
        selected = [item for item in precursor_rows if item["crossing_type"] == crossing_type]
        for threshold in (1, 2, 3):
            qualified = [item for item in selected if item["minimum_sustained_observations"] == threshold and item["qualifies"] == "true"]
            precursor_summary[crossing_type][str(threshold)] = {
                "crossings_qualified": len(qualified),
                "mean_lead_observations": None if not qualified else float(np.mean([float(item["lead_observations"]) for item in qualified])),
                "median_lead_observations": None if not qualified else float(np.median([float(item["lead_observations"]) for item in qualified])),
                "mean_lead_seconds": None if not qualified else float(np.mean([float(item["lead_seconds"]) for item in qualified])),
                "median_lead_seconds": None if not qualified else float(np.median([float(item["lead_seconds"]) for item in qualified])),
            }

    internal_by_state: dict[str, Any] = {}
    for state_name in sorted(set(states[ACTIONABLE_START:])):
        indices = [index for index in range(ACTIONABLE_START, len(rows)) if states[index] == state_name]
        internal_by_state[state_name] = {
            "count": len(indices),
            **{
                name: numeric_summary([float(rows[index][name]) for index in indices])
                for name in ("H", "Q_G", "Q_S", "Q_R", "C")
            },
        }

    trajectory_stability: dict[str, Any] = {}
    trajectory_rows = list(csv.DictReader((ROOT / "APTF_TEST_009_TURNING_TRAJECTORIES_V0_1.csv").open(newline="", encoding="utf-8")))
    for crossing_type in ("UPPER", "LOWER"):
        by_relative: dict[int, list[float]] = defaultdict(list)
        for item in trajectory_rows:
            if item["transition_type"] == crossing_type:
                by_relative[int(item["relative_observation"])].append(float(item["normalized_price"]))
        trajectory_stability[crossing_type] = {
            str(relative): {
                "count": len(values),
                "median_normalized_price": float(np.median(values)),
                "IQR_normalized_price": float(np.quantile(values, 0.75) - np.quantile(values, 0.25)),
            }
            for relative, values in sorted(by_relative.items())
        }

    pnl_timing: dict[str, Any] = {}
    for result in ("WIN", "LOSS", "FLAT_RESULT"):
        selected = [item for item in alignments if item["test008_result_classification"] == result]
        pnl_timing[result] = {
            "count": len(selected),
            "buy_offset_observations": numeric_summary([float(item["buy_offset_observations"]) for item in selected if item["buy_offset_observations"] != ""]),
            "sell_offset_observations": numeric_summary([float(item["sell_offset_observations"]) for item in selected if item["sell_offset_observations"] != ""]),
            "buy_state_counts": dict(Counter(item["buy_derivative_state"] for item in selected)),
            "sell_state_counts": dict(Counter(item["sell_derivative_state"] for item in selected)),
        }

    state_transitions = Counter(
        f"{states[index - 1]}->{states[index]}"
        for index in range(ACTIONABLE_START, len(states))
        if states[index - 1] != "UNAVAILABLE" and states[index] != "UNAVAILABLE"
    )

    summary = {
        "test_id": "APTF_TEST_009_SUMMARY_V0_1",
        "source_rows": len(rows),
        "initializing_context_only": 15,
        "actionable_observations": len(rows) - 15,
        "derivative_price_field": "close",
        "derivative_units": {"D1": "SPY price units per minute", "D2": "SPY price units per minute squared"},
        "windows": {str(window): comparisons[window] for window in WINDOWS},
        "primary_window": primary_window,
        "selection_used_emitter_labels": False,
        "selection_used_pnl": False,
        "near_zero_sensitivity": epsilon_sensitivity,
        "primary_near_zero_threshold": epsilon,
        "D1_distribution": d1_distribution,
        "upper_D1_crossings": crossing_types.count("UPPER"),
        "lower_D1_crossings": crossing_types.count("LOWER"),
        "upward_derivative_cycles": upward_cycles,
        "downward_derivative_cycles": downward_cycles,
        "buy_transitions_analyzed": len(alignments),
        "sell_transitions_analyzed": len(alignments),
        "buy_offsets": {"observations": numeric_summary(buy_offsets), "seconds": numeric_summary(buy_seconds)},
        "sell_offsets": {"observations": numeric_summary(sell_offsets), "seconds": numeric_summary(sell_seconds)},
        "buy_preceded_by_falling_weakening": len(buy_precursors),
        "buy_preceded_by_falling_weakening_percent": 100.0 * len(buy_precursors) / len(alignments),
        "sell_preceded_by_rising_weakening": len(sell_precursors),
        "sell_preceded_by_rising_weakening_percent": 100.0 * len(sell_precursors) / len(alignments),
        "sell_before_upper_crossing": sum(float(item["sell_offset_observations"]) < 0 for item in alignments if item["sell_offset_observations"] != ""),
        "sell_at_upper_crossing": sum(float(item["sell_offset_observations"]) == 0 for item in alignments if item["sell_offset_observations"] != ""),
        "sell_after_upper_crossing": sum(float(item["sell_offset_observations"]) > 0 for item in alignments if item["sell_offset_observations"] != ""),
        "D2_precursor_by_minimum_run": precursor_summary,
        "derivative_state_transitions": dict(state_transitions),
        "internal_values_by_derivative_state": internal_by_state,
        "pnl_descriptive_timing": pnl_timing,
        "turning_trajectory_stability": trajectory_stability,
        "future_observations_used_for_primary_derivatives": 0,
        "centered_derivatives_used": False,
        "reserve_emitter_reruns": 0,
        "runtime_modified": False,
        "curve_fitted_into_runtime": False,
        "status": "PASS",
    }
    (ROOT / "APTF_TEST_009_SUMMARY_V0_1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "primary_window": primary_window,
        "near_zero_threshold": epsilon,
        "upper_crossings": summary["upper_D1_crossings"],
        "lower_crossings": summary["lower_D1_crossings"],
        "buy_transitions": len(alignments),
        "sell_transitions": len(alignments),
        "future_observations_primary": 0,
        "status": "PASS",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())