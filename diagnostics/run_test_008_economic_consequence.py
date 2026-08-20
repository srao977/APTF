from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, getcontext
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "APTF_TEST_007_OBSERVATION_EPISODE_MAP_V0_1.csv"
EPISODE_PATH = ROOT / "APTF_TEST_007_POSITION_EPISODES_V0_1.csv"
STRUCTURAL_GATE_PATH = ROOT / "APTF_TEST_008_PRE_PNL_STRUCTURAL_GATE_V0_2.json"
QUANTITY = 100
getcontext().prec = 50

MAP_APPEND_COLUMNS = [
    "test008_status",
    "test008_execution_intent",
    "test008_pending_execution_id",
    "test008_execution_event_id",
    "test008_simulated_quantity_before",
    "test008_simulated_quantity_after",
    "test008_active_trade_id",
    "test008_execution_price_if_filled",
    "test008_realized_gross_pnl",
    "test008_cumulative_realized_gross_pnl",
]

EXECUTION_COLUMNS = [
    "execution_event_id",
    "trade_id",
    "episode_id",
    "source_emission_id",
    "source_observation_index",
    "source_physical_row",
    "signal_timestamp",
    "emitter_decision",
    "position_state_before",
    "position_state_after",
    "execution_intent",
    "quantity",
    "execution_source_observation_index",
    "execution_source_physical_row",
    "execution_timestamp",
    "execution_price_field",
    "execution_price",
    "signal_to_execution_elapsed_seconds",
]

TRADE_COLUMNS = [
    "trade_id",
    "episode_id",
    "trade_status",
    "entry_signal_observation_index",
    "entry_signal_physical_row",
    "entry_signal_emission_id",
    "entry_signal_timestamp",
    "entry_execution_observation_index",
    "entry_execution_physical_row",
    "entry_execution_timestamp",
    "entry_execution_price_field",
    "entry_price",
    "exit_signal_observation_index",
    "exit_signal_physical_row",
    "exit_signal_emission_id",
    "exit_signal_timestamp",
    "exit_execution_observation_index",
    "exit_execution_physical_row",
    "exit_execution_timestamp",
    "exit_execution_price_field",
    "exit_price",
    "quantity",
    "entry_notional",
    "exit_notional",
    "gross_pnl_per_share",
    "gross_pnl",
    "trade_return",
    "trade_return_percent",
    "result_classification",
    "episode_observation_count",
    "episode_hold_count",
    "repeated_buy_count",
    "signal_episode_elapsed_seconds",
    "execution_holding_elapsed_seconds",
    "entry_signal_to_execution_seconds",
    "exit_signal_to_execution_seconds",
    "cumulative_gross_pnl",
]

CUMULATIVE_COLUMNS = [
    "trade_id",
    "episode_id",
    "exit_execution_timestamp",
    "gross_pnl",
    "cumulative_gross_pnl",
    "running_peak_cumulative_pnl",
    "drawdown_from_running_peak",
]


def elapsed_seconds(start: str, end: str) -> Decimal:
    left = datetime.fromisoformat(start.replace("Z", "+00:00"))
    right = datetime.fromisoformat(end.replace("Z", "+00:00"))
    return Decimal(str((right - left).total_seconds()))


def decimal_text(value: Decimal) -> str:
    return str(value)


def mean(values: list[Decimal]) -> Decimal | None:
    return None if not values else sum(values, Decimal(0)) / Decimal(len(values))


def population_stddev(values: list[Decimal]) -> Decimal | None:
    average = mean(values)
    if average is None:
        return None
    variance = sum((value - average) ** 2 for value in values) / Decimal(len(values))
    return variance.sqrt()


