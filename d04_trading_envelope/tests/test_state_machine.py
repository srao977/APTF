from pathlib import Path

from aptf_d04.cli.main import build_envelope
from aptf_d04.inputs.scenario_loader import load_scenario
from aptf_d04.inputs.synthetic_generator import SyntheticGenerator
from aptf_d04.models.enums import EnvelopeState


ROOT = Path(__file__).resolve().parents[1]


def test_same_return_shape_id_versions_monotonic() -> None:
    envelope, _cfg = build_envelope(ROOT / "config" / "default.yaml")
    obs = SyntheticGenerator(load_scenario(ROOT / "scenarios" / "02_shape_becomes_capturable.yaml")).generate()

    ids = [o.return_shape.return_shape_id for o in obs]
    versions = [o.return_shape.version for o in obs]
    assert len(set(ids)) == 1
    assert versions == sorted(versions)


def test_no_threshold_chatter() -> None:
    envelope, _cfg = build_envelope(ROOT / "config" / "default.yaml")
    obs = SyntheticGenerator(load_scenario(ROOT / "scenarios" / "05_threshold_noise_hysteresis.yaml")).generate()
    transitions = []
    for o in obs:
        ev = envelope.process(o.return_shape, o.context)
        transitions.append((ev.previous_state, ev.new_state))

    # Reject pathological alternating OPEN/CLOSED oscillation.
    alternating_count = 0
    for prev, new in transitions:
        if prev == EnvelopeState.OPEN and new == EnvelopeState.CLOSED:
            alternating_count += 1
    assert alternating_count <= 1
