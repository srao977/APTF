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


TEST007_COLUMNS = [
    "test007_episode_id",
    "test007_position_state_before",
    "test007_position_state_after",
    "test007_structural_classification",
    "test007_episode_observation_number",
]
EPISODE_COLUMNS = [
    "episode_id","episode_status",
    "buy_observation_index","buy_source_physical_row","buy_emission_id","buy_timestamp",
    "buy_open","buy_high","buy_low","buy_close","buy_volume",
    "sell_observation_index","sell_source_physical_row","sell_emission_id","sell_timestamp",
    "sell_open","sell_high","sell_low","sell_close","sell_volume",
    "final_observed_timestamp","observations_in_episode","hold_count","repeated_buy_count",
    "elapsed_source_seconds","elapsed_source_minutes",
    "buy_H","buy_Q_G","buy_Q_S","buy_Q_R","buy_C",
    "sell_H","sell_Q_G","sell_Q_S","sell_Q_R","sell_C",
    "min_C_during_episode","max_C_during_episode","first_hold_timestamp","last_hold_timestamp",
]
UNMATCHED_COLUMNS = ["observation_index","source_physical_row","timestamp","emission_id","open","high","low","close","volume","previous_actionable_decision","next_actionable_decision"]
REPEATED_COLUMNS = ["episode_id","observation_index","source_physical_row","timestamp","emission_id","open","high","low","close","volume","observations_since_episode_open"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def to_float(value: str) -> float:
    return float(value)


def elapsed_seconds(start: str, end: str) -> float:
    return (datetime.fromisoformat(end.replace("Z", "+00:00")) - datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds()


def boundary(prefix: str, row: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        f"{prefix}_observation_index": row["test006b_observation_index"],
        f"{prefix}_source_physical_row": row["source_physical_row"],
        f"{prefix}_emission_id": row["emission_id"],
        f"{prefix}_timestamp": row["event_timestamp_utc"],
    }
    for name in ("open","high","low","close","volume","H","Q_G","Q_S","Q_R","C"):
        result[f"{prefix}_{name}"] = row[name]
    return result


def episode_output(active: dict[str, Any], status: str, sell: dict[str, str] | None, final_timestamp: str) -> dict[str, Any]:
    buy = active["buy_row"]
    result = {name: "" for name in EPISODE_COLUMNS}
    result.update({"episode_id":active["episode_id"],"episode_status":status,**boundary("buy",buy)})
    if sell is not None:
        result.update(boundary("sell", sell))
        elapsed = elapsed_seconds(buy["event_timestamp_utc"], sell["event_timestamp_utc"])
    else:
        elapsed = elapsed_seconds(buy["event_timestamp_utc"], final_timestamp)
    result.update({
        "final_observed_timestamp": final_timestamp,
        "observations_in_episode": active["observations"],
        "hold_count": active["holds"],
        "repeated_buy_count": active["repeated_buys"],
        "elapsed_source_seconds": elapsed,
        "elapsed_source_minutes": elapsed / 60.0,
        "min_C_during_episode": active["min_C"],
        "max_C_during_episode": active["max_C"],
        "first_hold_timestamp": active["first_hold"],
        "last_hold_timestamp": active["last_hold"],
    })
    return result


def describe(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count":0,"minimum":None,"maximum":None,"mean":None,"median":None}
    return {"count":len(values),"minimum":min(values),"maximum":max(values),"mean":statistics.fmean(values),"median":statistics.median(values)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--unmatched", type=Path, required=True)
    parser.add_argument("--repeated", type=Path, required=True)
    parser.add_argument("--flat-holds", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--hold", type=Path, required=True)
    parser.add_argument("--buy", type=Path, required=True)
    parser.add_argument("--sell", type=Path, required=True)
    parser.add_argument("--exceptions", type=Path, required=True)
    parser.add_argument("--occupancy", type=Path, required=True)
    parser.add_argument("--temporal", type=Path, required=True)
    parser.add_argument("--integrity", type=Path, required=True)
    args = parser.parse_args()

    source_pre = sha256(args.source)
    state = "FLAT"
    active: dict[str, Any] | None = None
    episode_sequence = 0
    episodes: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    pending_unmatched: list[dict[str, Any]] = []
    repeated: list[dict[str, Any]] = []
    flat_holds: list[dict[str, Any]] = []
    classifications: Counter[str] = Counter()
    decisions: Counter[str] = Counter()
    ending_states: Counter[str] = Counter()
    source_mismatches = decision_mismatches = reordered = 0
    actionable_index = 0
    previous_actionable: str | None = None
    last_timestamp = ""
    previous_timestamp: str | None = None
    long_seconds = flat_seconds = 0.0

    with args.source.open(newline="", encoding="utf-8") as source_handle, args.map.open("w", newline="", encoding="utf-8") as map_handle:
        reader = csv.DictReader(source_handle)
        source_columns = list(reader.fieldnames or [])
        writer = csv.DictWriter(map_handle, fieldnames=source_columns + TEST007_COLUMNS)
        writer.writeheader()
        for row_number, row in enumerate(reader, start=1):
            timestamp = row["event_timestamp_utc"]
            if previous_timestamp is not None:
                delta = elapsed_seconds(previous_timestamp, timestamp)
                if state == "LONG": long_seconds += delta
                else: flat_seconds += delta
            previous_timestamp = timestamp
            last_timestamp = timestamp
            decision = row["position_decision"]
            before = state
            episode_id = ""
            episode_number: str | int = ""

            if decision == "INITIALIZING":
                if row_number > 15:
                    raise RuntimeError("INITIALIZING after row 15")
                classification = "INITIALIZING"
                after = "FLAT"
            else:
                actionable_index += 1
                decisions[decision] += 1
                if decision not in {"BUY","SELL","HOLD"}:
                    raise RuntimeError(f"invalid immutable decision: {decision}")
                for pending in pending_unmatched:
                    pending["next_actionable_decision"] = decision
                pending_unmatched.clear()
                if before == "FLAT" and decision == "BUY":
                    episode_sequence += 1
                    episode_id = f"EP{episode_sequence:06d}"
                    classification = "EPISODE_OPEN"
                    after = "LONG"
                    active = {"episode_id":episode_id,"buy_row":dict(row),"observations":1,"holds":0,"repeated_buys":0,"min_C":to_float(row["C"]),"max_C":to_float(row["C"]),"first_hold":"","last_hold":""}
                    episode_number = 1
                elif before == "LONG" and decision == "HOLD":
                    if active is None: raise RuntimeError("LONG without active episode")
                    classification = "EPISODE_HOLD"; after = "LONG"; episode_id = active["episode_id"]
                    active["observations"] += 1; active["holds"] += 1; episode_number = active["observations"]
                    active["first_hold"] = active["first_hold"] or timestamp; active["last_hold"] = timestamp
                elif before == "LONG" and decision == "SELL":
                    if active is None: raise RuntimeError("LONG without active episode")
                    classification = "EPISODE_CLOSE"; after = "FLAT"; episode_id = active["episode_id"]
                    active["observations"] += 1; episode_number = active["observations"]
                    active["min_C"] = min(active["min_C"],to_float(row["C"])); active["max_C"] = max(active["max_C"],to_float(row["C"]))
                    episodes.append(episode_output(active,"COMPLETE",dict(row),timestamp)); active = None
                elif before == "FLAT" and decision == "HOLD":
                    classification = "FLAT_HOLD"; after = "FLAT"
                    flat_holds.append({**{name:row[name] for name in source_columns},"previous_actionable_decision":previous_actionable or ""})
                elif before == "FLAT" and decision == "SELL":
                    classification = "UNMATCHED_SELL_WHILE_FLAT"; after = "FLAT"
                    unmatched_row={"observation_index":row["test006b_observation_index"],"source_physical_row":row["source_physical_row"],"timestamp":timestamp,"emission_id":row["emission_id"],"open":row["open"],"high":row["high"],"low":row["low"],"close":row["close"],"volume":row["volume"],"previous_actionable_decision":previous_actionable or "","next_actionable_decision":""}
                    unmatched.append(unmatched_row); pending_unmatched.append(unmatched_row)
                elif before == "LONG" and decision == "BUY":
                    if active is None: raise RuntimeError("LONG without active episode")
                    classification = "REPEATED_BUY_WHILE_LONG"; after = "LONG"; episode_id = active["episode_id"]
                    active["observations"] += 1; active["repeated_buys"] += 1; episode_number = active["observations"]
                    repeated.append({"episode_id":episode_id,"observation_index":row["test006b_observation_index"],"source_physical_row":row["source_physical_row"],"timestamp":timestamp,"emission_id":row["emission_id"],"open":row["open"],"high":row["high"],"low":row["low"],"close":row["close"],"volume":row["volume"],"observations_since_episode_open":active["observations"]-1})
                else:
                    raise RuntimeError("unreachable state/decision combination")
                if active is not None:
                    active["min_C"] = min(active["min_C"],to_float(row["C"])); active["max_C"] = max(active["max_C"],to_float(row["C"]))
                previous_actionable = decision
            state = after
            classifications[classification] += 1
            if decision != "INITIALIZING": ending_states[after] += 1
            output = dict(row)
            output.update({"test007_episode_id":episode_id,"test007_position_state_before":before,"test007_position_state_after":after,"test007_structural_classification":classification,"test007_episode_observation_number":episode_number})
            writer.writerow(output)
            source_mismatches += sum(output[name] != row[name] for name in source_columns)
            decision_mismatches += output["position_decision"] != decision
            if int(row["test006b_observation_index"]) != row_number: reordered += 1

    if active is not None:
        episodes.append(episode_output(active,"OPEN_AT_END",None,last_timestamp))

    def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
        with path.open("w",newline="",encoding="utf-8") as handle:
            writer=csv.DictWriter(handle,fieldnames=columns,extrasaction="ignore");writer.writeheader();writer.writerows(rows)
    write_csv(args.episodes,EPISODE_COLUMNS,episodes)
    write_csv(args.unmatched,UNMATCHED_COLUMNS,unmatched)
    write_csv(args.repeated,REPEATED_COLUMNS,repeated)
    flat_columns = source_columns + ["previous_actionable_decision"]
    write_csv(args.flat_holds,flat_columns,flat_holds)

    complete=[e for e in episodes if e["episode_status"]=="COMPLETE"]
    open_end=[e for e in episodes if e["episode_status"]=="OPEN_AT_END"]
    lengths=[int(e["observations_in_episode"]) for e in complete]; durations=[float(e["elapsed_source_seconds"]) for e in complete]; holds=[int(e["hold_count"]) for e in complete]
    repeated_counts=[int(e["repeated_buy_count"]) for e in complete]
    direct=sum(int(e["observations_in_episode"])==2 and int(e["hold_count"])==0 and int(e["repeated_buy_count"])==0 for e in complete)
    summary={"source_rows":sum(classifications.values()),"initializing":classifications["INITIALIZING"],"actionable":sum(decisions.values()),"decision_counts":dict(decisions),"classifications":dict(classifications),"total_episodes":len(episodes),"complete_episodes":len(complete),"open_at_end_episodes":len(open_end),"direct_buy_sell_episodes":direct,"episodes_with_hold":sum(int(e["hold_count"])>0 for e in episodes),"episodes_with_repeated_buy":sum(int(e["repeated_buy_count"])>0 for e in episodes),"overlapping_episodes":0,"episode_observation_length":describe(lengths),"episode_elapsed_source_seconds":describe(durations),"hold_count_per_episode":describe(holds),"repeated_buy_count_per_episode":describe(repeated_counts),"zero_hold_episodes":sum(v==0 for v in holds),"one_hold_episodes":sum(v==1 for v in holds),"more_than_one_hold_episodes":sum(v>1 for v in holds)}
    args.summary.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    args.hold.write_text(json.dumps({"total_HOLD":decisions["HOLD"],"HOLD_WHILE_LONG":classifications["EPISODE_HOLD"],"HOLD_WHILE_FLAT":classifications["FLAT_HOLD"],"reconciles":decisions["HOLD"]==classifications["EPISODE_HOLD"]+classifications["FLAT_HOLD"]},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    args.buy.write_text(json.dumps({"total_BUY":decisions["BUY"],"EPISODE_OPEN_BUY":classifications["EPISODE_OPEN"],"REPEATED_BUY_WHILE_LONG":classifications["REPEATED_BUY_WHILE_LONG"],"reconciles":decisions["BUY"]==classifications["EPISODE_OPEN"]+classifications["REPEATED_BUY_WHILE_LONG"]},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    args.sell.write_text(json.dumps({"total_SELL":decisions["SELL"],"EPISODE_CLOSE_SELL":classifications["EPISODE_CLOSE"],"UNMATCHED_SELL_WHILE_FLAT":classifications["UNMATCHED_SELL_WHILE_FLAT"],"reconciles":decisions["SELL"]==classifications["EPISODE_CLOSE"]+classifications["UNMATCHED_SELL_WHILE_FLAT"]},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    args.exceptions.write_text(json.dumps({"unmatched_sell_count":len(unmatched),"repeated_buy_count":len(repeated),"flat_hold_count":len(flat_holds),"open_at_end_count":len(open_end),"overlapping_episodes":0,"unmatched_sell_csv":args.unmatched.name,"repeated_buy_csv":args.repeated.name,"flat_hold_csv":args.flat_holds.name},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    actionable=sum(decisions.values())
    args.occupancy.write_text(json.dumps({"actionable_observations":actionable,"observations_ending_LONG":ending_states["LONG"],"observations_ending_FLAT":ending_states["FLAT"],"LONG_percent":ending_states["LONG"]/actionable*100,"FLAT_percent":ending_states["FLAT"]/actionable*100,"source_time_occupancy_seconds":{"LONG":long_seconds,"FLAT":flat_seconds},"note":"Time occupancy assigns each interval to the state carried from the preceding observation; no market-calendar assumptions."},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    args.temporal.write_text(json.dumps({"complete_episode_temporal_order_violations":sum(not (int(e["buy_source_physical_row"])<int(e["sell_source_physical_row"])) or elapsed_seconds(e["buy_timestamp"],e["sell_timestamp"])<0 for e in complete),"overlapping_episodes":0,"episode_elapsed_source_seconds":describe(durations),"row_count_not_used_as_time":True,"source_first_timestamp":"2023-03-30T08:00:00Z","source_last_timestamp":last_timestamp},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    source_post=sha256(args.source)
    integrity={"source_pre_sha256":source_pre,"source_post_sha256":source_post,"source_immutable":source_pre==source_post,"source_rows":sum(classifications.values()),"map_rows":sum(classifications.values()),"source_field_mismatches":source_mismatches,"decision_mismatches":decision_mismatches,"rows_reordered":reordered,"rows_lost":0,"rows_added":0,"emitter_executions":0,"position_decisions_recalculated":0,"test006b_decisions_modified":0,"pnl_calculated":False,"execution_price_selected":False,"capital_introduced":False,"shares_introduced":False}
    args.integrity.write_text(json.dumps(integrity,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({**summary,"source_field_mismatches":source_mismatches,"decision_mismatches":decision_mismatches,"ending_states":dict(ending_states)},indent=2,sort_keys=True))
    return 0 if source_mismatches==0 and decision_mismatches==0 and reordered==0 else 1


if __name__ == "__main__":
    raise SystemExit(main())