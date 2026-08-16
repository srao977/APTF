from __future__ import annotations

import numpy as np

from aptf_d01.features.structural_independence import (
    ColumnMeta,
    build_independent_basis,
    classify_condition_number,
    matrix_condition_report,
)
from aptf_d01.model.feature_contract import derive_admissible_base_features
from aptf_d01.providers.observation_capabilities import firstrate_ohlcv_capabilities


def _col(name: str, stage: str = "BASE", intercept: bool = False) -> ColumnMeta:
    return ColumnMeta(
        name=name,
        feature_type="base",
        stage=stage,
        base_feature=name,
        polynomial_order=1,
        interaction_parent_a="",
        interaction_parent_b="",
        intercept=intercept,
        lineage_id=name,
    )


def test_exact_duplicate_retains_one() -> None:
    x1 = np.array([1.0, 2.0, 3.0, 4.0])
    x2 = x1.copy()
    x = np.column_stack([x1, x2])
    res = build_independent_basis(x, [_col("x1"), _col("x2")])
    assert res.retained_names == ("x1",)
    assert res.excluded_names == ("x2",)


def test_sign_reversal_retains_one() -> None:
    x1 = np.array([1.0, 2.0, 3.0, 4.0])
    x2 = -x1
    x = np.column_stack([x1, x2])
    res = build_independent_basis(x, [_col("x1"), _col("x2")])
    assert res.retained_names == ("x1",)
    assert res.excluded_names == ("x2",)


def test_constant_multiple_retains_one() -> None:
    x1 = np.array([1.0, 2.0, 3.0, 4.0])
    x2 = 2.0 * x1
    x = np.column_stack([x1, x2])
    res = build_independent_basis(x, [_col("x1"), _col("x2")])
    assert res.retained_names == ("x1",)


def test_affine_with_intercept_excluded() -> None:
    x1 = np.array([1.0, 2.0, 3.0, 4.0])
    bias = np.ones_like(x1)
    x2 = x1 + 3.0
    x = np.column_stack([bias, x1, x2])
    cols = [_col("bias", intercept=True), _col("x1"), _col("x2")]
    res = build_independent_basis(x, cols)
    assert res.retained_names == ("bias", "x1")
    assert res.excluded_names == ("x2",)


def test_constant_with_intercept_excluded() -> None:
    bias = np.ones(6)
    const = np.ones(6) * 5.0
    x = np.column_stack([bias, const])
    cols = [_col("bias", intercept=True), _col("const")]
    res = build_independent_basis(x, cols)
    assert res.retained_names == ("bias",)


def test_polynomial_binary_square_dependency() -> None:
    x = np.array([0.0, 1.0, 0.0, 1.0, 1.0])
    x2 = x * x
    mat = np.column_stack([x, x2])
    cols = [_col("x"), _col("x^2", stage="POLYNOMIAL")]
    res = build_independent_basis(mat, cols)
    assert res.retained_names == ("x",)


def test_interaction_zero_dependency() -> None:
    x1 = np.array([1.0, 2.0, 3.0, 4.0])
    zero = np.zeros_like(x1)
    inter = x1 * zero
    mat = np.column_stack([x1, inter])
    cols = [_col("x1"), _col("x1_x_zero", stage="INTERACTION")]
    res = build_independent_basis(mat, cols)
    assert res.retained_names == ("x1",)


def test_condition_classification() -> None:
    assert classify_condition_number(float("inf")) == "SINGULAR"
    assert classify_condition_number(100.0) == "WELL CONDITIONED"
    assert classify_condition_number(1.0e6) == "MODERATELY CONDITIONED"
    assert classify_condition_number(1.0e10) == "POORLY CONDITIONED"
    assert classify_condition_number(1.0e12) == "SEVERELY ILL-CONDITIONED"


def test_matrix_report_rank_deficiency() -> None:
    x = np.column_stack([np.array([1.0, 2.0, 3.0]), np.array([2.0, 4.0, 6.0])])
    rep = matrix_condition_report(x)
    assert int(rep["matrix_rank"]) == 1
    assert int(rep["rank_deficiency"]) == 1


def test_basis_hash_determinism_for_same_inputs() -> None:
    x1 = np.array([1.0, 2.0, 3.0, 4.0])
    x2 = np.array([2.0, 3.0, 4.0, 5.0])
    x3 = x1 + x2
    mat = np.column_stack([x1, x2, x3])
    cols = [_col("x1"), _col("x2"), _col("x3")]

    r1 = build_independent_basis(mat, cols)
    r2 = build_independent_basis(mat, cols)
    assert r1.basis_sha256 == r2.basis_sha256
    assert r1.retained_names == r2.retained_names


def test_provider_neutral_admissibility_equivalence() -> None:
    caps_a = firstrate_ohlcv_capabilities("SPY")
    caps_b = firstrate_ohlcv_capabilities("QQQ")

    active_a, _ = derive_admissible_base_features(capabilities=caps_a, include_volume=True)
    active_b, _ = derive_admissible_base_features(capabilities=caps_b, include_volume=True)

    assert sorted(active_a) == sorted(active_b)


def test_phase_freeze_detects_later_rank_drop() -> None:
    p1_x1 = np.array([1.0, 2.0, 3.0, 4.0])
    p1_x2 = np.array([0.0, 1.0, 0.0, 1.0])
    phase1 = np.column_stack([p1_x1, p1_x2])
    cols = [_col("x1"), _col("x2")]
    basis = build_independent_basis(phase1, cols)
    assert basis.retained_names == ("x1", "x2")

    p2_x1 = np.array([1.0, 1.0, 1.0, 1.0])
    p2_x2 = np.array([2.0, 2.0, 2.0, 2.0])
    phase2 = np.column_stack([p2_x1, p2_x2])
    rep = matrix_condition_report(phase2)
    assert int(rep["matrix_rank"]) == 1
    assert int(rep["rank_deficiency"]) == 1
