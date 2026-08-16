from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

import numpy as np


@dataclass(frozen=True)
class ColumnMeta:
    name: str
    feature_type: str
    stage: str
    base_feature: str
    polynomial_order: int
    interaction_parent_a: str
    interaction_parent_b: str
    intercept: bool
    lineage_id: str


@dataclass(frozen=True)
class DependencyGroup:
    group_id: str
    stage: str
    feature_names: tuple[str, ...]
    representative: str
    dependency_type: str
    exact_or_numerical: str
    tolerance: float
    evidence: str


@dataclass(frozen=True)
class IndependentBasisResult:
    retained_indices: tuple[int, ...]
    excluded_indices: tuple[int, ...]
    retained_names: tuple[str, ...]
    excluded_names: tuple[str, ...]
    dependency_groups: tuple[DependencyGroup, ...]
    basis_sha256: str


def classify_condition_number(cond: float) -> str:
    if not math.isfinite(cond):
        return "SINGULAR"
    if cond < 1.0e4:
        return "WELL CONDITIONED"
    if cond < 1.0e8:
        return "MODERATELY CONDITIONED"
    if cond < 1.0e12:
        return "POORLY CONDITIONED"
    return "SEVERELY ILL-CONDITIONED"


def _rank_tolerance(x: np.ndarray) -> float:
    if x.size == 0:
        return 0.0
    rows, cols = x.shape
    svals = np.linalg.svd(x, compute_uv=False, full_matrices=False)
    largest = float(np.max(svals)) if svals.size else 0.0
    return max(rows, cols) * np.finfo(float).eps * largest


def _affine_with_intercept(candidate: np.ndarray, representative: np.ndarray, tol: float) -> bool:
    if candidate.size != representative.size:
        return False
    if candidate.size == 0:
        return False
    xm = np.column_stack([representative, np.ones(candidate.size, dtype=float)])
    coef, *_ = np.linalg.lstsq(xm, candidate, rcond=None)
    recon = xm @ coef
    err = np.linalg.norm(candidate - recon)
    return bool(err <= tol * max(1.0, np.linalg.norm(candidate)))


def _dependency_type(candidate: np.ndarray, representative: np.ndarray, has_intercept: bool, tol: float) -> tuple[str, str, str]:
    if np.allclose(candidate, representative, rtol=0.0, atol=tol):
        return "EXACT_EQUALITY", "EXACT_DEPENDENCE", "candidate == representative"
    if np.allclose(candidate, -representative, rtol=0.0, atol=tol):
        return "SIGN_REVERSAL", "EXACT_DEPENDENCE", "candidate == -representative"

    denom = float(np.dot(representative, representative))
    if denom > 0.0:
        alpha = float(np.dot(candidate, representative) / denom)
        if np.allclose(candidate, alpha * representative, rtol=0.0, atol=tol):
            return "CONSTANT_MULTIPLE", "EXACT_DEPENDENCE", f"candidate == {alpha:.12g} * representative"

    if has_intercept and _affine_with_intercept(candidate, representative, tol):
        return "AFFINE_WITH_INTERCEPT", "EXACT_DEPENDENCE", "candidate affine-equivalent with intercept"

    corr = float("nan")
    if np.std(candidate) > 0 and np.std(representative) > 0:
        corr = float(np.corrcoef(candidate, representative)[0, 1])
    if math.isfinite(corr) and abs(corr) >= 0.95:
        return "HIGH_CORRELATION", "HIGH_CORRELATION_ONLY", f"abs(corr)={abs(corr):.6f}"

    return "LINEAR_DEPENDENCE", "NUMERICAL_DEPENDENCE", "incremental rank did not increase"


def build_independent_basis(
    x_phase1: np.ndarray,
    ordered_columns: list[ColumnMeta],
) -> IndependentBasisResult:
    if x_phase1.ndim != 2:
        raise ValueError("x_phase1 must be 2D")
    if x_phase1.shape[1] != len(ordered_columns):
        raise ValueError("column metadata length mismatch")

    retained: list[int] = []
    excluded: list[int] = []
    groups: list[DependencyGroup] = []

    x_retained: np.ndarray | None = None
    has_intercept = any(c.intercept for c in ordered_columns)

    for j, col in enumerate(ordered_columns):
        cand = x_phase1[:, j]
        if x_retained is None:
            retained.append(j)
            x_retained = cand.reshape(-1, 1)
            continue

        tol_before = _rank_tolerance(x_retained)
        rank_before = int(np.linalg.matrix_rank(x_retained, tol=tol_before if tol_before > 0 else None))

        x_new = np.column_stack([x_retained, cand])
        tol_after = _rank_tolerance(x_new)
        rank_after = int(np.linalg.matrix_rank(x_new, tol=tol_after if tol_after > 0 else None))

        if rank_after > rank_before:
            retained.append(j)
            x_retained = x_new
            continue

        excluded.append(j)

        rep_idx = retained[-1]
        rep_col = x_phase1[:, rep_idx]
        dep_type, dep_class, evidence = _dependency_type(cand, rep_col, has_intercept=has_intercept, tol=max(tol_after, 1e-12))
        gid = f"{ordered_columns[rep_idx].name}__{col.name}"
        groups.append(
            DependencyGroup(
                group_id=gid,
                stage=col.stage,
                feature_names=(ordered_columns[rep_idx].name, col.name),
                representative=ordered_columns[rep_idx].name,
                dependency_type=dep_type,
                exact_or_numerical=dep_class,
                tolerance=max(tol_after, 1e-12),
                evidence=evidence,
            )
        )

    retained_names = tuple(ordered_columns[i].name for i in retained)
    excluded_names = tuple(ordered_columns[i].name for i in excluded)

    h = hashlib.sha256()
    for name in retained_names:
        h.update(name.encode("utf-8"))
        h.update(b"\n")

    return IndependentBasisResult(
        retained_indices=tuple(retained),
        excluded_indices=tuple(excluded),
        retained_names=retained_names,
        excluded_names=excluded_names,
        dependency_groups=tuple(groups),
        basis_sha256=h.hexdigest().upper(),
    )


def matrix_condition_report(x: np.ndarray) -> dict[str, float | int | str]:
    rows, cols = x.shape
    if rows == 0 or cols == 0:
        return {
            "rows": rows,
            "columns": cols,
            "matrix_rank": 0,
            "rank_deficiency": cols,
            "condition_number": float("inf"),
            "smallest_singular_value": float("nan"),
            "largest_singular_value": float("nan"),
            "classification": "SINGULAR",
        }

    tol = _rank_tolerance(x)
    rank = int(np.linalg.matrix_rank(x, tol=tol if tol > 0 else None))
    rank_def = cols - rank

    svals = np.linalg.svd(x, compute_uv=False, full_matrices=False)
    min_sv = float(np.min(svals)) if svals.size else float("nan")
    max_sv = float(np.max(svals)) if svals.size else float("nan")

    try:
        cond = float(np.linalg.cond(x)) if rows >= cols else float(np.linalg.cond(x.T @ x))
    except Exception:
        cond = float("inf")

    return {
        "rows": rows,
        "columns": cols,
        "matrix_rank": rank,
        "rank_deficiency": rank_def,
        "condition_number": cond,
        "smallest_singular_value": min_sv,
        "largest_singular_value": max_sv,
        "classification": classify_condition_number(cond),
    }
