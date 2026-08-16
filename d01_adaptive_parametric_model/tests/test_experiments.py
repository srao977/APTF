from pathlib import Path

from aptf_d01.runtime.experiment_runner import _load_yaml


def test_all_15_experiments_and_10_scenarios_present() -> None:
    root = Path(__file__).resolve().parents[1]
    matrix = _load_yaml(root / "config" / "experiment_matrix.yaml")["experiments"]
    scenarios = _load_yaml(root / "config" / "synthetic_scenarios.yaml")["scenarios"]
    assert len(matrix) == 15
    assert len(scenarios) == 10
