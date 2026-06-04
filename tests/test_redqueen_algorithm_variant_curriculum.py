from jianmu.self_learning.darwinforge.redqueen_algorithm_variant_curriculum import redqueen_variant_curriculum


def test_redqueen_algorithm_variant_curriculum_assignments():
    result = redqueen_variant_curriculum()
    assert "variable_rename_binding_assignment" in result
    assert "algorithm_regression_guard_assignment" in result
    assert all(item["safety_contract"] for item in result.values())
