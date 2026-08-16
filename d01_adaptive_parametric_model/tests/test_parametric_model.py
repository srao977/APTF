from aptf_d01.parametric.basis import polynomial_basis


def test_polynomial_orders_supported() -> None:
    x = {"a": 2.0}
    assert "a" in polynomial_basis(x, 1)
    assert "a^2" in polynomial_basis(x, 2)
    assert "a^3" in polynomial_basis(x, 3)
