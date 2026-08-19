from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical_json import canonical_sha256, normalize_semantic
from .clock import Clock, SystemClock
from .payload_serialization import d01_payload, normalized_source_record, scientific_ids
from .stage_wrappers import StageResult, create_source_event, execute_stage


ROOT = Path(__file__).resolve().parents[3]
TARGET_TIMESTAMP = "2022-09-30T08:16:00Z"
SOURCE_PATH = ROOT / "data" / "market" / "normalized" / "SPY_1min_normalized_v0_1.csv"
D04_CONFIG_PATH = ROOT / "d04_trading_envelope" / "config" / "default.yaml"
SOURCE_STREAM_ID = (
    "aptf:source:v1:FirstRateData:SPY_1min_firstratedata:normalized_v0_1:sha256:"
    "73957227a0cc09103f7ca5ff62b011edd7c80c220017d91fb97c5fb5e6a1055d"
)
ACTUAL_POSITION_SNAPSHOT = {
    "state": "FLAT",
    "version": 0,
    "identity": "TEMPORAL_PROOF_ACTUAL_FLAT_V0",
}


def _bootstrap_frozen_imports() -> None:
    for path in (
        ROOT / "d01_adaptive_parametric_model" / "src",
        ROOT / "d02_return_shape" / "src",
        ROOT / "d04_trading_envelope" / "src",
        ROOT / "d03_decision_control" / "src",
        ROOT / "position_transition_controller",
    ):
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)


_bootstrap_frozen_imports()

from aptf_d04.cli.main import build_envelope  # noqa: E402
from aptf_d04.models.envelope_context import EnvelopeContext  # noqa: E402
from d01.v02.model import D01V02Model  # noqa: E402
from d02.v02.builder import build_return_shape  # noqa: E402
from d03.v01 import (  # noqa: E402
    D03Input,
    DecisionContext,
    PendingTargetState,
    PositionState,
    evaluate_decision,
)
from position_transition_controller import PositionTransitionController  # noqa: E402
from real_causal_replay_harness_v0_2 import RealCausalReplayHarness  # noqa: E402


@dataclass
class FrozenState:
    d01: D01V02Model
    envelope: Any
    mapper: Any


def _new_frozen_state() -> FrozenState:
    mapper = RealCausalReplayHarness.__new__(RealCausalReplayHarness)
    mapper.entity_id = "SPY"
    envelope, _ = build_envelope(D04_CONFIG_PATH)
    return FrozenState(d01=D01V02Model(entity_id="SPY"), envelope=envelope, mapper=mapper)


def _read_target_prefix() -> tuple[list[dict[str, str]], dict[str, str], int]:
    warmup: list[dict[str, str]] = []
    with SOURCE_PATH.open(newline="", encoding="utf-8") as handle:
        for index, row in enumerate(csv.DictReader(handle)):
            if row["event_timestamp_utc"] == TARGET_TIMESTAMP:
                return warmup, row, index
            warmup.append(row)
    raise RuntimeError(f"target not found: {TARGET_TIMESTAMP}")


def _observation(state: FrozenState, row: dict[str, str], index: int) -> Any:
    observation = RealCausalReplayHarness.source_row_to_normalized_observation(
        state.mapper, row, index
    )
    if observation is None:
        raise RuntimeError(f"source mapping failed at normalized ordinal {index}")
    return observation


def _context(observation: Any) -> EnvelopeContext:
    return EnvelopeContext.production(
        evaluation_time=observation.event_time,
    )


def _warmup(state: FrozenState, rows: list[dict[str, str]]) -> None:
    for index, row in enumerate(rows):
        observation = _observation(state, row, index)
        dmo, fmo = state.d01.step(observation)
        shape = build_return_shape(dmo, fmo)
        state.envelope.process(shape, _context(observation))


def _state_snapshot(state: FrozenState) -> dict[str, Any]:
    d01_state = state.d01.state
    d04 = state.envelope
    return normalize_semantic(
        {
            "D01": {
                "state_hash": state.d01._state_hash(),
                "sequence": d01_state.sequence,
                "model_time": d01_state.model_time,
                "last_event_time": d01_state.last_event_time,
            },
            "D04": {
                "current_state": d04.current_state,
                "current_aperture": d04.current_aperture,
                "current_entity_id": d04.current_entity_id,
                "current_model_time": d04.current_model_time,
                "current_candidate": d04.current_candidate,
                "consecutive_open_qualifying": d04.hysteresis.consecutive_open_qualifying,
                "consecutive_close_qualifying": d04.hysteresis.consecutive_close_qualifying,
            },
        }
    )


