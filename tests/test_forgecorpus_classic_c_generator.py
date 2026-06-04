from __future__ import annotations

from jianmu.self_learning.darwinforge.forgecorpus_classic_c_generator import algorithm_source


def test_classic_c_generator_contains_sort_search_math_array_matrix() -> None:
    for family, name in [
        ("sorting", "bubble_sort"),
        ("search", "binary_search"),
        ("math", "gcd_euclid"),
        ("array", "prefix_sum"),
        ("matrix", "matrix_add"),
    ]:
        source, expected = algorithm_source(0, family, name)
        assert "int compute" in source
        assert expected is not None

