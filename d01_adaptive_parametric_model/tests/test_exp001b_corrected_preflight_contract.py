from __future__ import annotations

import importlib.util
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from aptf_d01.model.frozen_basis_contract import APPROVED_BASIS_RUNTIME_MISMATCH, canonical_basis_hash, validate_basis_contract


def _load_runner_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_historical_spy_experiment_001b.py"
    spec = importlib.util.spec_from_file_location("run_historical_spy_experiment_001b", script_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_historical_spy_experiment_001b"] = mod
    spec.loader.exec_module(mod)
    return mod


def _must_raise_mismatch(approved: list[str], runtime: list[str], approved_hash: str | None = None) -> bool:
    try:
        validate_basis_contract(
            experiment_id="TEST",
            approved_feature_names=approved,
            approved_basis_sha256=approved_hash or canonical_basis_hash(approved),
            runtime_feature_names=runtime,
            error_code=APPROVED_BASIS_RUNTIME_MISMATCH,
            stage="test",
        )
    except RuntimeError as exc:
        return APPROVED_BASIS_RUNTIME_MISMATCH in str(exc)
    return False


def test_intentional_failure_extra_feature():
    approved = ["bias", "x", "y"]
    assert _must_raise_mismatch(approved, ["bias", "x", "y", "z"])


def test_intentional_failure_missing_feature():
    approved = ["bias", "x", "y"]
    assert _must_raise_mismatch(approved, ["bias", "x"])


def test_intentional_failure_wrong_order():
    approved = ["bias", "x", "y"]
    assert _must_raise_mismatch(approved, ["bias", "y", "x"])


def test_intentional_failure_wrong_hash():
    approved = ["bias", "x", "y"]
    assert _must_raise_mismatch(approved, ["bias", "x", "y"], approved_hash="BADHASH")


def test_intentional_failure_missing_manifest_registry():
    runner = _load_runner_module()
    ok, failures = runner.preflight_exp001b_execution_contract(
        dataset_sha256_actual=runner.EXPECTED_SHA256,
        model_version="D01_V0_1_2",
        phase_boundaries={
            "phase_1_start": runner.FIXED_PHASES["PHASE_1"][0],
            "phase_1_end": runner.FIXED_PHASES["PHASE_1"][1],
            "phase_1_rows": runner.FIXED_PHASES["PHASE_1"][2],
            "phase_2_start": runner.FIXED_PHASES["PHASE_2"][0],
            "phase_2_end": runner.FIXED_PHASES["PHASE_2"][1],
            "phase_2_rows": runner.FIXED_PHASES["PHASE_2"][2],
            "phase_3_start": runner.FIXED_PHASES["PHASE_3"][0],
            "phase_3_end": runner.FIXED_PHASES["PHASE_3"][1],
            "phase_3_rows": runner.FIXED_PHASES["PHASE_3"][2],
        },
        approved_basis_registry={"A_n1": {}},
        submitted_task_count=15,
        configured_workers=18,
        reserve_data_used=False,
    )
    assert ok is False
    assert "APPROVED_MANIFEST_COUNT_MISMATCH" in failures


def test_intentional_success_exact_basis():
    approved = ["bias", "x", "y"]
    chk = validate_basis_contract(
        experiment_id="TEST",
        approved_feature_names=approved,
        approved_basis_sha256=canonical_basis_hash(approved),
        runtime_feature_names=list(approved),
        error_code=APPROVED_BASIS_RUNTIME_MISMATCH,
        stage="test",
    )
    assert chk["count_match"] and chk["ordered_names_match"] and chk["hash_match"]


def test_old_a_n1_regression_fails_before_obs1_contract():
    approved = ["bias", "price_displacement", "price_velocity", "price_acceleration"]
    bad_runtime = [
        "bias",
        "price_displacement",
        "price_velocity",
        "price_acceleration",
        "volume_log_x_price_displacement",
        "relative_volume_x_price_velocity",
        "volume_density_x_price_displacement",
        "price_velocity_x_acceleration",
    ]
    assert _must_raise_mismatch(approved, bad_runtime)


def test_de_order_regression_fails_on_same_set_wrong_order():
    approved = ["bias", "a", "b", "c"]
    wrong = ["bias", "b", "a", "c"]
    assert _must_raise_mismatch(approved, wrong)


def _worker_probe(task_id: int) -> dict[str, float | int]:
    pid = __import__("os").getpid()
    ppid = __import__("os").getppid()
    start = datetime.now(UTC).timestamp()
    acc = 0
    for i in range(300000):
        acc = (acc + ((i * 2654435761) ^ (task_id + 17))) % 1000000007
    end = datetime.now(UTC).timestamp()
    return {"task_id": task_id, "pid": pid, "ppid": ppid, "start": start, "end": end, "checksum": acc}


def test_process_execution_contract_15_tasks_parallel():
    coordinator_pid = __import__("os").getpid()
    with ProcessPoolExecutor(max_workers=18) as ex:
        results = [f.result() for f in [ex.submit(_worker_probe, i) for i in range(15)]]

    assert len(results) == 15
    distinct_pids = len({int(r["pid"]) for r in results})
    assert distinct_pids > 1
    assert any(int(r["pid"]) != coordinator_pid for r in results)

    events: list[tuple[float, int]] = []
    for r in results:
        events.append((float(r["start"]), +1))
        events.append((float(r["end"]), -1))
    events.sort(key=lambda x: (x[0], -x[1]))

    active = 0
    peak = 0
    for _, delta in events:
        active += delta
        peak = max(peak, active)

    assert peak > 1
