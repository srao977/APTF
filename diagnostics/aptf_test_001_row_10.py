from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
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
from aptf_runtime.payload_serialization import (
    d01_payload,
    normalized_source_record,
    scientific_ids,
)
from aptf_runtime.stage_wrappers import create_source_event, execute_stage
from d02.v02.builder import build_return_shape
from d03.v01 import D03Input, DecisionContext, PendingTargetState, PositionState, evaluate_decision
from position_transition_controller import PositionTransitionController
from real_causal_replay_harness_v0_2 import RealCausalReplayHarness


SOURCE_PATH = ROOT / "data" / "market" / "normalized" / "SPY_1min_normalized_v0_1.csv"
SOURCE_STREAM_ID = (
    "aptf:source:v1:FirstRateData:SPY_1min_firstratedata:normalized_v0_1:sha256:"
    "73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d"
)
TARGET_INDEX = 8
TARGET_PHYSICAL_ROW = 10
TARGET_TIME = "2022-09-30T08:08:00Z"


def read_through_target() -> tuple[list[str], list[dict[str, str]]]:
    with SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(islice(reader, TARGET_INDEX + 1))
        header = list(reader.fieldnames or [])
    if len(rows) != 9:
        raise RuntimeError("physical row 10 could not be resolved")
    target = rows[-1]
    if target["event_timestamp_utc"] != TARGET_TIME or target["source_row_number"] != "9":
        raise RuntimeError("physical row 10 identity mismatch")
    return header, rows


def advance_warmup(harness: RealCausalReplayHarness, rows: list[dict[str, str]]) -> dict[str, Any]:
    initial = harness.actual_position.as_dict()
    authorized_advancements = 0
    plans = 0
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
        plans += 1
        if plan.action_authorized:
            harness.actual_position = harness.actual_position.advance_after_execution(
                plan.ordered_execution_verbs
            )
            authorized_advancements += 1
    return {
        "rows_consumed": len(rows),
        "data_indices": [0, len(rows) - 1] if rows else [],
        "initial_actual_position": initial,
        "target_pre_state_actual_position": harness.actual_position.as_dict(),
        "plans_generated": plans,
        "authorized_semantic_advancements": authorized_advancements,
        "position_source": "RealCausalReplayHarness explicit REPLAY_INITIAL_CONDITION plus semantic carry-forward",
        "broker_sourced": False,
    }


def d01_prior_state(harness: RealCausalReplayHarness) -> dict[str, Any]:
    state = harness.d01_model.state
    return normalize_semantic(
        {
            "state_type": type(state).__name__,
            "sequence": state.sequence,
            "adaptive_reference": state.adaptive_reference,
            "adaptive_scale": state.adaptive_scale,
            "volume_reference": state.volume_reference,
            "prev_level": state.prev_level,
            "prev_velocity": state.prev_velocity,
            "last_event_time": state.last_event_time,
            "parameter_state": state.parameter_state,
            "state_vector": state.state_vector,
            "half_life_state": state.half_life_state,
            "clipping_count": state.clipping_count,
            "nonfinite_count": state.nonfinite_count,
            "parameter_bound_hits": state.parameter_bound_hits,
            "innovation_extreme_count": state.innovation_extreme_count,
            "data_gap_count": state.data_gap_count,
        }
    )


def d04_prior_state(harness: RealCausalReplayHarness) -> dict[str, Any]:
    envelope = harness.envelope
    return normalize_semantic(
        {
            "current_state": envelope.current_state,
            "current_aperture": envelope.current_aperture,
            "current_entity_id": envelope.current_entity_id,
            "current_model_time": envelope.current_model_time,
            "current_candidate": envelope.current_candidate,
            "consecutive_open_qualifying": envelope.hysteresis.consecutive_open_qualifying,
            "consecutive_close_qualifying": envelope.hysteresis.consecutive_close_qualifying,
        }
    )


def envelope_context(observation: Any) -> EnvelopeContext:
    return EnvelopeContext.production(
        evaluation_time=observation.event_time,
    )


