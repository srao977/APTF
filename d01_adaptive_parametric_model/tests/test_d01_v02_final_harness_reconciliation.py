from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
VERIFY_PATH = ROOT / "scripts" / "verify_d01_v02_final_harness_reconciliation.py"
PRE_PATH = ROOT / "output" / "d01_v02_final_harness_reconciliation" / "manifests" / "pre_reconciliation_snapshot.json"
POST_PATH = ROOT / "output" / "d01_v02_final_harness_reconciliation" / "manifests" / "post_reconciliation_verification.json"
AUTHORIZED = {"S03_B", "S03_D", "S06_C", "S06_D", "S06_E", "S07_F", "S08_D"}


def _load_verifier():
    spec = importlib.util.spec_from_file_location("d01_v02_harness_reconciliation_verifier", VERIFY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _rules() -> dict[str, dict[str, str]]:
    return _load_verifier().assertion_snapshots()


def test_h01_s03_b_uses_corrected_semantic_channel() -> None:
    rule = _rules()["S03_B"]["normalized_rule"]
    assert "event_acceleration_mean" in rule
    assert "state_level" not in rule


def test_h02_s03_d_uses_corrected_displacement_comparison() -> None:
    rule = _rules()["S03_D"]["normalized_rule"]
    assert rule.count("event_displacement") >= 3
    assert "state_level" not in rule


def test_h03_s06_c_uses_pre_event_to_event_half_life() -> None:
    rule = _rules()["S06_C"]["normalized_rule"]
    assert "s06_h_event" in rule
    assert "s06_h_pre" in rule


def test_h04_s06_d_uses_pre_event_to_event_forward_interval() -> None:
    rule = _rules()["S06_D"]["normalized_rule"]
    assert "s06_fwd_event" in rule
    assert "s06_fwd_pre" in rule


def test_h05_s06_e_tests_transient_disruption_and_recovery() -> None:
    rule = _rules()["S06_E"]["normalized_rule"]
    assert "s06_persistence_event_min" in rule
    assert "s06_persistence_pre" in rule
    assert "s06_persistence_recovery" in rule


def test_h06_s07_f_uses_mean_strength_discrimination() -> None:
    rule = _rules()["S07_F"]["normalized_rule"]
    assert "strength" in rule and "mean" in rule
    assert "Constant(value=0.95)" not in rule
    assert "slice=Constant(value='max')" not in rule


def test_h07_s08_d_uses_gap_response_and_recovery() -> None:
    rule = _rules()["S08_D"]["normalized_rule"]
    assert "s08_u_gap" in rule
    assert "s08_u_pre" in rule
    assert "s08_u_recovery" in rule


def test_h08_only_seven_authorized_assertions_changed() -> None:
    post = json.loads(POST_PATH.read_text(encoding="utf-8"))
    assert set(post["changed_assertion_ids"]) == AUTHORIZED
    assert post["unauthorized_assertions_changed"] == []


def test_h09_other_74_assertions_are_identical() -> None:
    before = json.loads(PRE_PATH.read_text(encoding="utf-8"))["assertions"]
    after = _rules()
    unchanged = set(before) - AUTHORIZED
    assert len(unchanged) == 74
    assert all(before[assertion_id]["sha256"] == after[assertion_id]["sha256"] for assertion_id in unchanged)


def test_h10_d01_source_hashes_are_unchanged() -> None:
    verifier = _load_verifier()
    before = json.loads(PRE_PATH.read_text(encoding="utf-8"))["d01_source_hashes"]
    assert before == verifier.source_hashes()