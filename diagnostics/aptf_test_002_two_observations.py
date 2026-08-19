from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from datetime import datetime
from itertools import islice
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for path in (
    ROOT / "aptf_runtime" / "src",
    ROOT / "d01_adaptive_parametric_model" / "src",
    ROOT / "d02_return_shape" / "src",
    ROOT / "d04_trading_envelope" / "src",
    ROOT / "d03_decision_control" / "src",
    ROOT / "position_transition_controller",
):
    sys.path.insert(0, str(path))

from aptf_d04.models.envelope_context import EnvelopeContext
from aptf_runtime.canonical_json import canonical_sha256, normalize_semantic
from aptf_runtime.clock import SystemClock
from aptf_runtime.payload_serialization import d01_payload, normalized_source_record, scientific_ids
from aptf_runtime.stage_wrappers import create_source_event, execute_stage
from d02.v02.builder import build_return_shape
from d03.v01 import D03Input, DecisionContext, PendingTargetState, PositionState, evaluate_decision
from position_transition_controller import PositionTransitionController
from real_causal_replay_harness_v0_2 import RealCausalReplayHarness

SOURCE_PATH = ROOT / "data" / "market" / "normalized" / "SPY_1min_normalized_v0_1.csv"
TEST_001_TRACE_PATH = ROOT / "APTF_TEST_001_ROW_10_COMPONENT_TRACE_V0_1.json"
SOURCE_STREAM_ID = (
    "aptf:source:v1:FirstRateData:SPY_1min_firstratedata:normalized_v0_1:sha256:"
    "73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d"
)
TARGETS = (
    {"label": "t1", "physical_row": 10, "index": 8, "source_row": "9", "time": "2022-09-30T08:08:00Z"},
    {"label": "t2", "physical_row": 11, "index": 9, "source_row": "10", "time": "2022-09-30T08:09:00Z"},
)


def read_through_targets() -> tuple[list[str], list[dict[str, str]]]:
    with SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(islice(reader, 10))
        header = list(reader.fieldnames or [])
    if len(rows) != 10:
        raise RuntimeError("physical CSV rows 10 and 11 could not be resolved")
    for target in TARGETS:
        row = rows[target["index"]]
        if row["event_timestamp_utc"] != target["time"] or row["source_row_number"] != target["source_row"]:
            raise RuntimeError(f"{target['label']} source identity mismatch")
    return header, rows


def normalized_state(value: Any) -> Any:
    return normalize_semantic(value)


def d01_state_snapshot(harness: RealCausalReplayHarness) -> dict[str, Any]:
    state = harness.d01_model.state
    return normalized_state(
        {
            "object_type": type(state).__name__,
            "sequence": state.sequence,
            "model_time": state.model_time,
            "adaptive_reference": state.adaptive_reference,
            "adaptive_scale": state.adaptive_scale,
            "volume_reference": state.volume_reference,
            "prev_level": state.prev_level,
            "prev_velocity": state.prev_velocity,
            "last_event_time": state.last_event_time,
            "parameter_state": state.parameter_state,
            "state_vector": state.state_vector,
            "half_life_state": state.half_life_state,
            "data_gap_count": state.data_gap_count,
        }
    )


def d04_state_snapshot(harness: RealCausalReplayHarness) -> dict[str, Any]:
    envelope = harness.envelope
    return normalized_state(
        {
            "object_type": type(envelope).__name__,
            "current_state": envelope.current_state,
            "current_aperture": envelope.current_aperture,
            "current_entity_id": envelope.current_entity_id,
            "current_model_time": envelope.current_model_time,
            "current_candidate": envelope.current_candidate,
            "consecutive_open_qualifying": envelope.hysteresis.consecutive_open_qualifying,
            "consecutive_close_qualifying": envelope.hysteresis.consecutive_close_qualifying,
        }
    )


def controller_state_snapshot(harness: RealCausalReplayHarness) -> dict[str, Any]:
    return {
        "object_type": type(harness.actual_position).__name__,
        "state": harness.actual_position.state,
        "version": harness.actual_position.version,
        "identity": harness.actual_position.identity,
        "semantic_label": "INTERNAL CONTROLLER STATE",
        "broker_sourced": False,
    }


def envelope_context(observation: Any) -> EnvelopeContext:
    return EnvelopeContext.production(
        evaluation_time=observation.event_time,
    )


def decision_context(harness: RealCausalReplayHarness, observation: Any) -> DecisionContext:
    state = harness.actual_position.state
    candidate_id = None
    candidate_source_time = None
    if state in {"LONG", "SHORT"}:
        candidate_id = f"D04C|{harness.entity_id}|0.0|0.0"
        candidate_source_time = 0.0
    return DecisionContext(
        context_time=observation.event_time,
        entity_id=harness.entity_id,
        actual_position_state=PositionState(state),
        position_candidate_id=candidate_id,
        position_source_return_shape_model_time=candidate_source_time,
        pending_target_state=PendingTargetState.NONE,
        pending_decision_id=None,
        execution_available=True,
        system_enabled=True,
        trading_enabled=True,
        emergency_flatten=False,
        control_state_valid=True,
    )