def decision_context(harness: RealCausalReplayHarness, observation: Any) -> DecisionContext:
    actual = harness.actual_position.state
    candidate_id = None
    candidate_source_time = None
    if actual in {"LONG", "SHORT"}:
        candidate_id = f"D04C|{harness.entity_id}|0.0|0.0"
        candidate_source_time = 0.0
    return DecisionContext(
        context_time=observation.event_time,
        entity_id=harness.entity_id,
        actual_position_state=PositionState(actual),
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


def event_metadata(envelope: Any) -> dict[str, Any]:
    value = envelope.as_dict()
    value.pop("payload")
    return value


def run() -> dict[str, Any]:
    header, rows = read_through_target()
    target = rows[-1]
    harness = RealCausalReplayHarness(SOURCE_PATH, max_rows=9, entity_id="SPY")
    warmup = advance_warmup(harness, rows[:-1])
    prior_d01 = d01_prior_state(harness)
    prior_d04 = d04_prior_state(harness)

    observation = harness.source_row_to_normalized_observation(target, TARGET_INDEX)
    if observation is None:
        raise RuntimeError("target observation normalization failed")
    effective_observation = observation.with_defaults()
    context = envelope_context(observation)
    control_context = decision_context(harness, observation)
    actual_snapshot = harness.actual_position.as_dict()
    clock = SystemClock()

    source = create_source_event(
        clock=clock,
        source_stream_id=SOURCE_STREAM_ID,
        sequence_number=TARGET_INDEX,
        instrument_id="SPY",
        market_event_time_utc=TARGET_TIME,
        market_event_time_role="PROVIDER_EVENT",
        payload_type="NormalizedObservationSourceRecord",
        payload_version="v0_1",
        source_builder=lambda: normalized_source_record(target),
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
    d03_input = D03Input(d04_evaluation=d04.output, decision_context=control_context)
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
    decision_dict = d03.output.model_dump(mode="json")
    controller = PositionTransitionController()
    controller_result = execute_stage(
        parent=d03.envelope,
        clock=clock,
        producer_component="POSITION_TRANSITION_CONTROLLER",
        producer_version="0.1",
        payload_type="PositionTransitionPlan",
        payload_version="0.1",
        call=lambda: controller.derive_transition_plan(
            decision_dict,
            actual_snapshot,
            decision_dict["input_fingerprint"],
        ),
        scientific_id_adapter=lambda output: scientific_ids(output, "PositionTransitionPlan"),
    )
    if controller_result.output is None:
        raise RuntimeError("target controller rejected decision")

    envelopes = [
        source.envelope,
        d01.envelope,
        d02.envelope,
        d04.envelope,
        d03.envelope,
        controller_result.envelope,
    ]
    if len({envelope.observation_id for envelope in envelopes}) != 1:
        raise RuntimeError("target observation identity changed")
    if any(
        child.parent_event_id != parent.event_id
        for parent, child in zip(envelopes, envelopes[1:])
    ):
        raise RuntimeError("target parent lineage broken")

    return normalize_semantic(
        {
            "test_id": "APTF_TEST_001_ROW_10_V0_1",
            "selection": {
                "csv": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
                "header": header,
                "physical_csv_row": TARGET_PHYSICAL_ROW,
                "header_row": 1,
                "data_observation_number": 9,
                "zero_based_data_index": TARGET_INDEX,
                "source_row_number": int(target["source_row_number"]),
                "last_data_index_read": TARGET_INDEX,
                "future_rows_read": 0,
                "target_confirmed": True,
            },
            "raw_source_row": dict(target),
            "normalized_source_payload": normalized_source_record(target),
            "d01_input": {
                "received_observation": asdict(observation),
                "effective_observation_after_with_defaults": asdict(effective_observation),
                "prior_runtime_state_values_read": prior_d01,
            },
            "warmup_and_position_provenance": warmup,
            "d01_output": {"dmo": d01.output[0], "fmo": d01.output[1]},
            "d02_input": {"dmo": d01.output[0], "fmo": d01.output[1]},
            "d02_output": d02.output,
            "d04_input": {
                "return_shape": d02.output,
                "envelope_context": context,
                "prior_envelope_state": prior_d04,
                "implementation_configuration": {
                    "aperture_alpha": harness.envelope.aperture_model.alpha,
                    "open_threshold": harness.envelope.hysteresis.config.open_threshold,
                    "close_threshold": harness.envelope.hysteresis.config.close_threshold,
                    "open_persistence_observations": harness.envelope.hysteresis.config.open_persistence_observations,
                    "close_persistence_observations": harness.envelope.hysteresis.config.close_persistence_observations,
                },
            },
            "d04_output": d04.output,
            "d03_input": d03_input,
            "d03_output": d03.output,
            "controller_input": {
                "d03_decision": decision_dict,
                "actual_position_snapshot": actual_snapshot,
                "d03_decision_hash_argument": decision_dict["input_fingerprint"],
                "hash_argument_source": "existing RealCausalReplayHarness v0.2 behavior",
            },
            "controller_output": controller_result.output,
            "telemetry": [
                {"stage": stage, **event_metadata(envelope)}
                for stage, envelope in zip(("E0", "E1", "E2", "E3", "E4", "E5"), envelopes)
            ],
            "checks": {
                "target_count": 1,
                "observation_id_preserved": True,
                "parent_lineage_complete": True,
                "all_durations_nonnegative": all(
                    envelope.processing_duration_ns >= 0 for envelope in envelopes
                ),
                "all_market_times_preserved": all(
                    envelope.market_event_time_utc == TARGET_TIME for envelope in envelopes
                ),
                "terminal_payload_complete": controller_result.envelope.payload_type
                == "PositionTransitionPlan",
                "target_payload_hashes": {
                    envelope.payload_type: envelope.payload_sha256 for envelope in envelopes
                },
                "trace_sha256": canonical_sha256(
                    {
                        "observation": asdict(observation),
                        "d01": d01_payload(*d01.output),
                        "d02": d02.output,
                        "d04": d04.output,
                        "d03": d03.output,
                        "controller": controller_result.output,
                    }
                ),
            },
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
