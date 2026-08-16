from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from .constants import (
    DATASET_SHA256,
    SCORING_FREEZE_ID,
    SCORING_FREEZE_SHA256,
    SCORING_V022_FREEZE_ID,
    SCORING_V022_FREEZE_SHA256,
    STAGE1_FREEZE_SHA256,
    STAGE2_DESIGN_FREEZE_ID,
    STAGE2_DESIGN_FREEZE_SHA256,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


def logical_seal(records: list[dict[str, Any]], authority: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(canonical_json(record).encode("utf-8"))
        digest.update(b"\n")
    digest.update(canonical_json(authority).encode("utf-8"))
    return digest.hexdigest().upper()


def _verify(path: Path, expected: str, failures: list[str]) -> None:
    if not path.is_file() or sha256_file(path) != expected.upper():
        failures.append(str(path))


def verify_authorities(workspace_root: Path, include_dataset: bool = True) -> dict[str, Any]:
    failures: list[str] = []
    stage1_path = workspace_root / "D01_V0_2_STAGE_1_SYNTHETIC_ACCEPTANCE_FREEZE.json"
    design_path = workspace_root / "D01_STAGE_2_HISTORICAL_STATE_VALIDITY_DESIGN_V0_2_FREEZE.json"
    scoring_path = workspace_root / "D01_STAGE_2_SCORING_CLARIFICATION_ADDENDUM_V0_2_1_FREEZE.json"
    scoring_v022_path = workspace_root / "D01_STAGE_2_SCORING_CLARIFICATION_ADDENDUM_V0_2_2_FREEZE.json"
    _verify(stage1_path, STAGE1_FREEZE_SHA256, failures)
    _verify(design_path, STAGE2_DESIGN_FREEZE_SHA256, failures)
    _verify(scoring_path, SCORING_FREEZE_SHA256, failures)
    _verify(scoring_v022_path, SCORING_V022_FREEZE_SHA256, failures)
    stage1 = json.loads(stage1_path.read_text(encoding="utf-8"))
    design = json.loads(design_path.read_text(encoding="utf-8"))
    scoring = json.loads(scoring_path.read_text(encoding="utf-8"))
    scoring_v022 = json.loads(scoring_v022_path.read_text(encoding="utf-8"))
    if design.get("freeze_id") != STAGE2_DESIGN_FREEZE_ID:
        failures.append("stage2_design_freeze_id")
    if scoring.get("freeze_id") != SCORING_FREEZE_ID:
        failures.append("scoring_freeze_id")
    if scoring_v022.get("freeze_id") != SCORING_V022_FREEZE_ID:
        failures.append("scoring_v022_freeze_id")
    for section in ("model_authority_manifest", "design_authority_manifest", "stage_1_evidence_manifest"):
        for item in stage1[section]:
            _verify(workspace_root / item["relative_path"], item["sha256"], failures)
    for item in design["stage_2_design_authority"]:
        _verify(workspace_root / item["relative_path"], item["sha256"], failures)
    for item in design["canonical_specifications"].values():
        _verify(workspace_root / item["relative_path"], item["sha256"], failures)
    for item in scoring["frozen_authority"].values():
        _verify(workspace_root / item["relative_path"], item["sha256"], failures)
    for item in scoring_v022["frozen_authority"].values():
        _verify(workspace_root / item["relative_path"], item["sha256"], failures)
    dataset = workspace_root / design["dataset"]["path"]
    if include_dataset:
        _verify(dataset, DATASET_SHA256, failures)
    with dataset.open("r", encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    required = {"event_timestamp_utc", "event_timestamp_local", "close", "volume", "session_type", "data_valid"}
    if not required.issubset(header):
        failures.append("dataset_header")
    if not design["dataset"].get("reserve_sealed"):
        failures.append("reserve_sealed")
    if failures:
        raise RuntimeError("STAGE_1_BASELINE_INTEGRITY_FAILURE:" + ",".join(failures))
    return {
        "status": "PASS", "design_freeze_id": design["freeze_id"],
        "scoring_freeze_id": scoring["freeze_id"], "scoring_v022_freeze_id": scoring_v022["freeze_id"],
        "dataset_sha256": DATASET_SHA256,
        "header": header, "reserve_sealed": True, "reserve_accessed": False,
    }


def bootstrap_seed(freeze_identity: str = STAGE2_DESIGN_FREEZE_ID) -> int:
    return int.from_bytes(hashlib.sha256(freeze_identity.encode("utf-8")).digest()[:8], "big")