def maximum_run(classes: list[str], target: str) -> int:
    longest = 0
    current = 0
    for classification in classes:
        if classification == target:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def build_trades() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    episodes = list(csv.DictReader(EPISODE_PATH.open(newline="", encoding="utf-8")))
    trades = []
    by_episode = {}
    for sequence, episode in enumerate(episodes, start=1):
        trade = {
            "trade_id": f"TR{sequence:06d}",
            "episode_id": episode["episode_id"],
            "trade_status": "PENDING_ENTRY_EXECUTION",
            "entry_signal_observation_index": episode["buy_observation_index"],
            "entry_signal_physical_row": episode["buy_source_physical_row"],
            "entry_signal_emission_id": episode["buy_emission_id"],
            "entry_signal_timestamp": episode["buy_timestamp"],
            "entry_execution_observation_index": "",
            "entry_execution_physical_row": "",
            "entry_execution_timestamp": "",
            "entry_execution_price_field": "",
            "entry_price": "",
            "exit_signal_observation_index": episode["sell_observation_index"],
            "exit_signal_physical_row": episode["sell_source_physical_row"],
            "exit_signal_emission_id": episode["sell_emission_id"],
            "exit_signal_timestamp": episode["sell_timestamp"],
            "exit_execution_observation_index": "",
            "exit_execution_physical_row": "",
            "exit_execution_timestamp": "",
            "exit_execution_price_field": "",
            "exit_price": "",
            "quantity": str(QUANTITY),
            "entry_notional": "",
            "exit_notional": "",
            "gross_pnl_per_share": "",
            "gross_pnl": "",
            "trade_return": "",
            "trade_return_percent": "",
            "result_classification": "",
            "episode_observation_count": episode["observations_in_episode"],
            "episode_hold_count": episode["hold_count"],
            "repeated_buy_count": episode["repeated_buy_count"],
            "signal_episode_elapsed_seconds": episode["elapsed_source_seconds"],
            "execution_holding_elapsed_seconds": "",
            "entry_signal_to_execution_seconds": "",
            "exit_signal_to_execution_seconds": "",
            "cumulative_gross_pnl": "",
        }
        trades.append(trade)
        by_episode[episode["episode_id"]] = trade
    return trades, by_episode