def warmup(harness: RealCausalReplayHarness, rows: list[dict[str, str]]) -> dict[str, Any]:
    initial = controller_state_snapshot(harness)
    authorized_advancements = 0
    for index, row in enumerate(rows):
        decision, error = harness.process_row_to_decision(row, index, row["event_timestamp_utc"])
        if decision is None:
            raise RuntimeError(f"warm-up failed at index {index}: {error}")
        plan = harness.controller.derive_transition_plan(
            decision,
            harness.actual_position.as_dict(),
            decision["input_fingerprint"],
        )
        if plan is None:
            raise RuntimeError(f"warm-up controller rejected index {index}")
        if plan.action_authorized:
            harness.actual_position = harness.actual_position.advance_after_execution(plan.ordered_execution_verbs)
            authorized_advancements += 1
    return {
        "rows_consumed": len(rows),
        "data_indices": [0, len(rows) - 1],
        "initial_control_state": initial,
        "control_state_before_t1": controller_state_snapshot(harness),
        "authorized_semantic_advancements": authorized_advancements,
        "classification": "TEST/REPLAY INITIAL CONTROL STATE",
        "synthetic_market_data": False,
    }


def event_record(stage: str, envelope: Any) -> dict[str, Any]:
    value = envelope.as_dict()
    value.pop("payload")
    duration = envelope.processing_duration_ns
    return {
        "stage": stage,
        **value,
        "processing_duration_us": duration / 1_000.0,
        "processing_duration_ms": duration / 1_000_000.0,
    }


