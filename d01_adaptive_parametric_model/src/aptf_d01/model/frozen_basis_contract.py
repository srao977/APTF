from __future__ import annotations

import hashlib
import json
from typing import Any

APPROVED_BASIS_RUNTIME_MISMATCH = "APPROVED_BASIS_RUNTIME_MISMATCH"
FROZEN_BASIS_MUTATION_ATTEMPT = "FROZEN_BASIS_MUTATION_ATTEMPT"

FACTOR_ALIASES = {
    "displacement": "price_displacement",
    "velocity": "price_velocity",
    "acceleration": "price_acceleration",
}


def canonical_basis_payload(ordered_feature_names: list[str]) -> str:
    # Canonical serialization: UTF-8 JSON list, exact order preserved, compact separators.
    return json.dumps(ordered_feature_names, separators=(",", ":"), ensure_ascii=True)


def canonical_basis_hash(ordered_feature_names: list[str]) -> str:
    payload = canonical_basis_payload(ordered_feature_names)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def validate_basis_contract(
    experiment_id: str,
    approved_feature_names: list[str],
    approved_basis_sha256: str,
    runtime_feature_names: list[str],
    error_code: str = APPROVED_BASIS_RUNTIME_MISMATCH,
    stage: str = "pre_observation",
) -> dict[str, bool]:
    runtime_hash = canonical_basis_hash(runtime_feature_names)
    count_match = len(approved_feature_names) == len(runtime_feature_names)
    ordered_names_match = approved_feature_names == runtime_feature_names
    hash_match = approved_basis_sha256 == runtime_hash
    if count_match and ordered_names_match and hash_match:
        return {
            "count_match": True,
            "ordered_names_match": True,
            "hash_match": True,
        }

    first_diff_index = -1
    limit = min(len(approved_feature_names), len(runtime_feature_names))
    for i in range(limit):
        if approved_feature_names[i] != runtime_feature_names[i]:
            first_diff_index = i
            break

    raise RuntimeError(
        f"{error_code}: stage={stage}; experiment_id={experiment_id}; "
        f"expected_feature_count={len(approved_feature_names)}; actual_feature_count={len(runtime_feature_names)}; "
        f"expected_hash={approved_basis_sha256}; actual_hash={runtime_hash}; "
        f"count_match={count_match}; ordered_names_match={ordered_names_match}; hash_match={hash_match}; "
        f"first_diff_index={first_diff_index}"
    )


def _evaluate_term(stem: str, base_features: dict[str, float]) -> float:
    if stem == "bias":
        return 1.0
    factors = stem.split("_x_")
    value = 1.0
    for factor in factors:
        if factor == "bias":
            value *= 1.0
            continue
        key = factor if factor in base_features else FACTOR_ALIASES.get(factor, factor)
        if key not in base_features:
            raise KeyError(f"UNKNOWN_FROZEN_BASIS_FACTOR: {factor}")
        value *= float(base_features[key])
    return value


def evaluate_frozen_basis(ordered_feature_names: list[str], base_features: dict[str, float]) -> dict[str, float]:
    values: dict[str, float] = {}
    for feature_name in ordered_feature_names:
        stem = feature_name
        power = 1
        if "^" in feature_name:
            stem, power_text = feature_name.rsplit("^", 1)
            if not power_text.isdigit() or int(power_text) < 1:
                raise ValueError(f"INVALID_FROZEN_BASIS_POWER: {feature_name}")
            power = int(power_text)
        term_value = _evaluate_term(stem, base_features)
        values[feature_name] = float(term_value**power)
    return values


def build_registry_entry(experiment_id: str, manifest_path: str, manifest_sha256: str, payload: dict[str, Any]) -> dict[str, Any]:
    ordered = list(payload.get("final_feature_order", []))
    basis_sha = canonical_basis_hash(ordered)
    return {
        "experiment_id": experiment_id,
        "manifest_path": manifest_path,
        "manifest_sha256": manifest_sha256,
        "manifest_basis_sha256": str(payload.get("basis_sha256", "")),
        "approved_feature_names": ordered,
        "approved_feature_count": len(ordered),
        "approved_basis_sha256": basis_sha,
    }