def _decision_input(evaluation: Any, observation: Any) -> D03Input:
    return D03Input(
        d04_evaluation=evaluation,
        decision_context=DecisionContext(
            context_time=observation.event_time,
            entity_id="SPY",
            actual_position_state=PositionState.FLAT,
            position_candidate_id=None,
            position_source_return_shape_model_time=None,
            pending_target_state=PendingTargetState.NONE,
            pending_decision_id=None,
            execution_available=True,
            system_enabled=True,
            trading_enabled=True,
            emergency_flatten=False,
            control_state_valid=True,
        ),
    )


def _run_unwrapped(
    state: FrozenState,
    row: dict[str, str],
    index: int,
) -> dict[str, Any]:
    observation = _observation(state, row, index)
    dmo, fmo = state.d01.step(observation)
    shape = build_return_shape(dmo, fmo)
    evaluation = state.envelope.process(shape, _context(observation))
    decision = evaluate_decision(_decision_input(evaluation, observation))
    decision_hash = canonical_sha256(decision)
    plan = PositionTransitionController().derive_transition_plan(
        decision.model_dump(mode="json"),
        dict(ACTUAL_POSITION_SNAPSHOT),
        decision_hash,
    )
    if plan is None:
        raise RuntimeError("position controller rejected proof decision")
    return {
        "D01OutputPair": d01_payload(dmo, fmo),
        "ReturnShape": normalize_semantic(shape),
        "EnvelopeEvaluation": normalize_semantic(evaluation),
        "DecisionRecord": normalize_semantic(decision),
        "PositionTransitionPlan": normalize_semantic(plan),
    }


def _run_wrapped(
    state: FrozenState,
    row: dict[str, str],
    index: int,
    clock: Clock,
) -> tuple[list[Any], dict[str, Any]]:
    source = create_source_event(
        clock=clock,
        source_stream_id=SOURCE_STREAM_ID,
        sequence_number=index,
        instrument_id="SPY",
        market_event_time_utc=TARGET_TIMESTAMP,
        market_event_time_role="PROVIDER_EVENT",
        payload_type="NormalizedObservationSourceRecord",
        payload_version="v0_1",
        source_builder=lambda: normalized_source_record(row),
    )
    observation = _observation(state, row, index)
    d01_result = execute_stage(
        parent=source.envelope,
        clock=clock,
        producer_component="D01",
        producer_version="0.2",
        payload_type="D01OutputPair",
        payload_version="0.2.0",
        call=lambda: state.d01.step(observation),
        payload_adapter=lambda pair: d01_payload(pair[0], pair[1]),
        scientific_id_adapter=lambda pair: scientific_ids(pair, "D01OutputPair"),
    )
    d02_result = execute_stage(
        parent=d01_result.envelope,
        clock=clock,
        producer_component="D02",
        producer_version="0.2",
        payload_type="ReturnShape",
        payload_version="0.2",
        call=lambda: build_return_shape(*d01_result.output),
        scientific_id_adapter=lambda output: scientific_ids(output, "ReturnShape"),
    )
    d04_result = execute_stage(
        parent=d02_result.envelope,
        clock=clock,
        producer_component="D04",
        producer_version="0.2.1",
        payload_type="EnvelopeEvaluation",
        payload_version="0.2.1",
        call=lambda: state.envelope.process(d02_result.output, _context(observation)),
        scientific_id_adapter=lambda output: scientific_ids(output, "EnvelopeEvaluation"),
    )
    d03_result = execute_stage(
        parent=d04_result.envelope,
        clock=clock,
        producer_component="D03",
        producer_version="0.1",
        payload_type="DecisionRecord",
        payload_version="0.1",
        call=lambda: evaluate_decision(_decision_input(d04_result.output, observation)),
        scientific_id_adapter=lambda output: scientific_ids(output, "DecisionRecord"),
    )
    controller = PositionTransitionController()
    pc_result = execute_stage(
        parent=d03_result.envelope,
        clock=clock,
        producer_component="POSITION_TRANSITION_CONTROLLER",
        producer_version="0.1",
        payload_type="PositionTransitionPlan",
        payload_version="0.1",
        call=lambda: controller.derive_transition_plan(
            d03_result.output.model_dump(mode="json"),
            dict(ACTUAL_POSITION_SNAPSHOT),
            d03_result.envelope.payload_sha256 or "",
        ),
        scientific_id_adapter=lambda output: scientific_ids(output, "PositionTransitionPlan"),
    )
    if pc_result.output is None:
        raise RuntimeError("position controller rejected wrapped proof decision")
    envelopes = [
        source.envelope,
        d01_result.envelope,
        d02_result.envelope,
        d04_result.envelope,
        d03_result.envelope,
        pc_result.envelope,
    ]
    outputs = {
        "D01OutputPair": normalize_semantic(d01_result.envelope.payload),
        "ReturnShape": normalize_semantic(d02_result.envelope.payload),
        "EnvelopeEvaluation": normalize_semantic(d04_result.envelope.payload),
        "DecisionRecord": normalize_semantic(d03_result.envelope.payload),
        "PositionTransitionPlan": normalize_semantic(pc_result.envelope.payload),
    }
    return envelopes, outputs


