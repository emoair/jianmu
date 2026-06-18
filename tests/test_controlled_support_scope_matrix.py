from jianmu.self_learning.darwinforge.controlled_support_scope_matrix import build_support_scope_matrix


def test_support_scope_matrix_defines_supported_subsets(tmp_path):
    result = build_support_scope_matrix(tmp_path)
    subsets = {row["subset"] for row in result["subsets"]}
    assert {"function", "array", "function_array", "structured_recursion"} <= subsets


def test_support_scope_matrix_keeps_production_completed_false(tmp_path):
    result = build_support_scope_matrix(tmp_path)
    assert all(row["production_completed"] is False for row in result["subsets"])
    assert all(row["requires_explicit_opt_in"] is True for row in result["subsets"])