def main() -> int:
    structural = json.loads(STRUCTURAL_GATE_PATH.read_text(encoding="utf-8"))
    if structural["status"] != "PASS" or structural["pnl_calculated"]:
        raise RuntimeError("pre-P&L structural gate is not authorized")

    trades, trades_by_episode = build_trades()
    events: list[dict[str, Any]] = []
    cumulative_rows: list[dict[str, Any]] = []
    edge_cases: list[dict[str, Any]] = []
    pending: dict[str, Any] | None = None
    active_trade_id: str | None = None
    quantity = 0
    cumulative_pnl = Decimal(0)
    running_peak = Decimal(0)
    maximum_drawdown = Decimal(0)
    execution_sequence = 0
    rows = 0
    actionable = 0
    initializing = 0

    output_map = ROOT / "APTF_TEST_008_OBSERVATION_EXECUTION_MAP_V0_2.csv"
    execution_path = ROOT / "APTF_TEST_008_EXECUTION_EVENTS_V0_2.csv"
    with (
        MAP_PATH.open(newline="", encoding="utf-8") as source_handle,
        output_map.open("w", newline="", encoding="utf-8") as map_handle,
        execution_path.open("w", newline="", encoding="utf-8") as execution_handle,
    ):
        reader = csv.DictReader(source_handle)
        if reader.fieldnames is None:
            raise RuntimeError("Test 007 observation map has no header")
        map_writer = csv.DictWriter(map_handle, fieldnames=reader.fieldnames + MAP_APPEND_COLUMNS)
        event_writer = csv.DictWriter(execution_handle, fieldnames=EXECUTION_COLUMNS)
        map_writer.writeheader()
        event_writer.writeheader()

        for row in reader:
            rows += 1
            quantity_before = quantity
            filled_event: dict[str, Any] | None = None
            realized_pnl = Decimal(0)

            if pending is not None:
                execution_price = Decimal(row["open"])
                signal_delay = elapsed_seconds(
                    pending["signal_timestamp"], row["event_timestamp_utc"]
                )
                filled_event = {
                    "execution_event_id": pending["execution_event_id"],
                    "trade_id": pending["trade_id"],
                    "episode_id": pending["episode_id"],
                    "source_emission_id": pending["source_emission_id"],
                    "source_observation_index": pending["source_observation_index"],
                    "source_physical_row": pending["source_physical_row"],
                    "signal_timestamp": pending["signal_timestamp"],
                    "emitter_decision": pending["emitter_decision"],
                    "position_state_before": pending["position_state_before"],
                    "position_state_after": pending["position_state_after"],
                    "execution_intent": pending["execution_intent"],
                    "quantity": str(QUANTITY),
                    "execution_source_observation_index": row["test006b_observation_index"],
                    "execution_source_physical_row": row["source_physical_row"],
                    "execution_timestamp": row["event_timestamp_utc"],
                    "execution_price_field": "open",
                    "execution_price": decimal_text(execution_price),
                    "signal_to_execution_elapsed_seconds": decimal_text(signal_delay),
                }
                trade = trades_by_episode[pending["episode_id"]]
                if pending["execution_intent"] == "BUY":
                    if quantity != 0 or active_trade_id is not None:
                        raise RuntimeError("BUY fill violates zero-position entry authority")
                    quantity = QUANTITY
                    active_trade_id = trade["trade_id"]
                    trade.update({
                        "trade_status": "OPEN_EXECUTED",
                        "entry_execution_observation_index": row["test006b_observation_index"],
                        "entry_execution_physical_row": row["source_physical_row"],
                        "entry_execution_timestamp": row["event_timestamp_utc"],
                        "entry_execution_price_field": "open",
                        "entry_price": decimal_text(execution_price),
                        "entry_notional": decimal_text(Decimal(QUANTITY) * execution_price),
                        "entry_signal_to_execution_seconds": decimal_text(signal_delay),
                    })
                elif pending["execution_intent"] == "SELL":
                    if quantity != QUANTITY or active_trade_id != trade["trade_id"]:
                        raise RuntimeError("SELL fill violates active 100-share trade authority")
                    entry_price = Decimal(trade["entry_price"])
                    gross_per_share = execution_price - entry_price
                    gross_pnl = Decimal(QUANTITY) * gross_per_share
                    entry_notional = Decimal(trade["entry_notional"])
                    exit_notional = Decimal(QUANTITY) * execution_price
                    if gross_pnl != exit_notional - entry_notional:
                        raise RuntimeError("trade notional reconciliation failed")
                    classification = (
                        "WIN" if gross_pnl > 0 else "LOSS" if gross_pnl < 0 else "FLAT_RESULT"
                    )
                    cumulative_pnl += gross_pnl
                    running_peak = max(running_peak, cumulative_pnl)
                    drawdown = cumulative_pnl - running_peak
                    maximum_drawdown = max(maximum_drawdown, -drawdown)
                    realized_pnl = gross_pnl
                    trade.update({
                        "trade_status": "COMPLETED",
                        "exit_execution_observation_index": row["test006b_observation_index"],
                        "exit_execution_physical_row": row["source_physical_row"],
                        "exit_execution_timestamp": row["event_timestamp_utc"],
                        "exit_execution_price_field": "open",
                        "exit_price": decimal_text(execution_price),
                        "exit_notional": decimal_text(exit_notional),
                        "gross_pnl_per_share": decimal_text(gross_per_share),
                        "gross_pnl": decimal_text(gross_pnl),
                        "trade_return": decimal_text(gross_per_share / entry_price),
                        "trade_return_percent": decimal_text(
                            Decimal(100) * gross_per_share / entry_price
                        ),
                        "result_classification": classification,
                        "execution_holding_elapsed_seconds": decimal_text(
                            elapsed_seconds(
                                trade["entry_execution_timestamp"], row["event_timestamp_utc"]
                            )
                        ),
                        "exit_signal_to_execution_seconds": decimal_text(signal_delay),
                        "cumulative_gross_pnl": decimal_text(cumulative_pnl),
                    })
                    cumulative_rows.append({
                        "trade_id": trade["trade_id"],
                        "episode_id": trade["episode_id"],
                        "exit_execution_timestamp": row["event_timestamp_utc"],
                        "gross_pnl": decimal_text(gross_pnl),
                        "cumulative_gross_pnl": decimal_text(cumulative_pnl),
                        "running_peak_cumulative_pnl": decimal_text(running_peak),
                        "drawdown_from_running_peak": decimal_text(drawdown),
                    })
                    quantity = 0
                    active_trade_id = None
                else:
                    raise RuntimeError("unsupported pending execution intent")
                events.append(filled_event)
                event_writer.writerow(filled_event)
                pending = None

            decision = row["position_decision"]
            current_intent = "NONE"
            pending_id = ""
            if decision == "INITIALIZING":
                initializing += 1
                status = "INITIALIZING_EXCLUDED"
                if rows > 15 or quantity != 0 or filled_event is not None:
                    raise RuntimeError("initialization exclusion violated")
            else:
                actionable += 1
                classification = row["test007_structural_classification"]
                if classification == "EPISODE_OPEN":
                    current_intent = "BUY"
                elif classification == "EPISODE_CLOSE":
                    current_intent = "SELL"
                if current_intent != "NONE":
                    if pending is not None:
                        raise RuntimeError("pending execution collision")
                    execution_sequence += 1
                    pending_id = f"EX{execution_sequence:06d}"
                    episode_id = row["test007_episode_id"]
                    trade = trades_by_episode[episode_id]
                    pending = {
                        "execution_event_id": pending_id,
                        "trade_id": trade["trade_id"],
                        "episode_id": episode_id,
                        "source_emission_id": row["emission_id"],
                        "source_observation_index": row["test006b_observation_index"],
                        "source_physical_row": row["source_physical_row"],
                        "signal_timestamp": row["event_timestamp_utc"],
                        "emitter_decision": decision,
                        "position_state_before": row["test007_position_state_before"],
                        "position_state_after": row["test007_position_state_after"],
                        "execution_intent": current_intent,
                    }
                if filled_event is not None and pending is not None:
                    status = "EXECUTION_FILLED_AND_PENDING_CREATED"
                elif filled_event is not None:
                    status = "EXECUTION_FILLED"
                elif pending is not None:
                    status = "PENDING_EXECUTION_CREATED"
                else:
                    status = "ACTIONABLE_NO_TRANSACTION"

            if quantity not in (0, QUANTITY):
                raise RuntimeError("simulated quantity outside 0/100 authority")
            output = dict(row)
            output.update({
                "test008_status": status,
                "test008_execution_intent": current_intent,
                "test008_pending_execution_id": pending_id,
                "test008_execution_event_id": (
                    "" if filled_event is None else filled_event["execution_event_id"]
                ),
                "test008_simulated_quantity_before": str(quantity_before),
                "test008_simulated_quantity_after": str(quantity),
                "test008_active_trade_id": active_trade_id or "",
                "test008_execution_price_if_filled": (
                    "" if filled_event is None else filled_event["execution_price"]
                ),
                "test008_realized_gross_pnl": decimal_text(realized_pnl),
                "test008_cumulative_realized_gross_pnl": decimal_text(cumulative_pnl),
            })
            map_writer.writerow(output)

    if pending is not None:
        edge_cases.append({
            "edge_case": "NO_NEXT_OBSERVATION_EXECUTION",
            "execution_event_id": pending["execution_event_id"],
            "episode_id": pending["episode_id"],
            "signal_observation_index": pending["source_observation_index"],
            "signal_timestamp": pending["signal_timestamp"],
            "execution_intent": pending["execution_intent"],
        })

    completed = [trade for trade in trades if trade["trade_status"] == "COMPLETED"]
    pnl_values = [Decimal(trade["gross_pnl"]) for trade in completed]
    classes = [trade["result_classification"] for trade in completed]
    wins = [value for value in pnl_values if value > 0]
    losses = [value for value in pnl_values if value < 0]
    flats = [value for value in pnl_values if value == 0]
    total_pnl = sum(pnl_values, Decimal(0))
    entry_notional_total = sum((Decimal(trade["entry_notional"]) for trade in completed), Decimal(0))
    exit_notional_total = sum((Decimal(trade["exit_notional"]) for trade in completed), Decimal(0))
    gross_profit = sum(wins, Decimal(0))
    gross_negative = sum(losses, Decimal(0))
    gross_loss_absolute = -gross_negative
    profit_factor = None if gross_loss_absolute == 0 else gross_profit / gross_loss_absolute

    if not (
        rows == 101221
        and initializing == 15
        and actionable == 101206
        and len(trades) == 2051
        and len(completed) == 2051
        and len(events) == 4102
        and sum(event["execution_intent"] == "BUY" for event in events) == 2051
        and sum(event["execution_intent"] == "SELL" for event in events) == 2051
        and quantity == 0
        and pending is None
    ):
        raise RuntimeError("execution/trade reconciliation failed")
    if not (
        total_pnl == exit_notional_total - entry_notional_total == cumulative_pnl
    ):
        raise RuntimeError("three-method P&L reconciliation failed")

    with (ROOT / "APTF_TEST_008_TRADE_LEDGER_V0_2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=TRADE_COLUMNS)
        writer.writeheader()
        writer.writerows(trades)
    with (ROOT / "APTF_TEST_008_CUMULATIVE_GROSS_PNL_V0_2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=CUMULATIVE_COLUMNS)
        writer.writeheader()
        writer.writerows(cumulative_rows)
    edge_columns = [
        "edge_case", "execution_event_id", "episode_id", "signal_observation_index",
        "signal_timestamp", "execution_intent",
    ]
    with (ROOT / "APTF_TEST_008_EDGE_CASES_V0_2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=edge_columns)
        writer.writeheader()
        writer.writerows(edge_cases)

    monthly: dict[str, list[Decimal]] = defaultdict(list)
    for trade in completed:
        monthly[trade["exit_execution_timestamp"][:7]].append(Decimal(trade["gross_pnl"]))
    with (ROOT / "APTF_TEST_008_MONTHLY_PNL_V0_2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        columns = ["calendar_month", "completed_trades", "winning_trades", "losing_trades", "flat_result_trades", "gross_pnl"]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for month in sorted(monthly):
            values = monthly[month]
            writer.writerow({
                "calendar_month": month,
                "completed_trades": len(values),
                "winning_trades": sum(value > 0 for value in values),
                "losing_trades": sum(value < 0 for value in values),
                "flat_result_trades": sum(value == 0 for value in values),
                "gross_pnl": decimal_text(sum(values, Decimal(0))),
            })

    summary = {
        "test_id": "APTF_TEST_008_PNL_SUMMARY_V0_2",
        "label": "GROSS P&L UNDER TEST 008 V0.2 ASSUMPTIONS",
        "source_rows": rows,
        "initializing_excluded": initializing,
        "actionable_rows": actionable,
        "trade_episodes": len(trades),
        "completed_trades": len(completed),
        "incomplete_or_unexecutable": len(trades) - len(completed),
        "buy_executions": sum(event["execution_intent"] == "BUY" for event in events),
        "sell_executions": sum(event["execution_intent"] == "SELL" for event in events),
        "final_simulated_quantity": quantity,
        "total_gross_pnl": decimal_text(total_pnl),
        "mean_gross_pnl_per_trade": decimal_text(mean(pnl_values) or Decimal(0)),
        "median_gross_pnl_per_trade": decimal_text(median(pnl_values)),
        "minimum_trade_gross_pnl": decimal_text(min(pnl_values)),
        "maximum_trade_gross_pnl": decimal_text(max(pnl_values)),
        "population_standard_deviation_trade_pnl": decimal_text(population_stddev(pnl_values) or Decimal(0)),
        "gross_positive_pnl": decimal_text(gross_profit),
        "gross_negative_pnl": decimal_text(gross_negative),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "flat_result_trades": len(flats),
        "win_rate": decimal_text(Decimal(len(wins)) / Decimal(len(completed))),
        "win_rate_percent": decimal_text(Decimal(100 * len(wins)) / Decimal(len(completed))),
        "loss_rate": decimal_text(Decimal(len(losses)) / Decimal(len(completed))),
        "loss_rate_percent": decimal_text(Decimal(100 * len(losses)) / Decimal(len(completed))),
        "average_winning_trade": None if not wins else decimal_text(mean(wins) or Decimal(0)),
        "median_winning_trade": None if not wins else decimal_text(median(wins)),
        "average_losing_trade": None if not losses else decimal_text(mean(losses) or Decimal(0)),
        "median_losing_trade": None if not losses else decimal_text(median(losses)),
        "largest_winning_trade": None if not wins else decimal_text(max(wins)),
        "largest_losing_trade": None if not losses else decimal_text(min(losses)),
        "profit_factor": None if profit_factor is None else decimal_text(profit_factor),
        "profit_factor_status": "UNDEFINED_NO_GROSS_LOSS" if profit_factor is None else "DEFINED",
        "expectancy_per_trade": decimal_text(total_pnl / Decimal(len(completed))),
        "final_cumulative_gross_pnl": decimal_text(cumulative_pnl),
        "maximum_cumulative_pnl_drawdown": decimal_text(maximum_drawdown),
        "maximum_consecutive_wins": maximum_run(classes, "WIN"),
        "maximum_consecutive_losses": maximum_run(classes, "LOSS"),
        "maximum_consecutive_flat_results": maximum_run(classes, "FLAT_RESULT"),
        "commission": "0",
        "regulatory_fees": "0",
        "exchange_fees": "0",
        "spread_cost": "0",
        "slippage": "0",
        "compounding": False,
        "dividends": "EXCLUDED",
        "financing": "EXCLUDED",
        "account_capital_modeled": False,
        "status": "PASS",
    }
    reconciliation = {
        "test_id": "APTF_TEST_008_EXECUTION_RECONCILIATION_V0_2",
        "test007_episode_count": 2051,
        "test008_trade_rows": len(trades),
        "completed_trades": len(completed),
        "buy_executions": summary["buy_executions"],
        "sell_executions": summary["sell_executions"],
        "shares_bought": summary["buy_executions"] * QUANTITY,
        "shares_sold": summary["sell_executions"] * QUANTITY,
        "final_simulated_quantity": quantity,
        "sum_trade_gross_pnl": decimal_text(total_pnl),
        "exit_notional_minus_entry_notional": decimal_text(exit_notional_total - entry_notional_total),
        "final_cumulative_gross_pnl": decimal_text(cumulative_pnl),
        "three_method_exact_match": True,
        "pending_execution_collisions": 0,
        "no_next_observation_executions": len(edge_cases),
        "same_observation_execution_used": False,
        "next_observation_open_used": True,
        "short_executions": 0,
        "quantity_minimum": 0,
        "quantity_maximum": QUANTITY,
        "status": "PASS",
    }
    (ROOT / "APTF_TEST_008_PNL_SUMMARY_V0_2.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ROOT / "APTF_TEST_008_EXECUTION_RECONCILIATION_V0_2.json").write_text(
        json.dumps(reconciliation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "completed_trades": len(completed),
        "buy_executions": summary["buy_executions"],
        "sell_executions": summary["sell_executions"],
        "total_gross_pnl": summary["total_gross_pnl"],
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "flat_result_trades": len(flats),
        "reconciliation": "PASS",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())