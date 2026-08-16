from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "verify_exp001b_execution_harness.py"
    spec = importlib.util.spec_from_file_location("verify_exp001b_execution_harness", script_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_basis_manifest_mismatch_fails_count():
    mod = _load_module()
    try:
        mod.validate_runtime_basis_against_manifest(
            "A_n1",
            approved_feature_names=["bias", "a", "b"],
            approved_basis_sha256=mod.sha256_json_list(["bias", "a", "b"]),
            runtime_feature_names=["bias", "a"],
        )
        assert False, "expected mismatch error"
    except RuntimeError as exc:
        assert "APPROVED_BASIS_RUNTIME_MISMATCH" in str(exc)


def test_feature_order_mismatch_fails():
    mod = _load_module()
    approved = ["bias", "a", "b"]
    runtime = ["bias", "b", "a"]
    try:
        mod.validate_runtime_basis_against_manifest(
            "B_n1",
            approved_feature_names=approved,
            approved_basis_sha256=mod.sha256_json_list(approved),
            runtime_feature_names=runtime,
        )
        assert False, "expected mismatch error"
    except RuntimeError as exc:
        assert "first_diff_index=1" in str(exc)


def test_basis_hash_mismatch_fails():
    mod = _load_module()
    approved = ["bias", "a", "b"]
    runtime = ["bias", "a", "b"]
    try:
        mod.validate_runtime_basis_against_manifest(
            "C_n1",
            approved_feature_names=approved,
            approved_basis_sha256="BADHASH",
            runtime_feature_names=runtime,
        )
        assert False, "expected mismatch error"
    except RuntimeError as exc:
        assert "APPROVED_BASIS_RUNTIME_MISMATCH" in str(exc)


def test_correct_basis_passes():
    mod = _load_module()
    approved = ["bias", "x", "y"]
    result = mod.validate_runtime_basis_against_manifest(
        "D_n2",
        approved_feature_names=approved,
        approved_basis_sha256=mod.sha256_json_list(approved),
        runtime_feature_names=list(approved),
    )
    assert result["count_match"] is True
    assert result["ordered_names_match"] is True
    assert result["hash_match"] is True


def test_build_task_list_generates_15():
    mod = _load_module()
    experiments = [{"id": f"E{i}"} for i in range(15)]
    tasks = mod.build_task_list(experiments)
    assert len(tasks) == 15


def test_parallel_smoke_concurrency_math_detects_overlap():
    mod = _load_module()
    base = 1_000_000.0
    peak, timeline = mod.compute_peak_concurrency(
        [
            (base + 0.0, base + 5.0),
            (base + 1.0, base + 6.0),
            (base + 2.0, base + 3.0),
        ]
    )
    assert peak > 1
    assert len(timeline) == 6


def test_static_runner_has_processpool_and_worker_loop_location():
    mod = _load_module()
    audit = mod.static_runner_audit()
    assert audit["if_main_present"] is True
    assert audit["executor_calls"] >= 1
    assert audit["submit_calls"] >= 1
    assert audit["heavy_loop_location"] == "WORKER"


def test_detect_sequential_fallbacks_hits_keywords():
    mod = _load_module()
    text = "debug mode with fallback_to_sequential and workers = 1"
    hits = mod.detect_sequential_fallbacks(text)
    assert "fallback_to_sequential" in hits
    assert "workers = 1" in hits


def test_preflight_contract_detects_basis_and_task_failure():
    mod = _load_module()
    ok, errs = mod.preflight_exp001b_execution_contract(
        dataset_sha256_actual="ABC",
        dataset_sha256_expected="ABC",
        approved_manifests={"A_n1": {}},
        comp_rows=[{"status": "COUNT_MISMATCH"}],
        submitted_task_count=14,
    )
    assert ok is False
    assert "APPROVED_MANIFEST_COUNT_MISMATCH" in errs
    assert "BASIS_CONTRACT_MISMATCH" in errs
    assert "TASK_SUBMISSION_COUNT_MISMATCH" in errs