def process_target(
    harness: RealCausalReplayHarness,
    clock: SystemClock,
    row: dict[str, str],
    target: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    observation = harness.source_row_to_normalized_observation(row, target["index"])
    if observation is None:
        raise RuntimeError(f"{target['label']} normalization failed")
    before = {
        "d01": d01_state_snapshot(harness),
        "d04": d04_state_snapshot(harness),
        "d03": {"stateful": False},
        "controller": controller_state_snapshot(harness),
    }
    context = envelope_context(observation)
    control = decision_context(harness, observation)
    controller_snapshot = harness.actual_position.as_dict()

    direct_start_ns = clock.monotonic_ns()
    source = create_source_event(
        clock=clock,
        source_stream_id=SOURCE_STREAM_ID,
        sequence_number=target["index"],
        instrument_id="SPY",
        market_event_time_utc=target["time"],
        market_event_time_role="PROVIDER_EVENT",
        payload_type="NormalizedObservationSourceRecord",
        payload_version="v0_1",
        source_builder=lambda: normalized_source_record(row),
    )
    d01 = execute_stage(
        parent=source.envelope,
        clock=clock,
        producer_component="D01",
        producer_version="0.2",
        payload_type="D01OutputPair",
        payload_version="0.2.0",
        call=lambda: harness.d01_model.step(observation),
        payload_adapter=lambda pair: d01_payload(pair[0], pair[1]),
        scientific_id_adapter=lambda pair: scientific_ids(pair, "D01OutputPair"),
    )
    d02 = execute_stage(
        parent=d01.envelope,
        clock=clock,
        producer_component="D02",
        producer_version="0.2",
        payload_type="ReturnShape",
        payload_version="0.2",
        call=lambda: build_return_shape(*d01.output),
        scientific_id_adapter=lambda output: scientific_ids(output, "ReturnShape"),
    )
    d04 = execute_stage(
        parent=d02.envelope,
        clock=clock,
        producer_component="D04",
        producer_version="0.2.1",
        payload_type="EnvelopeEvaluation",
        payload_version="0.2.1",
        call=lambda: harness.envelope.process(d02.output, context),
        scientific_id_adapter=lambda output: scientific_ids(output, "EnvelopeEvaluation"),
    )
    d03_input = D03Input(d04_evaluation=d04.output, decision_context=control)
    d03 = execute_stage(
        parent=d04.envelope,
        clock=clock,
        producer_component="D03",
        producer_version="0.1",
        payload_type="DecisionRecord",
        payload_version="0.1",
        call=lambda: evaluate_decision(d03_input),
        scientific_id_adapter=lambda output: scientific_ids(output, "DecisionRecord"),
    )
    decision = d03.output.model_dump(mode="json")
    controller = execute_stage(
        parent=d03.envelope,
        clock=clock,
        producer_component="POSITION_TRANSITION_CONTROLLER",
        producer_version="0.1",
        payload_type="PositionTransitionPlan",
        payload_version="0.1",
        call=lambda: harness.controller.derive_transition_plan(
            decision,
            controller_snapshot,
            decision["input_fingerprint"],
        ),
        scientific_id_adapter=lambda output: scientific_ids(output, "PositionTransitionPlan"),
    )
    if controller.output is None:
        raise RuntimeError(f"{target['label']} controller rejected decision")
    direct_stop_ns = clock.monotonic_ns()

    envelopes = [source.envelope, d01.envelope, d02.envelope, d04.envelope, d03.envelope, controller.envelope]
    if len({item.observation_id for item in envelopes}) != 1:
        raise RuntimeError(f"{target['label']} observation identity changed")
    if any(child.parent_event_id != parent.event_id for parent, child in zip(envelopes, envelopes[1:])):
        raise RuntimeError(f"{target['label']} parent lineage failed")

    if controller.output.action_authorized:
        harness.actual_position = harness.actual_position.advance_after_execution(
            controller.output.ordered_execution_verbs
        )
    after = {
        "d01": d01_state_snapshot(harness),
        "d02": {"stateful": False},
        "d04": d04_state_snapshot(harness),
        "d03": {"stateful": False},
        "controller": controller_state_snapshot(harness),
    }

    stage_durations = {
        name: envelope.processing_duration_ns
        for name, envelope in zip(("E0", "D01", "D02", "D04", "D03", "POSITION_CONTROLLER"), envelopes)
    }
    math_sum = sum(stage_durations[name] for name in ("D01", "D02", "D04", "D03", "POSITION_CONTROLLER"))
    all_sum = sum(stage_durations.values())
    direct = direct_stop_ns - direct_start_ns

    return normalized_state(
        {
            "label": target["label"],
            "selection": {
                "physical_csv_row": target["physical_row"],
                "data_observation_number": target["physical_row"] - 1,
                "zero_based_data_index": target["index"],
                "source_row_number": int(row["source_row_number"]),
                "market_event_time_utc": target["time"],
                "ohlcv": {name: float(row[name]) for name in ("open", "high", "low", "close", "volume")},
            },
            "source_payload": normalized_source_record(row),
            "mathematics": {
                "d01_dmo": d01.output[0],
                "d01_fmo": d01.output[1],
                "d02_return_shape": d02.output,
                "d04_evaluation": d04.output,
                "d03_decision": d03.output,
                "position_controller_plan": controller.output,
            },
            "state_before": before,
            "state_after": after,
            "temporal_lineage": [
                event_record(stage, envelope)
                for stage, envelope in zip(("E0", "D01", "D02", "D04", "D03", "POSITION_CONTROLLER"), envelopes)
            ],
            "timing": {
                "direct_boundary": {
                    "start": "immediately before create_source_event for this target",
                    "stop": "immediately after complete E5 StageResult and envelope return to caller",
                    "clock_domain_id": clock.clock_domain_id,
                    "primitive": "time.perf_counter_ns() through SystemClock.monotonic_ns",
                    "start_monotonic_ns": direct_start_ns,
                    "stop_monotonic_ns": direct_stop_ns,
                },
                "stage_duration_ns": stage_durations,
                "t_math_components_ns": math_sum,
                "t_all_measured_stages_ns": all_sum,
                "t_direct_ns": direct,
                "delta_math_ns": direct - math_sum,
                "delta_all_stages_ns": direct - all_sum,
                "t_direct_us": direct / 1_000.0,
                "t_direct_ms": direct / 1_000_000.0,
            },
            "checks": {
                "observation_id_preserved": True,
                "parent_lineage_complete": True,
                "market_time_preserved": all(item.market_event_time_utc == target["time"] for item in envelopes),
                "all_durations_nonnegative_integers": all(
                    isinstance(item.processing_duration_ns, int) and item.processing_duration_ns >= 0
                    for item in envelopes
                ),
            },
        }
    ), direct_stop_ns


def test_001_comparison(t1: dict[str, Any]) -> dict[str, Any]:
    prior = json.loads(TEST_001_TRACE_PATH.read_text(encoding="utf-8"))
    current = t1["mathematics"]
    comparisons = {
        "D01": current["d01_dmo"] == prior["d01_output"]["dmo"] and current["d01_fmo"] == prior["d01_output"]["fmo"],
        "D02": current["d02_return_shape"] == prior["d02_output"],
        "D04": current["d04_evaluation"] == prior["d04_output"],
        "D03_POSITION": current["d03_decision"]["desired_position_state"] == prior["d03_output"]["desired_position_state"],
        "POSITION_CONTROLLER_DECISION": current["position_controller_plan"]["ordered_execution_verbs"] == prior["controller_output"]["ordered_execution_verbs"],
    }
    return {
        "field_equivalence": comparisons,
        "all_deterministically_comparable_results_match": all(comparisons.values()),
        "timing_values_required_to_match": False,
        "execution_ids_required_to_match": False,
    }


def run() -> dict[str, Any]:
    header, rows = read_through_targets()
    harness = RealCausalReplayHarness(SOURCE_PATH, max_rows=10, entity_id="SPY")
    warmup_result = warmup(harness, rows[:8])
    clock = SystemClock()

    t1, t1_stop_ns = process_target(harness, clock, rows[8], TARGETS[0])
    t1_after_for_t2 = {
        "d01": t1["state_after"]["d01"],
        "d04": t1["state_after"]["d04"],
        "controller": t1["state_after"]["controller"],
    }
    t2, _ = process_target(harness, clock, rows[9], TARGETS[1])
    inter_observation_gap_ns = (
        t2["timing"]["direct_boundary"]["start_monotonic_ns"] - t1_stop_ns
    )

    if t2["state_before"]["d01"] != t1_after_for_t2["d01"]:
        raise RuntimeError("D01 state discontinuity between t1 and t2")
    if t2["state_before"]["d04"] != t1_after_for_t2["d04"]:
        raise RuntimeError("D04 state discontinuity between t1 and t2")
    if t2["state_before"]["controller"] != t1_after_for_t2["controller"]:
        raise RuntimeError("controller state discontinuity between t1 and t2")

    t1_events = {item["event_id"] for item in t1["temporal_lineage"]}
    t2_parents = {item["parent_event_id"] for item in t2["temporal_lineage"] if item["parent_event_id"] is not None}
    cross_parents = sorted(t1_events & t2_parents)
    t1_observation = t1["temporal_lineage"][0]["observation_id"]
    t2_observation = t2["temporal_lineage"][0]["observation_id"]
    market_interval_seconds = int(
        (
            datetime.fromisoformat(TARGETS[1]["time"].replace("Z", "+00:00"))
            - datetime.fromisoformat(TARGETS[0]["time"].replace("Z", "+00:00"))
        ).total_seconds()
    )

    return normalized_state(
        {
            "test_id": "APTF_TEST_002_TWO_OBSERVATIONS_V0_1",
            "source": {
                "path": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
                "header": header,
                "rows_read": 10,
                "last_zero_based_data_index_read": 9,
                "future_rows_read": 0,
                "target_count": 2,
                "market_observation_interval_seconds": market_interval_seconds,
            },
            "warmup": warmup_result,
            "ordering": {
                "mode": "single-threaded synchronous sequential",
                "sequence": ["E0(t1)", "E1(t1)", "E2(t1)", "E3(t1)", "E4(t1)", "E5(t1)", "E0(t2)", "E1(t2)", "E2(t2)", "E3(t2)", "E4(t2)", "E5(t2)"],
                "artificial_wait_inserted": False,
                "inter_observation_runtime_gap_ns": inter_observation_gap_ns,
                "clock_domain_id": clock.clock_domain_id,
            },
            "targets": [t1, t2],
            "identity": {
                "t1_observation_id": t1_observation,
                "t2_observation_id": t2_observation,
                "distinct_observation_ids": t1_observation != t2_observation,
                "cross_observation_parent_links": cross_parents,
            },
            "continuity": {
                "d01_after_t1_equals_before_t2": t1_after_for_t2["d01"] == t2["state_before"]["d01"],
                "d04_after_t1_equals_before_t2": t1_after_for_t2["d04"] == t2["state_before"]["d04"],
                "controller_after_t1_equals_before_t2": t1_after_for_t2["controller"] == t2["state_before"]["controller"],
                "unauthorized_reset": False,
            },
            "test_001_non_drift": test_001_comparison(t1),
            "overhead_accounting": {
                "measured_separately": ["each E0-E5 frozen stage call interval", "outer direct E0-entry through E5-return interval", "inter-observation runtime gap"],
                "uninstrumented_inside_direct_boundary": [
                    "execution UUID generation before each stage timer",
                    "payload adapter normalization after each successful stage timer",
                    "canonical payload serialization and SHA256 hashing",
                    "deterministic event ID generation",
                    "TemporalEventEnvelope construction and validation",
                    "parent/child handoff and Python call overhead",
                    "target-local D03Input and controller-call argument construction between stage timers",
                ],
                "not_present": ["network", "database", "queue", "pub/sub", "asynchronous overlap", "artificial market-time sleep", "Azure", "broker input"],
                "numeric_sub_breakdown_available": False,
                "diagnostic_perturbation": "outer timer sampling adds small overhead; state capture and report generation are outside each direct target boundary",
                "resolution_statement": "integer nanosecond resolution; no nanosecond accuracy claim",
            },
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