def run_single_observation_proof(clock: Clock | None = None) -> dict[str, Any]:
    warmup_rows, target_row, target_index = _read_target_prefix()
    if target_index != 16 or target_row["source_row_number"] != "17":
        raise RuntimeError("target source sequence mapping changed")
    expected = ["366.0", "366.0", "366.0", "366.0", "616.0"]
    actual = [target_row[name] for name in ("open", "high", "low", "close", "volume")]
    if actual != expected:
        raise RuntimeError("target OHLCV mismatch")

    baseline_state = _new_frozen_state()
    wrapped_state = _new_frozen_state()
    _warmup(baseline_state, warmup_rows)
    _warmup(wrapped_state, warmup_rows)

    baseline = _run_unwrapped(baseline_state, target_row, target_index)
    envelopes, wrapped = _run_wrapped(
        wrapped_state,
        target_row,
        target_index,
        clock or SystemClock(),
    )
    equivalence = {
        name: {
            "field_equivalent": baseline[name] == wrapped[name],
            "baseline_sha256": canonical_sha256(baseline[name]),
            "wrapped_sha256": canonical_sha256(wrapped[name]),
            "hash_equivalent": canonical_sha256(baseline[name])
            == canonical_sha256(wrapped[name]),
        }
        for name in baseline
    }
    baseline_state_snapshot = _state_snapshot(baseline_state)
    wrapped_state_snapshot = _state_snapshot(wrapped_state)
    proof_rows = []
    for stage, envelope in zip(("E0", "E1", "E2", "E3", "E4", "E5"), envelopes):
        proof_rows.append(
            {
                "stage": stage,
                "event_id": envelope.event_id,
                "execution_id": envelope.execution_id,
                "observation_id": envelope.observation_id,
                "parent_event_id": envelope.parent_event_id,
                "source_stream_id": envelope.source_stream_id,
                "sequence_number": envelope.sequence_number,
                "market_event_time_utc": envelope.market_event_time_utc,
                "received_at_utc": envelope.as_dict()["received_at_utc"],
                "emitted_at_utc": envelope.as_dict()["emitted_at_utc"],
                "processing_duration_ns": envelope.processing_duration_ns,
                "processing_duration_us": envelope.processing_duration_us,
                "processing_duration_ms": envelope.processing_duration_ms,
                "telemetry_flags": list(envelope.telemetry_flags),
                "payload_type": envelope.payload_type,
                "payload_sha256": envelope.payload_sha256,
                "status": envelope.status,
                "clock_domain_id": envelope.clock_domain_id,
                "scientific_ids": normalize_semantic(envelope.scientific_ids),
            }
        )
    return {
        "proof_id": "APTF_SINGLE_OBSERVATION_TEMPORAL_PROOF_V0_2",
        "target_count": 1,
        "setup_rows": len(warmup_rows),
        "last_source_timestamp_read": target_row["event_timestamp_utc"],
        "target_source_row": normalized_source_record(target_row),
        "source_stream_id": SOURCE_STREAM_ID,
        "sequence_mapping": {
            "aptf_sequence_number": target_index,
            "normalized_source_row_number": int(target_row["source_row_number"]),
            "semantic": "zero-based normalized event_timestamp_utc ordering ordinal",
        },
        "events": proof_rows,
        "payload_non_drift": equivalence,
        "state_non_drift": {
            "field_equivalent": baseline_state_snapshot == wrapped_state_snapshot,
            "baseline_sha256": canonical_sha256(baseline_state_snapshot),
            "wrapped_sha256": canonical_sha256(wrapped_state_snapshot),
            "hash_equivalent": canonical_sha256(baseline_state_snapshot)
            == canonical_sha256(wrapped_state_snapshot),
            "baseline": baseline_state_snapshot,
            "wrapped": wrapped_state_snapshot,
        },
        "terminal_payload_type": envelopes[-1].payload_type,
        "terminal_verbs": wrapped["PositionTransitionPlan"]["ordered_execution_verbs"],
        "control_context": {
            "actual_position_state": "FLAT",
            "pending_target_state": "NONE",
            "execution_available": True,
            "system_enabled": True,
            "trading_enabled": True,
            "emergency_flatten": False,
            "control_state_valid": True,
        },
        "d04_context_authority": {
            "active": ["evaluation_time"],
            "unavailable_fields_are_null": True,
            "data_quality_responsibility": "UPSTREAM_OBSERVATION_ADMISSION",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the one-observation V0.2 temporal proof")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_single_observation_proof()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
