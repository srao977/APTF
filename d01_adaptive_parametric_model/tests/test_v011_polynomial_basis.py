from aptf_d01.parametric.basis import polynomial_basis


def test_interaction_max_order_defaults_to_linear_interaction_terms() -> None:
    features = {
        "a": 2.0,
        "b": -3.0,
        "a_x_b": -6.0,
    }
    out = polynomial_basis(features, order=3, interaction_max_order=1)
    assert "a^3" in out
    assert "a_x_b" in out
    assert "a_x_b^2" not in out
    assert "a_x_b^3" not in out


def test_conditioned_terms_expand_by_order() -> None:
    out2 = polynomial_basis({"z": 1.5}, order=2, interaction_max_order=1)
    out3 = polynomial_basis({"z": 1.5}, order=3, interaction_max_order=1)
    assert out2["z"] == 1.5
    assert out2["z^2"] == 2.25
    assert out3["z^3"] == 3.375
