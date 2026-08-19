from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
for path in (
    ROOT,
    ROOT / "d01_adaptive_parametric_model" / "src",
    ROOT / "d02_return_shape" / "src",
    ROOT / "d04_trading_envelope" / "src",
    ROOT / "position_transition_controller",
):
    sys.path.insert(0, str(path))

from experimental_adaptive_emitter import AdaptiveEmitter
from experimental_adaptive_emitter.emitter import canonical_sha256


RESERVE_COUNT = 101221
FIRST_PHYSICAL_ROW = 106605
LAST_PHYSICAL_ROW = 207825
RESERVE_START_UTC = "2023-03-30T08:00:00Z"
RESERVE_END_UTC = "2023-09-30T08:00:00Z"
ORIGINAL_COLUMNS = ["entity_id","event_timestamp_local","event_timestamp_utc","timezone","open","high","low","close","volume","close_return_1m","high_low_range","high_low_range_fraction","open_close_change","open_close_return","session_type","is_regular_session","minute_of_session","source_provider","source_dataset","source_row_number","data_valid","quality_flags"]
APPENDED_COLUMNS = ["test006b_observation_index","source_physical_row","emission_id","emitter_status","position_state_before","position_decision","H","Q_G","Q_S","Q_R","C","state_before_fingerprint","state_after_fingerprint","emitter_lifecycle_ns","path_direction","decision_rule_path","source_delta_t_seconds"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReserveObservationStream:
    def __init__(self, path: Path) -> None:
        self._handle = path.open(newline="", encoding="utf-8")
        self.header = next(csv.reader([self._handle.readline()]))
        if self.header != ORIGINAL_COLUMNS:
            raise RuntimeError("source header mismatch")
        for _ in range(FIRST_PHYSICAL_ROW - 2):
            if not self._handle.readline():
                raise RuntimeError("source ended before reserve")
        self._reader = csv.DictReader(self._handle, fieldnames=self.header)
        self._next_physical_row = FIRST_PHYSICAL_ROW
        self._last_timestamp: datetime | None = None
        self.rows_exposed = 0

    def next_observation(self) -> tuple[int, dict[str, str]] | None:
        if self.rows_exposed >= RESERVE_COUNT:
            return None
        row = next(self._reader, None)
        if row is None:
            raise RuntimeError("source ended inside reserve")
        timestamp = datetime.fromisoformat(row["event_timestamp_utc"].replace("Z", "+00:00"))
        start = datetime.fromisoformat(RESERVE_START_UTC.replace("Z", "+00:00"))
        end = datetime.fromisoformat(RESERVE_END_UTC.replace("Z", "+00:00"))
        if not start <= timestamp < end:
            raise RuntimeError("row outside reserve interval")
        if self._last_timestamp is not None and timestamp <= self._last_timestamp:
            raise RuntimeError("non-monotonic reserve source")
        physical_row = self._next_physical_row
        self._next_physical_row += 1
        self._last_timestamp = timestamp
        self.rows_exposed += 1
        return physical_row, dict(row)

    def close(self) -> None:
        self._handle.close()


class JsonArrayWriter:
    def __init__(self, path: Path, metadata: dict[str, Any], array_name: str, prefix: dict[str, Any] | None = None) -> None:
        self.path = path
        self._handle = path.open("w", encoding="utf-8")
        header = {**metadata, **(prefix or {})}
        encoded = json.dumps(header, sort_keys=True)
        self._handle.write(encoded[:-1] + f',"{array_name}":[')
        self._first = True
        self.count = 0
        self._closed = False

    def append(self, value: Any) -> None:
        if not self._first:
            self._handle.write(",")
        self._handle.write(json.dumps(value, sort_keys=True, separators=(",", ":")))
        self._first = False
        self.count += 1

    def extend(self, values: Iterable[Any]) -> None:
        for value in values:
            self.append(value)

    def close(self, suffix: dict[str, Any] | None = None) -> None:
        if self._closed:
            return
        self._handle.write("]")
        if suffix:
            for name, value in suffix.items():
                self._handle.write("," + json.dumps(name) + ":" + json.dumps(value, sort_keys=True, separators=(",", ":")))
        self._handle.write("}\n")
        self._handle.close()
        self._closed = True


class JsonLinesWriter:
    def __init__(self, path: Path) -> None:
        self._handle = path.open("w", encoding="utf-8")
        self.count = 0

    def append(self, value: Any) -> None:
        self._handle.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        self.count += 1

    def close(self) -> None:
        self._handle.close()


def verify_freeze(pre: dict[str, Any]) -> None:
    for item in pre["frozen_files"]:
        if sha256(ROOT / item["path"]) != item["sha256"]:
            raise RuntimeError(f"frozen authority drift: {item['path']}")
    if sha256(ROOT / pre["source_path"]) != pre["source_sha256"]:
        raise RuntimeError("source hash drift")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preexecution", type=Path, required=True)
    parser.add_argument("--emissions", type=Path, required=True)
    parser.add_argument("--adaptation", type=Path, required=True)
    parser.add_argument("--feedback", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--initialization", type=Path, required=True)
    parser.add_argument("--first-proof", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    pre = json.loads(args.preexecution.read_text(encoding="utf-8"))
    verify_freeze(pre)
    metadata = {name: pre[name] for name in ("run_id", "freeze_id", "freeze_manifest_sha256", "source_sha256", "execution_timestamp_utc")}

    emitter = AdaptiveEmitter("SPY", pre["rule_sha256"], pre["implementation_sha256"])
    adaptation_writer = JsonArrayWriter(args.adaptation, metadata, "updates")
    feedback_writer = JsonArrayWriter(args.feedback, metadata, "events")
    emitter.adaptation_audit = adaptation_writer
    emitter.feedback_audit = feedback_writer
    stream = ReserveObservationStream(ROOT / pre["source_path"])
    journal = JsonLinesWriter(args.journal)
    counts: Counter[str] = Counter()
    transitions: Counter[tuple[str, str]] = Counter()
    previous_decision: str | None = None
    source_mismatches = 0
    decision_mismatches = 0
    blank_actionable = 0
    invalid_terminal = 0
    emissions_writer: JsonArrayWriter | None = None
    csv_handle = args.csv.open("w", newline="", encoding="utf-8")
    csv_writer = csv.DictWriter(csv_handle, fieldnames=ORIGINAL_COLUMNS + APPENDED_COLUMNS)
    csv_writer.writeheader()

    try:
        while True:
            exposed = stream.next_observation()
            if exposed is None:
                break
            physical_row, original = exposed
            emission = emitter.process(physical_row, original)
            index = emission["observation_index"]
            if index == 15:
                args.initialization.write_text(json.dumps({**metadata, "status":"PASS", "count":15, "records":emitter.initialization}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                emissions_writer = JsonArrayWriter(args.emissions, metadata, "emissions", {"initialization_count":15,"expected_actionable_count":RESERVE_COUNT-15})
                emitter.emissions = emissions_writer
                print("TEST 006B INITIALIZATION COMPLETE\nRESERVE OBSERVATIONS CONSUMED: 15\nACTIONABLE POSITION DECISIONS: 0\nSTATE S_15: PERSISTED\nROLLING CONTEXT: O_1 ... O_15\nRULE CHANGES: 0\nFUTURE OBSERVATIONS ACCESSED: NO\nNEXT OBSERVATION PERMITTED: O_16 ONLY.")
            if index == 16:
                args.first_proof.write_text(json.dumps({**metadata, "status":"PASS", "observation":"O_16", "physical_row":physical_row, "timestamp":emission["observation_timestamp"], "prior_context_ids":emission["prior_context_ids"], "state_before":emission["state_before"], "mathematics":{k:emission["mathematics"][k] for k in ("H","Q_G","Q_S","Q_R","C")}, "position_state_before":emission["position_state_before"], "position_decision":emission["position_decision"], "state_after":emission["state_after"], "lifecycle_ns":emission["direct_lifecycle_ns"], "future_access_count":emission["future_access_count"], "immutable":True, "next_permitted":"O_17"}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                print(f"TEST 006B — FIRST RESERVED POSITION EMISSION\nOBSERVATION: O_16\nSOURCE PHYSICAL ROW: {physical_row}\nTIMESTAMP: {emission['observation_timestamp']}\nPRIOR CONTEXT: O_1 ... O_15\nH/Q_G/Q_S/Q_R/C: {emission['mathematics']['H']}/{emission['mathematics']['Q_G']}/{emission['mathematics']['Q_S']}/{emission['mathematics']['Q_R']}/{emission['mathematics']['C']}\nPOSITION STATE BEFORE: {emission['position_state_before']}\nFINAL EMITTED POSITION: {emission['position_decision']}\nEMITTER LIFECYCLE NS: {emission['direct_lifecycle_ns']}\nFUTURE OBSERVATIONS ACCESSED: NO\nEMISSION IMMUTABLE: YES\nNEXT OBSERVATION PERMITTED: O_17.")

            decision_value = "INITIALIZING" if emission["status"] == "INITIALIZING" else emission["position_decision"]
            csv_row = {name: original[name] for name in ORIGINAL_COLUMNS}
            csv_row.update({
                "test006b_observation_index": index,
                "source_physical_row": physical_row,
                "emission_id": emission["emission_id"],
                "emitter_status": "INITIALIZING" if emission["status"] == "INITIALIZING" else "EMITTED",
                "position_state_before": emission["position_state_before"],
                "position_decision": decision_value,
                "H": emission["mathematics"]["H"],
                "Q_G": emission["mathematics"]["Q_G"],
                "Q_S": emission["mathematics"]["Q_S"],
                "Q_R": emission["mathematics"]["Q_R"],
                "C": emission["mathematics"]["C"],
                "state_before_fingerprint": canonical_sha256(emission["state_before"]),
                "state_after_fingerprint": canonical_sha256(emission["state_after"]),
                "emitter_lifecycle_ns": emission["direct_lifecycle_ns"],
                "path_direction": emission["mathematics"]["return_shape"]["path_direction"],
                "decision_rule_path": emission["decision_rule_path"],
                "source_delta_t_seconds": emission["source_delta_t_seconds"],
            })
            source_mismatches += sum(csv_row[name] != original[name] for name in ORIGINAL_COLUMNS)
            if emission["status"] == "ACTIONABLE":
                if not emission["position_decision"]:
                    blank_actionable += 1
                if emission["position_decision"] not in {"BUY", "SELL", "HOLD"}:
                    invalid_terminal += 1
                if csv_row["position_decision"] != emission["position_decision"]:
                    decision_mismatches += 1
                counts[emission["position_decision"]] += 1
                if previous_decision is not None:
                    transitions[(previous_decision, emission["position_decision"])] += 1
                previous_decision = emission["position_decision"]
            csv_writer.writerow(csv_row)

            compact = {
                "observation_index": index,
                "physical_row": physical_row,
                "timestamp": emission["observation_timestamp"],
                "delta_t_seconds": emission["source_delta_t_seconds"],
                "status": emission["status"],
                "emission_id": emission["emission_id"],
                "observation_id": emission["observation_id"],
                "decision": decision_value,
                "position_state_before": emission["position_state_before"],
                "position_state_after": emission["state_after"]["position_state"],
                "H": emission["mathematics"]["H"], "Q_G": emission["mathematics"]["Q_G"], "Q_S": emission["mathematics"]["Q_S"], "Q_R": emission["mathematics"]["Q_R"], "C": emission["mathematics"]["C"],
                "path_direction": emission["mathematics"]["return_shape"]["path_direction"],
                "prior_context_ids": emission["prior_context_ids"],
                "adaptive_properties": emission["adaptive_properties"],
                "rule_path": emission["decision_rule_path"],
                "lifecycle_ns": emission["direct_lifecycle_ns"],
                "future_access_count": emission["future_access_count"],
            }
            journal.append(compact)
            actionable = sum(counts.values())
            if actionable and actionable % 100 == 0:
                total_transitions = sum(value for (left, right), value in transitions.items() if left != right)
                print(f"TEST006B emissions={actionable}/{RESERVE_COUNT-15} time={emission['observation_timestamp']} decision={emission['position_decision']} BUY={counts['BUY']} SELL={counts['SELL']} HOLD={counts['HOLD']} transitions={total_transitions} BUY->SELL={transitions[('BUY','SELL')]} SELL->BUY={transitions[('SELL','BUY')]} Q={compact['Q_G']}/{compact['Q_S']}/{compact['Q_R']} C={compact['C']} state={compact['position_state_after']} ns={compact['lifecycle_ns']} future_access=0 rule_changes=0")
    finally:
        stream.close()
        csv_handle.close()
        journal.close()
        adaptation_writer.close()
        feedback_writer.close()
        if emissions_writer is not None:
            emissions_writer.close({"count": emissions_writer.count})

    if stream.rows_exposed != RESERVE_COUNT or sum(counts.values()) != RESERVE_COUNT - 15:
        raise RuntimeError("reserve execution count mismatch")
    summary = {
        "source_rows": stream.rows_exposed,
        "initializing": 15,
        "actionable": sum(counts.values()),
        "counts": dict(counts),
        "blank_actionable": blank_actionable,
        "invalid_terminal": invalid_terminal,
        "source_field_mismatches": source_mismatches,
        "csv_emission_decision_mismatches": decision_mismatches,
        "adaptation_events": adaptation_writer.count,
        "feedback_events": feedback_writer.count,
        "journal_rows": journal.count,
        "emission_rows": 0 if emissions_writer is None else emissions_writer.count,
    }
    args.summary.write_text(json.dumps({**metadata, **summary}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())