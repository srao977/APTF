from pathlib import Path

from aptf_d04.cli.main import run_single, validate_scenario


ROOT = Path(__file__).resolve().parents[1]


SCENARIOS = [
    "01_strong_shape_poor_capture",
    "02_shape_becomes_capturable",
    "03_open_then_shape_deteriorates",
    "04_shape_up_envelope_down",
    "05_threshold_noise_hysteresis",
    "06_envelope_up_shape_down",
    "07_strong_shape_hard_gate",
]


def test_scenarios() -> None:
    for name in SCENARIOS:
        summary = run_single(ROOT, name, speed=0.0, verbose=False)
        ok, _msg = validate_scenario(name, summary)
        assert ok, f"scenario failed: {name}"


def test_scenario_04_shape_up_gate_down_capture_down() -> None:
    summary = run_single(ROOT, "04_shape_up_envelope_down", speed=0.0, verbose=False)
    assert summary["shapes"][-1] > summary["shapes"][0]
    assert summary["gates"][-1] < summary["gates"][0]
    assert summary["captures"][-1] < summary["captures"][0]


def test_scenario_07_stays_closed() -> None:
    summary = run_single(ROOT, "07_strong_shape_hard_gate", speed=0.0, verbose=False)
    assert summary["final_state"] == "CLOSED"
    assert summary["events"].get("CANDIDATE_QUALIFIED", 0) == 0
