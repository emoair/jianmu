from jianmu.self_learning.darwinforge.algorithm_variant_generator import build_variant_row


def test_variant_generator_variable_renaming():
    row = build_variant_row("pilot", 0)
    assert "v0_a" in row["algorithm_source"]


def test_variant_generator_function_renaming():
    row = build_variant_row("pilot", 1)
    assert "compute_" in row["algorithm_source"]
    assert "compute(void)" not in row["algorithm_source"]


def test_variant_generator_array_size_mutation():
    row = build_variant_row("pilot", 0)
    assert row["requirement_spec"]["array_size_policy"].startswith("static_size_")


def test_variant_generator_loop_direction_mutation():
    row = build_variant_row("pilot", 8000)
    assert row["variant_features"]["loop_direction_mutation"] is True


def test_variant_generator_sorting_order_mutation():
    row = build_variant_row("pilot", 8000)
    assert row["requirement_spec"]["sorting_order_policy"] in {"ascending", "descending"}
