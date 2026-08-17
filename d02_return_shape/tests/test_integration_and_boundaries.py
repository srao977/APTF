from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path
import subprocess
import sys

from d01.v02.model import D01V02Model
from d01.v02.observations import NormalizedObservation
from d01.v02.outputs import DMOOutput, FMOSample, FMOOutput
from d02.v02 import build_return_shape


WORKSPACE = Path(__file__).resolve().parents[2]


def observation(sequence: int, event_time: float, price: float) -> NormalizedObservation:
    return NormalizedObservation(
        entity_id="TEST:D02:INTEGRATION",
        event_time=event_time,
        receive_time=event_time,
        sequence_id=sequence,
        price=price,
        volume=1000.0,
        source_quality=1.0,
        availability_mask={"price": True, "volume": True},
    )


def actual_output():
    model = D01V02Model(entity_id="TEST:D02:INTEGRATION")
    output = None
    for index in range(1, 12):
        output = model.step(observation(index, float(index), 100.0 + index * 0.02))
    assert output is not None
    return output


def test_actual_d01_output_types_integrate_without_adapter() -> None:
    dmo, fmo = actual_output()
    assert isinstance(dmo, DMOOutput)
    assert isinstance(fmo, FMOOutput)
    assert all(isinstance(sample, FMOSample) for sample in fmo.samples)
    result = build_return_shape(dmo, fmo)
    assert result.model_time == dmo.model_time == fmo.model_time
    assert result.entity_id == dmo.entity_id == fmo.entity_id
    assert len(result.forward_samples) == len(fmo.samples) == 8


def test_d04_frozen_interface_accepts_all_implemented_fields() -> None:
    schema = json.loads((WORKSPACE / "D04_MODERNIZED_INTERFACE_SCHEMA_V0_2.json").read_text(encoding="utf-8"))
    design = json.loads((WORKSPACE / "D02_RETURNSHAPE_CANONICAL_SCHEMA_V0_2.json").read_text(encoding="utf-8"))
    implemented = {field.name for field in fields(build_return_shape(*actual_output()))}
    frozen = {field["canonical_name"] for field in design["fields"]}
    assert implemented == frozen
    assert schema["frozen_return_shape"]["field_count"] == len(implemented) == 17
    assert schema["frozen_return_shape"]["freeze_sha256"] == "6FC2D51FDA74284B7866B67DE2B6EA7025F9F3599606E2A9945FCF53D07A7CE6"


def test_no_legacy_or_d03_fields() -> None:
    names = {field.name.lower() for field in fields(build_return_shape(*actual_output()))}
    prohibited = {
        "shape_quality", "magnitude_score", "forward_support", "persistence_score",
        "decay_score", "expected_lifetime", "reversal_risk", "attractiveness",
        "confidence_score", "opportunity_score", "reward", "risk_reward",
        "buy", "sell", "hold", "candidate_id", "active", "position_open",
    }
    assert names.isdisjoint(prohibited)


def test_same_process_determinism() -> None:
    dmo, fmo = actual_output()
    outputs = [build_return_shape(dmo, fmo).to_dict() for _ in range(10)]
    assert outputs == [outputs[0]] * 10


def test_fresh_process_determinism() -> None:
    code = r'''
import json
from d01.v02.model import D01V02Model
from d01.v02.observations import NormalizedObservation
from d02.v02 import build_return_shape
model = D01V02Model("TEST:D02:SUBPROCESS")
result = None
for index in range(1, 6):
    obs = NormalizedObservation(entity_id="TEST:D02:SUBPROCESS", event_time=float(index), receive_time=float(index), sequence_id=index, price=100.0 + index * 0.01, volume=1000.0, source_quality=1.0, availability_mask={"price": True, "volume": True})
    result = build_return_shape(*model.step(obs))
print(json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":")))
'''
    env_path = f"{WORKSPACE / 'd02_return_shape' / 'src'};{WORKSPACE / 'd01_adaptive_parametric_model' / 'src'}"
    command = [sys.executable, "-c", code]
    first = subprocess.check_output(command, text=True, env={"PYTHONPATH": env_path})
    second = subprocess.check_output(command, text=True, env={"PYTHONPATH": env_path})
    assert first == second